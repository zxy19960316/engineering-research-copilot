from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "evals" / "m3"))

import r5_2_f02_protocol as protocol  # noqa: E402


CASES_PATH = (
    REPO_ROOT
    / "evals"
    / "m3"
    / "forward-inputs-r5.2-f02"
    / "protocol-regression-cases.json"
)


class R52F02StrictJsonProtocolTests(unittest.TestCase):
    def test_accepts_exactly_one_complete_json_object(self):
        result = protocol.parse_strict_json_object(b'\n {"decision":"stop"}\t')

        self.assertTrue(result.ok)
        self.assertEqual(result.value, {"decision": "stop"})
        self.assertEqual(result.classification, "json_object")
        self.assertIsNone(result.failure_code)
        self.assertIsNone(result.json_error)

    def test_rejects_fenced_object(self):
        result = protocol.parse_strict_json_object(b'```json\n{"ok":true}\n```')

        self.assertFalse(result.ok)
        self.assertEqual(result.failure_code, "payload_invalid_json")
        self.assertEqual(result.classification, "markdown_fenced_json")

    def test_rejects_leading_or_trailing_prose(self):
        samples = {
            b'Here is the object: {"ok":true}': "leading_prose",
            b'{"ok":true} done': "trailing_prose",
        }
        for raw, classification in samples.items():
            with self.subTest(raw=raw):
                result = protocol.parse_strict_json_object(raw)
                self.assertFalse(result.ok)
                self.assertEqual(result.failure_code, "payload_invalid_json")
                self.assertEqual(result.classification, classification)

    def test_rejects_truncated_object(self):
        result = protocol.parse_strict_json_object(b'{"ok":')

        self.assertFalse(result.ok)
        self.assertEqual(result.failure_code, "payload_invalid_json")
        self.assertEqual(result.classification, "truncated_json")

    def test_utf8_bom_policy_is_explicit_rejection(self):
        result = protocol.parse_strict_json_object(b"\xef\xbb\xbf{}")

        self.assertFalse(result.ok)
        self.assertEqual(result.classification, "utf8_bom")
        self.assertEqual(protocol.UTF8_BOM_POLICY, "reject")

    def test_rejects_duplicate_object_keys(self):
        result = protocol.parse_strict_json_object(b'{"key":1,"key":2}')

        self.assertFalse(result.ok)
        self.assertEqual(result.failure_code, "payload_invalid_json")
        self.assertEqual(result.classification, "duplicate_object_key")

    def test_empty_output_is_explicit_terminal_failure(self):
        result = protocol.parse_strict_json_object(b" \r\n\t")

        self.assertFalse(result.ok)
        self.assertEqual(result.failure_code, "empty_output_terminal_failure")
        self.assertEqual(result.classification, "empty_output")

    def test_authorization_refusal_is_classified_as_non_json_prose(self):
        raw = b"I cannot execute this reserved task without separate authorization."
        result = protocol.parse_strict_json_object(raw)

        self.assertFalse(result.ok)
        self.assertEqual(result.failure_code, "payload_invalid_json")
        self.assertEqual(result.classification, "non_json_prose")

    def test_rejects_non_object_roots_comments_and_non_finite_values(self):
        samples = {
            b"[]": "non_object_json",
            b'{"ok":true /* comment */}': "invalid_json_syntax",
            b'{"score":NaN}': "non_finite_json_number",
        }
        for raw, classification in samples.items():
            with self.subTest(raw=raw):
                result = protocol.parse_strict_json_object(raw)
                self.assertFalse(result.ok)
                self.assertEqual(result.classification, classification)

    def test_rejects_invalid_utf8_and_multiple_objects(self):
        samples = {
            b'{"value":"\xff"}': "invalid_utf8",
            b"{} {}": "multiple_json_values",
        }
        for raw, classification in samples.items():
            with self.subTest(raw=raw):
                result = protocol.parse_strict_json_object(raw)
                self.assertFalse(result.ok)
                self.assertEqual(result.classification, classification)


