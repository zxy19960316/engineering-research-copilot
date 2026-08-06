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

import audit_forward_r5_acceptance as audit  # noqa: E402
from r5_dispatch_contract import (  # noqa: E402
    CASE_IDS,
    COUNTER_KEYS,
    derive_counters,
    canonical_future_paths,
)


R4_MANIFEST = REPO_ROOT / "evals" / "m3" / "results" / "forward-r4" / "acceptance-manifest.json"


class AuditM3ForwardR5AcceptanceTests(unittest.TestCase):
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

    def _write_json(self, path: Path, value: object) -> None:
        path.write_text(
            json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
            newline="\n",
        )

    def _manifest(self, root: Path, records: list[dict]) -> tuple[Path, Path]:
        result_root = root / "forward-r5"
        result_root.mkdir()
        cases = []
        for record in records:
            paths = canonical_future_paths(record["case_id"], result_root)
            for key, raw in paths.items():
                if raw is None:
                    continue
                path = result_root / raw
                if key == "model_final_json" or record["state"] in {
                    "processed_accepted",
                    "processed_invalid",
                }:
                    path.write_text("{}\n", encoding="utf-8", newline="\n")
                elif record["state"] == "processing_failed" and (
                    key in {"context_finalization_json", "case_transaction_json"}
                    or (key == "composer_invocation_receipt_json" and record["composer_invocations"] == 1)
                    or (key == "validator_receipt_json" and record["validator_invocations"] == 1)
                ):
                    path.write_text("{}\n", encoding="utf-8", newline="\n")
            cases.append({"case_id": record["case_id"], "record": record, "future_paths": paths})
        historical = {
            "path": str(R4_MANIFEST.relative_to(REPO_ROOT)).replace("\\", "/"),
            "raw_sha256": hashlib.sha256(R4_MANIFEST.read_bytes()).hexdigest(),
            "status": "blocked_not_accepted",
            "count_as_r5": False,
        }
        try:
            counters = derive_counters(records)
        except ValueError:
            counters = {}
            for key in COUNTER_KEYS:
                if key == "accepted_cases":
                    counters[key] = sum(1 for record in records if record.get("accepted") is True)
                elif key == "transaction_failures":
                    counters[key] = sum(1 for record in records if record.get("transaction_failures"))
                else:
                    counters[key] = sum(
                        value
                        for record in records
                        if isinstance(value := record.get(key), int) and not isinstance(value, bool)
                    )
        manifest = {
            "schema_version": "m3.1-forward-acceptance-r5-v1",
            "status": "in_progress",
            "m3_status": "IN_PROGRESS",
            "later_gates": "NOT_RUN",
            "result_root": result_root.relative_to(REPO_ROOT).as_posix(),
            "counters": counters,
            "historical_r4": historical,
            "cases": cases,
        }
        path = root / "acceptance-manifest.json"
        self._write_json(path, manifest)
        return path, result_root

    def _partial_records(self) -> list[dict]:
        records = []
        for case_id in CASE_IDS:
            if case_id == "m3-f03":
                records.append(
                    self._record(
                        case_id,
                        "processed_invalid",
                        task_id=f"task-{case_id}",
                        finalizations=1,
                        preflighted=1,
                        processed=1,
                        validator=1,
                    )
                )
            else:
                records.append(
                    self._record(
                        case_id,
                        "finalized_unprocessed",
                        task_id=f"task-{case_id}",
                        finalizations=1,
                    )
                )
        return records

    def _accepted_records(self) -> list[dict]:
        return [
            self._record(
                case_id,
                "processed_accepted",
                task_id=f"task-{case_id}",
                finalizations=1,
                preflighted=1,
                processed=1,
                composer=0 if case_id == "m3-f03" else 1,
                validator=1,
                accepted=True,
            )
            for case_id in CASE_IDS
        ]

    def _audit(self, manifest_path: Path, result_root: Path) -> dict:
        with mock.patch.object(audit, "R5_RESULT_ROOT", result_root):
            return audit.audit_acceptance_manifest(manifest_path)

    def test_five_finalizations_and_one_processed_case_are_counted_from_records(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            manifest_path, result_root = self._manifest(Path(temp_dir), self._partial_records())
            result = self._audit(manifest_path, result_root)

        self.assertEqual(result["counters"]["task_finalizations_observed"], 5)
        self.assertEqual(result["counters"]["dispatcher_cases_processed"], 1)
        self.assertNotIn("fresh_contexts_consumed", result)
        self.assertNotIn("remaining_cases_not_dispatched", result["errors"])
        self.assertEqual(
            {case["record_state"] for case in result["cases"]},
            {"finalized_unprocessed", "processed_invalid"},
        )

    def test_missing_artifacts_do_not_become_not_dispatched_or_not_finalized(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            manifest_path, result_root = self._manifest(root, self._partial_records())
            (result_root / "m3-f01.model-final.json").unlink()
            result = self._audit(manifest_path, result_root)

        self.assertEqual(result["status"], "invalid")
        self.assertIn("artifact_missing:m3-f01:model_final_json", result["errors"])
        f01 = next(case for case in result["cases"] if case["case_id"] == "m3-f01")
        self.assertEqual(f01["record_state"], "finalized_unprocessed")
        self.assertNotIn("task_not_dispatched", result["errors"])

    def test_aggregate_counters_must_equal_per_case_derivation(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            manifest_path, result_root = self._manifest(root, self._partial_records())
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["counters"]["task_finalizations_observed"] = 1
            self._write_json(manifest_path, manifest)
            result = self._audit(manifest_path, result_root)

        self.assertEqual(result["status"], "invalid")
        self.assertIn("aggregate_counter_mismatch:task_finalizations_observed", result["errors"])

    def test_task_ids_are_unique_and_bound_to_case_ids(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            records = self._partial_records()
            records[1]["task_id"] = records[0]["task_id"]
            manifest_path, result_root = self._manifest(root, records)
            result = self._audit(manifest_path, result_root)

        self.assertEqual(result["status"], "invalid")
        self.assertIn("task_id_duplicate:task-m3-f01", result["errors"])

    def test_finalization_is_exactly_one_per_launched_case(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            records = self._partial_records()
            records[0]["task_finalizations_observed"] = 0
            manifest_path, result_root = self._manifest(root, records)
            result = self._audit(manifest_path, result_root)

        self.assertEqual(result["status"], "invalid")
        self.assertIn("finalized_unprocessed_counters_invalid", result["errors"])

    def test_accepted_requires_five_finalized_five_processed_expected_invocations_and_zero_failures(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            manifest_path, result_root = self._manifest(root, self._accepted_records())
            result = self._audit(manifest_path, result_root)

        self.assertEqual(result["status"], "accepted")
        self.assertEqual(result["counters"]["task_finalizations_observed"], 5)
        self.assertEqual(result["counters"]["dispatcher_cases_processed"], 5)
        self.assertEqual(result["counters"]["composer_invocations"], 4)
        self.assertEqual(result["counters"]["validator_invocations"], 5)
        self.assertEqual(result["counters"]["accepted_cases"], 5)
        self.assertEqual(result["counters"]["transaction_failures"], 0)

    def test_callback_or_receipt_failure_keeps_m3_in_progress_and_later_gates_not_run(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            records = self._partial_records()
            records[2] = self._record(
                "m3-f03",
                "processing_failed",
                task_id="task-m3-f03",
                finalizations=1,
                preflighted=1,
                validator=1,
                failures=["validator_receipt_write_failed"],
            )
            manifest_path, result_root = self._manifest(root, records)
            result = self._audit(manifest_path, result_root)

        self.assertEqual(result["status"], "blocked_not_accepted")
        self.assertEqual(result["m3_status"], "IN_PROGRESS")
        self.assertEqual(result["later_gates"], "NOT_RUN")
        self.assertEqual(result["counters"]["task_finalizations_observed"], 5)
        self.assertEqual(result["counters"]["dispatcher_cases_processed"], 0)

    def test_r4_blocked_manifest_is_historical_only(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            manifest_path, result_root = self._manifest(Path(temp_dir), self._partial_records())
            result = self._audit(manifest_path, result_root)

        self.assertEqual(result["historical_r4"]["status"], "blocked_not_accepted")
        self.assertEqual(result["counters"]["task_finalizations_observed"], 5)
        self.assertEqual(result["historical_r4"]["count_as_r5"], False)


if __name__ == "__main__":
    unittest.main()
