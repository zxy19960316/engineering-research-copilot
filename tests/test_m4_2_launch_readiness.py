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
import audit_m4_2_launch_readiness as readiness  # noqa: E402
import build_m4_2_launch_claim as claim_builder  # noqa: E402
import record_m4_2_execution_evidence as recorder  # noqa: E402
from tests.test_m4_2_execution import SyntheticGateARepository  # noqa: E402


class M42LaunchReadinessTests(unittest.TestCase):
    maxDiff = None

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.repo = SyntheticGateARepository(Path(self.temp.name))

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _snapshot(self) -> dict[str, bytes | str]:
        result: dict[str, bytes | str] = {}
        for path in sorted(self.repo.root.rglob("*")):
            relative = path.relative_to(self.repo.root).as_posix()
            result[relative] = path.read_bytes() if path.is_file() else "<dir>"
        return result

    def _readiness(self) -> dict[str, object]:
        return readiness.audit_launch_readiness(
            self.repo.root,
            verify_git=False,
            enforce_frozen_hashes=False,
            enforce_exact_changed_paths=False,
            authorization_path=self.repo.authorization_path,
            control_path=self.repo.control_path,
            claim_path=self.repo.claim_path,
            observations_base=self.repo.observations,
            results_base=self.repo.results,
            terminal_path=self.repo.terminal_path,
            results_manifest_path=self.repo.results_manifest,
            m5_path=self.repo.m5,
        )

    def test_launch_readiness_is_green_repeatable_read_only_and_gate_b_closed(self) -> None:
        before = self._snapshot()
        first = self._readiness()
        second = self._readiness()
        self.assertEqual(first, second)
        self.assertEqual(first["status"], "READY_FOR_ATOMIC_CLAIM")
        self.assertEqual(first["errors"], [])
        self.assertEqual(first["authorization_audit"], "READY_UNCONSUMED")
        self.assertEqual(first["execution_audit"], "READY_UNCLAIMED")
        self.assertEqual(first["claim_builder_check"], "READY_TO_CONSUME")
        self.assertEqual(first["recorder_check"], "READY_UNCLAIMED")
        self.assertEqual(first["writer_check"], "DETERMINISTIC_CHECK_ONLY")
        self.assertEqual(first["prompt_check"], "60_DETERMINISTIC_ISOLATED_REQUESTS")
        self.assertEqual(first["token"], "UNCONSUMED")
        self.assertEqual(first["launch_claim"], "ABSENT")
        self.assertEqual(first["result_root"], "ABSENT")
        self.assertEqual(first["terminal"], "ABSENT")
        self.assertIs(first["later_gates_authorized"], False)
        self.assertIs(first["gate_b_authorized"], False)
        self.assertEqual(first["writes"], 0)
        self.assertEqual(self._snapshot(), before)

    def test_schema_drift_fails_closed_without_writing(self) -> None:
        path = self.repo.root / protocol.LAUNCH_SCHEMA_RELATIVE
        schema = protocol.parse_json_object(path.read_bytes())
        schema["additionalProperties"] = True
        path.write_bytes(protocol.json_bytes(schema))
        before = self._snapshot()
        result = self._readiness()
        self.assertEqual(result["status"], "INVALID")
        self.assertTrue(
            any("schema_not_recursively_closed" in code for code in result["errors"])
        )
        self.assertEqual(self._snapshot(), before)

    def test_any_real_lifecycle_path_blocks_gate_a(self) -> None:
        targets = (
            self.repo.claim_path,
            self.repo.observations,
            self.repo.results,
            self.repo.terminal_path,
            self.repo.results_manifest,
            self.repo.m5,
        )
        for target in targets:
            with self.subTest(target=target.relative_to(self.repo.root).as_posix()):
                with tempfile.TemporaryDirectory() as directory:
                    candidate = SyntheticGateARepository(Path(directory))
                    mapped = candidate.root / target.relative_to(self.repo.root)
                    if target.suffix:
                        mapped.parent.mkdir(parents=True, exist_ok=True)
                        mapped.write_bytes(b"present")
                    else:
                        mapped.mkdir(parents=True)
                    result = readiness.audit_launch_readiness(
                        candidate.root,
                        verify_git=False,
                        enforce_frozen_hashes=False,
                        enforce_exact_changed_paths=False,
                        authorization_path=candidate.authorization_path,
                        control_path=candidate.control_path,
                        claim_path=candidate.claim_path,
                        observations_base=candidate.observations,
                        results_base=candidate.results,
                        terminal_path=candidate.terminal_path,
                        results_manifest_path=candidate.results_manifest,
                        m5_path=candidate.m5,
                    )
                    self.assertEqual(result["status"], "INVALID")

    def test_gate_a_baseline_is_the_exact_accepted_static_admission_repair(self) -> None:
        self.assertEqual(
            protocol.GATE_A_BASELINE_HEAD,
            "214acacfb984b3f9e41d35dde8841a4ffb342b34",
        )
        self.assertEqual(
            protocol.GATE_A_BASELINE_TREE,
            "7671e69844ea59a84411b6bcbfb9abf0feb64ae9",
        )

    def test_gate_a_allowlist_is_exact_and_contains_no_runtime_instance_path(self) -> None:
        expected = {
            "docs/superpowers/plans/2026-08-12-m4.2-one-shot-claim-and-execution.md",
            "evals/m4/execution/m4.2/launch-claim.schema.json",
            "evals/m4/execution/m4.2/dispatch-receipt.schema.json",
            "evals/m4/execution/m4.2/create-thread-response-attestation.schema.json",
            "evals/m4/execution/m4.2/execution-terminal.schema.json",
            "evals/m4/execution/audit_m4_2.py",
            "evals/m4/execution/build_m4_2_launch_claim.py",
            "evals/m4/execution/record_m4_2_execution_evidence.py",
            "evals/m4/execution/audit_m4_2_launch_readiness.py",
            "tests/test_m4_2_execution.py",
            "tests/test_m4_2_launch_readiness.py",
            ".github/workflows/m1-validation.yml",
            "STATUS.md",
            "tests/test_m3_r5_erratum.py",
        }
        self.assertEqual(set(protocol.GATE_A_ALLOWED_PATHS), expected)
        forbidden = {
            protocol.CLAIM_RELATIVE.as_posix(),
            protocol.TERMINAL_RELATIVE.as_posix(),
            protocol.RESULTS_BASE_RELATIVE.as_posix(),
            protocol.RESULTS_MANIFEST_RELATIVE.as_posix(),
            protocol.M5_RELATIVE.as_posix(),
        }
        self.assertTrue(expected.isdisjoint(forbidden))

    def test_claim_builder_default_check_is_zero_write(self) -> None:
        before = self._snapshot()
        result = claim_builder.check_claim_readiness(
            self.repo.root,
            verify_git=False,
            enforce_frozen_hashes=False,
            authorization_path=self.repo.authorization_path,
            control_path=self.repo.control_path,
            claim_path=self.repo.claim_path,
            observations_base=self.repo.observations,
            results_base=self.repo.results,
            terminal_path=self.repo.terminal_path,
            results_manifest_path=self.repo.results_manifest,
            m5_path=self.repo.m5,
        )
        self.assertEqual(result["status"], "READY_TO_CONSUME")
        self.assertEqual(result["mode"], "CHECK_ONLY")
        self.assertEqual(result["writes"], 0)
        self.assertEqual(self._snapshot(), before)

    def test_recorder_default_check_is_zero_write(self) -> None:
        before = self._snapshot()
        result = recorder.check_recorder(
            self.repo.root,
            verify_git=False,
            enforce_frozen_hashes=False,
            authorization_path=self.repo.authorization_path,
            control_path=self.repo.control_path,
            claim_path=self.repo.claim_path,
            observations_base=self.repo.observations,
            results_base=self.repo.results,
            terminal_path=self.repo.terminal_path,
            results_manifest_path=self.repo.results_manifest,
            m5_path=self.repo.m5,
        )
        self.assertEqual(result["status"], "READY_UNCLAIMED")
        self.assertEqual(result["mode"], "CHECK_ONLY")
        self.assertEqual(result["writes"], 0)
        self.assertEqual(self._snapshot(), before)

    def test_gate_a_acceptance_requires_exact_green_identity_and_decision(self) -> None:
        mutations = (
            claim_builder.GateAAcceptance("x", "2" * 40, 1, 2),
            claim_builder.GateAAcceptance("1" * 40, "x", 1, 2),
            claim_builder.GateAAcceptance("1" * 40, "2" * 40, 0, 2),
            claim_builder.GateAAcceptance("1" * 40, "2" * 40, 1, 0),
            claim_builder.GateAAcceptance(
                "1" * 40, "2" * 40, 1, 2, decision="NOT_APPROVED"
            ),
        )
        for value in mutations:
            with self.subTest(value=value):
                self.assertTrue(claim_builder.validate_gate_a_acceptance(value))
        self.assertEqual(
            claim_builder.validate_gate_a_acceptance(self.repo.gate_a), []
        )

    def test_valid_and_invalid_response_attestations_bind_raw_bytes(self) -> None:
        valid_raw = self.repo.response_raw(0)
        response, valid = recorder.attest_create_thread_response(
            valid_raw,
            task_id=self.repo.tasks[0]["task_id"],
            captured_at_utc="2026-08-12T12:01:00Z",
        )
        self.assertEqual(valid["status"], "VALID")
        self.assertTrue(response["ready"])
        self.assertEqual(valid["raw_response_sha256"], protocol.sha256(valid_raw))
        invalid_raw = b'{"clientThreadId":"setup-only"}'
        response, invalid = recorder.attest_create_thread_response(
            invalid_raw,
            task_id=self.repo.tasks[0]["task_id"],
            captured_at_utc="2026-08-12T12:01:00Z",
        )
        self.assertEqual(invalid["status"], "INVALID")
        self.assertFalse(response["ready"])
        self.assertIn("ready_thread_id_missing", invalid["errors"])
        self.assertIn("ready_host_id_missing", invalid["errors"])
        self.assertEqual(invalid["raw_response_sha256"], protocol.sha256(invalid_raw))

    def test_preclaim_authorization_auditor_is_not_a_postclaim_success_gate(self) -> None:
        source = Path(claim_builder.__file__).read_text(encoding="utf-8")
        self.assertNotIn("audit_m4_2_authorization", source)
        self.assertIn("post-claim execution auditor", source)
        self.repo.consume()
        state = protocol.audit_execution(self.repo.root, **self.repo.audit_kwargs())
        self.assertEqual(state["authorization_audit_status"], "CONSUMED_BY_CLAIM")
        self.assertEqual(state["status"], "CLAIMED_IN_PROGRESS")

    def test_cli_format_is_compact_closed_json_for_check_helpers(self) -> None:
        for value in (
            claim_builder.check_claim_readiness(
                self.repo.root,
                verify_git=False,
                enforce_frozen_hashes=False,
                authorization_path=self.repo.authorization_path,
                control_path=self.repo.control_path,
                claim_path=self.repo.claim_path,
                observations_base=self.repo.observations,
                results_base=self.repo.results,
                terminal_path=self.repo.terminal_path,
                results_manifest_path=self.repo.results_manifest,
                m5_path=self.repo.m5,
            ),
            recorder.check_recorder(
                self.repo.root,
                verify_git=False,
                enforce_frozen_hashes=False,
                authorization_path=self.repo.authorization_path,
                control_path=self.repo.control_path,
                claim_path=self.repo.claim_path,
                observations_base=self.repo.observations,
                results_base=self.repo.results,
                terminal_path=self.repo.terminal_path,
                results_manifest_path=self.repo.results_manifest,
                m5_path=self.repo.m5,
            ),
        ):
            rendered = json.dumps(value, sort_keys=True, separators=(",", ":"))
            self.assertEqual(json.loads(rendered), value)
            self.assertNotIn("\n", rendered)
            self.assertNotIn("sha256:" + "a" * 64, rendered)


if __name__ == "__main__":
    unittest.main()
