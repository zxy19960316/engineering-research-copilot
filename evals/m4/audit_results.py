from __future__ import annotations

import argparse
import hashlib
import json
import statistics
from collections import Counter
from pathlib import Path
from typing import Any


M4_ROOT = Path("evals/m4")
PREPARATION_PATH = M4_ROOT / "preparation-manifest.json"
RUBRIC_PATH = M4_ROOT / "judge-rubric.json"
DEFAULT_RESULTS_MANIFEST = M4_ROOT / "results-manifest.json"
DEFAULT_RESULTS_ROOT = M4_ROOT / "results"
ARM_IDS = ("N", "F", "A1", "A2", "A3")
SCORE_METRICS = (
    "direction_feasibility",
    "mismatch_detection",
    "plan_executability",
    "uncertainty_quality",
    "evidence_discipline",
)
COUNT_METRICS = (
    "fabricated_citation_count",
    "unverified_recommendation_count",
    "direction_gate_violation_count",
    "route_binding_violation_count",
    "resource_ceiling_violation_count",
    "stop_pivot_authority_violation_count",
    "unauthorized_side_effect_count",
)
TASK_RESULT_KEYS = {
    "schema_version",
    "task_id",
    "blind_id",
    "context_id",
    "finalization_id",
    "attempt_index",
    "retry_count",
    "independent_finalization",
    "visible_result_task_ids",
    "response",
    "citations",
    "machine_metrics",
    "detected_mismatch_ids",
    "side_effects",
    "terminal_state",
}
JUDGE_SCORE_KEYS = {
    "schema_version",
    "blind_id",
    "judge_id",
    "arm_identity_unknown",
    "mapping_accessed",
    "scores",
    "failure_tags",
}


def _load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _add(errors: list[str], code: str) -> None:
    if code not in errors:
        errors.append(code)


def _median(values: list[float]) -> float:
    return float(statistics.median(values)) if values else 0.0


def _bootstrap_interval(
    values: list[float], *, seed: str, resamples: int
) -> list[float]:
    if not values:
        return [0.0, 0.0]
    medians: list[float] = []
    size = len(values)
    for resample_index in range(resamples):
        sample: list[float] = []
        for position in range(size):
            digest = hashlib.sha256(
                f"{seed}:{resample_index}:{position}".encode("utf-8")
            ).digest()
            sample.append(values[int.from_bytes(digest[:8], "big") % size])
        medians.append(_median(sample))
    medians.sort()
    lower = medians[int((resamples - 1) * 0.025)]
    upper = medians[int((resamples - 1) * 0.975)]
    return [lower, upper]


def _empty_result(status: str, errors: list[str]) -> dict[str, object]:
    return {
        "valid": not errors,
        "status": status,
        "errors": errors,
        "observed_task_count": 0,
        "observed_finalization_count": 0,
        "retry_count": 0,
        "full_critical_metrics": {},
        "full_vs_no_skill": {},
        "full_vs_ablations": {},
        "failure_taxonomy": {},
    }


