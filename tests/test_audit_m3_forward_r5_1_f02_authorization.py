from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "evals" / "m3"))

import audit_forward_r5_1_f02_authorization as audit  # noqa: E402


MANIFEST = (
    REPO_ROOT
    / "evals"
    / "m3"
    / "forward-inputs-r5.1-f02"
    / "authorization-manifest.json"
)


class AuditM3ForwardR51F02AuthorizationTests(unittest.TestCase):
    def _write_manifest(self, root: Path, mutate) -> Path:
        value = json.loads(MANIFEST.read_text(encoding="utf-8"))
        mutate(value)
        path = root / "authorization-manifest.json"
        path.write_text(
            json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
        return path

    def _mutated(self, mutate) -> dict:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            path = self._write_manifest(Path(temp_dir), mutate)
            return audit.audit_authorization(path)

    def test_frozen_valid_preparation_is_ready_without_authorizing_a_run(self):
        with (
            mock.patch.object(audit, "_check_result_root", return_value=0),
            mock.patch.object(audit, "validate_future_paths", return_value=[]),
            mock.patch.object(
                audit,
                "audit_preparation",
                return_value={"status": "ready_for_fresh_authorization"},
            ),
        ):
            result = audit.audit_authorization(MANIFEST)

        self.assertEqual(result["status"], "ready_for_fresh_authorization")
        self.assertEqual(result["case_id"], "m3-f02")
        self.assertEqual(result["revision"], "r5.1-f02")
        self.assertFalse(result["new_fresh_run_authorized"])
        self.assertIsNone(result["reserved_task_id"])
        self.assertEqual(result["result_artifact_count"], 0)
        self.assertEqual(result["side_effects"], [])
        self.assertEqual(result["errors"], [])

    def test_preparation_baseline_sha_drift_is_invalid(self):
        result = self._mutated(
            lambda value: value.__setitem__("preparation_baseline_head", "0" * 40)
        )
        self.assertIn("preparation_baseline_head_drift", result["errors"])

    def test_historical_evidence_head_drift_is_invalid(self):
        result = self._mutated(
            lambda value: value.__setitem__("historical_evidence_head", "0" * 40)
        )
        self.assertIn("historical_evidence_head_drift", result["errors"])

    def test_forward_r5_tree_drift_is_invalid(self):
        with mock.patch.object(audit, "_r5_evidence_tree_clean", return_value=False):
            result = audit.audit_authorization(MANIFEST)
        self.assertIn("immutable_r5_evidence_changed", result["errors"])

    def test_source_input_raw_hash_drift_is_invalid(self):
        result = self._mutated(
            lambda value: value["source_input"].__setitem__("raw_sha256", "0" * 64)
        )
        self.assertIn("source_input_raw_sha256_mismatch", result["errors"])

    def test_source_input_canonical_hash_drift_is_invalid(self):
        result = self._mutated(
            lambda value: value["source_input"].__setitem__("canonical_sha256", "0" * 64)
        )
        self.assertIn("source_input_canonical_sha256_mismatch", result["errors"])

    def test_source_input_git_blob_drift_is_invalid(self):
        result = self._mutated(
            lambda value: value["source_input"].__setitem__("git_blob_oid", "0" * 40)
        )
        self.assertIn("source_input_git_blob_oid_mismatch", result["errors"])

    def test_prompt_drift_is_invalid(self):
        result = self._mutated(
            lambda value: value["prompt"].__setitem__("raw_sha256", "0" * 64)
        )
        self.assertIn("prompt_raw_sha256_mismatch", result["errors"])

    def test_replacement_contract_drift_is_invalid(self):
        result = self._mutated(
            lambda value: value["replacement_contract"].__setitem__(
                "canonical_sha256", "0" * 64
            )
        )
        self.assertIn("replacement_contract_canonical_sha256_mismatch", result["errors"])

    def test_base_contract_binding_checks_path_oid_raw_and_canonical_hashes(self):
        replacements = {
            "path": "evals/m3/forward-inputs-r5/not-the-contract.json",
            "git_blob_oid": "0" * 40,
            "raw_sha256": "0" * 64,
            "canonical_sha256": "0" * 64,
        }
        expected_codes = {
            "path": "base_contract_path_mismatch",
            "git_blob_oid": "base_contract_git_blob_oid_mismatch",
            "raw_sha256": "base_contract_raw_sha256_mismatch",
            "canonical_sha256": "base_contract_canonical_sha256_mismatch",
        }
        for field, replacement in replacements.items():
            with self.subTest(field=field):
                result = self._mutated(
                    lambda value, field=field, replacement=replacement: value[
                        "base_contract"
                    ].__setitem__(field, replacement)
                )
                self.assertIn(expected_codes[field], result["errors"])

    def test_route_authority_hash_drift_is_invalid(self):
        result = self._mutated(
            lambda value: value["route_condition_authority"].__setitem__(
                "canonical_sha256", "0" * 64
            )
        )
        self.assertIn("route_condition_authority_sha256_mismatch", result["errors"])

    def test_m2_validation_not_valid_is_invalid(self):
        result = self._mutated(
            lambda value: value["m2_validation"].__setitem__(
                "required_status", "invalid"
            )
        )
        self.assertIn("m2_validation_required_status_invalid", result["errors"])

    def test_eligibility_not_eligible_is_invalid(self):
        result = self._mutated(
            lambda value: value["eligibility"].__setitem__(
                "required_status", "not_run"
            )
        )
        self.assertIn("eligibility_required_status_invalid", result["errors"])

    def test_historical_f02_task_reuse_is_invalid(self):
        result = self._mutated(
            lambda value: value.__setitem__(
                "reserved_task_id", audit.HISTORICAL_TASK_ID
            )
        )
        self.assertIn("historical_task_id_reuse_forbidden", result["errors"])

    def test_historical_result_root_reuse_is_invalid(self):
        result = self._mutated(
            lambda value: value.__setitem__(
                "result_root", "evals/m3/results/forward-r5"
            )
        )
        self.assertIn("historical_result_root_reuse_forbidden", result["errors"])

    def test_nonempty_replacement_result_root_is_invalid(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            result_root = Path(temp_dir) / "forward-r5.1-f02"
            result_root.mkdir()
            (result_root / ".gitkeep").write_bytes(b"")
            (result_root / "m3-f02.model-final.json").write_text(
                "{}\n", encoding="utf-8", newline="\n"
            )

            def mutate(value: dict) -> None:
                value["result_root"] = result_root.relative_to(REPO_ROOT).as_posix()

            manifest = self._write_manifest(Path(temp_dir), mutate)
            with mock.patch.object(audit, "RESULT_ROOT", result_root):
                result = audit.audit_authorization(manifest)

        self.assertEqual(result["result_artifact_count"], 1)
        self.assertIn("result_root_not_empty", result["errors"])

    def test_nonzero_preparation_counter_is_invalid(self):
        result = self._mutated(
            lambda value: value["counters"].__setitem__("tasks_launched", 1)
        )
        self.assertIn("authorization_counter_nonzero:tasks_launched", result["errors"])

    def test_unsafe_future_path_is_invalid(self):
        result = self._mutated(
            lambda value: value["future_paths"].__setitem__(
                "model_final_json", "../m3-f02.model-final.json"
            )
        )
        self.assertIn("future_path_unsafe:model_final_json", result["errors"])

    def test_authorization_auditor_has_zero_side_effects(self):
        before_manifest = MANIFEST.read_bytes()
        before_root = {
            path.name: path.read_bytes() for path in audit.RESULT_ROOT.iterdir()
        }
        first = audit.audit_authorization(MANIFEST)
        second = audit.audit_authorization(MANIFEST)
        after_root = {
            path.name: path.read_bytes() for path in audit.RESULT_ROOT.iterdir()
        }

        self.assertEqual(first, second)
        self.assertEqual(MANIFEST.read_bytes(), before_manifest)
        self.assertEqual(after_root, before_root)
        self.assertEqual(first["side_effects"], [])


if __name__ == "__main__":
    unittest.main()
