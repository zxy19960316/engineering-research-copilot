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

from audit_forward_r4_preparation import audit_preparation  # noqa: E402


SOURCE = REPO_ROOT / "evals" / "m3" / "forward-inputs-r2" / "m3-f03-approved-change.bundle.json"


class AuditForwardR4PreparationTests(unittest.TestCase):
    def _sha256(self, path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def _manifest(self, root: Path) -> tuple[Path, Path]:
        result_root = root / "forward-r4"
        result_root.mkdir()
        prompt = root / "prompt.txt"
        prompt.write_text("prompt\n", encoding="utf-8", newline="\n")
        contract = root / "contract.json"
        contract.write_text('{"type":"object"}\n', encoding="utf-8", newline="\n")
        cases = []
        for case_id in ("m3-f01", "m3-f02", "m3-f03", "m3-f04", "m3-f05"):
            cases.append(
                {
                    "case_id": case_id,
                    "input_path": "evals/m3/forward-inputs-r2/m3-f03-approved-change.bundle.json",
                    "input_raw_sha256": self._sha256(SOURCE),
                    "prompt_path": prompt.relative_to(REPO_ROOT).as_posix(),
                    "prompt_raw_sha256": self._sha256(prompt),
                    "contract_path": contract.relative_to(REPO_ROOT).as_posix(),
                    "contract_raw_sha256": self._sha256(contract),
                    "eligibility_status": "eligible",
                }
            )
        manifest = {
            "schema_version": "m3.1-forward-acceptance-r4-v1",
            "status": "ready_for_authorized_fresh_contexts",
            "prompts_frozen": True,
            "fresh_contexts_consumed": 0,
            "cases": cases,
        }
        path = root / "acceptance-manifest.json"
        path.write_text(
            json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        return path, result_root

    def test_accepts_five_frozen_eligible_cases_without_result_paths(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            manifest_path, result_root = self._manifest(Path(temp_dir))
            with mock.patch("audit_forward_r4_preparation.R4_RESULT_ROOT", result_root):
                result = audit_preparation(manifest_path)
            self.assertEqual(result["status"], "valid")
            self.assertEqual(len(result["cases"]), 5)
            self.assertTrue(result["prompts_frozen"])
            self.assertEqual(result["fresh_contexts_consumed"], 0)

    def test_rejects_output_or_receipt_fields_in_manifest(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            manifest_path, result_root = self._manifest(Path(temp_dir))
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["cases"][0]["output_path"] = "evals/m3/results/forward-r4/m3-f01.outcome.json"
            manifest_path.write_text(
                json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            with mock.patch("audit_forward_r4_preparation.R4_RESULT_ROOT", result_root):
                result = audit_preparation(manifest_path)
            self.assertEqual(result["status"], "invalid")
            self.assertIn("output_or_receipt_fields_forbidden", result["errors"])

    def test_rejects_nonzero_consumed_count_and_ineligible_case(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            manifest_path, result_root = self._manifest(Path(temp_dir))
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["fresh_contexts_consumed"] = 1
            manifest["cases"][2]["eligibility_status"] = "not_run"
            manifest_path.write_text(
                json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            with mock.patch("audit_forward_r4_preparation.R4_RESULT_ROOT", result_root):
                result = audit_preparation(manifest_path)
            self.assertEqual(result["status"], "invalid")
            self.assertIn("fresh_contexts_nonzero", result["errors"])
            self.assertIn("case_not_eligible", result["errors"])

    def test_rejects_present_future_result_path(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            manifest_path, result_root = self._manifest(Path(temp_dir))
            (result_root / "m3-f01.payload.json").write_text(
                "sentinel\n", encoding="utf-8", newline="\n"
            )
            with mock.patch("audit_forward_r4_preparation.R4_RESULT_ROOT", result_root):
                result = audit_preparation(manifest_path)
            self.assertEqual(result["status"], "invalid")
            self.assertIn("future_output_exists", result["errors"])


if __name__ == "__main__":
    unittest.main()
