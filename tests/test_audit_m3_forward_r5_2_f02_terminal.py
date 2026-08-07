from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "evals" / "m3"))

import audit_forward_r5_2_f02_terminal as audit  # noqa: E402
import consume_forward_r5_2_f02_once as consume  # noqa: E402
import r5_2_f02_execution_contract as contract  # noqa: E402


TASK_ID = "019fffff-0000-7000-8000-000000000001"
MODEL_ID = "gpt-default-observed"


class AuditM3ForwardR52F02TerminalTests(unittest.TestCase):
    def _observation(self, raw: bytes) -> dict:
        return {
            "schema_version": "m3.1-r5.2-f02-raw-response-observation-v1",
            "revision": "r5.2-f02",
            "case_id": "m3-f02",
            "task_id": TASK_ID,
            "model_id": MODEL_ID,
            "request_id": None,
            "request_id_status": "not_exposed",
            "finalization_id": "finalization-observed-1",
            "raw_response_path": "m3-f02.model-final.raw",
            "raw_output_bytes": len(raw),
            "raw_output_sha256": hashlib.sha256(raw).hexdigest(),
            "finish_reason": None,
            "finish_reason_status": "not_exposed",
            "input_tokens": None,
            "input_tokens_status": "not_exposed",
            "output_tokens": None,
            "output_tokens_status": "not_exposed",
            "task_created_at": "2026-08-07T12:00:01Z",
            "task_completed_at": "2026-08-07T12:00:10Z",
            "request_envelope_sha256": contract.expected_request_envelope_sha256(),
            "model_visible_messages_sha256": contract.expected_model_visible_messages_sha256(),
        }

    def _root_with_launch(self, temp_dir: str) -> Path:
        root = Path(temp_dir)
        (root / ".gitkeep").write_bytes(b"")
        authorization_raw = contract.AUTHORIZATION_PATH.read_bytes()
        control_raw = contract.CONTROL_PATH.read_bytes()
        attempt = contract.build_launch_attempt(
            authorization_raw,
            control_raw,
            observed_at="2026-08-07T12:00:00Z",
        )
        contract.write_new_json(root / contract.LAUNCH_ATTEMPT_NAME, attempt)
        contract.write_new_json(
            root / contract.LAUNCH_RECEIPT_NAME,
            contract.build_launch_receipt(
                attempt,
                task_id=TASK_ID,
                model_id=MODEL_ID,
                task_created_at="2026-08-07T12:00:01Z",
            ),
        )
        return root

    def _audit(self, root: Path) -> dict:
        with mock.patch.object(audit, "_historical_tree_clean", return_value=True):
            return audit.audit_terminal(root)

    def test_repository_terminal_evidence_is_accepted(self):
        result = audit.audit_terminal(
            compose_once=audit._production_compose,
            validate_once=audit._production_validate,
        )
        self.assertEqual(result["status"], "accepted")
        self.assertTrue(result["accepted"])
        self.assertEqual(
            result["counters"],
            {
                "tasks": 1,
                "finalizations": 1,
                "composer": 1,
                "validator": 1,
                "retry": 0,
            },
        )
        self.assertEqual(result["raw_output_bytes"], 14532)
        self.assertEqual(
            result["raw_output_sha256"],
            "a8ec9c94fe5b55555dd1907e770054aacb5d396d050175b18d0f8d435c97eac7",
        )
        self.assertEqual(result["unexpected_artifacts"], [])
        self.assertEqual(result["side_effects"], [])
        self.assertEqual(result["gate_4"], "NOT_STARTED")
        self.assertEqual(result["errors"], [])

    def test_accepts_complete_success_terminal(self):
        raw = b'{"coaching_mode":"route_specific","method_cards":[],"domain_overlays":[]}'
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = self._root_with_launch(temp_dir)
            consume.consume_final_once(
                contract.AUTHORIZATION_PATH,
                task_id=TASK_ID,
                final_raw=raw,
                observation=self._observation(raw),
                result_root=root,
                compose_once=lambda source, payload: {"bundle": "accepted"},
                validate_once=lambda bundle: {"status": "valid", "errors": [], "evidence_gaps": []},
            )
            result = self._audit(root)
        self.assertEqual(result["status"], "accepted")
        self.assertTrue(result["accepted"])
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["unexpected_artifacts"], [])

    def test_accepts_terminal_failure_without_relabeling(self):
        raw = b"authorization required"
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = self._root_with_launch(temp_dir)
            consume.consume_final_once(
                contract.AUTHORIZATION_PATH,
                task_id=TASK_ID,
                final_raw=raw,
                observation=self._observation(raw),
                result_root=root,
                compose_once=lambda source, payload: {},
                validate_once=lambda bundle: {"status": "valid", "errors": [], "evidence_gaps": []},
            )
            result = self._audit(root)
        self.assertEqual(result["status"], "terminal_not_accepted")
        self.assertFalse(result["accepted"])
        self.assertEqual(result["errors"], [])

    def test_raw_tamper_or_unexpected_artifact_is_invalid(self):
        raw = b"authorization required"
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = self._root_with_launch(temp_dir)
            consume.consume_final_once(
                contract.AUTHORIZATION_PATH,
                task_id=TASK_ID,
                final_raw=raw,
                observation=self._observation(raw),
                result_root=root,
                compose_once=lambda source, payload: {},
                validate_once=lambda bundle: {"status": "valid", "errors": [], "evidence_gaps": []},
            )
            (root / "m3-f02.model-final.raw").write_bytes(b"tampered")
            (root / "unexpected.bin").write_bytes(b"x")
            result = self._audit(root)
        self.assertEqual(result["status"], "invalid")
        self.assertIn("raw_observation_byte_length_mismatch", result["errors"])
        self.assertIn("unexpected_result_artifacts", result["errors"])


if __name__ == "__main__":
    unittest.main()
