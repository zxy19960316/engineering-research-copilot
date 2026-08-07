from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "evals" / "m3"))

import audit_forward_r5_2_f02_execution_authorization as audit  # noqa: E402


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


class AuditM3ForwardR52F02ExecutionAuthorizationTests(unittest.TestCase):
    def _write_json(self, root: Path, name: str, source: Path, mutate) -> Path:
        value = json.loads(source.read_text(encoding="utf-8"))
        mutate(value)
        path = root / name
        path.write_text(
            json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
        return path

    def test_accepts_one_shot_authorization_without_writes(self):
        before_auth = AUTHORIZATION.read_bytes()
        before_control = CONTROL.read_bytes()
        before_root = {
            path.name: path.read_bytes() for path in audit.RESULT_ROOT.iterdir()
        }

        result = audit.audit_execution_authorization(AUTHORIZATION)

        after_root = {
            path.name: path.read_bytes() for path in audit.RESULT_ROOT.iterdir()
        }
        self.assertEqual(result["status"], "ready_for_one_shot_fresh_execution")
        self.assertEqual(result["readiness_head"], audit.GATE_2_HEAD)
        self.assertEqual(result["readiness_ci_run_id"], audit.GATE_2_CI_RUN_ID)
        self.assertEqual(result["logical_result_artifact_count"], 0)
        self.assertEqual(
            result["counters"],
            {
                "tasks": 0,
                "finalizations": 0,
                "composer": 0,
                "validator": 0,
                "retry": 0,
            },
        )
        self.assertEqual(result["callback_invocations"], 0)
        self.assertEqual(result["side_effects"], [])
        self.assertEqual(result["errors"], [])
        self.assertEqual(AUTHORIZATION.read_bytes(), before_auth)
        self.assertEqual(CONTROL.read_bytes(), before_control)
        self.assertEqual(after_root, before_root)

    def test_rejects_receipt_drift(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            path = self._write_json(
                Path(temp_dir),
                "authorization.json",
                AUTHORIZATION,
                lambda value: value.__setitem__("authorized_task_count", 2),
            )
            result = audit.audit_execution_authorization(path)

        self.assertEqual(result["status"], "invalid")
        self.assertIn("authorization_receipt_task_count_invalid", result["errors"])
        self.assertIn("authorization_receipt_control_hash_mismatch", result["errors"])

    def test_rejects_control_request_or_permission_drift(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            request_path = self._write_json(
                root,
                "request-control.json",
                CONTROL,
                lambda value: value["task_request"].__setitem__(
                    "request_envelope_sha256", "0" * 64
                ),
            )
            permission_path = self._write_json(
                root,
                "permission-control.json",
                CONTROL,
                lambda value: value["permissions"].__setitem__(
                    "retry_allowed", True
                ),
            )
            request_result = audit.audit_execution_authorization(
                AUTHORIZATION, control_path=request_path
            )
            permission_result = audit.audit_execution_authorization(
                AUTHORIZATION, control_path=permission_path
            )

        self.assertIn(
            "execution_control_task_request_invalid", request_result["errors"]
        )
        self.assertIn(
            "execution_control_permission_invalid:retry_allowed",
            permission_result["errors"],
        )

    def test_rejects_nonempty_result_root(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            (root / ".gitkeep").write_bytes(b"")
            (root / "m3-f02.launch-attempt.json").write_bytes(b"{}\n")
            result = audit.audit_execution_authorization(
                AUTHORIZATION, result_root=root
            )

        self.assertEqual(result["logical_result_artifact_count"], 1)
        self.assertIn("result_root_not_logically_empty", result["errors"])

    def test_rejects_gate_2_blob_or_ancestry_drift(self):
        with mock.patch.object(
            audit,
            "_gate_2_snapshot_errors",
            return_value=["gate_2_frozen_blob_changed:manifest.json"],
        ):
            result = audit.audit_execution_authorization(AUTHORIZATION)
        self.assertIn("gate_2_frozen_blob_changed:manifest.json", result["errors"])

    def test_gate_2_snapshot_compares_git_blobs_not_platform_worktree_bytes(self):
        completed = mock.Mock(returncode=0)
        with (
            mock.patch.object(audit.subprocess, "run", return_value=completed),
            mock.patch.object(audit, "_git_blob", return_value=b"frozen-git-bytes"),
            mock.patch.object(
                Path,
                "read_bytes",
                side_effect=AssertionError("worktree bytes must not define Git identity"),
            ),
        ):
            self.assertEqual(audit._gate_2_snapshot_errors(), [])

    def test_rejects_historical_tree_drift(self):
        with mock.patch.object(
            audit,
            "_historical_tree_clean",
            side_effect=[False, False],
        ):
            result = audit.audit_execution_authorization(AUTHORIZATION)
        self.assertIn("immutable_forward_r5_changed", result["errors"])
        self.assertIn("immutable_forward_r5_1_f02_changed", result["errors"])

    def test_rejects_nonzero_prelaunch_counter(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            path = self._write_json(
                Path(temp_dir),
                "control.json",
                CONTROL,
                lambda value: value["prelaunch_counters"].__setitem__("tasks", 1),
            )
            result = audit.audit_execution_authorization(
                AUTHORIZATION, control_path=path
            )
        self.assertIn("execution_control_counter_nonzero:tasks", result["errors"])


if __name__ == "__main__":
    unittest.main()
