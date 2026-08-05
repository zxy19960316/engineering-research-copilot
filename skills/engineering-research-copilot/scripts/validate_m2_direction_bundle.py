#!/usr/bin/env python3
"""Validate one saved M2 direction-decision bundle without network access."""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

from validate_m1_bundle import validate_bundle as validate_m1_bundle


SCHEMA_VERSION = "m2.1"
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
    "axis_changes",
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
AXES = {"problem", "method", "data"}
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
    "hypothesis",
    "inputs",
    "baseline",
    "steps",
    "primary_metric",
    "success_threshold",
    "stop_condition",
    "pivot_condition",
    "expected_time",
    "required_resources",
}
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
    "evidence_chain",
}
ROUTE_TEXT_FIELDS = {"selected_direction_id", "hypothesis", "minimum_meaningful_improvement"}
ROUTE_LIST_FIELDS = ROUTE_FIELDS - ROUTE_TEXT_FIELDS - {"evidence_chain"}
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


def _validate_axis_changes(value: Any, position: Any, result: _Result) -> None:
    if not isinstance(value, list):
        result.error("invalid_axis_changes")
        return
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
    if position == "provisional_main" and value:
        result.error("main_direction_must_define_baseline_axes")
    elif position == "adjacent_alternative" and len(value) != 1:
        result.error("adjacent_requires_one_axis_change")
    elif position == "transfer_exploration" and len(set(axes)) < 2:
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


def _validate_decisive_test(value: Any, result: _Result) -> None:
    test = _validate_closed_fields(
        value,
        DECISIVE_TEST_FIELDS,
        result,
        "invalid_minimum_decisive_test",
        "unknown_minimum_decisive_test_fields",
    )
    for field in ("hypothesis", "baseline", "primary_metric", "expected_time"):
        if not _nonempty_text(test.get(field)):
            result.error(f"invalid_decisive_test_{field}")
    for field in ("inputs", "steps", "required_resources"):
        if not _nonempty_text_list(test.get(field)):
            result.error(f"invalid_decisive_test_{field}")
    _validate_threshold(test.get("success_threshold"), "success_threshold", result)
    _validate_threshold(test.get("stop_condition"), "stop_condition", result)
    _validate_threshold(test.get("pivot_condition"), "pivot_condition", result)


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

    _validate_axis_changes(direction.get("axis_changes"), position, result)
    hard_gate_failed = _validate_hard_gates(
        direction.get("hard_gates"), index, fixture_mode, result
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
    _validate_decisive_test(direction.get("minimum_decisive_test"), result)

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
) -> tuple[set[str], bool]:
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
    return formal_ids, any_failed


def _validate_route_output(
    value: Any, selected_direction_id: str, result: _Result
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
    for field in ROUTE_TEXT_FIELDS:
        if not _nonempty_text(route.get(field)):
            result.error(f"empty_route_output_{field}")
    for field in ROUTE_LIST_FIELDS:
        if not _nonempty_text_list(route.get(field)):
            result.error(f"empty_route_output_{field}")
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


def _validate_decision(
    value: Any,
    route_output: Any,
    formal_ids: set[str],
    portfolio_incomplete: bool,
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
    if status == "user_confirmed":
        if selected not in formal_ids:
            result.error("selected_direction_not_formal")
        if portfolio_incomplete:
            result.error("confirmed_incomplete_portfolio")
        if route_output is not None and selected in formal_ids:
            _validate_route_output(route_output, selected, result)
    else:
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
    formal_ids, incomplete = _validate_portfolio(
        portfolio, index, fixture_mode, result
    )
    _validate_decision(
        root.get("direction_decision"),
        root.get("route_output"),
        formal_ids,
        incomplete,
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
