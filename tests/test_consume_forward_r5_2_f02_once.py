from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "evals" / "m3"))

import consume_forward_r5_2_f02_once as consume  # noqa: E402
import r5_2_f02_execution_contract as contract  # noqa: E402


TASK_ID = "019fffff-0000-7000-8000-000000000001"
MODEL_ID = "gpt-default-observed"


class ConsumeForwardR52F02OnceTests(unittest.TestCase):
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
        launch = contract.build_launch_receipt(
            attempt,
            task_id=TASK_ID,
            model_id=MODEL_ID,
            task_created_at="2026-08-07T12:00:01Z",
        )
        contract.write_new_json(root / contract.LAUNCH_RECEIPT_NAME, launch)
        return root

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

    def test_valid_final_is_composed_and_validated_once(self):
        raw = b'{"coaching_mode":"route_specific","method_cards":[],"domain_overlays":[]}'
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = self._root_with_launch(temp_dir)
            callback_counts = {"composer": 0, "validator": 0}

            def compose_once(source: dict, payload: dict) -> dict:
                callback_counts["composer"] += 1
                self.assertTrue((root / "m3-f02.model-final.raw").exists())
                self.assertTrue((root / "m3-f02.raw-response-observation.json").exists())
                self.assertEqual(payload["coaching_mode"], "route_specific")
                return {"bundle": "accepted"}

            def validate_once(bundle: dict) -> dict:
                callback_counts["validator"] += 1
                self.assertEqual(bundle, {"bundle": "accepted"})
                return {"status": "valid", "errors": [], "evidence_gaps": []}

            result = consume.consume_final_once(
                contract.AUTHORIZATION_PATH,
                task_id=TASK_ID,
                final_raw=raw,
                observation=self._observation(raw),
                result_root=root,
                compose_once=compose_once,
                validate_once=validate_once,
            )

            self.assertEqual(result["status"], "accepted")
            self.assertTrue(result["accepted"])
            self.assertEqual(
                result["counters"],
                {"tasks": 1, "finalizations": 1, "composer": 1, "validator": 1, "retry": 0},
            )
            self.assertEqual(callback_counts, {"composer": 1, "validator": 1})
            self.assertEqual((root / "m3-f02.model-final.raw").read_bytes(), raw)
            terminal = json.loads((root / "terminal-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(terminal["status"], "accepted")

    def test_invalid_json_is_frozen_before_parser_and_never_validated(self):
        raw = b"authorization required"
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = self._root_with_launch(temp_dir)
            callbacks = {"composer": 0, "validator": 0}

            def compose_once(source: dict, payload: dict) -> dict:
                callbacks["composer"] += 1
                return {}

            def validate_once(bundle: dict) -> dict:
                callbacks["validator"] += 1
                return {"status": "valid", "errors": [], "evidence_gaps": []}

            result = consume.consume_final_once(
                contract.AUTHORIZATION_PATH,
                task_id=TASK_ID,
                final_raw=raw,
                observation=self._observation(raw),
                result_root=root,
                compose_once=compose_once,
                validate_once=validate_once,
            )

            self.assertEqual(result["status"], "terminal_not_accepted")
            self.assertFalse(result["accepted"])
            self.assertEqual(
                result["counters"],
                {"tasks": 1, "finalizations": 1, "composer": 1, "validator": 0, "retry": 0},
            )
            self.assertEqual(callbacks, {"composer": 0, "validator": 0})
            self.assertEqual((root / "m3-f02.model-final.raw").read_bytes(), raw)
            self.assertTrue((root / "m3-f02.raw-response-observation.json").exists())

    def test_validator_rejection_is_terminal_without_retry(self):
        raw = b'{"coaching_mode":"route_specific","method_cards":[],"domain_overlays":[]}'
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = self._root_with_launch(temp_dir)
            result = consume.consume_final_once(
                contract.AUTHORIZATION_PATH,
                task_id=TASK_ID,
                final_raw=raw,
                observation=self._observation(raw),
                result_root=root,
                compose_once=lambda source, payload: {"bundle": "rejected"},
                validate_once=lambda bundle: {
                    "status": "invalid",
                    "errors": ["validator_rejected"],
                    "evidence_gaps": [],
                },
            )
            self.assertEqual(result["status"], "terminal_not_accepted")
            self.assertEqual(result["counters"]["validator"], 1)
            self.assertEqual(result["counters"]["retry"], 0)

    def test_second_finalization_is_blocked_without_overwrite(self):
        raw = b'{"coaching_mode":"route_specific","method_cards":[],"domain_overlays":[]}'
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = self._root_with_launch(temp_dir)
            first = consume.consume_final_once(
                contract.AUTHORIZATION_PATH,
                task_id=TASK_ID,
                final_raw=raw,
                observation=self._observation(raw),
                result_root=root,
                compose_once=lambda source, payload: {"bundle": "accepted"},
                validate_once=lambda bundle: {"status": "valid", "errors": [], "evidence_gaps": []},
            )
            before = (root / "m3-f02.model-final.raw").read_bytes()
            second = consume.consume_final_once(
                contract.AUTHORIZATION_PATH,
                task_id=TASK_ID,
                final_raw=b"{}",
                observation=self._observation(b"{}"),
                result_root=root,
                compose_once=lambda source, payload: {},
                validate_once=lambda bundle: {"status": "valid", "errors": [], "evidence_gaps": []},
            )
            self.assertEqual(first["status"], "accepted")
            self.assertEqual(second["status"], "already_consumed")
            self.assertEqual((root / "m3-f02.model-final.raw").read_bytes(), before)

    def test_observation_mismatch_blocks_before_finalization(self):
        raw = b"{}"
        observation = self._observation(raw)
        observation["raw_output_bytes"] = 999
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = self._root_with_launch(temp_dir)
            result = consume.consume_final_once(
                contract.AUTHORIZATION_PATH,
                task_id=TASK_ID,
                final_raw=raw,
                observation=observation,
                result_root=root,
                compose_once=lambda source, payload: {},
                validate_once=lambda bundle: {"status": "valid", "errors": [], "evidence_gaps": []},
            )
            self.assertEqual(result["status"], "blocked")
            self.assertFalse((root / "m3-f02.model-final.raw").exists())


if __name__ == "__main__":
    unittest.main()
