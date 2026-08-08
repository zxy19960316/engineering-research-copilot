from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from evals.m4.execution import audit_m4_0 as execution_audit
from evals.m4.execution.audit_m4_0 import audit_execution


REPO_ROOT = Path(__file__).resolve().parents[1]
EXECUTION_ROOT = REPO_ROOT / "evals" / "m4" / "execution" / "m4.0"
CLAIM_PATH = EXECUTION_ROOT / "launch-claim.json"
FAILURE_PATH = EXECUTION_ROOT / "pre-dispatch-failure.json"

ZERO_COUNTERS = {
    "create_thread_calls": 0,
    "created_contexts": 0,
    "dispatched_tasks": 0,
    "finalizations": 0,
    "results_observed": 0,
    "retries": 0,
    "repairs": 0,
    "followup_messages": 0,
    "judge_contexts": 0,
    "unauthorized_side_effects": 0,
}


def snapshot_guarded_paths() -> dict[str, bytes]:
    roots = [EXECUTION_ROOT, REPO_ROOT / "evals" / "m4" / "results"]
    snapshot: dict[str, bytes] = {}
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(item for item in root.rglob("*") if item.is_file()):
            snapshot[path.relative_to(REPO_ROOT).as_posix()] = path.read_bytes()
    return snapshot


