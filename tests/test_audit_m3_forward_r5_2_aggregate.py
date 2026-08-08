from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "evals" / "m3"))

import m3_cross_revision_contract as contract  # noqa: E402
import audit_forward_r5_2_aggregate as audit  # noqa: E402


class M3CrossRevisionContractTests(unittest.TestCase):
    def test_contract_rejects_duplicate_keys_bom_nonfinite_and_nonobject(self):
        for raw in (
            b'{"a":1,"a":2}',
            b"\xef\xbb\xbf{}",
            b'{"a":NaN}',
            b"[]",
        ):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                contract.parse_strict_object(raw)

    def test_canonical_hash_is_key_order_independent(self):
        self.assertEqual(
            contract.canonical_sha256({"b": 2, "a": 1}),
            contract.canonical_sha256({"a": 1, "b": 2}),
        )

    def test_historical_raw_identity_comes_from_fixed_git_blob(self):
        artifact = contract.git_artifact(
            REPO_ROOT,
            contract.R5_HEAD,
            "evals/m3/results/forward-r5/acceptance-manifest-consumed.json",
        )
        self.assertEqual(artifact["byte_length"], 12099)
        self.assertEqual(
            artifact["raw_sha256"],
            "dc36f9f86517adfbe1997a2ea0119b040b9ee5c1565016f3086f287e9a4fc410",
        )

    def test_artifact_ref_rejects_stale_identity_and_traversal(self):
        artifact = contract.git_artifact(
            REPO_ROOT,
            contract.R5_HEAD,
            "evals/m3/results/forward-r5/m3-f01.context.json",
        )
        artifact["raw_sha256"] = "0" * 64
        errors = contract.validate_artifact_ref(
            artifact,
            repo_root=REPO_ROOT,
            expected_head=contract.R5_HEAD,
            allowed_prefixes=("evals/m3/results/forward-r5",),
            json_required=True,
        )
        self.assertIn("artifact_ref_raw_sha256_mismatch", errors)

        artifact["path"] = "../outside.json"
        errors = contract.validate_artifact_ref(
            artifact,
            repo_root=REPO_ROOT,
            expected_head=contract.R5_HEAD,
            allowed_prefixes=("evals/m3/results/forward-r5",),
            json_required=True,
        )
        self.assertIn("artifact_ref_path_invalid", errors)


