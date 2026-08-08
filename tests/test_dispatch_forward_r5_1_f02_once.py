from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "evals" / "m3"))

import dispatch_forward_r5_1_f02_once as dispatch  # noqa: E402


AUTHORIZATION = (
    REPO_ROOT
    / "evals"
    / "m3"
    / "forward-inputs-r5.1-f02"
    / "execution-authorization.json"
)
NEW_TASK_ID = "019fffff-0000-7000-8000-000000000001"


class DispatchForwardR51F02OnceTests(unittest.TestCase):
    @staticmethod
    def _frozen_ready_audit() -> dict:
        authorization = json.loads(AUTHORIZATION.read_text(encoding="utf-8"))
        return {
            "status": "ready_for_one_shot_fresh_execution",
            "authorization_token": authorization["authorization_token"],
            "errors": [],
        }

    def _invalid_authorization(self, root: Path) -> Path:
        value = json.loads(AUTHORIZATION.read_text(encoding="utf-8"))
        value["readiness_ci_run_id"] = 1
        path = root / "execution-authorization.json"
        path.write_text(
            json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
        return path

    def test_dry_run_preflight_has_zero_callback_and_zero_side_effects(self):
        callback = mock.Mock()
        before = {path.name: path.read_bytes() for path in dispatch.RESULT_ROOT.iterdir()}
        with mock.patch.object(
            dispatch,
            "audit_execution_authorization",
            return_value=self._frozen_ready_audit(),
        ):
            result = dispatch.preflight_execution(AUTHORIZATION)
        after = {path.name: path.read_bytes() for path in dispatch.RESULT_ROOT.iterdir()}
        self.assertEqual(result["status"], "ready_for_one_shot_fresh_execution")
        self.assertEqual(result["callback_invocations"], 0)
        self.assertIsNone(result["task_id"])
        self.assertEqual(result["side_effects"], [])
        self.assertEqual(after, before)
        callback.assert_not_called()

    def test_invalid_preflight_never_calls_callback(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            callback = mock.Mock()
            path = self._invalid_authorization(Path(temp_dir))
            result = dispatch.dispatch_authorized_once(path, callback)
        self.assertEqual(result["status"], "invalid")
        self.assertEqual(result["callback_invocations"], 0)
        callback.assert_not_called()

    def test_success_binds_one_new_task_and_second_dispatch_is_forbidden(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            callback = mock.Mock(return_value=NEW_TASK_ID)
            with (
                mock.patch.object(dispatch, "RESULT_ROOT", root),
                mock.patch.object(
                    dispatch,
                    "audit_execution_authorization",
                    return_value=self._frozen_ready_audit(),
                ),
            ):
                first = dispatch.dispatch_authorized_once(AUTHORIZATION, callback)
                second_callback = mock.Mock(return_value="second-task")
                second = dispatch.dispatch_authorized_once(
                    AUTHORIZATION, second_callback
                )
            receipt = json.loads((root / "m3-f02.launch.json").read_text(encoding="utf-8"))

        self.assertEqual(first["status"], "launched")
        self.assertEqual(first["callback_invocations"], 1)
        self.assertEqual(first["task_id"], NEW_TASK_ID)
        self.assertEqual(receipt["fresh_task_id"], NEW_TASK_ID)
        callback.assert_called_once_with()
        self.assertEqual(second["status"], "already_consumed")
        self.assertEqual(second["callback_invocations"], 0)
        second_callback.assert_not_called()

    def test_historical_task_id_consumes_attempt_and_cannot_retry(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            callback = mock.Mock(return_value=dispatch.HISTORICAL_TASK_ID)
            with (
                mock.patch.object(dispatch, "RESULT_ROOT", root),
                mock.patch.object(
                    dispatch,
                    "audit_execution_authorization",
                    return_value=self._frozen_ready_audit(),
                ),
            ):
                first = dispatch.dispatch_authorized_once(AUTHORIZATION, callback)
                retry = mock.Mock(return_value=NEW_TASK_ID)
                second = dispatch.dispatch_authorized_once(AUTHORIZATION, retry)
            receipt = json.loads((root / "m3-f02.launch.json").read_text(encoding="utf-8"))
        self.assertEqual(first["status"], "launch_failed")
        self.assertIn("historical_task_id_reuse_forbidden", first["errors"])
        self.assertEqual(receipt["launch_status"], "launch_failed")
        self.assertEqual(second["status"], "already_consumed")
        retry.assert_not_called()

    def test_callback_failure_is_terminal_and_cannot_retry(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            callback = mock.Mock(side_effect=RuntimeError("private launch detail"))
            with (
                mock.patch.object(dispatch, "RESULT_ROOT", root),
                mock.patch.object(
                    dispatch,
                    "audit_execution_authorization",
                    return_value=self._frozen_ready_audit(),
                ),
            ):
                first = dispatch.dispatch_authorized_once(AUTHORIZATION, callback)
                retry = mock.Mock(return_value=NEW_TASK_ID)
                second = dispatch.dispatch_authorized_once(AUTHORIZATION, retry)
            receipt_raw = (root / "m3-f02.launch.json").read_text(encoding="utf-8")
        self.assertEqual(first["status"], "launch_failed")
        self.assertEqual(first["errors"], ["fresh_context_launch_failed"])
        self.assertNotIn("private launch detail", receipt_raw)
        self.assertEqual(second["status"], "already_consumed")
        retry.assert_not_called()

    def test_final_bytes_are_preserved_and_consumed_only_once(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            compose = mock.Mock(return_value={"bundle": "composed"})
            validate = mock.Mock(return_value={"status": "valid", "accepted": True})
            final_raw = b'{"model":"final"}\r\n'
            with (
                mock.patch.object(dispatch, "RESULT_ROOT", root),
                mock.patch.object(
                    dispatch,
                    "audit_execution_authorization",
                    return_value=self._frozen_ready_audit(),
                ),
            ):
                launch = dispatch.dispatch_authorized_once(
                    AUTHORIZATION, lambda: NEW_TASK_ID
                )
                first = dispatch.finalize_authorized_once(
                    AUTHORIZATION,
                    NEW_TASK_ID,
                    final_raw,
                    compose_once=compose,
                    validate_once=validate,
                )
                compose.reset_mock()
                validate.reset_mock()
                second = dispatch.finalize_authorized_once(
                    AUTHORIZATION,
                    NEW_TASK_ID,
                    b'{"model":"second"}\n',
                    compose_once=compose,
                    validate_once=validate,
                )
            preserved = (root / "m3-f02.model-final.json").read_bytes()

        self.assertEqual(launch["status"], "launched")
        self.assertEqual(first["status"], "processed")
        self.assertEqual(preserved, final_raw)
        self.assertEqual(second["status"], "blocked")
        compose.assert_not_called()
        validate.assert_not_called()

    def test_existing_result_artifact_is_not_overwritten(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            with (
                mock.patch.object(dispatch, "RESULT_ROOT", root),
                mock.patch.object(
                    dispatch,
                    "audit_execution_authorization",
                    return_value=self._frozen_ready_audit(),
                ),
            ):
                dispatch.dispatch_authorized_once(AUTHORIZATION, lambda: NEW_TASK_ID)
                model_final = root / "m3-f02.model-final.json"
                model_final.write_bytes(b"sentinel\n")
                compose = mock.Mock()
                validate = mock.Mock()
                result = dispatch.finalize_authorized_once(
                    AUTHORIZATION,
                    NEW_TASK_ID,
                    b"replacement\n",
                    compose_once=compose,
                    validate_once=validate,
                )
            preserved = model_final.read_bytes()
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(preserved, b"sentinel\n")
        compose.assert_not_called()
        validate.assert_not_called()


if __name__ == "__main__":
    unittest.main()
