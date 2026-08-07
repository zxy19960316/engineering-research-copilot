#!/usr/bin/env python3
"""Closed Gate 3 authorization, launch, and exclusive-write contracts."""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
INPUT_ROOT = REPO_ROOT / "evals" / "m3" / "forward-inputs-r5.2-f02"
RESULT_ROOT = REPO_ROOT / "evals" / "m3" / "results" / "forward-r5.2-f02"
REVISION = "r5.2-f02"
CASE_ID = "m3-f02"
BRANCH = "codex/m3.1.1-r5.2-f02-one-shot-fresh-execution"
GATE_2_HEAD = "05e64d9678f9755126b1c1a0bfa4835bd8296e08"
GATE_2_CI_RUN_ID = 31184790162
PROJECT_ID = "ff35b25f-4644-41c8-9073-74c697559439"
TASK_TITLE = "M3 r5.2-f02 authorized one-shot execution"
PROMPT_SHA256 = "815eae213701505755fb7edc4d64d16089bd4e14e14dc6ec1e16c787918ea1df"
INPUT_BINDING_SHA256 = "3d90ed7f02a865eb3cab0fd8f70f0407ce5a80a93e500996686e2fad54c1709d"
PROMPT_RELATIVE = "evals/m3/forward-inputs-r5.2-f02/m3-f02.prompt.txt"
INPUT_BINDING_RELATIVE = (
    "evals/m3/forward-inputs-r5.2-f02/m3-f02.input-binding.json"
)
OUTPUT_MODE_RELATIVE = "evals/m3/forward-inputs-r5.2-f02/m3-f02.output-mode.json"
AUTHORIZATION_RELATIVE = (
    "evals/m3/forward-inputs-r5.2-f02/execution-authorization.json"
)
CONTROL_RELATIVE = (
    "evals/m3/forward-inputs-r5.2-f02/m3-f02.execution-control.json"
)
LAUNCH_SCHEMA_RELATIVE = (
    "evals/m3/forward-inputs-r5.2-f02/m3-f02.launch.schema.json"
)
RESULT_ROOT_RELATIVE = "evals/m3/results/forward-r5.2-f02"
PROMPT_PATH = REPO_ROOT / PROMPT_RELATIVE
INPUT_BINDING_PATH = REPO_ROOT / INPUT_BINDING_RELATIVE
OUTPUT_MODE_PATH = REPO_ROOT / OUTPUT_MODE_RELATIVE
AUTHORIZATION_PATH = REPO_ROOT / AUTHORIZATION_RELATIVE
CONTROL_PATH = REPO_ROOT / CONTROL_RELATIVE
LAUNCH_SCHEMA_PATH = REPO_ROOT / LAUNCH_SCHEMA_RELATIVE
LAUNCH_ATTEMPT_NAME = "m3-f02.launch-attempt.json"
LAUNCH_RECEIPT_NAME = "m3-f02.launch.json"
HISTORICAL_TASK_IDS = {
    "019fd687-5575-7143-8cf3-1ab3069611f5",
    "019fdb7c-1728-7a92-b6cf-b0eb631a18b8",
}
COUNTER_KEYS = {"tasks", "finalizations", "composer", "validator", "retry"}
ZERO_COUNTERS = {
    "tasks": 0,
    "finalizations": 0,
    "composer": 0,
    "validator": 0,
    "retry": 0,
}
LIMITS = {
    "tasks": 1,
    "finalizations": 1,
    "composer": 1,
    "validator": 1,
    "retry": 0,
}
FUTURE_PATHS = {
    "launch_attempt_json": LAUNCH_ATTEMPT_NAME,
    "launch_receipt_json": LAUNCH_RECEIPT_NAME,
    "raw_model_final": "m3-f02.model-final.raw",
    "raw_response_observation_json": "m3-f02.raw-response-observation.json",
    "context_finalization_json": "m3-f02.context.json",
    "payload_json": "m3-f02.payload.json",
    "composer_invocation_receipt_json": "m3-f02.composer-receipt.json",
    "composed_bundle_json": "m3-f02.bundle.json",
    "validator_receipt_json": "m3-f02.validator-receipt.json",
    "validation_json": "m3-f02.validation.json",
    "case_transaction_json": "m3-f02.transaction.json",
    "terminal_manifest_json": "terminal-manifest.json",
}
CONTROL_KEYS = {
    "schema_version",
    "status",
    "revision",
    "case_id",
    "branch",
    "gate_2",
    "authorization_receipt",
    "prompt",
    "input_binding",
    "output_mode",
    "task_request",
    "result_root",
    "future_paths",
    "limits",
    "prelaunch_counters",
    "permissions",
    "historical_evidence",
    "does_not_authorize",
}
PERMISSION_KEYS = {
    "retry_allowed",
    "repair_allowed",
    "followup_message_allowed",
    "second_task_allowed",
    "second_finalization_allowed",
    "historical_task_reuse_allowed",
    "historical_result_mutation_allowed",
    "cross_revision_aggregation_authorized",
    "m3_closure_authorized",
    "gate_4_authorized",
    "direct_api_substitution_authorized",
}
ATTEMPT_KEYS = {
    "schema_version",
    "revision",
    "case_id",
    "authorization_receipt",
    "execution_control",
    "attempt_count",
    "max_fresh_tasks",
    "no_retry",
    "request_envelope_sha256",
    "model_visible_messages_sha256",
    "claimed_at",
}
LAUNCH_KEYS = {
    "schema_version",
    "revision",
    "case_id",
    "launch_attempt",
    "fresh_task_id",
    "model_id",
    "launch_count",
    "historical_task_reused",
    "launch_status",
    "no_retry",
    "task_created_at",
    "request_envelope_sha256",
    "model_visible_messages_sha256",
    "errors",
}
_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")


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


