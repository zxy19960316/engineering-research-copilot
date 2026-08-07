from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "evals" / "m3"))

import dispatch_forward_r5_1_f02 as dispatch  # noqa: E402


MANIFEST = (
    REPO_ROOT
    / "evals"
    / "m3"
    / "forward-inputs-r5.1-f02"
    / "authorization-manifest.json"
)


class DispatchForwardR51F02Tests(unittest.TestCase):
    def test_invalid_preflight_refuses_callback(self):
        value = json.loads(MANIFEST.read_text(encoding="utf-8"))
        value["preparation_baseline_head"] = "0" * 40
        callback = mock.Mock()
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            path = Path(temp_dir) / "authorization-manifest.json"
            path.write_text(
                json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                + "\n",
                encoding="utf-8",
                newline="\n",
            )
            result = dispatch.preflight_dispatch(path, callback)

        self.assertEqual(result["status"], "invalid")
        self.assertEqual(result["callback_invocations"], 0)
        callback.assert_not_called()

    def test_ready_preflight_still_refuses_callback_without_fresh_authorization(self):
        callback = mock.Mock()
        result = dispatch.preflight_dispatch(MANIFEST, callback)

        self.assertEqual(result["status"], "ready_for_fresh_authorization")
        self.assertEqual(result["callback_invocations"], 0)
        self.assertEqual(result["reason"], "fresh_run_not_authorized")
        callback.assert_not_called()

    def test_only_r5_1_f02_identity_is_accepted(self):
        callback = mock.Mock()
        for case_id, revision in (("m3-f01", "r5.1-f02"), ("m3-f02", "r6")):
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
