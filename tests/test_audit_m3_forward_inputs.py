from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
M3_INPUT_ROOT = REPO_ROOT / "evals" / "m3" / "forward-inputs"
OLD_MANIFEST = M3_INPUT_ROOT / "manifest.json"
DIAGNOSTIC = REPO_ROOT / "evals" / "m3" / "diagnose_forward_input_hashes.py"

sys.path.insert(0, str(REPO_ROOT / "evals" / "m3"))

import audit_forward_inputs as audit  # noqa: E402


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
            return audit.audit_manifest(path)

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

    def test_historical_json_identity_is_cross_platform_and_diagnostic(self):
        result = self._audit(_r2_manifest())

        for case_id in ("m3-f01", "m3-f03", "m3-f04"):
            case = self._case(result, case_id)
            self.assertTrue(
                {
                    "case_id",
                    "status",
                    "errors",
                    "evidence_gaps",
                    "expected_raw_sha256",
                    "observed_raw_sha256",
                    "source_m1_expected_sha256",
                    "source_m1_observed_sha256",
                    "input_git_blob_oid",
                    "source_m1_git_blob_oid",
                    "input_canonical_sha256",
                    "source_m1_canonical_sha256",
                }.issubset(case)
            )
            self.assertEqual(case["source_m1_identity_status"], "valid")
            self.assertEqual(len(case["source_m1_git_blob_oid"]), 40)
            self.assertEqual(len(case["source_m1_canonical_sha256"]), 64)

        f01 = self._case(result, "m3-f01")
        self.assertEqual(f01["input_identity_status"], "not_checked")
        self.assertIsNone(f01["expected_raw_sha256"])
        self.assertIsNone(f01["observed_raw_sha256"])
        self.assertEqual(
            f01["source_m1_expected_sha256"],
            "ff6d4eed792358049213b114dbca3d3850c1c95caad68bb0e50cfb6f5b802529",
        )

        f04 = self._case(result, "m3-f04")
        self.assertIsNone(f04["expected_raw_sha256"])
        self.assertIsNone(f04["observed_raw_sha256"])
        self.assertEqual(
            f04["source_m1_expected_sha256"],
            "bee8c0f739647512298d180eb68c934e96dd55054a4aec851ddead7b8e846173",
        )

        f03 = self._case(result, "m3-f03")
        self.assertEqual(f03["input_identity_status"], "valid")

    def test_historical_identity_registry_rejects_evidence_head_drift(self):
        registry = json.loads(audit.HISTORICAL_IDENTITY_PATH.read_text(encoding="utf-8"))
        registry["evidence_head"] = "0" * 40
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            registry_path = Path(temp_dir) / "historical-identities.json"
            registry_path.write_text(
                json.dumps(registry, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            with mock.patch.object(audit, "HISTORICAL_IDENTITY_PATH", registry_path):
                result = self._audit(_r2_manifest())

        self.assertEqual(result["status"], "invalid")
        self.assertIn("historical_evidence_head_mismatch", result["errors"])

    def test_modified_worktree_and_registry_cannot_replace_fixed_head_identity(self):
        manifest = _r2_manifest()
        target_path = (REPO_ROOT / manifest["cases"][2]["source_m1_artifact"]).resolve()
        original_loader = audit._load_json_file
        tampered = original_loader(target_path, "source_m1", [])
        tampered = {**tampered, "simultaneous_worktree_and_registry_tamper": True}
        registry = json.loads(audit.HISTORICAL_IDENTITY_PATH.read_text(encoding="utf-8"))
        registry_entry = next(
            item
            for item in registry["artifacts"]
            if item["path"] == target_path.relative_to(REPO_ROOT).as_posix()
        )
        registry_entry["canonical_sha256"] = audit._canonical_sha256(tampered)

        def load_tampered_worktree(path: Path, prefix: str, errors: list[str]) -> object:
            if path.resolve() == target_path:
                return copy.deepcopy(tampered)
            return original_loader(path, prefix, errors)

        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            registry_path = Path(temp_dir) / "historical-identities.json"
            registry_path.write_text(
                json.dumps(registry, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            with (
                mock.patch.object(audit, "HISTORICAL_IDENTITY_PATH", registry_path),
                mock.patch.object(audit, "_load_json_file", side_effect=load_tampered_worktree),
            ):
                result = self._audit(manifest)

        f03 = self._case(result, "m3-f03")
        self.assertEqual(f03["status"], "invalid")
        self.assertIn("source_m1_canonical_sha256_mismatch", f03["errors"])
        self.assertIn("source_m1_worktree_content_mismatch", f03["errors"])

    def test_read_only_diagnostic_cli_prints_complete_audit(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            manifest_path = Path(temp_dir) / "manifest.json"
            manifest_path.write_text(
                json.dumps(_r2_manifest(), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            completed = subprocess.run(
                [sys.executable, "-X", "utf8", str(DIAGNOSTIC), str(manifest_path)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )

        self.assertEqual(completed.returncode, 1)
        self.assertEqual(completed.stderr, "")
        result = json.loads(completed.stdout)
        f03 = self._case(result, "m3-f03")
        self.assertEqual(f03["status"], "valid")
        self.assertEqual(f03["errors"], [])
        self.assertEqual(f03["evidence_gaps"], [])
        self.assertEqual(len(f03["source_m1_expected_sha256"]), 64)
        self.assertEqual(len(f03["source_m1_observed_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
