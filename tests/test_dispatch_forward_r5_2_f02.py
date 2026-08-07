from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "evals" / "m3"))

import dispatch_forward_r5_2_f02 as dispatch  # noqa: E402


MANIFEST = (
    REPO_ROOT
    / "evals"
    / "m3"
    / "forward-inputs-r5.2-f02"
    / "manifest.json"
)


class DispatchForwardR52F02Tests(unittest.TestCase):
    def test_valid_gate_2_preflight_never_invokes_callback(self):
        callback = mock.Mock()

        result = dispatch.preflight_dispatch(MANIFEST, callback)

        self.assertEqual(result["status"], "gate_2_preparation_ready")
        self.assertEqual(result["reason"], "fresh_run_not_authorized")
        self.assertEqual(result["callback_invocations"], 0)
        self.assertEqual(result["counters"], dispatch.ZERO_COUNTERS)
        self.assertEqual(result["side_effects"], [])
        callback.assert_not_called()

    def test_invalid_audit_never_invokes_callback(self):
        callback = mock.Mock()
        with mock.patch.object(
            dispatch,
            "audit_preparation",
            return_value={"status": "invalid", "errors": ["manifest_invalid"]},
        ):
            result = dispatch.preflight_dispatch(MANIFEST, callback)

        self.assertEqual(result["status"], "invalid")
        self.assertEqual(result["callback_invocations"], 0)
        self.assertIn("manifest_invalid", result["errors"])
        callback.assert_not_called()

    def test_gate_3_receipt_is_not_consumed_by_gate_2_dispatcher(self):
        callback = mock.Mock()
        receipt = {
            "revision": "r5.2-f02",
            "authorized": True,
            "prompt_sha256": "0" * 64,
            "input_binding_sha256": "1" * 64,
            "authorized_task_count": 1,
        }

        result = dispatch.preflight_dispatch(
            MANIFEST, callback, authorization_receipt=receipt
        )

        self.assertEqual(result["status"], "invalid")
        self.assertEqual(result["reason"], "gate_3_receipt_forbidden_in_gate_2")
        self.assertEqual(result["callback_invocations"], 0)
        callback.assert_not_called()

    def test_only_r5_2_f02_identity_is_accepted(self):
        callback = mock.Mock()
        for case_id, revision in (("m3-f01", "r5.2-f02"), ("m3-f02", "r6")):
            with self.subTest(case_id=case_id, revision=revision):
                result = dispatch.preflight_dispatch(
                    MANIFEST,
                    callback,
                    case_id=case_id,
                    revision=revision,
                )
                self.assertEqual(result["status"], "invalid")
                self.assertEqual(result["callback_invocations"], 0)
        callback.assert_not_called()


if __name__ == "__main__":
    unittest.main()