def prompt_text() -> str:
    return PROMPT_PATH.read_bytes().decode("utf-8", errors="strict")


def expected_create_thread_arguments() -> dict[str, Any]:
    return {
        "prompt": prompt_text(),
        "target": {
            "type": "project",
            "projectId": PROJECT_ID,
            "environment": {
                "type": "worktree",
                "startingState": {
                    "type": "branch",
                    "branchName": BRANCH,
                },
            },
        },
        "title": TASK_TITLE,
    }


def expected_request_envelope_sha256() -> str:
    return canonical_sha256(expected_create_thread_arguments())


def expected_model_visible_messages_sha256() -> str:
    return canonical_sha256([{"role": "user", "content": prompt_text()}])


def _add(errors: list[str], code: str) -> None:
    if code not in errors:
        errors.append(code)


def _valid_timestamp(value: object) -> bool:
    return isinstance(value, str) and _UTC_RE.fullmatch(value) is not None


def validate_execution_control(value: object) -> list[str]:
    if not isinstance(value, dict):
        return ["execution_control_object_required"]
    errors: list[str] = []
    if set(value) != CONTROL_KEYS:
        _add(errors, "execution_control_fields_invalid")
    expected_scalars = {
        "schema_version": "m3.1-r5.2-f02-execution-control-v1",
        "status": "ready_for_one_shot_fresh_execution",
        "revision": REVISION,
        "case_id": CASE_ID,
        "branch": BRANCH,
        "result_root": RESULT_ROOT_RELATIVE,
        "future_paths": FUTURE_PATHS,
    }
    for field, required in expected_scalars.items():
        if value.get(field) != required:
            _add(errors, f"execution_control_field_invalid:{field}")

    if value.get("gate_2") != {
        "head": GATE_2_HEAD,
        "ci_run_id": GATE_2_CI_RUN_ID,
        "ci_conclusion": "success",
    }:
        _add(errors, "execution_control_gate_2_invalid")

    try:
        authorization_raw = AUTHORIZATION_PATH.read_bytes()
    except OSError:
        authorization_raw = b""
    if value.get("authorization_receipt") != {
        "path": AUTHORIZATION_RELATIVE,
        "raw_sha256": sha256(authorization_raw),
    }:
        _add(errors, "execution_control_authorization_reference_invalid")

    try:
        prompt_raw = PROMPT_PATH.read_bytes()
        input_raw = INPUT_BINDING_PATH.read_bytes()
        output_mode_raw = OUTPUT_MODE_PATH.read_bytes()
    except OSError:
        prompt_raw = input_raw = output_mode_raw = b""
    if value.get("prompt") != {
        "path": PROMPT_RELATIVE,
        "raw_sha256": sha256(prompt_raw),
    }:
        _add(errors, "execution_control_prompt_reference_invalid")
    if value.get("input_binding") != {
        "path": INPUT_BINDING_RELATIVE,
        "raw_sha256": sha256(input_raw),
    }:
        _add(errors, "execution_control_input_binding_reference_invalid")

    output_mode = value.get("output_mode")
    expected_output_mode = {
        "path": OUTPUT_MODE_RELATIVE,
        "raw_sha256": sha256(output_mode_raw),
        "selected_mode": "strict_text_json_fail_closed",
        "structured_output_request_config": None,
        "capability_rechecked_at": "2026-08-07",
        "request_fields_observed": ["model", "prompt", "target", "thinking", "title"],
        "response_format_field_exposed": False,
        "json_schema_field_exposed": False,
    }
    if output_mode != expected_output_mode:
        _add(errors, "execution_control_output_mode_invalid")

    request = value.get("task_request")
    expected_request = {
        "surface": "codex_app.create_thread",
        "create_thread_arguments": expected_create_thread_arguments(),
        "model_field": "omitted",
        "thinking_field": "omitted",
        "request_envelope_sha256": expected_request_envelope_sha256(),
        "model_visible_messages_projection": "initial_user_message_only",
        "model_visible_messages_sha256": expected_model_visible_messages_sha256(),
    }
    if request != expected_request:
        _add(errors, "execution_control_task_request_invalid")

    limits = value.get("limits")
    if not isinstance(limits, dict) or set(limits) != COUNTER_KEYS:
        _add(errors, "execution_control_limits_invalid")
    else:
        for key, required in LIMITS.items():
            item = limits.get(key)
            if isinstance(item, bool) or item != required:
                _add(errors, f"execution_control_limit_invalid:{key}")
    counters = value.get("prelaunch_counters")
    if not isinstance(counters, dict) or set(counters) != COUNTER_KEYS:
        _add(errors, "execution_control_counters_invalid")
    else:
        for key in sorted(COUNTER_KEYS):
            item = counters.get(key)
            if isinstance(item, bool) or item != 0:
                _add(errors, f"execution_control_counter_nonzero:{key}")

    permissions = value.get("permissions")
    if not isinstance(permissions, dict) or set(permissions) != PERMISSION_KEYS:
        _add(errors, "execution_control_permissions_invalid")
    else:
        for field in sorted(PERMISSION_KEYS):
            if permissions.get(field) is not False:
                _add(errors, f"execution_control_permission_invalid:{field}")

    if value.get("historical_evidence") != {
        "forward_r5": {
            "head": "1b696bce53ee0a11163bfe4f91a9a49ab3af6f49",
            "path": "evals/m3/results/forward-r5",
            "required_diff": "empty",
        },
        "forward_r5_1_f02": {
            "head": "fb5eec44bbf86446cf12bda2bddc76fcb07a7e69",
            "path": "evals/m3/results/forward-r5.1-f02",
            "required_diff": "empty",
            "task_id": "019fdb7c-1728-7a92-b6cf-b0eb631a18b8",
            "retry_forbidden": True,
        },
    }:
        _add(errors, "execution_control_historical_evidence_invalid")
    if not isinstance(value.get("does_not_authorize"), list):
        _add(errors, "execution_control_does_not_authorize_invalid")
    return sorted(errors)


