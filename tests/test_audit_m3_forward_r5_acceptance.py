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
sys.path.insert(0, str(REPO_ROOT / "tests"))

import audit_forward_r5_acceptance as audit  # noqa: E402
from r5_dispatch_contract import (  # noqa: E402
    CASE_IDS,
    COUNTER_KEYS,
    derive_counters,
    canonical_future_paths,
)
from test_validate_m3_method_bundle import make_valid_m3_bundle  # noqa: E402


R4_MANIFEST = REPO_ROOT / "evals" / "m3" / "results" / "forward-r4" / "acceptance-manifest.json"
F03_SOURCE = REPO_ROOT / "evals" / "m3" / "forward-inputs-r2" / "m3-f03-approved-change.bundle.json"
F03_OUTCOME = REPO_ROOT / "evals" / "m3" / "results" / "forward-r5" / "m3-f03.outcome.json"
CONSUMED_MANIFEST = REPO_ROOT / "evals" / "m3" / "results" / "forward-r5" / "acceptance-manifest-consumed.json"


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
        input_root = root / "inputs"
        input_root.mkdir()
        prompt_root = root / "prompts"
        prompt_root.mkdir()
        contract_path = root / "contract.json"
        self._write_json(contract_path, {"schema_version": "test-contract-v1"})
        cases = []
        task_ids: dict[str, str | None] = {}
        finalization_ids: dict[str, str] = {}
        for record in records:
            case_id = record["case_id"]
            paths = canonical_future_paths(record["case_id"], result_root)
            if case_id == "m3-f03":
                source_value = json.loads(F03_SOURCE.read_text(encoding="utf-8"))
            else:
                source_value = make_valid_m3_bundle()["source_m2_bundle"]
            source_path = input_root / f"{case_id}.source.json"
            self._write_json(source_path, source_value)
            prompt_path = prompt_root / f"{case_id}.prompt.txt"
            prompt_path.write_text(f"frozen prompt for {case_id}\n", encoding="utf-8", newline="\n")

            model_value: dict = {}
            bundle_value: dict | None = None
            outcome_value: dict | None = None
            validation_value: dict | None = None
            if record["state"] in {"processed_accepted", "processed_invalid"}:
                if case_id == "m3-f03":
                    outcome_value = (
                        json.loads(F03_OUTCOME.read_text(encoding="utf-8"))
                        if record["accepted"]
                        else {}
                    )
                    model_value = outcome_value
                    replay = audit.validate_forward_outcome(case_id, source_value, outcome_value)
                    validation_value = {
                        **replay,
                        "accepted": replay.get("status") == "accepted_expected_block",
                    }
                else:
                    bundle_value = make_valid_m3_bundle()
                    source_value = bundle_value["source_m2_bundle"]
                    self._write_json(source_path, source_value)
                    model_value = {
                        key: bundle_value[key]
                        for key in ("coaching_mode", "method_cards", "domain_overlays")
                    }
                    replay = audit.validate_m3_bundle(bundle_value)
                    validation_value = {**replay, "accepted": replay["status"] == "valid"}
                    outcome_value = {
                        "case_id": case_id,
                        "accepted": validation_value["accepted"],
                        "validation_status": validation_value["status"],
                    }

            artifact_hashes: dict[str, str] = {}
            if record["task_finalizations_observed"] == 1:
                model_path = result_root / paths["model_final_json"]
                self._write_json(model_path, model_value)
                artifact_hashes["model_final_json"] = hashlib.sha256(model_path.read_bytes()).hexdigest()
            if record["state"] in {"processing_failed", "processed_accepted", "processed_invalid"}:
                context = {
                    key: record[key]
                    for key in audit.RECORD_CONTEXT_KEYS
                }
                context["final_raw_sha256"] = artifact_hashes["model_final_json"]
                context["final_byte_length"] = (result_root / paths["model_final_json"]).stat().st_size
                if validation_value is not None:
                    context["validation_status"] = validation_value["status"]
                context_path = result_root / paths["context_finalization_json"]
                transaction_path = result_root / paths["case_transaction_json"]
                self._write_json(context_path, context)
                self._write_json(transaction_path, record)
                artifact_hashes["context_finalization_json"] = hashlib.sha256(context_path.read_bytes()).hexdigest()
                artifact_hashes["case_transaction_json"] = hashlib.sha256(transaction_path.read_bytes()).hexdigest()
            if record["composer_invocations"] == 1:
                composer_receipt = {
                    "case_id": case_id,
                    "composer_invocation_count": 1,
                    "status": "invoked" if record["state"] in {"processed_accepted", "processed_invalid"} else "failed",
                }
                receipt_path = result_root / paths["composer_invocation_receipt_json"]
                self._write_json(receipt_path, composer_receipt)
                artifact_hashes["composer_invocation_receipt_json"] = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
            if bundle_value is not None:
                payload_path = result_root / paths["payload_json"]
                bundle_path = result_root / paths["composed_bundle_json"]
                self._write_json(payload_path, model_value)
                self._write_json(bundle_path, bundle_value)
                artifact_hashes["payload_json"] = hashlib.sha256(payload_path.read_bytes()).hexdigest()
                artifact_hashes["composed_bundle_json"] = hashlib.sha256(bundle_path.read_bytes()).hexdigest()
            if record["validator_invocations"] == 1:
                validator_receipt = {
                    "case_id": case_id,
                    "validator_invocation_count": 1,
                    "status": "invoked" if record["state"] in {"processed_accepted", "processed_invalid"} else "failed",
                }
                receipt_path = result_root / paths["validator_receipt_json"]
                self._write_json(receipt_path, validator_receipt)
                artifact_hashes["validator_receipt_json"] = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
            if validation_value is not None and outcome_value is not None:
                validation_path = result_root / paths["validation_json"]
                outcome_path = result_root / paths["outcome_json"]
                self._write_json(validation_path, validation_value)
                self._write_json(outcome_path, outcome_value)
                artifact_hashes["validation_json"] = hashlib.sha256(validation_path.read_bytes()).hexdigest()
                artifact_hashes["outcome_json"] = hashlib.sha256(outcome_path.read_bytes()).hexdigest()

            finalization_id = f"finalization-{case_id}"
            task_ids[case_id] = record["task_id"]
            finalization_ids[case_id] = finalization_id
            cases.append(
                {
                    "case_id": case_id,
                    "record": record,
                    "future_paths": paths,
                    "fresh_context_thread_id": record["task_id"],
                    "finalization_turn_id": finalization_id,
                    "input_path": source_path.relative_to(REPO_ROOT).as_posix(),
                    "input_raw_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
                    "input_canonical_sha256": audit._canonical_sha256(source_value),
                    "prompt_path": prompt_path.relative_to(REPO_ROOT).as_posix(),
                    "prompt_raw_sha256": hashlib.sha256(prompt_path.read_bytes()).hexdigest(),
                    "contract_path": contract_path.relative_to(REPO_ROOT).as_posix(),
                    "contract_raw_sha256": hashlib.sha256(contract_path.read_bytes()).hexdigest(),
                    "artifact_sha256": artifact_hashes,
                }
            )
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
            "contract": {
                "path": contract_path.relative_to(REPO_ROOT).as_posix(),
                "raw_sha256": hashlib.sha256(contract_path.read_bytes()).hexdigest(),
            },
            "run": {
                "task_ids": task_ids,
                "finalization_turn_ids": finalization_ids,
            },
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

    def _case_entry(self, manifest: dict, case_id: str) -> dict:
        return next(item for item in manifest["cases"] if item["case_id"] == case_id)

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

    def test_consumed_r5_is_cross_validated_but_remains_blocked(self):
        result = audit.audit_acceptance_manifest(CONSUMED_MANIFEST)

        self.assertEqual(result["status"], "blocked_not_accepted")
        self.assertEqual(result["errors"], ["acceptance_requirements_unmet"])
        f02 = next(item for item in result["cases"] if item["case_id"] == "m3-f02")
        self.assertEqual(f02["record_state"], "processing_failed")
        self.assertEqual(
            f02["model_final_sha256"],
            "72b0aaef8fdabb3456d1226ba4ef93705512d60c74cccf5c29da2f0278b154a2",
        )

    def test_modified_validation_without_manifest_update_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            manifest_path, result_root = self._manifest(root, self._accepted_records())
            validation_path = result_root / "m3-f01.validation.json"
            validation = json.loads(validation_path.read_text(encoding="utf-8"))
            validation["errors"] = ["tampered_validation"]
            self._write_json(validation_path, validation)
            result = self._audit(manifest_path, result_root)

        self.assertEqual(result["status"], "invalid")
        self.assertIn("validation_replay_mismatch:m3-f01", result["errors"])

    def test_modified_transaction_state_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            manifest_path, result_root = self._manifest(root, self._accepted_records())
            transaction_path = result_root / "m3-f01.transaction.json"
            transaction = json.loads(transaction_path.read_text(encoding="utf-8"))
            transaction["state"] = "processing_failed"
            self._write_json(transaction_path, transaction)
            result = self._audit(manifest_path, result_root)

        self.assertEqual(result["status"], "invalid")
        self.assertIn("transaction_record_mismatch:m3-f01", result["errors"])

    def test_deleted_receipt_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            manifest_path, result_root = self._manifest(root, self._accepted_records())
            (result_root / "m3-f01.validator-receipt.json").unlink()
            result = self._audit(manifest_path, result_root)

        self.assertEqual(result["status"], "invalid")
        self.assertIn("artifact_missing:m3-f01:validator_receipt_json", result["errors"])

    def test_failed_case_cannot_be_flipped_to_accepted(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            records = self._partial_records()
            records[1] = self._record(
                "m3-f02",
                "processing_failed",
                task_id="task-m3-f02",
                finalizations=1,
                preflighted=1,
                composer=1,
                failures=["composer_invocation_failed"],
            )
            manifest_path, result_root = self._manifest(root, records)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self._case_entry(manifest, "m3-f02")["record"]["accepted"] = True
            self._write_json(manifest_path, manifest)
            result = self._audit(manifest_path, result_root)

        self.assertEqual(result["status"], "invalid")
        self.assertIn("accepted_state_invalid", result["errors"])

    def test_bundle_from_another_case_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            manifest_path, result_root = self._manifest(root, self._accepted_records())
            source = REPO_ROOT / "evals" / "m3" / "results" / "forward-r5" / "m3-f04.bundle.json"
            target = result_root / "m3-f01.bundle.json"
            target.write_bytes(source.read_bytes())
            result = self._audit(manifest_path, result_root)

        self.assertEqual(result["status"], "invalid")
        self.assertIn("composed_source_mismatch:m3-f01", result["errors"])

    def test_modified_artifact_with_stale_hash_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            manifest_path, result_root = self._manifest(root, self._accepted_records())
            self._write_json(result_root / "m3-f01.model-final.json", {"tampered": True})
            result = self._audit(manifest_path, result_root)

        self.assertEqual(result["status"], "invalid")
        self.assertIn("artifact_sha256_mismatch:m3-f01:model_final_json", result["errors"])

    def test_result_root_must_equal_frozen_root_not_a_subdirectory(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            manifest_path, result_root = self._manifest(root, self._accepted_records())
            nested = result_root / "nested"
            nested.mkdir()
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["result_root"] = nested.relative_to(REPO_ROOT).as_posix()
            self._write_json(manifest_path, manifest)
            result = self._audit(manifest_path, result_root)

        self.assertEqual(result["status"], "invalid")
        self.assertIn("result_root_not_exact", result["errors"])


if __name__ == "__main__":
    unittest.main()
