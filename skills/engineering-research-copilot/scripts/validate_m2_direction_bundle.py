#!/usr/bin/env python3
"""Validate one saved M2 direction-decision bundle without network access."""

from __future__ import annotations

import copy
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

from validate_m1_bundle import validate_bundle as validate_m1_bundle


SCHEMA_VERSION = "m2.1.1"
ROOT_FIELDS = {
    "source_m1_bundle",
    "direction_portfolio",
    "direction_decision",
    "route_output",
}
ROOT_OPTIONAL_FIELDS = {
    "fixture_mode",
    "evidence_class",
    "proves",
    "does_not_prove",
}
PORTFOLIO_FIELDS = {
    "schema_version",
    "source_m1_terminal_state",
    "source_m1_bundle_hash",
    "brief_version",
    "branch_id",
    "directions",
    "high_risk_ideas",
    "portfolio_status",
}
DIRECTION_FIELDS = {
    "direction_id",
    "position",
    "title",
    "evidence_tier",
    "claim_language",
    "axis_profile",
    "axis_changes",
    "core_claims",
    "resource_limits",
    "hard_gates",
    "transfer_case",
    "scorecard",
    "minimum_decisive_test",
    "supporting_candidate_ids",
    "counter_candidate_ids",
    "unknowns",
    "confidence",
    "recommendation_status",
}
FORMAL_POSITIONS = {
    "provisional_main",
    "adjacent_alternative",
    "transfer_exploration",
}
EVIDENCE_TIERS = {
    "established-in-target",
    "transfer-supported",
    "mechanism-plausible",
    "speculative",
}
CONFIDENCE_LEVELS = {"low", "medium", "high"}
HARD_GATE_FIELDS = {
    "gate_id",
    "status",
    "evidence_candidate_ids",
    "required_precondition_ids",
    "rationale",
    "blockers",
}
HARD_GATES = {
    "target_problem_evidence",
    "data_availability",
    "falsifiability",
    "resource_feasibility",
    "time_feasibility",
    "safety_ethics_compliance",
    "m1_citation_integrity",
}
TRANSFER_FIELDS = {
    "target_problem_evidence",
    "source_success_evidence",
    "transfer_compatibility",
    "anti_transfer_factors",
}
COMPATIBILITY_FIELDS = {
    "concepts",
    "units",
    "scales",
    "boundary_conditions",
    "assumptions",
}
AXIS_CHANGE_FIELDS = {"axis", "from", "to"}
AXIS_PROFILE_FIELDS = {"problem", "method", "data"}
AXES = {"problem", "method", "data"}
CORE_CLAIM_FIELDS = {
    "claim_id",
    "claim",
    "claim_type",
    "evidence_candidate_ids",
    "required_decision_metrics",
}
CLAIM_TYPES = {
    "predictive_performance",
    "uncertainty_quality",
    "open_set_detection",
    "data_availability",
    "safety",
}
DECISION_METRIC_FIELDS = {"metric_id", "metric", "metric_role", "unit"}
METRIC_ROLES = {
    "predictive_performance",
    "uncertainty_quality",
    "open_set_detection",
    "data_availability",
    "safety",
}
CLAIM_REQUIRED_METRIC_ROLE = {
    "predictive_performance": "predictive_performance",
    "uncertainty_quality": "uncertainty_quality",
    "open_set_detection": "open_set_detection",
    "data_availability": "data_availability",
    "safety": "safety",
}
RESOURCE_LIMIT_FIELDS = {
    "constraint_id",
    "resource",
    "operator",
    "value",
    "unit",
}
SCORECARD_FIELDS = {"dimensions", "weighted_total"}
SCORE_DIMENSION_FIELDS = {
    "dimension",
    "weight",
    "score",
    "evidence_candidate_ids",
    "evidence",
    "confidence",
    "unknowns",
    "change_triggers",
}
SCORE_DIMENSIONS = {
    "engineering_value",
    "gap_and_evidence_quality",
    "data_and_resource_fit",
    "validation_and_falsifiability",
    "method_maturity",
    "time_to_decisive_signal",
    "interdisciplinary_interface_quality",
    "safety_ethics_compliance",
}
DECISIVE_TEST_FIELDS = {
    "scope",
    "hypothesis",
    "inputs",
    "baseline",
    "steps",
    "primary_metric_id",
    "claim_coverage",
    "required_preconditions",
    "expected_time",
    "required_resources",
}
DECISIVE_STEP_FIELDS = {"step_id", "action", "bounded_output"}
CLAIM_COVERAGE_FIELDS = {
    "claim_id",
    "metric_ids",
    "decision_criteria",
    "required_precondition_ids",
}
CRITERION_FIELDS = {
    "criterion_type",
    "metric_id",
    "operator",
    "value",
    "unit",
}
CRITERION_TYPES = {"success", "stop", "pivot"}
PRECONDITION_FIELDS = {
    "precondition_id",
    "description",
    "gate_id",
    "status",
    "evidence_candidate_ids",
    "blocking_if_unresolved",
    "preflight_check",
    "stop_condition",
}
PRECONDITION_STATES = {"verified", "bounded_testable", "unresolved"}
THRESHOLD_FIELDS = {"metric", "operator", "value", "unit"}
THRESHOLD_OPERATORS = {">=", "<=", ">", "<"}
HIGH_RISK_FIELDS = {
    "direction_id",
    "title",
    "evidence_tier",
    "claim_language",
    "supporting_candidate_ids",
    "unknowns",
    "recommendation_status",
}
DECISION_FIELDS = {
    "selected_direction_id",
    "status",
    "permitted_next_actions",
    "confirmation_event",
}
CONFIRMATION_EVENT_FIELDS = {
    "actor_role",
    "selected_direction_id",
    "source_message_id",
    "source_message_excerpt",
    "source_message_sha256",
    "previous_bundle_hash",
}
DECISION_ACTIONS = {
    "direction_evidence_incomplete": ["modify", "reject"],
    "waiting_for_user_confirmation": ["confirm", "modify", "reject"],
    "modification_requested": ["modify", "reject"],
    "rejected": ["modify"],
    "user_confirmed": ["modify", "reject", "generate_route"],
}
ROUTE_FIELDS = {
    "selected_direction_id",
    "source_direction_hash",
    "confirmation_event_hash",
    "source_bundle_hash",
    "hypothesis",
    "baselines",
    "controls",
    "sequence",
    "inputs",
    "outputs",
    "controlled_variables",
    "confounders",
    "primary_metrics",
    "secondary_metrics",
    "minimum_meaningful_improvement",
    "uncertainty_checks",
    "sensitivity_checks",
    "validity_checks",
    "go_conditions",
    "stop_conditions",
    "pivot_conditions",
    "route_traceability",
    "source_test_mapping",
    "inherited_constraints",
    "approved_constraint_changes",
    "evidence_chain",
}
ROUTE_TEXT_FIELDS = {
    "selected_direction_id",
    "source_direction_hash",
    "confirmation_event_hash",
    "source_bundle_hash",
    "hypothesis",
    "minimum_meaningful_improvement",
}
ROUTE_TEXT_LIST_FIELDS = {
    "baselines",
    "controls",
    "sequence",
    "inputs",
    "outputs",
    "controlled_variables",
    "confounders",
    "primary_metrics",
    "secondary_metrics",
    "uncertainty_checks",
    "sensitivity_checks",
    "validity_checks",
}
ROUTE_CRITERION_FIELDS = {"go_conditions", "stop_conditions", "pivot_conditions"}
ROUTE_TRACE_FIELDS = {
    "claim_id",
    "route_metric_ids",
    "source_precondition_ids",
    "route_condition_types",
}
ROUTE_CONDITION_TYPES = {"go", "stop", "pivot"}
SOURCE_TEST_MAPPING_FIELDS = {
    "claim_id",
    "minimum_test_metric_ids",
    "route_metric_ids",
}
APPROVED_CONSTRAINT_CHANGE_FIELDS = {
    "constraint_id",
    "previous_value",
    "approved_value",
    "unit",
    "approval_message_id",
    "approval_message_sha256",
}
EVIDENCE_CHAIN_FIELDS = {"design", "data", "analysis", "result", "claim"}
TIER_LANGUAGE = {
    "established-in-target": "Direct evidence supports applicability",
    "transfer-supported": "Recommended for priority validation",
    "mechanism-plausible": "Divergent exploration suggestion",
    "speculative": "High-uncertainty idea",
}
ELIGIBLE_M1_STATES = {"verified_primary", "verified_registry", "verified_preprint"}
BLOCKED_M1_STATES = {"partial", "conflicted", "not_found", "manual_needed"}
PROHIBITED_PRECONFIRMATION_KEYS = {
    "experiment_steps",
    "full_experiment_steps",
    "simulation_route",
    "full_simulation_route",
    "training_plan",
    "model_download",
    "service_deployment",
    "large_scale_resource_execution",
}


