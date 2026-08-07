from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "evals" / "m3"))

import audit_forward_r5_1_f02_execution_authorization as audit  # noqa: E402


AUTHORIZATION = (
    REPO_ROOT
    / "evals"
    / "m3"
    / "forward-inputs-r5.1-f02"
    / "execution-authorization.json"
)


class AuditM3ForwardR51F02ExecutionAuthorizationTests(unittest.TestCase):
    def _mutated(self, mutate) -> dict:
        value = json.loads(AUTHORIZATION.read_text(encoding="utf-8"))
        mutate(value)
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            path = Path(temp_dir) / "execution-authorization.json"
            path.write_text(
                json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                + "\n",
                encoding="utf-8",
                newline="\n",
            )
            return audit.audit_execution_authorization(path)

    def test_frozen_execution_authorization_is_ready_without_side_effects(self):
        result = audit.audit_execution_authorization(AUTHORIZATION)
        self.assertEqual(result["status"], "ready_for_one_shot_fresh_execution")
        self.assertEqual(result["case_id"], "m3-f02")
        self.assertEqual(result["revision"], "r5.1-f02")
        self.assertEqual(result["max_fresh_tasks"], 1)
        self.assertIsNone(result["reserved_task_id"])
        self.assertEqual(result["result_artifact_count"], 0)
        self.assertEqual(result["historical_f02_retry_count"], 0)
        self.assertEqual(result["callback_invocations"], 0)
        self.assertEqual(result["side_effects"], [])
        self.assertEqual(result["errors"], [])

    def test_wrong_readiness_head_and_ci_run_are_invalid(self):
        mutations = {
            "readiness_head": "0" * 40,
            "readiness_ci_run_id": 1,
        }
        for field, replacement in mutations.items():
            with self.subTest(field=field):
                result = self._mutated(
                    lambda value, field=field, replacement=replacement: value.__setitem__(
                        field, replacement
                    )
                )
                self.assertEqual(result["status"], "invalid")
                self.assertTrue(
                    any(field in error for error in result["errors"]), result["errors"]
                )

    def test_readiness_manifest_identity_drift_is_invalid(self):
        expected = {
            "git_blob_oid": "readiness_manifest_git_blob_oid_mismatch",
            "raw_sha256": "readiness_manifest_raw_sha256_mismatch",
            "canonical_sha256": "readiness_manifest_canonical_sha256_mismatch",
        }
        for field, code in expected.items():
            with self.subTest(field=field):
                replacement = "0" * (40 if field == "git_blob_oid" else 64)
                result = self._mutated(
                    lambda value, field=field, replacement=replacement: value[
                        "readiness_authorization_manifest"
                    ].__setitem__(field, replacement)
                )
                self.assertIn(code, result["errors"])

    def test_each_predecessor_binding_drift_is_invalid(self):
        fields = {
            "preparation_manifest": "raw_sha256",
            "input_binding": "canonical_sha256",
            "source_input": "git_blob_oid",
            "prompt": "raw_sha256",
            "replacement_contract": "canonical_sha256",
            "base_contract": "git_blob_oid",
            "m2_validation": "required_status",
            "eligibility": "required_status",
            "supersession_policy": "policy",
            "route_condition_authority": "canonical_sha256",
        }
        for binding, field in fields.items():
            with self.subTest(binding=binding):
                result = self._mutated(
                    lambda value, binding=binding, field=field: value["bindings"][
                        binding
                    ].__setitem__(field, "drift")
                )
                self.assertIn(f"readiness_binding_drift:{binding}", result["errors"])

    def test_launch_contract_identity_drift_is_invalid(self):
        result = self._mutated(
            lambda value: value["launch_contract"].__setitem__("raw_sha256", "0" * 64)
        )
        self.assertIn("launch_contract_raw_sha256_mismatch", result["errors"])

    def test_nonzero_readiness_or_execution_counter_is_invalid(self):
        result = self._mutated(
            lambda value: value["counters"].__setitem__("tasks_launched", 1)
        )
        self.assertIn(
            "execution_authorization_counter_nonzero:tasks_launched", result["errors"]
        )
        predecessor = audit.readiness_audit(audit.READINESS_MANIFEST)
        predecessor["status"] = "invalid"
        predecessor["counters"]["tasks_launched"] = 1
        with mock.patch.object(audit, "readiness_audit", return_value=predecessor):
            result = audit.audit_execution_authorization(AUTHORIZATION)
        self.assertIn("readiness_audit_not_ready", result["errors"])

    def test_nonempty_replacement_root_or_r5_drift_is_invalid(self):
        predecessor = audit.readiness_audit(audit.READINESS_MANIFEST)
        predecessor["status"] = "invalid"
        predecessor["result_artifact_count"] = 1
        predecessor["errors"] = ["result_root_not_empty", "immutable_r5_evidence_changed"]
        with mock.patch.object(audit, "readiness_audit", return_value=predecessor):
            result = audit.audit_execution_authorization(AUTHORIZATION)
        self.assertIn("readiness_audit_not_ready", result["errors"])
        self.assertIn("readiness_result_root_not_empty", result["errors"])
        self.assertIn("immutable_r5_evidence_changed", result["errors"])

    def test_every_unsafe_permission_is_invalid(self):
        for field in (
            "retry_allowed",
            "repair_allowed",
            "second_finalization_allowed",
            "historical_task_reuse_allowed",
            "cross_revision_aggregation_authorized",
            "m3_closure_authorized",
            "m4_authorized",
        ):
            with self.subTest(field=field):
                result = self._mutated(
                    lambda value, field=field: value.__setitem__(field, True)
                )
                self.assertIn(
                    f"execution_authorization_field_invalid:{field}", result["errors"]
                )

    def test_auditor_is_repeatable_and_read_only(self):
        before_auth = AUTHORIZATION.read_bytes()
        before_root = {
            path.name: path.read_bytes() for path in audit.RESULT_ROOT.iterdir()
        }
        first = audit.audit_execution_authorization(AUTHORIZATION)
        second = audit.audit_execution_authorization(AUTHORIZATION)
        after_root = {
            path.name: path.read_bytes() for path in audit.RESULT_ROOT.iterdir()
        }
        self.assertEqual(first, second)
        self.assertEqual(AUTHORIZATION.read_bytes(), before_auth)
        self.assertEqual(after_root, before_root)
        self.assertEqual(first["side_effects"], [])


if __name__ == "__main__":
    unittest.main()
