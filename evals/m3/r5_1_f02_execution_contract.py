#!/usr/bin/env python3
"""Closed one-shot authorization, launch-receipt, and exclusive-write contracts."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from r5_dispatch_contract import COUNTER_KEYS, canonical_future_paths


SCHEMA_VERSION = "m3.1-forward-r5.1-f02-one-shot-execution-authorization-v1"
LAUNCH_SCHEMA_VERSION = "m3.1-forward-r5.1-f02-launch-receipt-v1"
AUTHORIZATION_SCOPE = "one_new_fresh_context_for_m3_f02_only"
CASE_ID = "m3-f02"
REVISION = "r5.1-f02"
READINESS_HEAD = "dae68ebd0d876a4aa2258f12a4a7ad8b4948e5ea"
READINESS_CI_RUN_ID = 31144763405
EVIDENCE_HEAD = "1b696bce53ee0a11163bfe4f91a9a49ab3af6f49"
PREPARATION_BASELINE_HEAD = "bbf54721b090d9d91b269d88e31919ae00fb0a39"
HISTORICAL_TASK_ID = "019fd687-5575-7143-8cf3-1ab3069611f5"
HISTORICAL_RESULT_ROOT = "evals/m3/results/forward-r5"
RESULT_ROOT = "evals/m3/results/forward-r5.1-f02"
AUTHORIZATION_PATH = (
    "evals/m3/forward-inputs-r5.1-f02/execution-authorization.json"
)
READINESS_MANIFEST_PATH = (
    "evals/m3/forward-inputs-r5.1-f02/authorization-manifest.json"
)
LAUNCH_CONTRACT_PATH = (
    "evals/m3/forward-inputs-r5.1-f02/m3-f02.launch.schema.json"
)
EXECUTION_PATHS = {
    "launch_attempt_json": "m3-f02.launch-attempt.json",
    "launch_receipt_json": "m3-f02.launch.json",
}
READINESS_JOBS = [
    "validate",
    "historical-audit-cross-platform (ubuntu-latest)",
    "historical-audit-cross-platform (windows-latest)",
]
BINDING_KEYS = {
    "preparation_manifest",
    "input_binding",
    "source_input",
    "prompt",
    "replacement_contract",
    "base_contract",
    "m2_validation",
    "eligibility",
    "supersession_policy",
    "route_condition_authority",
}
LIMIT_FIELDS = {
    "max_fresh_tasks",
    "max_finalizations",
    "max_composer_invocations",
    "max_validator_invocations",
}
FALSE_FIELDS = {
    "retry_allowed",
    "repair_allowed",
    "second_finalization_allowed",
    "historical_task_reuse_allowed",
    "historical_result_root_reuse_allowed",
    "cross_revision_aggregation_authorized",
    "m3_closure_authorized",
    "m4_authorized",
}
AUTHORIZATION_KEYS = {
    "schema_version",
    "status",
    "authorization_scope",
    "authorization_token",
    "authorized_case_id",
    "authorized_revision",
    "readiness_head",
    "readiness_ci_run_id",
    "readiness_ci_conclusion",
    "readiness_ci_jobs",
    "historical_evidence_head",
    "preparation_baseline_head",
    "readiness_authorization_manifest",
    "bindings",
    "launch_contract",
    "result_root",
    "execution_paths",
    "future_paths",
    "reserved_task_id",
    "historical_failed_task",
    "counters",
    "side_effects",
    "does_not_authorize",
} | LIMIT_FIELDS | FALSE_FIELDS
LAUNCH_RECEIPT_KEYS = {
    "schema_version",
    "case_id",
    "revision",
    "execution_authorization",
    "fresh_task_id",
    "launch_count",
    "historical_task_reused",
    "launch_status",
    "no_retry",
    "errors",
}


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return sha256(canonical_bytes(value))


def parse_json_object(raw: bytes) -> dict[str, Any]:
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ValueError("utf8_bom_forbidden")
    value = json.loads(raw.decode("utf-8", errors="strict"))
    if not isinstance(value, dict):
        raise ValueError("json_object_required")
    return value


def expected_authorization_token(value: dict[str, Any]) -> str:
    readiness = value.get("readiness_authorization_manifest")
    launch = value.get("launch_contract")
    selector = {
        "schema_version": value.get("schema_version"),
        "authorization_scope": value.get("authorization_scope"),
        "authorized_case_id": value.get("authorized_case_id"),
        "authorized_revision": value.get("authorized_revision"),
        "readiness_head": value.get("readiness_head"),
        "readiness_ci_run_id": value.get("readiness_ci_run_id"),
        "readiness_manifest_raw_sha256": readiness.get("raw_sha256")
        if isinstance(readiness, dict)
        else None,
        "launch_contract_raw_sha256": launch.get("raw_sha256")
        if isinstance(launch, dict)
        else None,
    }
    return canonical_sha256(selector)


def _add(errors: list[str], code: str) -> None:
    if code not in errors:
        errors.append(code)


def validate_execution_authorization_shape(value: object) -> list[str]:
    if not isinstance(value, dict):
        return ["execution_authorization_object_required"]
    errors: list[str] = []
    for key in sorted(AUTHORIZATION_KEYS - set(value)):
        _add(errors, f"execution_authorization_field_missing:{key}")
    for key in sorted(set(value) - AUTHORIZATION_KEYS, key=str):
        _add(errors, f"execution_authorization_field_unknown:{key}")

    expected = {
        "schema_version": SCHEMA_VERSION,
        "status": "ready_for_one_shot_fresh_execution",
        "authorization_scope": AUTHORIZATION_SCOPE,
        "authorized_case_id": CASE_ID,
        "authorized_revision": REVISION,
        "readiness_head": READINESS_HEAD,
        "readiness_ci_run_id": READINESS_CI_RUN_ID,
        "readiness_ci_conclusion": "success",
        "readiness_ci_jobs": READINESS_JOBS,
        "historical_evidence_head": EVIDENCE_HEAD,
        "preparation_baseline_head": PREPARATION_BASELINE_HEAD,
        "result_root": RESULT_ROOT,
        "execution_paths": EXECUTION_PATHS,
        "reserved_task_id": None,
        "side_effects": [],
    }
    for field, required in expected.items():
        if value.get(field) != required:
            _add(errors, f"execution_authorization_field_invalid:{field}")
    if value.get("reserved_task_id") is not None:
        _add(errors, "reserved_task_id_must_be_null")
    for field in LIMIT_FIELDS:
        field_value = value.get(field)
        if isinstance(field_value, bool) or field_value != 1:
            _add(errors, f"execution_authorization_field_invalid:{field}")
    for field in FALSE_FIELDS:
        if value.get(field) is not False:
            _add(errors, f"execution_authorization_field_invalid:{field}")

    bindings = value.get("bindings")
    if not isinstance(bindings, dict) or set(bindings) != BINDING_KEYS:
        _add(errors, "execution_authorization_bindings_invalid")
    readiness = value.get("readiness_authorization_manifest")
    if not isinstance(readiness, dict) or readiness.get("path") != READINESS_MANIFEST_PATH:
        _add(errors, "readiness_authorization_manifest_reference_invalid")
    launch = value.get("launch_contract")
    if not isinstance(launch, dict) or launch.get("path") != LAUNCH_CONTRACT_PATH:
        _add(errors, "launch_contract_reference_invalid")
    historical = value.get("historical_failed_task")
    if not isinstance(historical, dict) or historical != {
        "task_id": HISTORICAL_TASK_ID,
        "result_root": HISTORICAL_RESULT_ROOT,
        "retry_count": 0,
        "retry_forbidden": True,
    }:
        _add(errors, "historical_failed_task_binding_invalid")
    counters = value.get("counters")
    if not isinstance(counters, dict) or set(counters) != set(COUNTER_KEYS):
        _add(errors, "execution_authorization_counters_invalid")
    else:
        for key in COUNTER_KEYS:
            counter = counters.get(key)
            if isinstance(counter, bool) or counter != 0:
                _add(errors, f"execution_authorization_counter_nonzero:{key}")
    if value.get("future_paths") != canonical_future_paths(CASE_ID, Path(RESULT_ROOT)):
        _add(errors, "execution_authorization_future_paths_invalid")
    if not isinstance(value.get("does_not_authorize"), list):
        _add(errors, "does_not_authorize_list_required")
    if value.get("authorization_token") != expected_authorization_token(value):
        _add(errors, "authorization_token_invalid")
    return sorted(errors)


def _authorization_raw(value: dict[str, Any], raw: bytes | None) -> bytes:
    return raw if raw is not None else canonical_bytes(value)


def build_launch_receipt(
    authorization: dict[str, Any],
    *,
    task_id: str | None,
    status: str,
    errors: list[str],
    authorization_raw: bytes | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": LAUNCH_SCHEMA_VERSION,
        "case_id": CASE_ID,
        "revision": REVISION,
        "execution_authorization": {
            "path": AUTHORIZATION_PATH,
            "raw_sha256": sha256(_authorization_raw(authorization, authorization_raw)),
            "authorization_token": authorization.get("authorization_token"),
        },
        "fresh_task_id": task_id,
        "launch_count": 1,
        "historical_task_reused": False,
        "launch_status": status,
        "no_retry": True,
        "errors": errors,
    }


def validate_launch_receipt(
    value: object,
    authorization: dict[str, Any],
    *,
    authorization_raw: bytes | None = None,
) -> list[str]:
    if not isinstance(value, dict):
        return ["launch_receipt_object_required"]
    errors: list[str] = []
    if set(value) != LAUNCH_RECEIPT_KEYS:
        _add(errors, "launch_receipt_fields_invalid")
    expected = {
        "schema_version": LAUNCH_SCHEMA_VERSION,
        "case_id": CASE_ID,
        "revision": REVISION,
        "launch_count": 1,
        "historical_task_reused": False,
        "no_retry": True,
    }
    for field, required in expected.items():
        field_value = value.get(field)
        if field in {"launch_count"} and isinstance(field_value, bool):
            _add(errors, f"launch_receipt_field_invalid:{field}")
        elif field_value != required:
            _add(errors, f"launch_receipt_field_invalid:{field}")
    expected_identity = {
        "path": AUTHORIZATION_PATH,
        "raw_sha256": sha256(_authorization_raw(authorization, authorization_raw)),
        "authorization_token": authorization.get("authorization_token"),
    }
    if value.get("execution_authorization") != expected_identity:
        _add(errors, "launch_receipt_authorization_identity_invalid")
    status = value.get("launch_status")
    task_id = value.get("fresh_task_id")
    receipt_errors = value.get("errors")
    if not isinstance(receipt_errors, list) or any(
        not isinstance(item, str) or not item for item in receipt_errors
    ):
        _add(errors, "launch_receipt_errors_invalid")
        receipt_errors = []
    if status == "launched":
        if not isinstance(task_id, str) or not task_id:
            _add(errors, "fresh_task_id_required")
        if receipt_errors:
            _add(errors, "successful_launch_errors_forbidden")
    elif status == "launch_failed":
        if task_id is not None:
            _add(errors, "failed_launch_task_id_forbidden")
        if not receipt_errors:
            _add(errors, "failed_launch_error_required")
    else:
        _add(errors, "launch_status_invalid")
    if task_id == HISTORICAL_TASK_ID:
        _add(errors, "historical_task_id_reuse_forbidden")
    return sorted(errors)


def write_new_bytes(path: Path, raw: bytes) -> None:
    """Create one file exactly once without normalizing or replacing bytes."""

    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = -1
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def write_new_json(path: Path, value: dict[str, Any]) -> None:
    write_new_bytes(path, canonical_bytes(value) + b"\n")
