#!/usr/bin/env python3
"""Validate bundle or expected-blocked outcomes for M3 r3 forward cases."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = REPO_ROOT / "skills" / "engineering-research-copilot" / "scripts"
sys.path.insert(0, str(SCRIPT_ROOT))

from validate_m2_direction_bundle import validate_bundle as validate_m2_bundle  # noqa: E402
from validate_m3_method_bundle import validate_m3_bundle  # noqa: E402


EXPECTED_CASE_IDS = {"m3-f01", "m3-f02", "m3-f03", "m3-f04", "m3-f05"}
TERMINAL_CODE = "unsupported_approved_constraint_change_provenance"
BUNDLE_FIELDS = {"outcome_kind", "bundle"}
BLOCKED_FIELDS = {
    "outcome_kind",
    "terminal_code",
    "original_resource_limits",
    "applied_constraint_changes",
}


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


def _selected_direction(source_m2: dict[str, Any]) -> dict[str, Any] | None:
    try:
        selected_id = source_m2["direction_decision"]["selected_direction_id"]
        directions = source_m2["direction_portfolio"]["directions"]
    except (KeyError, TypeError):
        return None
    matches = [
        direction
        for direction in directions
        if isinstance(direction, dict) and direction.get("direction_id") == selected_id
    ]
    return matches[0] if len(matches) == 1 else None


def _base(case_id: str, kind: Any) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "status": "invalid",
        "outcome_kind": kind,
        "errors": [],
        "evidence_gaps": [],
        "method_bundle_validation": "not_run",
    }


def _close(result: dict[str, Any], accepted_status: str) -> dict[str, Any]:
    result["errors"] = sorted(set(result["errors"]))
    result["evidence_gaps"] = sorted(set(result["evidence_gaps"]))
    if not result["errors"] and not result["evidence_gaps"]:
        result["status"] = accepted_status
    return result


def _validate_bundle_outcome(
    case_id: str,
    source_m2: dict[str, Any],
    outcome: dict[str, Any],
    result: dict[str, Any],
) -> dict[str, Any]:
    if case_id == "m3-f03":
        result["errors"].append("f03_requires_blocked_outcome")
        return _close(result, "accepted")
    if set(outcome) != BUNDLE_FIELDS:
        result["errors"].append("invalid_bundle_outcome_fields")
    bundle = outcome.get("bundle")
    if not isinstance(bundle, dict):
        result["errors"].append("bundle_outcome_missing_bundle")
        return _close(result, "accepted")
    if not _strict_equal(bundle.get("source_m2_bundle"), source_m2):
        result["errors"].append("outcome_source_m2_mismatch")
    validation = validate_m3_bundle(bundle)
    result["method_bundle_validation"] = validation
    if validation.get("status") != "valid":
        result["errors"].append("method_bundle_not_valid")
    return _close(result, "accepted")


def _validate_blocked_outcome(
    case_id: str,
    source_m2: dict[str, Any],
    outcome: dict[str, Any],
    result: dict[str, Any],
) -> dict[str, Any]:
    result["method_bundle_validation"] = "not_applicable_expected_block"
    if case_id != "m3-f03":
        result["errors"].append("blocked_outcome_only_allowed_for_f03")
    if set(outcome) != BLOCKED_FIELDS:
        result["errors"].append("unknown_blocked_outcome_fields")
    if outcome.get("terminal_code") != TERMINAL_CODE:
        result["errors"].append("unexpected_blocked_terminal_code")

    route = source_m2.get("route_output")
    if not isinstance(route, dict):
        result["errors"].append("f03_source_route_required")
        changes: Any = None
    else:
        changes = route.get("approved_constraint_changes")
    if not isinstance(changes, list) or not changes:
        result["errors"].append("upstream_approved_constraint_changes_required")

    direction = _selected_direction(source_m2)
    if direction is None:
        result["errors"].append("selected_direction_missing")
    elif not _strict_equal(
        outcome.get("original_resource_limits"), direction.get("resource_limits")
    ):
        result["errors"].append("original_resource_limits_mismatch")
    if outcome.get("applied_constraint_changes") != []:
        result["errors"].append("approved_constraint_change_applied")
    return _close(result, "accepted_expected_block")


def validate_forward_outcome(
    case_id: str,
    source_m2: Any,
    outcome: Any,
) -> dict[str, Any]:
    """Return case acceptance without relabeling a blocked outcome as a bundle."""

    kind = outcome.get("outcome_kind") if isinstance(outcome, dict) else None
    result = _base(case_id, kind)
    if case_id not in EXPECTED_CASE_IDS:
        result["errors"].append("unknown_case_id")
    if not isinstance(source_m2, dict):
        result["errors"].append("invalid_source_m2_bundle")
        return _close(result, "accepted")
    m2_validation = validate_m2_bundle(source_m2)
    if m2_validation.get("status") != "valid":
        result["errors"].append("source_m2_bundle_not_valid")
    if not isinstance(outcome, dict):
        result["errors"].append("invalid_forward_outcome")
        return _close(result, "accepted")
    if kind == "bundle":
        return _validate_bundle_outcome(case_id, source_m2, outcome, result)
    if kind == "blocked":
        return _validate_blocked_outcome(case_id, source_m2, outcome, result)
    result["errors"].append("unknown_outcome_kind")
    return _close(result, "accepted")


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
        output = _base("unknown", None)
        output["errors"] = ["expected_case_source_outcome_paths"]
    else:
        case_id, source_name, outcome_name = arguments
        try:
            source_m2 = _load_object(Path(source_name))
            outcome = _load_object(Path(outcome_name))
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
            output = _base(case_id, None)
            output["errors"] = ["unreadable_or_invalid_forward_outcome_input"]
        else:
            output = validate_forward_outcome(case_id, source_m2, outcome)
    print(
        json.dumps(
            output,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    )
    return 0 if output["status"] in {"accepted", "accepted_expected_block"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
