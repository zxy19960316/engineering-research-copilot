from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "evals" / "m3"))

import audit_m3_r5_1_ci_state as state_audit  # noqa: E402


class AuditM3R51CIStateTests(unittest.TestCase):
    def test_current_expected_blocked_state_is_structurally_valid(self):
        result = state_audit.audit_expected_state()

        self.assertEqual(result["status"], "valid")
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["historical_prerequisite_status"], "evidence_incomplete")
        self.assertEqual(result["r5_acceptance_status"], "blocked_not_accepted")
        self.assertEqual(result["m3_status"], "IN_PROGRESS")
        self.assertEqual(result["later_gates"], "NOT_RUN")

    def test_acceptance_drift_fails_without_relabeling(self):
        prerequisite = {
            "status": "evidence_incomplete",
            "errors": [],
            "evidence_gaps": ["no independently accepted complete non-nuclear M1/M2 input"],
            "cases": [
                {
                    "case_id": case_id,
                    "status": "evidence_incomplete" if case_id == "m3-f04" else "valid",
                }
                for case_id in ("m3-f01", "m3-f02", "m3-f03", "m3-f04", "m3-f05")
            ],
        }
        with mock.patch.object(state_audit, "audit_manifest", return_value=prerequisite), mock.patch.object(
            state_audit,
            "audit_acceptance_manifest",
            return_value={
                "status": "accepted",
                "errors": [],
                "counters": {},
                "m3_status": "COMPLETE",
                "later_gates": "RUN",
            },
        ):
            result = state_audit.audit_expected_state()

        self.assertEqual(result["status"], "invalid")
        self.assertIn("r5_acceptance_status_drift", result["errors"])
        self.assertIn("r5_m3_status_drift", result["errors"])


if __name__ == "__main__":
    unittest.main()
