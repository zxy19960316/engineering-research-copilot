from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "evals" / "m3"))

import r5_2_f02_execution_contract as contract  # noqa: E402
import r5_2_f02_protocol as protocol  # noqa: E402


AUTHORIZATION = (
    REPO_ROOT
    / "evals"
    / "m3"
    / "forward-inputs-r5.2-f02"
    / "execution-authorization.json"
)
CONTROL = (
    REPO_ROOT
    / "evals"
    / "m3"
    / "forward-inputs-r5.2-f02"
    / "m3-f02.execution-control.json"
)


class R52F02ExecutionContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.authorization_raw = AUTHORIZATION.read_bytes()
        self.authorization = json.loads(self.authorization_raw)
        self.control_raw = CONTROL.read_bytes()
        self.control = json.loads(self.control_raw)

    def test_five_field_authorization_receipt_is_exact(self):
        self.assertEqual(
            protocol.validate_authorization_receipt(
                self.authorization,
                expected_prompt_sha256=contract.PROMPT_SHA256,
                expected_input_binding_sha256=contract.INPUT_BINDING_SHA256,
            ),
            [],
        )
        self.assertEqual(
            set(self.authorization),
            {
                "revision",
                "authorized",
                "prompt_sha256",
                "input_binding_sha256",
                "authorized_task_count",
            },
        )

    def test_execution_control_is_closed_and_hash_bound(self):
        self.assertEqual(contract.validate_execution_control(self.control), [])
        self.assertEqual(
            self.control["authorization_receipt"]["raw_sha256"],
            contract.sha256(self.authorization_raw),
        )
        self.assertEqual(
            self.control["task_request"]["request_envelope_sha256"],
            contract.expected_request_envelope_sha256(),
        )
        self.assertEqual(
            self.control["task_request"]["model_visible_messages_sha256"],
            contract.expected_model_visible_messages_sha256(),
        )

    def test_execution_control_rejects_unknown_missing_or_unsafe_fields(self):
        unknown = copy.deepcopy(self.control)
        unknown["unexpected"] = True
        self.assertIn(
            "execution_control_fields_invalid",
            contract.validate_execution_control(unknown),
        )

        missing = copy.deepcopy(self.control)
        missing.pop("limits")
        self.assertIn(
            "execution_control_fields_invalid",
            contract.validate_execution_control(missing),
        )

        unsafe = copy.deepcopy(self.control)
        unsafe["permissions"]["retry_allowed"] = True
        self.assertIn(
            "execution_control_permission_invalid:retry_allowed",
            contract.validate_execution_control(unsafe),
        )

    def test_limits_and_prelaunch_counters_are_exact(self):
        self.assertEqual(
            self.control["limits"],
            {
                "tasks": 1,
                "finalizations": 1,
                "composer": 1,
                "validator": 1,
                "retry": 0,
            },
        )
        self.assertEqual(
            self.control["prelaunch_counters"],
            {
                "tasks": 0,
                "finalizations": 0,
                "composer": 0,
                "validator": 0,
                "retry": 0,
            },
        )
        drift = copy.deepcopy(self.control)
        drift["limits"]["tasks"] = True
        drift["prelaunch_counters"]["retry"] = 1
        errors = contract.validate_execution_control(drift)
        self.assertIn("execution_control_limit_invalid:tasks", errors)
        self.assertIn("execution_control_counter_nonzero:retry", errors)

    def test_task_request_omits_model_and_thinking(self):
        request = self.control["task_request"]["create_thread_arguments"]
        self.assertEqual(set(request), {"prompt", "target", "title"})
        self.assertNotIn("model", request)
        self.assertNotIn("thinking", request)
        self.assertEqual(request["prompt"], contract.PROMPT_PATH.read_text(encoding="utf-8"))

    def test_launch_attempt_and_receipt_bind_one_new_task(self):
        attempt = contract.build_launch_attempt(
            self.authorization_raw,
            self.control_raw,
            observed_at="2026-08-07T12:00:00Z",
        )
        self.assertEqual(
            contract.validate_launch_attempt(
                attempt,
                authorization_raw=self.authorization_raw,
                control_raw=self.control_raw,
            ),
            [],
        )
        receipt = contract.build_launch_receipt(
            attempt,
            task_id="019fffff-0000-7000-8000-000000000001",
            model_id="gpt-default-observed",
            task_created_at="2026-08-07T12:00:01Z",
        )
        self.assertEqual(
            contract.validate_launch_receipt(receipt, attempt=attempt),
            [],
        )

    def test_historical_or_second_task_binding_is_rejected(self):
        attempt = contract.build_launch_attempt(
            self.authorization_raw,
            self.control_raw,
            observed_at="2026-08-07T12:00:00Z",
        )
        with self.assertRaises(ValueError):
            contract.build_launch_receipt(
                attempt,
                task_id="019fdb7c-1728-7a92-b6cf-b0eb631a18b8",
                model_id="gpt-default-observed",
                task_created_at="2026-08-07T12:00:01Z",
            )

        receipt = contract.build_launch_receipt(
            attempt,
            task_id="019fffff-0000-7000-8000-000000000001",
            model_id="gpt-default-observed",
            task_created_at="2026-08-07T12:00:01Z",
        )
        errors = contract.validate_launch_receipt(
            receipt,
            attempt=attempt,
            task_id="019fffff-0000-7000-8000-000000000002",
        )
        self.assertIn("launch_receipt_task_binding_mismatch", errors)

    def test_exclusive_write_forbids_overwrite(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            path = Path(temp_dir) / "once.bin"
            contract.write_new_bytes(path, b"first")
            self.assertEqual(path.read_bytes(), b"first")
            with self.assertRaises(FileExistsError):
                contract.write_new_bytes(path, b"second")
            self.assertEqual(path.read_bytes(), b"first")


if __name__ == "__main__":
    unittest.main()