def audit_result_matrix(
    preparation: dict[str, Any],
    rubric: dict[str, Any],
    task_results: dict[str, dict[str, Any]],
    judge_scores: dict[str, dict[str, Any]],
    case_mismatches: dict[str, set[str]],
) -> dict[str, object]:
    errors: list[str] = []
    expected_tasks = preparation.get("tasks")
    if not isinstance(expected_tasks, list) or len(expected_tasks) != 60:
        return _empty_result("failed", ["preparation_task_matrix_invalid"])
    task_by_id = {task["task_id"]: task for task in expected_tasks}
    blind_to_task = {task["blind_id"]: task for task in expected_tasks}
    if set(task_results) != set(task_by_id):
        _add(errors, "task_result_set_incomplete")
    if set(judge_scores) != set(blind_to_task):
        _add(errors, "judge_score_set_incomplete")

    context_ids: list[str] = []
    finalization_ids: list[str] = []
    retry_count = 0
    machine_totals = {
        arm_id: {metric: 0 for metric in COUNT_METRICS} for arm_id in ARM_IDS
    }
    normalized_scores: dict[tuple[str, str], dict[str, int]] = {}
    detected_by_case_arm: dict[tuple[str, str], set[str]] = {}
    taxonomy = Counter()

    for task_id, task in task_by_id.items():
        result = task_results.get(task_id)
        if not isinstance(result, dict):
            continue
        if set(result) != TASK_RESULT_KEYS or result.get("schema_version") != "m4-task-result-v1":
            _add(errors, "task_result_shape_invalid")
        if result.get("task_id") != task_id or result.get("blind_id") != task["blind_id"]:
            _add(errors, "task_result_binding_invalid")
        if result.get("attempt_index") != 1 or result.get("retry_count") != 0:
            _add(errors, "retry_or_repair_forbidden")
        retry_value = result.get("retry_count")
        if isinstance(retry_value, int) and not isinstance(retry_value, bool):
            retry_count += retry_value
        if result.get("independent_finalization") is not True:
            _add(errors, "independent_finalization_required")
        if result.get("visible_result_task_ids") != []:
            _add(errors, "cross_task_result_visibility_forbidden")
        if result.get("terminal_state") != "finalized":
            _add(errors, "task_terminal_state_invalid")
        if isinstance(result.get("context_id"), str) and result["context_id"]:
            context_ids.append(result["context_id"])
        else:
            _add(errors, "context_id_invalid")
        if isinstance(result.get("finalization_id"), str) and result["finalization_id"]:
            finalization_ids.append(result["finalization_id"])
        else:
            _add(errors, "finalization_id_invalid")

        metrics = result.get("machine_metrics")
        if not isinstance(metrics, dict) or set(metrics) != {*COUNT_METRICS, "schema_valid"}:
            _add(errors, "machine_metrics_invalid")
            metrics = {}
        for metric in COUNT_METRICS:
            value = metrics.get(metric)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                _add(errors, "machine_metrics_invalid")
            else:
                machine_totals[task["arm_id"]][metric] += value
        if metrics.get("schema_valid") is not True:
            _add(errors, "task_schema_invalid")
        side_effects = result.get("side_effects")
        if not isinstance(side_effects, list):
            _add(errors, "side_effects_invalid")
        elif isinstance(metrics.get("unauthorized_side_effect_count"), int) and len(side_effects) != metrics.get(
            "unauthorized_side_effect_count"
        ):
            _add(errors, "side_effect_counter_mismatch")
        detected = result.get("detected_mismatch_ids")
        if not isinstance(detected, list) or any(not isinstance(item, str) for item in detected):
            _add(errors, "detected_mismatch_ids_invalid")
            detected = []
        detected_by_case_arm[(task["case_id"], task["arm_id"])] = set(detected)

        score = judge_scores.get(task["blind_id"])
        if not isinstance(score, dict):
            continue
        if set(score) != JUDGE_SCORE_KEYS or score.get("schema_version") != "m4-judge-score-v1":
            _add(errors, "judge_score_shape_invalid")
        if score.get("blind_id") != task["blind_id"]:
            _add(errors, "judge_score_binding_invalid")
        if score.get("arm_identity_unknown") is not True or score.get("mapping_accessed") is not False:
            _add(errors, "judge_blinding_violation")
        scores = score.get("scores")
        if not isinstance(scores, dict) or set(scores) != set(SCORE_METRICS):
            _add(errors, "judge_metric_set_invalid")
            continue
        normalized: dict[str, int] = {}
        for metric in SCORE_METRICS:
            value = scores.get(metric)
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 4:
                _add(errors, "judge_score_out_of_range")
            else:
                normalized[metric] = value
        if len(normalized) == len(SCORE_METRICS):
            normalized_scores[(task["case_id"], task["arm_id"])] = normalized
        failure_tags = score.get("failure_tags")
        allowed_tags = set(rubric.get("failure_taxonomy", []))
        if not isinstance(failure_tags, list) or any(tag not in allowed_tags for tag in failure_tags):
            _add(errors, "failure_taxonomy_invalid")
        else:
            taxonomy.update(failure_tags)

    if len(set(context_ids)) != len(context_ids):
        _add(errors, "context_id_reused")
    if len(set(finalization_ids)) != len(finalization_ids):
        _add(errors, "finalization_id_reused")
    if len(normalized_scores) != 60:
        _add(errors, "judge_score_set_incomplete")

    critical = rubric["acceptance_thresholds"]["critical_full_skill"]
    for metric, maximum in critical.items():
        if machine_totals["F"][metric] != maximum:
            _add(errors, f"full_skill_{metric}_nonzero")

    case_ids = sorted({task["case_id"] for task in expected_tasks})
    feasibility_deltas: list[float] = []
    executability_deltas: list[float] = []
    strict_wins = 0
    if len(normalized_scores) == 60:
        for case_id in case_ids:
            full = normalized_scores[(case_id, "F")]
            no_skill = normalized_scores[(case_id, "N")]
            feasibility_deltas.append(
                float(full["direction_feasibility"] - no_skill["direction_feasibility"])
            )
            executability_deltas.append(
                float(full["plan_executability"] - no_skill["plan_executability"])
            )
            if sum(full.values()) > sum(no_skill.values()):
                strict_wins += 1

    expected_mismatch_count = sum(len(case_mismatches.get(case_id, set())) for case_id in case_ids)

    def mismatch_recall(arm_id: str) -> float:
        if expected_mismatch_count == 0:
            return 0.0
        detected_count = 0
        for case_id in case_ids:
            expected = case_mismatches.get(case_id, set())
            detected = detected_by_case_arm.get((case_id, arm_id), set())
            detected_count += len(expected & detected)
        return detected_count / expected_mismatch_count

    mismatch_delta_pp = (mismatch_recall("F") - mismatch_recall("N")) * 100.0
    full_vs_n_thresholds = rubric["acceptance_thresholds"]["full_vs_no_skill"]
    feasibility_median = _median(feasibility_deltas)
    executability_median = _median(executability_deltas)
    if feasibility_median < full_vs_n_thresholds["feasibility_paired_median_delta_min"]:
        _add(errors, "full_vs_no_skill_feasibility_delta_below_threshold")
    if executability_median < full_vs_n_thresholds["executability_paired_median_delta_min"]:
        _add(errors, "full_vs_no_skill_executability_delta_below_threshold")
    if strict_wins < full_vs_n_thresholds["strictly_better_case_count_min"]:
        _add(errors, "full_vs_no_skill_strict_win_count_below_threshold")
    if mismatch_delta_pp < full_vs_n_thresholds["mismatch_recall_percentage_point_delta_min"]:
        _add(errors, "full_vs_no_skill_mismatch_recall_below_threshold")

    bootstrap_resamples = rubric["reporting"]["paired_bootstrap_resamples"]
    bootstrap_seed = rubric["reporting"]["paired_bootstrap_seed"]
    full_vs_no_skill = {
        "feasibility_paired_deltas": feasibility_deltas,
        "feasibility_paired_median_delta": feasibility_median,
        "feasibility_paired_bootstrap_interval": _bootstrap_interval(
            feasibility_deltas,
            seed=f"{bootstrap_seed}:feasibility",
            resamples=bootstrap_resamples,
        ),
        "executability_paired_deltas": executability_deltas,
        "executability_paired_median_delta": executability_median,
        "executability_paired_bootstrap_interval": _bootstrap_interval(
            executability_deltas,
            seed=f"{bootstrap_seed}:executability",
            resamples=bootstrap_resamples,
        ),
        "strictly_better_case_count": strict_wins,
        "mismatch_recall_full": mismatch_recall("F"),
        "mismatch_recall_no_skill": mismatch_recall("N"),
        "mismatch_recall_percentage_point_delta": mismatch_delta_pp,
    }

    ablation_thresholds = rubric["acceptance_thresholds"]["full_vs_ablations"]
    full_vs_ablations: dict[str, object] = {}
    for arm_id in ("A1", "A2", "A3"):
        metric = ablation_thresholds["primary_metric_by_arm"][arm_id]
        wins = 0
        deltas: list[float] = []
        if len(normalized_scores) == 60:
            for case_id in case_ids:
                delta = float(
                    normalized_scores[(case_id, "F")][metric]
                    - normalized_scores[(case_id, arm_id)][metric]
                )
                deltas.append(delta)
                if delta > 0:
                    wins += 1
        if wins < ablation_thresholds["strictly_better_case_count_min"]:
            _add(errors, f"full_vs_{arm_id}_strict_win_count_below_threshold")
        for machine_metric in ablation_thresholds["no_increase_metrics"]:
            if machine_totals["F"][machine_metric] > machine_totals[arm_id][machine_metric]:
                _add(errors, f"full_vs_{arm_id}_{machine_metric}_increase")
        full_vs_ablations[arm_id] = {
            "primary_metric": metric,
            "paired_deltas": deltas,
            "paired_median_delta": _median(deltas),
            "strictly_better_case_count": wins,
        }

    return {
        "valid": not errors,
        "status": "accepted" if not errors else "failed",
        "errors": errors,
        "observed_task_count": len(task_results),
        "observed_finalization_count": len(finalization_ids),
        "retry_count": retry_count,
        "full_critical_metrics": machine_totals["F"],
        "full_vs_no_skill": full_vs_no_skill,
        "full_vs_ablations": full_vs_ablations,
        "failure_taxonomy": dict(sorted(taxonomy.items())),
    }


