#!/usr/bin/env python3
"""Closed identities and shape rules for the r5.1-f02 terminal state."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "m3.1-forward-r5.1-f02-terminal-v1"
REVISION = "r5.1-f02"
CASE_ID = "m3-f02"
STATUS = "terminal_not_accepted"
EXECUTION_AUTHORIZATION_HEAD = "85ce824c55a3a40f3f05153a57edb809dc68eee6"
EXECUTION_AUTHORIZATION_CI_RUN = 31162936407
EXECUTION_EVIDENCE_HEAD = "a847b3eaf39a6f4f70353cd669e41e414afc658c"
HISTORICAL_EVIDENCE_HEAD = "1b696bce53ee0a11163bfe4f91a9a49ab3af6f49"
HISTORICAL_TASK_ID = "019fd687-5575-7143-8cf3-1ab3069611f5"
FRESH_TASK_ID = "019fdb7c-1728-7a92-b6cf-b0eb631a18b8"
AUTHORIZATION_TOKEN = (
    "cf656f33434f470fc597fa538ade90b161a328af32cd5e5839f3d10efff01add"
)
RESULT_ROOT = "evals/m3/results/forward-r5.1-f02"
TERMINAL_MANIFEST_PATH = f"{RESULT_ROOT}/terminal-manifest.json"
HISTORICAL_RESULT_ROOT = "evals/m3/results/forward-r5"

ARTIFACT_SPECS: dict[str, tuple[str, str, str]] = {
    "launch_attempt": (
        EXECUTION_EVIDENCE_HEAD,
        f"{RESULT_ROOT}/m3-f02.launch-attempt.json",
        "json",
    ),
    "launch_receipt": (
        EXECUTION_EVIDENCE_HEAD,
        f"{RESULT_ROOT}/m3-f02.launch.json",
        "json",
    ),
    "model_final": (
        EXECUTION_EVIDENCE_HEAD,
        f"{RESULT_ROOT}/m3-f02.model-final.json",
        "malformed_json",
    ),
    "payload": (
        EXECUTION_EVIDENCE_HEAD,
        f"{RESULT_ROOT}/m3-f02.payload.json",
        "malformed_json",
    ),
    "composer_receipt": (
        EXECUTION_EVIDENCE_HEAD,
        f"{RESULT_ROOT}/m3-f02.composer-receipt.json",
        "json",
    ),
    "context": (
        EXECUTION_EVIDENCE_HEAD,
        f"{RESULT_ROOT}/m3-f02.context.json",
        "json",
    ),
    "transaction": (
        EXECUTION_EVIDENCE_HEAD,
        f"{RESULT_ROOT}/m3-f02.transaction.json",
        "json",
    ),
    "execution_validation": (
        EXECUTION_EVIDENCE_HEAD,
        "evals/m3/results/2026-08-07-m3.1.1-r5.1-f02-one-shot-execution-validation.md",
        "text",
    ),
    "execution_authorization": (
        EXECUTION_AUTHORIZATION_HEAD,
        "evals/m3/forward-inputs-r5.1-f02/execution-authorization.json",
        "json",
    ),
    "launch_schema": (
        EXECUTION_AUTHORIZATION_HEAD,
        "evals/m3/forward-inputs-r5.1-f02/m3-f02.launch.schema.json",
        "json",
    ),
    "authorization_manifest": (
        EXECUTION_AUTHORIZATION_HEAD,
        "evals/m3/forward-inputs-r5.1-f02/authorization-manifest.json",
        "json",
    ),
    "prompt": (
        EXECUTION_AUTHORIZATION_HEAD,
        "evals/m3/forward-inputs-r5.1-f02/m3-f02.prompt.txt",
        "text",
    ),
    "source_input": (
        EXECUTION_AUTHORIZATION_HEAD,
        "evals/m3/forward-inputs-r2/m3-f02-route-compatible.bundle.json",
        "json",
    ),
    "input_binding": (
        EXECUTION_AUTHORIZATION_HEAD,
        "evals/m3/forward-inputs-r5.1-f02/m3-f02.input-binding.json",
        "json",
    ),
    "replacement_contract": (
        EXECUTION_AUTHORIZATION_HEAD,
        "evals/m3/forward-inputs-r5.1-f02/m3-model-output-contract.schema.json",
        "json",
    ),
    "base_contract": (
        EXECUTION_AUTHORIZATION_HEAD,
        "evals/m3/forward-inputs-r5/m3-model-output-contract.schema.json",
        "json",
    ),
    "supersession_policy": (
        EXECUTION_AUTHORIZATION_HEAD,
        "evals/m3/results/diagnostics-r5.1/r5-acceptance-erratum.json",
        "json",
    ),
}

REQUIRED_RESULT_FILES = {
    ".gitkeep",
    "m3-f02.launch-attempt.json",
    "m3-f02.launch.json",
    "m3-f02.model-final.json",
    "m3-f02.payload.json",
    "m3-f02.composer-receipt.json",
    "m3-f02.context.json",
    "m3-f02.transaction.json",
    "terminal-manifest.json",
}
ALLOWED_RESULT_FILES = set(REQUIRED_RESULT_FILES)
FORBIDDEN_RESULT_FILES = {
    "m3-f02.bundle.json",
    "m3-f02.outcome.json",
    "m3-f02.validation.json",
    "m3-f02.validator-receipt.json",
}

COUNTERS = {
    "callback_invocations": 1,
    "tasks_launched": 1,
    "task_finalizations_observed": 1,
    "dispatcher_cases_preflighted": 1,
    "dispatcher_cases_processed": 0,
    "composer_invocations": 1,
    "validator_invocations": 0,
    "retry_count": 0,
    "repair_count": 0,
    "historical_f02_retry_count": 0,
}
FALSE_FIELDS = {
    "retry_allowed",
    "repair_allowed",
    "second_task_allowed",
    "second_finalization_allowed",
    "cross_revision_aggregation_authorized",
    "m3_closure_authorized",
    "m4_authorized",
}
MANIFEST_KEYS = {
    "schema_version",
    "revision",
    "case_id",
    "status",
    "accepted",
    "m3_status",
    "historical_r5_status",
    "m4_status",
    "execution_authorization_head",
    "execution_authorization_ci_run",
    "execution_evidence_head",
    "historical_evidence_head",
    "historical_failed_f02_task_id",
    "fresh_task_id",
    "authorization_token",
    "authorization_token_status",
    "task_budget",
    "counters",
    "failure",
    "artifacts",
} | FALSE_FIELDS
IDENTITY_KEYS = {
    "path",
    "source_head",
    "git_blob_oid",
    "byte_length",
    "raw_sha256",
    "utf8_status",
    "json_status",
}
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


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


def _add(errors: list[str], code: str) -> None:
    if code not in errors:
        errors.append(code)


def validate_terminal_manifest_shape(value: object) -> list[str]:
    if not isinstance(value, dict):
        return ["terminal_manifest_object_required"]
    errors: list[str] = []
    if set(value) != MANIFEST_KEYS:
        _add(errors, "terminal_manifest_fields_invalid")
    expected = {
        "schema_version": SCHEMA_VERSION,
        "revision": REVISION,
        "case_id": CASE_ID,
        "status": STATUS,
        "accepted": False,
        "m3_status": "IN_PROGRESS",
        "historical_r5_status": "BLOCKED_NOT_ACCEPTED",
        "m4_status": "NOT_STARTED",
        "execution_authorization_head": EXECUTION_AUTHORIZATION_HEAD,
        "execution_authorization_ci_run": EXECUTION_AUTHORIZATION_CI_RUN,
        "execution_evidence_head": EXECUTION_EVIDENCE_HEAD,
        "historical_evidence_head": HISTORICAL_EVIDENCE_HEAD,
        "historical_failed_f02_task_id": HISTORICAL_TASK_ID,
        "fresh_task_id": FRESH_TASK_ID,
        "authorization_token": AUTHORIZATION_TOKEN,
        "authorization_token_status": "CONSUMED_TERMINAL",
        "task_budget": "CONSUMED",
        "counters": COUNTERS,
        "failure": {
            "failure_stage": "composition",
            "failure_code": "payload_invalid_json",
            "transaction_failure": "composer_invocation_failed",
        },
    }
    for field, required in expected.items():
        if value.get(field) != required:
            _add(errors, f"terminal_manifest_field_invalid:{field}")
    for field in FALSE_FIELDS:
        if value.get(field) is not False:
            _add(errors, f"terminal_manifest_field_invalid:{field}")

    artifacts = value.get("artifacts")
    if not isinstance(artifacts, dict) or set(artifacts) != set(ARTIFACT_SPECS):
        _add(errors, "terminal_manifest_artifacts_invalid")
        return sorted(errors)
    for key, (head, path, kind) in ARTIFACT_SPECS.items():
        identity = artifacts.get(key)
        if not isinstance(identity, dict):
            _add(errors, f"artifact_identity_invalid:{key}")
            continue
        expected_keys = IDENTITY_KEYS | ({"canonical_sha256"} if kind == "json" else set())
        if set(identity) != expected_keys:
            _add(errors, f"artifact_identity_fields_invalid:{key}")
        if identity.get("path") != path:
            _add(errors, f"artifact_identity_path_invalid:{key}")
        if identity.get("source_head") != head:
            _add(errors, f"artifact_identity_source_head_invalid:{key}")
        if not isinstance(identity.get("byte_length"), int) or isinstance(
            identity.get("byte_length"), bool
        ) or identity.get("byte_length", -1) < 0:
            _add(errors, f"artifact_identity_byte_length_invalid:{key}")
        if HEX40.fullmatch(str(identity.get("git_blob_oid", ""))) is None:
            _add(errors, f"artifact_identity_git_blob_oid_invalid:{key}")
        if HEX64.fullmatch(str(identity.get("raw_sha256", ""))) is None:
            _add(errors, f"artifact_identity_raw_sha256_invalid:{key}")
        if identity.get("utf8_status") != "valid":
            _add(errors, f"artifact_identity_utf8_status_invalid:{key}")
        required_json_status = {
            "json": "valid",
            "malformed_json": "invalid_expected",
            "text": "not_applicable",
        }[kind]
        if identity.get("json_status") != required_json_status:
            _add(errors, f"artifact_identity_json_status_invalid:{key}")
        if kind == "json" and HEX64.fullmatch(
            str(identity.get("canonical_sha256", ""))
        ) is None:
            _add(errors, f"artifact_identity_canonical_sha256_invalid:{key}")
        if kind != "json" and "canonical_sha256" in identity:
            _add(errors, f"artifact_identity_canonical_sha256_forbidden:{key}")
    return sorted(errors)
