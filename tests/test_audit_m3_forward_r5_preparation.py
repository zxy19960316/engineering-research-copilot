from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "evals" / "m3"))

import audit_forward_r5_preparation as audit  # noqa: E402
from r5_dispatch_contract import CASE_IDS, COUNTER_KEYS, R5_SCHEMA_VERSION, canonical_future_paths  # noqa: E402


SOURCE = REPO_ROOT / "evals" / "m3" / "forward-inputs-r2" / "m3-f03-approved-change.bundle.json"
R4_MANIFEST = REPO_ROOT / "evals" / "m3" / "results" / "forward-r4" / "acceptance-manifest.json"


class AuditM3ForwardR5PreparationTests(unittest.TestCase):
    def _sha256(self, path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def _write_json(self, path: Path, value: object) -> None:
        path.write_text(
            json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
            newline="\n",
        )

    def _manifest(self, root: Path) -> tuple[Path, Path]:
        result_root = root / "forward-r5"
        result_root.mkdir()
        prompt = root / "prompt.txt"
        prompt.write_text("frozen r5 prompt\n", encoding="utf-8", newline="\n")
        contract = root / "contract.json"
        self._write_json(contract, {"type": "object", "additionalProperties": False})
        validation = root / "m2-validation.json"
        self._write_json(validation, {"status": "valid", "errors": [], "evidence_gaps": []})
        eligibility = root / "eligibility.json"
        self._write_json(eligibility, {"status": "eligible", "errors": [], "evidence_gaps": []})
        cases = []
        for case_id in CASE_IDS:
            cases.append(
                {
                    "case_id": case_id,
                    "input_path": "evals/m3/forward-inputs-r2/m3-f03-approved-change.bundle.json",
                    "input_raw_sha256": self._sha256(SOURCE),
                    "prompt_path": prompt.relative_to(REPO_ROOT).as_posix(),
                    "prompt_raw_sha256": self._sha256(prompt),
                    "contract_path": contract.relative_to(REPO_ROOT).as_posix(),
                    "contract_raw_sha256": self._sha256(contract),
                    "m2_validation_path": validation.relative_to(REPO_ROOT).as_posix(),
                    "m2_validation_raw_sha256": self._sha256(validation),
                    "eligibility_path": eligibility.relative_to(REPO_ROOT).as_posix(),
                    "eligibility_raw_sha256": self._sha256(eligibility),
                    "eligibility_status": "eligible",
                    "future_paths": canonical_future_paths(case_id, result_root),
                }
            )
        manifest = {
            "schema_version": R5_SCHEMA_VERSION,
            "status": "ready_for_authorized_fresh_contexts",
            "prompts_frozen": True,
            "result_root": result_root.relative_to(REPO_ROOT).as_posix(),
            "counters": {key: 0 for key in COUNTER_KEYS},
            "historical_r4": {
                "path": R4_MANIFEST.relative_to(REPO_ROOT).as_posix(),
                "raw_sha256": self._sha256(R4_MANIFEST),
                "status": "blocked_not_accepted",
                "count_as_r5": False,
            },
            "cases": cases,
        }
        path = root / "acceptance-manifest.json"
        self._write_json(path, manifest)
        return path, result_root

    def _audit(self, manifest_path: Path, result_root: Path) -> dict:
        with mock.patch.object(audit, "R5_RESULT_ROOT", result_root):
            return audit.audit_preparation(manifest_path)

    def test_accepts_five_eligible_cases_after_batch_dry_preflight(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            manifest_path, result_root = self._manifest(Path(temp_dir))
            before = manifest_path.read_bytes()
            with (
                mock.patch.object(audit, "R5_RESULT_ROOT", result_root),
                mock.patch.object(audit, "preflight_batch", wraps=audit.preflight_batch) as preflight_mock,
            ):
                result = audit.audit_preparation(manifest_path)
                after = manifest_path.read_bytes()

        self.assertEqual(result["status"], "valid")
        self.assertEqual(len(result["cases"]), 5)
        self.assertEqual(result["batch_preflight"]["status"], "valid")
        self.assertEqual(result["batch_preflight"]["case_ids_preflighted"], list(CASE_IDS))
        self.assertEqual(result["batch_preflight"]["side_effects"], [])
        self.assertEqual(preflight_mock.call_count, 1)
        self.assertEqual(after, before)

    def test_missing_validator_receipt_or_alias_is_blocked_before_any_callback(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            manifest_path, result_root = self._manifest(root)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            paths = manifest["cases"][0]["future_paths"]
            paths["receipt_validator_receipt_json"] = paths.pop("validator_receipt_json")
            self._write_json(manifest_path, manifest)
            result = self._audit(manifest_path, result_root)

        self.assertEqual(result["status"], "invalid")
        self.assertIn("future_path_keys_missing:validator_receipt_json", result["errors"])
        self.assertIn("future_path_keys_unknown:receipt_validator_receipt_json", result["errors"])
        self.assertEqual(result["batch_preflight"]["side_effects"], [])

    def test_rejects_duplicate_absolute_escape_and_existing_paths(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            manifest_path, result_root = self._manifest(root)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["cases"][1]["future_paths"]["outcome_json"] = manifest["cases"][0]["future_paths"]["outcome_json"]
            manifest["cases"][2]["future_paths"]["validation_json"] = "C:/outside.json"
            manifest["cases"][3]["future_paths"]["context_finalization_json"] = "../escape.json"
            (result_root / "m3-f05.outcome.json").write_text("sentinel\n", encoding="utf-8", newline="\n")
            self._write_json(manifest_path, manifest)
            result = self._audit(manifest_path, result_root)

        self.assertEqual(result["status"], "invalid")
        self.assertTrue(any(code.startswith("future_path_duplicate:") for code in result["errors"]))
        self.assertIn("future_path_unsafe:validation_json", result["errors"])
        self.assertIn("future_path_unsafe:context_finalization_json", result["errors"])
        self.assertIn("future_path_exists:outcome_json", result["errors"])

    def test_rejects_nonzero_counter_ineligible_case_and_f03_alias(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            manifest_path, result_root = self._manifest(root)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["counters"]["task_finalizations_observed"] = 1
            manifest["cases"][0]["eligibility_status"] = "not_run"
            manifest["cases"][2]["input_path"] = "evals/m3/forward-inputs-r2/m3-f02-route-compatible.bundle.json"
            self._write_json(manifest_path, manifest)
            result = self._audit(manifest_path, result_root)

        self.assertEqual(result["status"], "invalid")
        self.assertIn("manifest_counter_nonzero:task_finalizations_observed", result["errors"])
        self.assertIn("case_not_eligible", result["errors"])
        self.assertIn("f03_source_alias_forbidden", result["errors"])

    def test_missing_source_or_hash_is_blocked_without_writing_result_artifacts(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            manifest_path, result_root = self._manifest(root)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["cases"][0]["input_path"] = "evals/m3/does-not-exist-r5.json"
            manifest["cases"][1]["prompt_raw_sha256"] = "0" * 64
            before = {path.name: path.read_bytes() for path in result_root.iterdir()}
            self._write_json(manifest_path, manifest)
            result = self._audit(manifest_path, result_root)
            after = {path.name: path.read_bytes() for path in result_root.iterdir()}

        self.assertEqual(result["status"], "invalid")
        self.assertIn("source_input_missing", result["errors"])
        self.assertIn("prompt_sha256_mismatch", result["errors"])
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
