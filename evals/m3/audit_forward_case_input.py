#!/usr/bin/env python3
"""Audit one immutable M2 input before freezing an M3 r3 prompt."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = REPO_ROOT / "skills" / "engineering-research-copilot" / "scripts"
sys.path.insert(0, str(SCRIPT_ROOT))

from validate_m2_direction_bundle import (  # noqa: E402
    canonical_sha256,
    validate_bundle as validate_m2_bundle,
)


CASE_MODES = {
    "m3-f01": "bounded",
    "m3-f02": "route_specific",
    "m3-f03": None,
    "m3-f04": "bounded",
    "m3-f05": "route_specific",
}
VALIDATOR = "skills/engineering-research-copilot/scripts/validate_m2_direction_bundle.py"
ELIGIBLE_STATUSES = {"verified_primary", "verified_registry", "verified_preprint"}
NON_PREPRINT_STATUSES = {"verified_primary", "verified_registry"}
ALLOWED_PRECONDITION_STATUSES = {"bounded_testable", "verified", "satisfied", "pass"}
NUCLEAR_TOKENS = ("nuclear", "reactor", "pwr", "loca", "npp")
ML_TOKENS = ("machine learning", "deep learning", "neural", "ml", "bayesian")
F05_BOUNDARIES = [
    "non_preprint_safety_support_is_claim_limited",
    "specialist_review_required",
    "no_operational_or_safety_credit",
    "transfer_status_hypothesis",
]


def _result(case_id: str) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "status": "eligible",
        "coaching_mode": CASE_MODES.get(case_id),
        "errors": [],
        "evidence_gaps": [],
        "required_model_boundaries": [],
    }


def _close(result: dict[str, Any], status: str | None = None) -> dict[str, Any]:
    result["errors"] = sorted(set(result["errors"]))
    result["evidence_gaps"] = sorted(set(result["evidence_gaps"]))
    if status is not None:
        result["status"] = status
    elif result["errors"]:
        result["status"] = "contract_conflict"
    elif result["evidence_gaps"]:
        result["status"] = "not_run"
    else:
        result["status"] = "eligible"
    return result


def _finite_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def _strict_equal(left: Any, right: Any) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(
            _strict_equal(left[key], right[key]) for key in left
        )
    if isinstance(left, list):
        return len(left) == len(right) and all(
            _strict_equal(a, b) for a, b in zip(left, right)
        )
    return left == right


def _selected_direction(bundle: dict[str, Any]) -> dict[str, Any] | None:
    decision = bundle.get("direction_decision")
    portfolio = bundle.get("direction_portfolio")
    if not isinstance(decision, dict) or not isinstance(portfolio, dict):
        return None
    selected_id = decision.get("selected_direction_id")
    directions = portfolio.get("directions")
    if not isinstance(selected_id, str) or not isinstance(directions, list):
        return None
    matches = [
        direction
        for direction in directions
        if isinstance(direction, dict) and direction.get("direction_id") == selected_id
    ]
    return matches[0] if len(matches) == 1 else None


def _selected_metrics(direction: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        metric["metric_id"]: metric
        for claim in direction.get("core_claims", [])
        if isinstance(claim, dict)
        for metric in claim.get("required_decision_metrics", [])
        if isinstance(metric, dict) and isinstance(metric.get("metric_id"), str)
    }


def _coverage(direction: dict[str, Any]) -> dict[str, dict[str, Any]]:
    decisive = direction.get("minimum_decisive_test")
    rows = decisive.get("claim_coverage", []) if isinstance(decisive, dict) else []
    return {
        row["claim_id"]: row
        for row in rows
        if isinstance(row, dict) and isinstance(row.get("claim_id"), str)
    }


def _eligible_candidates(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    source_m1 = bundle.get("source_m1_bundle")
    if not isinstance(source_m1, dict):
        return []
    round2 = source_m1.get("round2")
    pool = round2.get("candidate_pool", []) if isinstance(round2, dict) else []
    return [
        candidate
        for candidate in pool
        if isinstance(candidate, dict)
        and candidate.get("recommendation_eligible") is True
        and candidate.get("verification_status") in ELIGIBLE_STATUSES
    ]


def _direction_text(direction: dict[str, Any]) -> str:
    return json.dumps(direction, ensure_ascii=False, sort_keys=True).lower()


def _validate_receipt(
    case_id: str,
    bundle: dict[str, Any] | None,
    receipt: Any,
    result: dict[str, Any],
) -> bool:
    if not isinstance(receipt, dict):
        result["errors"].append("m2_validation_receipt_invalid")
        return False
    if receipt.get("case_id") not in {None, case_id}:
        result["errors"].append("m2_validation_case_id_mismatch")
    if receipt.get("status") == "NOT_RUN":
        if bundle is not None:
            result["errors"].append("not_run_receipt_has_input")
            return False
        if receipt.get("invocation_count") != 0:
            result["errors"].append("not_run_invocation_count_invalid")
        gaps = receipt.get("evidence_gaps")
        if not isinstance(gaps, list) or not gaps:
            result["errors"].append("not_run_evidence_gap_required")
        else:
            result["evidence_gaps"].extend(
                gap for gap in gaps if isinstance(gap, str) and gap
            )
        return False
    if receipt.get("status") != "valid" or receipt.get("errors") != [] or receipt.get(
        "evidence_gaps"
    ) != []:
        result["errors"].append("m2_validation_not_valid")
    if receipt.get("invocation_count") != 1 or receipt.get("validator") != VALIDATOR:
        result["errors"].append("m2_validation_receipt_not_one_shot")
    if bundle is not None and receipt.get("input_canonical_sha256") != canonical_sha256(
        bundle
    ):
        result["errors"].append("m2_validation_input_hash_mismatch")
    if receipt.get("source_m1_acceptance_status") != "complete":
        result["errors"].append("source_m1_not_independently_accepted")
    constructed = receipt.get("constructed_by_context")
    reviewed = receipt.get("reviewed_by_context")
    if not isinstance(constructed, str) or not constructed:
        result["errors"].append("constructed_by_context_required")
    if not isinstance(reviewed, str) or not reviewed:
        result["errors"].append("reviewed_by_context_required")
    if constructed == reviewed:
        result["errors"].append("construction_and_review_context_must_differ")
    return True


def _check_common(
    bundle: dict[str, Any], direction: dict[str, Any], result: dict[str, Any]
) -> None:
    decision = bundle.get("direction_decision")
    if not isinstance(decision, dict) or decision.get("status") != "user_confirmed":
        result["errors"].append("direction_not_user_confirmed")
    limits = direction.get("resource_limits")
    if not isinstance(limits, list) or not limits:
        result["errors"].append("resource_limits_incomplete")
    else:
        for limit in limits:
            if (
                not isinstance(limit, dict)
                or not isinstance(limit.get("constraint_id"), str)
                or limit.get("operator") not in {"<", "<="}
                or not _finite_number(limit.get("value"))
                or not isinstance(limit.get("unit"), str)
                or not limit.get("unit")
            ):
                result["errors"].append("resource_limits_incomplete")
                break
    if not _eligible_candidates(bundle):
        result["errors"].append("eligible_source_missing")

    decisive = direction.get("minimum_decisive_test")
    preconditions = (
        decisive.get("required_preconditions", [])
        if isinstance(decisive, dict)
        else []
    )
    if not isinstance(preconditions, list) or not preconditions:
        result["errors"].append("required_preconditions_missing")
    else:
        for precondition in preconditions:
            if not isinstance(precondition, dict):
                result["errors"].append("required_preconditions_invalid")
                continue
            if (
                precondition.get("blocking_if_unresolved") is True
                and precondition.get("status") not in ALLOWED_PRECONDITION_STATUSES
            ):
                result["errors"].append("blocking_precondition_unresolved")


def _check_numeric_stop_pivot(
    direction: dict[str, Any], result: dict[str, Any]
) -> None:
    metrics = _selected_metrics(direction)
    seen = {"stop": False, "pivot": False}
    for coverage in _coverage(direction).values():
        criteria = coverage.get("decision_criteria", [])
        if not isinstance(criteria, list):
            continue
        for criterion in criteria:
            if not isinstance(criterion, dict):
                continue
            criterion_type = criterion.get("criterion_type")
            metric = metrics.get(criterion.get("metric_id"))
            if criterion_type not in seen or metric is None:
                continue
            if (
                _finite_number(criterion.get("value"))
                and criterion.get("unit") == metric.get("unit")
            ):
                seen[criterion_type] = True
            else:
                result["errors"].append("numeric_stop_pivot_invalid")
    if not seen["stop"] or not seen["pivot"]:
        result["errors"].append("numeric_stop_pivot_missing")


def _check_mode(
    bundle: dict[str, Any], mode: str, result: dict[str, Any]
) -> dict[str, Any] | None:
    route = bundle.get("route_output")
    if mode == "bounded" and route is not None:
        result["errors"].append("bounded_coaching_requires_route_absent")
        return route if isinstance(route, dict) else None
    if mode == "route_specific" and not isinstance(route, dict):
        result["errors"].append("route_specific_requires_route")
        return None
    return route if isinstance(route, dict) else None


def _actual_condition_types(
    route: dict[str, Any], metric_ids: set[str]
) -> set[str]:
    return {
        kind
        for kind in ("go", "stop", "pivot")
        if any(
            isinstance(condition, dict)
            and condition.get("metric_id") in metric_ids
            for condition in route.get(f"{kind}_conditions", [])
        )
    }


def _check_route_compatibility(
    direction: dict[str, Any], route: dict[str, Any], result: dict[str, Any]
) -> None:
    metrics = _selected_metrics(direction)
    metric_ids = set(metrics)
    for kind in ("go", "stop", "pivot"):
        conditions = route.get(f"{kind}_conditions")
        if not isinstance(conditions, list) or not conditions:
            result["errors"].append("route_condition_coverage_incomplete")
            continue
        for condition in conditions:
            if not isinstance(condition, dict):
                result["errors"].append("route_condition_invalid")
                continue
            metric = metrics.get(condition.get("metric_id"))
            if metric is None:
                result["errors"].append("route_condition_metric_not_selected")
                continue
            expected_criterion_type = "success" if kind == "go" else kind
            if (
                condition.get("criterion_type") != expected_criterion_type
                or not _finite_number(condition.get("value"))
                or condition.get("unit") != metric.get("unit")
            ):
                result["errors"].append("route_condition_invalid")

    coverage = _coverage(direction)
    traces = route.get("route_traceability")
    if not isinstance(traces, list):
        result["errors"].append("route_traceability_missing")
        return
    trace_by_claim = {
        trace.get("claim_id"): trace
        for trace in traces
        if isinstance(trace, dict) and isinstance(trace.get("claim_id"), str)
    }
    if set(trace_by_claim) != set(coverage):
        result["errors"].append("route_traceability_claim_mismatch")
    for claim_id, coverage_row in coverage.items():
        trace = trace_by_claim.get(claim_id)
        if not isinstance(trace, dict):
            continue
        expected_metrics = set(coverage_row.get("metric_ids", []))
        if set(trace.get("route_metric_ids", [])) != expected_metrics:
            result["errors"].append("route_metric_traceability_mismatch")
        if set(trace.get("source_precondition_ids", [])) != set(
            coverage_row.get("required_precondition_ids", [])
        ):
            result["errors"].append("route_precondition_traceability_mismatch")
        actual_types = _actual_condition_types(route, expected_metrics)
        if actual_types != {"go", "stop", "pivot"}:
            result["errors"].append("route_condition_coverage_incomplete")
        if set(trace.get("route_condition_types", [])) != actual_types:
            result["errors"].append("route_condition_traceability_mismatch")


def _check_f01(
    bundle: dict[str, Any], direction: dict[str, Any], result: dict[str, Any]
) -> None:
    _check_mode(bundle, "bounded", result)
    claim_types = {
        claim.get("claim_type")
        for claim in direction.get("core_claims", [])
        if isinstance(claim, dict)
    }
    if not {"predictive_performance", "uncertainty_quality"}.issubset(claim_types):
        result["errors"].append("data_ml_hybrid_family_not_derivable")
    _check_numeric_stop_pivot(direction, result)


def _check_f02_or_f05(
    bundle: dict[str, Any], direction: dict[str, Any], result: dict[str, Any]
) -> dict[str, Any] | None:
    route = _check_mode(bundle, "route_specific", result)
    if route is None:
        return None
    if route.get("approved_constraint_changes") != []:
        result["errors"].append("approved_constraint_changes_must_be_empty")
    _check_route_compatibility(direction, route, result)
    return route


def _check_f03(
    bundle: dict[str, Any], direction: dict[str, Any], result: dict[str, Any]
) -> None:
    route = bundle.get("route_output")
    if not isinstance(route, dict):
        result["errors"].append("f03_route_required")
        return
    changes = route.get("approved_constraint_changes")
    if not isinstance(changes, list) or not changes:
        result["errors"].append("approved_constraint_changes_required")
    if not _strict_equal(route.get("inherited_constraints"), direction.get("resource_limits")):
        result["errors"].append("original_resource_limits_not_type_strict_equal")


def _check_f04(
    bundle: dict[str, Any], direction: dict[str, Any], result: dict[str, Any]
) -> None:
    _check_mode(bundle, "bounded", result)
    text = _direction_text(direction)
    if any(token in text for token in NUCLEAR_TOKENS):
        result["errors"].append("f04_must_be_non_nuclear")
    required_terms = (
        "measurement",
        "unit",
        "calibration",
        "repeatability",
        "reproducibility",
        "uncertainty",
    )
    if any(term not in text for term in required_terms):
        result["errors"].append("experiment_measurement_uq_family_not_derivable")
    if any(
        not isinstance(metric.get("unit"), str) or not metric.get("unit")
        for metric in _selected_metrics(direction).values()
    ):
        result["errors"].append("measurement_metric_unit_missing")
    source_m1 = bundle.get("source_m1_bundle")
    if (
        not isinstance(source_m1, dict)
        or source_m1.get("terminal_state") != "M1_COMPLETE"
        or source_m1.get("outcome") != "complete"
        or bundle.get("fixture_mode") is True
    ):
        result["errors"].append("f04_upstream_not_independently_complete")
    _check_numeric_stop_pivot(direction, result)


def _candidate_text(candidate: dict[str, Any]) -> str:
    return json.dumps(candidate, ensure_ascii=False, sort_keys=True).lower()


def _check_f05(
    bundle: dict[str, Any], direction: dict[str, Any], result: dict[str, Any]
) -> None:
    route = _check_f02_or_f05(bundle, direction, result)
    if route is None:
        return
    text = _direction_text(direction)
    padded = f" {text} "
    if not any(token in text for token in NUCLEAR_TOKENS) or not any(
        token in padded for token in ML_TOKENS
    ):
        result["errors"].append("nuclear_engineering_ml_family_not_derivable")

    decisive = direction.get("minimum_decisive_test", {})
    preconditions = decisive.get("required_preconditions", [])
    precondition_ids = {
        item.get("precondition_id")
        for item in preconditions
        if isinstance(item, dict) and isinstance(item.get("precondition_id"), str)
    }
    referenced_ids = {
        precondition_id
        for coverage in _coverage(direction).values()
        for precondition_id in coverage.get("required_precondition_ids", [])
        if isinstance(precondition_id, str)
    }
    if not precondition_ids or not precondition_ids.issubset(referenced_ids):
        result["errors"].append("target_domain_preconditions_incomplete")
    if "target" not in text and "domain" not in text:
        result["errors"].append("target_domain_preconditions_incomplete")
    if "hypothesis" not in text:
        result["errors"].append("transfer_not_preserved_as_hypothesis")

    safety_candidates = [
        candidate
        for candidate in _eligible_candidates(bundle)
        if candidate.get("verification_status") in NON_PREPRINT_STATUSES
        and candidate.get("basis_level") in {"abstract_level", "fulltext_level"}
        and any(
            token in _candidate_text(candidate)
            for token in ("safety", "reliability", "uncertainty")
        )
    ]
    if not safety_candidates:
        result["errors"].append("non_preprint_safety_source_missing")
    if not (
        "operational" in text
        and any(token in text for token in ("no plant", "exclude operational", "no operational"))
    ):
        result["errors"].append("no_operational_credit_boundary_missing")
    result["required_model_boundaries"] = list(F05_BOUNDARIES)


def audit_case(
    case_id: str,
    bundle: dict[str, Any] | None,
    validation_receipt: Any,
) -> dict[str, Any]:
    """Return one closed eligibility state without changing the supplied values."""

    result = _result(case_id)
    if case_id not in CASE_MODES:
        result["errors"].append("unknown_case_id")
        return _close(result)
    receipt_can_continue = _validate_receipt(
        case_id, bundle, validation_receipt, result
    )
    if bundle is None:
        if validation_receipt.get("status") == "NOT_RUN" and not result["errors"]:
            return _close(result, "not_run")
        result["errors"].append("m2_input_missing")
        return _close(result)
    if not isinstance(bundle, dict):
        result["errors"].append("m2_input_invalid")
        return _close(result)
    if not receipt_can_continue:
        return _close(result)

    m2_result = validate_m2_bundle(bundle)
    if m2_result.get("status") != "valid":
        result["errors"].append("m2_bundle_not_valid")
    direction = _selected_direction(bundle)
    if direction is None:
        result["errors"].append("selected_direction_missing")
        return _close(result)
    _check_common(bundle, direction, result)

    if case_id == "m3-f01":
        _check_f01(bundle, direction, result)
    elif case_id == "m3-f02":
        _check_f02_or_f05(bundle, direction, result)
    elif case_id == "m3-f03":
        _check_f03(bundle, direction, result)
    elif case_id == "m3-f04":
        _check_f04(bundle, direction, result)
    elif case_id == "m3-f05":
        _check_f05(bundle, direction, result)
    return _close(result)


def _reject_constant(_: str) -> None:
    raise ValueError("non-finite number")


def _load_object(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ValueError("utf8_bom_forbidden")
    value = json.loads(raw.decode("utf-8", errors="strict"), parse_constant=_reject_constant)
    if not isinstance(value, dict):
        raise ValueError("json_object_required")
    return value


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) != 3:
        output = _result("unknown")
        output["errors"].append("expected_case_input_receipt_paths")
        output = _close(output)
    else:
        case_id, input_name, receipt_name = arguments
        try:
            receipt = _load_object(Path(receipt_name))
            bundle = None if input_name == "-" else _load_object(Path(input_name))
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
            output = _result(case_id)
            output["errors"].append("unreadable_or_invalid_case_input")
            output = _close(output)
        else:
            output = audit_case(case_id, bundle, receipt)
    print(
        json.dumps(
            output,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    )
    return {"eligible": 0, "contract_conflict": 1, "not_run": 2}[output["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