class R52F02PromptAndReceiptTests(unittest.TestCase):
    def test_prompt_lint_requires_authorized_execution_prefix(self):
        prompt = (
            "This is the authorized r5.2-f02 execution.\n"
            "Execute the frozen task now.\n"
            "Return exactly one JSON object.\n"
        )
        self.assertEqual(protocol.lint_execution_prompt(prompt), [])

        errors = protocol.lint_execution_prompt("Execute it later.\n")
        self.assertIn("authorized_execution_prefix_missing", errors)

    def test_prompt_lint_rejects_all_frozen_contradiction_phrases(self):
        prefix = (
            "This is the authorized r5.2-f02 execution.\n"
            "Execute the frozen task now.\n"
        )
        for phrase in protocol.FORBIDDEN_PROMPT_PHRASES:
            with self.subTest(phrase=phrase):
                errors = protocol.lint_execution_prompt(prefix + phrase.upper())
                self.assertIn(f"forbidden_prompt_phrase:{phrase}", errors)

    def test_authorization_receipt_is_closed_and_hash_bound(self):
        prompt_sha = hashlib.sha256(b"prompt").hexdigest()
        input_sha = hashlib.sha256(b"input").hexdigest()
        receipt = {
            "revision": "r5.2-f02",
            "authorized": True,
            "prompt_sha256": prompt_sha,
            "input_binding_sha256": input_sha,
            "authorized_task_count": 1,
        }

        self.assertEqual(
            protocol.validate_authorization_receipt(
                receipt,
                expected_prompt_sha256=prompt_sha,
                expected_input_binding_sha256=input_sha,
            ),
            [],
        )
        for field, replacement in {
            "revision": "r5.1-f02",
            "authorized": False,
            "prompt_sha256": "0" * 64,
            "input_binding_sha256": "1" * 64,
            "authorized_task_count": 2,
        }.items():
            with self.subTest(field=field):
                changed = dict(receipt)
                changed[field] = replacement
                self.assertTrue(
                    protocol.validate_authorization_receipt(
                        changed,
                        expected_prompt_sha256=prompt_sha,
                        expected_input_binding_sha256=input_sha,
                    )
                )

        changed = dict(receipt)
        changed["extra"] = True
        self.assertIn(
            "authorization_receipt_fields_invalid",
            protocol.validate_authorization_receipt(
                changed,
                expected_prompt_sha256=prompt_sha,
                expected_input_binding_sha256=input_sha,
            ),
        )

    def test_raw_observation_is_closed_and_matches_raw_bytes(self):
        raw = b'{"decision":"stop"}'
        observation = {
            "schema_version": "m3.1-r5.2-f02-raw-response-observation-v1",
            "revision": "r5.2-f02",
            "case_id": "m3-f02",
            "task_id": "new-task-id",
            "model_id": "gpt-5.6-sol",
            "request_id": "request-id",
            "request_id_status": "recorded",
            "finalization_id": "finalization-id",
            "raw_response_path": "m3-f02.model-final.raw",
            "raw_output_bytes": len(raw),
            "raw_output_sha256": hashlib.sha256(raw).hexdigest(),
            "finish_reason": "stop",
            "finish_reason_status": "recorded",
            "input_tokens": 100,
            "input_tokens_status": "recorded",
            "output_tokens": 8,
            "output_tokens_status": "recorded",
            "task_created_at": "2026-08-07T00:00:00Z",
            "task_completed_at": "2026-08-07T00:00:01Z",
            "request_envelope_sha256": "a" * 64,
            "model_visible_messages_sha256": "b" * 64,
        }

        self.assertEqual(
            protocol.validate_raw_observation(observation, raw_bytes=raw), []
        )
        changed = dict(observation)
        changed["raw_output_bytes"] += 1
        self.assertIn(
            "raw_observation_byte_length_mismatch",
            protocol.validate_raw_observation(changed, raw_bytes=raw),
        )
        changed = dict(observation)
        changed["unexpected"] = "repair"
        self.assertIn(
            "raw_observation_fields_invalid",
            protocol.validate_raw_observation(changed, raw_bytes=raw),
        )

    def test_raw_observation_marks_unexposed_provider_fields_without_inference(self):
        raw = b"{}"
        observation = {
            "schema_version": "m3.1-r5.2-f02-raw-response-observation-v1",
            "revision": "r5.2-f02",
            "case_id": "m3-f02",
            "task_id": "new-task-id",
            "model_id": "gpt-5.6-sol",
            "request_id": None,
            "request_id_status": "not_exposed",
            "finalization_id": "finalization-id",
            "raw_response_path": "m3-f02.model-final.raw",
            "raw_output_bytes": 2,
            "raw_output_sha256": hashlib.sha256(raw).hexdigest(),
            "finish_reason": None,
            "finish_reason_status": "not_exposed",
            "input_tokens": None,
            "input_tokens_status": "not_exposed",
            "output_tokens": None,
            "output_tokens_status": "not_exposed",
            "task_created_at": "2026-08-07T00:00:00Z",
            "task_completed_at": "2026-08-07T00:00:01Z",
            "request_envelope_sha256": "a" * 64,
            "model_visible_messages_sha256": "b" * 64,
        }

        self.assertEqual(
            protocol.validate_raw_observation(observation, raw_bytes=raw), []
        )


