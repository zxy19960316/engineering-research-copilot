#!/usr/bin/env python3
"""Validate the read-only M2 compatibility boundary for an M3 bundle."""

from __future__ import annotations

import copy
import json
import math
import sys
from pathlib import Path
from typing import Any

from validate_m2_direction_bundle import (
    canonical_sha256,
    validate_bundle as validate_m2_bundle,
)


SCHEMA_VERSION = "m3.1"
TOP_LEVEL_FIELDS = {
    "schema_version",
    "source_m2_bundle",
    "source_m2_bundle_hash",
    "selected_direction_id",
    "selected_direction_hash",
    "coaching_mode",
    "method_cards",
    "domain_overlays",
}
METHOD_CARD_FIELDS = {
    "schema_version",
    "card_id",
    "method_family",
    "applicability",
    "assumptions",
    "minimum_resources",
    "inherited_constraints",
    "baselines",
    "controls",
    "procedure_outline",
    "primary_metrics",
    "uncertainty_handling",
    "validation_checks",
    "failure_modes",
    "stop_conditions",
    "pivot_conditions",
    "safety_boundaries",
    "source_ledger",
}
APPLICABILITY_FIELDS = {
    "supported_claim_types",
    "required_inputs",
    "incompatible_conditions",
}
MINIMUM_RESOURCE_FIELDS = {
    "resource",
    "required_value",
    "unit",
    "source_constraint_id",
}
CRITERION_FIELDS = {
    "criterion_type",
    "metric_id",
    "operator",
    "value",
    "unit",
}
SOURCE_LEDGER_FIELDS = {
    "source_id",
    "candidate_id",
    "basis_level",
    "supports",
    "does_not_support",
    "limitations",
}
DOMAIN_OVERLAY_FIELDS = {
    "schema_version",
    "overlay_id",
    "domain",
    "base_card_ids",
    "additional_assumptions",
    "additional_failure_modes",
    "additional_validation_checks",
    "additional_stop_conditions",
    "specialist_review_boundaries",
    "transfer_status",
    "source_ledger",
}
COACHING_MODES = {"bounded", "route_specific"}
CONDITION_FIELDS = {
    "go": "go_conditions",
    "stop": "stop_conditions",
    "pivot": "pivot_conditions",
}
METHOD_FAMILIES = {
    "experiment_measurement_uq",
    "modeling_simulation_vvuq",
    "control_optimization_identification",
    "signal_diagnostics",
    "data_ml_hybrid",
    "reliability_safety_risk",
}
REQUIRED_NONEMPTY_CARD_LISTS = {
    "assumptions",
    "minimum_resources",
    "inherited_constraints",
    "baselines",
    "controls",
    "procedure_outline",
    "primary_metrics",
    "uncertainty_handling",
    "validation_checks",
    "failure_modes",
    "stop_conditions",
    "pivot_conditions",
    "safety_boundaries",
    "source_ledger",
}
BASIS_LEVEL_MAP = {
    "metadata_level": "metadata",
    "abstract_level": "abstract",
    "fulltext_level": "full_text",
}
ELIGIBLE_VERIFICATION_STATES = {
    "verified_primary",
    "verified_registry",
    "verified_preprint",
}
BLOCKED_VERIFICATION_STATES = {
    "partial",
    "conflicted",
    "not_found",
    "manual_needed",
}
CRITERION_OPERATORS = {"<", "<=", ">", ">="}
LEDGER_REQUIRED_LISTS = {"supports", "does_not_support", "limitations"}
METADATA_PROHIBITED_SUPPORT_TERMS = (
    "result",
    "performance",
    "safety",
    "transfer success",
    "successful transfer",
)


class _Result:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.evidence_gaps: list[str] = []

    def error(self, code: str) -> None:
        if code not in self.errors:
            self.errors.append(code)

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


