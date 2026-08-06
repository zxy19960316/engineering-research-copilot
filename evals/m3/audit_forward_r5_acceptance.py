#!/usr/bin/env python3
"""Audit explicit r5 task records without treating missing files as task history."""

from __future__ import annotations

import hashlib
import json
import stat
import sys
from pathlib import Path
from typing import Any

from r5_dispatch_contract import (
    CASE_IDS,
    COMPOSER_CASE_IDS,
    COUNTER_KEYS,
    R5_SCHEMA_VERSION,
    derive_counters,
    validate_case_record,
    validate_case_records,
    validate_future_path_sets,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
R5_RESULT_ROOT = REPO_ROOT / "evals" / "m3" / "results" / "forward-r5"
R4_MANIFEST_RELATIVE = "evals/m3/results/forward-r4/acceptance-manifest.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def _load_json(path: Path, code: str, errors: list[str]) -> Any:
    try:
        raw = path.read_bytes()
        if raw.startswith(b"\xef\xbb\xbf"):
            raise ValueError("utf8_bom_forbidden")
        return json.loads(raw.decode("utf-8", errors="strict"))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        errors.append(code)
        return None


def _path_for(result_root: Path, future_paths: dict[str, Any], key: str) -> Path | None:
    raw = future_paths.get(key)
    if not isinstance(raw, str):
        return None
    return result_root / raw


def _require_artifacts(
    case_id: str,
    record: dict[str, Any],
    future_paths: dict[str, Any],
    result_root: Path,
    errors: list[str],
) -> None:
    state = record["state"]
    required: list[str] = []
    if record["task_finalizations_observed"] == 1:
        required.append("model_final_json")
    if state in {"processing_failed", "processed_accepted", "processed_invalid"}:
        required.extend(["context_finalization_json", "case_transaction_json"])
    if state in {"processed_accepted", "processed_invalid"}:
        required.extend(["outcome_json", "validation_json", "validator_receipt_json"])
        if case_id in COMPOSER_CASE_IDS:
            required.extend(
                ["payload_json", "composed_bundle_json", "composer_invocation_receipt_json"]
            )
    elif state == "processing_failed":
        if record["composer_invocations"] == 1:
            required.append("composer_invocation_receipt_json")
        if record["validator_invocations"] == 1:
            required.append("validator_receipt_json")
    for key in required:
        path = _path_for(result_root, future_paths, key)
        if path is None or not path.is_file():
            errors.append(f"artifact_missing:{case_id}:{key}")


def _audit_historical_r4(value: object, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append("historical_r4_reference_invalid")
        return {"status": "invalid", "count_as_r5": False}
    if value.get("path") != R4_MANIFEST_RELATIVE:
        errors.append("historical_r4_path_invalid")
    if value.get("count_as_r5") is not False:
        errors.append("historical_r4_counting_forbidden")
    path = _safe_file(value.get("path"), "historical_r4_manifest", errors)
    if path is not None:
        expected_hash = value.get("raw_sha256")
        if not isinstance(expected_hash, str) or _sha256(path) != expected_hash:
            errors.append("historical_r4_manifest_hash_mismatch")
        historical = _load_json(path, "historical_r4_manifest_invalid_json", errors)
        if not isinstance(historical, dict) or historical.get("status") != "blocked_not_accepted":
            errors.append("historical_r4_not_blocked")
    return {
        "path": value.get("path"),
        "raw_sha256": value.get("raw_sha256"),
        "status": value.get("status"),
        "count_as_r5": value.get("count_as_r5"),
    }


def audit_acceptance_manifest(manifest_path: str | Path) -> dict[str, Any]:
    errors: list[str] = []
    try:
        raw = Path(manifest_path).read_bytes()
        if raw.startswith(b"\xef\xbb\xbf"):
            raise ValueError("utf8_bom_forbidden")
        manifest = json.loads(raw.decode("utf-8", errors="strict"))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        return {
            "status": "invalid",
            "cases": [],
            "counters": {key: 0 for key in COUNTER_KEYS},
            "errors": ["invalid_manifest_json"],
            "evidence_gaps": [],
            "m3_status": "IN_PROGRESS",
            "later_gates": "NOT_RUN",
        }
    if not isinstance(manifest, dict):
        return {
            "status": "invalid",
            "cases": [],
            "counters": {key: 0 for key in COUNTER_KEYS},
            "errors": ["manifest_object_required"],
            "evidence_gaps": [],
            "m3_status": "IN_PROGRESS",
            "later_gates": "NOT_RUN",
        }
    if manifest.get("schema_version") != R5_SCHEMA_VERSION:
        errors.append("manifest_schema_version_invalid")
    if "fresh_contexts_consumed" in manifest:
        errors.append("legacy_fresh_context_counter_forbidden")
    result_root_expected = R5_RESULT_ROOT.resolve()
    try:
        declared_root = (REPO_ROOT / manifest.get("result_root", "")).resolve()
        declared_root.relative_to(result_root_expected)
    except (AttributeError, TypeError, ValueError):
        errors.append("result_root_not_canonical")
    if not result_root_expected.is_dir():
        errors.append("future_result_root_missing")
    raw_cases = manifest.get("cases")
    if not isinstance(raw_cases, list) or len(raw_cases) != len(CASE_IDS):
        errors.append("manifest_cases_invalid")
        raw_cases = []
    case_by_id: dict[str, dict[str, Any]] = {}
    records: list[object] = []
    path_maps: dict[str, object] = {}
    case_results: list[dict[str, Any]] = []
    for item in raw_cases:
        if not isinstance(item, dict):
            errors.append("case_entry_object_required")
            continue
        case_id = item.get("case_id")
        if case_id in case_by_id:
            errors.append(f"case_id_duplicate:{case_id}")
        case_by_id[case_id] = item
    if set(case_by_id) != set(CASE_IDS):
        errors.append("manifest_case_ids_invalid")
    for case_id in CASE_IDS:
        item = case_by_id.get(case_id)
        if item is None:
            errors.append(f"case_missing:{case_id}")
            continue
        record = item.get("record")
        future_paths = item.get("future_paths")
        records.append(record)
        path_maps[case_id] = future_paths
        case_errors = validate_case_record(record)
        if case_errors:
            errors.extend(case_errors)
        if not isinstance(record, dict):
            case_results.append({"case_id": case_id, "record_state": "invalid", "errors": case_errors})
            continue
        case_errors.extend(validate_case_record(record))
        _require_artifacts(case_id, record, future_paths if isinstance(future_paths, dict) else {}, result_root_expected, case_errors)
        errors.extend(case_errors)
        case_results.append(
            {
                "case_id": case_id,
                "record_state": record.get("state"),
                "errors": sorted(set(case_errors)),
            }
        )
    errors.extend(validate_case_records(records))
    errors.extend(validate_future_path_sets(path_maps, result_root_expected, check_existing=False))
    derived: dict[str, int]
    try:
        derived = derive_counters(records)
    except ValueError:
        derived = {key: 0 for key in COUNTER_KEYS}
    counters = manifest.get("counters")
    if not isinstance(counters, dict) or set(counters) != set(COUNTER_KEYS):
        errors.append("manifest_counter_keys_invalid")
        counters = {key: 0 for key in COUNTER_KEYS}
    else:
        for key in COUNTER_KEYS:
            if counters.get(key) != derived.get(key):
                errors.append(f"aggregate_counter_mismatch:{key}")
    historical_r4 = _audit_historical_r4(manifest.get("historical_r4"), errors)
    structural_errors = sorted(set(errors))
    if structural_errors:
        status = "invalid"
    else:
        acceptance_conditions = {
            "task_finalizations_observed": derived["task_finalizations_observed"] == 5,
            "dispatcher_cases_processed": derived["dispatcher_cases_processed"] == 5,
            "composer_invocations": derived["composer_invocations"] == 4,
            "validator_invocations": derived["validator_invocations"] == 5,
            "accepted_cases": derived["accepted_cases"] == 5,
            "transaction_failures": derived["transaction_failures"] == 0,
        }
        all_processed_accepted = all(
            isinstance(record, dict) and record.get("state") == "processed_accepted"
            for record in records
        )
        if not all_processed_accepted:
            acceptance_conditions["processed_accepted_states"] = False
        if all(acceptance_conditions.values()):
            status = "accepted"
        else:
            status = "blocked_not_accepted"
            structural_errors.append("acceptance_requirements_unmet")
    return {
        "status": status,
        "m3_status": "IN_PROGRESS",
        "later_gates": "NOT_RUN",
        "cases": case_results,
        "counters": derived,
        "historical_r4": historical_r4,
        "errors": sorted(set(structural_errors)),
        "evidence_gaps": [],
    }


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) != 1:
        return 2
    result = audit_acceptance_manifest(arguments[0])
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0 if result["status"] == "accepted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
