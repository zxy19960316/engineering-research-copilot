#!/usr/bin/env python3
"""Raw-first, write-once M4.2 execution evidence recorder.

Every CLI invocation defaults to --check.  Explicit writer modes are intended
for a separately authorized Gate B coordinator and are tested only against
synthetic temporary roots during Gate A.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import audit_m4_2 as protocol


RAW_RESPONSE_NAME = "create-thread-response.json"
RESPONSE_ATTESTATION_NAME = "create-thread-response-attestation.json"
RECEIPT_NAME = "dispatch-receipt.json"
RAW_FINAL_NAME = "raw-final.txt"
SOURCE_READER = Path.read_bytes


def _compact(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _source_inputs(
    repo_root: Path,
    *,
    verify_git: bool,
    enforce_frozen_hashes: bool,
    authorization_path: Path | None,
    control_path: Path | None,
) -> tuple[dict[str, Any], dict[str, Any], bytes, bytes, list[dict[str, Any]]]:
    authorization, control, authorization_raw, control_raw, tasks, errors = (
        protocol.load_frozen_inputs(
            repo_root,
            policy=protocol.FrozenPolicy(
                enforce_raw_hashes=enforce_frozen_hashes,
                verify_git=verify_git,
            ),
            authorization_path=authorization_path,
            control_path=control_path,
        )
    )
    if errors:
        raise protocol.ContractError(errors[0])
    return authorization, control, authorization_raw, control_raw, tasks


def attest_create_thread_response(
    raw: bytes,
    *,
    task_id: str,
    captured_at_utc: str,
    expected_checkout_sha: str = protocol.AUTHORIZATION_CLOSURE_HEAD,
    raw_response_path: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if protocol.ISO_UTC_RE.fullmatch(captured_at_utc) is None:
        raise protocol.ContractError("captured_at_utc_invalid")
    errors: list[str] = []
    canonical_hash: str | None = None
    value: dict[str, Any] = {}
    try:
        value = protocol.parse_json_object(raw, label="create_thread_response")
    except protocol.ContractError as error:
        errors.append(error.code)
    else:
        canonical_hash = protocol.canonical_sha256(value)
    thread_id = value.get("threadId") if isinstance(value, dict) else None
    host_id = value.get("hostId") if isinstance(value, dict) else None
    client_thread_id = value.get("clientThreadId") if isinstance(value, dict) else None
    if not isinstance(thread_id, str) or not thread_id:
        errors.append("ready_thread_id_missing")
        thread_id = None
    if not isinstance(host_id, str) or not host_id:
        errors.append("ready_host_id_missing")
        host_id = None
    if client_thread_id is not None and not isinstance(client_thread_id, str):
        errors.append("client_thread_id_invalid")
        client_thread_id = None
    checkout_exposed = "resolvedCheckoutSha" in value
    checkout = value.get("resolvedCheckoutSha") if checkout_exposed else None
    checkout_validated = False
    if checkout_exposed:
        if not isinstance(checkout, str) or protocol.OID_RE.fullmatch(checkout) is None:
            errors.append("resolved_checkout_sha_invalid")
            checkout = None
        elif checkout != expected_checkout_sha:
            errors.append("resolved_checkout_sha_mismatch")
        else:
            checkout_validated = True
    status = "VALID" if not errors else "INVALID"
    response = {
        "thread_id": thread_id,
        "host_id": host_id,
        "client_thread_id": client_thread_id,
        "ready": status == "VALID",
    }
    attestation = {
        "schema_version": "m4.2-create-thread-response-attestation-v1",
        "milestone": protocol.MILESTONE,
        "revision": protocol.REVISION,
        "task_id": task_id,
        "raw_response_path": raw_response_path
        or f"evals/m4/execution/m4.2/platform-observations/{task_id}/{RAW_RESPONSE_NAME}",
        "byte_length": len(raw),
        "raw_response_sha256": protocol.sha256(raw),
        "canonical_response_sha256": canonical_hash,
        "captured_at_utc": captured_at_utc,
        "status": status,
        "thread_id": thread_id,
        "host_id": host_id,
        "client_thread_id": client_thread_id,
        "ready_identifiers_validated": status == "VALID",
        "resolved_checkout_sha_exposed": checkout_exposed,
        "resolved_checkout_sha": checkout,
        "checkout_sha_validated": checkout_validated,
        "errors": errors,
    }
    return response, attestation


def _receipt(
    *,
    repo_root: Path,
    claim: Mapping[str, Any],
    claim_raw: bytes,
    task: Mapping[str, Any],
    task_claim: Mapping[str, Any],
    index: int,
    response: Mapping[str, Any],
    response_attestation: Mapping[str, Any],
    created_at_utc: str,
) -> dict[str, Any]:
    request = protocol.expected_create_thread_arguments(repo_root, task, task_claim)
    task_id = str(task_claim["task_id"])
    return {
        "schema_version": "m4.2-dispatch-receipt-v1",
        "milestone": protocol.MILESTONE,
        "revision": protocol.REVISION,
        "status": "DISPATCHED",
        "claim": {
            "claim_id": claim["claim_id"],
            "path": protocol.CLAIM_RELATIVE.as_posix(),
            "raw_sha256": protocol.sha256(claim_raw),
        },
        "task_id": task_id,
        "batch_id": task_claim["batch_id"],
        "batch_sequence": index // 10 + 1,
        "task_sequence_in_batch": index % 10 + 1,
        "dispatch_sequence": index + 1,
        "request_binding_sha256": task_claim["request_binding_sha256"],
        "blind_id": task_claim["blind_id"],
        "context_id": task_claim["context_id"],
        "finalization_id": task_claim["finalization_id"],
        "request": {
            "surface": "codex_app.create_thread",
            "project_id": protocol.PROJECT_ID,
            "target_type": "project",
            "environment_type": "worktree",
            "starting_branch": protocol.AUTHORIZATION_BRANCH,
            "starting_head": protocol.AUTHORIZATION_CLOSURE_HEAD,
            "initial_request_sha256": protocol.sha256(
                request["prompt"].encode("utf-8")
            ),
            "request_envelope_sha256": protocol.canonical_sha256(request),
            "model_field": "OMITTED",
            "thinking_field": "OMITTED",
            "initial_request_count": 1,
            "followup_count": 0,
        },
        "response": dict(response),
        "response_attestation": {
            "path": response_attestation["raw_response_path"].replace(
                RAW_RESPONSE_NAME, RESPONSE_ATTESTATION_NAME
            ),
            "raw_sha256": response_attestation["raw_response_sha256"],
            "canonical_sha256": response_attestation["canonical_response_sha256"],
        },
        "created_at_utc": created_at_utc,
        "attempt_index": 1,
        "retry_count": 0,
        "repair_count": 0,
        "errors": [],
    }


def check_recorder(
    repo_root: Path = protocol.REPO_ROOT,
    **audit_kwargs: Any,
) -> dict[str, Any]:
    state = protocol.audit_execution(repo_root, **audit_kwargs)
    allowed = {
        "READY_UNCLAIMED",
        "CLAIMED_IN_PROGRESS",
        "COMPLETE_UNJUDGED",
        "STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE",
    }
    return {
        "status": state["status"] if state["status"] in allowed else "INVALID",
        "mode": "CHECK_ONLY",
        "errors": state["errors"],
        "tasks": state["tasks"],
        "threads": state["threads"],
        "finalizations": state["finalizations"],
        "attempts": state["attempts"],
        "retries": state["retries"],
        "repairs": state["repairs"],
        "followups": state["followups"],
        "writes": 0,
    }


def _next_action_result(
    *,
    status: str,
    action: str,
    errors: Sequence[str] = (),
    task: Mapping[str, Any] | None = None,
    global_sequence: int | None = None,
    create_thread_arguments: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "mode": "NEXT_ACTION",
        "status": status,
        "action": action,
        "task_id": None if task is None else task.get("task_id"),
        "batch_id": None if task is None else task.get("batch_id"),
        "global_sequence": global_sequence,
        "create_thread_arguments": (
            None if create_thread_arguments is None else dict(create_thread_arguments)
        ),
        "errors": list(errors),
        "writes": 0,
    }


def next_action(
    repo_root: Path = protocol.REPO_ROOT,
    **audit_kwargs: Any,
) -> dict[str, Any]:
    """Return the sole permitted next coordinator action without writing."""
    state = protocol.audit_execution(repo_root, **audit_kwargs)
    status = str(state["status"])
    errors = list(state["errors"])
    if status == "READY_UNCLAIMED" and not errors:
        return _next_action_result(
            status=status,
            action="CONSUME_CLAIM",
        )
    if status in {
        "COMPLETE_UNJUDGED",
        "STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE",
    } and not errors:
        return _next_action_result(status=status, action="STOP")
    complete_without_terminal = (
        status == "INVALID"
        and errors == ["complete_matrix_without_terminal"]
        and state["tasks"] == 60
        and state["finalizations"] == 60
        and not state["terminal_present"]
    )
    if complete_without_terminal:
        return _next_action_result(
            status="READY_TO_RECORD_COMPLETE_TERMINAL",
            action="RECORD_COMPLETE_TERMINAL",
        )
    if status != "CLAIMED_IN_PROGRESS" or errors:
        return _next_action_result(status="INVALID", action="INVALID", errors=errors)

    paths = _paths(
        repo_root,
        claim_path=audit_kwargs.get("claim_path"),
        observations_base=audit_kwargs.get("observations_base"),
        results_base=audit_kwargs.get("results_base"),
        terminal_path=audit_kwargs.get("terminal_path"),
        results_manifest_path=audit_kwargs.get("results_manifest_path"),
        m5_path=audit_kwargs.get("m5_path"),
    )
    try:
        claim, _, tasks = _claim_and_tasks(
            repo_root,
            paths,
            verify_git=bool(audit_kwargs.get("verify_git", True)),
            enforce_frozen_hashes=bool(
                audit_kwargs.get("enforce_frozen_hashes", True)
            ),
            authorization_path=audit_kwargs.get("authorization_path"),
            control_path=audit_kwargs.get("control_path"),
        )
    except (OSError, protocol.ContractError) as error:
        code = error.code if isinstance(error, protocol.ContractError) else type(error).__name__
        return _next_action_result(status="INVALID", action="INVALID", errors=[code])

    receipt_count = int(state["tasks"])
    final_count = int(state["finalizations"])
    if receipt_count == final_count and receipt_count < len(tasks):
        task = tasks[receipt_count]
        task_claim = claim["task_claims"][receipt_count]
        try:
            request = protocol.expected_create_thread_arguments(
                repo_root, task, task_claim
            )
        except protocol.ContractError as error:
            return _next_action_result(
                status="INVALID", action="INVALID", errors=[error.code]
            )
        if set(request) != {"prompt", "target", "title"}:
            return _next_action_result(
                status="INVALID",
                action="INVALID",
                errors=["create_thread_arguments_invalid"],
            )
        return _next_action_result(
            status=status,
            action="CREATE_THREAD",
            task=task,
            global_sequence=receipt_count + 1,
            create_thread_arguments=request,
        )
    if receipt_count == final_count + 1 and final_count < len(tasks):
        return _next_action_result(
            status=status,
            action="RECORD_FINAL",
            task=tasks[final_count],
            global_sequence=final_count + 1,
        )
    return _next_action_result(
        status="INVALID",
        action="INVALID",
        errors=["coordinator_lifecycle_prefix_invalid"],
    )


def _paths(
    repo_root: Path,
    *,
    claim_path: Path | None,
    observations_base: Path | None,
    results_base: Path | None,
    terminal_path: Path | None,
    results_manifest_path: Path | None,
    m5_path: Path | None,
) -> protocol.LifecyclePaths:
    defaults = protocol.default_paths(repo_root)
    return protocol.LifecyclePaths(
        claim=claim_path or defaults.claim,
        observations=observations_base or defaults.observations,
        results=results_base or defaults.results,
        terminal=terminal_path or defaults.terminal,
        results_manifest=results_manifest_path or defaults.results_manifest,
        m5=m5_path or defaults.m5,
    )


def _claim_and_tasks(
    repo_root: Path,
    paths: protocol.LifecyclePaths,
    *,
    verify_git: bool,
    enforce_frozen_hashes: bool,
    authorization_path: Path | None,
    control_path: Path | None,
) -> tuple[dict[str, Any], bytes, list[dict[str, Any]]]:
    if not paths.claim.is_file():
        raise protocol.ContractError("claim_missing")
    claim_raw = paths.claim.read_bytes()
    claim = protocol.parse_json_object(claim_raw, label="launch_claim")
    _, _, _, _, tasks = _source_inputs(
        repo_root,
        verify_git=verify_git,
        enforce_frozen_hashes=enforce_frozen_hashes,
        authorization_path=authorization_path,
        control_path=control_path,
    )
    return claim, claim_raw, tasks


def _gate_a_terminal_ref(claim: Mapping[str, Any]) -> dict[str, Any]:
    gate_a = claim["gate_a_acceptance"]
    return {
        "candidate_head": gate_a["candidate_head"],
        "push_run_id": gate_a["push_run_id"],
        "pr_run_id": gate_a["pr_run_id"],
    }


def _later_batches(failed_batch: str | None) -> list[str]:
    if failed_batch is None:
        return list(protocol.BATCH_ORDER)
    try:
        index = protocol.BATCH_ORDER.index(failed_batch)
    except ValueError:
        return list(protocol.BATCH_ORDER)
    return list(protocol.BATCH_ORDER[index + 1 :])


def _terminal_value(
    *,
    claim: Mapping[str, Any],
    claim_raw: bytes,
    evidence: Mapping[str, Any],
    state: str,
    recorded_at_utc: str,
    attempted_task_ids: list[str],
    failed_task_id: str | None = None,
    failed_stage: str | None = None,
    failure_class: str | None = None,
    failure_raw: bytes | None = None,
    failure_raw_path: str | None = None,
    diagnostic: str | None = None,
    attempt_count: int | None = None,
) -> dict[str, Any]:
    complete = state == "COMPLETE_UNJUDGED"
    task_claim_by_id = {
        str(item["task_id"]): item
        for item in claim.get("task_claims", [])
        if isinstance(item, dict)
    }
    failed_batch = (
        task_claim_by_id.get(failed_task_id, {}).get("batch_id")
        if failed_task_id is not None
        else None
    )
    last_completed_batch: str | None = None
    if complete:
        last_completed_batch = protocol.BATCH_ORDER[-1]
    elif attempted_task_ids:
        completed = evidence["final_count"]
        if completed and completed % 10 == 0:
            last_completed_batch = protocol.BATCH_ORDER[completed // 10 - 1]
    if complete:
        failure_evidence = None
    else:
        raw = failure_raw or (diagnostic or "terminal failure").encode("utf-8")
        failure_evidence = {
            "failure_class": failure_class or "INFRASTRUCTURE_FAILURE",
            "raw_evidence_sha256": protocol.sha256(raw),
            "raw_evidence_byte_length": len(raw),
            "raw_evidence_path": failure_raw_path,
            "diagnostic": diagnostic or "terminal failure",
        }
    finals = []
    for item in evidence["finals"]:
        finals.append(
            {
                **item,
                "observed_at_utc": recorded_at_utc,
            }
        )
    return {
        "schema_version": "m4.2-execution-terminal-v1",
        "milestone": protocol.MILESTONE,
        "revision": protocol.REVISION,
        "terminal_state": state,
        "recorded_at_utc": recorded_at_utc,
        "launch_claim": {
            "claim_id": claim["claim_id"],
            "path": protocol.CLAIM_RELATIVE.as_posix(),
            "raw_sha256": protocol.sha256(claim_raw),
        },
        "gate_a_acceptance": _gate_a_terminal_ref(claim),
        "batch_order": list(protocol.BATCH_ORDER),
        "last_completed_batch": last_completed_batch,
        "failed_batch": None if complete else failed_batch,
        "failed_task_id": None if complete else failed_task_id,
        "failed_stage": None if complete else failed_stage,
        "attempted_task_ids": attempted_task_ids,
        "dispatch_receipts": evidence["receipts"],
        "create_thread_responses": evidence["responses"],
        "raw_finals": finals,
        "counts": {
            "tasks": evidence["receipt_count"],
            "threads": evidence["ready_response_count"],
            "finalizations": evidence["final_count"],
            "attempts": (
                60 if complete else attempt_count if attempt_count is not None else max(evidence["receipt_count"], evidence["response_count"])
            ),
            "retries": 0,
            "repairs": 0,
            "followups": 0,
            "results": evidence["final_count"],
            "judge_calls": 0,
            "aggregation_calls": 0,
            "side_effects": 0,
        },
        "failure_evidence": failure_evidence,
        "later_batches_not_started": [] if complete else _later_batches(failed_batch),
        "successor_revision_required": not complete,
        "permissions_still_closed": list(protocol.PERMISSIONS_STILL_CLOSED),
    }


def _evidence_snapshot(
    repo_root: Path,
    paths: protocol.LifecyclePaths,
    claim: Mapping[str, Any],
    claim_raw: bytes,
    tasks: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    evidence = protocol._validate_evidence(
        repo_root,
        paths,
        claim,
        claim_raw,
        tasks,
        errors,
        allow_terminal_failure_prefix=True,
    )
    return evidence, errors


def _write_failure_terminal(
    repo_root: Path,
    paths: protocol.LifecyclePaths,
    *,
    claim: Mapping[str, Any],
    claim_raw: bytes,
    tasks: list[dict[str, Any]],
    recorded_at_utc: str,
    attempted_task_ids: list[str],
    failed_task_id: str | None,
    failed_stage: str,
    failure_class: str,
    failure_raw: bytes,
    failure_raw_path: str | None,
    diagnostic: str,
    attempt_count: int,
) -> dict[str, Any]:
    evidence, _ = _evidence_snapshot(repo_root, paths, claim, claim_raw, tasks)
    terminal = _terminal_value(
        claim=claim,
        claim_raw=claim_raw,
        evidence=evidence,
        state="STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE",
        recorded_at_utc=recorded_at_utc,
        attempted_task_ids=attempted_task_ids,
        failed_task_id=failed_task_id,
        failed_stage=failed_stage,
        failure_class=failure_class,
        failure_raw=failure_raw,
        failure_raw_path=failure_raw_path,
        diagnostic=diagnostic,
        attempt_count=attempt_count,
    )
    try:
        protocol.exclusive_create_json(paths.terminal, terminal)
    except FileExistsError:
        return {
            "status": "TERMINAL_ALREADY_EXISTS",
            "errors": ["terminal_target_preexists"],
            "writes": 0,
        }
    return protocol.audit_execution(
        repo_root,
        claim_path=paths.claim,
        observations_base=paths.observations,
        results_base=paths.results,
        terminal_path=paths.terminal,
        results_manifest_path=paths.results_manifest,
        m5_path=paths.m5,
        verify_git=False,
        enforce_frozen_hashes=False,
    )


def record_dispatch(
    repo_root: Path,
    *,
    task_id: str,
    response_raw: bytes,
    captured_at_utc: str,
    claim_path: Path | None = None,
    observations_base: Path | None = None,
    results_base: Path | None = None,
    terminal_path: Path | None = None,
    results_manifest_path: Path | None = None,
    m5_path: Path | None = None,
    verify_git: bool = True,
    enforce_frozen_hashes: bool = True,
    authorization_path: Path | None = None,
    control_path: Path | None = None,
) -> dict[str, Any]:
    paths = _paths(
        repo_root,
        claim_path=claim_path,
        observations_base=observations_base,
        results_base=results_base,
        terminal_path=terminal_path,
        results_manifest_path=results_manifest_path,
        m5_path=m5_path,
    )
    state = protocol.audit_execution(
        repo_root,
        claim_path=paths.claim,
        observations_base=paths.observations,
        results_base=paths.results,
        terminal_path=paths.terminal,
        results_manifest_path=paths.results_manifest,
        m5_path=paths.m5,
        verify_git=verify_git,
        enforce_frozen_hashes=enforce_frozen_hashes,
        authorization_path=authorization_path,
        control_path=control_path,
    )
    if state["status"] != "CLAIMED_IN_PROGRESS" or state["errors"]:
        return {**state, "writes": 0}
    if state["tasks"] != state["finalizations"]:
        return {
            "status": "INVALID",
            "errors": ["previous_task_not_finalized"],
            "writes": 0,
        }
    claim, claim_raw, tasks = _claim_and_tasks(
        repo_root,
        paths,
        verify_git=verify_git,
        enforce_frozen_hashes=enforce_frozen_hashes,
        authorization_path=authorization_path,
        control_path=control_path,
    )
    index = state["tasks"]
    if index >= 60 or task_id != tasks[index]["task_id"]:
        return {
            "status": "INVALID",
            "errors": ["dispatch_not_next_frozen_task"],
            "writes": 0,
        }
    task_claim = claim["task_claims"][index]
    observation_dir = paths.observations / task_id
    result_dir = paths.results / task_id
    raw_path = observation_dir / RAW_RESPONSE_NAME
    attestation_path = observation_dir / RESPONSE_ATTESTATION_NAME
    receipt_path = result_dir / RECEIPT_NAME
    preexisting = [
        path.as_posix()
        for path in (raw_path, attestation_path, receipt_path)
        if path.exists()
    ]
    if preexisting:
        return {
            "status": "INVALID",
            "errors": ["dispatch_target_preexists"],
            "preexisting": preexisting,
            "writes": 0,
        }
    try:
        protocol.exclusive_create_bytes(raw_path, response_raw)
    except FileExistsError:
        return {
            "status": "INVALID",
            "errors": ["dispatch_target_preexists"],
            "writes": 0,
        }
    response, attestation = attest_create_thread_response(
        response_raw,
        task_id=task_id,
        captured_at_utc=captured_at_utc,
        raw_response_path=(
            f"evals/m4/execution/m4.2/platform-observations/{task_id}/{RAW_RESPONSE_NAME}"
        ),
    )
    protocol.exclusive_create_json(attestation_path, attestation)
    if attestation["status"] != "VALID":
        stopped = _write_failure_terminal(
            repo_root,
            paths,
            claim=claim,
            claim_raw=claim_raw,
            tasks=tasks,
            recorded_at_utc=captured_at_utc,
            attempted_task_ids=[str(item["task_id"]) for item in tasks[: index + 1]],
            failed_task_id=task_id,
            failed_stage="create_thread_response_attestation",
            failure_class="INFRASTRUCTURE_FAILURE",
            failure_raw=response_raw,
            failure_raw_path=(
                f"evals/m4/execution/m4.2/platform-observations/{task_id}/{RAW_RESPONSE_NAME}"
            ),
            diagnostic=";".join(attestation["errors"]),
            attempt_count=index + 1,
        )
        return {**stopped, "writes": 3}
    receipt = _receipt(
        repo_root=repo_root,
        claim=claim,
        claim_raw=claim_raw,
        task=tasks[index],
        task_claim=task_claim,
        index=index,
        response=response,
        response_attestation=attestation,
        created_at_utc=captured_at_utc,
    )
    try:
        protocol.exclusive_create_json(receipt_path, receipt)
    except FileExistsError:
        stopped = _write_failure_terminal(
            repo_root,
            paths,
            claim=claim,
            claim_raw=claim_raw,
            tasks=tasks,
            recorded_at_utc=captured_at_utc,
            attempted_task_ids=[str(item["task_id"]) for item in tasks[: index + 1]],
            failed_task_id=task_id,
            failed_stage="dispatch_receipt_exclusive_create",
            failure_class="INFRASTRUCTURE_FAILURE",
            failure_raw=b"dispatch receipt target preexisted after raw response capture",
            failure_raw_path=None,
            diagnostic="dispatch_receipt_target_preexists",
            attempt_count=index + 1,
        )
        return {**stopped, "writes": 3}
    result = protocol.audit_execution(
        repo_root,
        claim_path=paths.claim,
        observations_base=paths.observations,
        results_base=paths.results,
        terminal_path=paths.terminal,
        results_manifest_path=paths.results_manifest,
        m5_path=paths.m5,
        verify_git=verify_git,
        enforce_frozen_hashes=enforce_frozen_hashes,
        authorization_path=authorization_path,
        control_path=control_path,
    )
    return {**result, "writes": 3}


def record_final(
    repo_root: Path,
    *,
    task_id: str,
    final_raw: bytes,
    observed_at_utc: str,
    claim_path: Path | None = None,
    observations_base: Path | None = None,
    results_base: Path | None = None,
    terminal_path: Path | None = None,
    results_manifest_path: Path | None = None,
    m5_path: Path | None = None,
    verify_git: bool = True,
    enforce_frozen_hashes: bool = True,
    authorization_path: Path | None = None,
    control_path: Path | None = None,
) -> dict[str, Any]:
    if protocol.ISO_UTC_RE.fullmatch(observed_at_utc) is None:
        return {
            "status": "INVALID",
            "errors": ["observed_at_utc_invalid"],
            "writes": 0,
        }
    paths = _paths(
        repo_root,
        claim_path=claim_path,
        observations_base=observations_base,
        results_base=results_base,
        terminal_path=terminal_path,
        results_manifest_path=results_manifest_path,
        m5_path=m5_path,
    )
    state = protocol.audit_execution(
        repo_root,
        claim_path=paths.claim,
        observations_base=paths.observations,
        results_base=paths.results,
        terminal_path=paths.terminal,
        results_manifest_path=paths.results_manifest,
        m5_path=paths.m5,
        verify_git=verify_git,
        enforce_frozen_hashes=enforce_frozen_hashes,
        authorization_path=authorization_path,
        control_path=control_path,
    )
    if state["status"] != "CLAIMED_IN_PROGRESS" or state["errors"]:
        return {**state, "writes": 0}
    if state["tasks"] != state["finalizations"] + 1:
        return {
            "status": "INVALID",
            "errors": ["no_single_dispatched_task_awaiting_final"],
            "writes": 0,
        }
    claim, claim_raw, tasks = _claim_and_tasks(
        repo_root,
        paths,
        verify_git=verify_git,
        enforce_frozen_hashes=enforce_frozen_hashes,
        authorization_path=authorization_path,
        control_path=control_path,
    )
    index = state["finalizations"]
    if task_id != tasks[index]["task_id"]:
        return {
            "status": "INVALID",
            "errors": ["final_not_next_frozen_task"],
            "writes": 0,
        }
    final_path = paths.results / task_id / RAW_FINAL_NAME
    if final_path.exists():
        return {
            "status": "INVALID",
            "errors": ["raw_final_target_preexists"],
            "writes": 0,
        }
    protocol.exclusive_create_bytes(final_path, final_raw)
    final_errors = protocol._validate_task_result(
        final_raw, tasks[index], claim["task_claims"][index]
    )
    if final_errors:
        stopped = _write_failure_terminal(
            repo_root,
            paths,
            claim=claim,
            claim_raw=claim_raw,
            tasks=tasks,
            recorded_at_utc=observed_at_utc,
            attempted_task_ids=[str(item["task_id"]) for item in tasks[: index + 1]],
            failed_task_id=task_id,
            failed_stage="raw_final_protocol_validation",
            failure_class="PROTOCOL_FAILURE",
            failure_raw=final_raw,
            failure_raw_path=f"evals/m4/results/m4.2/{task_id}/{RAW_FINAL_NAME}",
            diagnostic=";".join(final_errors),
            attempt_count=index + 1,
        )
        return {**stopped, "writes": 2}
    if index == 59:
        return {
            "status": "READY_TO_RECORD_COMPLETE_TERMINAL",
            "errors": [],
            "tasks": 60,
            "threads": 60,
            "finalizations": 60,
            "results": 60,
            "retries": 0,
            "repairs": 0,
            "followups": 0,
            "writes": 1,
        }
    result = protocol.audit_execution(
        repo_root,
        claim_path=paths.claim,
        observations_base=paths.observations,
        results_base=paths.results,
        terminal_path=paths.terminal,
        results_manifest_path=paths.results_manifest,
        m5_path=paths.m5,
        verify_git=verify_git,
        enforce_frozen_hashes=enforce_frozen_hashes,
        authorization_path=authorization_path,
        control_path=control_path,
    )
    if result["status"] == "CLAIMED_IN_PROGRESS" and not result["errors"]:
        return {**result, "status": "PROTOCOL_VALID_CONTINUE", "writes": 1}
    return {**result, "writes": 1}


def record_terminal(
    repo_root: Path,
    *,
    state: str,
    recorded_at_utc: str,
    failed_task_id: str | None = None,
    failed_stage: str | None = None,
    failure_class: str | None = None,
    failure_evidence_raw: bytes | None = None,
    failure_evidence_path: str | None = None,
    attempt_included: bool = False,
    claim_path: Path | None = None,
    observations_base: Path | None = None,
    results_base: Path | None = None,
    terminal_path: Path | None = None,
    results_manifest_path: Path | None = None,
    m5_path: Path | None = None,
    verify_git: bool = True,
    enforce_frozen_hashes: bool = True,
    authorization_path: Path | None = None,
    control_path: Path | None = None,
) -> dict[str, Any]:
    if state not in {
        "COMPLETE_UNJUDGED",
        "STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE",
    }:
        return {"status": "INVALID", "errors": ["terminal_state_invalid"], "writes": 0}
    if protocol.ISO_UTC_RE.fullmatch(recorded_at_utc) is None:
        return {"status": "INVALID", "errors": ["recorded_at_utc_invalid"], "writes": 0}
    paths = _paths(
        repo_root,
        claim_path=claim_path,
        observations_base=observations_base,
        results_base=results_base,
        terminal_path=terminal_path,
        results_manifest_path=results_manifest_path,
        m5_path=m5_path,
    )
    if paths.terminal.exists():
        return {
            "status": "TERMINAL_ALREADY_EXISTS",
            "errors": ["terminal_target_preexists"],
            "writes": 0,
        }
    try:
        claim, claim_raw, tasks = _claim_and_tasks(
            repo_root,
            paths,
            verify_git=verify_git,
            enforce_frozen_hashes=enforce_frozen_hashes,
            authorization_path=authorization_path,
            control_path=control_path,
        )
    except protocol.ContractError as error:
        return {"status": "INVALID", "errors": [error.code], "writes": 0}
    evidence, evidence_errors = _evidence_snapshot(
        repo_root, paths, claim, claim_raw, tasks
    )
    if state == "COMPLETE_UNJUDGED":
        if evidence_errors:
            return {"status": "INVALID", "errors": evidence_errors, "writes": 0}
        if evidence["receipt_count"] != 60 or evidence["ready_response_count"] != 60 or evidence["final_count"] != 60:
            return {
                "status": "INVALID",
                "errors": ["complete_terminal_requires_60_60_60"],
                "writes": 0,
            }
        if any(evidence["protocol_errors"].values()):
            return {
                "status": "INVALID",
                "errors": ["complete_terminal_protocol_errors_present"],
                "writes": 0,
            }
        attempted = [str(task["task_id"]) for task in tasks]
        terminal = _terminal_value(
            claim=claim,
            claim_raw=claim_raw,
            evidence=evidence,
            state=state,
            recorded_at_utc=recorded_at_utc,
            attempted_task_ids=attempted,
        )
    else:
        if not isinstance(failed_stage, str) or not failed_stage:
            return {"status": "INVALID", "errors": ["failed_stage_required"], "writes": 0}
        completed_or_dispatched = max(evidence["receipt_count"], evidence["response_count"])
        attempt_count = completed_or_dispatched + (1 if attempt_included else 0)
        if failed_task_id is not None:
            task_ids = [str(task["task_id"]) for task in tasks]
            if failed_task_id not in task_ids:
                return {"status": "INVALID", "errors": ["failed_task_id_invalid"], "writes": 0}
            failure_index = task_ids.index(failed_task_id)
            attempted = task_ids[: failure_index + 1]
            attempt_count = max(attempt_count, failure_index + 1 if attempt_included else failure_index)
        else:
            attempted = [str(task["task_id"]) for task in tasks[:attempt_count]]
        terminal = _terminal_value(
            claim=claim,
            claim_raw=claim_raw,
            evidence=evidence,
            state=state,
            recorded_at_utc=recorded_at_utc,
            attempted_task_ids=attempted,
            failed_task_id=failed_task_id,
            failed_stage=failed_stage,
            failure_class=failure_class or "INFRASTRUCTURE_FAILURE",
            failure_raw=failure_evidence_raw or b"terminal failure",
            failure_raw_path=failure_evidence_path,
            diagnostic=failed_stage,
            attempt_count=attempt_count,
        )
    try:
        protocol.exclusive_create_json(paths.terminal, terminal)
    except FileExistsError:
        return {
            "status": "TERMINAL_ALREADY_EXISTS",
            "errors": ["terminal_target_preexists"],
            "writes": 0,
        }
    result = protocol.audit_execution(
        repo_root,
        claim_path=paths.claim,
        observations_base=paths.observations,
        results_base=paths.results,
        terminal_path=paths.terminal,
        results_manifest_path=paths.results_manifest,
        m5_path=paths.m5,
        verify_git=verify_git,
        enforce_frozen_hashes=enforce_frozen_hashes,
        authorization_path=authorization_path,
        control_path=control_path,
    )
    return {**result, "writes": 1}


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise protocol.ContractError("argument_error:" + message)


def _invalid_cli(code: str, *, mode: str = "INVALID") -> dict[str, Any]:
    return {"mode": mode, "status": "INVALID", "errors": [code], "writes": 0}


def _missing(args: argparse.Namespace, *names: str) -> str | None:
    for name in names:
        if getattr(args, name) is None:
            return "argument_required:" + name.replace("_", "-")
    return None


def _cli_result(
    args: argparse.Namespace,
    *,
    repo_root: Path,
    audit_kwargs: Mapping[str, Any],
) -> dict[str, Any]:
    if args.next_action:
        return next_action(repo_root, **audit_kwargs)
    if args.record_dispatch:
        missing = _missing(args, "task_id", "response_file", "captured_at_utc")
        if missing:
            return _invalid_cli(missing, mode="RECORD_DISPATCH")
        try:
            response_raw = SOURCE_READER(Path(args.response_file))
        except OSError as error:
            return _invalid_cli(
                "response_file_read_failed:" + type(error).__name__,
                mode="RECORD_DISPATCH",
            )
        return {
            "mode": "RECORD_DISPATCH",
            **record_dispatch(
                repo_root,
                task_id=args.task_id,
                response_raw=response_raw,
                captured_at_utc=args.captured_at_utc,
                **audit_kwargs,
            ),
        }
    if args.record_final:
        missing = _missing(args, "task_id", "final_file", "observed_at_utc")
        if missing:
            return _invalid_cli(missing, mode="RECORD_FINAL")
        try:
            final_raw = SOURCE_READER(Path(args.final_file))
        except OSError as error:
            return _invalid_cli(
                "final_file_read_failed:" + type(error).__name__, mode="RECORD_FINAL"
            )
        return {
            "mode": "RECORD_FINAL",
            **record_final(
                repo_root,
                task_id=args.task_id,
                final_raw=final_raw,
                observed_at_utc=args.observed_at_utc,
                **audit_kwargs,
            ),
        }
    if args.record_terminal:
        missing = _missing(args, "state", "recorded_at_utc")
        if missing:
            return _invalid_cli(missing, mode="RECORD_TERMINAL")
        if args.state not in {
            "COMPLETE_UNJUDGED",
            "STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE",
        }:
            return _invalid_cli("terminal_state_invalid", mode="RECORD_TERMINAL")
        if args.failure_class not in {
            None,
            "PROTOCOL_FAILURE",
            "INFRASTRUCTURE_FAILURE",
        }:
            return _invalid_cli("failure_class_invalid", mode="RECORD_TERMINAL")
        if args.state == "STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE":
            missing = _missing(args, "failed_stage", "failure_class")
            if missing:
                return _invalid_cli(missing, mode="RECORD_TERMINAL")
        failure_raw = None
        if args.failure_file is not None:
            try:
                failure_raw = SOURCE_READER(Path(args.failure_file))
            except OSError as error:
                return _invalid_cli(
                    "failure_file_read_failed:" + type(error).__name__,
                    mode="RECORD_TERMINAL",
                )
        return {
            "mode": "RECORD_TERMINAL",
            **record_terminal(
                repo_root,
                state=args.state,
                failed_task_id=args.failed_task_id,
                failed_stage=args.failed_stage,
                failure_class=args.failure_class,
                failure_evidence_raw=failure_raw,
                failure_evidence_path=args.failure_file,
                attempt_included=args.attempt_included,
                recorded_at_utc=args.recorded_at_utc,
                **audit_kwargs,
            ),
        }
    return {"mode": "CHECK_ONLY", **check_recorder(repo_root, **audit_kwargs)}


def main(
    argv: Sequence[str] | None = None,
    *,
    repo_root: Path = protocol.REPO_ROOT,
    audit_kwargs: Mapping[str, Any] | None = None,
) -> int:
    parser = _ArgumentParser()
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--check", action="store_true")
    modes.add_argument("--next-action", action="store_true")
    modes.add_argument("--record-dispatch", action="store_true")
    modes.add_argument("--record-final", action="store_true")
    modes.add_argument("--record-terminal", action="store_true")
    parser.add_argument("--task-id")
    parser.add_argument("--response-file")
    parser.add_argument("--captured-at-utc")
    parser.add_argument("--final-file")
    parser.add_argument("--observed-at-utc")
    parser.add_argument("--state")
    parser.add_argument("--recorded-at-utc")
    parser.add_argument("--failed-task-id")
    parser.add_argument("--failed-stage")
    parser.add_argument("--failure-class")
    parser.add_argument("--failure-file")
    parser.add_argument("--attempt-included", action="store_true")
    try:
        args = parser.parse_args(argv)
        result = _cli_result(
            args,
            repo_root=repo_root,
            audit_kwargs={} if audit_kwargs is None else audit_kwargs,
        )
    except protocol.ContractError as error:
        result = _invalid_cli(error.code)
    print(_compact(result))
    successful_statuses = {
        "READY_UNCLAIMED",
        "CLAIMED_IN_PROGRESS",
        "PROTOCOL_VALID_CONTINUE",
        "READY_TO_RECORD_COMPLETE_TERMINAL",
        "COMPLETE_UNJUDGED",
        "STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE",
    }
    return 0 if result["status"] in successful_statuses else 1


if __name__ == "__main__":
    raise SystemExit(main())
