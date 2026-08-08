#!/usr/bin/env python3
"""Audit immutable M3 fresh-context results without re-running the validator."""

from __future__ import annotations

import hashlib
import json
import re
import stat
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
PREVIOUS_FORWARD_ROOT = (REPO_ROOT / "evals" / "m3" / "results" / "forward").resolve()
EXPECTED_CASE_IDS = ("m3-f01", "m3-f02", "m3-f03", "m3-f04", "m3-f05")
EXPECTED_RESULTS = {
    "m3-f01": ("valid", [], []),
    "m3-f02": ("valid", [], []),
    "m3-f03": ("invalid", ["unsupported_approved_constraint_change_provenance"], []),
    "m3-f04": ("valid", [], []),
    "m3-f05": ("valid", [], []),
}
REQUIRED_CASE_FIELDS = {
    "case_id",
    "input_path",
    "input_raw_sha256",
    "prompt_sha256",
    "output_path",
    "output_raw_sha256",
    "validation_path",
    "validation_raw_sha256",
    "context_path",
    "expected_status",
    "expected_errors",
    "expected_evidence_gaps",
    "finalization_count",
    "validator_invocation_count",
    "loaded_references",
    "side_effects",
    "deviations",
    "accepted",
}
REQUIRED_OUTPUT_FIELDS = {
    "schema_version",
    "source_m2_bundle",
    "source_m2_bundle_hash",
    "selected_direction_id",
    "selected_direction_hash",
    "coaching_mode",
    "method_cards",
    "domain_overlays",
}
REQUIRED_CONTEXT_FIELDS = {
    "context_id",
    "input_sha256",
    "prompt_sha256",
    "output_sha256",
    "validation_sha256",
    "loaded_references",
    "finalization_count",
    "validator_invocation_count",
    "side_effects",
    "deviations",
    "limitations",
}
FORBIDDEN_REFERENCE_MARKERS = (
    "validate_m3_method_bundle.py",
    "tests/",
    "tests\\",
    "evals/m3/fixtures",
    "evals\\m3\\fixtures",
    "build_fixtures.py",
    "adversarial-cases.json",
    "offline-results.json",
    "results/forward/",
    "results\\forward\\",
)
EXPECTED_PREVIOUS_RESULTS = {
    f"evals/m3/results/forward/m3-f0{case}.{suffix}"
    for case in (2, 3, 5)
    for suffix in ("output.json", "validation.json", "context.md")
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _has_reparse_point(path: Path) -> bool:
    try:
        attributes = getattr(path.stat(), "st_file_attributes", 0)
    except OSError:
        return True
    return bool(attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def _safe_file(
    raw_path: Any,
    code_prefix: str,
    errors: list[str],
    allow_previous: bool = False,
) -> Path | None:
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
    if not allow_previous and (resolved == PREVIOUS_FORWARD_ROOT or PREVIOUS_FORWARD_ROOT in resolved.parents):
        errors.append(f"{code_prefix}_previous_result_forbidden")
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


def _load_json(path: Path, code: str, errors: list[str]) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        errors.append(code)
        return None


def _parse_context(text: str) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for line in text.splitlines():
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", line.strip())
        if not match:
            continue
        key, raw_value = match.groups()
        value = raw_value.strip()
        if value in {"", "null", "~"}:
            values[key] = None if value else ""
            continue
        try:
            values[key] = json.loads(value)
        except json.JSONDecodeError:
            if value.startswith("[") and value.endswith("]"):
                values[key] = [
                    item.strip().strip("\"'")
                    for item in value[1:-1].split(",")
                    if item.strip()
                ]
            else:
                values[key] = value
    return values


def _forbidden_reference(reference: Any) -> bool:
    if not isinstance(reference, str):
        return True
    normalized = reference.replace("\\", "/").lower()
    return any(marker in normalized for marker in FORBIDDEN_REFERENCE_MARKERS)


def _case_audit(case_data: dict[str, Any]) -> dict[str, Any]:
    case_id = case_data.get("case_id", "unknown")
    case_result = {"case_id": case_id, "status": "valid", "errors": [], "evidence_gaps": []}
    errors: list[str] = case_result["errors"]
    expected = EXPECTED_RESULTS.get(case_id)
    if expected is None:
        errors.append("unknown_case_id")
    if not REQUIRED_CASE_FIELDS.issubset(case_data):
        errors.append("missing_acceptance_case_fields")
        case_result["status"] = "invalid"
        return case_result
    if expected is not None and (
        case_data.get("expected_status"),
        case_data.get("expected_errors"),
        case_data.get("expected_evidence_gaps"),
    ) != expected:
        errors.append("expected_result_mismatch")
    if case_data.get("accepted") is not True:
        errors.append("case_not_accepted")
    if case_data.get("finalization_count") != 1 or case_data.get("validator_invocation_count") != 1:
        errors.append("fresh_case_one_shot_violation")
    if case_data.get("side_effects") != [] or case_data.get("deviations") != []:
        errors.append("fresh_case_one_shot_violation")
    references = case_data.get("loaded_references")
    if not isinstance(references, list) or not references or any(
        _forbidden_reference(reference) for reference in references
    ):
        errors.append("forbidden_fresh_reference")

    paths: dict[str, Path | None] = {}
    for field in ("input_path", "prompt_path", "output_path", "validation_path", "context_path"):
        if field == "prompt_path" and field not in case_data:
            errors.append("prompt_path_missing")
            paths[field] = None
            continue
        paths[field] = _safe_file(case_data.get(field), field, errors)

    for field, hash_field in (
        ("input_path", "input_raw_sha256"),
        ("prompt_path", "prompt_sha256"),
        ("output_path", "output_raw_sha256"),
        ("validation_path", "validation_raw_sha256"),
    ):
        path = paths[field]
        if path is not None and (
            not isinstance(case_data.get(hash_field), str)
            or _sha256(path) != case_data.get(hash_field)
        ):
            errors.append(f"{field.replace('_path', '')}_raw_sha256_mismatch")

    validation = None
    if paths["validation_path"] is not None:
        validation = _load_json(paths["validation_path"], "validation_json_invalid", errors)
    if not isinstance(validation, dict) or set(validation) != {"status", "errors", "evidence_gaps"}:
        errors.append("validation_json_not_closed")
    else:
        if not isinstance(validation["errors"], list) or not isinstance(validation["evidence_gaps"], list):
            errors.append("validation_json_not_closed")
        elif (
            validation["status"],
            validation["errors"],
            validation["evidence_gaps"],
        ) != (
            case_data.get("expected_status"),
            case_data.get("expected_errors"),
            case_data.get("expected_evidence_gaps"),
        ):
            errors.append("validator_result_mismatch")

    output = None
    if paths["output_path"] is not None:
        output = _load_json(paths["output_path"], "output_json_invalid", errors)
    if not isinstance(output, dict) or not REQUIRED_OUTPUT_FIELDS.issubset(output):
        errors.append("output_m3_shape_incomplete")

    context = None
    if paths["context_path"] is not None:
        try:
            context = _parse_context(paths["context_path"].read_text(encoding="utf-8"))
        except (OSError, UnicodeError):
            errors.append("context_invalid")
    if not isinstance(context, dict) or not REQUIRED_CONTEXT_FIELDS.issubset(context):
        errors.append("context_fields_incomplete")
    else:
        if context.get("input_sha256") != case_data.get("input_raw_sha256"):
            errors.append("context_input_hash_mismatch")
        if context.get("prompt_sha256") != case_data.get("prompt_sha256"):
            errors.append("context_prompt_hash_mismatch")
        if context.get("output_sha256") != case_data.get("output_raw_sha256"):
            errors.append("context_output_hash_mismatch")
        if context.get("validation_sha256") != case_data.get("validation_raw_sha256"):
            errors.append("context_validation_hash_mismatch")
        if context.get("finalization_count") != 1 or context.get("validator_invocation_count") != 1:
            errors.append("fresh_case_one_shot_violation")
        if context.get("side_effects") != [] or context.get("deviations") != []:
            errors.append("fresh_case_one_shot_violation")
        context_references = context.get("loaded_references")
        if not isinstance(context_references, list) or any(
            _forbidden_reference(reference) for reference in context_references
        ):
            errors.append("forbidden_fresh_reference")
        elif sorted(context_references) != sorted(references):
            errors.append("context_references_mismatch")

    if errors:
        case_result["status"] = "invalid"
    return case_result


def audit_acceptance_manifest(manifest_path: str | Path) -> dict[str, Any]:
    try:
        manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {"status": "invalid", "cases": [], "errors": ["invalid_manifest_json"], "evidence_gaps": []}
    errors: list[str] = []
    if not isinstance(manifest, dict) or manifest.get("schema_version") != "m3.1-forward-acceptance-r2":
        errors.append("invalid_manifest_schema_version")
    raw_cases = manifest.get("cases") if isinstance(manifest, dict) else None
    if not isinstance(raw_cases, list):
        return {"status": "invalid", "cases": [], "errors": [*errors, "invalid_manifest_cases"], "evidence_gaps": []}
    case_by_id = {case.get("case_id"): case for case in raw_cases if isinstance(case, dict)}
    if len(raw_cases) != len(case_by_id) or set(case_by_id) != set(EXPECTED_CASE_IDS):
        errors.append("manifest_case_ids_mismatch")
    cases = [
        _case_audit(case_by_id[case_id])
        for case_id in EXPECTED_CASE_IDS
        if case_id in case_by_id
    ]
    previous = manifest.get("preserved_previous_results")
    previous_paths: set[str] = set()
    if not isinstance(previous, list):
        errors.append("preserved_previous_results_missing")
    else:
        for item in previous:
            if not isinstance(item, dict) or not isinstance(item.get("path"), str):
                errors.append("preserved_previous_result_invalid")
                continue
            normalized = item["path"].replace("\\", "/")
            previous_paths.add(normalized)
            path = _safe_file(item["path"], "preserved_previous_result_path", errors, allow_previous=True)
            if path is not None and (
                not isinstance(item.get("raw_sha256"), str)
                or _sha256(path) != item.get("raw_sha256")
            ):
                errors.append("preserved_previous_result_hash_mismatch")
    if previous_paths != EXPECTED_PREVIOUS_RESULTS:
        errors.append("preserved_previous_results_incomplete")
    for case in cases:
        errors.extend(case["errors"])
    status = "invalid" if errors else "valid"
    return {
        "status": status,
        "cases": cases,
        "errors": sorted(set(errors)),
        "evidence_gaps": [],
    }


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) != 1:
        return 1
    result = audit_acceptance_manifest(arguments[0])
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return 0 if result["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