def _closed_object(
    value: Any,
    fields: set[str],
    result: _Result,
    invalid_code: str,
    unknown_code: str,
) -> dict:
    if not isinstance(value, dict):
        result.error(invalid_code)
        return {}
    if not fields.issubset(value):
        result.error(invalid_code)
    if set(value) - fields:
        result.error(unknown_code)
    return value


def _closed_rows(
    value: Any,
    fields: set[str],
    result: _Result,
    invalid_list_code: str,
    invalid_row_code: str,
    unknown_row_code: str,
) -> list[dict]:
    if not isinstance(value, list):
        result.error(invalid_list_code)
        return []
    rows: list[dict] = []
    for raw_row in value:
        row = _closed_object(
            raw_row,
            fields,
            result,
            invalid_row_code,
            unknown_row_code,
        )
        if row:
            rows.append(row)
    return rows


def _candidate_context(source_m2_bundle: dict) -> dict[str, dict]:
    source_m1 = source_m2_bundle["source_m1_bundle"]
    candidates = source_m1["round2"]["candidate_pool"]
    return {
        candidate["candidate_id"]: {
            "basis_level": candidate["basis_level"],
            "recommendation_eligible": candidate["recommendation_eligible"],
            "verification_status": candidate["verification_status"],
        }
        for candidate in candidates
    }


def _derive_m2_context(source_m2_bundle: dict) -> dict:
    """Validate M2 first, then derive immutable compatibility facts from it."""

    m2_result = validate_m2_bundle(source_m2_bundle)
    if m2_result.get("status") != "valid":
        return {"errors": ["invalid_source_m2_bundle"]}

    decision = source_m2_bundle["direction_decision"]
    if decision["status"] != "user_confirmed":
        return {"errors": ["direction_not_user_confirmed"]}

    selected_direction_id = decision["selected_direction_id"]
    matches = [
        direction
        for direction in source_m2_bundle["direction_portfolio"]["directions"]
        if direction["direction_id"] == selected_direction_id
    ]
    if len(matches) != 1:
        return {"errors": ["selected_direction_not_formal"]}
    selected_direction = matches[0]

    claims = {
        claim["claim_id"]: copy.deepcopy(claim)
        for claim in selected_direction["core_claims"]
    }
    claim_metrics = {
        claim_id: frozenset(
            metric["metric_id"]
            for metric in claim["required_decision_metrics"]
        )
        for claim_id, claim in claims.items()
    }
    claim_preconditions = {
        coverage["claim_id"]: frozenset(coverage["required_precondition_ids"])
        for coverage in selected_direction["minimum_decisive_test"]["claim_coverage"]
    }

    return {
        "errors": [],
        "source_m2_bundle_hash": canonical_sha256(source_m2_bundle),
        "selected_direction_id": selected_direction_id,
        "selected_direction": copy.deepcopy(selected_direction),
        "selected_direction_hash": canonical_sha256(selected_direction),
        "claims": claims,
        "claim_metrics": claim_metrics,
        "claim_preconditions": claim_preconditions,
        "claim_types": frozenset(
            claim["claim_type"] for claim in claims.values()
        ),
        "metrics": {
            metric["metric_id"]: copy.deepcopy(metric)
            for claim in claims.values()
            for metric in claim["required_decision_metrics"]
        },
        "candidates": _candidate_context(source_m2_bundle),
        "fixture_mode": source_m2_bundle.get("fixture_mode") is True,
        "resource_limits": copy.deepcopy(selected_direction["resource_limits"]),
        "route_output": copy.deepcopy(source_m2_bundle["route_output"]),
    }


def _validate_source_ledger_shape(value: Any, result: _Result) -> None:
    _closed_rows(
        value,
        SOURCE_LEDGER_FIELDS,
        result,
        "invalid_source_ledger",
        "invalid_source_ledger",
        "unknown_source_ledger_fields",
    )


