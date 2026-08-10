from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path
from types import ModuleType
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = (
    REPO_ROOT
    / "evals/m4/authorization/m4.2/gate-iv-b-protocol-proof.schema.json"
)
PROOF_PATH = (
    REPO_ROOT / "evals/m4/authorization/m4.2/gate-iv-b-protocol-proof.json"
)
AUDITOR_PATH = (
    REPO_ROOT
    / "evals/m4/authorization/audit_m4_2_gate_iv_b_protocol_proof.py"
)
R2_PATH = REPO_ROOT / "evals/m4/authorization/m4.2/gate-iv-a-review-r2.json"
BASELINE_HEAD = "988b4332504549df2038f51532175effd696a445"
BASELINE_TREE = "38b1aeacd54b5e5a9ac115be1816206a7a3f8a4f"
R2_BLOB = "734918bd5de16ea6f7595e206c3cd313ba041fa7"
R2_RAW_SHA256 = "73162089ad9a477598fe0ddcc975f666be60c15fb21e7471e32f472a4c30fded"
BRANCH = (
    "codex/m4-cross-engineering-forward-evaluation-"
    "m4.2-gate-iv-b-protocol-proof"
)
ROOT_KEYS = {
    "schema_version",
    "milestone",
    "revision",
    "proof_kind",
    "baseline",
    "source_artifacts",
    "matrix_proof",
    "request_binding_proof",
    "candidate_authorization_fixture",
    "claim_semantics",
    "pre_dispatch_proofs",
    "batch_failure_proofs",
    "visibility_proof",
    "negative_authority",
    "delivery",
    "findings",
    "reviewer_side_effects",
    "decision",
    "status",
}
PROVISIONAL_DECISION = "PENDING_M4_2_GATE_IV_B_EXACT_HEAD_CI"
PROVISIONAL_STATUS = (
    "M4_2_GATE_IV_B_LOCAL_PROTOCOL_PROOF_PASSED_PENDING_EXACT_HEAD_CI"
)
FINAL_DECISION = "APPROVE_M4_2_AUTHORIZATION_PREPARATION_ONLY"
FINAL_STATUS = "M4_2_GATE_IV_B_PROTOCOL_PROOF_PASSED_NOT_AUTHORIZED"
ZERO_MARKERS = {"FAIL:": 0, "FAILED (": 0, "Traceback": 0, "##[error]": 0}
IMPLEMENTED = all(path.is_file() for path in (SCHEMA_PATH, PROOF_PATH, AUDITOR_PATH))


def _load_auditor() -> ModuleType:
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec = importlib.util.spec_from_file_location(
            "audit_m4_2_gate_iv_b_protocol_proof_test", AUDITOR_PATH
        )
        if spec is None or spec.loader is None:
            raise AssertionError("auditor_import_spec_missing")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.dont_write_bytecode = previous


def _load_proof() -> dict[str, Any]:
    value = json.loads(PROOF_PATH.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError("proof_not_object")
    return value


def _ci_job(job_id: int, platform: str) -> dict[str, Any]:
    return {
        "job_id": job_id,
        "name": (
            "M4.2 Gate IV-B protocol proof (NOT AUTHORIZED) "
            f"({platform}-latest)"
        ),
        "conclusion": "success",
    }


def _delivery_run(event: str, head: str, run_id: int) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "event": event,
        "head": head,
        "branch": BRANCH,
        "conclusion": "success",
        "job_count": 2,
        "jobs": [
            _ci_job(run_id * 10 + 1, "windows"),
            _ci_job(run_id * 10 + 2, "ubuntu"),
        ],
        "raw_log": {
            "byte_length": 1,
            "sha256": "a" * 64,
            "markers": copy.deepcopy(ZERO_MARKERS),
        },
    }


def _runtime_result(runtime: str) -> dict[str, Any]:
    return {
        "runtime": runtime,
        "status": "VERIFIED",
        "checked_task_count": 60,
        "mismatches": [],
        "side_effects": [],
    }


