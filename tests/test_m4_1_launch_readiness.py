from __future__ import annotations

import contextlib
import copy
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
EXECUTION_ROOT = REPO_ROOT / "evals" / "m4" / "execution"
sys.path.insert(0, str(EXECUTION_ROOT))

import audit_m4_1 as protocol  # noqa: E402
import audit_m4_1_launch_readiness as readiness  # noqa: E402
import build_m4_1_launch_claim as claim  # noqa: E402
import record_m4_1_execution_evidence as recorder  # noqa: E402


class M41LaunchReadinessTests(unittest.TestCase):
    maxDiff = None

    def _fixture_paths(self, root: Path) -> dict[str, Path]:
        return {
            "claim": root / "launch-claim.json",
            "results": root / "results" / "m4.1",
            "terminal": root / "execution-terminal.json",
            "manifest": root / "results-manifest.json",
            "observations": root / "platform-observations",
        }

    def _claim_fixture(
        self, root: Path
    ) -> tuple[dict[str, Path], dict[str, object]]:
        paths = self._fixture_paths(root)
        value = claim.build_claim(
            REPO_ROOT, claimed_at_utc="2026-08-08T13:00:00Z"
        )
        claim.exclusive_create_json(paths["claim"], value)
        return paths, value

    def _tasks(self) -> list[dict[str, object]]:
        control = protocol.parse_json_object(protocol.CONTROL_PATH.read_bytes())
        return protocol.ordered_tasks(control)

    def _response_raw(self, index: int) -> bytes:
        return protocol.canonical_bytes(
            {
                "threadId": f"thread-{index + 1:03d}",
                "hostId": "local",
                "resolvedCheckoutSha": readiness.AUTHORIZATION_HEAD,
            }
        ) + b"\n"

    def _valid_final(
        self,
        claim_value: dict[str, object],
        tasks: list[dict[str, object]],
        index: int,
        *,
        response: str = "protocol-valid evaluation response",
    ) -> bytes:
        task_claim = claim_value["task_claims"][index]
        task = tasks[index]
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
        return protocol.canonical_bytes(value) + b"\n"

    def _write_complete_fixture(
        self, root: Path
    ) -> tuple[dict[str, Path], dict[str, object]]:
        paths, claim_value = self._claim_fixture(root)
        tasks = self._tasks()
        claim_raw = paths["claim"].read_bytes()
        paths["results"].mkdir(parents=True)
        paths["observations"].mkdir()
        for index, task in enumerate(tasks):
            task_id = str(task["task_id"])
            result_task = paths["results"] / task_id
            observation_task = paths["observations"] / task_id
            result_task.mkdir()
            observation_task.mkdir()
            response_raw = self._response_raw(index)
            response, response_attestation = recorder.attest_create_thread_response(
                response_raw,
                task_id=task_id,
                captured_at_utc="2026-08-08T13:01:00Z",
            )
            receipt = recorder._receipt(
                claim=claim_value,
                claim_raw=claim_raw,
                tasks=tasks,
                task_claim=claim_value["task_claims"][index],
                index=index,
                response=response,
                created_at_utc="2026-08-08T13:01:00Z",
            )
            final_raw = self._valid_final(claim_value, tasks, index)
            (observation_task / recorder.RAW_RESPONSE_NAME).write_bytes(response_raw)
            (observation_task / recorder.RESPONSE_ATTESTATION_NAME).write_bytes(
                protocol.canonical_bytes(response_attestation) + b"\n"
            )
            (result_task / recorder.RECEIPT_NAME).write_bytes(
                protocol.canonical_bytes(receipt) + b"\n"
            )
            (result_task / recorder.RAW_FINAL_NAME).write_bytes(final_raw)
            final_attestation = {
                "schema_version": "m4.1-raw-final-attestation-v1",
                "milestone": "M4",
                "revision": "M4.1",
                "task_id": task_id,
                "raw_final_path": (
                    f"evals/m4/results/m4.1/{task_id}/{recorder.RAW_FINAL_NAME}"
                ),
                "byte_length": len(final_raw),
                "raw_sha256": protocol.sha256(final_raw),
                "observed_at_utc": "2026-08-08T13:02:00Z",
                "protocol_validation": "VALID",
                "protocol_errors": [],
            }
            (observation_task / recorder.FINAL_ATTESTATION_NAME).write_bytes(
                protocol.canonical_bytes(final_attestation) + b"\n"
            )
        return paths, claim_value

    def _repository_execution_snapshot(self) -> dict[str, bytes | None]:
        paths = (
            REPO_ROOT / protocol.CLAIM_RELATIVE,
            REPO_ROOT / protocol.TERMINAL_RELATIVE,
            REPO_ROOT / protocol.RESULTS_BASE_RELATIVE,
            REPO_ROOT / protocol.RESULTS_MANIFEST_RELATIVE,
            REPO_ROOT / recorder.PLATFORM_OBSERVATIONS_RELATIVE,
        )
        result: dict[str, bytes | None] = {}
        for path in paths:
            relative = path.relative_to(REPO_ROOT).as_posix()
            if path.is_file():
                result[relative] = path.read_bytes()
            elif path.exists():
                result[relative] = b"<directory-present>"
            else:
                result[relative] = None
        return result

    def test_review_binds_exact_green_inputs_and_closes_later_gates(self) -> None:
        review = protocol.parse_json_object(readiness.REVIEW_PATH.read_bytes())
        self.assertEqual(set(review), readiness.REVIEW_KEYS)
        self.assertEqual(review["decision"], "PASSED")
        self.assertEqual(review["findings"], [])
        self.assertEqual(review["authorization"]["head"], readiness.AUTHORIZATION_HEAD)
        self.assertEqual(review["authorization"]["ci_run_id"], 31251141941)
        self.assertEqual(review["authorization"]["token_status"], "UNCONSUMED")
        self.assertEqual(review["protocol"]["head"], readiness.PROTOCOL_HEAD)
        self.assertEqual(review["protocol"]["ci_run_id"], 31255966197)
        self.assertEqual(
            [item["job_id"] for item in review["protocol"]["jobs"]],
            [93099235968, 93099235987, 93099235994],
        )
        self.assertEqual(
            review["request_binding_aggregate"]["sha256"],
            readiness.REQUEST_AGGREGATE,
        )
        self.assertFalse(review["branch_immutability"]["authorization_branch_protected"])
        self.assertEqual(review["branch_immutability"]["active_repository_rulesets"], 0)
        self.assertEqual(
            review["branch_immutability"]["mechanism"],
            "immutable-start-equivalent-v1",
        )
        self.assertTrue(
            review["branch_immutability"]["pre_consume_remote_ref_recheck_required"]
        )
        self.assertEqual(
            review["branch_immutability"]["resolved_checkout_sha_policy"],
            "require_exact_if_exposed",
        )
        self.assertEqual(
            review["does_not_authorize"], list(readiness.DOES_NOT_AUTHORIZE)
        )

    def test_writer_defaults_are_check_only_and_deterministic(self) -> None:
        before = self._repository_execution_snapshot()
        first = claim.check_claim_readiness(REPO_ROOT)
        self.assertEqual(first["status"], "READY_TO_CONSUME")
        self.assertEqual(first["mode"], "CHECK_ONLY")
        self.assertEqual(first["token"], "UNCONSUMED")
        self.assertEqual(first["claim"], "ABSENT")
        self.assertEqual(recorder.check_recorder(REPO_ROOT)["status"], "READY_UNCLAIMED")
        first_template = claim.build_claim(
            REPO_ROOT, claimed_at_utc="2000-01-01T00:00:00Z"
        )
        second_template = claim.build_claim(
            REPO_ROOT, claimed_at_utc="2000-01-01T00:00:00Z"
        )
        self.assertEqual(
            protocol.canonical_bytes(first_template),
            protocol.canonical_bytes(second_template),
        )
        for module in (claim, recorder):
            stream = io.StringIO()
            with contextlib.redirect_stdout(stream):
                self.assertEqual(module.main([]), 0)
            value = json.loads(stream.getvalue())
            self.assertIn(value["status"], {"READY_TO_CONSUME", "READY_UNCLAIMED"})
        self.assertEqual(before, self._repository_execution_snapshot())

    def test_claim_builds_the_exact_gate_iv_a_contract(self) -> None:
        value = claim.build_claim(
            REPO_ROOT, claimed_at_utc="2026-08-08T13:00:00Z"
        )
        self.assertEqual(value["execution_protocol"]["head"], readiness.PROTOCOL_HEAD)
        self.assertEqual(value["execution_protocol"]["ci_run_id"], 31255966197)
        self.assertEqual(len(value["task_claims"]), 60)
        self.assertEqual(len({item["context_id"] for item in value["task_claims"]}), 60)
        self.assertEqual(
            len({item["finalization_id"] for item in value["task_claims"]}), 60
        )
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            claim_path = root / "launch-claim.json"
            claim.exclusive_create_json(claim_path, value)
            result = protocol.audit_execution(
                REPO_ROOT,
                claim_path=claim_path,
                results_base=root / "results" / "m4.1",
                terminal_path=root / "execution-terminal.json",
                results_manifest_path=root / "results-manifest.json",
                verify_git=False,
            )
        self.assertEqual(result["status"], "CLAIMED_IN_PROGRESS")
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["tasks"], 0)
        self.assertEqual(result["finalizations"], 0)

    def test_exclusive_claim_refuses_every_existing_target(self) -> None:
        value = claim.build_claim(
            REPO_ROOT, claimed_at_utc="2026-08-08T13:00:00Z"
        )
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            target = Path(temp_dir) / "launch-claim.json"
            target.write_bytes(b"preserve-me")
            with self.assertRaises(FileExistsError):
                claim.exclusive_create_json(target, value)
            self.assertEqual(target.read_bytes(), b"preserve-me")

    def test_atomic_claim_consumption_gets_both_required_confirmations(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            paths = self._fixture_paths(root)
            result = claim.consume_claim(
                REPO_ROOT,
                claimed_at_utc="2026-08-08T13:00:00Z",
                claim_path=paths["claim"],
                results_base=paths["results"],
                terminal_path=paths["terminal"],
                results_manifest_path=paths["manifest"],
                observations_base=paths["observations"],
                verify_git=False,
                verify_live=False,
            )
            self.assertEqual(result["status"], "CLAIMED_IN_PROGRESS")
            self.assertEqual(
                result["authorization_auditor"], "authorization_already_claimed"
            )
            self.assertEqual(result["execution_auditor"], "CLAIMED_IN_PROGRESS")
            self.assertEqual(result["tasks"], 0)
            self.assertEqual(result["finalizations"], 0)
            first_raw = paths["claim"].read_bytes()
            second = claim.consume_claim(
                REPO_ROOT,
                claimed_at_utc="2026-08-08T13:00:01Z",
                claim_path=paths["claim"],
                results_base=paths["results"],
                terminal_path=paths["terminal"],
                results_manifest_path=paths["manifest"],
                observations_base=paths["observations"],
                verify_git=False,
                verify_live=False,
            )
            self.assertEqual(second["status"], "ALREADY_CLAIMED")
            self.assertEqual(paths["claim"].read_bytes(), first_raw)

    def test_post_claim_confirmation_failure_creates_unique_stopped_terminal(self) -> None:
        original_audit = claim.authorization_audit.audit_authorization
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            paths = self._fixture_paths(root)

            def controlled_audit(*args, **kwargs):
                launch_path = kwargs.get("launch_claim_path")
                if launch_path == paths["claim"] and paths["claim"].is_file():
                    return {"status": "INVALID", "errors": []}
                return original_audit(*args, **kwargs)

            with mock.patch.object(
                claim.authorization_audit,
                "audit_authorization",
                side_effect=controlled_audit,
            ):
                result = claim.consume_claim(
                    REPO_ROOT,
                    claimed_at_utc="2026-08-08T13:00:00Z",
                    claim_path=paths["claim"],
                    results_base=paths["results"],
                    terminal_path=paths["terminal"],
                    results_manifest_path=paths["manifest"],
                    observations_base=paths["observations"],
                    verify_git=False,
                    verify_live=False,
                )
            self.assertEqual(
                result["status"], "STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE"
            )
            self.assertTrue(paths["claim"].is_file())
            self.assertTrue(paths["terminal"].is_file())
            claim_raw = paths["claim"].read_bytes()
            terminal_raw = paths["terminal"].read_bytes()
            repeated = claim.consume_claim(
                REPO_ROOT,
                claimed_at_utc="2026-08-08T13:00:01Z",
                claim_path=paths["claim"],
                results_base=paths["results"],
                terminal_path=paths["terminal"],
                results_manifest_path=paths["manifest"],
                observations_base=paths["observations"],
                verify_git=False,
                verify_live=False,
            )
            self.assertEqual(repeated["status"], "ALREADY_CLAIMED")
            self.assertEqual(paths["claim"].read_bytes(), claim_raw)
            self.assertEqual(paths["terminal"].read_bytes(), terminal_raw)

    def test_any_preexisting_launch_target_fails_without_replacement(self) -> None:
        labels = ("claim", "terminal", "results", "manifest", "observations")
        for label in labels:
            with self.subTest(label=label), tempfile.TemporaryDirectory(
                dir=REPO_ROOT
            ) as temp_dir:
                root = Path(temp_dir)
                paths = self._fixture_paths(root)
                target = paths[label]
                if label in {"results", "observations"}:
                    target.mkdir(parents=True)
                    marker = target / "marker"
                    marker.write_bytes(b"preserve")
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(b"preserve")
                    marker = target
                before = marker.read_bytes()
                result = claim.check_claim_readiness(
                    REPO_ROOT,
                    claim_path=paths["claim"],
                    results_base=paths["results"],
                    terminal_path=paths["terminal"],
                    results_manifest_path=paths["manifest"],
                    observations_base=paths["observations"],
                    verify_git=False,
                )
                self.assertEqual(result["status"], "INVALID")
                self.assertEqual(marker.read_bytes(), before)

    def test_response_attestation_preserves_hashes_and_validates_checkout(self) -> None:
        raw = (
            b'{"hostId":"local","resolvedCheckoutSha":"'
            + readiness.AUTHORIZATION_HEAD.encode("ascii")
            + b'","threadId":"thread-1"}'
        )
        response, attestation = recorder.attest_create_thread_response(
            raw,
            task_id="M4-T061",
            captured_at_utc="2026-08-08T13:01:00Z",
        )
        self.assertEqual(response["thread_id"], "thread-1")
        self.assertEqual(response["host_id"], "local")
        self.assertTrue(attestation["resolved_checkout_sha_exposed"])
        self.assertEqual(attestation["resolved_checkout_sha"], readiness.AUTHORIZATION_HEAD)
        self.assertTrue(attestation["checkout_sha_validated"])
        self.assertEqual(attestation["raw_response_sha256"], protocol.sha256(raw))
        self.assertEqual(
            attestation["canonical_response_sha256"],
            protocol.canonical_sha256(protocol.parse_json_object(raw)),
        )

    def test_response_attestation_rejects_checkout_mismatch(self) -> None:
        raw = b'{"hostId":"local","resolvedCheckoutSha":"0000000000000000000000000000000000000000","threadId":"thread-1"}'
        with self.assertRaisesRegex(ValueError, "resolved_checkout_sha_mismatch"):
            recorder.attest_create_thread_response(
                raw,
                task_id="M4-T061",
                captured_at_utc="2026-08-08T13:01:00Z",
            )

    def test_dispatch_and_raw_final_are_exclusive_and_prefix_ordered(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            paths, claim_value = self._claim_fixture(root)
            tasks = self._tasks()
            first_task_id = str(tasks[0]["task_id"])
            response_raw = self._response_raw(0)
            dispatched = recorder.record_dispatch(
                REPO_ROOT,
                task_id=first_task_id,
                response_raw=response_raw,
                captured_at_utc="2026-08-08T13:01:00Z",
                claim_path=paths["claim"],
                results_base=paths["results"],
                terminal_path=paths["terminal"],
                results_manifest_path=paths["manifest"],
                observations_base=paths["observations"],
                verify_git=False,
            )
            self.assertEqual(dispatched["status"], "CLAIMED_IN_PROGRESS")
            self.assertEqual(dispatched["tasks"], 1)
            self.assertEqual(dispatched["finalizations"], 0)
            observation_task = paths["observations"] / first_task_id
            self.assertEqual(
                (observation_task / recorder.RAW_RESPONSE_NAME).read_bytes(),
                response_raw,
            )
            final_raw = self._valid_final(
                claim_value,
                tasks,
                0,
                response="poor quality but protocol-valid and therefore retained",
            )
            finalized = recorder.record_final(
                REPO_ROOT,
                task_id=first_task_id,
                final_raw=final_raw,
                observed_at_utc="2026-08-08T13:02:00Z",
                claim_path=paths["claim"],
                results_base=paths["results"],
                terminal_path=paths["terminal"],
                results_manifest_path=paths["manifest"],
                observations_base=paths["observations"],
                verify_git=False,
            )
            self.assertEqual(finalized["status"], "PROTOCOL_VALID_CONTINUE")
            final_path = paths["results"] / first_task_id / recorder.RAW_FINAL_NAME
            self.assertEqual(final_path.read_bytes(), final_raw)
            repeated = recorder.record_final(
                REPO_ROOT,
                task_id=first_task_id,
                final_raw=b"replacement forbidden",
                observed_at_utc="2026-08-08T13:03:00Z",
                claim_path=paths["claim"],
                results_base=paths["results"],
                terminal_path=paths["terminal"],
                results_manifest_path=paths["manifest"],
                observations_base=paths["observations"],
                verify_git=False,
            )
            self.assertEqual(repeated["status"], "INVALID")
            self.assertEqual(final_path.read_bytes(), final_raw)
            self.assertFalse(paths["manifest"].exists())

    def test_invalid_raw_final_is_preserved_and_stops_without_resume(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            paths, _ = self._claim_fixture(root)
            tasks = self._tasks()
            first_task_id = str(tasks[0]["task_id"])
            recorder.record_dispatch(
                REPO_ROOT,
                task_id=first_task_id,
                response_raw=self._response_raw(0),
                captured_at_utc="2026-08-08T13:01:00Z",
                claim_path=paths["claim"],
                results_base=paths["results"],
                terminal_path=paths["terminal"],
                results_manifest_path=paths["manifest"],
                observations_base=paths["observations"],
                verify_git=False,
            )
            raw = b"not-json and never repaired"
            stopped = recorder.record_final(
                REPO_ROOT,
                task_id=first_task_id,
                final_raw=raw,
                observed_at_utc="2026-08-08T13:02:00Z",
                claim_path=paths["claim"],
                results_base=paths["results"],
                terminal_path=paths["terminal"],
                results_manifest_path=paths["manifest"],
                observations_base=paths["observations"],
                verify_git=False,
            )
            self.assertEqual(
                stopped["status"], "STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE"
            )
            raw_path = paths["results"] / first_task_id / recorder.RAW_FINAL_NAME
            self.assertEqual(raw_path.read_bytes(), raw)
            terminal_raw = paths["terminal"].read_bytes()
            resume = recorder.record_dispatch(
                REPO_ROOT,
                task_id=str(tasks[1]["task_id"]),
                response_raw=self._response_raw(1),
                captured_at_utc="2026-08-08T13:03:00Z",
                claim_path=paths["claim"],
                results_base=paths["results"],
                terminal_path=paths["terminal"],
                results_manifest_path=paths["manifest"],
                observations_base=paths["observations"],
                verify_git=False,
            )
            self.assertEqual(resume["status"], "INVALID")
            self.assertEqual(paths["terminal"].read_bytes(), terminal_raw)
            self.assertEqual(raw_path.read_bytes(), raw)

    def test_checkout_mismatch_preserves_raw_response_and_stops(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            paths, _ = self._claim_fixture(root)
            task_id = str(self._tasks()[0]["task_id"])
            raw = b'{"hostId":"local","resolvedCheckoutSha":"0000000000000000000000000000000000000000","threadId":"thread-1"}'
            stopped = recorder.record_dispatch(
                REPO_ROOT,
                task_id=task_id,
                response_raw=raw,
                captured_at_utc="2026-08-08T13:01:00Z",
                claim_path=paths["claim"],
                results_base=paths["results"],
                terminal_path=paths["terminal"],
                results_manifest_path=paths["manifest"],
                observations_base=paths["observations"],
                verify_git=False,
            )
            self.assertEqual(
                stopped["status"], "STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE"
            )
            self.assertEqual(
                (paths["observations"] / task_id / recorder.RAW_RESPONSE_NAME).read_bytes(),
                raw,
            )
            self.assertFalse(paths["results"].exists())
            self.assertTrue(paths["terminal"].is_file())

    def test_untrusted_task_id_cannot_escape_or_create_any_target(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            paths, _ = self._claim_fixture(root)
            before = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))
            result = recorder.record_dispatch(
                REPO_ROOT,
                task_id="..\\escape",
                response_raw=self._response_raw(0),
                captured_at_utc="2026-08-08T13:01:00Z",
                claim_path=paths["claim"],
                results_base=paths["results"],
                terminal_path=paths["terminal"],
                results_manifest_path=paths["manifest"],
                observations_base=paths["observations"],
                verify_git=False,
            )
            self.assertEqual(result["status"], "INVALID")
            self.assertEqual(result["errors"], ["dispatch_not_next_frozen_task"])
            after = sorted(path.relative_to(root).as_posix() for path in root.rglob("*"))
            self.assertEqual(after, before)

    def test_writer_sources_have_no_overwrite_delete_or_rollback_primitive(self) -> None:
        sources = {
            "claim": Path(claim.__file__).read_text(encoding="utf-8"),
            "recorder": Path(recorder.__file__).read_text(encoding="utf-8"),
        }
        for name, source in sources.items():
            with self.subTest(name=name):
                self.assertNotIn("os.replace", source)
                self.assertNotIn("os.remove", source)
                self.assertNotIn(".unlink(", source)
                self.assertNotIn("rmtree(", source)
        self.assertIn("os.O_EXCL", sources["claim"])
        self.assertIn("exclusive_create_json", sources["recorder"])

    def test_coordinator_exception_goes_directly_to_terminal(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            paths, _ = self._claim_fixture(root)
            task_id = str(self._tasks()[0]["task_id"])
            raw_error = b"coordinator exception bytes"
            stopped = recorder.record_terminal(
                REPO_ROOT,
                state="STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE",
                recorded_at_utc="2026-08-08T13:01:00Z",
                failed_task_id=task_id,
                failed_stage="coordinator_exception",
                failure_class="INFRASTRUCTURE_FAILURE",
                failure_evidence_raw=raw_error,
                attempt_included=False,
                claim_path=paths["claim"],
                results_base=paths["results"],
                terminal_path=paths["terminal"],
                results_manifest_path=paths["manifest"],
                observations_base=paths["observations"],
                verify_git=False,
            )
            self.assertEqual(
                stopped["status"], "STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE"
            )
            original = paths["terminal"].read_bytes()
            repeated = recorder.record_terminal(
                REPO_ROOT,
                state="STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE",
                recorded_at_utc="2026-08-08T13:02:00Z",
                failed_task_id=task_id,
                failed_stage="coordinator_exception",
                failure_class="INFRASTRUCTURE_FAILURE",
                failure_evidence_raw=b"retry forbidden",
                claim_path=paths["claim"],
                results_base=paths["results"],
                terminal_path=paths["terminal"],
                results_manifest_path=paths["manifest"],
                observations_base=paths["observations"],
                verify_git=False,
            )
            self.assertEqual(repeated["status"], "TERMINAL_ALREADY_EXISTS")
            self.assertEqual(paths["terminal"].read_bytes(), original)

    def test_complete_writer_terminal_is_complete_unjudged_only(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            paths, _ = self._write_complete_fixture(root)
            result = recorder.record_terminal(
                REPO_ROOT,
                state="COMPLETE_UNJUDGED",
                recorded_at_utc="2026-08-08T13:30:00Z",
                claim_path=paths["claim"],
                results_base=paths["results"],
                terminal_path=paths["terminal"],
                results_manifest_path=paths["manifest"],
                observations_base=paths["observations"],
                verify_git=False,
            )
            self.assertEqual(result["status"], "COMPLETE_UNJUDGED")
            self.assertEqual(result["tasks"], 60)
            self.assertEqual(result["threads"], 60)
            self.assertEqual(result["finalizations"], 60)
            self.assertEqual(result["results"], 60)
            self.assertEqual(result["retries"], 0)
            self.assertEqual(result["repairs"], 0)
            self.assertEqual(result["followups"], 0)
            self.assertFalse(paths["manifest"].exists())

    def test_launch_readiness_audit_is_green_and_read_only(self) -> None:
        before = self._repository_execution_snapshot()
        result = readiness.audit_launch_readiness(REPO_ROOT)
        self.assertEqual(result["status"], "READY_FOR_ATOMIC_CLAIM")
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["protocol_review"], "PASSED")
        self.assertEqual(result["authorization_audit"], "READY_UNCONSUMED")
        self.assertEqual(result["execution_audit"], "READY_UNCLAIMED")
        self.assertEqual(result["writer_check"], "DETERMINISTIC")
        self.assertEqual(result["token"], "UNCONSUMED")
        self.assertEqual(result["launch_claim"], "ABSENT")
        self.assertEqual(result["result_root"], "ABSENT")
        self.assertEqual(before, self._repository_execution_snapshot())

    def test_review_mutations_fail_closed(self) -> None:
        source = protocol.parse_json_object(readiness.REVIEW_PATH.read_bytes())
        mutations = {
            "authorization_head": lambda value: value["authorization"].__setitem__(
                "head", "0" * 40
            ),
            "protocol_run": lambda value: value["protocol"].__setitem__(
                "ci_run_id", 1
            ),
            "request_aggregate": lambda value: value[
                "request_binding_aggregate"
            ].__setitem__("sha256", "0" * 64),
            "writer_default": lambda value: value["writer_contract"].__setitem__(
                "default_mode", "--consume"
            ),
            "immutability": lambda value: value["branch_immutability"].__setitem__(
                "pre_consume_remote_ref_recheck_required", False
            ),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                value = copy.deepcopy(source)
                mutate(value)
                self.assertTrue(claim.validate_review(value))


if __name__ == "__main__":
    unittest.main()