def _validate_criterion_shapes(value: Any, result: _Result) -> None:
    _closed_rows(
        value,
        CRITERION_FIELDS,
        result,
        "invalid_criteria",
        "invalid_criterion",
        "unknown_criterion_fields",
    )


def _validate_method_card_shape(value: Any, result: _Result) -> None:
    card = _closed_object(
        value,
        METHOD_CARD_FIELDS,
        result,
        "invalid_method_card",
        "unknown_method_card_fields",
    )
    if not card:
        return
    if card.get("schema_version") != SCHEMA_VERSION:
        result.error("invalid_method_card_schema_version")
    _closed_object(
        card.get("applicability"),
        APPLICABILITY_FIELDS,
        result,
        "invalid_applicability",
        "unknown_applicability_fields",
    )
    _closed_rows(
        card.get("minimum_resources"),
        MINIMUM_RESOURCE_FIELDS,
        result,
        "invalid_minimum_resources",
        "invalid_minimum_resource",
        "unknown_minimum_resource_fields",
    )
    _validate_criterion_shapes(card.get("stop_conditions"), result)
    _validate_criterion_shapes(card.get("pivot_conditions"), result)
    _validate_source_ledger_shape(card.get("source_ledger"), result)


def _validate_domain_overlay_shape(value: Any, result: _Result) -> None:
    overlay = _closed_object(
        value,
        DOMAIN_OVERLAY_FIELDS,
        result,
        "invalid_domain_overlay",
        "unknown_domain_overlay_fields",
    )
    if not overlay:
        return
    if overlay.get("schema_version") != SCHEMA_VERSION:
        result.error("invalid_domain_overlay_schema_version")
    _validate_criterion_shapes(overlay.get("additional_stop_conditions"), result)
    _validate_source_ledger_shape(overlay.get("source_ledger"), result)


def _nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _finite_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def _nonempty_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value)


def _nonempty_text_list(value: Any) -> bool:
    return _nonempty_list(value) and all(_nonempty_text(item) for item in value)


def _candidate_is_eligible(candidate: dict, fixture_mode: bool) -> bool:
    status = candidate.get("verification_status")
    if candidate.get("recommendation_eligible") is not True:
        return False
    if status in BLOCKED_VERIFICATION_STATES:
        return False
    if fixture_mode:
        return status == "fixture_only"
    return status in ELIGIBLE_VERIFICATION_STATES


def _candidate_is_non_preprint(candidate: dict, fixture_mode: bool) -> bool:
    return _candidate_is_eligible(candidate, fixture_mode) and (
        fixture_mode or candidate.get("verification_status") != "verified_preprint"
    )


def _validate_source_ledger(
    value: Any,
    context: dict,
    result: _Result,
) -> list[dict]:
    rows = _closed_rows(
        value,
        SOURCE_LEDGER_FIELDS,
        result,
        "invalid_source_ledger",
        "invalid_source_ledger",
        "unknown_source_ledger_fields",
    )
    candidates = context["candidates"]
    fixture_mode = context["fixture_mode"]
    for row in rows:
        for field in LEDGER_REQUIRED_LISTS:
            if field not in row:
                result.error(f"missing_source_ledger_{field}")
            elif not _nonempty_text_list(row[field]):
                result.error(f"empty_source_ledger_{field}")

        if not _nonempty_text(row.get("source_id")):
            result.error("invalid_source_ledger_source_id")
        candidate_id = row.get("candidate_id")
        if not _nonempty_text(candidate_id) or candidate_id not in candidates:
            result.error("source_ledger_unknown_candidate")
            continue

        candidate = candidates[candidate_id]
        mapped_basis = BASIS_LEVEL_MAP.get(candidate.get("basis_level"))
        if mapped_basis is None or row.get("basis_level") != mapped_basis:
            result.error("source_ledger_basis_level_mismatch")
        if not _candidate_is_eligible(candidate, fixture_mode):
            result.error("source_ledger_ineligible_candidate")

        supports = row.get("supports")
        if mapped_basis == "metadata" and isinstance(supports, list):
            normalized_supports = " ".join(
                item.casefold() for item in supports if isinstance(item, str)
            )
            if any(
                term in normalized_supports
                for term in METADATA_PROHIBITED_SUPPORT_TERMS
            ):
                result.error("metadata_only_source_overclaim")
    return rows