class R52F02SyntheticComposerTests(unittest.TestCase):
    def test_valid_object_reaches_validator_exactly_once(self):
        validator = mock.Mock(return_value=[])

        result = protocol.process_synthetic_final(b'{"ok":true}', validator)

        self.assertEqual(result["status"], "accepted")
        self.assertEqual(result["counters"], {"composer": 1, "validator": 1, "retry": 0})
        validator.assert_called_once_with({"ok": True})

    def test_invalid_json_fails_closed_before_validator(self):
        validator = mock.Mock(return_value=[])

        result = protocol.process_synthetic_final(
            b'```json\n{"ok":true}\n```', validator
        )

        self.assertEqual(result["status"], "terminal_not_accepted")
        self.assertEqual(result["reason"], "payload_invalid_json")
        self.assertEqual(result["counters"], {"composer": 1, "validator": 0, "retry": 0})
        validator.assert_not_called()

    def test_schema_rejection_occurs_after_composer_success(self):
        validator = mock.Mock(return_value=["required_field_missing"])

        result = protocol.process_synthetic_final(b'{"ok":true}', validator)

        self.assertEqual(result["status"], "terminal_not_accepted")
        self.assertEqual(result["reason"], "validator_rejected")
        self.assertEqual(result["counters"], {"composer": 1, "validator": 1, "retry": 0})
        self.assertEqual(result["validator_errors"], ["required_field_missing"])
        validator.assert_called_once()

    def test_frozen_regression_matrix_has_all_nine_cases(self):
        matrix = json.loads(CASES_PATH.read_text(encoding="utf-8"))
        cases = matrix["cases"]

        self.assertEqual(len(cases), 9)
        self.assertEqual(
            {case["case_id"] for case in cases},
            {
                "valid_complete_object",
                "markdown_fenced_object",
                "leading_prose_object",
                "truncated_object",
                "utf8_bom_object",
                "duplicate_keys",
                "empty_output",
                "authorization_refusal_prose",
                "valid_json_schema_rejection",
            },
        )
        for case in cases:
            with self.subTest(case_id=case["case_id"]):
                raw = (
                    bytes.fromhex(case["raw_hex"])
                    if "raw_hex" in case
                    else case["raw_text"].encode("utf-8")
                )
                validator_errors = case.get("validator_errors", [])
                result = protocol.process_synthetic_final(
                    raw, lambda _payload: validator_errors
                )
                self.assertEqual(result["status"], case["expected_status"])
                self.assertEqual(result["reason"], case["expected_reason"])
                self.assertEqual(result["counters"], case["expected_counters"])


if __name__ == "__main__":
    unittest.main()
