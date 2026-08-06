#!/usr/bin/env python3
"""Pure, closed contracts shared by M3.1.1 r5 preparation and acceptance."""

from __future__ import annotations

from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Mapping


R5_SCHEMA_VERSION = "m3.1-forward-acceptance-r5-v1"
CASE_IDS = ("m3-f01", "m3-f02", "m3-f03", "m3-f04", "m3-f05")
COMPOSER_CASE_IDS = frozenset({"m3-f01", "m3-f02", "m3-f04", "m3-f05"})
CANONICAL_PATH_KEYS = (
    "model_final_json",
    "payload_json",
    "composed_bundle_json",
    "outcome_json",
    "validation_json",
    "composer_invocation_receipt_json",
    "validator_receipt_json",
    "context_finalization_json",
    "case_transaction_json",
)
PATH_SUFFIXES = {
    "model_final_json": ".model-final.json",
    "payload_json": ".payload.json",
    "composed_bundle_json": ".bundle.json",
    "outcome_json": ".outcome.json",
    "validation_json": ".validation.json",
    "composer_invocation_receipt_json": ".composer-receipt.json",
    "validator_receipt_json": ".validator-receipt.json",
    "context_finalization_json": ".context.json",
    "case_transaction_json": ".transaction.json",
}
NULLABLE_PATH_KEYS = frozenset(
    {"payload_json", "composed_bundle_json", "composer_invocation_receipt_json"}
)
COUNTER_KEYS = (
    "tasks_launched",
    "task_finalizations_observed",
    "dispatcher_cases_preflighted",
    "dispatcher_cases_processed",
    "composer_invocations",
    "validator_invocations",
    "accepted_cases",
    "transaction_failures",
)
CASE_STATES = (
    "not_launched",
    "launched",
    "finalized_unprocessed",
    "processing_failed",
    "processed_accepted",
    "processed_invalid",
)
REQUIRED_CASE_RECORD_KEYS = frozenset(
    {
        "case_id",
        "task_id",
        "state",
        "tasks_launched",
        "task_finalizations_observed",
        "dispatcher_cases_preflighted",
        "dispatcher_cases_processed",
        "composer_invocations",
        "validator_invocations",
        "accepted",
        "transaction_failures",
    }
)


def canonical_future_paths(case_id: str, result_root: Path) -> dict[str, str | None]:
    """Return the exact r5 path-key map relative to ``result_root``.

    ``result_root`` is accepted so callers can derive and validate a map in one
    place. The returned strings are intentionally root-relative POSIX names;
    no caller may replace them with an absolute path or an alias.
    """

    if case_id not in CASE_IDS:
        raise ValueError("unknown_case_id")
    del result_root
    return {
        key: None if case_id == "m3-f03" and key in NULLABLE_PATH_KEYS else f"{case_id}{suffix}"
        for key, suffix in PATH_SUFFIXES.items()
    }


def _add_path_error(errors: list[str], code: str) -> None:
    if code not in errors:
        errors.append(code)


def _unsafe_relative_path(raw: str) -> bool:
    if not raw or "\x00" in raw or "\\" in raw:
        return True
    if raw.startswith(("/", "//")):
        return True
    if PureWindowsPath(raw).drive:
        return True
    parts = PurePosixPath(raw).parts
    return any(part in {"", ".", ".."} for part in parts)


def _candidate(result_root: Path, raw: str) -> Path:
    return (result_root / PurePosixPath(raw)).resolve()


