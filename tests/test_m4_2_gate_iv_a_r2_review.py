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
    / "evals/m4/authorization/m4.2/gate-iv-a-review-r2.schema.json"
)
REVIEW_PATH = REPO_ROOT / "evals/m4/authorization/m4.2/gate-iv-a-review-r2.json"
OLD_REVIEW_PATH = REPO_ROOT / "evals/m4/authorization/m4.2/gate-iv-a-review.json"
AUDITOR_PATH = (
    REPO_ROOT / "evals/m4/authorization/audit_m4_2_gate_iv_a_r2_review.py"
)

ROOT_KEYS = {
    "schema_version",
    "reviewed_head",
    "reviewed_tree",
    "reviewed_branch",
    "reviewed_artifacts",
    "prior_blocked_review",
    "repair_evidence",
    "matrix_checks",
    "identity_checks",
    "lineage_checks",
    "request_binding_checks",
    "historical_preservation",
    "zero_state",
    "lifecycle_requirements",
    "review_delivery",
    "findings",
    "limitations",
    "reviewer_side_effects",
    "decision",
    "status",
}
PROVISIONAL_DECISION = "PENDING_M4_2_GATE_IV_A_R2_EXACT_HEAD_CI"
PROVISIONAL_STATUS = (
    "M4_2_GATE_IV_A_R2_LOCAL_REVIEW_PASSED_PENDING_EXACT_HEAD_CI"
)
FINAL_DECISION = "APPROVE_M4_2_GATE_IV_B_PROTOCOL_PROOF_ONLY"
FINAL_STATUS = "M4_2_GATE_IV_A_REVIEW_PASSED_NOT_AUTHORIZED"
R2_BRANCH = (
    "codex/m4-cross-engineering-forward-evaluation-m4.2-gate-iv-a-r2"
)
ZERO_MARKERS = {"FAIL:": 0, "FAILED (": 0, "Traceback": 0, "##[error]": 0}


def _load_auditor() -> ModuleType:
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec = importlib.util.spec_from_file_location(
            "audit_m4_2_gate_iv_a_r2_review_test", AUDITOR_PATH
        )
        if spec is None or spec.loader is None:
            raise AssertionError("auditor_import_spec_missing")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.dont_write_bytecode = previous


