from __future__ import annotations

import copy
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


CANDIDATE_ROOT = Path(__file__).resolve().parents[1]
EXECUTION_ROOT = CANDIDATE_ROOT / "evals" / "m4" / "execution"
sys.path.insert(0, str(EXECUTION_ROOT))

import audit_m4_2 as protocol  # noqa: E402
import build_m4_2_launch_claim as claim_builder  # noqa: E402
import record_m4_2_execution_evidence as recorder  # noqa: E402


TASK_SUFFIXES = (
    "A-F",
    "B-A1",
    "A-A1",
    "B-A3",
    "A-A2",
    "B-F",
    "A-N",
    "B-A2",
    "A-A3",
    "B-N",
)


def _write_json(path: Path, value: object) -> bytes:
    raw = protocol.json_bytes(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return raw


class SyntheticGateARepository:
    def __init__(self, root: Path):
        self.root = root
        self.authorization_path = (
            root / "evals/m4/authorization/m4.2/execution-authorization.json"
        )
        self.control_path = (
            root / "evals/m4/authorization/m4.2/execution-control.json"
        )
        self.claim_path = root / protocol.CLAIM_RELATIVE
        self.observations = root / protocol.OBSERVATIONS_BASE_RELATIVE
        self.results = root / protocol.RESULTS_BASE_RELATIVE
        self.terminal_path = root / protocol.TERMINAL_RELATIVE
        self.results_manifest = root / protocol.RESULTS_MANIFEST_RELATIVE
        self.m5 = root / protocol.M5_RELATIVE
        self.gate_a = claim_builder.GateAAcceptance(
            candidate_head="1" * 40,
            candidate_tree="2" * 40,
            push_run_id=123456,
            pr_run_id=123457,
        )
        self.tasks = self._build()

    def _build(self) -> list[dict[str, object]]:
        for relative in (
            protocol.LAUNCH_SCHEMA_RELATIVE,
            protocol.DISPATCH_SCHEMA_RELATIVE,
            protocol.RESPONSE_ATTESTATION_SCHEMA_RELATIVE,
            protocol.TERMINAL_SCHEMA_RELATIVE,
        ):
            source = CANDIDATE_ROOT / relative
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())
        (self.root / protocol.TASK_PROTOCOL_RELATIVE).parent.mkdir(
            parents=True, exist_ok=True
        )
        (self.root / protocol.TASK_PROTOCOL_RELATIVE).write_text(
            "Follow the frozen protocol. Never read another task result.\n",
            encoding="utf-8",
            newline="\n",
        )
        (self.root / protocol.RESULT_SCHEMA_RELATIVE).parent.mkdir(
            parents=True, exist_ok=True
        )
        (self.root / protocol.RESULT_SCHEMA_RELATIVE).write_text(
            '{"type":"object","additionalProperties":false}\n',
            encoding="utf-8",
            newline="\n",
        )
        case_path = "evals/m4/cases/synthetic.json"
        (self.root / case_path).parent.mkdir(parents=True, exist_ok=True)
        (self.root / case_path).write_text(
            '{"case_id":"synthetic","user_input":"Evaluate this engineering problem."}\n',
            encoding="utf-8",
            newline="\n",
        )
        variant_paths: dict[str, str] = {}
        for variant in ("F", "A1", "A2", "A3"):
            relative = f"evals/m4/variants/{variant}/instructions.md"
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                f"Synthetic frozen {variant} instruction.\n",
                encoding="utf-8",
                newline="\n",
            )
            variant_paths[variant] = relative
        tasks: list[dict[str, object]] = []
        batches: list[dict[str, object]] = []
        blind = 121
        for batch_id in protocol.BATCH_ORDER:
            domain = batch_id.rsplit("-", 1)[-1]
            task_ids = []
            for suffix in TASK_SUFFIXES:
                task_id = f"M4.2-{domain}-{suffix}"
                task_ids.append(task_id)
                arm = suffix.split("-", 1)[1]
                variant = None if arm == "N" else variant_paths[arm]
                tasks.append(
                    {
                        "allowed_context_paths": [
                            case_path,
                            protocol.TASK_PROTOCOL_RELATIVE.as_posix(),
                            *([] if variant is None else [variant]),
                        ],
                        "attempt_limit": 1,
                        "batch_id": batch_id,
                        "blind_id": f"M4-J{blind}",
                        "case_path": case_path,
                        "cross_task_result_visibility": False,
                        "forbidden_context_roots": [
                            "evals/m4/results",
                            "evals/m4/execution",
                        ],
                        "independent_finalization_required": True,
                        "request_binding_sha256": protocol.sha256(
                            f"binding|{task_id}".encode("utf-8")
                        ),
                        "result_root": f"evals/m4/results/m4.2/{task_id}",
                        "result_root_must_be_absent": True,
                        "root_task_id": task_id.replace("M4.2", "M4"),
                        "source_task_id": task_id.replace("M4.2", "M4.1"),
                        "task_id": task_id,
                        "task_protocol_path": protocol.TASK_PROTOCOL_RELATIVE.as_posix(),
                        "variant_instruction_path": variant,
                    }
                )
                blind += 1
            batches.append(
                {
                    "batch_id": batch_id,
                    "domain": domain.lower(),
                    "later_batches_mutable_after_observation": False,
                    "planned_task_count": 10,
                    "source_batch_id": batch_id.replace("M4.2", "M4.1"),
                    "stop_on_infrastructure_or_protocol_failure": True,
                    "task_ids": task_ids,
                }
            )
        token = "sha256:" + "a" * 64
        zeros = {name: 0 for name in protocol.ZERO_COUNTER_NAMES}
        authorization = {
            "schema_version": "m4.2-execution-authorization-v1",
            "milestone": "M4",
            "revision": "M4.2",
            "status": "AUTHORIZED_UNCONSUMED",
            "authorization_token": token,
            "prelaunch_counters": zeros,
            "authority": {
                "aggregation_authorized": False,
                "attempts_per_task_id": 1,
                "authorized_batch_count": 6,
                "authorized_batch_ids": list(protocol.BATCH_ORDER),
                "authorized_task_count": 60,
                "authorized_task_ids": [task["task_id"] for task in tasks],
                "blind_mapping_access_authorized": False,
                "closure_authorized": False,
                "cross_task_result_visibility": False,
                "followup_message_authorized": False,
                "fresh_contexts_authorized": 60,
                "fresh_execution_authorized": True,
                "independent_finalizations_authorized": 60,
                "judge_execution_authorized": False,
                "partial_authority_allowed": False,
                "repair_authorized": False,
                "result_write_root_prefix": "evals/m4/results/m4.2",
                "result_writes_authorized": True,
                "retry_authorized": False,
                "threshold_claim_authorized": False,
                "whole_matrix_required": True,
            },
            "model_binding": {
                "configured_default_required": True,
                "exact_model_id": protocol.MODEL_ID,
                "model_argument_policy": "OMIT_AND_VERIFY_CONFIGURED_DEFAULT",
                "reasoning_effort": protocol.REASONING_EFFORT,
                "thinking_argument_policy": "OMIT_AND_VERIFY_CONFIGURED_DEFAULT",
            },
            "execution_surface": {
                "cross_task_result_visibility": False,
                "environment": "worktree",
                "project_id": protocol.PROJECT_ID,
                "project_is_git_repository": True,
                "project_label": "synthetic",
                "starting_branch": protocol.AUTHORIZATION_BRANCH,
                "task_context_isolation": "ONE_NEW_THREAD_PER_TASK_ID",
                "tool": "codex_app.create_thread",
            },
        }
        authorization_raw = _write_json(self.authorization_path, authorization)
        control = {
            "schema_version": "m4.2-execution-control-v1",
            "milestone": "M4",
            "revision": "M4.2",
            "status": "READY_UNCONSUMED",
            "authorization": {
                "authorization_token": token,
                "path": protocol.AUTHORIZATION_RELATIVE.as_posix(),
                "raw_sha256": protocol.sha256(authorization_raw),
            },
            "batch_order": list(protocol.BATCH_ORDER),
            "batches": batches,
            "tasks": tasks,
            "prelaunch_counters": zeros,
            "request_policy": {
                "cross_task_result_visibility": False,
                "environment_type": "worktree",
                "one_independent_finalization_per_task_id": True,
                "one_new_thread_per_task_id": True,
                "project_id": protocol.PROJECT_ID,
                "starting_branch": protocol.AUTHORIZATION_BRANCH,
                "surface": "codex_app.create_thread",
                "target_type": "project",
            },
            "permissions": {
                "aggregation": False,
                "blind_mapping_access": False,
                "cross_task_result_read": False,
                "followup_message": False,
                "fresh_task_creation": True,
                "judge_execution": False,
                "m4_closure": False,
                "repair": False,
                "result_writes_below_frozen_roots": True,
                "retry": False,
                "threshold_claim": False,
            },
        }
        _write_json(self.control_path, control)
        return tasks

    def audit_kwargs(self) -> dict[str, object]:
        return {
            "claim_path": self.claim_path,
            "observations_base": self.observations,
            "results_base": self.results,
            "terminal_path": self.terminal_path,
            "results_manifest_path": self.results_manifest,
            "m5_path": self.m5,
            "verify_git": False,
            "enforce_frozen_hashes": False,
            "authorization_path": self.authorization_path,
            "control_path": self.control_path,
        }

    def claim(self, at: str = "2026-08-12T12:00:00Z") -> dict[str, object]:
        return claim_builder.build_claim(
            self.root,
            gate_a=self.gate_a,
            claimed_at_utc=at,
            verify_git=False,
            enforce_frozen_hashes=False,
            authorization_path=self.authorization_path,
            control_path=self.control_path,
        )

    def consume(self) -> dict[str, object]:
        return claim_builder.consume_claim(
            self.root,
            gate_a=self.gate_a,
            claimed_at_utc="2026-08-12T12:00:00Z",
            verify_git=False,
            verify_live=False,
            enforce_frozen_hashes=False,
            authorization_path=self.authorization_path,
            control_path=self.control_path,
            claim_path=self.claim_path,
            observations_base=self.observations,
            results_base=self.results,
            terminal_path=self.terminal_path,
            results_manifest_path=self.results_manifest,
            m5_path=self.m5,
        )

    def response_raw(self, index: int, checkout: str | None = None) -> bytes:
        value = {
            "threadId": f"thread-{index + 1:03d}",
            "hostId": "local",
            "resolvedCheckoutSha": checkout or protocol.AUTHORIZATION_CLOSURE_HEAD,
        }
        return protocol.json_bytes(value)

    def final_raw(self, index: int, *, response: str = "protocol valid") -> bytes:
        claim = protocol.parse_json_object(self.claim_path.read_bytes())
        task_claim = claim["task_claims"][index]
        task = self.tasks[index]
        value = {
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
        return protocol.json_bytes(value)


class M42ExecutionProtocolTests(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.repo = SyntheticGateARepository(Path(self.temp.name))

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_all_four_schemas_are_recursively_closed_and_gate_a_non_instances(self) -> None:
        for relative in (
            protocol.LAUNCH_SCHEMA_RELATIVE,
            protocol.DISPATCH_SCHEMA_RELATIVE,
            protocol.RESPONSE_ATTESTATION_SCHEMA_RELATIVE,
            protocol.TERMINAL_SCHEMA_RELATIVE,
        ):
            with self.subTest(path=relative.as_posix()):
                schema = protocol.parse_json_object((self.repo.root / relative).read_bytes())
                self.assertTrue(protocol.recursively_closed_schema(schema))
                self.assertIs(schema["x-real-instance-allowed-in-gate-a"], False)

    def test_repository_is_ready_unclaimed_and_read_only(self) -> None:
        before = sorted(path.relative_to(self.repo.root).as_posix() for path in self.repo.root.rglob("*"))
        first = protocol.audit_execution(self.repo.root, **self.repo.audit_kwargs())
        second = protocol.audit_execution(self.repo.root, **self.repo.audit_kwargs())
        self.assertEqual(first, second)
        self.assertEqual(first["status"], "READY_UNCLAIMED")
        self.assertEqual(first["errors"], [])
        self.assertEqual(first["token"], "UNCONSUMED")
        self.assertEqual(first["claim_count"], 0)
        self.assertEqual(first["tasks"], 0)
        self.assertFalse(self.repo.claim_path.exists())
        after = sorted(path.relative_to(self.repo.root).as_posix() for path in self.repo.root.rglob("*"))
        self.assertEqual(before, after)

    def test_request_envelopes_are_deterministic_unique_and_omit_overrides(self) -> None:
        claim = self.repo.claim()
        hashes = set()
        for task, task_claim in zip(self.repo.tasks, claim["task_claims"], strict=True):
            first = protocol.expected_create_thread_arguments(self.repo.root, task, task_claim)
            second = protocol.expected_create_thread_arguments(self.repo.root, task, task_claim)
            self.assertEqual(first, second)
            self.assertEqual(set(first), {"prompt", "target", "title"})
            self.assertNotIn("model", first)
            self.assertNotIn("thinking", first)
            self.assertIn(task_claim["task_id"], first["prompt"])
            self.assertIn(task_claim["context_id"], first["prompt"])
            hashes.add(protocol.canonical_sha256(first))
        self.assertEqual(len(hashes), 60)

    def test_claim_template_is_byte_deterministic_and_exactly_whole_matrix(self) -> None:
        first = self.repo.claim()
        second = self.repo.claim()
        self.assertEqual(protocol.json_bytes(first), protocol.json_bytes(second))
        self.assertEqual(first["claim_count"], 1)
        self.assertEqual(len(first["task_ids"]), 60)
        self.assertEqual(len(first["task_claims"]), 60)
        self.assertEqual(len({x["context_id"] for x in first["task_claims"]}), 60)
        self.assertEqual(len({x["finalization_id"] for x in first["task_claims"]}), 60)
        self.assertNotIn("authorization_token", first["authorization"])

    def test_exclusive_claim_consumes_once_and_uses_only_postclaim_execution_auditor(self) -> None:
        preclaim = recorder.next_action(self.repo.root, **self.repo.audit_kwargs())
        self.assertEqual(preclaim["mode"], "NEXT_ACTION")
        self.assertEqual(preclaim["status"], "READY_UNCLAIMED")
        self.assertEqual(preclaim["action"], "CONSUME_CLAIM")
        self.assertIsNone(preclaim["task_id"])
        self.assertEqual(preclaim["writes"], 0)
        first = self.repo.consume()
        self.assertEqual(first["status"], "CLAIMED_IN_PROGRESS")
        self.assertEqual(first["errors"], [])
        self.assertIs(first["preclaim_authorization_auditor_reused"], False)
        postclaim = recorder.next_action(self.repo.root, **self.repo.audit_kwargs())
        self.assertEqual(postclaim["action"], "CREATE_THREAD")
        self.assertEqual(postclaim["task_id"], self.repo.tasks[0]["task_id"])
        self.assertEqual(postclaim["batch_id"], protocol.BATCH_ORDER[0])
        self.assertEqual(postclaim["global_sequence"], 1)
        self.assertEqual(set(postclaim["create_thread_arguments"]), {"prompt", "target", "title"})
        self.assertNotIn("model", postclaim["create_thread_arguments"])
        self.assertNotIn("thinking", postclaim["create_thread_arguments"])
        self.assertEqual(postclaim["writes"], 0)
        raw = self.repo.claim_path.read_bytes()
        second = self.repo.consume()
        self.assertEqual(second["status"], "ALREADY_CLAIMED")
        self.assertEqual(self.repo.claim_path.read_bytes(), raw)
        source = Path(claim_builder.__file__).read_text(encoding="utf-8")
        self.assertNotIn("audit_m4_2_authorization", source)

    def test_reordered_or_partial_claim_fails_closed(self) -> None:
        claim = self.repo.claim()
        claim["task_ids"][0], claim["task_ids"][1] = claim["task_ids"][1], claim["task_ids"][0]
        _write_json(self.repo.claim_path, claim)
        result = protocol.audit_execution(self.repo.root, **self.repo.audit_kwargs())
        self.assertEqual(result["status"], "INVALID")
        self.assertIn("claim_task_order_invalid", result["errors"])

    def test_valid_dispatch_and_final_are_raw_first_and_prefix_ordered(self) -> None:
        self.assertEqual(self.repo.consume()["status"], "CLAIMED_IN_PROGRESS")
        task_id = self.repo.tasks[0]["task_id"]
        response_raw = self.repo.response_raw(0)
        response_file = self.repo.root / "synthetic-inputs" / "response.bin"
        response_file.parent.mkdir(parents=True)
        response_file.write_bytes(response_raw)
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = recorder.main(
                [
                    "--record-dispatch",
                    "--task-id",
                    task_id,
                    "--response-file",
                    str(response_file),
                    "--captured-at-utc",
                    "2026-08-12T12:01:00Z",
                ],
                repo_root=self.repo.root,
                audit_kwargs=self.repo.audit_kwargs(),
            )
        self.assertEqual(exit_code, 0)
        dispatched = json.loads(output.getvalue())
        self.assertEqual(dispatched["mode"], "RECORD_DISPATCH")
        self.assertEqual(response_file.read_bytes(), response_raw)
        self.assertEqual(dispatched["status"], "CLAIMED_IN_PROGRESS")
        self.assertEqual(dispatched["tasks"], 1)
        awaiting_final = recorder.next_action(self.repo.root, **self.repo.audit_kwargs())
        self.assertEqual(awaiting_final["action"], "RECORD_FINAL")
        self.assertEqual(awaiting_final["task_id"], task_id)
        self.assertEqual(awaiting_final["global_sequence"], 1)
        self.assertIsNone(awaiting_final["create_thread_arguments"])
        self.assertEqual(awaiting_final["writes"], 0)
        self.assertEqual(
            (self.repo.observations / task_id / recorder.RAW_RESPONSE_NAME).read_bytes(),
            response_raw,
        )
        final_raw = self.repo.final_raw(0, response="poor quality but protocol valid")
        final_file = self.repo.root / "synthetic-inputs" / "final.bin"
        final_file.write_bytes(final_raw)
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = recorder.main(
                [
                    "--record-final",
                    "--task-id",
                    task_id,
                    "--final-file",
                    str(final_file),
                    "--observed-at-utc",
                    "2026-08-12T12:02:00Z",
                ],
                repo_root=self.repo.root,
                audit_kwargs=self.repo.audit_kwargs(),
            )
        self.assertEqual(exit_code, 0)
        finalized = json.loads(output.getvalue())
        self.assertEqual(finalized["mode"], "RECORD_FINAL")
        self.assertEqual(final_file.read_bytes(), final_raw)
        self.assertEqual(finalized["status"], "PROTOCOL_VALID_CONTINUE")
        self.assertEqual(
            (self.repo.results / task_id / recorder.RAW_FINAL_NAME).read_bytes(),
            final_raw,
        )
        wrong = recorder.record_dispatch(
            self.repo.root,
            task_id=self.repo.tasks[2]["task_id"],
            response_raw=self.repo.response_raw(2),
            captured_at_utc="2026-08-12T12:03:00Z",
            **self.repo.audit_kwargs(),
        )
        self.assertEqual(wrong["status"], "INVALID")
        self.assertEqual(wrong["errors"], ["dispatch_not_next_frozen_task"])
        self.assertEqual(wrong["writes"], 0)

    def test_checkout_mismatch_preserves_response_and_creates_unique_terminal(self) -> None:
        self.repo.consume()
        task_id = self.repo.tasks[0]["task_id"]
        raw = self.repo.response_raw(0, checkout="0" * 40)
        result = recorder.record_dispatch(
            self.repo.root,
            task_id=task_id,
            response_raw=raw,
            captured_at_utc="2026-08-12T12:01:00Z",
            **self.repo.audit_kwargs(),
        )
        self.assertEqual(
            result["status"], "STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE"
        )
        self.assertEqual(
            (self.repo.observations / task_id / recorder.RAW_RESPONSE_NAME).read_bytes(),
            raw,
        )
        terminal_raw = self.repo.terminal_path.read_bytes()
        repeated = recorder.record_dispatch(
            self.repo.root,
            task_id=self.repo.tasks[1]["task_id"],
            response_raw=self.repo.response_raw(1),
            captured_at_utc="2026-08-12T12:02:00Z",
            **self.repo.audit_kwargs(),
        )
        self.assertEqual(repeated["status"], "STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE")
        self.assertEqual(self.repo.terminal_path.read_bytes(), terminal_raw)

    def test_invalid_raw_final_is_preserved_stopped_and_never_repaired(self) -> None:
        self.repo.consume()
        task_id = self.repo.tasks[0]["task_id"]
        recorder.record_dispatch(
            self.repo.root,
            task_id=task_id,
            response_raw=self.repo.response_raw(0),
            captured_at_utc="2026-08-12T12:01:00Z",
            **self.repo.audit_kwargs(),
        )
        raw = b"not-json and must remain exact"
        stopped = recorder.record_final(
            self.repo.root,
            task_id=task_id,
            final_raw=raw,
            observed_at_utc="2026-08-12T12:02:00Z",
            **self.repo.audit_kwargs(),
        )
        self.assertEqual(
            stopped["status"], "STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE"
        )
        final_path = self.repo.results / task_id / recorder.RAW_FINAL_NAME
        self.assertEqual(final_path.read_bytes(), raw)
        repeated = recorder.record_final(
            self.repo.root,
            task_id=task_id,
            final_raw=b"replacement",
            observed_at_utc="2026-08-12T12:03:00Z",
            **self.repo.audit_kwargs(),
        )
        self.assertEqual(repeated["status"], "STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE")
        self.assertEqual(final_path.read_bytes(), raw)
        with tempfile.TemporaryDirectory() as directory:
            candidate = SyntheticGateARepository(Path(directory))
            candidate.consume()
            mismatch_task_id = candidate.tasks[0]["task_id"]
            recorder.record_dispatch(
                candidate.root,
                task_id=mismatch_task_id,
                response_raw=candidate.response_raw(0),
                captured_at_utc="2026-08-12T12:01:00Z",
                **candidate.audit_kwargs(),
            )
            mismatch = protocol.parse_json_object(candidate.final_raw(0))
            mismatch["task_id"] = candidate.tasks[1]["task_id"]
            mismatch_raw = protocol.json_bytes(mismatch)
            stopped = recorder.record_final(
                candidate.root,
                task_id=mismatch_task_id,
                final_raw=mismatch_raw,
                observed_at_utc="2026-08-12T12:02:00Z",
                **candidate.audit_kwargs(),
            )
            self.assertEqual(
                stopped["status"], "STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE"
            )
            self.assertEqual(
                (candidate.results / mismatch_task_id / recorder.RAW_FINAL_NAME).read_bytes(),
                mismatch_raw,
            )
            self.assertTrue(candidate.terminal_path.is_file())

    def test_untrusted_task_id_cannot_escape_or_create_target(self) -> None:
        self.repo.consume()
        before = sorted(path.relative_to(self.repo.root).as_posix() for path in self.repo.root.rglob("*"))
        result = recorder.record_dispatch(
            self.repo.root,
            task_id="../escape",
            response_raw=self.repo.response_raw(0),
            captured_at_utc="2026-08-12T12:01:00Z",
            **self.repo.audit_kwargs(),
        )
        self.assertEqual(result["status"], "INVALID")
        self.assertEqual(result["errors"], ["dispatch_not_next_frozen_task"])
        after = sorted(path.relative_to(self.repo.root).as_posix() for path in self.repo.root.rglob("*"))
        self.assertEqual(before, after)

    def test_full_synthetic_matrix_closes_only_as_complete_unjudged(self) -> None:
        self.assertEqual(
            recorder.next_action(self.repo.root, **self.repo.audit_kwargs())["action"],
            "CONSUME_CLAIM",
        )
        self.repo.consume()
        claim = protocol.parse_json_object(self.repo.claim_path.read_bytes())
        self.assertEqual(len({item["context_id"] for item in claim["task_claims"]}), 60)
        self.assertEqual(len({item["finalization_id"] for item in claim["task_claims"]}), 60)
        self.assertEqual(
            [task["batch_id"] for task in self.repo.tasks[::10]],
            list(protocol.BATCH_ORDER),
        )
        for index, task in enumerate(self.repo.tasks):
            task_id = task["task_id"]
            action = recorder.next_action(self.repo.root, **self.repo.audit_kwargs())
            self.assertEqual(action["action"], "CREATE_THREAD")
            self.assertEqual(action["task_id"], task_id)
            self.assertEqual(action["batch_id"], task["batch_id"])
            self.assertEqual(action["global_sequence"], index + 1)
            self.assertEqual(set(action["create_thread_arguments"]), {"prompt", "target", "title"})
            self.assertEqual(action["writes"], 0)
            if index == 10:
                for wrong_index in (11, 20):
                    rejected = recorder.record_dispatch(
                        self.repo.root,
                        task_id=self.repo.tasks[wrong_index]["task_id"],
                        response_raw=self.repo.response_raw(wrong_index),
                        captured_at_utc="2026-08-12T12:09:00Z",
                        **self.repo.audit_kwargs(),
                    )
                    self.assertEqual(rejected["status"], "INVALID")
                    self.assertEqual(rejected["writes"], 0)
            dispatched = recorder.record_dispatch(
                self.repo.root,
                task_id=task_id,
                response_raw=self.repo.response_raw(index),
                captured_at_utc="2026-08-12T12:10:00Z",
                **self.repo.audit_kwargs(),
            )
            self.assertEqual(dispatched["status"], "CLAIMED_IN_PROGRESS")
            final_action = recorder.next_action(self.repo.root, **self.repo.audit_kwargs())
            self.assertEqual(final_action["action"], "RECORD_FINAL")
            self.assertEqual(final_action["task_id"], task_id)
            self.assertEqual(final_action["global_sequence"], index + 1)
            self.assertEqual(final_action["writes"], 0)
            finalized = recorder.record_final(
                self.repo.root,
                task_id=task_id,
                final_raw=self.repo.final_raw(index),
                observed_at_utc="2026-08-12T12:11:00Z",
                **self.repo.audit_kwargs(),
            )
            expected = "READY_TO_RECORD_COMPLETE_TERMINAL" if index == 59 else "PROTOCOL_VALID_CONTINUE"
            self.assertEqual(finalized["status"], expected)
        complete_action = recorder.next_action(self.repo.root, **self.repo.audit_kwargs())
        self.assertEqual(complete_action["action"], "RECORD_COMPLETE_TERMINAL")
        self.assertEqual(complete_action["writes"], 0)
        output = io.StringIO()
        with redirect_stdout(output):
            exit_code = recorder.main(
                [
                    "--record-terminal",
                    "--state",
                    "COMPLETE_UNJUDGED",
                    "--recorded-at-utc",
                    "2026-08-12T12:30:00Z",
                ],
                repo_root=self.repo.root,
                audit_kwargs=self.repo.audit_kwargs(),
            )
        self.assertEqual(exit_code, 0)
        terminal = json.loads(output.getvalue())
        self.assertEqual(terminal["mode"], "RECORD_TERMINAL")
        self.assertEqual(terminal["status"], "COMPLETE_UNJUDGED")
        self.assertEqual(terminal["tasks"], 60)
        self.assertEqual(terminal["threads"], 60)
        self.assertEqual(terminal["finalizations"], 60)
        self.assertEqual(terminal["results"], 60)
        self.assertEqual(terminal["judge_calls"], 0)
        self.assertEqual(terminal["aggregation_calls"], 0)
        self.assertEqual(terminal["attempts"], 60)
        self.assertEqual(terminal["retries"], 0)
        self.assertEqual(terminal["repairs"], 0)
        self.assertEqual(terminal["followups"], 0)
        self.assertEqual(terminal["side_effects"], 0)
        self.assertEqual(
            recorder.next_action(self.repo.root, **self.repo.audit_kwargs())["action"],
            "STOP",
        )
        thread_ids = {
            protocol.parse_json_object(
                (self.repo.observations / task["task_id"] / recorder.RAW_RESPONSE_NAME).read_bytes()
            )["threadId"]
            for task in self.repo.tasks
        }
        self.assertEqual(len(thread_ids), 60)
        self.assertFalse(self.repo.results_manifest.exists())
        self.assertFalse(self.repo.m5.exists())

    def test_raw_tamper_and_unexpected_artifact_fail_closed(self) -> None:
        self.repo.consume()
        task_id = self.repo.tasks[0]["task_id"]
        recorder.record_dispatch(
            self.repo.root,
            task_id=task_id,
            response_raw=self.repo.response_raw(0),
            captured_at_utc="2026-08-12T12:01:00Z",
            **self.repo.audit_kwargs(),
        )
        recorder.record_final(
            self.repo.root,
            task_id=task_id,
            final_raw=self.repo.final_raw(0),
            observed_at_utc="2026-08-12T12:02:00Z",
            **self.repo.audit_kwargs(),
        )
        (self.repo.results / task_id / recorder.RAW_FINAL_NAME).write_bytes(b"tampered")
        result = protocol.audit_execution(self.repo.root, **self.repo.audit_kwargs())
        self.assertEqual(result["status"], "INVALID")
        self.assertIn("invalid_raw_final_without_terminal", result["errors"])
        (self.repo.results / "unexpected.bin").write_bytes(b"x")
        result = protocol.audit_execution(self.repo.root, **self.repo.audit_kwargs())
        self.assertIn("unexpected_execution_artifact", result["errors"])

    def test_strict_json_rejects_duplicate_bom_nonfinite_and_nonobject(self) -> None:
        samples = (
            (b'{"a":1,"a":2}', "duplicate_key"),
            (b"\xef\xbb\xbf{}", "utf8_bom_forbidden"),
            (b'{"x":NaN}', "non_finite_number"),
            (b"[]", "root_not_object"),
        )
        for raw, suffix in samples:
            with self.subTest(suffix=suffix):
                with self.assertRaises(protocol.ContractError) as context:
                    protocol.parse_json_object(raw, label="sample")
                self.assertIn(suffix, context.exception.code)

    def test_writer_sources_have_no_delete_overwrite_or_rollback_primitive(self) -> None:
        for module in (claim_builder, recorder):
            source = Path(module.__file__).read_text(encoding="utf-8")
            self.assertNotIn("os.replace", source)
            self.assertNotIn("os.remove", source)
            self.assertNotIn(".unlink(", source)
            self.assertNotIn("rmtree(", source)
        self.assertIn("os.O_EXCL", Path(protocol.__file__).read_text(encoding="utf-8"))


    def test_authorization_control_counter_and_batch_drift_fail_closed(self) -> None:
        mutations = (
            ("token", lambda authorization, control: control["authorization"].__setitem__("authorization_token", "sha256:" + "b" * 64), "control_authorization_token_mismatch"),
            ("counter", lambda authorization, control: authorization["prelaunch_counters"].__setitem__("retries", 1), "authorization_prelaunch_retries_nonzero_or_invalid"),
            ("bool-counter", lambda authorization, control: control["prelaunch_counters"].__setitem__("repairs", False), "control_prelaunch_repairs_nonzero_or_invalid"),
            ("batch-order", lambda authorization, control: control["batch_order"].__setitem__(slice(0, 2), list(reversed(control["batch_order"][:2]))), "control_batch_order_invalid"),
        )
        for label, mutate, expected in mutations:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                candidate = SyntheticGateARepository(Path(directory))
                authorization = protocol.parse_json_object(candidate.authorization_path.read_bytes())
                control = protocol.parse_json_object(candidate.control_path.read_bytes())
                mutate(authorization, control)
                _write_json(candidate.authorization_path, authorization)
                _write_json(candidate.control_path, control)
                result = protocol.audit_execution(candidate.root, **candidate.audit_kwargs())
                self.assertEqual(result["status"], "INVALID")
                self.assertIn(expected, result["errors"])

    def test_claim_context_limit_and_second_claim_mutations_fail_closed(self) -> None:
        mutations = (
            ("duplicate-context", lambda value: value["task_claims"][1].__setitem__("context_id", value["task_claims"][0]["context_id"]), "claim_task_claims_invalid"),
            ("retry", lambda value: value["limits"].__setitem__("retries", 1), "claim_limits_invalid"),
            ("partial", lambda value: value["task_claims"].pop(), "launch_claim_schema_invalid"),
        )
        for label, mutate, expected in mutations:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                candidate = SyntheticGateARepository(Path(directory))
                value = candidate.claim()
                mutate(value)
                _write_json(candidate.claim_path, value)
                result = protocol.audit_execution(candidate.root, **candidate.audit_kwargs())
                self.assertEqual(result["status"], "INVALID")
                self.assertIn(expected, result["errors"])

    def test_results_manifest_m5_and_runtime_without_claim_are_rejected(self) -> None:
        targets = (
            self.repo.results_manifest,
            self.repo.m5 / "marker.txt",
            self.repo.results / "orphan" / "raw-final.txt",
            self.repo.observations / "orphan" / recorder.RAW_RESPONSE_NAME,
            self.repo.terminal_path,
        )
        for target in targets:
            with self.subTest(target=target.relative_to(self.repo.root).as_posix()), tempfile.TemporaryDirectory() as directory:
                candidate = SyntheticGateARepository(Path(directory))
                mapped = candidate.root / target.relative_to(self.repo.root)
                mapped.parent.mkdir(parents=True, exist_ok=True)
                mapped.write_bytes(b"present")
                result = protocol.audit_execution(candidate.root, **candidate.audit_kwargs())
                self.assertEqual(result["status"], "INVALID")

    def test_setup_only_and_empty_responses_are_preserved_as_terminal_failures(self) -> None:
        for label, raw in (
            ("setup-only", b'{"clientThreadId":"setup-only"}'),
            ("empty", b""),
        ):
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                candidate = SyntheticGateARepository(Path(directory))
                candidate.consume()
                task_id = candidate.tasks[0]["task_id"]
                result = recorder.record_dispatch(
                    candidate.root,
                    task_id=task_id,
                    response_raw=raw,
                    captured_at_utc="2026-08-12T12:01:00Z",
                    **candidate.audit_kwargs(),
                )
                self.assertEqual(result["status"], "STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE")
                self.assertEqual(
                    (candidate.observations / task_id / recorder.RAW_RESPONSE_NAME).read_bytes(),
                    raw,
                )
                self.assertTrue(candidate.terminal_path.is_file())
        with tempfile.TemporaryDirectory() as directory:
            candidate = SyntheticGateARepository(Path(directory))
            candidate.consume()
            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = recorder.main(
                    [
                        "--record-terminal",
                        "--state",
                        "STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE",
                        "--failed-stage",
                        "create_thread_before_dispatch",
                        "--failure-class",
                        "INFRASTRUCTURE_FAILURE",
                        "--recorded-at-utc",
                        "2026-08-12T12:01:00Z",
                    ],
                    repo_root=candidate.root,
                    audit_kwargs=candidate.audit_kwargs(),
                )
            self.assertEqual(exit_code, 0)
            stopped = json.loads(output.getvalue())
            self.assertEqual(stopped["mode"], "RECORD_TERMINAL")
            self.assertEqual(stopped["status"], "STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE")
            self.assertEqual(stopped["attempts"], 0)
            self.assertEqual(stopped["retries"], 0)
            self.assertEqual(stopped["repairs"], 0)
            self.assertEqual(stopped["followups"], 0)
            self.assertTrue(candidate.terminal_path.is_file())
            self.assertEqual(
                recorder.next_action(candidate.root, **candidate.audit_kwargs())["action"],
                "STOP",
            )
        with tempfile.TemporaryDirectory() as directory:
            candidate = SyntheticGateARepository(Path(directory))
            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = recorder.main(
                    [
                        "--record-terminal",
                        "--state",
                        "UNAUTHORIZED_TERMINAL",
                        "--recorded-at-utc",
                        "2026-08-12T12:01:00Z",
                    ],
                    repo_root=candidate.root,
                    audit_kwargs=candidate.audit_kwargs(),
                )
            invalid = json.loads(output.getvalue())
            self.assertEqual(exit_code, 1)
            self.assertEqual(invalid["status"], "INVALID")
            self.assertEqual(invalid["writes"], 0)
            self.assertFalse(candidate.terminal_path.exists())

    def test_writer_refuses_preexisting_response_attestation_receipt_and_final(self) -> None:
        for name in (
            recorder.RAW_RESPONSE_NAME,
            recorder.RESPONSE_ATTESTATION_NAME,
            recorder.RECEIPT_NAME,
        ):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                candidate = SyntheticGateARepository(Path(directory))
                candidate.consume()
                task_id = candidate.tasks[0]["task_id"]
                target = (
                    candidate.results / task_id / name
                    if name == recorder.RECEIPT_NAME
                    else candidate.observations / task_id / name
                )
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(b"preserve")
                result = recorder.record_dispatch(
                    candidate.root,
                    task_id=task_id,
                    response_raw=candidate.response_raw(0),
                    captured_at_utc="2026-08-12T12:01:00Z",
                    **candidate.audit_kwargs(),
                )
                self.assertEqual(result["status"], "INVALID")
                self.assertEqual(target.read_bytes(), b"preserve")
        self.repo.consume()
        task_id = self.repo.tasks[0]["task_id"]
        recorder.record_dispatch(
            self.repo.root,
            task_id=task_id,
            response_raw=self.repo.response_raw(0),
            captured_at_utc="2026-08-12T12:01:00Z",
            **self.repo.audit_kwargs(),
        )
        final_path = self.repo.results / task_id / recorder.RAW_FINAL_NAME
        final_path.write_bytes(b"preserve")
        result = recorder.record_final(
            self.repo.root,
            task_id=task_id,
            final_raw=self.repo.final_raw(0),
            observed_at_utc="2026-08-12T12:02:00Z",
            **self.repo.audit_kwargs(),
        )
        self.assertEqual(result["status"], "INVALID")
        self.assertEqual(final_path.read_bytes(), b"preserve")
        with tempfile.TemporaryDirectory() as directory:
            candidate = SyntheticGateARepository(Path(directory))
            candidate.consume()
            candidate.terminal_path.parent.mkdir(parents=True, exist_ok=True)
            candidate.terminal_path.write_bytes(b"preserve")
            result = recorder.record_terminal(
                candidate.root,
                state="STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE",
                failed_stage="synthetic_terminal_preexisting",
                failure_class="INFRASTRUCTURE_FAILURE",
                recorded_at_utc="2026-08-12T12:03:00Z",
                **candidate.audit_kwargs(),
            )
            self.assertEqual(result["status"], "TERMINAL_ALREADY_EXISTS")
            self.assertEqual(result["writes"], 0)
            self.assertEqual(candidate.terminal_path.read_bytes(), b"preserve")

    def test_terminal_tamper_fails_closed(self) -> None:
        self.repo.consume()
        task_id = self.repo.tasks[0]["task_id"]
        recorder.record_dispatch(
            self.repo.root,
            task_id=task_id,
            response_raw=self.repo.response_raw(0, checkout="0" * 40),
            captured_at_utc="2026-08-12T12:01:00Z",
            **self.repo.audit_kwargs(),
        )
        terminal = protocol.parse_json_object(self.repo.terminal_path.read_bytes())
        terminal["counts"]["retries"] = 1
        self.repo.terminal_path.write_bytes(protocol.json_bytes(terminal))
        result = protocol.audit_execution(self.repo.root, **self.repo.audit_kwargs())
        self.assertEqual(result["status"], "INVALID")
        self.assertIn("terminal_schema_invalid", result["errors"])


if __name__ == "__main__":
    unittest.main()