def validate_future_paths(
    case_id: str,
    future_paths: object,
    result_root: Path,
    existing_paths: set[Path | str] | None = None,
) -> list[str]:
    """Validate one exact path map without touching the filesystem."""

    errors: list[str] = []
    if case_id not in CASE_IDS:
        return ["unknown_case_id"]
    if not isinstance(future_paths, dict):
        return ["future_paths_object_required"]

    expected_keys = set(CANONICAL_PATH_KEYS)
    actual_keys = set(future_paths)
    for key in sorted(expected_keys - actual_keys):
        _add_path_error(errors, f"future_path_keys_missing:{key}")
    for key in sorted(actual_keys - expected_keys, key=str):
        _add_path_error(errors, f"future_path_keys_unknown:{key}")

    root = result_root.resolve()
    existing_resolved = {
        (item.resolve() if isinstance(item, Path) else (root / str(item)).resolve())
        for item in (existing_paths or set())
    }
    seen: dict[str, str] = {}
    for key in CANONICAL_PATH_KEYS:
        if key not in future_paths:
            continue
        raw = future_paths[key]
        nullable = case_id == "m3-f03" and key in NULLABLE_PATH_KEYS
        if raw is None:
            if not nullable:
                _add_path_error(errors, f"future_path_missing:{key}")
            continue
        if nullable:
            _add_path_error(errors, f"future_path_not_applicable:{key}")
            continue
        if not isinstance(raw, str) or _unsafe_relative_path(raw):
            _add_path_error(errors, f"future_path_unsafe:{key}")
            continue
        expected = f"{case_id}{PATH_SUFFIXES[key]}"
        if raw != expected:
            _add_path_error(errors, f"future_path_alias:{key}")
        if raw in seen:
            _add_path_error(errors, f"future_path_duplicate_within:{seen[raw]}:{key}")
        else:
            seen[raw] = key
        candidate = _candidate(root, raw)
        try:
            candidate.relative_to(root)
        except ValueError:
            _add_path_error(errors, f"future_path_outside_root:{key}")
            continue
        if candidate.exists() or candidate in existing_resolved:
            _add_path_error(errors, f"future_path_exists:{key}")
    return sorted(errors)


def validate_future_path_sets(
    paths_by_case: Mapping[str, object],
    result_root: Path,
    existing_paths: set[Path | str] | None = None,
) -> list[str]:
    """Validate every case map and reject cross-case path collisions."""

    errors: list[str] = []
    normalized: dict[str, dict[str, str]] = {}
    for case_id, future_paths in paths_by_case.items():
        errors.extend(validate_future_paths(case_id, future_paths, result_root, existing_paths))
        if isinstance(future_paths, dict):
            normalized[case_id] = {
                key: value
                for key, value in future_paths.items()
                if key in CANONICAL_PATH_KEYS and isinstance(value, str)
            }
    owners: dict[str, tuple[str, str]] = {}
    for case_id in sorted(normalized):
        for key, raw in sorted(normalized[case_id].items()):
            owner = owners.get(raw)
            if owner is not None and owner[0] != case_id:
                left_case, left_key = owner
                errors.append(f"future_path_duplicate:{key}:{left_case}:{case_id}")
            else:
                owners[raw] = (case_id, key)
    return sorted(set(errors))


def _integer_counter(record: Mapping[str, Any], key: str, errors: list[str]) -> int:
    value = record.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value not in {0, 1}:
        _add_path_error(errors, f"{key}_must_be_zero_or_one")
        return -1
    return value


