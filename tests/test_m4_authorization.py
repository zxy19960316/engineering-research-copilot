from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
AUTHORIZATION_ROOT = REPO_ROOT / "evals" / "m4" / "authorization"
sys.path.insert(0, str(AUTHORIZATION_ROOT))

import audit_authorization as audit  # noqa: E402
import build_authorization as build  # noqa: E402


REVIEW_PATH = AUTHORIZATION_ROOT / "gate-iv-review.json"
AUTHORIZATION_PATH = AUTHORIZATION_ROOT / "execution-authorization.json"
CONTROL_PATH = AUTHORIZATION_ROOT / "execution-control.json"


class M4AuthorizationContractTests(unittest.TestCase):
    def _snapshot(self) -> dict[str, bytes]:
        return {
            path.name: path.read_bytes()
            for path in sorted(AUTHORIZATION_ROOT.glob("*"))
            if path.is_file()
        }

    def _audit_mutation(self, name: str, mutate) -> dict[str, object]:
        source = AUTHORIZATION_ROOT / name
        value = json.loads(source.read_text(encoding="utf-8"))
        mutate(value)
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            changed = Path(temp_dir) / name
            changed.write_bytes(build.json_bytes(value))
            kwargs = {
                "review_path": REVIEW_PATH,
                "authorization_path": AUTHORIZATION_PATH,
                "control_path": CONTROL_PATH,
            }
            kwargs[
                {
                    "gate-iv-review.json": "review_path",
                    "execution-authorization.json": "authorization_path",
                    "execution-control.json": "control_path",
                }[name]
            ] = changed
            return audit.audit_authorization(
                REPO_ROOT, verify_git=False, **kwargs
            )

    def test_repository_authorization_is_ready_unconsumed_and_read_only(self) -> None:
        before = self._snapshot()
        self.assertFalse((REPO_ROOT / "evals" / "m4" / "results").exists())
        self.assertFalse((REPO_ROOT / "evals" / "m4" / "execution").exists())
        result = audit.audit_authorization(REPO_ROOT)
        self.assertEqual(result["status"], "READY_UNCONSUMED")
        self.assertEqual(result["authorized_task_count"], 60)
        self.assertEqual(result["authorized_batch_count"], 6)
        self.assertEqual(result["existing_result_root_count"], 0)
        self.assertEqual(result["execution_counters"], build.ZERO_COUNTERS)
        self.assertEqual(result["authorization_token_status"], "UNCONSUMED")
        self.assertEqual(result["result_state"], "NOT_RUN")
        self.assertFalse(result["launch_claim_present"])
        self.assertEqual(result["callback_invocations"], 0)
        self.assertEqual(result["network_calls"], 0)
        self.assertEqual(result["side_effects"], [])
        self.assertEqual(result["errors"], [])
        self.assertEqual(self._snapshot(), before)

    def test_generated_artifacts_are_byte_stable(self) -> None:
        expected = build.build_artifacts(REPO_ROOT)
        self.assertEqual(expected[REVIEW_PATH], REVIEW_PATH.read_bytes())
        self.assertEqual(expected[AUTHORIZATION_PATH], AUTHORIZATION_PATH.read_bytes())
        self.assertEqual(expected[CONTROL_PATH], CONTROL_PATH.read_bytes())

    def test_schemas_are_closed_and_have_exact_root_fields(self) -> None:
        pairs = (
            (
                AUTHORIZATION_ROOT / "execution-authorization.schema.json",
                audit.AUTHORIZATION_KEYS,
            ),
            (
                AUTHORIZATION_ROOT / "execution-control.schema.json",
                audit.CONTROL_KEYS,
            ),
        )
        for path, required in pairs:
            value = json.loads(path.read_text(encoding="utf-8"))
            self.assertFalse(value["additionalProperties"])
            self.assertEqual(set(value["required"]), required)
            self.assertEqual(set(value["properties"]), required)

    def test_review_has_zero_findings_and_exact_green_baseline(self) -> None:
        value = json.loads(REVIEW_PATH.read_text(encoding="utf-8"))
        self.assertEqual(value["status"], "PASSED")
        self.assertEqual(value["findings"], [])
        self.assertEqual(value["preparation_head"], build.PREPARATION_HEAD)
        self.assertEqual(value["preparation_ci_run_id"], 31237480839)
        self.assertEqual(value["checks"]["planned_task_count"], 60)
        self.assertEqual(value["checks"]["result_root_count"], 0)

    def test_authorization_binds_model_matrix_and_token(self) -> None:
        value = json.loads(AUTHORIZATION_PATH.read_text(encoding="utf-8"))
        self.assertEqual(value["model_binding"], audit.EXPECTED_MODEL_BINDING)
        self.assertEqual(value["authority"]["authorized_task_count"], 60)
        self.assertEqual(value["authority"]["authorized_batch_count"], 6)
        self.assertEqual(value["prelaunch_counters"], build.ZERO_COUNTERS)
        self.assertEqual(value["authorization_token"], build.authorization_token(value))

    def test_configured_defaults_match_and_drift_fail_closed(self) -> None:
        matched = audit.audit_authorization(
            REPO_ROOT,
            configured_model="gpt-5.6-sol",
            configured_reasoning_effort="max",
        )
        self.assertEqual(matched["status"], "READY_UNCONSUMED")
        self.assertEqual(matched["configured_default_check"], "MATCHED")
        drifted = audit.audit_authorization(
            REPO_ROOT,
            configured_model="gpt-5.6-terra",
            configured_reasoning_effort="high",
            verify_git=False,
        )
        self.assertIn("configured_model_mismatch", drifted["errors"])
        self.assertIn("configured_reasoning_effort_mismatch", drifted["errors"])

    def test_rejects_model_binding_or_token_tampering(self) -> None:
        model = self._audit_mutation(
            "execution-authorization.json",
            lambda value: value["model_binding"].__setitem__(
                "exact_model_id", "gpt-5.6-terra"
            ),
        )
        self.assertIn("model_binding_invalid", model["errors"])
        token = self._audit_mutation(
            "execution-authorization.json",
            lambda value: value.__setitem__(
                "authorization_token", "sha256:" + "0" * 64
            ),
        )
        self.assertIn("authorization_token_invalid", token["errors"])

    def test_rejects_task_batch_or_attempt_drift(self) -> None:
        batch = self._audit_mutation(
            "execution-control.json",
            lambda value: value["batch_order"].reverse(),
        )
        self.assertIn("batch_order_invalid", batch["errors"])
        task = self._audit_mutation(
            "execution-control.json",
            lambda value: value["tasks"][0].__setitem__("attempt_limit", 2),
        )
        self.assertIn("task_attempt_limit_invalid", task["errors"])

    def test_rejects_counter_retry_or_judge_authority(self) -> None:
        counter = self._audit_mutation(
            "execution-authorization.json",
            lambda value: value["prelaunch_counters"].__setitem__("retries", 1),
        )
        self.assertIn("prelaunch_counters_nonzero", counter["errors"])
        retry = self._audit_mutation(
            "execution-authorization.json",
            lambda value: value["authority"].__setitem__(
                "retry_authorized", True
            ),
        )
        self.assertIn("retry_or_repair_authority_forbidden", retry["errors"])
        judge = self._audit_mutation(
            "execution-authorization.json",
            lambda value: value["authority"].__setitem__(
                "judge_execution_authorized", True
            ),
        )
        self.assertIn("judge_authority_forbidden", judge["errors"])

    def test_rejects_launch_claim_or_result_root(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            claim = root / "launch-claim.json"
            claim.write_bytes(b"{}\n")
            result_base = root / "results" / "m4.0"
            (result_base / "M4-ELE-B-A2").mkdir(parents=True)
            result = audit.audit_authorization(
                REPO_ROOT,
                launch_claim_path=claim,
                results_base=result_base,
                verify_git=False,
            )
        self.assertIn("authorization_already_claimed", result["errors"])
        self.assertIn("result_root_present_before_launch", result["errors"])

    def test_rejects_frozen_preparation_git_drift(self) -> None:
        with mock.patch.object(
            audit,
            "_git_snapshot_errors",
            return_value=["frozen_preparation_blob_changed:case.json"],
        ):
            result = audit.audit_authorization(REPO_ROOT)
        self.assertIn(
            "frozen_preparation_blob_changed:case.json", result["errors"]
        )

    def test_auditor_source_has_no_network_or_task_creation(self) -> None:
        source = (AUTHORIZATION_ROOT / "audit_authorization.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("create_thread(", source)
        self.assertNotIn("urlopen(", source)
        self.assertNotIn("requests.", source)


if __name__ == "__main__":
    unittest.main()