class M4ExecutionTerminalTests(unittest.TestCase):
    def test_accepts_single_branch_checkout_without_authorization_branch_ref(
        self,
    ) -> None:
        real_git = execution_audit._git
        calls: list[tuple[str, ...]] = []

        def single_branch_git(*arguments: str) -> subprocess.CompletedProcess[str]:
            calls.append(arguments)
            if arguments == (
                "rev-parse",
                execution_audit.AUTHORIZATION_BRANCH,
            ):
                return subprocess.CompletedProcess(
                    ["git", *arguments],
                    returncode=128,
                    stdout="",
                    stderr="unknown revision",
                )
            return real_git(*arguments)

        with mock.patch.object(execution_audit, "_git", side_effect=single_branch_git):
            result = audit_execution(REPO_ROOT)

        self.assertEqual(result["status"], "PRE_DISPATCH_FAILED_PRESERVED")
        self.assertEqual(result["errors"], [])
        self.assertNotIn(
            ("rev-parse", execution_audit.AUTHORIZATION_BRANCH), calls
        )
        self.assertIn(
            (
                "cat-file",
                "-e",
                f"{execution_audit.AUTHORIZATION_HEAD}^{{commit}}",
            ),
            calls,
        )
        self.assertIn(
            (
                "merge-base",
                "--is-ancestor",
                execution_audit.AUTHORIZATION_HEAD,
                "HEAD",
            ),
            calls,
        )

    def test_rejects_missing_authorization_commit(self) -> None:
        real_git = execution_audit._git

        def missing_commit_git(
            *arguments: str,
        ) -> subprocess.CompletedProcess[str]:
            if arguments == (
                "cat-file",
                "-e",
                f"{execution_audit.AUTHORIZATION_HEAD}^{{commit}}",
            ):
                return subprocess.CompletedProcess(
                    ["git", *arguments],
                    returncode=1,
                    stdout="",
                    stderr="missing object",
                )
            return real_git(*arguments)

        with mock.patch.object(execution_audit, "_git", side_effect=missing_commit_git):
            result = audit_execution(REPO_ROOT)

        self.assertEqual(result["status"], "INVALID")
        self.assertIn("authorization_head_unavailable", result["errors"])
        self.assertNotIn("authorization_head_not_ancestor", result["errors"])

    def test_rejects_authorization_commit_outside_head_ancestry(self) -> None:
        real_git = execution_audit._git

        def nonancestor_git(
            *arguments: str,
        ) -> subprocess.CompletedProcess[str]:
            if arguments == (
                "merge-base",
                "--is-ancestor",
                execution_audit.AUTHORIZATION_HEAD,
                "HEAD",
            ):
                return subprocess.CompletedProcess(
                    ["git", *arguments],
                    returncode=1,
                    stdout="",
                    stderr="not an ancestor",
                )
            return real_git(*arguments)

        with mock.patch.object(execution_audit, "_git", side_effect=nonancestor_git):
            result = audit_execution(REPO_ROOT)

        self.assertEqual(result["status"], "INVALID")
        self.assertIn("authorization_head_not_ancestor", result["errors"])

    def test_repository_pre_dispatch_failure_is_preserved_read_only(self) -> None:
        before = snapshot_guarded_paths()
        result = audit_execution(REPO_ROOT)
        self.assertEqual(result["status"], "PRE_DISPATCH_FAILED_PRESERVED")
        self.assertEqual(result["errors"], [])
        self.assertEqual(
            result["claim_id"], "507b5fef-c05f-4ede-ad06-b6694203cfe1"
        )
        self.assertEqual(result["authorization_token_status"], "CONSUMED")
        self.assertEqual(
            result["failed_stage"], "frozen_request_bundle_hash_verification"
        )
        self.assertEqual(result["failed_batch_id"], "M4-BATCH-NUC")
        self.assertIsNone(result["failed_task_id"])
        self.assertEqual(result["execution_counters"], ZERO_COUNTERS)
        self.assertEqual(result["existing_result_root_count"], 0)
        self.assertFalse(result["results_manifest_present"])
        self.assertEqual(result["fresh_result_state"], "NOT_RUN")
        self.assertFalse(result["same_revision_resume_authorized"])
        self.assertTrue(result["successor_revision_required"])
        self.assertEqual(result["m3_changed_paths"], [])
        self.assertEqual(result["preparation_changed_paths"], [])
        self.assertEqual(result["side_effects"], [])
        self.assertEqual(snapshot_guarded_paths(), before)

    def _audit_mutation(self, name: str, mutate) -> dict[str, object]:
        source = EXECUTION_ROOT / name
        value = json.loads(source.read_text(encoding="utf-8"))
        mutate(value)
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            changed = Path(temp_dir) / name
            changed.write_text(
                json.dumps(value, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            kwargs = {
                "claim_path": CLAIM_PATH,
                "failure_path": FAILURE_PATH,
            }
            kwargs[
                {
                    "launch-claim.json": "claim_path",
                    "pre-dispatch-failure.json": "failure_path",
                }[name]
            ] = changed
            return audit_execution(REPO_ROOT, verify_git=False, **kwargs)

    def test_rejects_claim_token_drift(self) -> None:
        result = self._audit_mutation(
            "launch-claim.json",
            lambda value: value.__setitem__(
                "authorization_token", "sha256:" + "0" * 64
            ),
        )
        self.assertIn("claim_authorization_token_invalid", result["errors"])
        self.assertEqual(result["status"], "INVALID")

    def test_rejects_nonzero_failure_counter(self) -> None:
        result = self._audit_mutation(
            "pre-dispatch-failure.json",
            lambda value: value["counters"].__setitem__("created_contexts", 1),
        )
        self.assertIn("execution_counters_nonzero", result["errors"])
        self.assertEqual(result["status"], "INVALID")

    def test_rejects_failure_claim_hash_drift(self) -> None:
        result = self._audit_mutation(
            "pre-dispatch-failure.json",
            lambda value: value["launch_claim"].__setitem__(
                "claim_sha256", "0" * 64
            ),
        )
        self.assertIn("failure_claim_hash_invalid", result["errors"])

    def test_rejects_any_result_root(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            results_base = Path(temp_dir) / "m4.0"
            (results_base / "M4-NUC-A-F").mkdir(parents=True)
            result = audit_execution(
                REPO_ROOT, results_base=results_base, verify_git=False
            )
        self.assertIn("result_root_present", result["errors"])
        self.assertEqual(result["existing_result_root_count"], 1)


if __name__ == "__main__":
    unittest.main()
