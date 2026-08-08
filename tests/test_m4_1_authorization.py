from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
AUTHORIZATION_ROOT = REPO_ROOT / "evals" / "m4" / "authorization"
M4_1_ROOT = AUTHORIZATION_ROOT / "m4.1"
M4_ROOT = REPO_ROOT / "evals" / "m4"
sys.path.insert(0, str(AUTHORIZATION_ROOT))
sys.path.insert(0, str(M4_ROOT))

import audit_m4_1_authorization as audit  # noqa: E402
import audit_m4_1_preparation as preparation_audit  # noqa: E402
import build_m4_1_authorization as build  # noqa: E402


REVIEW_PATH = M4_1_ROOT / "gate-iv-review.json"
AUTHORIZATION_PATH = M4_1_ROOT / "execution-authorization.json"
CONTROL_PATH = M4_1_ROOT / "execution-control.json"


class M41AuthorizationAuditTests(unittest.TestCase):
    def _snapshot(self) -> dict[str, bytes]:
        paths = (
            REVIEW_PATH,
            AUTHORIZATION_PATH,
            CONTROL_PATH,
            build.PREPARATION_PATH,
            REPO_ROOT / build.HELPER_RELATIVE,
            REPO_ROOT / preparation_audit.M4_0_CLAIM_RELATIVE,
            REPO_ROOT / preparation_audit.M4_0_FAILURE_RELATIVE,
        )
        return {path.as_posix(): path.read_bytes() for path in paths}

    def _audit_mutation(self, name: str, mutate) -> dict[str, object]:
        source = M4_1_ROOT / name
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
                REPO_ROOT,
                configured_model=build.MODEL_ID,
                configured_reasoning_effort=build.REASONING_EFFORT,
                verify_git=False,
                **kwargs,
            )

    def _audit_coherent_review_rewrite(self) -> dict[str, object]:
        review = json.loads(REVIEW_PATH.read_text(encoding="utf-8"))
        authorization = json.loads(AUTHORIZATION_PATH.read_text(encoding="utf-8"))
        control = json.loads(CONTROL_PATH.read_text(encoding="utf-8"))
        review["limitations"].append("coherent rewrite")
        review_raw = build.json_bytes(review)
        review_blob = subprocess.run(
            ["git", "hash-object", "--stdin"],
            cwd=REPO_ROOT,
            input=review_raw,
            capture_output=True,
            check=True,
        ).stdout.decode("ascii").strip()
        authorization["review"]["raw_sha256"] = build.sha256(review_raw)
        authorization["review"]["git_blob_oid"] = review_blob
        authorization["authorization_token"] = build.authorization_token(authorization)
        authorization_raw = build.json_bytes(authorization)
        control["authorization"]["raw_sha256"] = build.sha256(authorization_raw)
        control["authorization"]["authorization_token"] = authorization[
            "authorization_token"
        ]
        control_raw = build.json_bytes(control)
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            review_path = root / REVIEW_PATH.name
            authorization_path = root / AUTHORIZATION_PATH.name
            control_path = root / CONTROL_PATH.name
            review_path.write_bytes(review_raw)
            authorization_path.write_bytes(authorization_raw)
            control_path.write_bytes(control_raw)
            return audit.audit_authorization(
                REPO_ROOT,
                review_path=review_path,
                authorization_path=authorization_path,
                control_path=control_path,
                configured_model=build.MODEL_ID,
                configured_reasoning_effort=build.REASONING_EFFORT,
                verify_git=False,
            )

    def test_repository_authorization_is_ready_unconsumed_and_read_only(self) -> None:
        before = self._snapshot()
        self.assertFalse((REPO_ROOT / "evals/m4/results").exists())
        self.assertFalse((REPO_ROOT / build.LAUNCH_CLAIM_RELATIVE).exists())
        result = audit.audit_authorization(
            REPO_ROOT,
            configured_model="gpt-5.6-sol",
            configured_reasoning_effort="max",
        )
        self.assertEqual(result["status"], "READY_UNCONSUMED")
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["review_status"], "PASSED")
        self.assertEqual(result["configured_default_check"], "MATCHED")
        self.assertEqual(result["authorized_task_count"], 60)
        self.assertEqual(result["authorized_batch_count"], 6)
        self.assertEqual(result["request_binding_count"], 60)
        self.assertEqual(result["execution_counters"], build.ZERO_COUNTERS)
        self.assertEqual(result["authorization_token_status"], "UNCONSUMED")
        self.assertEqual(result["existing_result_root_count"], 0)
        self.assertFalse(result["results_parent_present"])
        self.assertFalse(result["launch_claim_present"])
        self.assertEqual(result["result_state"], "NOT_RUN")
        self.assertEqual(result["callback_invocations"], 0)
        self.assertEqual(result["network_calls"], 0)
        self.assertEqual(result["side_effects"], [])
        self.assertEqual(self._snapshot(), before)

    def test_review_requires_zero_findings_exact_decision_and_green_baseline(self) -> None:
        status = self._audit_mutation(
            "gate-iv-review.json", lambda value: value.__setitem__("status", "BLOCKED")
        )
        self.assertIn("review_field_invalid:status", status["errors"])
        findings = self._audit_mutation(
            "gate-iv-review.json",
            lambda value: value["findings"].append({"severity": "blocking"}),
        )
        self.assertIn("review_findings_nonempty", findings["errors"])
        decision = self._audit_mutation(
            "gate-iv-review.json",
            lambda value: value.__setitem__("decision", "DO_NOT_AUTHORIZE"),
        )
        self.assertIn("review_field_invalid:decision", decision["errors"])
        head = self._audit_mutation(
            "gate-iv-review.json",
            lambda value: value.__setitem__("preparation_head", "0" * 40),
        )
        self.assertIn("review_field_invalid:preparation_head", head["errors"])
        run = self._audit_mutation(
            "gate-iv-review.json",
            lambda value: value.__setitem__("preparation_ci_run_id", 0),
        )
        self.assertIn("review_field_invalid:preparation_ci_run_id", run["errors"])

    def test_coherent_review_and_authorization_rewrite_still_fails_closed(self) -> None:
        result = self._audit_coherent_review_rewrite()
        self.assertEqual(result["status"], "INVALID")
        self.assertIn("review_raw_sha256_mismatch", result["errors"])
        self.assertIn("authorization_regeneration_mismatch", result["errors"])

    def test_review_commit_and_schema_source_snapshots_are_exact(self) -> None:
        self.assertEqual(audit._review_snapshot_errors(REPO_ROOT), [])
        self.assertEqual(audit._schema_snapshot_errors(REPO_ROOT), [])

    def test_nested_schema_drift_is_rejected_by_raw_hash(self) -> None:
        schema = json.loads(
            audit.AUTHORIZATION_SCHEMA_PATH.read_text(encoding="utf-8")
        )
        schema["properties"]["authority"]["description"] = "nested drift"
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            changed = Path(temp_dir) / "execution-authorization.schema.json"
            changed.write_bytes(build.json_bytes(schema))
            self.assertEqual(
                audit._schema_errors(
                    changed, audit.AUTHORIZATION_KEYS, "authorization_schema"
                ),
                [],
            )
            errors = audit._schema_snapshot_errors(
                REPO_ROOT,
                authorization_schema_path=changed,
                verify_git=False,
            )
        self.assertIn("authorization_schema_raw_sha256_mismatch", errors)

    def test_rejects_token_model_or_helper_binding_tampering(self) -> None:
        token = self._audit_mutation(
            "execution-authorization.json",
            lambda value: value.__setitem__(
                "authorization_token", "sha256:" + "0" * 64
            ),
        )
        self.assertIn("authorization_token_invalid", token["errors"])
        model = self._audit_mutation(
            "execution-authorization.json",
            lambda value: value["model_binding"].__setitem__(
                "exact_model_id", "gpt-5.6-terra"
            ),
        )
        self.assertIn("model_binding_invalid", model["errors"])
        helper = self._audit_mutation(
            "execution-control.json",
            lambda value: value["execution_helper"].__setitem__(
                "raw_sha256", "0" * 64
            ),
        )
        self.assertIn("execution_helper_reference_invalid", helper["errors"])

    def test_rejects_roster_order_request_binding_or_attempt_drift(self) -> None:
        roster = self._audit_mutation(
            "execution-authorization.json",
            lambda value: value["authority"]["authorized_task_ids"].reverse(),
        )
        self.assertIn("authorized_task_ids_invalid", roster["errors"])
        order = self._audit_mutation(
            "execution-control.json", lambda value: value["batch_order"].reverse()
        )
        self.assertIn("batch_order_invalid", order["errors"])
        binding = self._audit_mutation(
            "execution-control.json",
            lambda value: value["tasks"][0].__setitem__(
                "request_binding_sha256", "0" * 64
            ),
        )
        self.assertIn("request_binding_mismatch", binding["errors"])
        attempt = self._audit_mutation(
            "execution-control.json",
            lambda value: value["tasks"][0].__setitem__("attempt_limit", 2),
        )
        self.assertIn("task_attempt_limit_invalid", attempt["errors"])

    def test_rejects_nonzero_counters_and_every_later_gate(self) -> None:
        counter = self._audit_mutation(
            "execution-authorization.json",
            lambda value: value["prelaunch_counters"].__setitem__(
                "created_contexts", 1
            ),
        )
        self.assertIn("prelaunch_counters_nonzero", counter["errors"])
        retry = self._audit_mutation(
            "execution-authorization.json",
            lambda value: value["authority"].__setitem__("retry_authorized", True),
        )
        self.assertIn("retry_or_repair_authority_forbidden", retry["errors"])
        followup = self._audit_mutation(
            "execution-authorization.json",
            lambda value: value["authority"].__setitem__(
                "followup_message_authorized", True
            ),
        )
        self.assertIn("followup_authority_forbidden", followup["errors"])
        for permission in (
            "judge_execution",
            "blind_mapping_access",
            "aggregation",
            "threshold_claim",
            "m4_closure",
        ):
            with self.subTest(permission=permission):
                result = self._audit_mutation(
                    "execution-control.json",
                    lambda value, key=permission: value["permissions"].__setitem__(
                        key, True
                    ),
                )
                self.assertIn("control_permissions_invalid", result["errors"])

    def test_empty_results_parent_or_launch_claim_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            results_parent = root / "results"
            results_parent.mkdir()
            claim = root / "launch-claim.json"
            claim.write_bytes(b"{}\n")
            result = audit.audit_authorization(
                REPO_ROOT,
                launch_claim_path=claim,
                results_parent=results_parent,
                configured_model=build.MODEL_ID,
                configured_reasoning_effort=build.REASONING_EFFORT,
                verify_git=False,
            )
        self.assertEqual(result["status"], "INVALID")
        self.assertIn("authorization_already_claimed", result["errors"])
        self.assertIn("results_parent_present_before_launch", result["errors"])
        self.assertTrue(result["launch_claim_present"])
        self.assertTrue(result["results_parent_present"])

    def test_configured_defaults_match_and_drift_fails_closed(self) -> None:
        matched = audit.audit_authorization(
            REPO_ROOT,
            configured_model="gpt-5.6-sol",
            configured_reasoning_effort="max",
            verify_git=False,
        )
        self.assertEqual(matched["configured_default_check"], "MATCHED")
        drifted = audit.audit_authorization(
            REPO_ROOT,
            configured_model="gpt-5.6-terra",
            configured_reasoning_effort="high",
            verify_git=False,
        )
        self.assertIn("configured_model_mismatch", drifted["errors"])
        self.assertIn("configured_reasoning_effort_mismatch", drifted["errors"])
        self.assertEqual(drifted["configured_default_check"], "MISMATCH")

    def test_m4_0_raw_sha_blobs_and_diff_locks_are_rechecked(self) -> None:
        self.assertEqual(audit._m4_0_evidence_errors(REPO_ROOT), [])
        pairs = (
            (
                preparation_audit.M4_0_CLAIM_RELATIVE,
                preparation_audit.CLAIM_SHA256,
                preparation_audit.CLAIM_BLOB_OID,
            ),
            (
                preparation_audit.M4_0_FAILURE_RELATIVE,
                preparation_audit.FAILURE_SHA256,
                preparation_audit.FAILURE_BLOB_OID,
            ),
        )
        for relative, expected_sha, expected_blob in pairs:
            raw = (REPO_ROOT / relative).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), expected_sha)
            for revision in ("HEAD", preparation_audit.TERMINAL_HEAD):
                actual_blob = subprocess.run(
                    ["git", "rev-parse", f"{revision}:{relative.as_posix()}"],
                    cwd=REPO_ROOT,
                    capture_output=True,
                    text=True,
                    check=True,
                ).stdout.strip()
                self.assertEqual(actual_blob, expected_blob)

    def test_rejects_frozen_preparation_git_drift(self) -> None:
        with mock.patch.object(
            audit,
            "_git_snapshot_errors",
            return_value=["frozen_preparation_blob_changed:manifest.json"],
        ):
            result = audit.audit_authorization(REPO_ROOT)
        self.assertIn(
            "frozen_preparation_blob_changed:manifest.json", result["errors"]
        )

    def test_auditor_source_has_no_network_task_creation_or_writes(self) -> None:
        source = (AUTHORIZATION_ROOT / "audit_m4_1_authorization.py").read_text(
            encoding="utf-8"
        )
        for forbidden in (
            "create_thread(",
            "urlopen(",
            "requests.",
            ".write_bytes(",
            ".write_text(",
            ".mkdir(",
            "os.replace(",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
