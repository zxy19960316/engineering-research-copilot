from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
OLD_FORWARD_ROOT = REPO_ROOT / "evals" / "m3" / "results" / "forward"

import sys

sys.path.insert(0, str(REPO_ROOT / "evals" / "m3"))

from audit_forward_acceptance import audit_acceptance_manifest  # noqa: E402


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


def _case_fixture(root: Path, case_id: str, expected_status: str, errors: list[str]):
    input_path = root / f"{case_id}.input.json"
    prompt_path = root / f"{case_id}.prompt.txt"
    output_path = root / f"{case_id}.output.json"
    validation_path = root / f"{case_id}.validation.json"
    context_path = root / f"{case_id}.context.md"
    _write_json(input_path, {"case_id": case_id, "immutable": True})
    prompt_path.write_text(f"Frozen prompt for {case_id}\n", encoding="utf-8")
    _write_json(output_path, {"case_id": case_id, "schema_version": "m3.1"})
    _write_json(
        validation_path,
        {"status": expected_status, "errors": errors, "evidence_gaps": []},
    )
    context_path.write_text(
        "\n".join(
            [
                f"context_id: fresh-{case_id}",
                f"input_sha256: {_sha256(input_path)}",
                f"prompt_sha256: {_sha256(prompt_path)}",
                f"output_sha256: {_sha256(output_path)}",
                f"validation_sha256: {_sha256(validation_path)}",
                "loaded_references: [skills/engineering-research-copilot/SKILL.md]",
                "finalization_count: 1",
                "validator_invocation_count: 1",
                "side_effects: []",
                "deviations: []",
                "limitations: [structural-only]",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return {
        "case_id": case_id,
        "input_path": str(input_path.relative_to(REPO_ROOT)).replace("\\", "/"),
        "input_raw_sha256": _sha256(input_path),
        "prompt_path": str(prompt_path.relative_to(REPO_ROOT)).replace("\\", "/"),
        "prompt_sha256": _sha256(prompt_path),
        "output_path": str(output_path.relative_to(REPO_ROOT)).replace("\\", "/"),
        "output_raw_sha256": _sha256(output_path),
        "validation_path": str(validation_path.relative_to(REPO_ROOT)).replace("\\", "/"),
        "validation_raw_sha256": _sha256(validation_path),
        "context_path": str(context_path.relative_to(REPO_ROOT)).replace("\\", "/"),
        "expected_status": expected_status,
        "expected_errors": errors,
        "expected_evidence_gaps": [],
        "finalization_count": 1,
        "validator_invocation_count": 1,
        "loaded_references": ["skills/engineering-research-copilot/SKILL.md"],
        "side_effects": [],
        "deviations": [],
        "accepted": True,
    }


def _manifest(root: Path) -> dict:
    cases = []
    for case_id in ("m3-f01", "m3-f02", "m3-f04", "m3-f05"):
        cases.append(_case_fixture(root, case_id, "valid", []))
    cases.append(
        _case_fixture(
            root,
            "m3-f03",
            "invalid",
            ["unsupported_approved_constraint_change_provenance"],
        )
    )
    preserved = []
    for case_id in ("m3-f02", "m3-f03", "m3-f05"):
        for suffix in ("output.json", "validation.json", "context.md"):
            path = OLD_FORWARD_ROOT / f"{case_id}.{suffix}"
            preserved.append(
                {
                    "path": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
                    "raw_sha256": _sha256(path),
                }
            )
    return {
        "schema_version": "m3.1-forward-acceptance-r2",
        "cases": cases,
        "preserved_previous_results": preserved,
    }


class AuditM3ForwardAcceptanceTests(unittest.TestCase):
    def _audit(self, manifest: dict) -> dict:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            path = root / "acceptance-manifest.json"
            _write_json(path, manifest)
            return audit_acceptance_manifest(path)

    def test_complete_manifest_is_valid(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            result = self._audit(_manifest(root))

        self.assertEqual(result["status"], "valid")
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["evidence_gaps"], [])
        self.assertEqual(len(result["cases"]), 5)

    def test_f03_requires_exact_expected_fail_closed_result(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            manifest = _manifest(root)
            case = next(item for item in manifest["cases"] if item["case_id"] == "m3-f03")
            case["expected_errors"] = ["different_error"]
            result = self._audit(manifest)

        self.assertEqual(result["status"], "invalid")
        self.assertTrue(result["errors"])

    def test_output_hash_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            manifest = _manifest(root)
            manifest["cases"][0]["output_raw_sha256"] = "0" * 64
            result = self._audit(manifest)

        self.assertEqual(result["status"], "invalid")
        self.assertIn("output_raw_sha256_mismatch", result["errors"])

    def test_forbidden_validator_reference_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            manifest = _manifest(root)
            manifest["cases"][0]["loaded_references"].append(
                "skills/engineering-research-copilot/scripts/validate_m3_method_bundle.py"
            )
            result = self._audit(manifest)

        self.assertEqual(result["status"], "invalid")
        self.assertIn("forbidden_fresh_reference", result["errors"])

    def test_old_failure_hash_is_required(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            manifest = _manifest(root)
            manifest["preserved_previous_results"][0]["raw_sha256"] = "0" * 64
            result = self._audit(manifest)

        self.assertEqual(result["status"], "invalid")
        self.assertIn("preserved_previous_result_hash_mismatch", result["errors"])

    def test_side_effect_or_retry_counter_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            manifest = _manifest(root)
            manifest["cases"][0]["finalization_count"] = 2
            manifest["cases"][0]["side_effects"] = ["write outside output path"]
            result = self._audit(manifest)

        self.assertEqual(result["status"], "invalid")
        self.assertIn("fresh_case_one_shot_violation", result["errors"])


if __name__ == "__main__":
    unittest.main()
