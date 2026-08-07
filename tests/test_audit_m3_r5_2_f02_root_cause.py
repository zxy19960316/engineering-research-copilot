from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "evals" / "m3"))

import audit_r5_2_f02_root_cause as audit  # noqa: E402


class AuditM3R52F02RootCauseTests(unittest.TestCase):
    def _report(self) -> dict:
        return json.loads(audit.REPORT.read_text(encoding="utf-8"))

    def _audit_mutation(self, mutate, **kwargs) -> dict:
        value = copy.deepcopy(self._report())
        mutate(value)
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            path = Path(temp_dir) / "root-cause-report.json"
            path.write_text(
                json.dumps(
                    value,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                + "\n",
                encoding="utf-8",
                newline="\n",
            )
            return audit.audit_report(path, **kwargs)

    def test_current_report_confirms_root_cause(self):
        result = audit.audit_report(audit.REPORT)
        self.assertEqual(result["status"], "root_cause_confirmed")
        self.assertEqual(result["errors"], [])
        self.assertEqual(
            result["primary_root_cause"],
            "authorization_not_visible_in_consumed_turn",
        )
        self.assertIs(result["fresh_execution_authorized"], False)
        self.assertEqual(result["gate2_status"], "NOT_STARTED")
        self.assertIs(result["r5_2_result_root_absent"], False)
        self.assertIs(result["r5_2_result_root_safe"], True)

    def test_required_scalar_findings_are_exact(self):
        report = self._report()
        self.assertEqual(report["revision"], "r5.1-f02")
        self.assertEqual(
            report["task_id"], "019fdb7c-1728-7a92-b6cf-b0eb631a18b8"
        )
        self.assertEqual(report["raw_output_bytes"], 216)
        self.assertEqual(
            report["raw_output_sha256"],
            "75b4f9f5f4e2459b2886c0a9654c8cc1bda4015c525869cd154a302a2bc0589a",
        )
        self.assertIs(report["utf8_valid"], True)
        self.assertIs(report["json_valid"], False)
        self.assertEqual(
            report["json_error"],
            {
                "message": "Expecting value",
                "line": 1,
                "column": 1,
                "byte_offset": 0,
            },
        )
        self.assertEqual(report["output_tokens"], 102)

    def test_context_layers_remain_distinct(self):
        layers = self._report()["context_layers"]
        self.assertEqual(
            set(layers),
            {
                "frozen_repository_prompt",
                "consumed_turn_model_visible_context",
                "external_user_authorization",
                "late_authorized_turn",
            },
        )
        self.assertIs(
            layers["consumed_turn_model_visible_context"]["authorization_visible"],
            False,
        )
        self.assertIs(layers["external_user_authorization"]["present"], True)
        self.assertIs(
            layers["external_user_authorization"]["visible_in_consumed_turn"],
            False,
        )
        self.assertIs(layers["late_authorized_turn"]["authorization_visible"], True)
        self.assertIs(
            layers["late_authorized_turn"]["occurred_after_terminal_consumption"],
            True,
        )

    def test_raw_hash_mutation_is_rejected(self):
        result = self._audit_mutation(
            lambda value: value.__setitem__("raw_output_sha256", "0" * 64)
        )
        self.assertIn("raw_output_sha256_invalid", result["errors"])

    def test_task_id_mutation_is_rejected(self):
        result = self._audit_mutation(
            lambda value: value.__setitem__(
                "task_id", "019fd687-5575-7143-8cf3-1ab3069611f5"
            )
        )
        self.assertIn("task_id_invalid", result["errors"])

    def test_consumed_turn_authorization_mutation_is_rejected(self):
        result = self._audit_mutation(
            lambda value: value["context_layers"][
                "consumed_turn_model_visible_context"
            ].__setitem__("authorization_visible", True)
        )
        self.assertIn("consumed_turn_authorization_visibility_invalid", result["errors"])

    def test_output_tokens_must_be_observed_non_boolean_integer(self):
        result = self._audit_mutation(
            lambda value: value.__setitem__("output_tokens", False)
        )
        self.assertIn("output_tokens_invalid", result["errors"])

    def test_late_turn_must_remain_outside_consumption_window(self):
        result = self._audit_mutation(
            lambda value: value["context_layers"]["late_authorized_turn"].__setitem__(
                "occurred_after_terminal_consumption", False
            )
        )
        self.assertIn("late_authorization_timing_invalid", result["errors"])

    def test_primary_root_cause_mutation_is_rejected(self):
        result = self._audit_mutation(
            lambda value: value["primary_root_cause"].__setitem__(
                "code", "model_generation_defect"
            )
        )
        self.assertIn("primary_root_cause_invalid", result["errors"])

    def test_hypotheses_have_required_order_and_closed_dispositions(self):
        report = self._report()
        self.assertEqual(
            [item["id"] for item in report["hypotheses"]],
            list(audit.HYPOTHESIS_ORDER),
        )
        self.assertTrue(
            all(
                item["disposition"] in {"confirmed", "ruled_out", "unresolved"}
                for item in report["hypotheses"]
            )
        )

    def test_hypothesis_order_mutation_is_rejected(self):
        def mutate(value):
            value["hypotheses"][0], value["hypotheses"][1] = (
                value["hypotheses"][1],
                value["hypotheses"][0],
            )

        result = self._audit_mutation(mutate)
        self.assertIn("hypothesis_order_invalid", result["errors"])

    def test_parser_replay_is_offline_once_and_fail_closed(self):
        replay = self._report()["parser_replay"]
        self.assertEqual(replay["replay_count"], 1)
        self.assertEqual(replay["model_calls"], 0)
        self.assertEqual(replay["writes"], 0)
        self.assertEqual(replay["retry_count"], 0)
        self.assertEqual(replay["failure_code"], "payload_invalid_json")
        self.assertEqual(replay["byte_offset"], 0)

    def test_parser_replay_count_mutation_is_rejected(self):
        result = self._audit_mutation(
            lambda value: value["parser_replay"].__setitem__("replay_count", 2)
        )
        self.assertIn("parser_replay_invalid", result["errors"])

    def test_historical_failure_callback_is_closed(self):
        result = audit.audit_report(
            audit.REPORT,
            historical_r5_check=lambda: False,
            historical_r5_1_check=lambda: True,
        )
        self.assertEqual(result["status"], "invalid")
        self.assertIn("historical_r5_changed", result["errors"])

    def test_gate2_result_root_must_remain_absent_or_logically_empty(self):
        result = audit.audit_report(audit.REPORT, gate2_root_safe_check=lambda: False)
        self.assertEqual(result["status"], "invalid")
        self.assertIn("r5_2_result_root_not_logically_empty", result["errors"])

    def test_fresh_execution_authorization_is_forbidden(self):
        result = self._audit_mutation(
            lambda value: value["gate_state"].__setitem__(
                "new_fresh_run_authorized", True
            )
        )
        self.assertIn("fresh_execution_authorization_invalid", result["errors"])

    def test_hash_fields_are_lowercase_sha256(self):
        report = self._report()
        for field in (
            "raw_output_sha256",
            "request_envelope_sha256",
            "model_visible_messages_sha256",
            "finalization_sha256",
        ):
            self.assertRegex(report[field], r"^[0-9a-f]{64}$")


if __name__ == "__main__":
    unittest.main()
