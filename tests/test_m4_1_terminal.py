from __future__ import annotations

import base64
import copy
import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from evals.m4.execution import audit_m4_1 as protocol
from evals.m4.execution import audit_m4_1_terminal as terminal


REPO_ROOT = Path(__file__).resolve().parents[1]
CLAIM_PATH = REPO_ROOT / protocol.CLAIM_RELATIVE
TERMINAL_PATH = REPO_ROOT / protocol.TERMINAL_RELATIVE


def git_status() -> bytes:
    return subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all", "-z"],
        cwd=REPO_ROOT,
        capture_output=True,
        check=True,
    ).stdout


def write_json(path: Path, value: dict[str, object]) -> None:
    path.write_bytes(protocol.canonical_bytes(value) + b"\n")


class M41TerminalAuditTests(unittest.TestCase):
    @contextmanager
    def copied_evidence(self) -> Iterator[dict[str, Path]]:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            claim_path = root / "launch-claim.json"
            terminal_path = root / "execution-terminal.json"
            shutil.copyfile(CLAIM_PATH, claim_path)
            shutil.copyfile(TERMINAL_PATH, terminal_path)
            yield {
                "claim": claim_path,
                "terminal": terminal_path,
                "results": root / "results" / "m4.1",
                "manifest": root / "results-manifest.json",
                "observations": root / "platform-observations",
            }

    def audit_copy(self, paths: dict[str, Path]) -> dict[str, object]:
        return terminal.audit_terminal(
            REPO_ROOT,
            claim_path=paths["claim"],
            terminal_path=paths["terminal"],
            results_base=paths["results"],
            results_manifest_path=paths["manifest"],
            platform_observations_path=paths["observations"],
            verify_git=False,
        )

    def test_repository_terminal_is_preserved_read_only_and_repeatable(self) -> None:
        before_status = git_status()
        before_claim = CLAIM_PATH.read_bytes()
        before_terminal = TERMINAL_PATH.read_bytes()

        first = terminal.audit_terminal(REPO_ROOT)
        second = terminal.audit_terminal(REPO_ROOT)

        self.assertEqual(first, second)
        self.assertEqual(
            first,
            {
                "aggregation_calls": 0,
                "attempts": 0,
                "claim_count": 1,
                "claim_id": "32e0df57-a8d2-5c19-9ffc-da69997686e8",
                "claim_sha256": (
                    "c16a2e53aa2e9215e2325464d547356afdb73897bfc7d29605e0105b9987b3c6"
                ),
                "errors": [],
                "failed_stage": "post_claim_dual_confirmation",
                "finalizations": 0,
                "followups": 0,
                "judge_calls": 0,
                "repairs": 0,
                "result_root_count": 0,
                "results": 0,
                "retries": 0,
                "side_effects": 0,
                "status": "M4_1_STOPPED_PROTOCOL_FAILURE_PRESERVED",
                "successor_revision_required": True,
                "tasks": 0,
                "terminal_sha256": (
                    "7305d71ba94cd209f5bb0cb2c977db3bb157d95b907f8f59df9133c192f4d66e"
                ),
                "threads": 0,
                "token": "CONSUMED",
            },
        )
        self.assertEqual(before_status, git_status())
        self.assertEqual(before_claim, CLAIM_PATH.read_bytes())
        self.assertEqual(before_terminal, TERMINAL_PATH.read_bytes())

    def test_claim_and_terminal_mutations_fail_closed(self) -> None:
        mutations = {
            "claim_count": (
                "claim",
                lambda value: value.__setitem__("claim_count", 2),
                "claim_count_invalid",
            ),
            "claim_token": (
                "claim",
                lambda value: value["authorization"].__setitem__(
                    "token_status_after_claim", "UNCONSUMED"
                ),
                "claim_token_not_consumed",
            ),
            "terminal_state": (
                "terminal",
                lambda value: value.__setitem__("terminal_state", "COMPLETE_UNJUDGED"),
                "terminal_state_invalid",
            ),
            "failed_stage": (
                "terminal",
                lambda value: value.__setitem__("failed_stage", "not-run"),
                "failed_stage_invalid",
            ),
            "claim_binding": (
                "terminal",
                lambda value: value["launch_claim"].__setitem__("claim_id", "changed"),
                "terminal_claim_binding_invalid",
            ),
            "successor": (
                "terminal",
                lambda value: value.__setitem__("successor_revision_required", False),
                "successor_revision_not_required",
            ),
            "later_gate": (
                "terminal",
                lambda value: value["later_gates"].__setitem__("judge", "RUN"),
                "later_gates_invalid",
            ),
        }
        for name, (target, mutate, expected_error) in mutations.items():
            with self.subTest(name=name), self.copied_evidence() as paths:
                value = protocol.parse_json_object(paths[target].read_bytes())
                mutate(value)
                write_json(paths[target], value)
                result = self.audit_copy(paths)
                self.assertEqual(result["status"], "INVALID")
                self.assertIn(expected_error, result["errors"])

    def test_nonzero_counters_and_activity_arrays_fail_closed(self) -> None:
        for counter in (
            "tasks",
            "threads",
            "attempts",
            "finalizations",
            "results",
            "retries",
            "repairs",
            "followups",
            "judge_calls",
            "aggregation_calls",
            "side_effects",
        ):
            with self.subTest(counter=counter), self.copied_evidence() as paths:
                value = protocol.parse_json_object(paths["terminal"].read_bytes())
                value["counts"][counter] = 1
                write_json(paths["terminal"], value)
                result = self.audit_copy(paths)
                self.assertEqual(result["status"], "INVALID")
                self.assertIn(f"nonzero_counter:{counter}", result["errors"])

        for field in ("attempted_task_ids", "dispatch_receipts", "raw_finals"):
            with self.subTest(field=field), self.copied_evidence() as paths:
                value = protocol.parse_json_object(paths["terminal"].read_bytes())
                value[field] = [{"unexpected": True}] if field != "attempted_task_ids" else ["x"]
                write_json(paths["terminal"], value)
                result = self.audit_copy(paths)
                self.assertEqual(result["status"], "INVALID")
                self.assertIn(f"terminal_activity_present:{field}", result["errors"])

    def test_failure_evidence_must_decode_and_include_observed_protocol_error(self) -> None:
        with self.copied_evidence() as paths:
            value = protocol.parse_json_object(paths["terminal"].read_bytes())
            raw_evidence = "base64:***"
            value["failure_evidence"]["raw_evidence"] = raw_evidence
            value["failure_evidence"]["raw_evidence_sha256"] = hashlib.sha256(
                raw_evidence.encode("utf-8")
            ).hexdigest()
            write_json(paths["terminal"], value)
            result = self.audit_copy(paths)
            self.assertEqual(result["status"], "INVALID")
            self.assertIn("failure_evidence_base64_invalid", result["errors"])

        with self.copied_evidence() as paths:
            value = protocol.parse_json_object(paths["terminal"].read_bytes())
            evidence = value["failure_evidence"]
            decoded = base64.b64decode(evidence["raw_evidence"].removeprefix("base64:"))
            payload = json.loads(decoded.decode("utf-8"))
            payload["authorization_errors"].remove("authorization_already_claimed")
            encoded = base64.b64encode(protocol.canonical_bytes(payload)).decode("ascii")
            raw_evidence = f"base64:{encoded}"
            evidence["raw_evidence"] = raw_evidence
            evidence["raw_evidence_sha256"] = hashlib.sha256(
                raw_evidence.encode("utf-8")
            ).hexdigest()
            write_json(paths["terminal"], value)
            result = self.audit_copy(paths)
            self.assertEqual(result["status"], "INVALID")
            self.assertIn("authorization_already_claimed_missing", result["errors"])

    def test_result_dispatch_final_manifest_and_observation_paths_must_be_absent(self) -> None:
        with self.copied_evidence() as paths:
            receipt = paths["results"] / "M4.1-NUC-A-F" / "dispatch-receipt.json"
            receipt.parent.mkdir(parents=True)
            receipt.write_text("{}\n", encoding="utf-8")
            (receipt.parent / "raw-final.txt").write_text("unexpected", encoding="utf-8")
            paths["manifest"].write_text("{}\n", encoding="utf-8")
            paths["observations"].mkdir()

            result = self.audit_copy(paths)

            self.assertEqual(result["status"], "INVALID")
            self.assertIn("result_root_present", result["errors"])
            self.assertIn("dispatch_receipt_present", result["errors"])
            self.assertIn("raw_final_present", result["errors"])
            self.assertIn("results_manifest_present", result["errors"])
            self.assertIn("platform_observations_present", result["errors"])

    def test_schema_shape_is_validated_by_frozen_protocol(self) -> None:
        with self.copied_evidence() as paths:
            value = protocol.parse_json_object(paths["terminal"].read_bytes())
            del value["permissions_still_closed"]
            write_json(paths["terminal"], value)
            result = self.audit_copy(paths)
            self.assertEqual(result["status"], "INVALID")
            self.assertIn("protocol:terminal_fields_invalid", result["errors"])


if __name__ == "__main__":
    unittest.main()
