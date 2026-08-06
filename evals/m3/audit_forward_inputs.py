#!/usr/bin/env python3
"""Audit immutable M2.1.1 prerequisites for the M3 forward cases."""

from __future__ import annotations

import hashlib
import json
import math
import os
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
M3_FIXTURE_ROOT = (REPO_ROOT / "evals" / "m3" / "fixtures").resolve()
HISTORICAL_IDENTITY_PATH = REPO_ROOT / "evals" / "m3" / "historical-json-identities.json"
HISTORICAL_EVIDENCE_HEAD = "1b696bce53ee0a11163bfe4f91a9a49ab3af6f49"
M2_SCRIPT_ROOT = REPO_ROOT / "skills" / "engineering-research-copilot" / "scripts"
sys.path.insert(0, str(M2_SCRIPT_ROOT))

from validate_m2_direction_bundle import validate_bundle as validate_m2_bundle  # noqa: E402


EXPECTED_CASE_IDS = ("m3-f01", "m3-f02", "m3-f03", "m3-f04", "m3-f05")
MANIFEST_REQUIRED_FIELDS = {
    "schema_version",
    "evidence_class",
    "preparation_context",
    "cases",
}
CASE_REQUIRED_FIELDS = {
    "case_id",
    "input_path",
    "raw_sha256",
    "canonical_sha256",
    "validation_path",
    "m2_validation_status",
    "m2_validation_errors",
    "m2_validation_evidence_gaps",
    "source_m1_artifact",
    "source_m1_raw_sha256",
    "constructed_by_context",
    "reviewed_by_context",
    "does_not_prove",
}
VALID_M2_STATUS = "valid"
VALID_M2_VALIDATOR = (
    "skills/engineering-research-copilot/scripts/validate_m2_direction_bundle.py"
)
ALLOWED_VERIFICATION_STATES = {
    "verified_primary",
    "verified_registry",
    "verified_preprint",
}
NON_PREPRINT_STATES = {"verified_primary", "verified_registry"}
NUCLEAR_TOKENS = (
    "nuclear",
    "pwr",
    "reactor",
    "npp",
    "loca",
    "safety-critical",
)
ML_TOKENS = ("machine learning", "deep learning", "neural", "regression", "ml")
MEASUREMENT_TOKENS = (
    "measurement",
    "measurand",
    "calibration",
    "repeatability",
    "reproducibility",
    "uncertainty",
)


def _empty_case(case_id: str) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "status": "valid",
        "errors": [],
        "evidence_gaps": [],
        "expected_raw_sha256": None,
        "observed_raw_sha256": None,
        "source_m1_expected_sha256": None,
        "source_m1_observed_sha256": None,
        "input_git_blob_oid": None,
        "source_m1_git_blob_oid": None,
        "input_canonical_sha256": None,
        "source_m1_canonical_sha256": None,
        "input_identity_status": "not_checked",
        "source_m1_identity_status": "not_checked",
    }


def _close_case(case: dict[str, Any]) -> None:
    if case["errors"]:
        case["status"] = "invalid"
    elif case["evidence_gaps"]:
        case["status"] = "evidence_incomplete"
    else:
        case["status"] = "valid"
    case["errors"] = sorted(set(case["errors"]))
    case["evidence_gaps"] = sorted(set(case["evidence_gaps"]))


