from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "evals" / "m3"))

import consume_forward_r5_once as consumer  # noqa: E402
from r5_dispatch_contract import canonical_future_paths  # noqa: E402


SOURCE = REPO_ROOT / "evals" / "m3" / "forward-inputs-r2" / "m3-f03-approved-change.bundle.json"


class ConsumeForwardR5OnceTests(unittest.TestCase):
    def _plan(self, root: Path, case_id: str = "m3-f01") -> dict:
        return {
            "case_id": case_id,
            "task_id": f"task-{case_id}",
            "future_paths": canonical_future_paths(case_id, root),
            "result_root": root,
            "source_input_path": SOURCE,
        }

    def _path(self, plan: dict, key: str) -> Path:
        raw = plan["future_paths"][key]
        assert raw is not None
        return plan["result_root"] / raw

    def test_successful_processing_invokes_composer_and_validator_once(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            plan = self._plan(root)
            compose = mock.Mock(return_value={"bundle": "composed"})
            validate = mock.Mock(return_value={"status": "valid", "accepted": True})

            result = consumer.consume_case_once(
                plan,
                b'{"model":"final"}\n',
                compose_once=compose,
                validate_once=validate,
            )

            self.assertEqual(result["status"], "processed")
            self.assertEqual(result["record"]["state"], "processed_accepted")
            self.assertEqual(result["record"]["composer_invocations"], 1)
            self.assertEqual(result["record"]["validator_invocations"], 1)
            compose.assert_called_once()
            validate.assert_called_once()
            self.assertTrue(self._path(plan, "model_final_json").exists())
            self.assertTrue(self._path(plan, "payload_json").exists())
            self.assertTrue(self._path(plan, "composed_bundle_json").exists())
            self.assertTrue(self._path(plan, "outcome_json").exists())
            self.assertTrue(self._path(plan, "validation_json").exists())
            transaction = json.loads(
                self._path(plan, "case_transaction_json").read_text(encoding="utf-8")
            )
            self.assertEqual(transaction["state"], "processed_accepted")

            compose.reset_mock()
            validate.reset_mock()
            second = consumer.consume_case_once(
                plan,
                b'{"model":"retry"}\n',
                compose_once=compose,
                validate_once=validate,
            )
            self.assertEqual(second["status"], "blocked")
            compose.assert_not_called()
            validate.assert_not_called()

    def test_f03_expected_invalid_path_skips_composer_but_validates_once(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            plan = self._plan(root, "m3-f03")
            compose = mock.Mock()
            validate = mock.Mock(return_value={"status": "accepted_expected_block", "accepted": False})

            result = consumer.consume_case_once(
                plan,
                b'{"outcome_kind":"blocked"}\n',
                compose_once=None,
                validate_once=validate,
            )

            self.assertEqual(result["status"], "processed")
            self.assertEqual(result["record"]["state"], "processed_invalid")
            self.assertEqual(result["record"]["composer_invocations"], 0)
            self.assertEqual(result["record"]["validator_invocations"], 1)
            compose.assert_not_called()
            validate.assert_called_once_with(self._path(plan, "outcome_json"))
            self.assertFalse(self._path(plan, "model_final_json").read_bytes() == b"\"")

    def test_composer_failure_after_finalization_is_processing_failed_and_not_retried(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            plan = self._plan(root)
            compose = mock.Mock(side_effect=RuntimeError("secret exception text"))
            validate = mock.Mock()

            result = consumer.consume_case_once(
                plan,
                b'{"model":"final"}\n',
                compose_once=compose,
                validate_once=validate,
            )

            self.assertEqual(result["status"], "processing_failed")
            self.assertEqual(result["record"]["state"], "processing_failed")
            self.assertEqual(result["record"]["task_finalizations_observed"], 1)
            self.assertEqual(result["record"]["dispatcher_cases_processed"], 0)
            self.assertEqual(result["record"]["composer_invocations"], 1)
            self.assertEqual(result["record"]["validator_invocations"], 0)
            self.assertFalse(result["record"]["accepted"])
            self.assertTrue(self._path(plan, "model_final_json").exists())
            self.assertTrue(self._path(plan, "composer_invocation_receipt_json").exists())
            self.assertFalse(self._path(plan, "composed_bundle_json").exists())
            transaction_raw = self._path(plan, "case_transaction_json").read_text(encoding="utf-8")
            self.assertNotIn("secret exception text", transaction_raw)
            receipt = json.loads(
                self._path(plan, "composer_invocation_receipt_json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(receipt["failure_stage"], "unexpected")
            self.assertEqual(receipt["failure_code"], "unexpected_processing_failure")
            self.assertEqual(receipt["contract_errors"], [])
            self.assertEqual(receipt["validator_errors"], [])
            self.assertEqual(receipt["evidence_gaps"], [])
            self.assertEqual(receipt["retry_count"], 0)
            self.assertEqual(len(receipt["source_sha256"]), 64)
            self.assertEqual(len(receipt["model_final_sha256"]), 64)
            self.assertEqual(receipt["model_final_sha256"], receipt["payload_sha256"])
            self.assertNotIn("secret exception text", json.dumps(receipt))
            validate.assert_not_called()

    def test_structured_composer_failure_whitelists_contract_and_validator_codes(self):
        class StructuredFailure(RuntimeError):
            def __init__(self) -> None:
                super().__init__("uncontrolled secret C:\\private\\trace.txt")
                self.code = "invalid_composed_m3_bundle"
                self.detail = {
                    "contract_errors": ["allowed_contract_code", "bad code with spaces"],
                    "validator_errors": [
                        "method_card_pivot_condition_not_authoritative",
                        "method_card_stop_condition_not_authoritative",
                    ],
                    "validator_evidence_gaps": ["allowed_gap", "https://secret.invalid"],
                    "traceback": "must not persist",
                }

        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            plan = self._plan(root, "m3-f02")
            result = consumer.consume_case_once(
                plan,
                b'{"model":"final"}\n',
                compose_once=mock.Mock(side_effect=StructuredFailure()),
                validate_once=mock.Mock(),
            )

            receipt = json.loads(
                self._path(plan, "composer_invocation_receipt_json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(result["status"], "processing_failed")
        self.assertEqual(receipt["failure_stage"], "m3_validation")
        self.assertEqual(receipt["failure_code"], "invalid_composed_m3_bundle")
        self.assertEqual(receipt["contract_errors"], ["allowed_contract_code"])
        self.assertEqual(
            receipt["validator_errors"],
            [
                "method_card_pivot_condition_not_authoritative",
                "method_card_stop_condition_not_authoritative",
            ],
        )
        self.assertEqual(receipt["evidence_gaps"], ["allowed_gap"])
        self.assertEqual(receipt["retry_count"], 0)
        serialized = json.dumps(receipt)
        self.assertNotIn("private", serialized)
        self.assertNotIn("traceback", serialized)
        self.assertNotIn("https", serialized)

    def test_validator_failure_after_composition_records_bounded_invocations(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            plan = self._plan(root)
            compose = mock.Mock(return_value={"bundle": "composed"})
            validate = mock.Mock(side_effect=RuntimeError("validator private detail"))

            result = consumer.consume_case_once(
                plan,
                b'{"model":"final"}\n',
                compose_once=compose,
                validate_once=validate,
            )

            self.assertEqual(result["status"], "processing_failed")
            self.assertEqual(result["record"]["task_finalizations_observed"], 1)
            self.assertEqual(result["record"]["composer_invocations"], 1)
            self.assertEqual(result["record"]["validator_invocations"], 1)
            self.assertTrue(self._path(plan, "validator_receipt_json").exists())
            self.assertNotIn("validator private detail", self._path(plan, "case_transaction_json").read_text())

    def test_existing_sentinel_blocks_before_any_invocation(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            plan = self._plan(root)
            sentinel = self._path(plan, "model_final_json")
            sentinel.write_text("sentinel\n", encoding="utf-8", newline="\n")
            compose = mock.Mock()
            validate = mock.Mock()

            result = consumer.consume_case_once(
                plan,
                b'{"model":"final"}\n',
                compose_once=compose,
                validate_once=validate,
            )

            self.assertEqual(result["status"], "blocked")
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "sentinel\n")
            compose.assert_not_called()
            validate.assert_not_called()


if __name__ == "__main__":
    unittest.main()
