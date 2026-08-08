from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
M4_ROOT = REPO_ROOT / "evals" / "m4"


def _load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"expected object: {path}")
    return value


def _load_auditor():
    path = M4_ROOT / "audit_results.py"
    spec = importlib.util.spec_from_file_location("m4_audit_results", path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class M4ResultAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.auditor = _load_auditor()
        cls.preparation = _load_json(M4_ROOT / "preparation-manifest.json")
        cls.rubric = _load_json(M4_ROOT / "judge-rubric.json")
        cls.case_mismatches = {}
        for path in sorted((M4_ROOT / "cases").glob("*.json")):
            case = _load_json(path)
            cls.case_mismatches[case["case_id"]] = {
                item["mismatch_id"] for item in case["preregistered_mismatches"]
            }

    def _passing_matrix(self):
        task_results = {}
        judge_scores = {}
        arm_scores = {
            "N": {
                "direction_feasibility": 1,
                "mismatch_detection": 1,
                "plan_executability": 1,
                "uncertainty_quality": 1,
                "evidence_discipline": 1,
            },
            "F": {
                "direction_feasibility": 4,
                "mismatch_detection": 4,
                "plan_executability": 4,
                "uncertainty_quality": 4,
                "evidence_discipline": 4,
            },
            "A1": {
                "direction_feasibility": 3,
                "mismatch_detection": 3,
                "plan_executability": 3,
                "uncertainty_quality": 3,
                "evidence_discipline": 2,
            },
            "A2": {
                "direction_feasibility": 2,
                "mismatch_detection": 3,
                "plan_executability": 3,
                "uncertainty_quality": 3,
                "evidence_discipline": 3,
            },
            "A3": {
                "direction_feasibility": 3,
                "mismatch_detection": 3,
                "plan_executability": 3,
                "uncertainty_quality": 2,
                "evidence_discipline": 3,
            },
        }
        for index, task in enumerate(self.preparation["tasks"], start=1):
            expected = self.case_mismatches[task["case_id"]]
            detected = sorted(expected) if task["arm_id"] == "F" else []
            task_results[task["task_id"]] = {
                "schema_version": "m4-task-result-v1",
                "task_id": task["task_id"],
                "blind_id": task["blind_id"],
                "context_id": f"synthetic-context-{index:03d}",
                "finalization_id": f"synthetic-final-{index:03d}",
                "attempt_index": 1,
                "retry_count": 0,
                "independent_finalization": True,
                "visible_result_task_ids": [],
                "response": "Synthetic structural test result; not fresh evidence.",
                "citations": [],
                "machine_metrics": {
                    "fabricated_citation_count": 0,
                    "unverified_recommendation_count": 0,
                    "direction_gate_violation_count": 0,
                    "route_binding_violation_count": 0,
                    "resource_ceiling_violation_count": 0,
                    "stop_pivot_authority_violation_count": 0,
                    "unauthorized_side_effect_count": 0,
                    "schema_valid": True,
                },
                "detected_mismatch_ids": detected,
                "side_effects": [],
                "terminal_state": "finalized",
            }
            judge_scores[task["blind_id"]] = {
                "schema_version": "m4-judge-score-v1",
                "blind_id": task["blind_id"],
                "judge_id": f"synthetic-judge-{index:03d}",
                "arm_identity_unknown": True,
                "mapping_accessed": False,
                "scores": arm_scores[task["arm_id"]],
                "failure_tags": [],
            }
        return task_results, judge_scores

    def _audit(self, task_results, judge_scores):
        return self.auditor.audit_result_matrix(
            self.preparation,
            self.rubric,
            task_results,
            judge_scores,
            self.case_mismatches,
        )

    def test_repository_results_are_truthfully_not_run(self) -> None:
        result = self.auditor.audit_results(REPO_ROOT)
        self.assertTrue(result["valid"])
        self.assertEqual(result["status"], "NOT_RUN")
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["observed_task_count"], 0)
        self.assertEqual(result["retry_count"], 0)

    def test_synthetic_complete_matrix_meets_thresholds(self) -> None:
        task_results, judge_scores = self._passing_matrix()
        result = self._audit(task_results, judge_scores)
        self.assertTrue(result["valid"])
        self.assertEqual(result["status"], "accepted")
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["observed_task_count"], 60)
        self.assertEqual(result["full_vs_no_skill"]["strictly_better_case_count"], 12)
        self.assertGreaterEqual(
            result["full_vs_no_skill"]["mismatch_recall_percentage_point_delta"],
            20,
        )
        for arm_id in ("A1", "A2", "A3"):
            self.assertEqual(
                result["full_vs_ablations"][arm_id]["strictly_better_case_count"],
                12,
            )

    def test_full_skill_critical_machine_metrics_fail_closed(self) -> None:
        task_results, judge_scores = self._passing_matrix()
        full_task = next(
            task for task in self.preparation["tasks"] if task["arm_id"] == "F"
        )
        task_results[full_task["task_id"]]["machine_metrics"][
            "fabricated_citation_count"
        ] = 1
        result = self._audit(task_results, judge_scores)
        self.assertIn("full_skill_fabricated_citation_count_nonzero", result["errors"])

        task_results, judge_scores = self._passing_matrix()
        task_results[full_task["task_id"]]["machine_metrics"][
            "unauthorized_side_effect_count"
        ] = 1
        task_results[full_task["task_id"]]["side_effects"] = ["synthetic-write"]
        result = self._audit(task_results, judge_scores)
        self.assertIn("full_skill_unauthorized_side_effect_count_nonzero", result["errors"])

    def test_retry_visibility_and_blinding_fail_closed(self) -> None:
        task_results, judge_scores = self._passing_matrix()
        task_id = self.preparation["tasks"][0]["task_id"]
        blind_id = self.preparation["tasks"][0]["blind_id"]
        task_results[task_id]["retry_count"] = 1
        task_results[task_id]["visible_result_task_ids"] = [
            self.preparation["tasks"][1]["task_id"]
        ]
        judge_scores[blind_id]["arm_identity_unknown"] = False
        result = self._audit(task_results, judge_scores)
        self.assertIn("retry_or_repair_forbidden", result["errors"])
        self.assertIn("cross_task_result_visibility_forbidden", result["errors"])
        self.assertIn("judge_blinding_violation", result["errors"])

    def test_incomplete_matrix_and_threshold_regression_fail_closed(self) -> None:
        task_results, judge_scores = self._passing_matrix()
        removed = self.preparation["tasks"][0]
        del task_results[removed["task_id"]]
        del judge_scores[removed["blind_id"]]
        result = self._audit(task_results, judge_scores)
        self.assertIn("task_result_set_incomplete", result["errors"])
        self.assertIn("judge_score_set_incomplete", result["errors"])

        task_results, judge_scores = self._passing_matrix()
        for task in self.preparation["tasks"]:
            if task["arm_id"] == "F":
                judge_scores[task["blind_id"]]["scores"]["direction_feasibility"] = 1
        result = self._audit(task_results, judge_scores)
        self.assertIn("full_vs_no_skill_feasibility_delta_below_threshold", result["errors"])

    def test_schema_invalid_terminal_fails_closed(self) -> None:
        task_results, judge_scores = self._passing_matrix()
        task_id = self.preparation["tasks"][0]["task_id"]
        task_results[task_id]["machine_metrics"]["schema_valid"] = False
        task_results[task_id]["terminal_state"] = "schema_invalid"
        result = self._audit(task_results, judge_scores)
        self.assertIn("task_schema_invalid", result["errors"])


if __name__ == "__main__":
    unittest.main()
