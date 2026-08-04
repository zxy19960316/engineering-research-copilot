from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "skills" / "engineering-research-copilot" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from validate_citation_gate import validate_gate  # noqa: E402


def make_gate() -> dict:
    return {
        "schema_version": "citation-gate.1",
        "terminal_state": "CITATION_BLOCKED",
        "verification_status": "conflicted",
        "recommendation_eligible": False,
        "checked_sources": [
            {
                "source_type": "official_repository",
                "canonical_record": "https://example.invalid/fixture-citation-record",
                "checked_at": "2026-08-04T18:17:16+08:00",
                "result": "conflict",
            }
        ],
        "blocking_reasons": ["The supplied title and DOI identify different works."],
    }


class CitationGateTests(unittest.TestCase):
    def test_valid_blocked_gate(self) -> None:
        self.assertEqual(
            validate_gate(make_gate()),
            {"status": "valid", "errors": [], "evidence_gaps": []},
        )

    def test_rejects_recommendation_eligible(self) -> None:
        gate = make_gate()
        gate["recommendation_eligible"] = True
        self.assertIn("citation_gate_marked_eligible", validate_gate(gate)["errors"])

    def test_rejects_non_conflicted_status(self) -> None:
        gate = make_gate()
        gate["verification_status"] = "verified_primary"
        self.assertIn("invalid_verification_status", validate_gate(gate)["errors"])

    def test_rejects_missing_source(self) -> None:
        gate = make_gate()
        gate["checked_sources"] = []
        self.assertIn("missing_checked_sources", validate_gate(gate)["errors"])

    def test_rejects_unknown_fields(self) -> None:
        gate = make_gate()
        gate["unexpected"] = True
        self.assertIn("unknown_root_field", validate_gate(gate)["errors"])

    def test_rejects_invalid_timestamp(self) -> None:
        gate = make_gate()
        gate["checked_sources"][0]["checked_at"] = "2026-08-04T18:17:16"
        self.assertIn("invalid_checked_source", validate_gate(gate)["errors"])

    def test_rejects_round_fields(self) -> None:
        for field in ("round1", "round2"):
            with self.subTest(field=field):
                gate = make_gate()
                gate[field] = {}
                result = validate_gate(gate)
                self.assertIn("round_field_in_citation_gate", result["errors"])

    def test_rejects_unknown_source_field(self) -> None:
        gate = make_gate()
        gate["checked_sources"][0]["note"] = "extra"
        self.assertIn("invalid_checked_source", validate_gate(gate)["errors"])

    def test_rejects_empty_blocking_reason(self) -> None:
        gate = make_gate()
        gate["blocking_reasons"] = [""]
        self.assertIn("invalid_blocking_reasons", validate_gate(gate)["errors"])

    def test_closed_on_malformed_object(self) -> None:
        self.assertEqual(
            validate_gate([]),
            {"status": "invalid", "errors": ["malformed_gate"], "evidence_gaps": []},
        )

    def test_cli_valid_and_invalid_exits(self) -> None:
        script = SCRIPTS_DIR / "validate_citation_gate.py"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "gate.json"
            path.write_text(json.dumps(make_gate()), encoding="utf-8")
            valid = subprocess.run(
                [sys.executable, str(script), str(path)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(valid.returncode, 0)
            self.assertEqual(json.loads(valid.stdout)["status"], "valid")

            invalid_gate = copy.deepcopy(make_gate())
            invalid_gate["recommendation_eligible"] = True
            path.write_text(json.dumps(invalid_gate), encoding="utf-8")
            invalid = subprocess.run(
                [sys.executable, str(script), str(path)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(invalid.returncode, 1)
            self.assertEqual(json.loads(invalid.stdout)["status"], "invalid")
            self.assertEqual(invalid.stderr, "")


if __name__ == "__main__":
    unittest.main()
