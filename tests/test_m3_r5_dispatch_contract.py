from __future__ import annotations

import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(REPO_ROOT / "evals" / "m3"))

from r5_dispatch_contract import (  # noqa: E402
    CANONICAL_PATH_KEYS,
    CASE_IDS,
    COUNTER_KEYS,
    canonical_future_paths,
    derive_counters,
    validate_case_record,
    validate_future_path_sets,
    validate_future_paths,
)


class M3R5DispatchContractTests(unittest.TestCase):
    def _paths(self, case_id: str, root: Path) -> dict[str, str | None]:
        return canonical_future_paths(case_id, root)

    def _record(
        self,
        case_id: str,
        state: str,
        *,
        task_id: str | None = None,
        finalizations: int = 0,
        preflighted: int = 0,
        processed: int = 0,
        composer: int = 0,
        validator: int = 0,
        accepted: bool = False,
        failures: list[str] | None = None,
    ) -> dict:
        return {
            "case_id": case_id,
            "task_id": task_id,
            "state": state,
            "tasks_launched": int(task_id is not None),
            "task_finalizations_observed": finalizations,
            "dispatcher_cases_preflighted": preflighted,
            "dispatcher_cases_processed": processed,
            "composer_invocations": composer,
            "validator_invocations": validator,
            "accepted": accepted,
            "transaction_failures": failures or [],
        }

    def test_canonical_paths_have_all_keys_and_unique_rooted_paths(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            f01 = self._paths("m3-f01", root)
            f03 = self._paths("m3-f03", root)

            self.assertEqual(set(f01), set(CANONICAL_PATH_KEYS))
            self.assertEqual(set(f03), set(CANONICAL_PATH_KEYS))
            self.assertTrue(all(value is not None for value in f01.values()))
            self.assertIsNone(f03["payload_json"])
            self.assertIsNone(f03["composed_bundle_json"])
            self.assertIsNone(f03["composer_invocation_receipt_json"])
            non_null = [value for value in f01.values() if value is not None]
            self.assertEqual(len(non_null), len(set(non_null)))
            self.assertEqual(validate_future_paths("m3-f01", f01, root), [])

    def test_missing_validator_receipt_key_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            paths = self._paths("m3-f01", root)
            del paths["validator_receipt_json"]

            errors = validate_future_paths("m3-f01", paths, root)

            self.assertIn("future_path_keys_missing:validator_receipt_json", errors)

    def test_unknown_or_alias_key_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            paths = self._paths("m3-f01", root)
            paths["receipt_validator_receipt_json"] = paths.pop("validator_receipt_json")

            errors = validate_future_paths("m3-f01", paths, root)

            self.assertIn("future_path_keys_unknown:receipt_validator_receipt_json", errors)
            self.assertIn("future_path_keys_missing:validator_receipt_json", errors)

    def test_absolute_parent_escape_and_backslash_paths_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            for bad in ("..\\outside.json", "../outside.json", "C:/outside.json"):
                paths = self._paths("m3-f01", root)
                paths["outcome_json"] = bad
                errors = validate_future_paths("m3-f01", paths, root)
                self.assertTrue(
                    any(code.startswith("future_path_unsafe:outcome_json") for code in errors),
                    (bad, errors),
                )

    def test_duplicate_paths_across_cases_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            f01 = self._paths("m3-f01", root)
            f02 = self._paths("m3-f02", root)
            f02["outcome_json"] = f01["outcome_json"]

            errors = validate_future_path_sets(
                {"m3-f01": f01, "m3-f02": f02},
                root,
            )

            self.assertIn("future_path_duplicate:outcome_json:m3-f01:m3-f02", errors)

    def test_existing_reserved_path_is_rejected_without_writing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            paths = self._paths("m3-f01", root)
            existing = root / str(paths["outcome_json"])
            existing.write_bytes(b"sentinel")

            errors = validate_future_paths("m3-f01", paths, root)

            self.assertIn("future_path_exists:outcome_json", errors)
            self.assertEqual(existing.read_bytes(), b"sentinel")

    def test_closed_states_reject_impossible_counter_combinations(self):
        record = self._record(
            "m3-f03",
            "processing_failed",
            task_id="task-f03",
            finalizations=1,
            preflighted=1,
            processed=0,
            validator=1,
            failures=["validator_receipt_write_failed"],
        )
        self.assertEqual(validate_case_record(record), [])

        impossible = dict(record)
        impossible["accepted"] = True
        self.assertIn("accepted_state_invalid", validate_case_record(impossible))

        missing_failure = dict(record)
        missing_failure["transaction_failures"] = []
        self.assertIn("processing_failure_reason_missing", validate_case_record(missing_failure))

    def test_counters_are_derived_from_case_records_not_filenames(self):
        records = [
            self._record("m3-f01", "finalized_unprocessed", task_id="task-f01", finalizations=1),
            self._record("m3-f02", "finalized_unprocessed", task_id="task-f02", finalizations=1),
            self._record(
                "m3-f03",
                "processed_invalid",
                task_id="task-f03",
                finalizations=1,
                preflighted=1,
                processed=1,
                validator=1,
            ),
            self._record("m3-f04", "finalized_unprocessed", task_id="task-f04", finalizations=1),
            self._record("m3-f05", "finalized_unprocessed", task_id="task-f05", finalizations=1),
        ]

        counters = derive_counters(records)

        self.assertEqual(set(counters), set(COUNTER_KEYS))
        self.assertEqual(counters["tasks_launched"], 5)
        self.assertEqual(counters["task_finalizations_observed"], 5)
        self.assertEqual(counters["dispatcher_cases_preflighted"], 1)
        self.assertEqual(counters["dispatcher_cases_processed"], 1)
        self.assertEqual(counters["validator_invocations"], 1)
        self.assertEqual(counters["accepted_cases"], 0)

        with self.assertRaises(ValueError):
            derive_counters([{"fresh_contexts_consumed": 1}])


if __name__ == "__main__":
    unittest.main()