class _Result:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.evidence_gaps: list[str] = []

    def error(self, code: str) -> None:
        if code not in self.errors:
            self.errors.append(code)

    def gap(self, code: str) -> None:
        if code not in self.evidence_gaps:
            self.evidence_gaps.append(code)

    def closed(self) -> dict:
        if self.errors:
            status = "invalid"
        elif self.evidence_gaps:
            status = "evidence_incomplete"
        else:
            status = "valid"
        return {
            "status": status,
            "errors": self.errors,
            "evidence_gaps": self.evidence_gaps,
        }


def _nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _finite_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def _nonempty_text_list(value: Any) -> bool:
    return (
        isinstance(value, list)
        and bool(value)
        and all(_nonempty_text(item) for item in value)
    )


def _text_list(value: Any) -> bool:
    return isinstance(value, list) and all(_nonempty_text(item) for item in value)


def canonical_sha256(value: Any) -> str:
    """Hash canonical UTF-8 JSON and reject non-finite numeric values."""

    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _valid_sha256(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _validate_closed_fields(
    value: Any,
    required: set[str],
    result: _Result,
    invalid_code: str,
    unknown_code: str,
    optional: set[str] | None = None,
) -> dict:
    if not isinstance(value, dict):
        result.error(invalid_code)
        return {}
    allowed = required | (optional or set())
    if not required.issubset(value):
        result.error(invalid_code)
    if set(value) - allowed:
        result.error(unknown_code)
    return value


def _m1_candidate_index(source: dict) -> dict[str, dict]:
    round_two = source.get("round2")
    if not isinstance(round_two, dict):
        return {}
    pool = round_two.get("candidate_pool")
    if not isinstance(pool, list):
        return {}
    index: dict[str, dict] = {}
    for candidate in pool:
        if not isinstance(candidate, dict):
            continue
        candidate_id = candidate.get("candidate_id")
        if _nonempty_text(candidate_id) and candidate_id not in index:
            index[candidate_id] = candidate
    return index


def _candidate_is_eligible(candidate: dict, fixture_mode: bool) -> bool:
    status = candidate.get("verification_status")
    if candidate.get("recommendation_eligible") is not True:
        return False
    if status in BLOCKED_M1_STATES:
        return False
    return status == "fixture_only" if fixture_mode else status in ELIGIBLE_M1_STATES


def _candidate_is_non_preprint_support(candidate: dict, fixture_mode: bool) -> bool:
    if candidate.get("recommendation_eligible") is not True:
        return False
    status = candidate.get("verification_status")
    if status in BLOCKED_M1_STATES or status == "verified_preprint":
        return False
    return status == "fixture_only" if fixture_mode else status in {
        "verified_primary",
        "verified_registry",
    }


def _validate_candidate_ids(
    value: Any,
    index: dict[str, dict],
    fixture_mode: bool,
    result: _Result,
    *,
    require_nonempty: bool,
) -> list[str]:
    if not isinstance(value, list) or any(not _nonempty_text(item) for item in value):
        result.error("invalid_m1_candidate_ids")
        return []
    if require_nonempty and not value:
        result.error("missing_m1_candidate_ids")
    if len(set(value)) != len(value):
        result.error("duplicate_m1_candidate_id_reference")
    for candidate_id in value:
        candidate = index.get(candidate_id)
        if candidate is None:
            result.error("unknown_m1_candidate_id")
        elif not _candidate_is_eligible(candidate, fixture_mode):
            result.error("blocked_m1_candidate")
    return value


def _validate_source(
    bundle: dict, portfolio: dict, fixture_mode: bool, result: _Result
) -> tuple[dict, dict[str, dict]]:
    source = bundle.get("source_m1_bundle")
    if not isinstance(source, dict):
        result.error("invalid_source_m1_bundle")
        return {}, {}

    source_result = validate_m1_bundle(source)
    if source_result.get("status") != "valid":
        result.error("invalid_source_m1_bundle")
    if not (
        source.get("schema_version") == "m1.2"
        and source.get("terminal_state") == "M1_COMPLETE"
        and source.get("stopped_after_round") == 2
        and source.get("outcome") == "complete"
    ):
        result.error("source_m1_not_complete")

    try:
        expected_hash = canonical_sha256(source)
    except (TypeError, ValueError):
        result.error("invalid_source_m1_bundle")
    else:
        if portfolio.get("source_m1_bundle_hash") != expected_hash:
            result.error("source_m1_bundle_hash_mismatch")

    if portfolio.get("source_m1_terminal_state") != source.get("terminal_state"):
        result.error("source_m1_terminal_state_mismatch")

    round_two = source.get("round2") if isinstance(source.get("round2"), dict) else {}
    brief = (
        round_two.get("research_brief")
        if isinstance(round_two.get("research_brief"), dict)
        else {}
    )
    plan = (
        round_two.get("search_plan")
        if isinstance(round_two.get("search_plan"), dict)
        else {}
    )
    if portfolio.get("brief_version") != brief.get("brief_version"):
        result.error("m1_brief_version_mismatch")
    if (
        portfolio.get("branch_id") != brief.get("branch_id")
        or portfolio.get("branch_id") != plan.get("branch_id")
    ):
        result.error("m1_branch_id_mismatch")

    index = _m1_candidate_index(source)
    if not index:
        result.error("missing_m1_candidate_ledger")
    return source, index


def _validate_hard_gates(
    value: Any,
    index: dict[str, dict],
    fixture_mode: bool,
    preconditions: dict[str, dict],
    result: _Result,
) -> bool:
    if not isinstance(value, list):
        result.error("invalid_hard_gates")
        return True
    seen: set[str] = set()
    any_failed = False
    for raw_gate in value:
        gate = _validate_closed_fields(
            raw_gate,
            HARD_GATE_FIELDS,
            result,
            "invalid_hard_gate",
            "unknown_hard_gate_fields",
        )
        gate_id = gate.get("gate_id")
        if gate_id not in HARD_GATES:
            result.error("invalid_hard_gate_id")
        elif gate_id in seen:
            result.error("duplicate_hard_gate_id")
        else:
            seen.add(gate_id)
        status = gate.get("status")
        if status not in {"pass", "fail"}:
            result.error("invalid_hard_gate_status")
        if not _nonempty_text(gate.get("rationale")):
            result.error("invalid_hard_gate_rationale")
        candidate_ids = _validate_candidate_ids(
            gate.get("evidence_candidate_ids"),
            index,
            fixture_mode,
            result,
            require_nonempty=gate_id
            in {"target_problem_evidence", "m1_citation_integrity"},
        )
        required_preconditions = gate.get("required_precondition_ids")
        if not _text_list(required_preconditions) or len(set(required_preconditions)) != len(
            required_preconditions or []
        ):
            result.error("invalid_hard_gate_precondition_ids")
            required_preconditions = []
        for precondition_id in required_preconditions:
            if precondition_id not in preconditions:
                result.error("unknown_hard_gate_precondition_id")
        unresolved_blocking = [
            item
            for item in preconditions.values()
            if item.get("gate_id") == gate_id
            and item.get("status") == "unresolved"
            and item.get("blocking_if_unresolved") is True
        ]
        if status == "pass" and unresolved_blocking:
            result.error("unresolved_blocking_precondition_passed_gate")
        if gate_id == "safety_ethics_compliance" and status == "pass" and candidate_ids:
            if not any(
                _candidate_is_non_preprint_support(index[candidate_id], fixture_mode)
                for candidate_id in candidate_ids
                if candidate_id in index
            ):
                result.error("safety_gate_requires_non_preprint_support")
        blockers = gate.get("blockers")
        if not _text_list(blockers):
            result.error("invalid_hard_gate_blockers")
        if status == "pass" and blockers:
            result.error("passing_hard_gate_has_blockers")
        if status == "fail":
            any_failed = True
            if not blockers:
                result.error("failed_hard_gate_without_blocker")
            if gate_id in HARD_GATES:
                result.gap(gate_id)
        if gate_id == "target_problem_evidence" and not candidate_ids:
            result.error("target_problem_gate_without_m1_evidence")
    if seen != HARD_GATES:
        result.error("invalid_hard_gate_set")
    return any_failed


def _validate_axis_profile(value: Any, result: _Result) -> dict:
    profile = _validate_closed_fields(
        value,
        AXIS_PROFILE_FIELDS,
        result,
        "invalid_axis_profile",
        "unknown_axis_profile_fields",
    )
    for field in AXIS_PROFILE_FIELDS:
        if not _nonempty_text(profile.get(field)):
            result.error("invalid_axis_profile_value")
    return profile


def _validate_axis_changes(value: Any, result: _Result) -> list[dict]:
    if not isinstance(value, list):
        result.error("invalid_axis_changes")
        return []
    axes: list[str] = []
    for raw_change in value:
        change = _validate_closed_fields(
            raw_change,
            AXIS_CHANGE_FIELDS,
            result,
            "invalid_axis_change",
            "unknown_axis_change_fields",
        )
        axis = change.get("axis")
        if axis not in AXES:
            result.error("invalid_axis")
        else:
            axes.append(axis)
        before = change.get("from")
        after = change.get("to")
        if not _nonempty_text(before) or not _nonempty_text(after):
            result.error("invalid_axis_change_value")
        elif before.strip().casefold() == after.strip().casefold():
            result.error("axis_change_has_no_change")
    if len(set(axes)) != len(axes):
        result.error("duplicate_axis_change")
    return value


def _validate_axis_binding(
    direction: dict, main_profile: dict, result: _Result
) -> None:
    position = direction.get("position")
    profile = direction.get("axis_profile")
    changes = direction.get("axis_changes")
    if not isinstance(profile, dict) or not isinstance(changes, list):
        return
    expected = [
        {
            "axis": axis,
            "from": main_profile.get(axis),
            "to": profile.get(axis),
        }
        for axis in sorted(AXES)
        if _nonempty_text(main_profile.get(axis))
        and _nonempty_text(profile.get(axis))
        and main_profile[axis].strip().casefold() != profile[axis].strip().casefold()
    ]
    actual = sorted(
        (
            change.get("axis"),
            change.get("from"),
            change.get("to"),
        )
        for change in changes
        if isinstance(change, dict)
    )
    derived = sorted((item["axis"], item["from"], item["to"]) for item in expected)
    if actual != derived:
        result.error("axis_changes_do_not_match_profiles")
    if position == "provisional_main" and (changes or expected):
        result.error("main_direction_must_define_baseline_axes")
    elif position == "adjacent_alternative" and (
        len(changes) != 1 or len(expected) != 1
    ):
        result.error("adjacent_requires_one_axis_change")
    elif position == "transfer_exploration" and (
        len({item.get("axis") for item in changes if isinstance(item, dict)}) < 2
        or len(expected) < 2
    ):
        result.error("transfer_requires_two_axis_changes")


def _validate_transfer_case(
    value: Any,
    index: dict[str, dict],
    fixture_mode: bool,
    result: _Result,
) -> None:
    transfer = _validate_closed_fields(
        value,
        TRANSFER_FIELDS,
        result,
        "invalid_transfer_case",
        "unknown_transfer_case_fields",
    )
    _validate_candidate_ids(
        transfer.get("target_problem_evidence"),
        index,
        fixture_mode,
        result,
        require_nonempty=True,
    )
    _validate_candidate_ids(
        transfer.get("source_success_evidence"),
        index,
        fixture_mode,
        result,
        require_nonempty=True,
    )
    compatibility = _validate_closed_fields(
        transfer.get("transfer_compatibility"),
        COMPATIBILITY_FIELDS,
        result,
        "invalid_transfer_compatibility",
        "unknown_transfer_compatibility_fields",
    )
    for field in sorted(COMPATIBILITY_FIELDS):
        if not _nonempty_text_list(compatibility.get(field)):
            result.error(f"missing_transfer_compatibility_{field}")
    if not _nonempty_text_list(transfer.get("anti_transfer_factors")):
        result.error("missing_anti_transfer_factors")


def _validate_core_claims(
    value: Any,
    index: dict[str, dict],
    fixture_mode: bool,
    result: _Result,
) -> tuple[dict[str, dict], dict[str, dict]]:
    if not isinstance(value, list) or not value:
        result.error("invalid_core_claims")
        return {}, {}
    claims: dict[str, dict] = {}
    metrics: dict[str, dict] = {}
    for raw_claim in value:
        claim = _validate_closed_fields(
            raw_claim,
            CORE_CLAIM_FIELDS,
            result,
            "invalid_core_claim",
            "unknown_core_claim_fields",
        )
        claim_id = claim.get("claim_id")
        claim_type = claim.get("claim_type")
        if not _nonempty_text(claim_id):
            result.error("invalid_core_claim_id")
            continue
        if claim_id in claims:
            result.error("duplicate_core_claim_id")
        else:
            claims[claim_id] = claim
        if not _nonempty_text(claim.get("claim")):
            result.error("invalid_core_claim_text")
        if claim_type not in CLAIM_TYPES:
            result.error("invalid_core_claim_type")
        _validate_candidate_ids(
            claim.get("evidence_candidate_ids"),
            index,
            fixture_mode,
            result,
            require_nonempty=True,
        )
        raw_metrics = claim.get("required_decision_metrics")
        if not isinstance(raw_metrics, list) or not raw_metrics:
            result.error("missing_core_claim_metrics")
            continue
        claim_roles: set[str] = set()
        for raw_metric in raw_metrics:
            metric = _validate_closed_fields(
                raw_metric,
                DECISION_METRIC_FIELDS,
                result,
                "invalid_decision_metric",
                "unknown_decision_metric_fields",
            )
            metric_id = metric.get("metric_id")
            if not all(
                _nonempty_text(metric.get(field))
                for field in ("metric_id", "metric", "unit")
            ):
                result.error("invalid_decision_metric")
                continue
            if metric_id in metrics:
                result.error("duplicate_decision_metric_id")
            else:
                metrics[metric_id] = metric
            role = metric.get("metric_role")
            if role not in METRIC_ROLES:
                result.error("invalid_decision_metric_role")
            else:
                claim_roles.add(role)
        required_role = CLAIM_REQUIRED_METRIC_ROLE.get(claim_type)
        if required_role not in claim_roles:
            error = {
                "uncertainty_quality": "uncertainty_claim_requires_uncertainty_metric",
                "open_set_detection": "open_set_claim_requires_open_set_metric",
                "data_availability": "data_claim_requires_data_metric",
                "safety": "safety_claim_requires_safety_metric",
                "predictive_performance": "predictive_claim_requires_predictive_metric",
            }.get(claim_type, "core_claim_missing_required_metric_role")
            result.error(error)
    return claims, metrics


def _validate_resource_limits(value: Any, result: _Result) -> list[dict]:
    if not isinstance(value, list) or not value:
        result.error("invalid_resource_limits")
        return []
    seen: set[str] = set()
    limits: list[dict] = []
    for raw_limit in value:
        limit = _validate_closed_fields(
            raw_limit,
            RESOURCE_LIMIT_FIELDS,
            result,
            "invalid_resource_limit",
            "unknown_resource_limit_fields",
        )
        constraint_id = limit.get("constraint_id")
        if not _nonempty_text(constraint_id) or constraint_id in seen:
            result.error("invalid_resource_constraint_id")
        else:
            seen.add(constraint_id)
        if (
            not _nonempty_text(limit.get("resource"))
            or limit.get("operator") not in THRESHOLD_OPERATORS
            or not _finite_number(limit.get("value"))
            or not _nonempty_text(limit.get("unit"))
        ):
            result.error("invalid_resource_limit")
        limits.append(limit)
    return limits


def _validate_scorecard(
    value: Any,
    index: dict[str, dict],
    fixture_mode: bool,
    result: _Result,
) -> dict[str, int] | None:
    scorecard = _validate_closed_fields(
        value,
        SCORECARD_FIELDS,
        result,
        "invalid_scorecard",
        "unknown_scorecard_fields",
    )
    dimensions = scorecard.get("dimensions")
    if not isinstance(dimensions, list):
        result.error("invalid_scorecard_dimensions")
        return None
    weights: dict[str, int] = {}
    rationale_fingerprints: set[tuple[str, tuple[str, ...], tuple[str, ...]]] = set()
    computed_total = 0.0
    all_numeric = True
    for raw_dimension in dimensions:
        item = _validate_closed_fields(
            raw_dimension,
            SCORE_DIMENSION_FIELDS,
            result,
            "invalid_score_dimension",
            "unknown_score_dimension_fields",
        )
        name = item.get("dimension")
        if name not in SCORE_DIMENSIONS:
            result.error("invalid_score_dimension_name")
        elif name in weights:
            result.error("duplicate_score_dimension")
        weight = item.get("weight")
        if not isinstance(weight, int) or isinstance(weight, bool) or weight < 0:
            result.error("invalid_score_weight")
            all_numeric = False
        elif name in SCORE_DIMENSIONS:
            weights[name] = weight
        score = item.get("score")
        if not isinstance(score, int) or isinstance(score, bool) or not 0 <= score <= 5:
            result.error("score_out_of_range")
            all_numeric = False
        if isinstance(weight, int) and not isinstance(weight, bool) and isinstance(score, int) and not isinstance(score, bool):
            computed_total += score * weight / 5
        _validate_candidate_ids(
            item.get("evidence_candidate_ids"),
            index,
            fixture_mode,
            result,
            require_nonempty=False,
        )
        if not _nonempty_text(item.get("evidence")):
            result.error("missing_score_evidence")
        if item.get("confidence") not in CONFIDENCE_LEVELS:
            result.error("invalid_score_confidence")
        if not _nonempty_text_list(item.get("unknowns")):
            result.error("missing_score_unknowns")
        if not _nonempty_text_list(item.get("change_triggers")):
            result.error("missing_score_change_triggers")
        if (
            _nonempty_text(item.get("evidence"))
            and _nonempty_text_list(item.get("unknowns"))
            and _nonempty_text_list(item.get("change_triggers"))
        ):
            fingerprint = (
                item["evidence"].strip().casefold(),
                tuple(sorted(text.strip().casefold() for text in item["unknowns"])),
                tuple(
                    sorted(text.strip().casefold() for text in item["change_triggers"])
                ),
            )
            if fingerprint in rationale_fingerprints:
                result.error("duplicate_score_dimension_rationale")
            rationale_fingerprints.add(fingerprint)
    if set(weights) != SCORE_DIMENSIONS:
        result.error("invalid_score_dimension_set")
    if sum(weights.values()) != 100:
        result.error("scorecard_weights_do_not_total_100")
    total = scorecard.get("weighted_total")
    if not _finite_number(total) or not 0 <= total <= 100:
        result.error("invalid_weighted_total")
    elif all_numeric and not math.isclose(total, computed_total, abs_tol=1e-9):
        result.error("weighted_total_mismatch")
    return weights if set(weights) == SCORE_DIMENSIONS else None


def _validate_threshold(value: Any, name: str, result: _Result) -> None:
    if not isinstance(value, dict) or set(value) != THRESHOLD_FIELDS:
        result.error(f"invalid_{name}")
        return
    if (
        not _nonempty_text(value.get("metric"))
        or value.get("operator") not in THRESHOLD_OPERATORS
        or not _finite_number(value.get("value"))
        or not _nonempty_text(value.get("unit"))
    ):
        result.error(f"invalid_{name}")


def _validate_criterion(
    value: Any, result: _Result, invalid_code: str
) -> dict:
    criterion = _validate_closed_fields(
        value,
        CRITERION_FIELDS,
        result,
        invalid_code,
        "unknown_decision_criterion_fields",
    )
    if (
        criterion.get("criterion_type") not in CRITERION_TYPES
        or not _nonempty_text(criterion.get("metric_id"))
        or criterion.get("operator") not in THRESHOLD_OPERATORS
        or not _finite_number(criterion.get("value"))
        or not _nonempty_text(criterion.get("unit"))
    ):
        result.error(invalid_code)
    return criterion


def _validate_preconditions(
    value: Any,
    index: dict[str, dict],
    fixture_mode: bool,
    result: _Result,
) -> dict[str, dict]:
    if not isinstance(value, list) or not value:
        result.error("invalid_required_preconditions")
        return {}
    preconditions: dict[str, dict] = {}
    for raw_precondition in value:
        precondition = _validate_closed_fields(
            raw_precondition,
            PRECONDITION_FIELDS,
            result,
            "invalid_precondition",
            "unknown_precondition_fields",
        )
        precondition_id = precondition.get("precondition_id")
        if not _nonempty_text(precondition_id) or precondition_id in preconditions:
            result.error("invalid_precondition_id")
        else:
            preconditions[precondition_id] = precondition
        if not _nonempty_text(precondition.get("description")):
            result.error("invalid_precondition_description")
        if precondition.get("gate_id") not in HARD_GATES:
            result.error("invalid_precondition_gate_id")
        if precondition.get("status") not in PRECONDITION_STATES:
            result.error("invalid_precondition_status")
        if not isinstance(precondition.get("blocking_if_unresolved"), bool):
            result.error("invalid_precondition_blocking_flag")
        if not _nonempty_text(precondition.get("preflight_check")):
            result.error("invalid_precondition_preflight_check")
        _validate_candidate_ids(
            precondition.get("evidence_candidate_ids"),
            index,
            fixture_mode,
            result,
            require_nonempty=False,
        )
        _validate_threshold(
            precondition.get("stop_condition"),
            "precondition_stop_condition",
            result,
        )
    return preconditions


def _validate_decisive_test(
    value: Any,
    claims: dict[str, dict],
    metrics: dict[str, dict],
    index: dict[str, dict],
    fixture_mode: bool,
    result: _Result,
) -> dict[str, dict]:
    test = _validate_closed_fields(
        value,
        DECISIVE_TEST_FIELDS,
        result,
        "invalid_minimum_decisive_test",
        "unknown_minimum_decisive_test_fields",
    )
    if test.get("scope") != "minimum_decisive_test":
        result.error("invalid_decisive_test_scope")
    for field in ("hypothesis", "baseline", "primary_metric_id", "expected_time"):
        if not _nonempty_text(test.get(field)):
            result.error(f"invalid_decisive_test_{field}")
    if test.get("primary_metric_id") not in metrics:
        result.error("unknown_decisive_test_primary_metric_id")
    for field in ("inputs", "required_resources"):
        if not _nonempty_text_list(test.get(field)):
            result.error(f"invalid_decisive_test_{field}")
    steps = test.get("steps")
    if not isinstance(steps, list) or not 2 <= len(steps) <= 4:
        result.error("invalid_decisive_test_step_count")
        steps = [] if not isinstance(steps, list) else steps
    step_ids: set[str] = set()
    for raw_step in steps:
        step = _validate_closed_fields(
            raw_step,
            DECISIVE_STEP_FIELDS,
            result,
            "invalid_decisive_test_step",
            "unknown_decisive_test_step_fields",
        )
        step_id = step.get("step_id")
        if not _nonempty_text(step_id) or step_id in step_ids:
            result.error("invalid_decisive_test_step")
        else:
            step_ids.add(step_id)
        for field in ("action", "bounded_output"):
            if not _nonempty_text(step.get(field)):
                result.error("invalid_decisive_test_step")
            elif len(step[field].encode("utf-8")) > 500:
                result.error("decisive_test_step_too_large")
    try:
        if len(
            json.dumps(test, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
                "utf-8"
            )
        ) > 6000:
            result.error("decisive_test_too_large")
    except (TypeError, ValueError):
        result.error("invalid_minimum_decisive_test")

    preconditions = _validate_preconditions(
        test.get("required_preconditions"), index, fixture_mode, result
    )
    coverage = test.get("claim_coverage")
    if not isinstance(coverage, list) or not coverage:
        result.error("invalid_claim_coverage")
        coverage = []
    covered_claims: set[str] = set()
    for raw_item in coverage:
        item = _validate_closed_fields(
            raw_item,
            CLAIM_COVERAGE_FIELDS,
            result,
            "invalid_claim_coverage_item",
            "unknown_claim_coverage_fields",
        )
        claim_id = item.get("claim_id")
        if claim_id not in claims:
            result.error("unknown_claim_coverage_id")
            continue
        if claim_id in covered_claims:
            result.error("duplicate_claim_coverage")
        covered_claims.add(claim_id)
        metric_ids = item.get("metric_ids")
        expected_metric_ids = {
            metric.get("metric_id")
            for metric in claims[claim_id].get("required_decision_metrics", [])
            if isinstance(metric, dict)
        }
        if (
            not _nonempty_text_list(metric_ids)
            or set(metric_ids) != expected_metric_ids
            or len(metric_ids) != len(set(metric_ids))
        ):
            result.error("claim_metric_coverage_mismatch")
        criteria = item.get("decision_criteria")
        if not isinstance(criteria, list) or not criteria:
            result.error("invalid_claim_decision_criteria")
            criteria = []
        criterion_metrics: set[str] = set()
        for raw_criterion in criteria:
            criterion = _validate_criterion(
                raw_criterion, result, "invalid_claim_decision_criterion"
            )
            metric_id = criterion.get("metric_id")
            if metric_id not in expected_metric_ids:
                result.error("claim_decision_criterion_metric_mismatch")
            else:
                criterion_metrics.add(metric_id)
        if criterion_metrics != expected_metric_ids:
            result.error("claim_metric_without_numeric_criterion")
        required_precondition_ids = item.get("required_precondition_ids")
        if not _text_list(required_precondition_ids) or len(
            set(required_precondition_ids or [])
        ) != len(required_precondition_ids or []):
            result.error("invalid_claim_precondition_ids")
            required_precondition_ids = []
        if any(item_id not in preconditions for item_id in required_precondition_ids):
            result.error("unknown_claim_precondition_id")
        if claims[claim_id].get("claim_type") == "data_availability" and not required_precondition_ids:
            result.error("data_claim_requires_precondition")
    if covered_claims != set(claims):
        result.error("core_claim_without_test_coverage")
    return preconditions


def _validate_direction(
    value: Any,
    index: dict[str, dict],
    fixture_mode: bool,
    result: _Result,
) -> tuple[str | None, str | None, str | None, bool, dict[str, int] | None]:
    direction = _validate_closed_fields(
        value,
        DIRECTION_FIELDS,
        result,
        "invalid_direction",
        "unknown_direction_fields",
    )
    direction_id = direction.get("direction_id")
    position = direction.get("position")
    title = direction.get("title")
    tier = direction.get("evidence_tier")
    if not _nonempty_text(direction_id):
        result.error("invalid_direction_id")
        direction_id = None
    if position not in FORMAL_POSITIONS:
        result.error("invalid_formal_position")
    if not _nonempty_text(title):
        result.error("invalid_direction_title")
        title = None
    if tier not in EVIDENCE_TIERS:
        result.error("invalid_evidence_tier")
    allowed_tiers = {
        "provisional_main": {"established-in-target", "transfer-supported"},
        "adjacent_alternative": {"established-in-target", "transfer-supported"},
        "transfer_exploration": {
            "established-in-target",
            "transfer-supported",
            "mechanism-plausible",
        },
    }
    if tier not in allowed_tiers.get(position, set()):
        result.error("invalid_tier_for_formal_position")
    if direction.get("claim_language") != TIER_LANGUAGE.get(tier):
        result.error("evidence_tier_language_mismatch")
    confidence = direction.get("confidence")
    if confidence not in CONFIDENCE_LEVELS:
        result.error("invalid_direction_confidence")
    if tier == "transfer-supported" and confidence == "high":
        result.error("transfer_supported_confidence_too_high")

    _validate_axis_profile(direction.get("axis_profile"), result)
    _validate_axis_changes(direction.get("axis_changes"), result)
    claims, metrics = _validate_core_claims(
        direction.get("core_claims"), index, fixture_mode, result
    )
    _validate_resource_limits(direction.get("resource_limits"), result)
    preconditions = _validate_decisive_test(
        direction.get("minimum_decisive_test"),
        claims,
        metrics,
        index,
        fixture_mode,
        result,
    )
    hard_gate_failed = _validate_hard_gates(
        direction.get("hard_gates"), index, fixture_mode, preconditions, result
    )
    _validate_transfer_case(direction.get("transfer_case"), index, fixture_mode, result)
    _validate_candidate_ids(
        direction.get("supporting_candidate_ids"),
        index,
        fixture_mode,
        result,
        require_nonempty=True,
    )
    _validate_candidate_ids(
        direction.get("counter_candidate_ids"),
        index,
        fixture_mode,
        result,
        require_nonempty=True,
    )
    if not _nonempty_text_list(direction.get("unknowns")):
        result.error("missing_direction_unknowns")
    if position == "provisional_main":
        supporting_ids = direction.get("supporting_candidate_ids")
        if isinstance(supporting_ids, list) and not any(
            candidate_id in index
            and _candidate_is_non_preprint_support(index[candidate_id], fixture_mode)
            for candidate_id in supporting_ids
        ):
            result.error("provisional_main_requires_non_preprint_support")

    score_weights: dict[str, int] | None = None
    if hard_gate_failed:
        if direction.get("scorecard") is not None:
            result.error("failed_hard_gate_has_scorecard")
        if direction.get("recommendation_status") != "excluded":
            result.error("failed_hard_gate_ranked")
    else:
        if direction.get("recommendation_status") != "provisional":
            result.error("passing_direction_not_provisional")
        score_weights = _validate_scorecard(
            direction.get("scorecard"), index, fixture_mode, result
        )
    return direction_id, position, title, hard_gate_failed, score_weights


def _validate_high_risk_ideas(
    value: Any,
    index: dict[str, dict],
    fixture_mode: bool,
    formal_ids: set[str],
    result: _Result,
) -> None:
    if not isinstance(value, list):
        result.error("invalid_high_risk_ideas")
        return
    if len(value) > 2:
        result.error("too_many_high_risk_ideas")
    seen = set(formal_ids)
    for raw_idea in value:
        idea = _validate_closed_fields(
            raw_idea,
            HIGH_RISK_FIELDS,
            result,
            "invalid_high_risk_idea",
            "unknown_high_risk_idea_fields",
        )
        idea_id = idea.get("direction_id")
        valid = True
        if not _nonempty_text(idea_id) or idea_id in seen:
            valid = False
        else:
            seen.add(idea_id)
        if not _nonempty_text(idea.get("title")):
            valid = False
        if idea.get("evidence_tier") != "speculative":
            valid = False
        if idea.get("claim_language") != TIER_LANGUAGE["speculative"]:
            valid = False
        if idea.get("recommendation_status") != "unranked_high_risk":
            valid = False
        if not _nonempty_text_list(idea.get("unknowns")):
            valid = False
        _validate_candidate_ids(
            idea.get("supporting_candidate_ids"),
            index,
            fixture_mode,
            result,
            require_nonempty=True,
        )
        if not valid:
            result.error("invalid_high_risk_idea")


def _validate_portfolio(
    portfolio: dict,
    index: dict[str, dict],
    fixture_mode: bool,
    result: _Result,
) -> tuple[dict[str, dict], bool]:
    if portfolio.get("schema_version") != SCHEMA_VERSION:
        result.error("invalid_schema_version")
    directions = portfolio.get("directions")
    if not isinstance(directions, list):
        result.error("invalid_directions")
        directions = []
    if len(directions) != 3:
        result.error("invalid_formal_direction_count")
    ids: list[str] = []
    positions: list[str] = []
    titles: list[str] = []
    any_failed = False
    weight_profiles: list[dict[str, int]] = []
    for direction in directions:
        direction_id, position, title, failed, weights = _validate_direction(
            direction, index, fixture_mode, result
        )
        if direction_id is not None:
            ids.append(direction_id)
        if position is not None:
            positions.append(position)
        if title is not None:
            titles.append(title.strip().casefold())
        any_failed = any_failed or failed
        if weights is not None:
            weight_profiles.append(weights)
    if len(set(ids)) != len(ids):
        result.error("duplicate_direction_id")
    if set(positions) != FORMAL_POSITIONS or len(positions) != 3:
        result.error("invalid_formal_positions")
    if len(set(titles)) != len(titles):
        result.error("duplicate_direction_title")
    if weight_profiles and any(profile != weight_profiles[0] for profile in weight_profiles[1:]):
        result.error("scorecard_weight_profiles_differ")

    main_direction = next(
        (
            direction
            for direction in directions
            if isinstance(direction, dict)
            and direction.get("position") == "provisional_main"
        ),
        None,
    )
    main_profile = (
        main_direction.get("axis_profile")
        if isinstance(main_direction, dict)
        and isinstance(main_direction.get("axis_profile"), dict)
        else {}
    )
    for direction in directions:
        if isinstance(direction, dict):
            _validate_axis_binding(direction, main_profile, result)

    formal_ids = set(ids)
    _validate_high_risk_ideas(
        portfolio.get("high_risk_ideas"), index, fixture_mode, formal_ids, result
    )
    status = portfolio.get("portfolio_status")
    if status not in {"provisional", "evidence_incomplete"}:
        result.error("invalid_portfolio_status")
    if any_failed and status == "provisional":
        result.error("incomplete_portfolio_marked_provisional")
    if not any_failed and status == "evidence_incomplete":
        result.error("complete_portfolio_marked_incomplete")
    return {
        direction.get("direction_id"): direction
        for direction in directions
        if isinstance(direction, dict) and _nonempty_text(direction.get("direction_id"))
    }, any_failed


def _validate_route_output(
    value: Any,
    selected_direction_id: str,
    selected_direction: dict,
    confirmation_event: dict,
    root: dict,
    result: _Result,
) -> None:
    route = _validate_closed_fields(
        value,
        ROUTE_FIELDS,
        result,
        "invalid_route_output",
        "unknown_route_output_fields",
    )
    if route.get("selected_direction_id") != selected_direction_id:
        result.error("route_selected_direction_mismatch")
    try:
        expected_direction_hash = canonical_sha256(selected_direction)
        expected_event_hash = canonical_sha256(confirmation_event)
        confirmed_bundle = copy.deepcopy(root)
        confirmed_bundle["route_output"] = None
        expected_bundle_hash = canonical_sha256(confirmed_bundle)
    except (TypeError, ValueError):
        result.error("invalid_route_hash_source")
        expected_direction_hash = expected_event_hash = expected_bundle_hash = None
    if (
        not _valid_sha256(route.get("source_direction_hash"))
        or route.get("source_direction_hash") != expected_direction_hash
    ):
        result.error("route_source_direction_hash_mismatch")
    if (
        not _valid_sha256(route.get("confirmation_event_hash"))
        or route.get("confirmation_event_hash") != expected_event_hash
    ):
        result.error("route_confirmation_event_hash_mismatch")
    if (
        not _valid_sha256(route.get("source_bundle_hash"))
        or route.get("source_bundle_hash") != expected_bundle_hash
    ):
        result.error("route_source_bundle_hash_mismatch")
    for field in ROUTE_TEXT_FIELDS:
        if not _nonempty_text(route.get(field)):
            result.error(f"empty_route_output_{field}")
    for field in ROUTE_TEXT_LIST_FIELDS:
        if not _nonempty_text_list(route.get(field)):
            result.error(f"empty_route_output_{field}")

    expected_criterion_type = {
        "go_conditions": "success",
        "stop_conditions": "stop",
        "pivot_conditions": "pivot",
    }
    condition_metric_ids: dict[str, set[str]] = {}
    for field in ROUTE_CRITERION_FIELDS:
        raw_conditions = route.get(field)
        if not isinstance(raw_conditions, list) or not raw_conditions:
            result.error(f"empty_route_output_{field}")
            raw_conditions = []
        metric_ids: set[str] = set()
        for raw_condition in raw_conditions:
            condition = _validate_criterion(
                raw_condition, result, "invalid_route_condition"
            )
            if condition.get("criterion_type") != expected_criterion_type[field]:
                result.error("route_condition_type_mismatch")
            if _nonempty_text(condition.get("metric_id")):
                metric_ids.add(condition["metric_id"])
        condition_metric_ids[field] = metric_ids

    raw_claims = selected_direction.get("core_claims")
    claims = {
        claim.get("claim_id"): claim
        for claim in raw_claims
        if isinstance(raw_claims, list)
        and isinstance(claim, dict)
        and _nonempty_text(claim.get("claim_id"))
    } if isinstance(raw_claims, list) else {}
    claim_metrics = {
        claim_id: {
            metric.get("metric_id")
            for metric in claim.get("required_decision_metrics", [])
            if isinstance(metric, dict) and _nonempty_text(metric.get("metric_id"))
        }
        for claim_id, claim in claims.items()
    }
    required_metric_ids = set().union(*claim_metrics.values()) if claim_metrics else set()
    route_metric_ids = set(route.get("primary_metrics", [])) | set(
        route.get("secondary_metrics", [])
    ) if isinstance(route.get("primary_metrics"), list) and isinstance(
        route.get("secondary_metrics"), list
    ) else set()
    if not required_metric_ids.issubset(route_metric_ids):
        result.error("route_missing_required_claim_metric")
    if not required_metric_ids.issubset(condition_metric_ids.get("go_conditions", set())):
        result.error("route_go_conditions_do_not_cover_claim_metrics")

    minimum_test = selected_direction.get("minimum_decisive_test")
    raw_preconditions = (
        minimum_test.get("required_preconditions", [])
        if isinstance(minimum_test, dict)
        else []
    )
    precondition_ids = {
        item.get("precondition_id")
        for item in raw_preconditions
        if isinstance(item, dict) and _nonempty_text(item.get("precondition_id"))
    }

    traces = route.get("route_traceability")
    if not isinstance(traces, list) or not traces:
        result.error("invalid_route_traceability")
        traces = []
    traced_claims: set[str] = set()
    for raw_trace in traces:
        trace = _validate_closed_fields(
            raw_trace,
            ROUTE_TRACE_FIELDS,
            result,
            "invalid_route_traceability_item",
            "unknown_route_traceability_fields",
        )
        claim_id = trace.get("claim_id")
        if claim_id not in claims or claim_id in traced_claims:
            result.error("invalid_route_traceability_claim_id")
            continue
        traced_claims.add(claim_id)
        metric_ids = trace.get("route_metric_ids")
        if not _nonempty_text_list(metric_ids) or set(metric_ids) != claim_metrics[claim_id]:
            result.error("route_claim_metric_traceability_mismatch")
        source_precondition_ids = trace.get("source_precondition_ids")
        if not _text_list(source_precondition_ids) or any(
            item not in precondition_ids for item in source_precondition_ids or []
        ):
            result.error("invalid_route_precondition_traceability")
        condition_types = trace.get("route_condition_types")
        if (
            not _nonempty_text_list(condition_types)
            or set(condition_types) != ROUTE_CONDITION_TYPES
            or len(condition_types) != 3
        ):
            result.error("invalid_route_condition_traceability")
    if traced_claims != set(claims):
        result.error("route_missing_claim_traceability")

    mappings = route.get("source_test_mapping")
    if not isinstance(mappings, list) or not mappings:
        result.error("invalid_source_test_mapping")
        mappings = []
    mapped_claims: set[str] = set()
    for raw_mapping in mappings:
        mapping = _validate_closed_fields(
            raw_mapping,
            SOURCE_TEST_MAPPING_FIELDS,
            result,
            "invalid_source_test_mapping_item",
            "unknown_source_test_mapping_fields",
        )
        claim_id = mapping.get("claim_id")
        if claim_id not in claims or claim_id in mapped_claims:
            result.error("invalid_source_test_mapping_claim_id")
            continue
        mapped_claims.add(claim_id)
        for field in ("minimum_test_metric_ids", "route_metric_ids"):
            metric_ids = mapping.get(field)
            if not _nonempty_text_list(metric_ids) or set(metric_ids) != claim_metrics[claim_id]:
                result.error("source_test_mapping_metric_mismatch")
    if mapped_claims != set(claims):
        result.error("missing_source_test_mapping")

    if route.get("inherited_constraints") != selected_direction.get("resource_limits"):
        result.error("route_inherited_constraints_mismatch")
    changes = route.get("approved_constraint_changes")
    if not isinstance(changes, list):
        result.error("invalid_approved_constraint_changes")
        changes = []
    for raw_change in changes:
        change = _validate_closed_fields(
            raw_change,
            APPROVED_CONSTRAINT_CHANGE_FIELDS,
            result,
            "invalid_approved_constraint_change",
            "unknown_approved_constraint_change_fields",
        )
        if (
            not _nonempty_text(change.get("constraint_id"))
            or not _finite_number(change.get("previous_value"))
            or not _finite_number(change.get("approved_value"))
            or not _nonempty_text(change.get("unit"))
            or not _nonempty_text(change.get("approval_message_id"))
            or not _valid_sha256(change.get("approval_message_sha256"))
        ):
            result.error("invalid_approved_constraint_change")
    chain = _validate_closed_fields(
        route.get("evidence_chain"),
        EVIDENCE_CHAIN_FIELDS,
        result,
        "invalid_route_evidence_chain",
        "unknown_route_evidence_chain_fields",
    )
    for field in EVIDENCE_CHAIN_FIELDS:
        if not _nonempty_text_list(chain.get(field)):
            result.error(f"empty_route_evidence_chain_{field}")


def _contains_prohibited_preconfirmation_content(value: Any) -> bool:
    if isinstance(value, dict):
        if set(value) & PROHIBITED_PRECONFIRMATION_KEYS:
            return True
        return any(
            _contains_prohibited_preconfirmation_content(item)
            for item in value.values()
        )
    if isinstance(value, list):
        return any(_contains_prohibited_preconfirmation_content(item) for item in value)
    return False


def _preconfirmation_bundle_hash(root: dict) -> str:
    previous = copy.deepcopy(root)
    previous["direction_decision"] = {
        "selected_direction_id": None,
        "status": "waiting_for_user_confirmation",
        "permitted_next_actions": DECISION_ACTIONS["waiting_for_user_confirmation"],
        "confirmation_event": None,
    }
    previous["route_output"] = None
    return canonical_sha256(previous)


def _validate_confirmation_event(
    value: Any,
    selected_direction_id: str,
    formal_directions: dict[str, dict],
    root: dict,
    result: _Result,
) -> dict:
    event = _validate_closed_fields(
        value,
        CONFIRMATION_EVENT_FIELDS,
        result,
        "invalid_confirmation_event",
        "unknown_confirmation_event_fields",
    )
    if event.get("actor_role") != "user":
        result.error("confirmation_actor_not_user")
    if event.get("selected_direction_id") != selected_direction_id:
        result.error("confirmation_direction_mismatch")
    if event.get("selected_direction_id") not in formal_directions:
        result.error("confirmation_direction_not_formal")
    for field in ("source_message_id", "source_message_excerpt"):
        if not _nonempty_text(event.get(field)):
            result.error("invalid_confirmation_message_source")
    excerpt = event.get("source_message_excerpt")
    if _nonempty_text(excerpt):
        if event.get("source_message_sha256") != _text_sha256(excerpt):
            result.error("confirmation_message_hash_mismatch")
        if re.search(
            rf"(?<![A-Za-z0-9_]){re.escape(selected_direction_id)}(?![A-Za-z0-9_])",
            excerpt,
        ) is None:
            result.error("confirmation_message_missing_explicit_direction_id")
    elif not _valid_sha256(event.get("source_message_sha256")):
        result.error("invalid_confirmation_message_hash")
    try:
        expected_previous_hash = _preconfirmation_bundle_hash(root)
    except (TypeError, ValueError):
        result.error("invalid_confirmation_previous_bundle")
    else:
        if event.get("previous_bundle_hash") != expected_previous_hash:
            result.error("confirmation_previous_bundle_hash_mismatch")
    return event


def _validate_decision(
    value: Any,
    route_output: Any,
    formal_directions: dict[str, dict],
    portfolio_incomplete: bool,
    root: dict,
    result: _Result,
) -> None:
    decision = _validate_closed_fields(
        value,
        DECISION_FIELDS,
        result,
        "invalid_direction_decision",
        "unknown_direction_decision_fields",
    )
    status = decision.get("status")
    if status not in DECISION_ACTIONS:
        result.error("invalid_direction_decision_status")
        return
    if decision.get("permitted_next_actions") != DECISION_ACTIONS[status]:
        result.error("invalid_permitted_next_actions")
    selected = decision.get("selected_direction_id")
    confirmation_event = decision.get("confirmation_event")
    if status == "user_confirmed":
        if selected not in formal_directions:
            result.error("selected_direction_not_formal")
        if portfolio_incomplete:
            result.error("confirmed_incomplete_portfolio")
        if not isinstance(confirmation_event, dict):
            result.error("confirmed_without_confirmation_event")
            confirmation_event = {}
        else:
            _validate_confirmation_event(
                confirmation_event, selected, formal_directions, root, result
            )
        if route_output is not None and selected in formal_directions:
            _validate_route_output(
                route_output,
                selected,
                formal_directions[selected],
                confirmation_event,
                root,
                result,
            )
    else:
        if confirmation_event is not None:
            result.error("confirmation_event_before_confirmation")
        if selected is not None:
            result.error("selected_direction_before_confirmation")
        if route_output is not None:
            result.error("route_output_before_user_confirmation")
    if portfolio_incomplete and status != "direction_evidence_incomplete":
        result.error("incomplete_portfolio_entered_decision_gate")
    if not portfolio_incomplete and status == "direction_evidence_incomplete":
        result.error("complete_portfolio_marked_decision_incomplete")


def _validate_bundle(bundle: Any) -> dict:
    result = _Result()
    root = _validate_closed_fields(
        bundle,
        ROOT_FIELDS,
        result,
        "invalid_bundle",
        "unknown_root_fields",
        ROOT_OPTIONAL_FIELDS,
    )
    if not root:
        return result.closed()

    raw_fixture_mode = root.get("fixture_mode", False)
    if not isinstance(raw_fixture_mode, bool):
        result.error("invalid_fixture_mode")
        fixture_mode = False
    else:
        fixture_mode = raw_fixture_mode
    if fixture_mode and root.get("evidence_class") != "offline_contract_fixture":
        result.error("invalid_fixture_evidence_class")
    if not fixture_mode and any(
        field in root for field in ("evidence_class", "proves", "does_not_prove")
    ):
        result.error("fixture_evidence_fields_outside_fixture_mode")
    if fixture_mode:
        if not _nonempty_text_list(root.get("proves")):
            result.error("invalid_fixture_proves")
        if not _nonempty_text_list(root.get("does_not_prove")):
            result.error("invalid_fixture_does_not_prove")

    portfolio = _validate_closed_fields(
        root.get("direction_portfolio"),
        PORTFOLIO_FIELDS,
        result,
        "invalid_direction_portfolio",
        "unknown_direction_portfolio_fields",
    )
    _source, index = _validate_source(root, portfolio, fixture_mode, result)
    formal_directions, incomplete = _validate_portfolio(
        portfolio, index, fixture_mode, result
    )
    _validate_decision(
        root.get("direction_decision"),
        root.get("route_output"),
        formal_directions,
        incomplete,
        root,
        result,
    )
    decision = root.get("direction_decision")
    if (
        isinstance(decision, dict)
        and decision.get("status") != "user_confirmed"
        and _contains_prohibited_preconfirmation_content(
            {
                key: value
                for key, value in root.items()
                if key != "source_m1_bundle"
            }
        )
    ):
        result.error("prohibited_route_content_before_user_confirmation")
    return result.closed()


def validate_bundle(bundle: Any) -> dict:
    """Return a closed validation result without performing I/O."""

    try:
        return _validate_bundle(bundle)
    except Exception:
        return {
            "status": "invalid",
            "errors": ["malformed_bundle"],
            "evidence_gaps": [],
        }


def main(argv: list[str] | None = None) -> int:
    """Read one JSON bundle, print one closed result, and return 0, 1, or 2."""

    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) != 1:
        output = {
            "status": "invalid",
            "errors": ["expected_one_json_path"],
            "evidence_gaps": [],
        }
    else:
        try:
            payload = json.loads(Path(arguments[0]).read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            output = {
                "status": "invalid",
                "errors": ["unreadable_or_invalid_json"],
                "evidence_gaps": [],
            }
        else:
            output = validate_bundle(payload)
    print(json.dumps(output, ensure_ascii=False, separators=(",", ":")))
    return {"valid": 0, "invalid": 1, "evidence_incomplete": 2}[output["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
