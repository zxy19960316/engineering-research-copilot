#!/usr/bin/env python3
"""Read-only batch preflight for the frozen M3.1.1 r5 acceptance contract."""

from __future__ import annotations

import hashlib
import json
import stat
import sys
from pathlib import Path
from typing import Any, Callable

from r5_dispatch_contract import (
    CASE_IDS,
    COUNTER_KEYS,
    R5_SCHEMA_VERSION,
    validate_future_path_sets,
    validate_future_paths,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
R5_RESULT_ROOT = REPO_ROOT / "evals" / "m3" / "results" / "forward-r5"
F03_SOURCE = "evals/m3/forward-inputs-r2/m3-f03-approved-change.bundle.json"


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
        errors.append(f"{code}_not_file")
        return None
    return resolved


def _load_json(path: Path, errors: list[str], code: str) -> dict[str, Any] | None:
    try:
        raw = path.read_bytes()
        if raw.startswith(b"\xef\xbb\xbf"):
            raise ValueError("utf8_bom_forbidden")
        value = json.loads(raw.decode("utf-8", errors="strict"))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        errors.append(code)
        return None
    if not isinstance(value, dict):
        errors.append(code)
        return None
    return value


def _load_manifest(path: Path, errors: list[str]) -> dict[str, Any] | None:
    return _load_json(path, errors, "manifest_unreadable_or_invalid_json")


def _hash_check(path: Path | None, expected: Any, code: str, errors: list[str]) -> None:
    if path is None:
        return
    if not isinstance(expected, str) or len(expected) != 64:
        errors.append(f"{code}_sha256_invalid")
    elif _sha256(path) != expected:
        errors.append(f"{code}_sha256_mismatch")


def _preflight_case(case: object, result_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(case, dict):
        return {"case_id": "unknown", "status": "blocked", "errors": ["case_object_required"]}
    case_id = case.get("case_id")
    if not isinstance(case_id, str) or case_id not in CASE_IDS:
        return {"case_id": case_id, "status": "blocked", "errors": ["case_id_invalid"]}
    for key in case:
        normalized = str(key).lower()
        if (
            "output" in normalized
            or "receipt" in normalized
            or normalized in {"fresh_context_id", "task_id"}
        ) and key != "future_paths":
            errors.append("case_output_or_receipt_field_forbidden")
    source_relative = case.get("input_path")
    if case_id == "m3-f03" and source_relative != F03_SOURCE:
        errors.append("f03_source_alias_forbidden")
    source_path = _safe_file(source_relative, "source_input", errors)
    prompt_path = _safe_file(case.get("prompt_path"), "prompt", errors)
    contract_path = _safe_file(case.get("contract_path"), "contract", errors)
    validation_path = _safe_file(case.get("m2_validation_path"), "m2_validation", errors)
    eligibility_path = _safe_file(case.get("eligibility_path"), "eligibility", errors)
    _hash_check(source_path, case.get("input_raw_sha256"), "source_input", errors)
    _hash_check(prompt_path, case.get("prompt_raw_sha256"), "prompt", errors)
    _hash_check(contract_path, case.get("contract_raw_sha256"), "contract", errors)
    _hash_check(validation_path, case.get("m2_validation_raw_sha256"), "m2_validation", errors)
    _hash_check(eligibility_path, case.get("eligibility_raw_sha256"), "eligibility", errors)
    if case.get("eligibility_status") != "eligible":
        errors.append("case_not_eligible")
    if validation_path is not None:
        validation = _load_json(validation_path, errors, "m2_validation_invalid_json")
        if validation is not None and (
            validation.get("status") != "valid"
            or validation.get("errors") != []
            or validation.get("evidence_gaps") != []
        ):
            errors.append("m2_validation_not_valid")
    if eligibility_path is not None:
        eligibility = _load_json(eligibility_path, errors, "eligibility_invalid_json")
        if eligibility is not None and eligibility.get("status") != "eligible":
            errors.append("eligibility_receipt_not_eligible")
    future_paths = case.get("future_paths")
    errors.extend(validate_future_paths(case_id, future_paths, result_root))
    if not result_root.is_dir():
        errors.append("future_result_root_missing")
    plan = {
        "case_id": case_id,
        "source_input_relative_path": source_relative,
        "source_input_path": source_path,
        "source_input_raw_sha256": case.get("input_raw_sha256"),
        "prompt_path": prompt_path,
        "prompt_raw_sha256": case.get("prompt_raw_sha256"),
        "contract_path": contract_path,
        "contract_raw_sha256": case.get("contract_raw_sha256"),
        "m2_validation_path": validation_path,
        "eligibility_path": eligibility_path,
        "future_paths": future_paths,
        "result_root": result_root,
    }
    return {
        **plan,
        "status": "ready" if not errors else "blocked",
        "errors": sorted(set(errors)),
    }


def _zero_counters(manifest: dict[str, Any], errors: list[str]) -> None:
    if "fresh_contexts_consumed" in manifest:
        errors.append("legacy_fresh_context_counter_forbidden")
    counters = manifest.get("counters")
    if not isinstance(counters, dict):
        errors.append("manifest_counters_invalid")
        return
    if set(counters) != set(COUNTER_KEYS):
        errors.append("manifest_counter_keys_invalid")
        return
    for key in COUNTER_KEYS:
        if counters.get(key) != 0:
            errors.append(f"manifest_counter_nonzero:{key}")


def preflight_batch(manifest_path: Path, result_root: Path | None = None) -> dict[str, Any]:
    """Dry-preflight every case before any caller callback can run."""

    errors: list[str] = []
    active_result_root = R5_RESULT_ROOT if result_root is None else Path(result_root)
    manifest = _load_manifest(manifest_path, errors)
    if manifest is None:
        return {"status": "blocked", "errors": sorted(set(errors)), "plans": [], "side_effects": []}
    if manifest.get("schema_version") != R5_SCHEMA_VERSION:
        errors.append("manifest_schema_version_invalid")
    if manifest.get("status") != "ready_for_authorized_fresh_contexts":
        errors.append("manifest_status_not_ready")
    if manifest.get("prompts_frozen") is not True:
        errors.append("prompts_not_frozen")
    _zero_counters(manifest, errors)
    expected_root = _relative(active_result_root)
    if manifest.get("result_root") != expected_root:
        errors.append("result_root_not_canonical")
    raw_cases = manifest.get("cases")
    if not isinstance(raw_cases, list):
        return {
            "status": "blocked",
            "errors": sorted(set(errors + ["manifest_cases_invalid"])),
            "plans": [],
            "side_effects": [],
        }
    case_by_id: dict[str, object] = {}
    for case in raw_cases:
        if isinstance(case, dict) and isinstance(case.get("case_id"), str):
            if case["case_id"] in case_by_id:
                errors.append(f"case_id_duplicate:{case['case_id']}")
            case_by_id[case["case_id"]] = case
        else:
            errors.append("case_object_or_id_invalid")
    if set(case_by_id) != set(CASE_IDS) or len(raw_cases) != len(CASE_IDS):
        errors.append("manifest_case_ids_invalid")

    plans: list[dict[str, Any]] = []
    path_maps: dict[str, object] = {}
    for case_id in CASE_IDS:
        case = case_by_id.get(case_id)
        if case is None:
            errors.append(f"case_missing:{case_id}")
            continue
        plan = _preflight_case(case, active_result_root)
        plans.append(plan)
        path_maps[case_id] = case.get("future_paths") if isinstance(case, dict) else None
        errors.extend(plan["errors"])
    errors.extend(validate_future_path_sets(path_maps, active_result_root))
    if errors:
        return {
            "status": "blocked",
            "errors": sorted(set(errors)),
            "plans": [],
            "side_effects": [],
            "case_ids_preflighted": [plan["case_id"] for plan in plans],
        }
    return {
        "status": "ready",
        "errors": [],
        "plans": plans,
        "side_effects": [],
        "case_ids_preflighted": list(CASE_IDS),
    }


def preflight_case(manifest_path: Path, case_id: str) -> dict[str, Any]:
    """Return one plan only after the entire five-case batch is clean."""

    batch = preflight_batch(manifest_path)
    if batch["status"] != "ready":
        return {**batch, "case_id": case_id, "plan": None}
    matches = [plan for plan in batch["plans"] if plan["case_id"] == case_id]
    if len(matches) != 1:
        return {
            "status": "blocked",
            "errors": ["case_id_not_unique"],
            "plans": [],
            "plan": None,
            "side_effects": [],
            "case_id": case_id,
        }
    return {**batch, "case_id": case_id, "plan": matches[0]}


def dispatch_batch(
    manifest_path: Path,
    consume_once: Callable[[dict[str, Any]], Any],
) -> dict[str, Any]:
    """Run the callback once per case, but only after a clean batch preflight."""

    batch = preflight_batch(manifest_path)
    if batch["status"] != "ready":
        return {
            **batch,
            "status": "blocked",
            "callback_invocations": 0,
            "callback_failures": 0,
            "plans": [],
        }
    callback_invocations = 0
    for plan in batch["plans"]:
        callback_invocations += 1
        try:
            consume_once(plan)
        except Exception:
            return {
                **batch,
                "status": "callback_failed",
                "callback_invocations": callback_invocations,
                "callback_failures": 1,
                "plans": batch["plans"],
                "errors": ["consumable_callback_failed"],
            }
    return {
        **batch,
        "status": "dispatched",
        "callback_invocations": callback_invocations,
        "callback_failures": 0,
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
    if len(arguments) != 1:
        print(json.dumps({"status": "blocked", "errors": ["expected_manifest_path"]}))
        return 2
    result = preflight_batch(Path(arguments[0]))
    print(json.dumps(_json_safe(result), ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0 if result["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