class AuditM3ForwardR52AggregateTests(unittest.TestCase):
    def _manifest(self) -> dict:
        return json.loads(audit.AGGREGATE_MANIFEST.read_text(encoding="utf-8"))

    def _mutate(self, mutate) -> dict:
        value = copy.deepcopy(self._manifest())
        mutate(value)
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            path = Path(temp_dir) / "aggregate-manifest.json"
            path.write_text(
                json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                + "\n",
                encoding="utf-8",
                newline="\n",
            )
            return audit.audit_aggregate(path)

    def _selected(self, value: dict, case_id: str) -> dict:
        return next(item for item in value["selected_cases"] if item["case_id"] == case_id)

    def test_actual_aggregate_selects_exact_revisions_and_closed_counters(self):
        result = audit.audit_aggregate(audit.AGGREGATE_MANIFEST)

        self.assertEqual(
            set(result),
            {
                "status",
                "selected_cases",
                "selected_counters",
                "historical_counters",
                "excluded_attempts",
                "historical_diffs",
                "errors",
                "evidence_gaps",
                "side_effects",
                "m3_status",
                "m4_status",
            },
        )
        self.assertEqual(result["status"], "accepted")
        self.assertEqual(result["errors"], [])
        self.assertEqual(
            {item["case_id"]: item["revision"] for item in result["selected_cases"]},
            contract.SELECTED_REVISIONS,
        )
        self.assertEqual(result["selected_counters"], contract.SELECTED_COUNTERS)
        self.assertEqual(result["historical_counters"], contract.HISTORICAL_COUNTERS)
        self.assertEqual(
            [item["attempt_id"] for item in result["excluded_attempts"]],
            ["r5:m3-f02", "r5.1-f02:m3-f02"],
        )
        self.assertTrue(all(item["status"] == "empty" for item in result["historical_diffs"]))
        self.assertEqual(result["m3_status"], "IN_PROGRESS")
        self.assertEqual(result["m4_status"], "NOT_STARTED")

    def test_f03_is_the_expected_fail_closed_case_without_bundle_composition(self):
        result = audit.audit_aggregate(audit.AGGREGATE_MANIFEST)
        f03 = next(item for item in result["selected_cases"] if item["case_id"] == "m3-f03")

        self.assertEqual(result["status"], "accepted")
        self.assertEqual(f03["terminal_status"], "processed_accepted")
        self.assertEqual(f03["composer"], 0)
        self.assertEqual(f03["validator"], 1)

    def test_failed_f02_attempt_cannot_be_deleted(self):
        result = self._mutate(lambda value: value["excluded_attempts"].pop())
        self.assertIn("excluded_attempt_set_invalid", result["errors"])

    def test_selected_case_set_and_revision_are_closed(self):
        result = self._mutate(lambda value: value["selected_cases"].pop())
        self.assertIn("selected_case_set_invalid", result["errors"])

        def select_historical_r5_f02(value: dict) -> None:
            value["selected_cases"][1] = copy.deepcopy(value["excluded_attempts"][0])

        result = self._mutate(select_historical_r5_f02)
        self.assertIn("selected_case_set_invalid", result["errors"])
        self.assertIn("selected_revision_mapping_invalid", result["errors"])

    def test_task_finalization_state_and_retry_are_hash_bound(self):
        for field, changed in (
            ("task_id", "wrong-task"),
            ("finalization_id", "wrong-finalization"),
            ("terminal_status", "processing_failed"),
            ("retry", 1),
        ):
            with self.subTest(field=field):
                result = self._mutate(
                    lambda value, field=field, changed=changed: self._selected(
                        value, "m3-f02"
                    ).__setitem__(field, changed)
                )
                self.assertTrue(
                    any(error.startswith("attempt_identity_invalid:r5.2-f02:m3-f02") for error in result["errors"])
                )

    def test_wrong_json_types_fail_closed_without_exception(self):
        for field, changed in (
            ("task_id", ["not", "a", "string"]),
            ("finalization_id", {"not": "a string"}),
            ("composer", [1]),
            ("validator", "1"),
            ("retry", {"count": 1}),
        ):
            with self.subTest(field=field):
                result = self._mutate(
                    lambda value, field=field, changed=changed: self._selected(
                        value, "m3-f02"
                    ).__setitem__(field, changed)
                )
                self.assertEqual(result["status"], "invalid")
                self.assertTrue(result["errors"])

        supersession = contract.load_strict_object(audit.SUPERSESSION_MANIFEST)
        supersession["attempts"][0]["task_id"] = ["wrong-type"]
        supersession["attempts"][1]["composer"] = {"wrong": "type"}
        errors: list[str] = []
        audit._validate_supersession(supersession, repo_root=REPO_ROOT, errors=errors)
        self.assertIn("task_id_invalid", errors)
        self.assertIn("historical_counter_derivation_mismatch", errors)

    def test_artifact_ref_rejects_hash_head_and_path_tampering(self):
        for field, changed, expected_fragment in (
            ("raw_sha256", "0" * 64, "artifact_ref_raw_sha256_mismatch"),
            ("source_head", contract.R5_HEAD, "artifact_ref_source_head_mismatch"),
            ("path", "../terminal-manifest.json", "artifact_ref_path_invalid"),
            ("path", "C:/terminal-manifest.json", "artifact_ref_path_invalid"),
        ):
            with self.subTest(field=field, changed=changed):
                result = self._mutate(
                    lambda value, field=field, changed=changed: self._selected(
                        value, "m3-f02"
                    )["evidence"].__setitem__(field, changed)
                )
                self.assertTrue(any(expected_fragment in error for error in result["errors"]))

    def test_f03_cannot_gain_composer_or_change_terminal_status(self):
        result = self._mutate(
            lambda value: self._selected(value, "m3-f03").__setitem__("composer", 1)
        )
        self.assertIn("f03_composer_must_be_zero", result["errors"])

        result = self._mutate(
            lambda value: self._selected(value, "m3-f03").__setitem__(
                "terminal_status", "processed_invalid"
            )
        )
        self.assertIn("f03_expected_block_counters_invalid", result["errors"])

    def test_selected_and_historical_counter_domains_cannot_be_mixed(self):
        result = self._mutate(
            lambda value: value["selected_counters"].__setitem__("tasks", 6)
        )
        self.assertIn("selected_counters_invalid", result["errors"])

        result = self._mutate(
            lambda value: value["historical_counters"].__setitem__("failed", 1)
        )
        self.assertIn("historical_counters_invalid", result["errors"])

    def test_failed_attempt_cannot_be_relabeled_or_duplicated(self):
        result = self._mutate(
            lambda value: value["excluded_attempts"][0].__setitem__("accepted", True)
        )
        self.assertTrue(
            any(error.startswith("attempt_identity_invalid:r5:m3-f02:accepted") for error in result["errors"])
        )

        def duplicate(value: dict) -> None:
            value["excluded_attempts"][1]["attempt_id"] = value["excluded_attempts"][0][
                "attempt_id"
            ]

        result = self._mutate(duplicate)
        self.assertIn("attempt_id_duplicate", result["errors"])
        self.assertIn("excluded_attempt_set_invalid", result["errors"])

    def test_supersession_binding_gate_scope_and_allowlist_are_closed(self):
        result = self._mutate(
            lambda value: value["supersession_manifest"].__setitem__("raw_sha256", "0" * 64)
        )
        self.assertIn("supersession_raw_sha256_mismatch", result["errors"])

        result = self._mutate(
            lambda value: value["scope_limits"].__setitem__("retry_authorized", True)
        )
        self.assertIn("scope_limits_invalid", result["errors"])

        result = self._mutate(lambda value: value["gate_state"].__setitem__("m4", "IN_PROGRESS"))
        self.assertIn("gate_state_invalid", result["errors"])

        result = self._mutate(lambda value: value["result_root_allowlist"].pop())
        self.assertIn("result_root_allowlist_invalid", result["errors"])

        result = self._mutate(lambda value: value["does_not_prove"].clear())
        self.assertIn("claim_limits_invalid", result["errors"])

    def test_extra_manifest_field_is_rejected(self):
        result = self._mutate(lambda value: value.__setitem__("extra", True))
        self.assertIn("aggregate_keys_invalid", result["errors"])


if __name__ == "__main__":
    unittest.main()
