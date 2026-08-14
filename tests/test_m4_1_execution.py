from __future__ import annotations

import copy
import hashlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
EXECUTION_ROOT = REPO_ROOT / "evals" / "m4" / "execution"
sys.path.insert(0, str(EXECUTION_ROOT))

import audit_m4_1 as audit  # noqa: E402


def _write_json(path: Path, value: dict[str, object]) -> bytes:
    raw = audit.canonical_bytes(value) + b"\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return raw


class M41ExecutionProtocolTests(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.control = audit.parse_json_object(audit.CONTROL_PATH.read_bytes())
        cls.authorization = audit.parse_json_object(
            audit.AUTHORIZATION_PATH.read_bytes()
        )
        cls.preparation = audit.parse_json_object(audit.PREPARATION_PATH.read_bytes())
        cls.tasks = audit.ordered_tasks(cls.control)
        cls.tasks_by_id = {str(task["task_id"]): task for task in cls.tasks}

    def _guarded_snapshot(self) -> dict[str, bytes | None]:
        paths = (
            audit.AUTHORIZATION_PATH,
            audit.CONTROL_PATH,
            audit.PREPARATION_PATH,
            audit.HELPER_PATH,
            REPO_ROOT / audit.CLAIM_RELATIVE,
            REPO_ROOT / audit.TERMINAL_RELATIVE,
            REPO_ROOT / audit.RESULTS_MANIFEST_RELATIVE,
        )
        snapshot: dict[str, bytes | None] = {}
        for path in paths:
            snapshot[path.relative_to(REPO_ROOT).as_posix()] = (
                path.read_bytes() if path.is_file() else None
            )
        results = REPO_ROOT / audit.RESULTS_BASE_RELATIVE
        snapshot[audit.RESULTS_BASE_RELATIVE.as_posix()] = (
            b"present" if results.exists() else None
        )
        return snapshot

    def _claim(self) -> dict[str, object]:
        batches = []
        task_claims = []
        task_ids = []
        task_index = 0
        task_by_id = {
            str(task["task_id"]): task for task in self.control["tasks"]
        }
        for batch_index, batch_id in enumerate(audit.BATCH_ORDER, start=1):
            source_batch = next(
                item
                for item in self.control["batches"]
                if item["batch_id"] == batch_id
            )
            batch_task_ids = list(source_batch["task_ids"])
            batches.append(
                {
                    "batch_id": batch_id,
                    "sequence": batch_index,
                    "task_ids": batch_task_ids,
                    "planned_task_count": 10,
                }
            )
            for task_id in batch_task_ids:
                task_index += 1
                task = task_by_id[task_id]
                task_ids.append(task_id)
                task_claims.append(
                    {
                        "task_id": task_id,
                        "batch_id": batch_id,
                        "request_binding_sha256": task["request_binding_sha256"],
                        "result_root": task["result_root"],
                        "context_id": f"m4.1-context-{task_index:03d}",
                        "finalization_id": f"m4.1-finalization-{task_index:03d}",
                    }
                )
        return {
            "schema_version": "m4.1-launch-claim-v1",
            "milestone": "M4",
            "revision": "M4.1",
            "status": "CLAIMED",
            "claim_id": "m4.1-synthetic-claim",
            "claimed_at_utc": "2026-08-08T12:00:00Z",
            "claim_count": 1,
            "creation_semantics": {
                "mechanism": "python_os_open_O_CREAT_O_EXCL",
                "target_path": audit.CLAIM_RELATIVE.as_posix(),
                "target_preexisted": False,
                "overwrite_allowed": False,
            },
            "authorization": {
                "head": audit.AUTHORIZATION_HEAD,
                "branch": audit.AUTHORIZATION_BRANCH,
                "ci_run_id": audit.AUTHORIZATION_CI_RUN_ID,
                "ci_conclusion": "success",
                "token": audit.AUTHORIZATION_TOKEN,
                "token_status_before_claim": "UNCONSUMED",
                "token_status_after_claim": "CONSUMED",
                "claim_consumes_entire_authorization": True,
            },
            "execution_protocol": {
                "head": "1" * 40,
                "branch": audit.EXECUTION_BRANCH,
                "ci_run_id": 99999999999,
                "ci_conclusion": "success",
            },
            "project": {
                "project_id": audit.PROJECT_ID,
                "is_git_repository": True,
                "environment": "worktree",
                "starting_branch": audit.AUTHORIZATION_BRANCH,
                "starting_head": audit.AUTHORIZATION_HEAD,
            },
            "configured_defaults": {
                "exact_model_id": audit.MODEL_ID,
                "reasoning_effort": audit.REASONING_EFFORT,
                "configured_default_check": "MATCHED",
                "create_thread_model_field": "OMITTED",
                "create_thread_thinking_field": "OMITTED",
            },
            "frozen_bindings": {
                "authorization": {
                    "path": audit.AUTHORIZATION_RELATIVE.as_posix(),
                    "raw_sha256": audit.sha256(audit.AUTHORIZATION_PATH.read_bytes()),
                },
                "execution_control": {
                    "path": audit.CONTROL_RELATIVE.as_posix(),
                    "raw_sha256": audit.sha256(audit.CONTROL_PATH.read_bytes()),
                },
                "preparation_manifest": {
                    "path": audit.PREPARATION_RELATIVE.as_posix(),
                    "raw_sha256": audit.sha256(audit.PREPARATION_PATH.read_bytes()),
                },
                "execution_helper": {
                    "path": audit.HELPER_RELATIVE.as_posix(),
                    "raw_sha256": audit.sha256(audit.HELPER_PATH.read_bytes()),
                },
            },
            "request_binding_aggregate": {
                "algorithm": "sha256-canonical-json-task-request-bindings-v1",
                "ordered_pair_count": 60,
                "sha256": audit.request_binding_aggregate(self.tasks),
            },
            "batch_order": list(audit.BATCH_ORDER),
            "batches": batches,
            "task_ids": task_ids,
            "task_claims": task_claims,
            "limits": dict(audit.CLAIM_LIMITS),
            "does_not_authorize": list(audit.DOES_NOT_AUTHORIZE),
        }

    def _receipt(
        self,
        claim: dict[str, object],
        claim_raw: bytes,
        index: int,
        *,
        thread_id: str | None = None,
    ) -> dict[str, object]:
        task_claim = claim["task_claims"][index]
        task_id = str(task_claim["task_id"])
        task = self.tasks_by_id[task_id]
        prompt = audit.build_initial_prompt(task, task_claim)
        request = audit.expected_create_thread_arguments(task, task_claim)
        return {
            "schema_version": "m4.1-dispatch-receipt-v1",
            "milestone": "M4",
            "revision": "M4.1",
            "status": "DISPATCHED",
            "claim": {
                "claim_id": claim["claim_id"],
                "path": audit.CLAIM_RELATIVE.as_posix(),
                "raw_sha256": audit.sha256(claim_raw),
            },
            "task_id": task_id,
            "batch_id": task_claim["batch_id"],
            "batch_sequence": index // 10 + 1,
            "task_sequence_in_batch": index % 10 + 1,
            "dispatch_sequence": index + 1,
            "request_binding_sha256": task_claim["request_binding_sha256"],
            "context_id": task_claim["context_id"],
            "finalization_id": task_claim["finalization_id"],
            "request": {
                "surface": "codex_app.create_thread",
                "project_id": audit.PROJECT_ID,
                "target_type": "project",
                "environment_type": "worktree",
                "starting_branch": audit.AUTHORIZATION_BRANCH,
                "starting_head": audit.AUTHORIZATION_HEAD,
                "initial_request_sha256": audit.sha256(prompt.encode("utf-8")),
                "request_envelope_sha256": audit.canonical_sha256(request),
                "model_field": "OMITTED",
                "thinking_field": "OMITTED",
                "initial_request_count": 1,
                "followup_count": 0,
            },
            "response": {
                "thread_id": thread_id or f"thread-{index + 1:03d}",
                "host_id": "local",
                "client_thread_id": None,
                "ready": True,
            },
            "created_at_utc": f"2026-08-08T12:{index // 60:02d}:{index % 60:02d}Z",
            "attempt_index": 1,
            "retry_count": 0,
            "repair_count": 0,
            "errors": [],
        }

    def _task_result(
        self,
        claim: dict[str, object],
        index: int,
        *,
        response: str = "synthetic protocol-valid result",
    ) -> dict[str, object]:
        task_claim = claim["task_claims"][index]
        task = self.tasks_by_id[str(task_claim["task_id"])]
        return {
            "schema_version": "m4-task-result-v1",
            "task_id": task_claim["task_id"],
            "blind_id": task["blind_id"],
            "context_id": task_claim["context_id"],
            "finalization_id": task_claim["finalization_id"],
            "attempt_index": 1,
            "retry_count": 0,
            "independent_finalization": True,
            "visible_result_task_ids": [],
            "response": response,
            "citations": [],
            "machine_metrics": {
                "schema_valid": True,
                "fabricated_citation_count": 0,
                "unverified_recommendation_count": 0,
                "direction_gate_violation_count": 0,
                "route_binding_violation_count": 0,
                "resource_ceiling_violation_count": 0,
                "stop_pivot_authority_violation_count": 0,
                "unauthorized_side_effect_count": 0,
            },
            "detected_mismatch_ids": [],
            "side_effects": [],
            "terminal_state": "finalized",
        }

    def _terminal(
        self,
        claim: dict[str, object],
        claim_raw: bytes,
        receipt_refs: list[dict[str, object]],
        raw_refs: list[dict[str, object]],
        *,
        state: str = "COMPLETE_UNJUDGED",
    ) -> dict[str, object]:
        complete = state == "COMPLETE_UNJUDGED"
        count = len(receipt_refs)
        return {
            "schema_version": "m4.1-execution-terminal-v1",
            "milestone": "M4",
            "revision": "M4.1",
            "terminal_state": state,
            "recorded_at_utc": "2026-08-08T13:30:00Z",
            "launch_claim": {
                "claim_id": claim["claim_id"],
                "path": audit.CLAIM_RELATIVE.as_posix(),
                "raw_sha256": audit.sha256(claim_raw),
            },
            "execution_protocol": {
                "head": claim["execution_protocol"]["head"],
                "ci_run_id": claim["execution_protocol"]["ci_run_id"],
            },
            "batch_order": list(audit.BATCH_ORDER),
            "last_completed_batch": audit.BATCH_ORDER[-1] if complete else None,
            "failed_batch": None if complete else audit.BATCH_ORDER[0],
            "failed_task_id": None if complete else claim["task_ids"][0],
            "failed_stage": None if complete else "raw_final_schema_validation",
            "attempted_task_ids": list(claim["task_ids"][:count]),
            "dispatch_receipts": receipt_refs,
            "raw_finals": raw_refs,
            "counts": {
                "tasks": count,
                "threads": count,
                "finalizations": len(raw_refs),
                "attempts": count,
                "retries": 0,
                "repairs": 0,
                "followups": 0,
                "results": len(raw_refs),
                "judge_calls": 0,
                "aggregation_calls": 0,
                "side_effects": 0,
            },
            "failure_evidence": (
                None
                if complete
                else {
                    "failure_class": "PROTOCOL_FAILURE",
                    "raw_evidence": "raw final is not one strict JSON object",
                    "raw_evidence_sha256": audit.sha256(
                        b"raw final is not one strict JSON object"
                    ),
                }
            ),
            "later_batches_not_started": (
                [] if complete else list(audit.BATCH_ORDER[1:])
            ),
            "successor_revision_required": not complete,
            "coordinator_observation_policy": dict(audit.OBSERVATION_POLICY),
            "permissions_still_closed": list(audit.PERMISSIONS_STILL_CLOSED),
            "later_gates": dict(audit.LATER_GATES),
        }

    def _write_complete_fixture(
        self,
        root: Path,
        *,
        poor_quality_first: bool = False,
    ) -> tuple[Path, Path, Path, dict[str, object]]:
        claim = self._claim()
        claim_path = root / "claim.json"
        claim_raw = _write_json(claim_path, claim)
        results_base = root / "results" / "m4.1"
        receipt_refs = []
        raw_refs = []
        for index, task_id in enumerate(claim["task_ids"]):
            task_root = results_base / task_id
            receipt = self._receipt(claim, claim_raw, index)
            receipt_raw = _write_json(task_root / "dispatch-receipt.json", receipt)
            task_result = self._task_result(
                claim,
                index,
                response=(
                    "poor research quality but protocol-valid"
                    if poor_quality_first and index == 0
                    else "synthetic protocol-valid result"
                ),
            )
            final_raw = audit.canonical_bytes(task_result) + b"\n"
            (task_root / "raw-final.txt").write_bytes(final_raw)
            receipt_refs.append(
                {
                    "task_id": task_id,
                    "thread_id": receipt["response"]["thread_id"],
                    "path": f"evals/m4/results/m4.1/{task_id}/dispatch-receipt.json",
                    "raw_sha256": audit.sha256(receipt_raw),
                }
            )
            raw_refs.append(
                {
                    "task_id": task_id,
                    "finalization_id": claim["task_claims"][index][
                        "finalization_id"
                    ],
                    "path": f"evals/m4/results/m4.1/{task_id}/raw-final.txt",
                    "byte_length": len(final_raw),
                    "raw_sha256": audit.sha256(final_raw),
                    "protocol_validation": "VALID",
                    "observed_at_utc": "2026-08-08T13:00:00Z",
                }
            )
        terminal = self._terminal(
            claim, claim_raw, receipt_refs, raw_refs, state="COMPLETE_UNJUDGED"
        )
        terminal_path = root / "terminal.json"
        _write_json(terminal_path, terminal)
        return claim_path, results_base, terminal_path, terminal

    def test_schema_contracts_are_closed_and_terminal_states_are_exact(self) -> None:
        contracts = (
            (audit.LAUNCH_SCHEMA_PATH, audit.CLAIM_KEYS),
            (audit.DISPATCH_SCHEMA_PATH, audit.RECEIPT_KEYS),
            (audit.TERMINAL_SCHEMA_PATH, audit.TERMINAL_KEYS),
        )
        for path, expected_keys in contracts:
            with self.subTest(path=path.name):
                schema = audit.parse_json_object(path.read_bytes())
                self.assertEqual(schema["type"], "object")
                self.assertFalse(schema["additionalProperties"])
                self.assertEqual(set(schema["required"]), expected_keys)
                self.assertEqual(set(schema["properties"]), expected_keys)
                self.assertFalse(schema["x-real-instance-allowed-in-gate-iv-a"])
        terminal = audit.parse_json_object(audit.TERMINAL_SCHEMA_PATH.read_bytes())
        self.assertEqual(
            set(terminal["properties"]["terminal_state"]["enum"]),
            {
                "COMPLETE_UNJUDGED",
                "STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE",
            },
        )

    def test_repository_is_ready_unclaimed_and_read_only(self) -> None:
        before = self._guarded_snapshot()
        result = audit.audit_execution(REPO_ROOT)
        self.assertEqual(result["status"], "READY_UNCLAIMED")
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["token"], "UNCONSUMED")
        self.assertEqual(result["tasks"], 0)
        self.assertEqual(result["threads"], 0)
        self.assertEqual(result["finalizations"], 0)
        self.assertEqual(result["attempts"], 0)
        self.assertEqual(result["retries"], 0)
        self.assertEqual(result["repairs"], 0)
        self.assertEqual(result["followups"], 0)
        self.assertEqual(result["results"], 0)
        self.assertEqual(result["judge_calls"], 0)
        self.assertEqual(result["aggregation_calls"], 0)
        self.assertEqual(result["side_effects"], 0)
        self.assertEqual(result["authorization_audit_status"], "READY_UNCONSUMED")
        self.assertFalse(result["launch_claim_present"])
        self.assertFalse(result["terminal_present"])
        self.assertFalse((REPO_ROOT / audit.CLAIM_RELATIVE).exists())
        self.assertFalse((REPO_ROOT / audit.RESULTS_BASE_RELATIVE).exists())
        self.assertEqual(self._guarded_snapshot(), before)

    def test_request_envelope_omits_model_and_thinking(self) -> None:
        claim = self._claim()
        task_claim = claim["task_claims"][0]
        task = self.tasks_by_id[str(task_claim["task_id"])]
        prompt = audit.build_initial_prompt(task, task_claim)
        request = audit.expected_create_thread_arguments(task, task_claim)
        self.assertEqual(set(request), {"prompt", "target", "title"})
        self.assertNotIn("model", request)
        self.assertNotIn("thinking", request)
        self.assertEqual(request["prompt"], prompt)
        self.assertIn(str(task_claim["task_id"]), prompt)
        self.assertIn(str(task_claim["context_id"]), prompt)
        self.assertIn(str(task_claim["finalization_id"]), prompt)
        self.assertIn("Return exactly one UTF-8 JSON object", prompt)
        self.assertEqual(
            request["target"],
            {
                "type": "project",
                "projectId": audit.PROJECT_ID,
                "environment": {
                    "type": "worktree",
                    "startingState": {
                        "type": "branch",
                        "branchName": audit.AUTHORIZATION_BRANCH,
                    },
                },
            },
        )

    def test_request_binding_aggregate_is_order_sensitive(self) -> None:
        aggregate = audit.request_binding_aggregate(self.tasks)
        self.assertRegex(aggregate, r"^[0-9a-f]{64}$")
        changed = list(self.tasks)
        changed[0], changed[1] = changed[1], changed[0]
        self.assertNotEqual(audit.request_binding_aggregate(changed), aggregate)

    def test_exclusive_create_refuses_overwrite(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            path = Path(temp_dir) / "claim.json"
            audit.exclusive_create_bytes(path, b"first")
            self.assertEqual(path.read_bytes(), b"first")
            with self.assertRaises(FileExistsError):
                audit.exclusive_create_bytes(path, b"second")
            self.assertEqual(path.read_bytes(), b"first")

    def test_valid_claim_without_tasks_is_claimed_in_progress(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            claim = self._claim()
            claim_path = root / "claim.json"
            _write_json(claim_path, claim)
            result = audit.audit_execution(
                REPO_ROOT,
                claim_path=claim_path,
                results_base=root / "results" / "m4.1",
                terminal_path=root / "terminal.json",
                results_manifest_path=root / "results-manifest.json",
                verify_git=False,
            )
        self.assertEqual(result["status"], "CLAIMED_IN_PROGRESS")
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["token"], "CONSUMED")
        self.assertEqual(result["tasks"], 0)

    def test_authorization_auditor_observes_claim_as_consumed_proof(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            claim_path = root / "claim.json"
            _write_json(claim_path, self._claim())
            result = audit.authorization_audit.audit_authorization(
                REPO_ROOT,
                launch_claim_path=claim_path,
                results_parent=root / "absent-results",
                configured_model=audit.MODEL_ID,
                configured_reasoning_effort=audit.REASONING_EFFORT,
                verify_git=False,
            )
        self.assertEqual(result["status"], "INVALID")
        self.assertIn("authorization_already_claimed", result["errors"])

    def test_accepts_complete_unjudged_without_content_scoring(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            claim_path, results_base, terminal_path, _ = self._write_complete_fixture(
                root, poor_quality_first=True
            )
            result = audit.audit_execution(
                REPO_ROOT,
                claim_path=claim_path,
                results_base=results_base,
                terminal_path=terminal_path,
                results_manifest_path=root / "results-manifest.json",
                verify_git=False,
            )
        self.assertEqual(result["status"], "COMPLETE_UNJUDGED")
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["tasks"], 60)
        self.assertEqual(result["threads"], 60)
        self.assertEqual(result["finalizations"], 60)
        self.assertEqual(result["attempts"], 60)
        self.assertEqual(result["results"], 60)
        self.assertEqual(result["retries"], 0)
        self.assertEqual(result["repairs"], 0)
        self.assertEqual(result["followups"], 0)
        self.assertEqual(result["judge_calls"], 0)
        self.assertEqual(result["aggregation_calls"], 0)
        self.assertEqual(result["side_effects"], 0)

    def test_accepts_stopped_protocol_failure_with_invalid_raw_preserved(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            claim = self._claim()
            claim_path = root / "claim.json"
            claim_raw = _write_json(claim_path, claim)
            results_base = root / "results" / "m4.1"
            task_id = claim["task_ids"][0]
            task_root = results_base / task_id
            receipt = self._receipt(claim, claim_raw, 0)
            receipt_raw = _write_json(task_root / "dispatch-receipt.json", receipt)
            raw_final = b"not-json and must remain byte-identical"
            (task_root / "raw-final.txt").write_bytes(raw_final)
            receipt_refs = [
                {
                    "task_id": task_id,
                    "thread_id": receipt["response"]["thread_id"],
                    "path": f"evals/m4/results/m4.1/{task_id}/dispatch-receipt.json",
                    "raw_sha256": audit.sha256(receipt_raw),
                }
            ]
            raw_refs = [
                {
                    "task_id": task_id,
                    "finalization_id": claim["task_claims"][0]["finalization_id"],
                    "path": f"evals/m4/results/m4.1/{task_id}/raw-final.txt",
                    "byte_length": len(raw_final),
                    "raw_sha256": audit.sha256(raw_final),
                    "protocol_validation": "INVALID",
                    "observed_at_utc": "2026-08-08T13:00:00Z",
                }
            ]
            terminal = self._terminal(
                claim,
                claim_raw,
                receipt_refs,
                raw_refs,
                state="STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE",
            )
            terminal_path = root / "terminal.json"
            _write_json(terminal_path, terminal)
            result = audit.audit_execution(
                REPO_ROOT,
                claim_path=claim_path,
                results_base=results_base,
                terminal_path=terminal_path,
                results_manifest_path=root / "results-manifest.json",
                verify_git=False,
            )
            self.assertEqual((task_root / "raw-final.txt").read_bytes(), raw_final)
        self.assertEqual(
            result["status"], "STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE"
        )
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["tasks"], 1)
        self.assertEqual(result["finalizations"], 1)
        self.assertEqual(result["results"], 1)
        self.assertTrue(result["successor_revision_required"])

    def test_accepts_stopped_infrastructure_creation_failure_without_receipt(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            claim = self._claim()
            claim_path = root / "claim.json"
            claim_raw = _write_json(claim_path, claim)
            terminal = self._terminal(
                claim,
                claim_raw,
                [],
                [],
                state="STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE",
            )
            terminal["attempted_task_ids"] = [claim["task_ids"][0]]
            terminal["counts"]["attempts"] = 1
            terminal["failed_stage"] = "create_thread_ready_identifier_observation"
            terminal["failure_evidence"] = {
                "failure_class": "INFRASTRUCTURE_FAILURE",
                "raw_evidence": "create_thread returned clientThreadId without a ready threadId",
                "raw_evidence_sha256": audit.sha256(
                    b"create_thread returned clientThreadId without a ready threadId"
                ),
            }
            terminal_path = root / "terminal.json"
            _write_json(terminal_path, terminal)
            result = audit.audit_execution(
                REPO_ROOT,
                claim_path=claim_path,
                results_base=root / "results" / "m4.1",
                terminal_path=terminal_path,
                results_manifest_path=root / "results-manifest.json",
                verify_git=False,
            )
        self.assertEqual(
            result["status"], "STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE"
        )
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["attempts"], 1)
        self.assertEqual(result["tasks"], 0)
        self.assertEqual(result["finalizations"], 0)

    def test_rejects_claim_order_duplicate_identity_and_later_authority_drift(self) -> None:
        mutations = (
            (
                "order",
                lambda claim: claim["task_ids"].__setitem__(
                    slice(0, 2), list(reversed(claim["task_ids"][:2]))
                ),
                "claim_task_order_invalid",
            ),
            (
                "context",
                lambda claim: claim["task_claims"][1].__setitem__(
                    "context_id", claim["task_claims"][0]["context_id"]
                ),
                "claim_context_id_duplicate",
            ),
            (
                "retry",
                lambda claim: claim["limits"].__setitem__("retries", 1),
                "claim_limits_invalid",
            ),
        )
        for label, mutate, error in mutations:
            with self.subTest(label=label), tempfile.TemporaryDirectory(
                dir=REPO_ROOT
            ) as temp_dir:
                root = Path(temp_dir)
                claim = self._claim()
                mutate(claim)
                claim_path = root / "claim.json"
                _write_json(claim_path, claim)
                result = audit.audit_execution(
                    REPO_ROOT,
                    claim_path=claim_path,
                    results_base=root / "results" / "m4.1",
                    terminal_path=root / "terminal.json",
                    results_manifest_path=root / "results-manifest.json",
                    verify_git=False,
                )
                self.assertEqual(result["status"], "INVALID")
                self.assertIn(error, result["errors"])

    def test_rejects_duplicate_thread_raw_tamper_or_unexpected_artifact(self) -> None:
        mutations = ("duplicate_thread", "raw_tamper", "unexpected_artifact")
        for mutation in mutations:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory(
                dir=REPO_ROOT
            ) as temp_dir:
                root = Path(temp_dir)
                claim_path, results_base, terminal_path, terminal = (
                    self._write_complete_fixture(root)
                )
                if mutation == "duplicate_thread":
                    second_id = terminal["dispatch_receipts"][1]["task_id"]
                    second_receipt_path = (
                        results_base / second_id / "dispatch-receipt.json"
                    )
                    second_receipt = audit.parse_json_object(
                        second_receipt_path.read_bytes()
                    )
                    second_receipt["response"]["thread_id"] = terminal[
                        "dispatch_receipts"
                    ][0]["thread_id"]
                    raw = _write_json(second_receipt_path, second_receipt)
                    terminal["dispatch_receipts"][1]["thread_id"] = second_receipt[
                        "response"
                    ]["thread_id"]
                    terminal["dispatch_receipts"][1]["raw_sha256"] = audit.sha256(
                        raw
                    )
                    _write_json(terminal_path, terminal)
                elif mutation == "raw_tamper":
                    first_id = terminal["raw_finals"][0]["task_id"]
                    (results_base / first_id / "raw-final.txt").write_bytes(
                        b"changed"
                    )
                else:
                    (results_base / "unexpected.bin").write_bytes(b"x")
                result = audit.audit_execution(
                    REPO_ROOT,
                    claim_path=claim_path,
                    results_base=results_base,
                    terminal_path=terminal_path,
                    results_manifest_path=root / "results-manifest.json",
                    verify_git=False,
                )
                self.assertEqual(result["status"], "INVALID")
                expected = {
                    "duplicate_thread": "thread_id_duplicate",
                    "raw_tamper": "raw_final_hash_mismatch",
                    "unexpected_artifact": "unexpected_execution_artifact",
                }[mutation]
                self.assertIn(expected, result["errors"])

    def test_rejects_malformed_final_marked_valid_and_stopped_later_batch_activity(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            claim = self._claim()
            claim_path = root / "claim.json"
            claim_raw = _write_json(claim_path, claim)
            results_base = root / "results" / "m4.1"
            task_id = claim["task_ids"][0]
            task_root = results_base / task_id
            receipt = self._receipt(claim, claim_raw, 0)
            receipt_raw = _write_json(task_root / "dispatch-receipt.json", receipt)
            malformed = b"{\"broken\":"
            (task_root / "raw-final.txt").write_bytes(malformed)
            receipt_refs = [
                {
                    "task_id": task_id,
                    "thread_id": receipt["response"]["thread_id"],
                    "path": f"evals/m4/results/m4.1/{task_id}/dispatch-receipt.json",
                    "raw_sha256": audit.sha256(receipt_raw),
                }
            ]
            raw_refs = [
                {
                    "task_id": task_id,
                    "finalization_id": claim["task_claims"][0]["finalization_id"],
                    "path": f"evals/m4/results/m4.1/{task_id}/raw-final.txt",
                    "byte_length": len(malformed),
                    "raw_sha256": audit.sha256(malformed),
                    "protocol_validation": "VALID",
                    "observed_at_utc": "2026-08-08T13:00:00Z",
                }
            ]
            terminal = self._terminal(
                claim,
                claim_raw,
                receipt_refs,
                raw_refs,
                state="COMPLETE_UNJUDGED",
            )
            terminal_path = root / "terminal.json"
            _write_json(terminal_path, terminal)
            result = audit.audit_execution(
                REPO_ROOT,
                claim_path=claim_path,
                results_base=results_base,
                terminal_path=terminal_path,
                results_manifest_path=root / "results-manifest.json",
                verify_git=False,
            )
        self.assertEqual(result["status"], "INVALID")
        self.assertIn("raw_final_marked_valid_but_protocol_invalid", result["errors"])

    def test_rejects_stopped_terminal_after_later_batch_activity(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            claim_path, results_base, terminal_path, terminal = (
                self._write_complete_fixture(root)
            )
            terminal["terminal_state"] = (
                "STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE"
            )
            terminal["last_completed_batch"] = None
            terminal["failed_batch"] = audit.BATCH_ORDER[0]
            terminal["failed_task_id"] = claim_task = terminal[
                "attempted_task_ids"
            ][10]
            terminal["failed_stage"] = "create_thread_transport"
            terminal["attempted_task_ids"] = terminal["attempted_task_ids"][:11]
            terminal["dispatch_receipts"] = terminal["dispatch_receipts"][:11]
            terminal["raw_finals"] = terminal["raw_finals"][:10]
            terminal["counts"].update(
                {
                    "tasks": 11,
                    "threads": 11,
                    "finalizations": 10,
                    "attempts": 11,
                    "results": 10,
                }
            )
            raw_evidence = f"later batch activity reached {claim_task}"
            terminal["failure_evidence"] = {
                "failure_class": "INFRASTRUCTURE_FAILURE",
                "raw_evidence": raw_evidence,
                "raw_evidence_sha256": audit.sha256(raw_evidence.encode("utf-8")),
            }
            terminal["later_batches_not_started"] = list(audit.BATCH_ORDER[1:])
            terminal["successor_revision_required"] = True
            _write_json(terminal_path, terminal)
            result = audit.audit_execution(
                REPO_ROOT,
                claim_path=claim_path,
                results_base=results_base,
                terminal_path=terminal_path,
                results_manifest_path=root / "results-manifest.json",
                verify_git=False,
            )
        self.assertEqual(result["status"], "INVALID")
        self.assertIn("stopped_later_batch_activity", result["errors"])
        self.assertIn("stopped_failed_task_batch_mismatch", result["errors"])

    def test_rejects_valid_raw_final_relabelled_as_protocol_failure(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            claim = self._claim()
            claim_path = root / "claim.json"
            claim_raw = _write_json(claim_path, claim)
            results_base = root / "results" / "m4.1"
            task_id = claim["task_ids"][0]
            task_root = results_base / task_id
            receipt = self._receipt(claim, claim_raw, 0)
            receipt_raw = _write_json(task_root / "dispatch-receipt.json", receipt)
            final_raw = audit.canonical_bytes(
                self._task_result(
                    claim,
                    0,
                    response="poor quality is not a protocol failure",
                )
            ) + b"\n"
            (task_root / "raw-final.txt").write_bytes(final_raw)
            terminal = self._terminal(
                claim,
                claim_raw,
                [
                    {
                        "task_id": task_id,
                        "thread_id": receipt["response"]["thread_id"],
                        "path": f"evals/m4/results/m4.1/{task_id}/dispatch-receipt.json",
                        "raw_sha256": audit.sha256(receipt_raw),
                    }
                ],
                [
                    {
                        "task_id": task_id,
                        "finalization_id": claim["task_claims"][0][
                            "finalization_id"
                        ],
                        "path": f"evals/m4/results/m4.1/{task_id}/raw-final.txt",
                        "byte_length": len(final_raw),
                        "raw_sha256": audit.sha256(final_raw),
                        "protocol_validation": "INVALID",
                        "observed_at_utc": "2026-08-08T13:00:00Z",
                    }
                ],
                state="STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE",
            )
            terminal_path = root / "terminal.json"
            _write_json(terminal_path, terminal)
            result = audit.audit_execution(
                REPO_ROOT,
                claim_path=claim_path,
                results_base=results_base,
                terminal_path=terminal_path,
                results_manifest_path=root / "results-manifest.json",
                verify_git=False,
            )
        self.assertEqual(result["status"], "INVALID")
        self.assertIn("raw_final_protocol_classification_invalid", result["errors"])

    def test_configured_default_drift_fails_before_claim(self) -> None:
        result = audit.audit_execution(
            REPO_ROOT,
            configured_model="wrong-model",
            configured_reasoning_effort=audit.REASONING_EFFORT,
        )
        self.assertEqual(result["status"], "INVALID")
        self.assertIn("authorization_audit_failed:configured_model_mismatch", result["errors"])


if __name__ == "__main__":
    unittest.main()
