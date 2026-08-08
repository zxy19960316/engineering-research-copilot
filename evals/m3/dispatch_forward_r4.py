#!/usr/bin/env python3
"""Preflight and dispatch one frozen r4 case without caller-supplied paths."""

from __future__ import annotations

import hashlib
import json
import stat
import sys
from pathlib import Path
from typing import Any, Callable


REPO_ROOT = Path(__file__).resolve().parents[2]
R4_RESULT_ROOT = REPO_ROOT / "evals" / "m3" / "results" / "forward-r4"
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


def _relative(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()


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
        errors.append(f"{code}_missing")
        return None
    return resolved


def _load_manifest(path: Path, errors: list[str]) -> dict[str, Any] | None:
    try:
        raw = path.read_bytes()
        if raw.startswith(b"\xef\xbb\xbf"):
            raise ValueError("utf8_bom_forbidden")
        value = json.loads(raw.decode("utf-8", errors="strict"))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        errors.append("manifest_unreadable_or_invalid_json")
        return None
    if not isinstance(value, dict):
        errors.append("manifest_object_required")
        return None
    return value


def _future_paths(case_id: str) -> dict[str, Path]:
    return {
        **{
            f"output_{suffix.lstrip('.').replace('.', '_')}": R4_RESULT_ROOT
            / f"{case_id}{suffix}"
            for suffix in FUTURE_OUTPUT_SUFFIXES
        },
        **{
            f"receipt_{suffix.lstrip('.').replace('.', '_')}": R4_RESULT_ROOT
            / f"{case_id}{suffix}"
            for suffix in FUTURE_RECEIPT_SUFFIXES
        },
    }


def _close(errors: list[str], **fields: Any) -> dict[str, Any]:
    unique_errors = sorted(set(errors))
    return {
        "status": "ready" if not unique_errors else "blocked",
        "errors": unique_errors,
        "fresh_context_consumed": False,
        **fields,
    }


def preflight_case(manifest_path: Path, case_id: str) -> dict[str, Any]:
    """Return a manifest-derived dispatch plan without writing or invoking."""

    errors: list[str] = []
    manifest = _load_manifest(manifest_path, errors)
    if manifest is None:
        return _close(errors, case_id=case_id)
    if manifest.get("schema_version") != "m3.1-forward-acceptance-r4-v1":
        errors.append("manifest_schema_version_invalid")
    if manifest.get("prompts_frozen") is not True:
        errors.append("prompts_not_frozen")
    if manifest.get("fresh_contexts_consumed") != 0:
        errors.append("fresh_contexts_already_consumed")
    cases = manifest.get("cases")
    if not isinstance(cases, list):
        return _close(errors + ["manifest_cases_invalid"], case_id=case_id)
    matches = [case for case in cases if isinstance(case, dict) and case.get("case_id") == case_id]
    if len(matches) != 1:
        return _close(errors + ["case_id_not_unique"], case_id=case_id)
    case = matches[0]
    forbidden_keys = [
        key
        for key in case
        if "output" in key.lower()
        or "receipt" in key.lower()
        or key == "fresh_context_id"
    ]
    if forbidden_keys:
        errors.append("output_or_receipt_fields_forbidden")
    source_relative = case.get("input_path")
    if case_id == "m3-f03" and source_relative != F03_SOURCE:
        errors.append("f03_source_alias_forbidden")
    source_path = _safe_file(source_relative, "source_input", errors)
    prompt_path = _safe_file(case.get("prompt_path"), "prompt", errors)
    contract_path = _safe_file(case.get("contract_path"), "contract", errors)
    for label, path, hash_field in (
        ("source_input", source_path, "input_raw_sha256"),
        ("prompt", prompt_path, "prompt_raw_sha256"),
        ("contract", contract_path, "contract_raw_sha256"),
    ):
        expected = case.get(hash_field)
        if path is None:
            continue
        if not isinstance(expected, str) or len(expected) != 64:
            errors.append(f"{label}_raw_sha256_invalid")
        elif _sha256(path) != expected:
            errors.append(f"{label}_raw_sha256_mismatch")
    if case.get("eligibility_status") != "eligible":
        errors.append("case_not_eligible")
    future_paths = _future_paths(case_id)
    if not R4_RESULT_ROOT.is_dir():
        errors.append("future_result_root_missing")
    for kind, path in future_paths.items():
        if path.exists():
            errors.append(
                "future_receipt_exists" if kind.startswith("receipt_") else "future_output_exists"
            )
    plan = {
        "case_id": case_id,
        "source_input_relative_path": source_relative,
        "source_input_path": source_path,
        "source_input_raw_sha256": case.get("input_raw_sha256"),
        "prompt_path": prompt_path,
        "prompt_raw_sha256": case.get("prompt_raw_sha256"),
        "contract_path": contract_path,
        "contract_raw_sha256": case.get("contract_raw_sha256"),
        "future_paths": future_paths,
        "manifest_path": manifest_path.resolve(),
    }
    return _close(errors, **plan)


def dispatch_case(
    manifest_path: Path,
    case_id: str,
    consume_once: Callable[[dict[str, Any]], Any],
) -> dict[str, Any]:
    """Invoke the supplied consumable callback only after a clean preflight."""

    plan = preflight_case(manifest_path, case_id)
    if plan["status"] != "ready":
        return plan
    try:
        consume_once(plan)
    except Exception:
        return {
            **plan,
            "status": "consumed_with_callback_failure",
            "fresh_context_consumed": True,
            "errors": ["consumable_callback_failed"],
        }
    return {
        **plan,
        "status": "dispatched",
        "fresh_context_consumed": True,
    }


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        try:
            return _relative(value)
        except ValueError:
            return value.as_posix()
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) != 2:
        print(json.dumps({"status": "blocked", "errors": ["expected_manifest_and_case_id"]}))
        return 2
    result = preflight_case(Path(arguments[0]), arguments[1])
    print(json.dumps(_json_safe(result), ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0 if result["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
