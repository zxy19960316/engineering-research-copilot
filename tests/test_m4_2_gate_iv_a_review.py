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
    / "evals/m4/authorization/m4.2/gate-iv-a-review.schema.json"
)
REVIEW_PATH = REPO_ROOT / "evals/m4/authorization/m4.2/gate-iv-a-review.json"
AUDITOR_PATH = (
    REPO_ROOT / "evals/m4/authorization/audit_m4_2_gate_iv_a_review.py"
)

REVIEW_KEYS = {
    "schema_version",
    "reviewed_head",
    "reviewed_tree",
    "reviewed_branch",
    "reviewed_artifacts",
    "ci_evidence",
    "matrix_checks",
    "identity_checks",
    "lineage_checks",
    "request_binding_checks",
    "ci_integrity_checks",
    "historical_preservation",
    "zero_state",
    "lifecycle_requirements",
    "findings",
    "limitations",
    "reviewer_side_effects",
    "decision",
    "status",
}


def _load_auditor() -> ModuleType:
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec = importlib.util.spec_from_file_location(
            "audit_m4_2_gate_iv_a_review_test", AUDITOR_PATH
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


def _passing_review() -> dict[str, Any]:
    review = copy.deepcopy(_load_review())
    review["findings"] = []
    review["decision"] = "APPROVE_M4_2_GATE_IV_B_PROTOCOL_PROOF_ONLY"
    review["status"] = "M4_2_GATE_IV_A_REVIEW_PASSED_NOT_AUTHORIZED"
    return review


def _artifact(review: dict[str, Any], suffix: str) -> dict[str, Any]:
    for item in review["reviewed_artifacts"]:
        if item["path"].endswith(suffix):
            return item
    raise AssertionError(f"artifact_missing:{suffix}")


class M42GateIVAReviewContractTests(unittest.TestCase):
    def test_schema_is_closed_at_every_object_definition(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertEqual(schema["type"], "object")
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(set(schema["required"]), REVIEW_KEYS)
        self.assertEqual(set(schema["properties"]), REVIEW_KEYS)

        for name, definition in schema["$defs"].items():
            if definition.get("type") == "object":
                with self.subTest(definition=name):
                    self.assertIs(definition.get("additionalProperties"), False)
                    self.assertEqual(
                        set(definition["required"]),
                        set(definition["properties"]),
                    )

    def test_review_artifact_and_auditor_exist(self) -> None:
        self.assertTrue(REVIEW_PATH.is_file())
        self.assertTrue(AUDITOR_PATH.is_file())

    def test_review_shape_and_blocked_decision_are_exact(self) -> None:
        review = _load_review()
        self.assertEqual(set(review), REVIEW_KEYS)
        self.assertEqual(len(review["findings"]), 3)
        self.assertTrue(
            all("0cc2364aa7833cc410d3133d33597d552b02153d" in finding
                for finding in review["findings"][:2])
        )
        self.assertEqual(review["reviewer_side_effects"], [])
        self.assertEqual(review["decision"], "BLOCKED")
        self.assertEqual(review["status"], "BLOCKED")
        lifecycle = review["lifecycle_requirements"]
        self.assertIs(lifecycle["fresh_execution_authorized"], False)
        self.assertIs(lifecycle["authorization_created"], False)
        self.assertIs(lifecycle["execution_created"], False)
        self.assertIs(lifecycle["claim_created"], False)

    def test_artifact_was_not_generated_and_auditor_has_no_network_or_write_api(
        self,
    ) -> None:
        source = AUDITOR_PATH.read_text(encoding="utf-8")
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


class M42GateIVAReviewMutationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.auditor = _load_auditor()
        cls.review = _load_review()

    def _audit(
        self,
        review: dict[str, Any],
        *,
        present_paths: set[str] | None = None,
        verify_git: bool = True,
    ) -> dict[str, Any]:
        result = self.auditor.audit_review(
            REPO_ROOT,
            review_data=review,
            verify_git=verify_git,
            present_paths=present_paths,
        )
        return result

    def _assert_blocked(
        self,
        review: dict[str, Any],
        error: str,
        *,
        present_paths: set[str] | None = None,
    ) -> None:
        result = self._audit(
            review,
            present_paths=present_paths,
            verify_git=False,
        )
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn(error, result["errors"])

    def test_exact_review_passes(self) -> None:
        result = self._audit(_passing_review())
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["findings"], [])
        self.assertEqual(result["reviewer_side_effects"], [])
        self.assertEqual(result["forbidden_path_count"], 0)
        self.assertEqual(
            result["status"],
            "M4_2_GATE_IV_A_REVIEW_PASSED_NOT_AUTHORIZED",
        )

    def test_committed_review_is_blocked_by_exact_head_windows_ci(self) -> None:
        result = self._audit(copy.deepcopy(self.review))
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["errors"], [])
        self.assertEqual(len(result["findings"]), 3)
        self.assertEqual(result["reviewer_side_effects"], [])

    def test_rejects_reviewed_head_drift(self) -> None:
        review = copy.deepcopy(self.review)
        review["reviewed_head"] = "0" * 40
        self._assert_blocked(review, "reviewed_head_mismatch")

    def test_rejects_reviewed_tree_drift(self) -> None:
        review = copy.deepcopy(self.review)
        review["reviewed_tree"] = "0" * 40
        self._assert_blocked(review, "reviewed_tree_mismatch")

    def test_rejects_preparation_manifest_hash_drift(self) -> None:
        review = copy.deepcopy(self.review)
        _artifact(review, "m4.2/preparation-manifest.json")["raw_sha256"] = "0" * 64
        self._assert_blocked(review, "reviewed_artifact_binding_mismatch")

    def test_rejects_helper_hash_drift(self) -> None:
        review = copy.deepcopy(self.review)
        review["request_binding_checks"]["helper"]["raw_sha256"] = "0" * 64
        self._assert_blocked(review, "request_binding_checks_mismatch")

    def test_rejects_task_count_drift(self) -> None:
        review = copy.deepcopy(self.review)
        review["matrix_checks"]["planned_task_count"] = 59
        self._assert_blocked(review, "matrix_checks_mismatch")

    def test_rejects_batch_count_drift(self) -> None:
        review = copy.deepcopy(self.review)
        review["matrix_checks"]["batch_count"] = 5
        self._assert_blocked(review, "matrix_checks_mismatch")

    def test_rejects_task_id_reuse(self) -> None:
        review = copy.deepcopy(self.review)
        review["identity_checks"]["reused_task_ids"] = ["M4-NUC-A-N"]
        self._assert_blocked(review, "identity_checks_mismatch")

    def test_rejects_blind_id_reuse(self) -> None:
        review = copy.deepcopy(self.review)
        review["identity_checks"]["reused_blind_ids"] = ["M4-J001"]
        self._assert_blocked(review, "identity_checks_mismatch")

    def test_rejects_lineage_drift(self) -> None:
        review = copy.deepcopy(self.review)
        review["lineage_checks"]["direct_lineage"] = "M4.0"
        self._assert_blocked(review, "lineage_checks_mismatch")

    def test_rejects_request_binding_drift(self) -> None:
        review = copy.deepcopy(self.review)
        review["request_binding_checks"]["matched"] = 59
        self._assert_blocked(review, "request_binding_checks_mismatch")

    def test_rejects_false_green_relabeling(self) -> None:
        review = copy.deepcopy(self.review)
        review["ci_evidence"]["historical_false_green"][0]["acceptance"] = "ACCEPTED"
        self._assert_blocked(review, "ci_evidence_mismatch")

    def test_rejects_missing_true_green_evidence(self) -> None:
        review = copy.deepcopy(self.review)
        del review["ci_evidence"]["implementation"]["push"]["jobs"][-1]
        self._assert_blocked(review, "ci_evidence_mismatch")

    def test_rejects_ci_log_hash_drift(self) -> None:
        review = copy.deepcopy(self.review)
        review["ci_evidence"]["closure"]["push"]["raw_log"]["sha256"] = "0" * 64
        self._assert_blocked(review, "ci_evidence_mismatch")

    def test_rejects_authority_true(self) -> None:
        review = copy.deepcopy(self.review)
        authority = review["zero_state"]["preparation_authority"]
        authority["fresh_execution_authorized"] = True
        self._assert_blocked(review, "zero_state_mismatch")

    def test_rejects_nonzero_counter(self) -> None:
        review = copy.deepcopy(self.review)
        review["zero_state"]["preparation_counters"]["results_observed"] = 1
        self._assert_blocked(review, "zero_state_mismatch")

    def test_rejects_authorization_artifact_present(self) -> None:
        review = copy.deepcopy(self.review)
        review["zero_state"]["authorization"] = "PRESENT"
        self._assert_blocked(
            review,
            "forbidden_future_path_present",
            present_paths={"evals/m4/authorization/m4.2/execution-authorization.json"},
        )

    def test_rejects_execution_or_result_path_present(self) -> None:
        for path in (
            "evals/m4/execution/m4.2/launch-claim.json",
            "evals/m4/results/m4.2/M4.2-NUC-A-N/result.json",
        ):
            with self.subTest(path=path):
                self._assert_blocked(
                    copy.deepcopy(self.review),
                    "forbidden_future_path_present",
                    present_paths={path},
                )

    def test_rejects_nonempty_findings_with_passed_status(self) -> None:
        review = _passing_review()
        review["findings"] = ["independent_finding"]
        self._assert_blocked(review, "passed_with_findings")

    def test_rejects_reviewer_side_effects(self) -> None:
        review = _passing_review()
        review["reviewer_side_effects"] = ["wrote_preparation"]
        self._assert_blocked(review, "passed_with_reviewer_side_effects")

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
        self.assertEqual(first.returncode, 1, first.stderr.decode("utf-8", "replace"))
        self.assertEqual(second.returncode, 1, second.stderr.decode("utf-8", "replace"))
        self.assertEqual(first.stdout, second.stdout)
        self.assertEqual(before, after)
        payload = json.loads(first.stdout)
        self.assertEqual(payload["status"], "BLOCKED")
        self.assertEqual(payload["errors"], [])
        self.assertEqual(len(payload["findings"]), 3)


if __name__ == "__main__":
    unittest.main()
