#!/usr/bin/env python3
"""Raw-first M4.1 execution evidence writer; default execution is check-only."""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Iterable


EXECUTION_ROOT = Path(__file__).resolve().parent
REPO_ROOT = EXECUTION_ROOT.parents[2]
if str(EXECUTION_ROOT) not in sys.path:
    sys.path.insert(0, str(EXECUTION_ROOT))

import audit_m4_1 as protocol  # noqa: E402
import build_m4_1_launch_claim as claim_builder  # noqa: E402


PLATFORM_OBSERVATIONS_RELATIVE = claim_builder.PLATFORM_OBSERVATIONS_RELATIVE
RAW_RESPONSE_NAME = "create-thread-response.json"
RESPONSE_ATTESTATION_NAME = "create-thread-response-attestation.json"
FINAL_ATTESTATION_NAME = "raw-final-attestation.json"
RECEIPT_NAME = "dispatch-receipt.json"
RAW_FINAL_NAME = "raw-final.txt"
ATTESTATION_KEYS = {
    "schema_version",
    "milestone",
    "revision",
    "task_id",
    "raw_response_path",
    "raw_response_byte_length",
    "raw_response_sha256",
    "canonical_response_sha256",
    "thread_id",
    "host_id",
    "client_thread_id",
    "resolved_checkout_sha_exposed",
    "resolved_checkout_sha_paths",
    "resolved_checkout_sha",
    "expected_checkout_sha",
    "checkout_sha_validated",
    "captured_at_utc",
}
FINAL_ATTESTATION_KEYS = {
    "schema_version",
    "milestone",
    "revision",
    "task_id",
    "raw_final_path",
    "byte_length",
    "raw_sha256",
    "observed_at_utc",
    "protocol_validation",
    "protocol_errors",
}
_HEX40 = re.compile(r"^[0-9a-f]{40}$")


def _add(errors: list[str], code: str) -> None:
    if code not in errors:
        errors.append(code)


def _valid_timestamp(value: object) -> bool:
    return isinstance(value, str) and protocol._valid_timestamp(value)


def _normalize_key(value: str) -> str:
    return "".join(character.lower() for character in value if character.isalnum())