def validate_case_record(record: object) -> list[str]:
    """Return deterministic errors for one explicit case transaction state."""

    if not isinstance(record, dict):
        return ["case_record_object_required"]
    errors: list[str] = []
    actual_keys = set(record)
    for key in sorted(REQUIRED_CASE_RECORD_KEYS - actual_keys):
        errors.append(f"case_record_field_missing:{key}")
    for key in sorted(actual_keys - REQUIRED_CASE_RECORD_KEYS, key=str):
        errors.append(f"case_record_field_unknown:{key}")
    if errors:
        return sorted(errors)

    case_id = record["case_id"]
    state = record["state"]
    if case_id not in CASE_IDS:
        errors.append("case_id_invalid")
    if state not in CASE_STATES:
        errors.append("case_state_invalid")
    task_id = record["task_id"]
    launched = _integer_counter(record, "tasks_launched", errors)
    finalizations = _integer_counter(record, "task_finalizations_observed", errors)
    preflighted = _integer_counter(record, "dispatcher_cases_preflighted", errors)
    processed = _integer_counter(record, "dispatcher_cases_processed", errors)
    composer = _integer_counter(record, "composer_invocations", errors)
    validator = _integer_counter(record, "validator_invocations", errors)
    accepted = record["accepted"]
    failures = record["transaction_failures"]
    if not isinstance(accepted, bool):
        errors.append("accepted_must_be_boolean")
    if not isinstance(failures, list) or any(not isinstance(item, str) or not item for item in failures):
        errors.append("transaction_failures_must_be_nonempty_strings")
        failures = []
    if launched == 1 and (not isinstance(task_id, str) or not task_id):
        errors.append("task_id_required_when_launched")
    if launched == 0 and task_id is not None:
        errors.append("task_id_forbidden_when_not_launched")
    if any(value < 0 for value in (launched, finalizations, preflighted, processed, composer, validator)):
        return sorted(set(errors))

    if state == "not_launched":
        if launched != 0 or finalizations != 0 or preflighted != 0 or processed != 0:
            errors.append("not_launched_counters_invalid")
        if composer != 0 or validator != 0 or accepted or failures:
            errors.append("not_launched_side_effects_invalid")
    elif state == "launched":
        if launched != 1 or finalizations != 0 or preflighted != 0 or processed != 0:
            errors.append("launched_counters_invalid")
        if composer != 0 or validator != 0 or accepted or failures:
            errors.append("launched_side_effects_invalid")
    elif state == "finalized_unprocessed":
        if launched != 1 or finalizations != 1 or preflighted != 0 or processed != 0:
            errors.append("finalized_unprocessed_counters_invalid")
        if composer != 0 or validator != 0 or accepted or failures:
            errors.append("finalized_unprocessed_side_effects_invalid")
    elif state == "processing_failed":
        if launched != 1 or finalizations != 1 or preflighted != 1 or processed != 0:
            errors.append("processing_failed_counters_invalid")
        if accepted:
            errors.append("accepted_state_invalid")
        if not failures:
            errors.append("processing_failure_reason_missing")
    elif state in {"processed_accepted", "processed_invalid"}:
        expected_composer = 0 if case_id == "m3-f03" else 1
        if launched != 1 or finalizations != 1 or preflighted != 1 or processed != 1:
            errors.append("processed_counters_invalid")
        if composer != expected_composer or validator != 1:
            errors.append("processed_invocation_counts_invalid")
        if failures:
            errors.append("processed_transaction_failure_invalid")
        if state == "processed_accepted" and not accepted:
            errors.append("accepted_state_invalid")
        if state == "processed_invalid" and accepted:
            errors.append("invalid_state_accepted")
    return sorted(set(errors))


def validate_case_records(records: object) -> list[str]:
    """Validate case records, including unique case and task bindings."""

    if not isinstance(records, list):
        return ["case_records_list_required"]
    errors: list[str] = []
    seen_cases: set[str] = set()
    seen_tasks: set[str] = set()
    for record in records:
        errors.extend(validate_case_record(record))
        if not isinstance(record, dict):
            continue
        case_id = record.get("case_id")
        if case_id in seen_cases:
            errors.append(f"case_id_duplicate:{case_id}")
        else:
            seen_cases.add(case_id)
        task_id = record.get("task_id")
        if task_id is not None:
            if task_id in seen_tasks:
                errors.append(f"task_id_duplicate:{task_id}")
            else:
                seen_tasks.add(task_id)
    if set(seen_cases) != set(CASE_IDS):
        errors.append("case_ids_incomplete")
    return sorted(set(errors))


def derive_counters(records: list[object]) -> dict[str, int]:
    """Derive all aggregate counters from explicit per-case records."""

    errors = validate_case_records(records)
    if errors:
        raise ValueError(";".join(errors))
    typed_records = [record for record in records if isinstance(record, dict)]
    return {
        "tasks_launched": sum(record["tasks_launched"] for record in typed_records),
        "task_finalizations_observed": sum(
            record["task_finalizations_observed"] for record in typed_records
        ),
        "dispatcher_cases_preflighted": sum(
            record["dispatcher_cases_preflighted"] for record in typed_records
        ),
        "dispatcher_cases_processed": sum(
            record["dispatcher_cases_processed"] for record in typed_records
        ),
        "composer_invocations": sum(record["composer_invocations"] for record in typed_records),
        "validator_invocations": sum(record["validator_invocations"] for record in typed_records),
        "accepted_cases": sum(1 for record in typed_records if record["accepted"]),
        "transaction_failures": sum(
            1 for record in typed_records if record["transaction_failures"]
        ),
    }