def _finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _historical_identities(errors: list[str]) -> dict[str, dict[str, Any]]:
    try:
        value = json.loads(HISTORICAL_IDENTITY_PATH.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        errors.append("historical_identity_registry_invalid")
        return {}
    if (
        not isinstance(value, dict)
        or value.get("schema_version") != "m3.1-historical-json-identities-v1"
        or not isinstance(value.get("artifacts"), list)
    ):
        errors.append("historical_identity_registry_invalid")
        return {}
    if value.get("evidence_head") != HISTORICAL_EVIDENCE_HEAD:
        errors.append("historical_evidence_head_mismatch")
        return {}
    return {
        item["path"]: item
        for item in value["artifacts"]
        if isinstance(item, dict) and isinstance(item.get("path"), str)
    }


def _repo_relative(path: Path) -> str | None:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return None


def _git_blob_oid(path: Path) -> str | None:
    relative = _repo_relative(path)
    if relative is None:
        return None
    try:
        completed = subprocess.run(
            ["git", "rev-parse", f"{HISTORICAL_EVIDENCE_HEAD}:{relative}"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
    except OSError:
        return None
    value = completed.stdout.strip()
    if completed.returncode != 0 or len(value) != 40 or any(
        char not in "0123456789abcdef" for char in value
    ):
        return None
    return value


def _git_blob_json(blob_oid: str) -> Any:
    try:
        completed = subprocess.run(
            ["git", "cat-file", "blob", blob_oid],
            cwd=REPO_ROOT,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            return None
        return json.loads(completed.stdout.decode("utf-8", errors="strict"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None


def _has_reparse_point(path: Path) -> bool:
    try:
        attributes = getattr(path.stat(), "st_file_attributes", 0)
    except OSError:
        return True
    return bool(attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def _safe_file(raw_path: Any, code_prefix: str, errors: list[str]) -> Path | None:
    if not isinstance(raw_path, str) or not raw_path:
        errors.append(f"{code_prefix}_missing")
        return None
    candidate = Path(raw_path)
    resolved = candidate.resolve() if candidate.is_absolute() else (REPO_ROOT / candidate).resolve()
    try:
        resolved.relative_to(REPO_ROOT.resolve())
    except ValueError:
        errors.append(f"{code_prefix}_outside_repository")
        return None
    if M3_FIXTURE_ROOT == resolved or M3_FIXTURE_ROOT in resolved.parents:
        errors.append(f"{code_prefix}_fixture_forbidden")
        return None
    current = resolved
    while True:
        if current.is_symlink() or _has_reparse_point(current):
            errors.append(f"{code_prefix}_reparse_point_forbidden")
            return None
        if current == REPO_ROOT.resolve():
            break
        if current.parent == current:
            errors.append(f"{code_prefix}_outside_repository")
            return None
        current = current.parent
    if not resolved.is_file():
        errors.append(f"{code_prefix}_missing")
        return None
    return resolved


def _load_json_file(path: Path, code_prefix: str, errors: list[str]) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        errors.append(f"{code_prefix}_invalid_json")
        return None


def _validate_hashes(
    path: Path,
    raw_hash: Any,
    canonical_hash: Any,
    prefix: str,
    errors: list[str],
    case: dict[str, Any],
    historical_identities: dict[str, dict[str, Any]],
) -> Any:
    raw_field = "expected_raw_sha256" if prefix == "input" else "source_m1_expected_sha256"
    observed_field = "observed_raw_sha256" if prefix == "input" else "source_m1_observed_sha256"
    blob_field = "input_git_blob_oid" if prefix == "input" else "source_m1_git_blob_oid"
    canonical_field = (
        "input_canonical_sha256" if prefix == "input" else "source_m1_canonical_sha256"
    )
    identity_field = "input_identity_status" if prefix == "input" else "source_m1_identity_status"
    case[raw_field] = raw_hash
    try:
        case[observed_field] = _sha256(path)
    except OSError:
        case[identity_field] = "invalid"
        errors.append(f"{prefix}_raw_sha256_mismatch")
        return None
    payload = _load_json_file(path, prefix, errors)
    actual_canonical = None
    if payload is not None:
        try:
            actual_canonical = _canonical_sha256(payload)
        except (TypeError, ValueError):
            errors.append(f"{prefix}_canonical_json_invalid")
        else:
            if canonical_hash is not None and (
                not isinstance(canonical_hash, str) or actual_canonical != canonical_hash
            ):
                errors.append(f"{prefix}_canonical_sha256_mismatch")
    relative = _repo_relative(path)
    identity = historical_identities.get(relative or "")
    if identity is None:
        case[canonical_field] = actual_canonical
        if (
            not isinstance(raw_hash, str)
            or len(raw_hash) != 64
            or case[observed_field] != raw_hash
        ):
            errors.append(f"{prefix}_raw_sha256_mismatch")
        case[identity_field] = "legacy_raw_only" if payload is not None else "invalid"
        return payload

    blob_oid = _git_blob_oid(path)
    case[blob_field] = blob_oid
    historical_payload = _git_blob_json(blob_oid) if blob_oid is not None else None
    historical_canonical = None
    if historical_payload is not None:
        try:
            historical_canonical = _canonical_sha256(historical_payload)
        except (TypeError, ValueError):
            historical_canonical = None
    case[canonical_field] = historical_canonical
    if raw_hash != identity.get("legacy_raw_sha256"):
        errors.append(f"{prefix}_raw_sha256_mismatch")
    if blob_oid != identity.get("git_blob_oid"):
        errors.append(f"{prefix}_git_blob_oid_mismatch")
    if historical_canonical != identity.get("canonical_sha256"):
        errors.append(f"{prefix}_canonical_sha256_mismatch")
    if actual_canonical != historical_canonical:
        errors.append(f"{prefix}_worktree_content_mismatch")
    identity_errors = {
        f"{prefix}_raw_sha256_mismatch",
        f"{prefix}_git_blob_oid_mismatch",
        f"{prefix}_canonical_sha256_mismatch",
        f"{prefix}_canonical_json_invalid",
        f"{prefix}_invalid_json",
        f"{prefix}_worktree_content_mismatch",
    }
    case[identity_field] = (
        "invalid" if identity_errors.intersection(errors) else "valid"
    )
    return payload


def _all_candidates(source_m1: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for round_name in ("round1", "round2"):
        round_data = source_m1.get(round_name, {})
        candidates.extend(round_data.get("candidate_pool", []))
    return candidates


def _eligible_candidates(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    source_m1 = bundle.get("source_m1_bundle", {})
    return [
        candidate
        for candidate in _all_candidates(source_m1)
        if candidate.get("recommendation_eligible") is True
        and candidate.get("verification_status") in ALLOWED_VERIFICATION_STATES
    ]


def _selected_direction(bundle: dict[str, Any]) -> dict[str, Any] | None:
    decision = bundle.get("direction_decision")
    portfolio = bundle.get("direction_portfolio")
    if not isinstance(decision, dict) or not isinstance(portfolio, dict):
        return None
    selected_id = decision.get("selected_direction_id")
    directions = portfolio.get("directions")
    if not isinstance(selected_id, str) or not isinstance(directions, list):
        return None
    return next(
        (direction for direction in directions if direction.get("direction_id") == selected_id),
        None,
    )


def _is_user_confirmed(bundle: dict[str, Any]) -> bool:
    decision = bundle.get("direction_decision")
    if not isinstance(decision, dict) or decision.get("status") != "user_confirmed":
        return False
    event = decision.get("confirmation_event")
    return (
        isinstance(event, dict)
        and event.get("actor_role") == "user"
        and event.get("selected_direction_id") == decision.get("selected_direction_id")
        and isinstance(event.get("source_message_id"), str)
        and isinstance(event.get("source_message_excerpt"), str)
    )


def _metric_ids(direction: dict[str, Any]) -> list[str]:
    return [
        metric["metric_id"]
        for claim in direction.get("core_claims", [])
        for metric in claim.get("required_decision_metrics", [])
        if isinstance(metric, dict) and isinstance(metric.get("metric_id"), str)
    ]


def _direction_text(direction: dict[str, Any]) -> str:
    return json.dumps(direction, ensure_ascii=False, sort_keys=True).lower()


def _check_common_direction(
    case_id: str,
    bundle: dict[str, Any],
    case: dict[str, Any],
    require_confirmation: bool,
) -> dict[str, Any] | None:
    direction = _selected_direction(bundle)
    if direction is None:
        case["errors"].append(f"{case_id}_selected_direction_missing")
        return None
    if require_confirmation and not _is_user_confirmed(bundle):
        case["errors"].append(f"{case_id}_requires_user_confirmed_direction")
    if bundle.get("fixture_mode") is True:
        case["errors"].append("fixture_input_forbidden")
    limits = direction.get("resource_limits")
    if not isinstance(limits, list) or not limits:
        case["errors"].append(f"{case_id}_resource_limits_incomplete")
    else:
        for limit in limits:
            if not isinstance(limit, dict) or not _finite_number(limit.get("value")):
                case["errors"].append(f"{case_id}_resource_limits_incomplete")
                break
    if not _eligible_candidates(bundle):
        case["errors"].append(f"{case_id}_eligible_source_missing")
    return direction


def _check_numeric_stop_pivot(
    case_id: str,
    direction: dict[str, Any],
    case: dict[str, Any],
) -> None:
    metric_ids = set(_metric_ids(direction))
    coverage = direction.get("minimum_decisive_test", {}).get("claim_coverage", [])
    criteria_by_metric: dict[str, set[str]] = {metric_id: set() for metric_id in metric_ids}
    if not isinstance(coverage, list):
        case["errors"].append(f"{case_id}_numeric_stop_pivot_missing")
        return
    for item in coverage:
        if not isinstance(item, dict):
            continue
        for criterion in item.get("decision_criteria", []):
            if not isinstance(criterion, dict):
                continue
            metric_id = criterion.get("metric_id")
            criterion_type = criterion.get("criterion_type")
            if metric_id in criteria_by_metric and criterion_type in {"stop", "pivot"}:
                if _finite_number(criterion.get("value")) and isinstance(criterion.get("unit"), str):
                    criteria_by_metric[metric_id].add(criterion_type)
                else:
                    case["errors"].append(f"{case_id}_numeric_stop_pivot_invalid")
    if any(types != {"stop", "pivot"} for types in criteria_by_metric.values()):
        case["errors"].append(f"{case_id}_numeric_stop_pivot_missing")


def _check_route_free_case(
    case_id: str,
    bundle: dict[str, Any],
    case: dict[str, Any],
) -> dict[str, Any] | None:
    direction = _check_common_direction(case_id, bundle, case, True)
    if direction is None:
        return None
    if bundle.get("route_output") is not None:
        case["errors"].append(f"{case_id}_route_must_be_null")
    _check_numeric_stop_pivot(case_id, direction, case)
    return direction


def _check_f01(bundle: dict[str, Any], case: dict[str, Any]) -> None:
    direction = _check_route_free_case("f01", bundle, case)
    if direction is None:
        return
    claim_types = {
        claim.get("claim_type")
        for claim in direction.get("core_claims", [])
        if isinstance(claim, dict)
    }
    required = {"predictive_performance", "uncertainty_quality", "data_availability"}
    if not required.issubset(claim_types):
        case["errors"].append("f01_direction_claim_types_incomplete")


def _actual_condition_types(route: dict[str, Any], metric_id: str) -> set[str]:
    return {
        kind
        for kind in ("go", "stop", "pivot")
        if any(
            isinstance(condition, dict) and condition.get("metric_id") == metric_id
            for condition in route.get(f"{kind}_conditions", [])
        )
    }


def _check_f02(bundle: dict[str, Any], case: dict[str, Any]) -> None:
    direction = _check_common_direction("f02", bundle, case, True)
    route = bundle.get("route_output")
    if direction is None or not isinstance(route, dict):
        case["errors"].append("f02_route_required")
        return
    if route.get("approved_constraint_changes") != []:
        case["errors"].append("f02_approved_constraint_changes_must_be_empty")
    coverage_by_claim = {
        item.get("claim_id"): item
        for item in direction.get("minimum_decisive_test", {}).get("claim_coverage", [])
        if isinstance(item, dict)
    }
    traceability = route.get("route_traceability", [])
    if not isinstance(traceability, list):
        case["errors"].append("f02_route_traceability_missing")
        return
    for trace in traceability:
        if not isinstance(trace, dict):
            case["errors"].append("f02_route_traceability_invalid")
            continue
        claim_id = trace.get("claim_id")
        coverage = coverage_by_claim.get(claim_id)
        if coverage is None:
            case["errors"].append("f02_route_traceability_claim_mismatch")
            continue
        if trace.get("source_precondition_ids") != coverage.get("required_precondition_ids"):
            case["errors"].append("f02_source_preconditions_mismatch")
        expected_metrics = set(coverage.get("metric_ids", []))
        if set(trace.get("route_metric_ids", [])) != expected_metrics:
            case["errors"].append("f02_route_metrics_mismatch")
        for metric_id in expected_metrics:
            actual_types = _actual_condition_types(route, metric_id)
            if actual_types != {"go", "stop", "pivot"}:
                case["errors"].append("f02_claim_metric_condition_coverage_incomplete")
            if set(trace.get("route_condition_types", [])) != actual_types:
                case["errors"].append("f02_route_condition_types_mismatch")
    if set(coverage_by_claim) != {
        trace.get("claim_id") for trace in traceability if isinstance(trace, dict)
    }:
        case["errors"].append("f02_route_traceability_claim_mismatch")


def _check_f03(bundle: dict[str, Any], case: dict[str, Any]) -> None:
    direction = _check_common_direction("f03", bundle, case, False)
    route = bundle.get("route_output")
    if direction is None or not isinstance(route, dict):
        case["errors"].append("f03_route_required")
        return
    changes = route.get("approved_constraint_changes")
    if not isinstance(changes, list) or not changes:
        case["errors"].append("f03_approved_constraint_changes_required")
    if route.get("inherited_constraints") != direction.get("resource_limits"):
        case["errors"].append("f03_selected_direction_resource_limits_not_preserved")


def _check_f04(bundle: dict[str, Any], case: dict[str, Any], source_m1: dict[str, Any] | None) -> None:
    direction = _check_route_free_case("f04", bundle, case)
    if direction is None:
        return
    text = _direction_text(direction)
    if any(token in text for token in NUCLEAR_TOKENS):
        case["errors"].append("f04_must_be_non_nuclear")
    if not any(token in text for token in MEASUREMENT_TOKENS):
        case["errors"].append("f04_measurement_uq_claim_missing")
    if not isinstance(source_m1, dict) or source_m1.get("terminal_state") != "M1_COMPLETE" or source_m1.get("outcome") != "complete":
        case["evidence_gaps"].append("no independently accepted complete non-nuclear M1/M2 input")


def _check_f05(bundle: dict[str, Any], case: dict[str, Any]) -> None:
    direction = _check_route_free_case("f05", bundle, case)
    if direction is None:
        return
    text = _direction_text(direction)
    if not any(token in text for token in NUCLEAR_TOKENS) or not any(token in text for token in ML_TOKENS):
        case["errors"].append("f05_nuclear_ml_direction_missing")
    safety_candidates = []
    for candidate in _eligible_candidates(bundle):
        if candidate.get("verification_status") not in NON_PREPRINT_STATES:
            continue
        candidate_text = json.dumps(candidate, ensure_ascii=False, sort_keys=True).lower()
        if "safety" in candidate_text:
            safety_candidates.append(candidate)
    if not safety_candidates:
        case["errors"].append("f05_non_preprint_safety_source_missing")


def _validate_m2_receipt(
    case_data: dict[str, Any],
    case: dict[str, Any],
) -> None:
    validation_path_value = case_data.get("validation_path")
    if validation_path_value is None:
        if case_data.get("m2_validation_status") == "NOT_RUN":
            case["evidence_gaps"].extend(case_data.get("m2_validation_evidence_gaps", []))
        else:
            case["errors"].append("m2_validation_receipt_missing")
        return
    validation_path = _safe_file(validation_path_value, "validation_path", case["errors"])
    if validation_path is None:
        return
    receipt = _load_json_file(validation_path, "validation_receipt", case["errors"])
    if not isinstance(receipt, dict):
        return
    if receipt.get("status") != case_data.get("m2_validation_status"):
        case["errors"].append("m2_validation_status_mismatch")
    if receipt.get("errors", []) != case_data.get("m2_validation_errors", []):
        case["errors"].append("m2_validation_errors_mismatch")
    if receipt.get("evidence_gaps", []) != case_data.get("m2_validation_evidence_gaps", []):
        case["errors"].append("m2_validation_evidence_gaps_mismatch")
    if receipt.get("status") == "NOT_RUN":
        case["evidence_gaps"].extend(receipt.get("evidence_gaps", []))
    elif receipt.get("status") != VALID_M2_STATUS:
        case["errors"].append("m2_validation_not_valid")
    elif receipt.get("invocation_count") != 1 or receipt.get("validator") != VALID_M2_VALIDATOR:
        case["errors"].append("m2_validation_receipt_not_one_shot")
    if receipt.get("input_path") != case_data.get("input_path") and receipt.get("input_path") is not None:
        case["errors"].append("m2_validation_input_path_mismatch")


def _audit_case(
    case_data: dict[str, Any],
    manifest: dict[str, Any],
    historical_identities: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    case_id = case_data.get("case_id", "unknown")
    case = _empty_case(case_id)
    missing = CASE_REQUIRED_FIELDS - set(case_data)
    if missing:
        case["errors"].append("missing_case_fields")
        _close_case(case)
        return case
    if not isinstance(case_data.get("does_not_prove"), list) or not case_data["does_not_prove"]:
        case["errors"].append("does_not_prove_required")
    if not isinstance(case_data.get("constructed_by_context"), str) or not case_data["constructed_by_context"]:
        case["errors"].append("constructed_by_context_required")
    if not isinstance(case_data.get("reviewed_by_context"), str) or not case_data["reviewed_by_context"]:
        case["errors"].append("reviewed_by_context_required")
    if case_data.get("constructed_by_context") == case_data.get("reviewed_by_context"):
        case["errors"].append("construction_and_review_context_must_differ")
    _validate_m2_receipt(case_data, case)

    source_m1_path = _safe_file(case_data.get("source_m1_artifact"), "source_m1_path", case["errors"])
    source_m1 = None
    if source_m1_path is not None:
        source_m1 = _validate_hashes(
            source_m1_path,
            case_data.get("source_m1_raw_sha256"),
            None,
            "source_m1",
            case["errors"],
            case,
            historical_identities,
        )

    if case_data.get("input_path") is None:
        if case_data.get("m2_validation_status") != "NOT_RUN":
            case["errors"].append("input_missing_for_non_not_run_case")
        _close_case(case)
        return case

    input_path = _safe_file(case_data.get("input_path"), "input_path", case["errors"])
    bundle = None
    if input_path is not None:
        bundle = _validate_hashes(
            input_path,
            case_data.get("raw_sha256"),
            case_data.get("canonical_sha256"),
            "input",
            case["errors"],
            case,
            historical_identities,
        )
    if not isinstance(bundle, dict):
        _close_case(case)
        return case
    if case_data.get("m2_validation_status") != VALID_M2_STATUS:
        case["errors"].append("m2_validation_not_valid")
        _close_case(case)
        return case
    m2_result = validate_m2_bundle(bundle)
    if m2_result.get("status") != VALID_M2_STATUS:
        case["errors"].append("m2_bundle_not_valid")
        _close_case(case)
        return case

    checks = {
        "m3-f01": lambda: _check_f01(bundle, case),
        "m3-f02": lambda: _check_f02(bundle, case),
        "m3-f03": lambda: _check_f03(bundle, case),
        "m3-f04": lambda: _check_f04(bundle, case, source_m1),
        "m3-f05": lambda: _check_f05(bundle, case),
    }
    check = checks.get(case_id)
    if check is None:
        case["errors"].append("unknown_case_id")
    else:
        check()
    _close_case(case)
    return case


def audit_manifest(manifest_path: str | Path) -> dict[str, Any]:
    errors: list[str] = []
    evidence_gaps: list[str] = []
    try:
        manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {
            "status": "invalid",
            "cases": [],
            "errors": ["invalid_manifest_json"],
            "evidence_gaps": [],
        }
    if not isinstance(manifest, dict) or not MANIFEST_REQUIRED_FIELDS.issubset(manifest):
        return {
            "status": "invalid",
            "cases": [],
            "errors": ["invalid_manifest_fields"],
            "evidence_gaps": [],
        }
    if manifest.get("schema_version") != "m3.1-forward-inputs-r2":
        errors.append("invalid_manifest_schema_version")
    if manifest.get("evidence_class") != "independent_m2_input_preparation":
        errors.append("invalid_manifest_evidence_class")
    historical_identities = _historical_identities(errors)
    raw_cases = manifest.get("cases")
    if not isinstance(raw_cases, list):
        return {
            "status": "invalid",
            "cases": [],
            "errors": [*errors, "invalid_manifest_cases"],
            "evidence_gaps": [],
        }
    case_by_id = {case.get("case_id"): case for case in raw_cases if isinstance(case, dict)}
    if len(raw_cases) != len(case_by_id):
        errors.append("duplicate_or_invalid_case_ids")
    if tuple(case_by_id) != EXPECTED_CASE_IDS:
        errors.append("manifest_case_ids_mismatch")
    cases = [
        _audit_case(case_by_id[case_id], manifest, historical_identities)
        for case_id in EXPECTED_CASE_IDS
        if case_id in case_by_id
    ]
    if len(cases) != len(EXPECTED_CASE_IDS):
        errors.append("manifest_case_ids_mismatch")
    for case in cases:
        errors.extend(case["errors"])
        evidence_gaps.extend(case["evidence_gaps"])
    if errors:
        status = "invalid"
    elif evidence_gaps:
        status = "evidence_incomplete"
    else:
        status = "valid"
    return {
        "status": status,
        "cases": cases,
        "errors": sorted(set(errors)),
        "evidence_gaps": sorted(set(evidence_gaps)),
    }


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) != 1:
        return 1
    result = audit_manifest(arguments[0])
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return {"valid": 0, "invalid": 1, "evidence_incomplete": 2}[result["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