def _find_named_values(
    value: object,
    names: set[str],
    *,
    path: str = "$",
) -> list[tuple[str, object]]:
    found: list[tuple[str, object]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if _normalize_key(str(key)) in names:
                found.append((child_path, child))
            found.extend(_find_named_values(child, names, path=child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(_find_named_values(child, names, path=f"{path}[{index}]"))
    return found


def _one_string(
    value: object,
    names: set[str],
    *,
    missing_code: str,
    ambiguous_code: str,
    required: bool,
) -> tuple[str | None, list[str]]:
    rows = _find_named_values(value, names)
    strings = [item for _, item in rows if isinstance(item, str) and item]
    distinct = sorted(set(strings))
    errors: list[str] = []
    if not distinct:
        if required:
            _add(errors, missing_code)
        return None, errors
    if len(distinct) != 1 or len(strings) != len(rows):
        _add(errors, ambiguous_code)
        return None, errors
    return distinct[0], errors


def attest_create_thread_response(
    raw: bytes,
    *,
    task_id: str,
    captured_at_utc: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if not isinstance(raw, bytes):
        raise TypeError("create_thread_response_bytes_required")
    if not _valid_timestamp(captured_at_utc):
        raise ValueError("captured_at_utc_invalid")
    value = protocol.parse_json_object(raw)
    thread_id, thread_errors = _one_string(
        value,
        {"threadid"},
        missing_code="thread_id_missing",
        ambiguous_code="thread_id_ambiguous",
        required=True,
    )
    host_id, host_errors = _one_string(
        value,
        {"hostid"},
        missing_code="host_id_missing",
        ambiguous_code="host_id_ambiguous",
        required=True,
    )
    client_id, client_errors = _one_string(
        value,
        {"clientthreadid"},
        missing_code="client_thread_id_missing",
        ambiguous_code="client_thread_id_ambiguous",
        required=False,
    )
    errors = thread_errors + host_errors + client_errors
    checkout_rows = _find_named_values(
        value,
        {
            "resolvedcheckoutsha",
            "checkoutsha",
            "resolvedheadsha",
            "resolvedcommitsha",
            "worktreeheadsha",
            "worktreecheckoutsha",
            "headsha",
        },
    )
    checkout_strings = [
        item for _, item in checkout_rows if isinstance(item, str) and item
    ]
    checkout_distinct = sorted(set(checkout_strings))
    resolved_checkout_sha: str | None = None
    if checkout_rows:
        if len(checkout_strings) != len(checkout_rows) or len(checkout_distinct) != 1:
            _add(errors, "resolved_checkout_sha_ambiguous")
        else:
            resolved_checkout_sha = checkout_distinct[0]
            if not _HEX40.fullmatch(resolved_checkout_sha):
                _add(errors, "resolved_checkout_sha_invalid")
            elif resolved_checkout_sha != claim_builder.AUTHORIZATION_HEAD:
                _add(errors, "resolved_checkout_sha_mismatch")
    if errors:
        raise ValueError(errors[0])
    response = {
        "thread_id": thread_id,
        "host_id": host_id,
        "client_thread_id": client_id,
        "ready": True,
    }
    attestation = {
        "schema_version": "m4.1-create-thread-response-attestation-v1",
        "milestone": "M4",
        "revision": "M4.1",
        "task_id": task_id,
        "raw_response_path": (
            f"{PLATFORM_OBSERVATIONS_RELATIVE.as_posix()}/{task_id}/{RAW_RESPONSE_NAME}"
        ),
        "raw_response_byte_length": len(raw),
        "raw_response_sha256": protocol.sha256(raw),
        "canonical_response_sha256": protocol.canonical_sha256(value),
        "thread_id": thread_id,
        "host_id": host_id,
        "client_thread_id": client_id,
        "resolved_checkout_sha_exposed": bool(checkout_rows),
        "resolved_checkout_sha_paths": [path for path, _ in checkout_rows],
        "resolved_checkout_sha": resolved_checkout_sha,
        "expected_checkout_sha": claim_builder.AUTHORIZATION_HEAD,
        "checkout_sha_validated": (
            resolved_checkout_sha == claim_builder.AUTHORIZATION_HEAD
            if checkout_rows
            else False
        ),
        "captured_at_utc": captured_at_utc,
    }
    return response, attestation


def _failure_attestation(
    raw: bytes,
    *,
    task_id: str,
    captured_at_utc: str,
    error_code: str,
) -> dict[str, Any]:
    try:
        value = protocol.parse_json_object(raw)
        canonical_hash: str | None = protocol.canonical_sha256(value)
    except (UnicodeError, ValueError, json.JSONDecodeError):
        canonical_hash = None
    return {
        "schema_version": "m4.1-create-thread-response-failure-attestation-v1",
        "milestone": "M4",
        "revision": "M4.1",
        "task_id": task_id,
        "raw_response_path": (
            f"{PLATFORM_OBSERVATIONS_RELATIVE.as_posix()}/{task_id}/{RAW_RESPONSE_NAME}"
        ),
        "raw_response_byte_length": len(raw),
        "raw_response_sha256": protocol.sha256(raw),
        "canonical_response_sha256": canonical_hash,
        "captured_at_utc": captured_at_utc,
        "status": "INVALID",
        "error_code": error_code,
    }


def _paths(
    repo_root: Path,
    *,
    claim_path: Path | None = None,
    results_base: Path | None = None,
    terminal_path: Path | None = None,
    results_manifest_path: Path | None = None,
    observations_base: Path | None = None,
) -> dict[str, Path]:
    return {
        "claim": claim_path or (repo_root / protocol.CLAIM_RELATIVE),
        "results": results_base or (repo_root / protocol.RESULTS_BASE_RELATIVE),
        "terminal": terminal_path or (repo_root / protocol.TERMINAL_RELATIVE),
        "results_manifest": results_manifest_path
        or (repo_root / protocol.RESULTS_MANIFEST_RELATIVE),
        "observations": observations_base
        or (repo_root / PLATFORM_OBSERVATIONS_RELATIVE),
    }


def _load_claim_and_tasks(claim_path: Path) -> tuple[dict[str, Any], bytes, list[dict[str, Any]], dict[str, dict[str, Any]]]:
    claim_raw = claim_path.read_bytes()
    claim = protocol.parse_json_object(claim_raw)
    control = protocol.parse_json_object(protocol.CONTROL_PATH.read_bytes())
    tasks = protocol.ordered_tasks(control)
    validation_errors: list[str] = []
    claim_by_id = protocol._validate_claim(claim, control, tasks, validation_errors)
    if validation_errors:
        raise ValueError("launch_claim_invalid")
    return claim, claim_raw, tasks, claim_by_id


def _exclusive_directory(path: Path) -> None:
    path.mkdir(exist_ok=False)


def _prepare_task_directories(
    results_base: Path,
    observations_base: Path,
    task_id: str,
    *,
    first_dispatch: bool,
) -> tuple[Path, Path]:
    result_task = results_base / task_id
    observation_task = observations_base / task_id
    for path in (result_task, observation_task):
        if path.exists():
            raise FileExistsError(f"target_directory_exists:{path.name}")
    if first_dispatch:
        for path in (results_base, observations_base):
            if path.exists():
                raise FileExistsError(f"target_directory_exists:{path.name}")
        if results_base.parent.exists() and not results_base.parent.is_dir():
            raise FileExistsError("results_parent_not_directory")
        if not results_base.parent.exists():
            _exclusive_directory(results_base.parent)
        _exclusive_directory(results_base)
        _exclusive_directory(observations_base)
    else:
        if not results_base.is_dir() or not observations_base.is_dir():
            raise FileNotFoundError("execution_roots_missing")
    _exclusive_directory(result_task)
    _exclusive_directory(observation_task)
    return result_task, observation_task


def _prepare_failure_observation_directory(
    observations_base: Path, task_id: str
) -> Path:
    observation_task = observations_base / task_id
    if observation_task.exists():
        raise FileExistsError("target_directory_exists:platform_observation")
    if observations_base.exists():
        if not observations_base.is_dir():
            raise FileExistsError("platform_observations_not_directory")
    else:
        _exclusive_directory(observations_base)
    _exclusive_directory(observation_task)
    return observation_task


def _receipt(
    *,
    claim: dict[str, Any],
    claim_raw: bytes,
    tasks: list[dict[str, Any]],
    task_claim: dict[str, Any],
    index: int,
    response: dict[str, Any],
    created_at_utc: str,
) -> dict[str, Any]:
    task = tasks[index]
    prompt = protocol.build_initial_prompt(task, task_claim)
    create_arguments = protocol.expected_create_thread_arguments(task, task_claim)
    return {
        "schema_version": "m4.1-dispatch-receipt-v1",
        "milestone": "M4",
        "revision": "M4.1",
        "status": "DISPATCHED",
        "claim": {
            "claim_id": claim["claim_id"],
            "path": protocol.CLAIM_RELATIVE.as_posix(),
            "raw_sha256": protocol.sha256(claim_raw),
        },
        "task_id": task["task_id"],
        "batch_id": task_claim["batch_id"],
        "batch_sequence": index // 10 + 1,
        "task_sequence_in_batch": index % 10 + 1,
        "dispatch_sequence": index + 1,
        "request_binding_sha256": task_claim["request_binding_sha256"],
        "context_id": task_claim["context_id"],
        "finalization_id": task_claim["finalization_id"],
        "request": {
            "surface": "codex_app.create_thread",
            "project_id": protocol.PROJECT_ID,
            "target_type": "project",
            "environment_type": "worktree",
            "starting_branch": claim_builder.AUTHORIZATION_BRANCH,
            "starting_head": claim_builder.AUTHORIZATION_HEAD,
            "initial_request_sha256": protocol.sha256(prompt.encode("utf-8")),
            "request_envelope_sha256": protocol.canonical_sha256(create_arguments),
            "model_field": "OMITTED",
            "thinking_field": "OMITTED",
            "initial_request_count": 1,
            "followup_count": 0,
        },
        "response": response,
        "created_at_utc": created_at_utc,
        "attempt_index": 1,
        "retry_count": 0,
        "repair_count": 0,
        "errors": [],
    }


def _audit_observations(
    *,
    observations_base: Path,
    results_base: Path,
    tasks: list[dict[str, Any]],
    execution_status: str,
    terminal: dict[str, Any] | None,
) -> list[str]:
    errors: list[str] = []
    task_ids = [str(task["task_id"]) for task in tasks]
    if not observations_base.exists():
        if results_base.exists():
            _add(errors, "platform_observations_missing")
        return errors
    if not observations_base.is_dir():
        return ["platform_observations_not_directory"]
    observed_ids: list[str] = []
    for child in observations_base.iterdir():
        if not child.is_dir() or child.name not in task_ids:
            _add(errors, "unexpected_platform_observation")
            continue
        observed_ids.append(child.name)
        files = {item.name: item for item in child.iterdir() if item.is_file()}
        allowed = {RAW_RESPONSE_NAME, RESPONSE_ATTESTATION_NAME, FINAL_ATTESTATION_NAME}
        if any(item.name not in allowed or not item.is_file() for item in child.iterdir()):
            _add(errors, f"unexpected_platform_observation:{child.name}")
        raw_response = files.get(RAW_RESPONSE_NAME)
        attestation_path = files.get(RESPONSE_ATTESTATION_NAME)
        receipt_path = results_base / child.name / RECEIPT_NAME
        if raw_response is None or attestation_path is None:
            _add(errors, f"platform_response_observation_incomplete:{child.name}")
            continue
        try:
            attestation = protocol.parse_json_object(attestation_path.read_bytes())
        except (OSError, UnicodeError, ValueError, json.JSONDecodeError):
            _add(errors, f"platform_response_attestation_invalid:{child.name}")
            continue
        if attestation.get("raw_response_sha256") != protocol.sha256(raw_response.read_bytes()):
            _add(errors, f"platform_response_raw_hash_mismatch:{child.name}")
        if receipt_path.is_file():
            try:
                receipt = protocol.parse_json_object(receipt_path.read_bytes())
            except (OSError, UnicodeError, ValueError, json.JSONDecodeError):
                receipt = {}
            response = receipt.get("response", {})
            if attestation.get("thread_id") != response.get("thread_id"):
                _add(errors, f"platform_response_thread_mismatch:{child.name}")
            if attestation.get("host_id") != response.get("host_id"):
                _add(errors, f"platform_response_host_mismatch:{child.name}")
            if set(attestation) != ATTESTATION_KEYS:
                _add(errors, f"platform_response_attestation_fields_invalid:{child.name}")
        elif execution_status != "STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE":
            _add(errors, f"platform_response_without_receipt:{child.name}")
        final_path = results_base / child.name / RAW_FINAL_NAME
        final_attestation_path = files.get(FINAL_ATTESTATION_NAME)
        if final_path.is_file():
            if final_attestation_path is None:
                _add(errors, f"raw_final_attestation_missing:{child.name}")
            else:
                try:
                    final_attestation = protocol.parse_json_object(
                        final_attestation_path.read_bytes()
                    )
                except (OSError, UnicodeError, ValueError, json.JSONDecodeError):
                    final_attestation = {}
                    _add(errors, f"raw_final_attestation_invalid:{child.name}")
                if set(final_attestation) != FINAL_ATTESTATION_KEYS:
                    _add(errors, f"raw_final_attestation_fields_invalid:{child.name}")
                if final_attestation.get("raw_sha256") != protocol.sha256(
                    final_path.read_bytes()
                ):
                    _add(errors, f"raw_final_attestation_hash_mismatch:{child.name}")
        elif final_attestation_path is not None:
            _add(errors, f"raw_final_attestation_without_raw:{child.name}")
    ordered_observed = [task_id for task_id in task_ids if task_id in observed_ids]
    if observed_ids and set(observed_ids) != set(ordered_observed):
        _add(errors, "platform_observation_unknown_task")
    if ordered_observed != task_ids[: len(ordered_observed)]:
        _add(errors, "platform_observations_not_frozen_prefix")
    if terminal is not None and terminal.get("terminal_state") == "COMPLETE_UNJUDGED":
        if ordered_observed != task_ids:
            _add(errors, "complete_platform_observations_incomplete")
    return errors


def check_recorder(
    repo_root: Path = REPO_ROOT,
    *,
    claim_path: Path | None = None,
    results_base: Path | None = None,
    terminal_path: Path | None = None,
    results_manifest_path: Path | None = None,
    observations_base: Path | None = None,
    verify_git: bool = True,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    paths = _paths(
        repo_root,
        claim_path=claim_path,
        results_base=results_base,
        terminal_path=terminal_path,
        results_manifest_path=results_manifest_path,
        observations_base=observations_base,
    )
    execution = protocol.audit_execution(
        repo_root,
        claim_path=paths["claim"],
        results_base=paths["results"],
        terminal_path=paths["terminal"],
        results_manifest_path=paths["results_manifest"],
        verify_git=verify_git,
    )
    errors = list(execution.get("errors", []))
    terminal: dict[str, Any] | None = None
    tasks: list[dict[str, Any]] = []
    if paths["claim"].is_file():
        try:
            _, _, tasks, _ = _load_claim_and_tasks(paths["claim"])
            if paths["terminal"].is_file():
                terminal = protocol.parse_json_object(paths["terminal"].read_bytes())
            errors.extend(
                _audit_observations(
                    observations_base=paths["observations"],
                    results_base=paths["results"],
                    tasks=tasks,
                    execution_status=str(execution.get("status")),
                    terminal=terminal,
                )
            )
        except (KeyError, OSError, TypeError, UnicodeError, ValueError, json.JSONDecodeError):
            _add(errors, "recorder_claim_or_observation_audit_failed")
    elif paths["observations"].exists():
        _add(errors, "platform_observations_without_claim")
    status = str(execution.get("status"))
    if errors:
        status = "INVALID"
    return {
        "status": status,
        "mode": "CHECK_ONLY",
        "errors": sorted(set(errors)),
        "token": execution.get("token"),
        "tasks": execution.get("tasks", 0),
        "threads": execution.get("threads", 0),
        "finalizations": execution.get("finalizations", 0),
        "results": execution.get("results", 0),
        "retries": execution.get("retries", 0),
        "repairs": execution.get("repairs", 0),
        "followups": execution.get("followups", 0),
        "writes": 0,
    }


def _compact_evidence(raw: bytes) -> str:
    return "base64:" + base64.b64encode(raw).decode("ascii")


def _terminal_value(
    *,
    claim: dict[str, Any],
    claim_raw: bytes,
    tasks: list[dict[str, Any]],
    claim_by_id: dict[str, dict[str, Any]],
    results_base: Path,
    observations_base: Path,
    state: str,
    recorded_at_utc: str,
    failed_task_id: str | None,
    failed_stage: str | None,
    failure_class: str | None,
    failure_evidence_raw: bytes | None,
    attempt_included: bool,
) -> dict[str, Any]:
    if state not in {
        "COMPLETE_UNJUDGED",
        "STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE",
    }:
        raise ValueError("terminal_state_invalid")
    if not _valid_timestamp(recorded_at_utc):
        raise ValueError("recorded_at_utc_invalid")
    errors: list[str] = []
    receipt_ids, receipts, raw_ids, raw_finals, _ = protocol._scan_results(
        results_base,
        claim=claim,
        claim_raw=claim_raw,
        tasks=tasks,
        claim_by_id=claim_by_id,
        errors=errors,
    )
    structural_errors = [
        code for code in errors if code not in {"protocol_failure_requires_terminal"}
    ]
    if structural_errors:
        raise ValueError("execution_prefix_invalid:" + ",".join(structural_errors))
    task_ids = [str(task["task_id"]) for task in tasks]
    task_by_id = {str(task["task_id"]): task for task in tasks}
    attempted = list(receipt_ids)
    if state == "STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE":
        if not isinstance(failed_task_id, str) or failed_task_id not in task_by_id:
            raise ValueError("failed_task_id_invalid")
        if attempt_included and failed_task_id not in attempted:
            if failed_task_id != task_ids[len(attempted)]:
                raise ValueError("failed_task_not_next_frozen_task")
            attempted.append(failed_task_id)
        if not isinstance(failed_stage, str) or not failed_stage:
            raise ValueError("failed_stage_invalid")
        if failure_class not in {"PROTOCOL_FAILURE", "INFRASTRUCTURE_FAILURE"}:
            raise ValueError("failure_class_invalid")
        if not isinstance(failure_evidence_raw, bytes) or not failure_evidence_raw:
            raise ValueError("failure_evidence_required")
    else:
        if receipt_ids != task_ids or raw_ids != task_ids:
            raise ValueError("complete_execution_incomplete")
        if any(raw_finals[task_id]["protocol_errors"] for task_id in raw_ids):
            raise ValueError("complete_execution_protocol_invalid")
        failed_task_id = None
        failed_stage = None
        failure_class = None
        failure_evidence_raw = None
        attempt_included = False
        attempted = list(task_ids)
    receipt_refs = [
        {
            "task_id": task_id,
            "thread_id": receipts[task_id]["value"]["response"]["thread_id"],
            "path": f"evals/m4/results/m4.1/{task_id}/{RECEIPT_NAME}",
            "raw_sha256": protocol.sha256(receipts[task_id]["raw"]),
        }
        for task_id in receipt_ids
    ]
    raw_refs: list[dict[str, Any]] = []
    for task_id in raw_ids:
        attestation_path = observations_base / task_id / FINAL_ATTESTATION_NAME
        if not attestation_path.is_file():
            raise ValueError("raw_final_attestation_missing")
        attestation = protocol.parse_json_object(attestation_path.read_bytes())
        raw = raw_finals[task_id]["raw"]
        raw_refs.append(
            {
                "task_id": task_id,
                "finalization_id": claim_by_id[task_id]["finalization_id"],
                "path": f"evals/m4/results/m4.1/{task_id}/{RAW_FINAL_NAME}",
                "byte_length": len(raw),
                "raw_sha256": protocol.sha256(raw),
                "protocol_validation": (
                    "INVALID" if raw_finals[task_id]["protocol_errors"] else "VALID"
                ),
                "observed_at_utc": attestation["observed_at_utc"],
            }
        )
    complete = state == "COMPLETE_UNJUDGED"
    if complete:
        failed_batch = None
        last_completed_batch = protocol.BATCH_ORDER[-1]
        later_batches: list[str] = []
        failure_evidence = None
    else:
        failed_batch = str(task_by_id[str(failed_task_id)]["batch_id"])
        failed_index = protocol.BATCH_ORDER.index(failed_batch)
        last_completed_batch = (
            protocol.BATCH_ORDER[failed_index - 1] if failed_index > 0 else None
        )
        later_batches = list(protocol.BATCH_ORDER[failed_index + 1 :])
        evidence_text = _compact_evidence(failure_evidence_raw or b"")
        failure_evidence = {
            "failure_class": failure_class,
            "raw_evidence": evidence_text,
            "raw_evidence_sha256": protocol.sha256(evidence_text.encode("utf-8")),
        }
    return {
        "schema_version": "m4.1-execution-terminal-v1",
        "milestone": "M4",
        "revision": "M4.1",
        "terminal_state": state,
        "recorded_at_utc": recorded_at_utc,
        "launch_claim": {
            "claim_id": claim["claim_id"],
            "path": protocol.CLAIM_RELATIVE.as_posix(),
            "raw_sha256": protocol.sha256(claim_raw),
        },
        "execution_protocol": {
            "head": claim["execution_protocol"]["head"],
            "ci_run_id": claim["execution_protocol"]["ci_run_id"],
        },
        "batch_order": list(protocol.BATCH_ORDER),
        "last_completed_batch": last_completed_batch,
        "failed_batch": failed_batch,
        "failed_task_id": failed_task_id,
        "failed_stage": failed_stage,
        "attempted_task_ids": attempted,
        "dispatch_receipts": receipt_refs,
        "raw_finals": raw_refs,
        "counts": {
            "tasks": len(receipt_ids),
            "threads": len(receipt_ids),
            "finalizations": len(raw_ids),
            "attempts": len(attempted),
            "retries": 0,
            "repairs": 0,
            "followups": 0,
            "results": len(raw_ids),
            "judge_calls": 0,
            "aggregation_calls": 0,
            "side_effects": 0,
        },
        "failure_evidence": failure_evidence,
        "later_batches_not_started": later_batches,
        "successor_revision_required": not complete,
        "coordinator_observation_policy": dict(protocol.OBSERVATION_POLICY),
        "permissions_still_closed": list(protocol.PERMISSIONS_STILL_CLOSED),
        "later_gates": dict(protocol.LATER_GATES),
    }


def record_terminal(
    repo_root: Path = REPO_ROOT,
    *,
    state: str,
    recorded_at_utc: str,
    failed_task_id: str | None = None,
    failed_stage: str | None = None,
    failure_class: str | None = None,
    failure_evidence_raw: bytes | None = None,
    attempt_included: bool = False,
    claim_path: Path | None = None,
    results_base: Path | None = None,
    terminal_path: Path | None = None,
    results_manifest_path: Path | None = None,
    observations_base: Path | None = None,
    verify_git: bool = True,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    paths = _paths(
        repo_root,
        claim_path=claim_path,
        results_base=results_base,
        terminal_path=terminal_path,
        results_manifest_path=results_manifest_path,
        observations_base=observations_base,
    )
    if paths["terminal"].exists():
        return {
            "status": "TERMINAL_ALREADY_EXISTS",
            "errors": ["terminal_overwrite_forbidden"],
            "writes": 0,
        }
    if paths["results_manifest"].exists():
        return {
            "status": "INVALID",
            "errors": ["results_manifest_forbidden"],
            "writes": 0,
        }
    try:
        claim, claim_raw, tasks, claim_by_id = _load_claim_and_tasks(paths["claim"])
        terminal = _terminal_value(
            claim=claim,
            claim_raw=claim_raw,
            tasks=tasks,
            claim_by_id=claim_by_id,
            results_base=paths["results"],
            observations_base=paths["observations"],
            state=state,
            recorded_at_utc=recorded_at_utc,
            failed_task_id=failed_task_id,
            failed_stage=failed_stage,
            failure_class=failure_class,
            failure_evidence_raw=failure_evidence_raw,
            attempt_included=attempt_included,
        )
        claim_builder.exclusive_create_json(paths["terminal"], terminal)
    except FileExistsError:
        return {
            "status": "TERMINAL_ALREADY_EXISTS",
            "errors": ["terminal_overwrite_forbidden"],
            "writes": 0,
        }
    except (KeyError, OSError, TypeError, UnicodeError, ValueError, json.JSONDecodeError) as error:
        return {
            "status": "INVALID",
            "errors": [str(error) or "terminal_create_failed"],
            "writes": 0,
        }
    result = check_recorder(
        repo_root,
        claim_path=paths["claim"],
        results_base=paths["results"],
        terminal_path=paths["terminal"],
        results_manifest_path=paths["results_manifest"],
        observations_base=paths["observations"],
        verify_git=verify_git,
    )
    return {**result, "writes": 1}


def record_dispatch(
    repo_root: Path = REPO_ROOT,
    *,
    task_id: str,
    response_raw: bytes,
    captured_at_utc: str,
    claim_path: Path | None = None,
    results_base: Path | None = None,
    terminal_path: Path | None = None,
    results_manifest_path: Path | None = None,
    observations_base: Path | None = None,
    verify_git: bool = True,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    paths = _paths(
        repo_root,
        claim_path=claim_path,
        results_base=results_base,
        terminal_path=terminal_path,
        results_manifest_path=results_manifest_path,
        observations_base=observations_base,
    )
    preflight = check_recorder(
        repo_root,
        claim_path=paths["claim"],
        results_base=paths["results"],
        terminal_path=paths["terminal"],
        results_manifest_path=paths["results_manifest"],
        observations_base=paths["observations"],
        verify_git=verify_git,
    )
    if preflight.get("status") != "CLAIMED_IN_PROGRESS":
        return {
            "status": "INVALID",
            "errors": list(preflight.get("errors", ["execution_not_in_progress"])),
            "writes": 0,
        }
    if preflight.get("tasks") != preflight.get("finalizations"):
        return {
            "status": "INVALID",
            "errors": ["previous_task_not_finalized"],
            "writes": 0,
        }
    failure_task_is_frozen = False
    try:
        claim, claim_raw, tasks, claim_by_id = _load_claim_and_tasks(paths["claim"])
        index = int(preflight["tasks"])
        if index >= len(tasks) or task_id != tasks[index]["task_id"]:
            return {
                "status": "INVALID",
                "errors": ["dispatch_not_next_frozen_task"],
                "writes": 0,
            }
        failure_task_is_frozen = True
        response, attestation = attest_create_thread_response(
            response_raw,
            task_id=task_id,
            captured_at_utc=captured_at_utc,
        )
        receipt = _receipt(
            claim=claim,
            claim_raw=claim_raw,
            tasks=tasks,
            task_claim=claim_by_id[task_id],
            index=index,
            response=response,
            created_at_utc=captured_at_utc,
        )
        validation_errors: list[str] = []
        protocol._validate_receipt(
            receipt,
            receipt_raw=protocol.canonical_bytes(receipt) + b"\n",
            claim=claim,
            claim_raw=claim_raw,
            task=tasks[index],
            task_claim=claim_by_id[task_id],
            index=index,
            errors=validation_errors,
        )
        if validation_errors:
            raise ValueError("dispatch_receipt_invalid")
    except (KeyError, OSError, TypeError, UnicodeError, ValueError, json.JSONDecodeError) as error:
        code = str(error) or "create_thread_response_invalid"
        if not failure_task_is_frozen:
            return {"status": "INVALID", "errors": [code], "writes": 0}
        try:
            observation_task = _prepare_failure_observation_directory(
                paths["observations"], task_id
            )
            claim_builder.exclusive_create_bytes(
                observation_task / RAW_RESPONSE_NAME, response_raw
            )
            claim_builder.exclusive_create_json(
                observation_task / RESPONSE_ATTESTATION_NAME,
                _failure_attestation(
                    response_raw,
                    task_id=task_id,
                    captured_at_utc=captured_at_utc,
                    error_code=code,
                ),
            )
        except (OSError, TypeError, ValueError):
            pass
        stopped = record_terminal(
            repo_root,
            state="STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE",
            recorded_at_utc=captured_at_utc,
            failed_task_id=task_id,
            failed_stage="create_thread_response_validation",
            failure_class="INFRASTRUCTURE_FAILURE",
            failure_evidence_raw=response_raw or code.encode("utf-8"),
            attempt_included=True,
            claim_path=paths["claim"],
            results_base=paths["results"],
            terminal_path=paths["terminal"],
            results_manifest_path=paths["results_manifest"],
            observations_base=paths["observations"],
            verify_git=verify_git,
        )
        return {**stopped, "dispatch_error": code}
    try:
        result_task, observation_task = _prepare_task_directories(
            paths["results"],
            paths["observations"],
            task_id,
            first_dispatch=int(preflight["tasks"]) == 0,
        )
        claim_builder.exclusive_create_bytes(
            observation_task / RAW_RESPONSE_NAME, response_raw
        )
        claim_builder.exclusive_create_json(
            observation_task / RESPONSE_ATTESTATION_NAME, attestation
        )
        claim_builder.exclusive_create_json(result_task / RECEIPT_NAME, receipt)
    except FileExistsError:
        return {
            "status": "STOP_REQUIRED",
            "errors": ["dispatch_target_already_exists"],
            "writes": 0,
        }
    except OSError:
        return {
            "status": "STOP_REQUIRED",
            "errors": ["dispatch_evidence_write_failed"],
            "writes": 0,
        }
    result = check_recorder(
        repo_root,
        claim_path=paths["claim"],
        results_base=paths["results"],
        terminal_path=paths["terminal"],
        results_manifest_path=paths["results_manifest"],
        observations_base=paths["observations"],
        verify_git=verify_git,
    )
    return {**result, "dispatched_task_id": task_id, "writes": 3}


def record_final(
    repo_root: Path = REPO_ROOT,
    *,
    task_id: str,
    final_raw: bytes,
    observed_at_utc: str,
    claim_path: Path | None = None,
    results_base: Path | None = None,
    terminal_path: Path | None = None,
    results_manifest_path: Path | None = None,
    observations_base: Path | None = None,
    verify_git: bool = True,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    if not isinstance(final_raw, bytes):
        return {"status": "INVALID", "errors": ["raw_final_bytes_required"], "writes": 0}
    if not _valid_timestamp(observed_at_utc):
        return {"status": "INVALID", "errors": ["observed_at_utc_invalid"], "writes": 0}
    paths = _paths(
        repo_root,
        claim_path=claim_path,
        results_base=results_base,
        terminal_path=terminal_path,
        results_manifest_path=results_manifest_path,
        observations_base=observations_base,
    )
    preflight = check_recorder(
        repo_root,
        claim_path=paths["claim"],
        results_base=paths["results"],
        terminal_path=paths["terminal"],
        results_manifest_path=paths["results_manifest"],
        observations_base=paths["observations"],
        verify_git=verify_git,
    )
    if preflight.get("status") != "CLAIMED_IN_PROGRESS":
        return {
            "status": "INVALID",
            "errors": list(preflight.get("errors", ["execution_not_in_progress"])),
            "writes": 0,
        }
    if preflight.get("tasks") != int(preflight.get("finalizations", 0)) + 1:
        return {"status": "INVALID", "errors": ["no_single_pending_final"], "writes": 0}
    try:
        _, _, tasks, claim_by_id = _load_claim_and_tasks(paths["claim"])
        index = int(preflight["finalizations"])
        if task_id != tasks[index]["task_id"]:
            raise ValueError("final_not_next_frozen_task")
        result_task = paths["results"] / task_id
        observation_task = paths["observations"] / task_id
        final_path = result_task / RAW_FINAL_NAME
        final_attestation_path = observation_task / FINAL_ATTESTATION_NAME
        if final_path.exists() or final_attestation_path.exists():
            raise FileExistsError("raw_final_or_attestation_exists")
        claim_builder.exclusive_create_bytes(final_path, final_raw)
        _, protocol_errors = protocol._validate_task_result(
            final_raw,
            task=tasks[index],
            task_claim=claim_by_id[task_id],
        )
        final_attestation = {
            "schema_version": "m4.1-raw-final-attestation-v1",
            "milestone": "M4",
            "revision": "M4.1",
            "task_id": task_id,
            "raw_final_path": f"evals/m4/results/m4.1/{task_id}/{RAW_FINAL_NAME}",
            "byte_length": len(final_raw),
            "raw_sha256": protocol.sha256(final_raw),
            "observed_at_utc": observed_at_utc,
            "protocol_validation": "INVALID" if protocol_errors else "VALID",
            "protocol_errors": sorted(protocol_errors),
        }
        claim_builder.exclusive_create_json(final_attestation_path, final_attestation)
    except FileExistsError:
        return {"status": "INVALID", "errors": ["raw_final_overwrite_forbidden"], "writes": 0}
    except (KeyError, OSError, TypeError, UnicodeError, ValueError, json.JSONDecodeError) as error:
        return {"status": "STOP_REQUIRED", "errors": [str(error) or "raw_final_write_failed"], "writes": 0}
    if protocol_errors:
        return record_terminal(
            repo_root,
            state="STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE",
            recorded_at_utc=observed_at_utc,
            failed_task_id=task_id,
            failed_stage="raw_final_schema_validation",
            failure_class="PROTOCOL_FAILURE",
            failure_evidence_raw=protocol.canonical_bytes(
                {"protocol_errors": sorted(protocol_errors)}
            ),
            attempt_included=False,
            claim_path=paths["claim"],
            results_base=paths["results"],
            terminal_path=paths["terminal"],
            results_manifest_path=paths["results_manifest"],
            observations_base=paths["observations"],
            verify_git=verify_git,
        )
    post = check_recorder(
        repo_root,
        claim_path=paths["claim"],
        results_base=paths["results"],
        terminal_path=paths["terminal"],
        results_manifest_path=paths["results_manifest"],
        observations_base=paths["observations"],
        verify_git=verify_git,
    )
    if post.get("status") != "CLAIMED_IN_PROGRESS":
        return {**post, "writes": 2}
    if post.get("results") == 60:
        return record_terminal(
            repo_root,
            state="COMPLETE_UNJUDGED",
            recorded_at_utc=observed_at_utc,
            claim_path=paths["claim"],
            results_base=paths["results"],
            terminal_path=paths["terminal"],
            results_manifest_path=paths["results_manifest"],
            observations_base=paths["observations"],
            verify_git=verify_git,
        )
    return {**post, "status": "PROTOCOL_VALID_CONTINUE", "writes": 2}


def _read_required(path: str | None) -> bytes:
    if path is None:
        raise ValueError("evidence_file_required")
    return Path(path).read_bytes()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--consume", choices=("dispatch", "final", "terminal"))
    parser.add_argument("--task-id")
    parser.add_argument("--response-file")
    parser.add_argument("--final-file")
    parser.add_argument("--evidence-file")
    parser.add_argument("--observed-at-utc")
    parser.add_argument(
        "--terminal-state",
        choices=(
            "COMPLETE_UNJUDGED",
            "STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE",
        ),
    )
    parser.add_argument("--failed-stage")
    parser.add_argument(
        "--failure-class", choices=("PROTOCOL_FAILURE", "INFRASTRUCTURE_FAILURE")
    )
    parser.add_argument("--attempt-included", action="store_true")
    arguments = parser.parse_args(argv)
    if arguments.consume == "dispatch":
        result = record_dispatch(
            REPO_ROOT,
            task_id=arguments.task_id or "",
            response_raw=_read_required(arguments.response_file),
            captured_at_utc=arguments.observed_at_utc or "",
        )
    elif arguments.consume == "final":
        result = record_final(
            REPO_ROOT,
            task_id=arguments.task_id or "",
            final_raw=_read_required(arguments.final_file),
            observed_at_utc=arguments.observed_at_utc or "",
        )
    elif arguments.consume == "terminal":
        result = record_terminal(
            REPO_ROOT,
            state=arguments.terminal_state or "",
            recorded_at_utc=arguments.observed_at_utc or "",
            failed_task_id=arguments.task_id,
            failed_stage=arguments.failed_stage,
            failure_class=arguments.failure_class,
            failure_evidence_raw=(
                _read_required(arguments.evidence_file)
                if arguments.terminal_state
                == "STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE"
                else None
            ),
            attempt_included=arguments.attempt_included,
        )
    else:
        result = check_recorder(REPO_ROOT)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0 if result["status"] in {
        "READY_UNCLAIMED",
        "CLAIMED_IN_PROGRESS",
        "PROTOCOL_VALID_CONTINUE",
        "COMPLETE_UNJUDGED",
        "STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE",
    } else 1


if __name__ == "__main__":
    raise SystemExit(main())
