from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[1]
EVALS_DIR = REPOSITORY / "evals" / "m1"
sys.path.insert(0, str(EVALS_DIR))

from replay_offline_results import replay_records  # noqa: E402


class OfflineResultsReplayTests(unittest.TestCase):
    def test_replay_matches_all_frozen_results_exactly(self) -> None:
        frozen = json.loads(
            (REPOSITORY / "evals" / "m1" / "offline-results.json").read_text(
                encoding="utf-8"
            )
        )

        result = replay_records(frozen["results"], REPOSITORY)

        self.assertEqual(result, {"status": "valid", "mismatches": []})

    def test_replay_reports_expected_status_mismatch(self) -> None:
        frozen = json.loads(
            (REPOSITORY / "evals" / "m1" / "offline-results.json").read_text(
                encoding="utf-8"
            )
        )
        expected = next(
            record.copy()
            for record in frozen["results"]
            if record["fixture"].endswith("blocked-conflict.json")
        )
        expected.update(
            {"exit_code": 0, "status": "valid", "errors": [], "evidence_gaps": []}
        )

        result = replay_records([expected], REPOSITORY)

        self.assertEqual(result["status"], "invalid")
        self.assertEqual(
            result["mismatches"][0]["fixture"],
            "evals/m1/fixtures/blocked-conflict.json",
        )
        self.assertEqual(
            set(result["mismatches"][0]), {"fixture", "expected", "actual"}
        )


if __name__ == "__main__":
    unittest.main()