def _safe_repo_path(repo_root: Path, relative_path: str) -> Path:
    root = repo_root.resolve()
    path = (repo_root / relative_path).resolve()
    if not path.is_relative_to(root):
        raise ValueError("result path escapes repository")
    return path


def audit_results(
    repo_root: Path,
    results_manifest_path: Path | None = None,
) -> dict[str, object]:
    preparation = _load_object(repo_root / PREPARATION_PATH)
    rubric = _load_object(repo_root / RUBRIC_PATH)
    manifest_path = results_manifest_path or (repo_root / DEFAULT_RESULTS_MANIFEST)
    results_root = repo_root / DEFAULT_RESULTS_ROOT
    if not manifest_path.exists():
        unexpected = []
        if results_root.exists():
            unexpected = [path for path in results_root.rglob("*") if path.is_file()]
        if unexpected:
            return _empty_result("invalid", ["results_exist_without_manifest"])
        return _empty_result("NOT_RUN", [])

    pre_errors: list[str] = []
    if preparation.get("authority", {}).get("fresh_execution_authorized") is not True:
        _add(pre_errors, "results_exist_without_execution_authority")
    try:
        results_manifest = _load_object(manifest_path)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        return _empty_result("invalid", ["results_manifest_invalid"])
    required_manifest_keys = {
        "schema_version",
        "revision",
        "preparation_manifest_sha256",
        "status",
        "records",
        "counters",
    }
    if set(results_manifest) != required_manifest_keys:
        _add(pre_errors, "results_manifest_shape_invalid")
    preparation_bytes = (repo_root / PREPARATION_PATH).read_bytes()
    if results_manifest.get("preparation_manifest_sha256") != _sha256(preparation_bytes):
        _add(pre_errors, "preparation_manifest_binding_invalid")
    records = results_manifest.get("records")
    if not isinstance(records, list) or len(records) != 60:
        return _empty_result("invalid", [*pre_errors, "results_record_set_incomplete"])

    task_results: dict[str, dict[str, Any]] = {}
    judge_scores: dict[str, dict[str, Any]] = {}
    for record in records:
        try:
            result_path = _safe_repo_path(repo_root, record["result_path"])
            judge_path = _safe_repo_path(repo_root, record["judge_score_path"])
            result_bytes = result_path.read_bytes()
            judge_bytes = judge_path.read_bytes()
            if _sha256(result_bytes) != record["result_sha256"]:
                _add(pre_errors, "task_result_hash_mismatch")
            if _sha256(judge_bytes) != record["judge_score_sha256"]:
                _add(pre_errors, "judge_score_hash_mismatch")
            task_result = json.loads(result_bytes.decode("utf-8"))
            judge_score = json.loads(judge_bytes.decode("utf-8"))
            if not isinstance(task_result, dict) or not isinstance(judge_score, dict):
                raise ValueError("result root must be object")
            task_results[record["task_id"]] = task_result
            judge_scores[record["blind_id"]] = judge_score
        except (KeyError, OSError, UnicodeError, json.JSONDecodeError, ValueError):
            _add(pre_errors, "result_artifact_invalid")

    case_mismatches: dict[str, set[str]] = {}
    for path in sorted((repo_root / M4_ROOT / "cases").glob("*.json")):
        case = _load_object(path)
        case_mismatches[case["case_id"]] = {
            item["mismatch_id"] for item in case["preregistered_mismatches"]
        }
    result = audit_result_matrix(
        preparation,
        rubric,
        task_results,
        judge_scores,
        case_mismatches,
    )
    for code in pre_errors:
        _add(result["errors"], code)
    if result["errors"]:
        result["valid"] = False
        result["status"] = "failed"
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expect-not-run", action="store_true")
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    result = audit_results(repo_root)
    if args.expect_not_run and result["status"] != "NOT_RUN":
        _add(result["errors"], "not_run_state_required")
        result["valid"] = False
        result["status"] = "invalid"
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    if args.expect_not_run:
        return 0 if result["status"] == "NOT_RUN" and result["valid"] else 1
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