def _validate_resource_bounds(card: dict, context: dict, result: _Result) -> None:
    inherited = card.get("inherited_constraints")
    if inherited != context["resource_limits"]:
        result.error("method_card_inherited_constraints_mismatch")

    limits_by_id = {
        limit["constraint_id"]: limit for limit in context["resource_limits"]
    }
    resources = card.get("minimum_resources")
    if not isinstance(resources, list):
        return
    for resource in resources:
        if not isinstance(resource, dict):
            continue
        required_value = resource.get("required_value")
        if not _finite_number(required_value):
            result.error("invalid_minimum_resource_required_value")

        source_constraint_id = resource.get("source_constraint_id")
        limit = limits_by_id.get(source_constraint_id)
        if limit is None:
            result.error("minimum_resource_unbound")
            continue
        if resource.get("resource") != limit["resource"]:
            result.error("minimum_resource_name_mismatch")
        if resource.get("unit") != limit["unit"]:
            result.error("minimum_resource_unit_mismatch")
        if not _finite_number(required_value):
            continue
        if limit["operator"] == "<" and required_value >= limit["value"]:
            result.error("minimum_resource_exceeds_ceiling")
        elif limit["operator"] == "<=" and required_value > limit["value"]:
            result.error("minimum_resource_exceeds_ceiling")
        elif limit["operator"] not in {"<", "<="}:
            result.error("minimum_resource_constraint_not_ceiling")


def _validate_conditions(
    value: Any,
    expected_type: str,
    context: dict,
    result: _Result,
    invalid_code: str,
) -> None:
    if not isinstance(value, list):
        return
    for condition in value:
        if not isinstance(condition, dict):
            result.error(invalid_code)
            continue
        metric_id = condition.get("metric_id")
        metric = context["metrics"].get(metric_id)
        if (
            condition.get("criterion_type") != expected_type
            or condition.get("operator") not in CRITERION_OPERATORS
            or not _finite_number(condition.get("value"))
            or metric is None
            or condition.get("unit") != metric.get("unit")
        ):
            result.error(invalid_code)


def _validate_applicability(card: dict, context: dict, result: _Result) -> None:
    applicability = card.get("applicability")
    if not isinstance(applicability, dict):
        return
    for field in APPLICABILITY_FIELDS:
        value = applicability.get(field)
        if field not in applicability:
            result.error(f"missing_method_card_applicability_{field}")
        elif not _nonempty_list(value):
            result.error(f"empty_method_card_applicability_{field}")
        elif not all(_nonempty_text(item) for item in value):
            result.error(f"invalid_method_card_applicability_{field}")

    claim_types = applicability.get("supported_claim_types")
    if isinstance(claim_types, list) and any(
        claim_type not in context["claim_types"] for claim_type in claim_types
    ):
        result.error("unsupported_method_card_claim_type")