def build_launch_attempt(
    authorization_raw: bytes,
    control_raw: bytes,
    *,
    observed_at: str,
) -> dict[str, Any]:
    if not _valid_timestamp(observed_at):
        raise ValueError("launch_attempt_timestamp_invalid")
    return {
        "schema_version": "m3.1-r5.2-f02-launch-attempt-v1",
        "revision": REVISION,
        "case_id": CASE_ID,
        "authorization_receipt": {
            "path": AUTHORIZATION_RELATIVE,
            "raw_sha256": sha256(authorization_raw),
        },
        "execution_control": {
            "path": CONTROL_RELATIVE,
            "raw_sha256": sha256(control_raw),
        },
        "attempt_count": 1,
        "max_fresh_tasks": 1,
        "no_retry": True,
        "request_envelope_sha256": expected_request_envelope_sha256(),
        "model_visible_messages_sha256": expected_model_visible_messages_sha256(),
        "claimed_at": observed_at,
    }


def validate_launch_attempt(
    value: object,
    *,
    authorization_raw: bytes,
    control_raw: bytes,
) -> list[str]:
    if not isinstance(value, dict):
        return ["launch_attempt_object_required"]
    errors: list[str] = []
    if set(value) != ATTEMPT_KEYS:
        _add(errors, "launch_attempt_fields_invalid")
    expected = build_launch_attempt(
        authorization_raw,
        control_raw,
        observed_at=value.get("claimed_at")
        if _valid_timestamp(value.get("claimed_at"))
        else "1970-01-01T00:00:00Z",
    )
    for field, required in expected.items():
        if value.get(field) != required:
            _add(errors, f"launch_attempt_field_invalid:{field}")
    if not _valid_timestamp(value.get("claimed_at")):
        _add(errors, "launch_attempt_field_invalid:claimed_at")
    return sorted(errors)