def _load_review() -> dict[str, Any]:
    value = json.loads(REVIEW_PATH.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError("review_not_object")
    return value


def _artifact(review: dict[str, Any], path: str) -> dict[str, Any]:
    for item in review["reviewed_artifacts"]:
        if item["path"] == path:
            return item
    raise AssertionError(f"artifact_missing:{path}")


def _diagnostic(review: dict[str, Any], path: str) -> dict[str, Any]:
    for item in review["repair_evidence"]["diagnostics_policy"]["files"]:
        if item["path"] == path:
            return item
    raise AssertionError(f"diagnostic_missing:{path}")


def _delivery_run(event: str, head: str, start: int) -> dict[str, Any]:
    return {
        "run_id": start,
        "event": event,
        "head": head,
        "branch": R2_BRANCH,
        "conclusion": "success",
        "job_count": 9,
        "jobs": [
            {
                "job_id": start * 100 + index,
                "name": f"job-{index}",
                "conclusion": "success",
            }
            for index in range(1, 10)
        ],
        "raw_log": {
            "byte_length": 1,
            "sha256": "a" * 64,
            "markers": copy.deepcopy(ZERO_MARKERS),
        },
    }


def _final_review() -> dict[str, Any]:
    review = copy.deepcopy(_load_review())
    head = "1" * 40
    review["review_delivery"] = {
        "status": "VERIFIED_TRUE_GREEN",
        "accepted_review_head": head,
        "push": _delivery_run("push", head, 1001),
        "pull_request": _delivery_run("pull_request", head, 1002),
    }
    review["decision"] = FINAL_DECISION
    review["status"] = FINAL_STATUS
    return review


class M42GateIVAR2ContractTests(unittest.TestCase):
    def test_schema_artifact_and_auditor_exist_without_copying_r1_artifact(self) -> None:
        self.assertTrue(SCHEMA_PATH.is_file())
        self.assertTrue(REVIEW_PATH.is_file())
        self.assertTrue(AUDITOR_PATH.is_file())
        self.assertFalse(OLD_REVIEW_PATH.exists())

    def test_schema_is_closed_at_every_instance_object_definition(self) -> None:
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

    def test_provisional_artifact_shape_and_permissions_are_exact(self) -> None:
        review = _load_review()
        self.assertEqual(set(review), ROOT_KEYS)
        self.assertEqual(review["findings"], [])
        self.assertEqual(review["reviewer_side_effects"], [])
        self.assertEqual(review["decision"], PROVISIONAL_DECISION)
        self.assertEqual(review["status"], PROVISIONAL_STATUS)
        self.assertEqual(
            review["review_delivery"],
            {
                "status": "PENDING_EXACT_HEAD_CI",
                "accepted_review_head": None,
                "push": None,
                "pull_request": None,
            },
        )
        lifecycle = review["lifecycle_requirements"]
        self.assertIs(lifecycle["fresh_execution_authorized"], False)
        self.assertIs(lifecycle["authorization_created"], False)
        self.assertIs(lifecycle["execution_created"], False)
        self.assertIs(lifecycle["claim_created"], False)
        self.assertEqual(lifecycle["judge"], "NOT_RUN")
        self.assertEqual(lifecycle["aggregation"], "NOT_RUN")
        self.assertEqual(lifecycle["closure"], "NOT_RUN")
        self.assertEqual(lifecycle["m5"], "NOT_STARTED")

    def test_reviewed_set_contains_eol_policy_and_every_repair_path(self) -> None:
        review = _load_review()
        paths = {item["path"] for item in review["reviewed_artifacts"]}
        self.assertEqual(len(paths), 19)
        self.assertTrue(
            {
                ".gitattributes",
                "docs/superpowers/plans/2026-08-10-m4.2-windows-lifecycle-repair.md",
                "evals/m4/audit_m4_2_preparation.py",
                "tests/test_m3_raw_sha_eol_policy.py",
            }.issubset(paths)
        )

    def test_prior_blocked_review_is_bound_as_immutable_evidence(self) -> None:
        prior = _load_review()["prior_blocked_review"]
        self.assertEqual(prior["head"], "ac6cc70714a90f73b4de09eaf0e521e699296890")
        self.assertEqual(prior["pull_request"], 4)
        self.assertEqual(prior["decision"], "BLOCKED")
        self.assertEqual(prior["status"], "BLOCKED")
        self.assertEqual(prior["finding_count"], 3)
        self.assertEqual(prior["reviewer_side_effects"], [])

    def test_artifact_is_handwritten_and_auditor_is_offline_read_only(self) -> None:
        plan = (
            REPO_ROOT
            / "docs/superpowers/plans/2026-08-10-m4.2-gate-iv-a-r2-independent-review.md"
        ).read_text(encoding="utf-8")
        source = AUDITOR_PATH.read_text(encoding="utf-8")
        self.assertIn("handwritten r2 evidence record; no builder may generate it", plan)
        for forbidden in (
            "from evals.m4.build_m4_2_preparation",
            "from evals.m4.audit_m4_2_preparation",
            "import evals.m4.build_m4_2_preparation",
            "import evals.m4.audit_m4_2_preparation",
            "urllib",
            "import requests",
            "from requests",
            "socket",
            "http.client",
            ".write_text(",
            ".write_bytes(",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)

    def test_strict_loader_rejects_duplicate_keys_and_bom(self) -> None:
        auditor = _load_auditor()
        duplicate_errors: list[str] = []
        self.assertEqual(
            auditor._load_json_bytes(
                b'{"x":1,"x":2}', "sample", duplicate_errors
            ),
            {},
        )
        self.assertIn("sample_duplicate_key", duplicate_errors)
        bom_errors: list[str] = []
        self.assertEqual(
            auditor._load_json_bytes(b"\xef\xbb\xbf{}", "sample", bom_errors),
            {},
        )
        self.assertIn("sample_bom_forbidden", bom_errors)


class M42GateIVAR2MutationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.auditor = _load_auditor()
        cls.review = _load_review()

    def _audit(
        self,
        review: dict[str, Any],
        *,
        present_paths: set[str] | None = None,
        verify_git: bool = False,
    ) -> dict[str, Any]:
        return self.auditor.audit_review(
            REPO_ROOT,
            review_data=review,
            verify_git=verify_git,
            present_paths=present_paths,
        )

    def _assert_blocked(
        self,
        review: dict[str, Any],
        error: str,
        *,
        present_paths: set[str] | None = None,
    ) -> None:
        result = self._audit(review, present_paths=present_paths)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn(error, result["errors"])

    def test_exact_provisional_review_passes_with_git_verification(self) -> None:
        result = self._audit(copy.deepcopy(self.review), verify_git=True)
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["findings"], [])
        self.assertEqual(result["reviewer_side_effects"], [])
        self.assertEqual(result["status"], PROVISIONAL_STATUS)
        self.assertEqual(result["planned_task_count"], 60)
        self.assertEqual(result["batch_count"], 6)
        self.assertEqual(result["request_binding_count"], 60)
        self.assertEqual(result["reused_task_id_count"], 0)
        self.assertEqual(result["forbidden_path_count"], 0)

    def test_semantically_complete_final_state_passes_without_git(self) -> None:
        result = self._audit(_final_review())
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["decision"], FINAL_DECISION)
        self.assertEqual(result["status"], FINAL_STATUS)

    def test_rejects_unknown_root_key(self) -> None:
        review = copy.deepcopy(self.review)
        review["unexpected"] = False
        self._assert_blocked(review, "review_root_keys_mismatch")

    def test_rejects_reviewed_head_tree_or_branch_drift(self) -> None:
        for key, value, error in (
            ("reviewed_head", "0" * 40, "reviewed_head_mismatch"),
            ("reviewed_tree", "0" * 40, "reviewed_tree_mismatch"),
            ("reviewed_branch", "wrong", "reviewed_branch_mismatch"),
        ):
            with self.subTest(key=key):
                review = copy.deepcopy(self.review)
                review[key] = value
                self._assert_blocked(review, error)

    def test_rejects_gitattributes_binding_drift(self) -> None:
        review = copy.deepcopy(self.review)
        _artifact(review, ".gitattributes")["raw_sha256"] = "0" * 64
        self._assert_blocked(review, "reviewed_artifact_binding_mismatch")

    def test_rejects_repair_change_set_or_historical_m3_drift(self) -> None:
        review = copy.deepcopy(self.review)
        review["repair_evidence"]["changed_paths"][0] = "wrong"
        self._assert_blocked(review, "repair_evidence_mismatch")
        review = copy.deepcopy(self.review)
        review["repair_evidence"]["historical_m3_changed_paths"] = [
            "evals/m3/forbidden.json"
        ]
        self._assert_blocked(review, "repair_evidence_mismatch")

    def test_rejects_diagnostics_eol_or_blob_drift(self) -> None:
        path = "evals/m3/results/diagnostics-r5.1/r5-acceptance-erratum.json"
        for key, value in (
            ("eol_attribute", "unspecified"),
            ("crlf_count", 1),
            ("worktree_equals_blob", False),
        ):
            with self.subTest(key=key):
                review = copy.deepcopy(self.review)
                _diagnostic(review, path)[key] = value
                self._assert_blocked(review, "repair_evidence_mismatch")

    def test_rejects_prior_blocked_review_relabel_or_identity_drift(self) -> None:
        for key, value in (
            ("head", "0" * 40),
            ("decision", "PASSED"),
            ("finding_count", 0),
        ):
            with self.subTest(key=key):
                review = copy.deepcopy(self.review)
                review["prior_blocked_review"][key] = value
                self._assert_blocked(review, "prior_blocked_review_mismatch")

    def test_rejects_task_or_batch_count_drift(self) -> None:
        for key, value in (("planned_task_count", 59), ("batch_count", 5)):
            with self.subTest(key=key):
                review = copy.deepcopy(self.review)
                review["matrix_checks"][key] = value
                self._assert_blocked(review, "matrix_checks_mismatch")

    def test_rejects_reused_identity_or_blind_range_drift(self) -> None:
        changes = (
            ("reused_task_ids", ["M4.1-NUC-A-N"]),
            ("blind_id_range", "M4-J120..M4-J179"),
            ("reused_batch_ids", ["M4.1-BATCH-NUC"]),
        )
        for key, value in changes:
            with self.subTest(key=key):
                review = copy.deepcopy(self.review)
                review["identity_checks"][key] = value
                self._assert_blocked(review, "identity_checks_mismatch")

    def test_rejects_lineage_drift(self) -> None:
        review = copy.deepcopy(self.review)
        review["lineage_checks"]["direct_lineage"] = "M4.0"
        self._assert_blocked(review, "lineage_checks_mismatch")

    def test_rejects_request_binding_count_or_aggregate_drift(self) -> None:
        for key, value in (("matched", 59), ("aggregate_sha256", "0" * 64)):
            with self.subTest(key=key):
                review = copy.deepcopy(self.review)
                review["request_binding_checks"][key] = value
                self._assert_blocked(review, "request_binding_checks_mismatch")

    def test_rejects_bool_int_confusion_in_authority(self) -> None:
        review = copy.deepcopy(self.review)
        review["zero_state"]["preparation_authority"][
            "fresh_execution_authorized"
        ] = 0
        self._assert_blocked(review, "zero_state_mismatch")

    def test_rejects_nonzero_counter(self) -> None:
        review = copy.deepcopy(self.review)
        review["zero_state"]["preparation_counters"]["results_observed"] = 1
        self._assert_blocked(review, "zero_state_mismatch")

    def test_rejects_m4_1_terminal_binding_drift(self) -> None:
        review = copy.deepcopy(self.review)
        review["historical_preservation"]["m4_1"]["terminal"][
            "raw_sha256"
        ] = "0" * 64
        self._assert_blocked(review, "historical_preservation_mismatch")

    def test_rejects_result_state_drift(self) -> None:
        review = copy.deepcopy(self.review)
        review["zero_state"]["results_status"] = "PARTIAL"
        self._assert_blocked(review, "zero_state_mismatch")

    def test_rejects_future_authorization_execution_or_result_paths(self) -> None:
        for path in (
            "evals/m4/authorization/m4.2/execution-authorization.json",
            "evals/m4/execution/m4.2/launch-claim.json",
            "evals/m4/results/m4.2/M4.2-NUC-A-N/result.json",
        ):
            with self.subTest(path=path):
                self._assert_blocked(
                    copy.deepcopy(self.review),
                    "forbidden_future_path_present",
                    present_paths={path},
                )

    def test_rejects_repair_ci_run_job_log_hash_or_marker_drift(self) -> None:
        mutations = (
            ("run_id", 1),
            ("jobs", []),
            ("raw_log.sha256", "0" * 64),
            ("raw_log.marker", 1),
        )
        for kind, value in mutations:
            with self.subTest(kind=kind):
                review = copy.deepcopy(self.review)
                push = review["repair_evidence"]["ci"]["push"]
                if kind == "run_id":
                    push["run_id"] = value
                elif kind == "jobs":
                    push["jobs"] = value
                elif kind == "raw_log.sha256":
                    push["raw_log"]["sha256"] = value
                else:
                    push["raw_log"]["markers"]["FAIL:"] = value
                self._assert_blocked(review, "repair_ci_evidence_mismatch")

    def test_rejects_provisional_or_final_state_mismatch(self) -> None:
        review = copy.deepcopy(self.review)
        review["decision"] = FINAL_DECISION
        self._assert_blocked(review, "provisional_decision_status_mismatch")
        review = _final_review()
        review["status"] = PROVISIONAL_STATUS
        self._assert_blocked(review, "final_decision_status_mismatch")

    def test_rejects_final_delivery_failure_marker_or_head_mismatch(self) -> None:
        review = _final_review()
        review["review_delivery"]["push"]["raw_log"]["markers"]["Traceback"] = 1
        self._assert_blocked(review, "review_delivery_push_mismatch")
        review = _final_review()
        review["review_delivery"]["pull_request"]["head"] = "2" * 40
        self._assert_blocked(review, "review_delivery_pull_request_mismatch")

    def test_rejects_findings_or_reviewer_side_effects(self) -> None:
        review = copy.deepcopy(self.review)
        review["findings"] = ["independent_finding"]
        self._assert_blocked(review, "review_findings_present")
        review = copy.deepcopy(self.review)
        review["reviewer_side_effects"] = ["wrote_preparation"]
        self._assert_blocked(review, "reviewer_side_effects_present")

    def test_rejects_decision_that_attempts_execution_authorization(self) -> None:
        review = copy.deepcopy(self.review)
        review["decision"] = "AUTHORIZE_M4_2_EXECUTION"
        self._assert_blocked(review, "decision_attempts_execution_authorization")

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
        self.assertEqual(payload["status"], PROVISIONAL_STATUS)
        self.assertEqual(payload["findings"], [])
        self.assertEqual(payload["reviewer_side_effects"], [])


if __name__ == "__main__":
    unittest.main()