def _validate_method_card(value: Any, context: dict, result: _Result) -> dict:
    _validate_method_card_shape(value, result)
    if not isinstance(value, dict):
        return {}
    card = value

    if not _nonempty_text(card.get("card_id")):
        result.error("invalid_method_card_id")
    if card.get("method_family") not in METHOD_FAMILIES:
        result.error("unknown_method_family")
    _validate_applicability(card, context, result)

    for field in REQUIRED_NONEMPTY_CARD_LISTS:
        if field not in card:
            result.error(f"missing_method_card_{field}")
        elif not _nonempty_list(card[field]):
            result.error(f"empty_method_card_{field}")

    narrative_fields = REQUIRED_NONEMPTY_CARD_LISTS - {
        "minimum_resources",
        "inherited_constraints",
        "primary_metrics",
        "stop_conditions",
        "pivot_conditions",
        "source_ledger",
    }
    for field in narrative_fields:
        value = card.get(field)
        if _nonempty_list(value) and not all(
            _nonempty_text(item) for item in value
        ):
            result.error(f"invalid_method_card_{field}")

    primary_metrics = card.get("primary_metrics")
    if isinstance(primary_metrics, list) and any(
        metric_id not in context["metrics"] for metric_id in primary_metrics
    ):
        result.error("unknown_method_card_primary_metric")

    _validate_resource_bounds(card, context, result)
    _validate_conditions(
        card.get("stop_conditions"),
        "stop",
        context,
        result,
        "invalid_method_card_stop_condition",
    )
    _validate_conditions(
        card.get("pivot_conditions"),
        "pivot",
        context,
        result,
        "invalid_method_card_pivot_condition",
    )
    _validate_source_ledger(card.get("source_ledger"), context, result)
    return card


def _validate_domain_overlay(
    value: Any,
    context: dict,
    cards_by_id: dict[str, dict],
    result: _Result,
) -> None:
    _validate_domain_overlay_shape(value, result)
    if not isinstance(value, dict):
        return
    overlay = value

    if not _nonempty_text(overlay.get("overlay_id")):
        result.error("invalid_domain_overlay_id")
    if overlay.get("domain") != "nuclear_engineering_ml":
        result.error("unknown_domain_overlay")
    base_card_ids = overlay.get("base_card_ids")
    if not _nonempty_list(base_card_ids):
        result.error("nuclear_overlay_missing_base_card")
        base_card_ids = []
    elif any(card_id not in cards_by_id for card_id in base_card_ids):
        result.error("nuclear_overlay_unknown_base_card")

    additive_text_fields = (
        "additional_assumptions",
        "additional_failure_modes",
        "additional_validation_checks",
        "specialist_review_boundaries",
    )
    if (
        any(
            not _nonempty_text_list(overlay.get(field))
            for field in additive_text_fields
        )
        or not _nonempty_list(overlay.get("additional_stop_conditions"))
        or not _nonempty_list(overlay.get("source_ledger"))
    ):
        result.error("nuclear_overlay_missing_additive_boundary")
    if overlay.get("transfer_status") != "hypothesis":
        result.error("nuclear_overlay_transfer_status_not_hypothesis")

    _validate_conditions(
        overlay.get("additional_stop_conditions"),
        "stop",
        context,
        result,
        "invalid_nuclear_overlay_stop_condition",
    )
    ledger = _validate_source_ledger(
        overlay.get("source_ledger"), context, result
    )
    safety_support_rows = [
        row
        for row in ledger
        if isinstance(row.get("supports"), list)
        and any(
            isinstance(statement, str)
            and any(
                term in statement.casefold()
                for term in ("safety", "hazard", "risk")
            )
            for statement in row["supports"]
        )
    ]
    if not any(
        isinstance(row.get("candidate_id"), str)
        and row["candidate_id"] in context["candidates"]
        and _candidate_is_non_preprint(
            context["candidates"][row["candidate_id"]],
            context["fixture_mode"],
        )
        for row in safety_support_rows
    ):
        result.error("nuclear_safety_requires_non_preprint_support")


def _validate_closed_m3_shapes(root: dict, context: dict, result: _Result) -> None:
    cards = root.get("method_cards")
    cards_by_id: dict[str, dict] = {}
    if not isinstance(cards, list):
        result.error("invalid_method_cards")
    else:
        if not cards:
            result.error("empty_method_cards")
        for card in cards:
            validated = _validate_method_card(card, context, result)
            card_id = validated.get("card_id")
            if _nonempty_text(card_id):
                if card_id in cards_by_id:
                    result.error("duplicate_method_card_id")
                else:
                    cards_by_id[card_id] = validated

    overlays = root.get("domain_overlays")
    if not isinstance(overlays, list):
        result.error("invalid_domain_overlays")
    else:
        for overlay in overlays:
            _validate_domain_overlay(overlay, context, cards_by_id, result)


