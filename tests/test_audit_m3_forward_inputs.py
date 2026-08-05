from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
M3_INPUT_ROOT = REPO_ROOT / "evals" / "m3" / "forward-inputs"
OLD_MANIFEST = M3_INPUT_ROOT / "manifest.json"

import sys

sys.path.insert(0, str(REPO_ROOT / "evals" / "m3"))

from audit_forward_inputs import audit_manifest  # noqa: E402


def _raw_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_sha256(path: Path) -> str:
    payload = json.loads(path.read_text(encoding="utf-8"))
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _r2_manifest() -> dict:
    old = json.loads(OLD_MANIFEST.read_text(encoding="utf-8"))
    cases = []
    for raw_case in old["cases"]:
        case = copy.deepcopy(raw_case)
        case["validation_path"] = (
            f"evals/m3/forward-inputs/{case['case_id']}.validation.json"
            if case["case_id"] != "m3-f04"
            else None
        )
        case["prompt_path"] = f"evals/m3/forward-cases.md"
        cases.append(case)
    return {
        "schema_version": "m3.1-forward-inputs-r2",
        "evidence_class": "independent_m2_input_preparation",
        "preparation_context": "test-independent-m2-input-context",
        "cases": cases,
    }


class AuditM3ForwardInputsTests(unittest.TestCase):
    def _audit(self, manifest: dict) -> dict:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            path = Path(temp_dir) / "manifest.json"
            path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            return audit_manifest(path)

    def _case(self, result: dict, case_id: str) -> dict:
        return next(case for case in result["cases"] if case["case_id"] == case_id)

    def test_current_revision_one_inputs_are_not_accepted_as_r2(self):
        result = self._audit(_r2_manifest())

        self.assertEqual(result["status"], "invalid")
        self.assertEqual(
            {case["case_id"] for case in result["cases"]},
            {"m3-f01", "m3-f02", "m3-f03", "m3-f04", "m3-f05"},
        )
        self.assertEqual(self._case(result, "m3-f03")["status"], "valid")
        self.assertIn(
            "f02_route_condition_types_mismatch",
            self._case(result, "m3-f02")["errors"],
        )
        self.assertIn(
            "f05_route_must_be_null",
            self._case(result, "m3-f05")["errors"],
        )

    def test_f01_and_f04_not_run_are_evidence_gaps(self):
        result = self._audit(_r2_manifest())

        f01 = self._case(result, "m3-f01")
        f04 = self._case(result, "m3-f04")
        self.assertEqual(f01["status"], "evidence_incomplete")
        self.assertEqual(f04["status"], "evidence_incomplete")
        self.assertTrue(f01["evidence_gaps"])
        self.assertTrue(f04["evidence_gaps"])
        self.assertIn(
            "no independently accepted complete non-nuclear M1/M2 input",
            f04["evidence_gaps"],
        )

    def test_input_raw_hash_mismatch_is_invalid(self):
        manifest = _r2_manifest()
        manifest["cases"][1]["raw_sha256"] = "0" * 64

        result = self._audit(manifest)

        self.assertEqual(result["status"], "invalid")
        self.assertIn(
            "input_raw_sha256_mismatch",
            self._case(result, "m3-f02")["errors"],
        )

    def test_source_m1_hash_mismatch_is_invalid(self):
        manifest = _r2_manifest()
        manifest["cases"][2]["source_m1_raw_sha256"] = "0" * 64

        result = self._audit(manifest)

        self.assertIn(
            "source_m1_raw_sha256_mismatch",
            self._case(result, "m3-f03")["errors"],
        )

    def test_path_escape_is_rejected(self):
        manifest = _r2_manifest()
        manifest["cases"][1]["input_path"] = "../outside.json"

        result = self._audit(manifest)

        self.assertIn(
            "input_path_outside_repository",
            self._case(result, "m3-f02")["errors"],
        )

    def test_m2_validation_receipt_must_be_valid_and_single_invocation(self):
        manifest = _r2_manifest()
        manifest["cases"][2]["m2_validation_status"] = "invalid"

        result = self._audit(manifest)

        self.assertIn(
            "m2_validation_not_valid",
            self._case(result, "m3-f03")["errors"],
        )

    def test_f03_requires_nonempty_approved_change_and_preserves_limits(self):
        result = self._audit(_r2_manifest())

        f03 = self._case(result, "m3-f03")
        self.assertEqual(f03["status"], "valid")
        self.assertEqual(f03["errors"], [])


if __name__ == "__main__":
    unittest.main()
