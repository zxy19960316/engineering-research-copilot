#!/usr/bin/env python3
"""Audit the r4 frozen preparation state without consuming a case."""

from __future__ import annotations

import hashlib
import json
import stat
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
R4_RESULT_ROOT = REPO_ROOT / "evals" / "m3" / "results" / "forward-r4"
EXPECTED_CASE_IDS = ("m3-f01", "m3-f02", "m3-f03", "m3-f04", "m3-f05")
F03_SOURCE = "evals/m3/forward-inputs-r2/m3-f03-approved-change.bundle.json"
FUTURE_OUTPUT_SUFFIXES = (
    ".payload.json",
    ".bundle.json",
    ".outcome.json",
    ".validation.json",
    ".context.md",
)
FUTURE_RECEIPT_SUFFIXES = (
    ".composer-receipt.json",
    ".validator-receipt.json",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        raw = path.read_bytes()
        if raw.startswith(b"\xef\xbb\xbf"):
            return None
        value = json.loads(raw.decode("utf-8", errors="strict"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _safe_file(raw_path: Any, code: str, errors: list[str]) -> Path | None:
    if not isinstance(raw_path, str) or not raw_path:
        errors.append(f"{code}_missing")
        return None
    candidate = Path(raw_path)
    resolved = (candidate if candidate.is_absolute() else REPO_ROOT / candidate).resolve()
    try:
        resolved.relative_to(REPO_ROOT.resolve())
    except ValueError:
        errors.append(f"{code}_outside_repository")
        return None
    if not resolved.exists():
        errors.append(f"{code}_missing")
        return None
    current = resolved
    while True:
        try:
            attributes = getattr(current.stat(), "st_file_attributes", 0)
        except OSError:
            errors.append(f"{code}_unreadable")
            return None
        if current.is_symlink() or attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            errors.append(f"{code}_reparse_point_forbidden")
            return None
        if current == REPO_ROOT.resolve():
            break
        if current.parent == current:
            errors.append(f"{code}_outside_repository")
            return None
        current = current.parent
    if not resolved.is_file():
        errors.append(f"{code}_not_file")
        return None
    return resolved


def _forbidden_keys(value: Any) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).lower()
            if (
                "output" in normalized
                or "receipt" in normalized
                or normalized == "fresh_context_id"
                or normalized.startswith("expected_")
                or normalized.startswith("observed_")
                or normalized == "accepted"
            ):
                return True
            if _forbidden_keys(child):
                return True
    elif isinstance(value, list):
        return any(_forbidden_keys(item) for item in value)
    return False


def _case_result(
    case: dict[str, Any],
    result_root: Path,
) -> dict[str, Any]:
    case_id = case.get("case_id", "unknown")
    errors: list[str] = []
    if _forbidden_keys(case):
        errors.append("output_or_receipt_fields_forbidden")
    if case.get("eligibility_status") != "eligible":
        errors.append("case_not_eligible")
    if case_id == "m3-f03" and case.get("input_path") != F03_SOURCE:
        errors.append("f03_source_alias_forbidden")
    paths: dict[str, Path | None] = {}
    for field, code in (
        ("input_path", "source_input"),
        ("prompt_path", "prompt"),
        ("contract_path", "contract"),
    ):
        paths[field] = _safe_file(case.get(field), code, errors)
    for field, path, code in (
        ("input_raw_sha256", paths["input_path"], "source_input"),
        ("prompt_raw_sha256", paths["prompt_path"], "prompt"),
        ("contract_raw_sha256", paths["contract_path"], "contract"),
    ):
        expected = case.get(field)
        if path is None:
            continue
        if not isinstance(expected, str) or len(expected) != 64:
            errors.append(f"{code}_raw_sha256_invalid")
        elif _sha256(path) != expected:
            errors.append(f"{code}_raw_sha256_mismatch")
    if not result_root.is_dir():
        errors.append("future_result_root_missing")
    for suffix in (*FUTURE_OUTPUT_SUFFIXES, *FUTURE_RECEIPT_SUFFIXES):
        future_path = result_root / f"{case_id}{suffix}"
        if future_path.exists():
            errors.append(
                "future_receipt_exists"
                if suffix in FUTURE_RECEIPT_SUFFIXES
                else "future_output_exists"
            )
    return {
        "case_id": case_id,
        "status": "eligible" if not errors else "invalid",
        "errors": sorted(set(errors)),
        "evidence_gaps": [],
    }


def audit_preparation(manifest_path: Path) -> dict[str, Any]:
    """Return a closed readiness audit for a frozen r4 acceptance manifest."""

    errors: list[str] = []
    manifest = _load_json(manifest_path)
    if manifest is None:
        return {
            "status": "invalid",
            "cases": [],
            "errors": ["invalid_manifest_json"],
            "evidence_gaps": [],
        }
    if manifest.get("schema_version") != "m3.1-forward-acceptance-r4-v1":
        errors.append("manifest_schema_version_invalid")
    if manifest.get("status") != "ready_for_authorized_fresh_contexts":
        errors.append("manifest_status_not_ready")
    if manifest.get("prompts_frozen") is not True:
        errors.append("prompts_not_frozen")
    if manifest.get("fresh_contexts_consumed") != 0:
        errors.append("fresh_contexts_nonzero")
    if _forbidden_keys(manifest):
        errors.append("output_or_receipt_fields_forbidden")
    raw_cases = manifest.get("cases")
    if not isinstance(raw_cases, list):
        errors.append("manifest_cases_invalid")
        raw_cases = []
    case_by_id = {
        case.get("case_id"): case
        for case in raw_cases
        if isinstance(case, dict) and isinstance(case.get("case_id"), str)
    }
    if len(raw_cases) != len(case_by_id) or set(case_by_id) != set(EXPECTED_CASE_IDS):
        errors.append("manifest_case_ids_mismatch")
    cases = [
        _case_result(case_by_id[case_id], R4_RESULT_ROOT)
        for case_id in EXPECTED_CASE_IDS
        if case_id in case_by_id
    ]
    for case in cases:
        errors.extend(case["errors"])
    return {
        "status": "valid" if not errors else "invalid",
        "cases": cases,
        "prompts_frozen": manifest.get("prompts_frozen"),
        "fresh_contexts_consumed": manifest.get("fresh_contexts_consumed"),
        "errors": sorted(set(errors)),
        "evidence_gaps": [],
    }


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) != 1:
        return 2
    result = audit_preparation(Path(arguments[0]))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0 if result["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
