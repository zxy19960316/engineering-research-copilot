from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "evals" / "m3"))

import r5_1_f02_execution_contract as contract  # noqa: E402


AUTHORIZATION = (
    REPO_ROOT
    / "evals"
    / "m3"
    / "forward-inputs-r5.1-f02"
    / "execution-authorization.json"
)


class R51F02ExecutionContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.authorization = json.loads(AUTHORIZATION.read_text(encoding="utf-8"))

    def test_frozen_authorization_has_closed_one_shot_shape(self):
        self.assertEqual(
            contract.validate_execution_authorization_shape(self.authorization), []
        )
        self.assertEqual(
            self.authorization["authorization_token"],
            contract.expected_authorization_token(self.authorization),
        )

    def test_authorization_rejects_non_one_limits_and_unsafe_permissions(self):
        mutations = {
            "max_fresh_tasks": 2,
            "max_finalizations": 0,
            "max_composer_invocations": True,
            "max_validator_invocations": 3,
            "retry_allowed": True,
            "repair_allowed": True,
            "second_finalization_allowed": True,
            "historical_task_reuse_allowed": True,
            "historical_result_root_reuse_allowed": True,
            "cross_revision_aggregation_authorized": True,
            "m3_closure_authorized": True,
            "m4_authorized": True,
        }
        for field, replacement in mutations.items():
            with self.subTest(field=field):
                value = dict(self.authorization)
                value[field] = replacement
                self.assertIn(
                    f"execution_authorization_field_invalid:{field}",
                    contract.validate_execution_authorization_shape(value),
                )

    def test_reserved_task_id_must_remain_null_before_launch(self):
        value = dict(self.authorization)
        value["reserved_task_id"] = contract.HISTORICAL_TASK_ID
        errors = contract.validate_execution_authorization_shape(value)
        self.assertIn("reserved_task_id_must_be_null", errors)

    def test_launch_receipt_accepts_one_new_task_and_rejects_historical_task(self):
        receipt = contract.build_launch_receipt(
            self.authorization,
            task_id="019fffff-0000-7000-8000-000000000001",
            status="launched",
            errors=[],
        )
        self.assertEqual(
            contract.validate_launch_receipt(receipt, self.authorization), []
        )
        receipt["fresh_task_id"] = contract.HISTORICAL_TASK_ID
        self.assertIn(
            "historical_task_id_reuse_forbidden",
            contract.validate_launch_receipt(receipt, self.authorization),
        )

    def test_launch_failure_receipt_is_terminal_and_has_no_task_binding(self):
        receipt = contract.build_launch_receipt(
            self.authorization,
            task_id=None,
            status="launch_failed",
            errors=["fresh_context_launch_failed"],
        )
        self.assertEqual(
            contract.validate_launch_receipt(receipt, self.authorization), []
        )
        self.assertTrue(receipt["no_retry"])

    def test_exclusive_writer_refuses_launch_receipt_overwrite(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            path = Path(temp_dir) / "m3-f02.launch.json"
            contract.write_new_json(path, {"first": True})
            first = path.read_bytes()
            with self.assertRaises(FileExistsError):
                contract.write_new_json(path, {"second": True})
            self.assertEqual(path.read_bytes(), first)


if __name__ == "__main__":
    unittest.main()