def _condition_metric_ids(route: dict) -> dict[str, frozenset[str]]:
    return {
        condition_type: frozenset(
            condition["metric_id"]
            for condition in route[field]
            if isinstance(condition, dict)
            and isinstance(condition.get("metric_id"), str)
        )
        for condition_type, field in CONDITION_FIELDS.items()
    }


def _validate_route_compatibility(route: dict, context: dict, result: _Result) -> None:
    trace_by_claim = {
        trace["claim_id"]: trace for trace in route["route_traceability"]
    }
    condition_metrics = _condition_metric_ids(route)

    for claim_id, claim_metric_ids in context["claim_metrics"].items():
        trace = trace_by_claim[claim_id]
        if (
            frozenset(trace["source_precondition_ids"])
            != context["claim_preconditions"][claim_id]
        ):
            result.error("route_precondition_traceability_mismatch")

        derived_condition_types = {
            condition_type
            for condition_type, metric_ids in condition_metrics.items()
            if claim_metric_ids & metric_ids
        }
        if set(trace["route_condition_types"]) != derived_condition_types:
            result.error("route_condition_traceability_mismatch")


def _validate_m3_bundle(bundle: Any) -> dict:
    result = _Result()
    root = _closed_object(
        bundle,
        TOP_LEVEL_FIELDS,
        result,
        "invalid_m3_bundle",
        "unknown_m3_bundle_fields",
    )
    if not root:
        return result.closed()
    if root.get("schema_version") != SCHEMA_VERSION:
        result.error("invalid_m3_schema_version")

    source_m2_bundle = root.get("source_m2_bundle")
    if not isinstance(source_m2_bundle, dict):
        result.error("invalid_source_m2_bundle")
        return result.closed()

    context = _derive_m2_context(source_m2_bundle)
    for error in context["errors"]:
        result.error(error)
    if context["errors"]:
        return result.closed()

    route = context["route_output"]
    if isinstance(route, dict) and route.get("approved_constraint_changes"):
        return {
            "status": "invalid",
            "errors": ["unsupported_approved_constraint_change_provenance"],
            "evidence_gaps": [],
        }

    if root.get("source_m2_bundle_hash") != context["source_m2_bundle_hash"]:
        result.error("source_m2_bundle_hash_mismatch")
    if root.get("selected_direction_id") != context["selected_direction_id"]:
        result.error("selected_direction_id_mismatch")
    if root.get("selected_direction_hash") != context["selected_direction_hash"]:
        result.error("selected_direction_hash_mismatch")

    coaching_mode = root.get("coaching_mode")
    if coaching_mode not in COACHING_MODES:
        result.error("invalid_coaching_mode")
    elif coaching_mode == "route_specific":
        if route is None:
            result.error("route_specific_requires_route")
        else:
            _validate_route_compatibility(route, context, result)

    _validate_closed_m3_shapes(root, context, result)
    return result.closed()


def validate_m3_bundle(bundle: Any) -> dict:
    """Return one closed result without changing the bundle or performing I/O."""

    try:
        return _validate_m3_bundle(bundle)
    except Exception:
        return {
            "status": "invalid",
            "errors": ["malformed_m3_bundle"],
            "evidence_gaps": [],
        }


def main(argv: list[str] | None = None) -> int:
    """Read one JSON file, print compact JSON, and return a closed exit code."""

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
            output = validate_m3_bundle(payload)
    print(json.dumps(output, ensure_ascii=False, separators=(",", ":")))
    return {"valid": 0, "invalid": 1, "evidence_incomplete": 2}[output["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