def build_launch_receipt(
    attempt: dict[str, Any],
    *,
    task_id: str,
    model_id: str,
    task_created_at: str,
) -> dict[str, Any]:
    if not isinstance(task_id, str) or not task_id:
        raise ValueError("fresh_task_id_invalid")
    if task_id in HISTORICAL_TASK_IDS:
        raise ValueError("historical_task_id_reuse_forbidden")
    if not isinstance(model_id, str) or not model_id:
        raise ValueError("model_id_invalid")
    if not _valid_timestamp(task_created_at):
        raise ValueError("task_created_at_invalid")
    return {
        "schema_version": "m3.1-r5.2-f02-launch-receipt-v1",
        "revision": REVISION,
        "case_id": CASE_ID,
        "launch_attempt": {
            "path": LAUNCH_ATTEMPT_NAME,
            "raw_sha256": sha256(canonical_bytes(attempt) + b"\n"),
        },
        "fresh_task_id": task_id,
        "model_id": model_id,
        "launch_count": 1,
        "historical_task_reused": False,
        "launch_status": "launched",
        "no_retry": True,
        "task_created_at": task_created_at,
        "request_envelope_sha256": expected_request_envelope_sha256(),
        "model_visible_messages_sha256": expected_model_visible_messages_sha256(),
        "errors": [],
    }


def validate_launch_receipt(
    value: object,
    *,
    attempt: dict[str, Any],
    task_id: str | None = None,
) -> list[str]:
    if not isinstance(value, dict):
        return ["launch_receipt_object_required"]
    errors: list[str] = []
    if set(value) != LAUNCH_KEYS:
        _add(errors, "launch_receipt_fields_invalid")
    fresh_task_id = value.get("fresh_task_id")
    if not isinstance(fresh_task_id, str) or not fresh_task_id:
        _add(errors, "launch_receipt_task_id_invalid")
    elif fresh_task_id in HISTORICAL_TASK_IDS:
        _add(errors, "launch_receipt_historical_task_reused")
    if task_id is not None and fresh_task_id != task_id:
        _add(errors, "launch_receipt_task_binding_mismatch")
    expected = {
        "schema_version": "m3.1-r5.2-f02-launch-receipt-v1",
        "revision": REVISION,
        "case_id": CASE_ID,
        "launch_attempt": {
            "path": LAUNCH_ATTEMPT_NAME,
            "raw_sha256": sha256(canonical_bytes(attempt) + b"\n"),
        },
        "launch_count": 1,
        "historical_task_reused": False,
        "launch_status": "launched",
        "no_retry": True,
        "request_envelope_sha256": expected_request_envelope_sha256(),
        "model_visible_messages_sha256": expected_model_visible_messages_sha256(),
        "errors": [],
    }
    for field, required in expected.items():
        if value.get(field) != required:
            _add(errors, f"launch_receipt_field_invalid:{field}")
    if not isinstance(value.get("model_id"), str) or not value.get("model_id"):
        _add(errors, "launch_receipt_model_id_invalid")
    if not _valid_timestamp(value.get("task_created_at")):
        _add(errors, "launch_receipt_task_created_at_invalid")
    return sorted(errors)


def write_new_bytes(path: Path, raw: bytes) -> None:
    if path.exists():
        raise FileExistsError("output_already_exists")
    descriptor = -1
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
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