def _final_proof() -> dict[str, Any]:
    proof = copy.deepcopy(_load_proof())
    head = "1" * 40
    proof["delivery"] = {
        "status": "VERIFIED_TRUE_GREEN",
        "accepted_proof_head": head,
        "push": _delivery_run("push", head, 1001),
        "pull_request": _delivery_run("pull_request", head, 1002),
        "powershell_5_1": _runtime_result("Windows PowerShell 5.1"),
        "powershell_7": _runtime_result("PowerShell 7 on Ubuntu"),
        "semantic_results_match": True,
    }
    proof["decision"] = FINAL_DECISION
    proof["status"] = FINAL_STATUS
    return proof


class M42GateIVBRedFirstTests(unittest.TestCase):
    def test_protocol_proof_files_exist(self) -> None:
        missing = [
            path.relative_to(REPO_ROOT).as_posix()
            for path in (SCHEMA_PATH, PROOF_PATH, AUDITOR_PATH)
            if not path.is_file()
        ]
        self.assertEqual(missing, [])


@unittest.skipUnless(IMPLEMENTED, "B1 red: Gate IV-B implementation absent")
class M42GateIVBContractTests(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.auditor = _load_auditor()
        cls.proof = _load_proof()

    def _audit(
        self,
        proof: dict[str, Any],
        *,
        verify_git: bool = False,
        present_paths: set[str] | None = None,
    ) -> dict[str, Any]:
        return self.auditor.audit_protocol_proof(
            REPO_ROOT,
            proof_data=proof,
            verify_git=verify_git,
            present_paths=present_paths,
        )

    def _assert_blocked(
        self,
        proof: dict[str, Any],
        error: str,
        *,
        present_paths: set[str] | None = None,
    ) -> None:
        result = self._audit(proof, present_paths=present_paths)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn(error, result["errors"])

    def test_schema_is_closed_at_every_object_definition(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertEqual(schema["type"], "object")
        self.assertIs(schema["additionalProperties"], False)
        self.assertEqual(set(schema["required"]), ROOT_KEYS)
        self.assertEqual(set(schema["properties"]), ROOT_KEYS)
        for name, definition in schema["$defs"].items():
            if definition.get("type") == "object":
                with self.subTest(definition=name):
                    self.assertIs(definition.get("additionalProperties"), False)
                    self.assertEqual(
                        set(definition["required"]),
                        set(definition["properties"]),
                    )

    def test_strict_loader_rejects_duplicate_keys_bom_and_nonfinite(self) -> None:
        duplicate_errors: list[str] = []
        self.assertEqual(
            self.auditor.load_json_bytes(
                b'{"x":1,"x":2}', "sample", duplicate_errors
            ),
            {},
        )
        self.assertIn("sample_duplicate_key", duplicate_errors)
        bom_errors: list[str] = []
        self.assertEqual(
            self.auditor.load_json_bytes(b"\xef\xbb\xbf{}", "sample", bom_errors),
            {},
        )
        self.assertIn("sample_bom_forbidden", bom_errors)
        nonfinite_errors: list[str] = []
        self.assertEqual(
            self.auditor.load_json_bytes(
                b'{"x":NaN}', "sample", nonfinite_errors
            ),
            {},
        )
        self.assertIn("sample_invalid_json", nonfinite_errors)

    def test_artifact_root_state_and_permissions_are_exact(self) -> None:
        proof = self.proof
        self.assertEqual(set(proof), ROOT_KEYS)
        self.assertEqual(
            proof["proof_kind"],
            "OFFLINE_PROTOCOL_PROOF_NOT_EXECUTION_AUTHORIZATION",
        )
        self.assertEqual(proof["findings"], [])
        self.assertEqual(proof["reviewer_side_effects"], [])
        fixture = proof["candidate_authorization_fixture"]
        self.assertIs(fixture["fresh_execution_authorized"], False)
        self.assertIs(fixture["result_writes_authorized"], False)
        self.assertEqual(fixture["authorization_token_status"], "NOT_ISSUED")
        self.assertIs(fixture["claim_authorized"], False)
        self.assertEqual(fixture["authorized_task_count"], 0)
        if proof["delivery"]["status"] == "PENDING_EXACT_HEAD_CI":
            self.assertEqual(proof["decision"], PROVISIONAL_DECISION)
            self.assertEqual(proof["status"], PROVISIONAL_STATUS)
        else:
            self.assertEqual(proof["decision"], FINAL_DECISION)
            self.assertEqual(proof["status"], FINAL_STATUS)

    def test_exact_repository_proof_passes_with_git_verification(self) -> None:
        result = self._audit(copy.deepcopy(self.proof), verify_git=True)
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["findings"], [])
        self.assertEqual(result["reviewer_side_effects"], [])
        self.assertEqual(result["planned_task_count"], 60)
        self.assertEqual(result["batch_count"], 6)
        self.assertEqual(result["request_binding_count"], 60)
        self.assertEqual(result["forbidden_path_count"], 0)
        self.assertEqual(result["authorized_tasks"], 0)
        self.assertEqual(result["created_contexts"], 0)
        self.assertEqual(result["dispatched_tasks"], 0)
        self.assertEqual(result["results_observed"], 0)

    def test_baseline_head_tree_r2_blob_and_decision_are_immutable(self) -> None:
        baseline = self.proof["baseline"]
        self.assertEqual(baseline["required_ancestor_head"], BASELINE_HEAD)
        self.assertEqual(baseline["required_ancestor_tree"], BASELINE_TREE)
        r2 = baseline["gate_iv_a_r2_artifact"]
        self.assertEqual(r2["git_blob_oid"], R2_BLOB)
        self.assertEqual(r2["raw_sha256"], R2_RAW_SHA256)
        self.assertEqual(
            baseline["gate_iv_a_r2_decision"],
            "APPROVE_M4_2_GATE_IV_B_PROTOCOL_PROOF_ONLY",
        )
        self.assertIs(baseline["fresh_execution_authorized"], False)

    def test_matrix_and_request_bindings_are_independently_recomputed(self) -> None:
        manifest = json.loads(
            (
                REPO_ROOT / "evals/m4/revisions/m4.2/preparation-manifest.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(
            self.auditor.matrix_projection(manifest), self.proof["matrix_proof"]
        )
        recomputed = [
            self.auditor.request_binding_sha256(task) for task in manifest["tasks"]
        ]
        self.assertEqual(len(recomputed), 60)
        self.assertEqual(len(set(recomputed)), 60)
        self.assertEqual(
            sum(
                value == task["request_binding_sha256"]
                for value, task in zip(recomputed, manifest["tasks"])
            ),
            60,
        )
        self.assertEqual(
            self.auditor.request_binding_projection(manifest),
            self.proof["request_binding_proof"],
        )

    def test_first_claim_consumes_whole_virtual_matrix_once_without_dispatch(self) -> None:
        outcome = self.auditor.simulate_claim(
            state="VIRTUAL_UNCONSUMED",
            preconditions={name: True for name in self.auditor.PRECONDITION_NAMES},
            requested_task_count=60,
        )
        self.assertEqual(outcome["decision"], "SIMULATED_CLAIM_ACCEPTED")
        self.assertEqual(outcome["virtual_state_after"], "VIRTUAL_CONSUMED")
        self.assertEqual(outcome["simulated_claim_count_delta"], 1)
        self.assertEqual(
            outcome["simulated_matrix_authority_consumed_count"], 60
        )
        self.assertEqual(outcome["simulated_dispatched_tasks"], 0)
        self.assertEqual(outcome["simulated_retry_count"], 0)
        self.assertEqual(outcome["simulated_repair_count"], 0)
        self.assertEqual(outcome["simulated_followup_count"], 0)

    def test_partial_or_second_claim_is_rejected(self) -> None:
        ready = {name: True for name in self.auditor.PRECONDITION_NAMES}
        partial = self.auditor.simulate_claim(
            state="VIRTUAL_UNCONSUMED",
            preconditions=ready,
            requested_task_count=59,
        )
        self.assertEqual(partial["decision"], "REJECTED_PARTIAL_AUTHORITY")
        self.assertEqual(partial["simulated_claim_count_delta"], 0)
        self.assertEqual(partial["simulated_dispatched_tasks"], 0)
        second = self.auditor.simulate_claim(
            state="VIRTUAL_CONSUMED",
            preconditions=ready,
            requested_task_count=60,
        )
        self.assertEqual(second["decision"], "REJECTED_ALREADY_CONSUMED")
        self.assertEqual(second["simulated_claim_count_delta"], 0)
        self.assertTrue(second["successor_revision_required"])

    def test_all_pre_dispatch_mismatches_reject_with_zero_tasks(self) -> None:
        expected = {
            "model_binding_matches",
            "project_matches",
            "worktree_matches",
            "request_bindings_match",
            "head_is_fresh",
            "prerequisites_present",
        }
        self.assertEqual(set(self.auditor.PRECONDITION_NAMES), expected)
        for failed in self.auditor.PRECONDITION_NAMES:
            with self.subTest(failed=failed):
                values = {name: True for name in self.auditor.PRECONDITION_NAMES}
                values[failed] = False
                outcome = self.auditor.simulate_claim(
                    state="VIRTUAL_UNCONSUMED",
                    preconditions=values,
                    requested_task_count=60,
                )
                self.assertEqual(outcome["decision"], "REJECTED_PRE_DISPATCH")
                self.assertEqual(outcome["simulated_claim_count_delta"], 0)
                self.assertEqual(outcome["simulated_dispatched_tasks"], 0)
                self.assertEqual(
                    outcome["virtual_state_after"], "VIRTUAL_UNCONSUMED"
                )

    def test_failed_claim_stops_zero_dispatch_and_requires_successor(self) -> None:
        outcome = self.auditor.simulate_claim(
            state="VIRTUAL_UNCONSUMED",
            preconditions={name: True for name in self.auditor.PRECONDITION_NAMES},
            requested_task_count=60,
            post_claim_failure=True,
        )
        self.assertEqual(
            outcome["decision"], "STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE"
        )
        self.assertEqual(outcome["virtual_state_after"], "VIRTUAL_TERMINAL_FAILED")
        self.assertEqual(outcome["simulated_claim_count_delta"], 1)
        self.assertEqual(outcome["simulated_dispatched_tasks"], 0)
        self.assertTrue(outcome["successor_revision_required"])

    def test_every_batch_failure_stops_all_later_batches_without_retry(self) -> None:
        for sequence in range(1, 7):
            with self.subTest(sequence=sequence):
                trace = self.auditor.simulate_batch_failure(sequence)
                self.assertEqual(
                    trace["decision"],
                    "STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE",
                )
                self.assertEqual(trace["failed_batch_sequence"], sequence)
                self.assertEqual(len(trace["completed_prior_batches"]), sequence - 1)
                self.assertEqual(len(trace["later_batches_not_started"]), 6 - sequence)
                self.assertEqual(trace["simulated_retry_count"], 0)
                self.assertEqual(trace["simulated_repair_count"], 0)
                self.assertEqual(trace["simulated_followup_count"], 0)
                self.assertTrue(trace["successor_revision_required"])

    def test_visibility_projection_excludes_results_map_judge_and_aggregate(self) -> None:
        visibility = self.auditor.visibility_projection()
        self.assertEqual(visibility, self.proof["visibility_proof"])
        self.assertEqual(
            visibility["task_context_allowed_inputs"],
            ["case", "task_protocol", "selected_variant_instruction"],
        )
        self.assertEqual(visibility["visible_result_task_ids"], [])
        for key in (
            "cross_task_results_visible",
            "blind_mapping_available_to_task",
            "judge_available",
            "unblinding_available",
            "aggregation_available",
        ):
            self.assertIs(visibility[key], False)

    def test_negative_authority_counters_and_paths_are_zero(self) -> None:
        negative = self.proof["negative_authority"]
        for key in (
            "authorized_tasks",
            "created_contexts",
            "dispatched_tasks",
            "finalizations",
            "results_observed",
            "judge_scores",
            "retries",
            "repairs",
            "unauthorized_side_effects",
            "raw_model_finals",
            "aggregation_calls",
            "acceptance_claims",
        ):
            self.assertEqual(negative[key], 0)
        self.assertEqual(negative["forbidden_paths"], [])
        self.assertEqual(negative["forbidden_states"], [])
        self.assertEqual(negative["authorization_artifact"], "ABSENT")
        self.assertEqual(negative["launch_claim"], "ABSENT")
        self.assertEqual(negative["result_root"], "ABSENT")

    def test_final_delivery_state_is_semantically_valid_without_git(self) -> None:
        result = self._audit(_final_proof())
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["decision"], FINAL_DECISION)
        self.assertEqual(result["status"], FINAL_STATUS)

    def test_auditor_source_is_offline_read_only_and_has_no_thread_surface(self) -> None:
        source = AUDITOR_PATH.read_text(encoding="utf-8")
        for forbidden in (
            "import urllib",
            "from urllib",
            "import requests",
            "from requests",
            "import socket",
            "http.client",
            ".write_text(",
            ".write_bytes(",
            "create_thread",
            "send_message_to_thread",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)

    def test_cli_is_read_only_and_byte_repeatable(self) -> None:
        before = subprocess.run(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
        ).stdout
        first = subprocess.run(
            [sys.executable, "-X", "utf8", str(AUDITOR_PATH)],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
        )
        second = subprocess.run(
            [sys.executable, "-X", "utf8", str(AUDITOR_PATH)],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
        )
        after = subprocess.run(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
        ).stdout
        self.assertEqual(first.returncode, 0, first.stderr.decode("utf-8", "replace"))
        self.assertEqual(second.returncode, 0, second.stderr.decode("utf-8", "replace"))
        self.assertEqual(first.stdout, second.stdout)
        self.assertEqual(before, after)
        payload = json.loads(first.stdout)
        self.assertEqual(payload["errors"], [])
        self.assertEqual(payload["authorized_tasks"], 0)
        self.assertEqual(payload["dispatched_tasks"], 0)


@unittest.skipUnless(IMPLEMENTED, "B1 red: Gate IV-B implementation absent")
class M42GateIVBMutationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.auditor = _load_auditor()
        cls.proof = _load_proof()

    def _assert_blocked(
        self,
        proof: dict[str, Any],
        error: str,
        *,
        present_paths: set[str] | None = None,
    ) -> None:
        result = self.auditor.audit_protocol_proof(
            REPO_ROOT,
            proof_data=proof,
            verify_git=False,
            present_paths=present_paths,
        )
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn(error, result["errors"])

    def test_rejects_unknown_root_key(self) -> None:
        proof = copy.deepcopy(self.proof)
        proof["unexpected"] = False
        self._assert_blocked(proof, "proof_root_keys_mismatch")

    def test_rejects_baseline_or_r2_binding_drift(self) -> None:
        proof = copy.deepcopy(self.proof)
        proof["baseline"]["required_ancestor_head"] = "0" * 40
        self._assert_blocked(proof, "baseline_binding_mismatch")
        proof = copy.deepcopy(self.proof)
        proof["baseline"]["gate_iv_a_r2_artifact"]["raw_sha256"] = "0" * 64
        self._assert_blocked(proof, "baseline_binding_mismatch")

    def test_rejects_source_matrix_or_request_binding_drift(self) -> None:
        proof = copy.deepcopy(self.proof)
        proof["source_artifacts"][0]["raw_sha256"] = "0" * 64
        self._assert_blocked(proof, "source_artifact_bindings_mismatch")
        proof = copy.deepcopy(self.proof)
        proof["matrix_proof"]["planned_task_count"] = 59
        self._assert_blocked(proof, "matrix_proof_mismatch")
        proof = copy.deepcopy(self.proof)
        proof["request_binding_proof"]["matched"] = 59
        self._assert_blocked(proof, "request_binding_proof_mismatch")

    def test_rejects_candidate_fixture_that_looks_authorized(self) -> None:
        proof = copy.deepcopy(self.proof)
        proof["candidate_authorization_fixture"]["claim_authorized"] = True
        self._assert_blocked(proof, "candidate_authorization_fixture_mismatch")
        proof = copy.deepcopy(self.proof)
        proof["candidate_authorization_fixture"][
            "authorization_token_status"
        ] = "UNCONSUMED"
        self._assert_blocked(proof, "candidate_authorization_fixture_mismatch")

    def test_rejects_claim_predispatch_batch_or_visibility_proof_drift(self) -> None:
        proof = copy.deepcopy(self.proof)
        proof["claim_semantics"]["scenarios"][0]["output"][
            "simulated_dispatched_tasks"
        ] = 1
        self._assert_blocked(proof, "claim_semantics_mismatch")
        proof = copy.deepcopy(self.proof)
        proof["pre_dispatch_proofs"][0]["output"]["simulated_dispatched_tasks"] = 1
        self._assert_blocked(proof, "pre_dispatch_proofs_mismatch")
        proof = copy.deepcopy(self.proof)
        proof["batch_failure_proofs"][0]["output"]["simulated_retry_count"] = 1
        self._assert_blocked(proof, "batch_failure_proofs_mismatch")
        proof = copy.deepcopy(self.proof)
        proof["visibility_proof"]["judge_available"] = True
        self._assert_blocked(proof, "visibility_proof_mismatch")

    def test_rejects_nonzero_actual_counter_or_forbidden_path(self) -> None:
        proof = copy.deepcopy(self.proof)
        proof["negative_authority"]["results_observed"] = 1
        self._assert_blocked(proof, "negative_authority_mismatch")
        self._assert_blocked(
            copy.deepcopy(self.proof),
            "forbidden_future_path_present",
            present_paths={
                "evals/m4/authorization/m4.2/execution-authorization.json"
            },
        )

    def test_rejects_execution_authorization_decision(self) -> None:
        proof = copy.deepcopy(self.proof)
        proof["decision"] = "AUTHORIZE_M4_2_EXECUTION"
        self._assert_blocked(proof, "decision_attempts_execution_authorization")

    def test_rejects_final_delivery_failure_marker_or_runtime_mismatch(self) -> None:
        proof = _final_proof()
        proof["delivery"]["push"]["raw_log"]["markers"]["Traceback"] = 1
        self._assert_blocked(proof, "delivery_push_mismatch")
        proof = _final_proof()
        proof["delivery"]["powershell_7"]["checked_task_count"] = 59
        self._assert_blocked(proof, "delivery_powershell_7_mismatch")
        proof = _final_proof()
        proof["delivery"]["semantic_results_match"] = False
        self._assert_blocked(proof, "delivery_semantics_mismatch")

    def test_rejects_findings_or_reviewer_side_effects(self) -> None:
        proof = copy.deepcopy(self.proof)
        proof["findings"] = ["finding"]
        self._assert_blocked(proof, "proof_findings_present")
        proof = copy.deepcopy(self.proof)
        proof["reviewer_side_effects"] = ["side_effect"]
        self._assert_blocked(proof, "reviewer_side_effects_present")


if __name__ == "__main__":
    unittest.main()
