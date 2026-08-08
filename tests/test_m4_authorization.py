from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
AUTHORIZATION_ROOT = REPO_ROOT / "evals" / "m4" / "authorization"
sys.path.insert(0, str(AUTHORIZATION_ROOT))

from audit_authorization import ZERO_COUNTERS, audit_authorization  # noqa: E402


class M4AuthorizationContractTests(unittest.TestCase):
    def test_repository_authorization_is_ready_unconsumed_and_read_only(self) -> None:
        result = audit_authorization(REPO_ROOT)
        self.assertEqual(result["status"], "READY_UNCONSUMED")
        self.assertEqual(result["authorized_task_count"], 60)
        self.assertEqual(result["existing_result_root_count"], 0)
        self.assertEqual(result["execution_counters"], ZERO_COUNTERS)
        self.assertFalse(result["launch_claim_present"])
        self.assertEqual(result["side_effects"], [])
        self.assertEqual(result["errors"], [])


if __name__ == "__main__":
    unittest.main()
