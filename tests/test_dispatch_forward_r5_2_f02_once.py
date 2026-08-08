from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "evals" / "m3"))

import dispatch_forward_r5_2_f02_once as dispatch  # noqa: E402


AUTHORIZATION = (
    REPO_ROOT
    / "evals"
    / "m3"
    / "forward-inputs-r5.2-f02"
    / "execution-authorization.json"
)


class DispatchForwardR52F02OnceTests(unittest.TestCase):
    def _root(self, temp_dir: str) -> Path:
        root = Path(temp_dir)
        (root / ".gitkeep").write_bytes(b"")
        return root

    def test_preflight_is_read_only(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = self._root(temp_dir)
            before = {
                path.name: path.read_bytes() for path in root.iterdir()
            }
            result = dispatch.preflight_execution(AUTHORIZATION, result_root=root)
            after = {
                path.name: path.read_bytes() for path in root.iterdir()
            }
        self.assertEqual(result["status"], "ready_for_one_shot_fresh_execution")
        self.assertEqual(result["callback_invocations"], 0)
        self.assertEqual(result["side_effects"], [])
        self.assertEqual(after, before)

    def test_claim_is_exclusive_and_consumes_attempt_budget(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = self._root(temp_dir)
            with mock.patch.object(
                dispatch,
                "audit_execution_authorization",
                return_value={"status": "ready_for_one_shot_fresh_execution", "errors": []},
            ):
                first = dispatch.claim_launch_once(
                    AUTHORIZATION,
                    result_root=root,
                    observed_at="2026-08-07T12:00:00Z",
                )
                second = dispatch.claim_launch_once(
                    AUTHORIZATION,
                    result_root=root,
                    observed_at="2026-08-07T12:00:01Z",
                )

            self.assertEqual(first["status"], "launch_claimed")
            self.assertEqual(first["task_count"], 0)
            self.assertEqual(second["status"], "already_consumed")
            self.assertEqual(second["side_effects"], [])
            self.assertEqual(
                sorted(path.name for path in root.iterdir()),
                [".gitkeep", "m3-f02.launch-attempt.json"],
            )

    def test_invalid_preflight_never_creates_claim(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = self._root(temp_dir)
            with mock.patch.object(
                dispatch,
                "audit_execution_authorization",
                return_value={"status": "invalid", "errors": ["not_ready"]},
            ):
                result = dispatch.claim_launch_once(
                    AUTHORIZATION,
                    result_root=root,
                    observed_at="2026-08-07T12:00:00Z",
                )
            self.assertEqual(result["status"], "invalid")
            self.assertFalse((root / "m3-f02.launch-attempt.json").exists())

    def test_record_launch_binds_one_new_task(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = self._root(temp_dir)
            with mock.patch.object(
                dispatch,
                "audit_execution_authorization",
                return_value={"status": "ready_for_one_shot_fresh_execution", "errors": []},
            ):
                dispatch.claim_launch_once(
                    AUTHORIZATION,
                    result_root=root,
                    observed_at="2026-08-07T12:00:00Z",
                )
            result = dispatch.record_launch_once(
                AUTHORIZATION,
                task_id="019fffff-0000-7000-8000-000000000001",
                model_id="gpt-default-observed",
                task_created_at="2026-08-07T12:00:01Z",
                result_root=root,
            )
            second = dispatch.record_launch_once(
                AUTHORIZATION,
                task_id="019fffff-0000-7000-8000-000000000002",
                model_id="gpt-default-observed",
                task_created_at="2026-08-07T12:00:02Z",
                result_root=root,
            )
            self.assertEqual(result["status"], "launched")
            self.assertEqual(result["task_count"], 1)
            self.assertEqual(second["status"], "already_consumed")

    def test_historical_task_id_is_rejected_without_receipt(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = self._root(temp_dir)
            with mock.patch.object(
                dispatch,
                "audit_execution_authorization",
                return_value={"status": "ready_for_one_shot_fresh_execution", "errors": []},
            ):
                dispatch.claim_launch_once(
                    AUTHORIZATION,
                    result_root=root,
                    observed_at="2026-08-07T12:00:00Z",
                )
            result = dispatch.record_launch_once(
                AUTHORIZATION,
                task_id="019fdb7c-1728-7a92-b6cf-b0eb631a18b8",
                model_id="gpt-default-observed",
                task_created_at="2026-08-07T12:00:01Z",
                result_root=root,
            )
            self.assertEqual(result["status"], "invalid")
            self.assertFalse((root / "m3-f02.launch.json").exists())


if __name__ == "__main__":
    unittest.main()
