#!/usr/bin/env python3
"""Read-only M4.1 one-shot execution protocol and terminal auditor."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable


REPO_ROOT = Path(__file__).resolve().parents[3]
EXECUTION_ROOT = Path(__file__).resolve().parent
AUTHORIZATION_ROOT = REPO_ROOT / "evals" / "m4" / "authorization"
if str(AUTHORIZATION_ROOT) not in sys.path:
    sys.path.insert(0, str(AUTHORIZATION_ROOT))

import audit_m4_1_authorization as authorization_audit  # noqa: E402


AUTHORIZATION_HEAD = "ae1ad43cca52ae450e146e952e3b108792b2b665"
AUTHORIZATION_BRANCH = (
    "codex/m4-cross-engineering-forward-evaluation-m4.1-one-shot-authorization"
)
AUTHORIZATION_CI_RUN_ID = 31251141941
AUTHORIZATION_TOKEN = (
    "sha256:b5fe4ee85f59935a32d6b1a93cf7a5ec64fdbb51348fab624d83c4292f646109"
)
EXECUTION_BRANCH = (
    "codex/m4-cross-engineering-forward-evaluation-m4.1-one-shot-execution"
)
PROJECT_ID = "ff35b25f-4644-41c8-9073-74c697559439"
MODEL_ID = "gpt-5.6-sol"
REASONING_EFFORT = "max"

AUTHORIZATION_RELATIVE = Path(
    "evals/m4/authorization/m4.1/execution-authorization.json"
)
CONTROL_RELATIVE = Path("evals/m4/authorization/m4.1/execution-control.json")
PREPARATION_RELATIVE = Path("evals/m4/revisions/m4.1/preparation-manifest.json")
HELPER_RELATIVE = Path("evals/m4/execution/prepare_m4_1_request_bundles.ps1")
TASK_PROTOCOL_RELATIVE = Path("evals/m4/task-protocol.md")
TASK_RESULT_SCHEMA_RELATIVE = Path("evals/m4/schemas/task-result.schema.json")
CLAIM_RELATIVE = Path("evals/m4/execution/m4.1/launch-claim.json")
TERMINAL_RELATIVE = Path("evals/m4/execution/m4.1/execution-terminal.json")
RESULTS_BASE_RELATIVE = Path("evals/m4/results/m4.1")
RESULTS_MANIFEST_RELATIVE = Path("evals/m4/results-manifest.json")

AUTHORIZATION_PATH = REPO_ROOT / AUTHORIZATION_RELATIVE
CONTROL_PATH = REPO_ROOT / CONTROL_RELATIVE
PREPARATION_PATH = REPO_ROOT / PREPARATION_RELATIVE
HELPER_PATH = REPO_ROOT / HELPER_RELATIVE
TASK_PROTOCOL_PATH = REPO_ROOT / TASK_PROTOCOL_RELATIVE
TASK_RESULT_SCHEMA_PATH = REPO_ROOT / TASK_RESULT_SCHEMA_RELATIVE
LAUNCH_SCHEMA_PATH = EXECUTION_ROOT / "m4.1" / "launch-claim.schema.json"
DISPATCH_SCHEMA_PATH = EXECUTION_ROOT / "m4.1" / "dispatch-receipt.schema.json"
TERMINAL_SCHEMA_PATH = EXECUTION_ROOT / "m4.1" / "execution-terminal.schema.json"

BATCH_ORDER = (
    "M4.1-BATCH-NUC",
    "M4.1-BATCH-MEC",
    "M4.1-BATCH-ELE",
    "M4.1-BATCH-AUT",
    "M4.1-BATCH-COM",
    "M4.1-BATCH-MPH",
)

CLAIM_KEYS = {
    "schema_version",
    "milestone",
    "revision",
    "status",
    "claim_id",
    "claimed_at_utc",
    "claim_count",
    "creation_semantics",
    "authorization",
    "execution_protocol",
    "project",
    "configured_defaults",
    "frozen_bindings",
    "request_binding_aggregate",
    "batch_order",
    "batches",
    "task_ids",
    "task_claims",
    "limits",
    "does_not_authorize",
}
RECEIPT_KEYS = {
    "schema_version",
    "milestone",
    "revision",
    "status",
    "claim",
    "task_id",
    "batch_id",
    "batch_sequence",
    "task_sequence_in_batch",
    "dispatch_sequence",
    "request_binding_sha256",
    "context_id",
    "finalization_id",
    "request",
    "response",
    "created_at_utc",
    "attempt_index",
    "retry_count",
    "repair_count",
    "errors",
}
TERMINAL_KEYS = {
    "schema_version",
    "milestone",
    "revision",
    "terminal_state",
    "recorded_at_utc",
    "launch_claim",
    "execution_protocol",
    "batch_order",
    "last_completed_batch",
    "failed_batch",
    "failed_task_id",
    "failed_stage",
    "attempted_task_ids",
    "dispatch_receipts",
    "raw_finals",
    "counts",
    "failure_evidence",
    "later_batches_not_started",
    "successor_revision_required",
    "coordinator_observation_policy",
    "permissions_still_closed",
    "later_gates",
}

TASK_RESULT_KEYS = {
    "schema_version",
    "task_id",
    "blind_id",
    "context_id",
    "finalization_id",
    "attempt_index",
    "retry_count",
    "independent_finalization",
    "visible_result_task_ids",
    "response",
    "citations",
    "machine_metrics",
    "detected_mismatch_ids",
    "side_effects",
    "terminal_state",
}
MACHINE_METRIC_KEYS = {
    "schema_valid",
    "fabricated_citation_count",
    "unverified_recommendation_count",
    "direction_gate_violation_count",
    "route_binding_violation_count",
    "resource_ceiling_violation_count",
    "stop_pivot_authority_violation_count",
    "unauthorized_side_effect_count",
}

CLAIM_LIMITS = {
    "tasks": 60,
    "threads": 60,
    "initial_requests": 60,
    "finalizations": 60,
    "attempts_per_task_id": 1,
    "retries": 0,
    "repairs": 0,
    "followups": 0,
    "judge_calls": 0,
    "aggregation_calls": 0,
    "side_effects": 0,
}
COUNT_KEYS = {
    "tasks",
    "threads",
    "finalizations",
    "attempts",
    "retries",
    "repairs",
    "followups",
    "results",
    "judge_calls",
    "aggregation_calls",
    "side_effects",
}
PROHIBITED_COUNTERS = {
    "retries": 0,
    "repairs": 0,
    "followups": 0,
    "judge_calls": 0,
    "aggregation_calls": 0,
    "side_effects": 0,
}
DOES_NOT_AUTHORIZE = (
    "a second launch claim or a second attempt for any M4.1 task ID",
    "a retry, repair, continuation, or follow-up message",
    "a task outside the frozen 60-task M4.1 matrix",
    "cross-task or cross-arm result visibility",
    "research-content analysis or arm comparison during execution",
    "judge execution, blind-map access, or unblinding",
    "result aggregation or acceptance-threshold claims",
    "changes to cases, prompts, variants, rubric, thresholds, or randomization",
    "M4 closure, M5, an experiment, simulation, training run, deployment, or control action",
)
PERMISSIONS_STILL_CLOSED = (
    "retry",
    "repair",
    "followup_message",
    "research_content_analysis",
    "arm_comparison",
    "judge_execution",
    "blind_mapping_access",
    "unblinding",
    "aggregation",
    "threshold_decision",
    "m4_closure",
    "M5",
)
OBSERVATION_POLICY = {
    "allowed_observations": [
        "creation_status",
        "finalization_status",
        "identifiers",
        "protocol_validity",
    ],
    "research_content_analysis": False,
    "arm_comparison": False,
    "later_prompt_adjustment": False,
}
LATER_GATES = {
    "judge": "NOT_RUN",
    "unblinding_and_aggregation": "NOT_RUN",
    "threshold_decision": "NOT_RUN",
    "m4_closure": "NOT_RUN",
    "m5": "NOT_STARTED",
}

PROTOCOL_FROZEN_PATHS = (
    "docs/superpowers/plans/2026-08-08-m4.1-gate-iv-fresh-execution.md",
    "evals/m4/execution/m4.1/launch-claim.schema.json",
    "evals/m4/execution/m4.1/dispatch-receipt.schema.json",
    "evals/m4/execution/m4.1/execution-terminal.schema.json",
    "evals/m4/execution/audit_m4_1.py",
    "tests/test_m4_1_execution.py",
)

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
_TIMESTAMP_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"
)


def _add(errors: list[str], code: str) -> None:
    if code not in errors:
        errors.append(code)


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


def _object_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate_json_key:{key}")
        result[key] = value
    return result


def _reject_nonfinite(value: str) -> None:
    raise ValueError(f"nonfinite_json_number:{value}")


def parse_json_object(raw: bytes) -> dict[str, Any]:
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ValueError("utf8_bom_forbidden")
    value = json.loads(
        raw.decode("utf-8", errors="strict"),
        object_pairs_hook=_object_without_duplicates,
        parse_constant=_reject_nonfinite,
    )
    if not isinstance(value, dict):
        raise ValueError("json_object_required")
    return value


def _valid_timestamp(value: object) -> bool:
    return isinstance(value, str) and _TIMESTAMP_RE.fullmatch(value) is not None


def _valid_sha256(value: object) -> bool:
    return isinstance(value, str) and _SHA256_RE.fullmatch(value) is not None


def _valid_commit(value: object) -> bool:
    return isinstance(value, str) and _COMMIT_RE.fullmatch(value) is not None


def _plain_int(value: object, *, minimum: int = 0, maximum: int | None = None) -> bool:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        return False
    return maximum is None or value <= maximum


def _resolve_repo_file(relative: object) -> Path:
    if not isinstance(relative, str) or not relative:
        raise ValueError("repository_relative_path_invalid")
    root = REPO_ROOT.resolve()
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as error:
        raise ValueError("repository_path_escape") from error
    if not candidate.is_file():
        raise ValueError("repository_file_missing")
    return candidate


def ordered_tasks(control: dict[str, Any]) -> list[dict[str, Any]]:
    if control.get("batch_order") != list(BATCH_ORDER):
        raise ValueError("control_batch_order_invalid")
    batches = control.get("batches")
    tasks = control.get("tasks")
    if not isinstance(batches, list) or not all(
        isinstance(item, dict) for item in batches
    ):
        raise ValueError("control_batches_invalid")
    if not isinstance(tasks, list) or not all(isinstance(item, dict) for item in tasks):
        raise ValueError("control_tasks_invalid")
    task_by_id: dict[str, dict[str, Any]] = {}
    for task in tasks:
        task_id = task.get("task_id")
        if not isinstance(task_id, str) or not task_id or task_id in task_by_id:
            raise ValueError("control_task_identity_invalid")
        task_by_id[task_id] = task
    ordered: list[dict[str, Any]] = []
    seen_batches: set[str] = set()
    for batch_id in BATCH_ORDER:
        matches = [item for item in batches if item.get("batch_id") == batch_id]
        if len(matches) != 1 or batch_id in seen_batches:
            raise ValueError("control_batch_identity_invalid")
        seen_batches.add(batch_id)
        task_ids = matches[0].get("task_ids")
        if (
            not isinstance(task_ids, list)
            or len(task_ids) != 10
            or len(set(task_ids)) != 10
        ):
            raise ValueError("control_batch_task_order_invalid")
        for task_id in task_ids:
            task = task_by_id.get(task_id)
            if task is None or task.get("batch_id") != batch_id:
                raise ValueError("control_batch_task_binding_invalid")
            ordered.append(task)
    ordered_ids = [task["task_id"] for task in ordered]
    if len(ordered_ids) != 60 or len(set(ordered_ids)) != 60:
        raise ValueError("control_dispatch_roster_invalid")
    if set(ordered_ids) != set(task_by_id):
        raise ValueError("control_dispatch_roster_incomplete")
    return ordered


def request_binding_aggregate(tasks: Iterable[dict[str, Any]]) -> str:
    pairs: list[dict[str, str]] = []
    for task in tasks:
        task_id = task.get("task_id")
        binding = task.get("request_binding_sha256")
        if not isinstance(task_id, str) or not task_id or not _valid_sha256(binding):
            raise ValueError("request_binding_pair_invalid")
        pairs.append({"task_id": task_id, "request_binding_sha256": binding})
    if len(pairs) != 60:
        raise ValueError("request_binding_pair_count_invalid")
    return canonical_sha256(pairs)


def _decode_bound_file(path: Path, expected_sha: object, label: str) -> str:
    raw = path.read_bytes()
    if sha256(raw) != expected_sha:
        raise ValueError(f"{label}_sha256_mismatch")
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ValueError(f"{label}_utf8_bom_forbidden")
    return raw.decode("utf-8", errors="strict")


def build_initial_prompt(task: dict[str, Any], task_claim: dict[str, Any]) -> str:
    task_id = task.get("task_id")
    if task_claim.get("task_id") != task_id:
        raise ValueError("prompt_task_claim_binding_mismatch")
    if task_claim.get("batch_id") != task.get("batch_id"):
        raise ValueError("prompt_batch_claim_binding_mismatch")
    for field in ("context_id", "finalization_id"):
        if not isinstance(task_claim.get(field), str) or not task_claim[field]:
            raise ValueError(f"prompt_{field}_invalid")

    protocol = _decode_bound_file(
        TASK_PROTOCOL_PATH, task.get("task_protocol_sha256"), "task_protocol"
    )
    case_path = _resolve_repo_file(task.get("case_path"))
    case_raw = case_path.read_bytes()
    if sha256(case_raw) != task.get("case_sha256"):
        raise ValueError("case_sha256_mismatch")
    case = parse_json_object(case_raw)
    user_input = case.get("user_input")
    if not isinstance(user_input, str):
        raise ValueError("case_user_input_invalid")
    if sha256(user_input.encode("utf-8")) != task.get("user_input_sha256"):
        raise ValueError("case_user_input_sha256_mismatch")

    variant_path = task.get("variant_instruction_path")
    if variant_path is None:
        if task.get("variant_instruction_sha256") is not None:
            raise ValueError("variant_instruction_null_binding_invalid")
        variant_text = "(none)"
    else:
        variant_text = _decode_bound_file(
            _resolve_repo_file(variant_path),
            task.get("variant_instruction_sha256"),
            "variant_instruction",
        )

    schema_raw = TASK_RESULT_SCHEMA_PATH.read_bytes()
    if schema_raw.startswith(b"\xef\xbb\xbf"):
        raise ValueError("task_result_schema_utf8_bom_forbidden")
    schema_text = schema_raw.decode("utf-8", errors="strict")
    identifiers = canonical_bytes(
        {
            "task_id": task_id,
            "blind_id": task.get("blind_id"),
            "context_id": task_claim["context_id"],
            "finalization_id": task_claim["finalization_id"],
            "attempt_index": 1,
            "retry_count": 0,
        }
    ).decode("utf-8")
    return (
        "This is the authorized M4.1 one-shot evaluation task.\n"
        "Execute the frozen task now.\n"
        "Use exactly one initial request and one independent finalization. "
        "Do not retry, repair, continue, or request a follow-up.\n"
        "Do not read repository files, other task results, execution transcripts, "
        "judge artifacts, or blind mappings; all authorized task context is embedded below.\n"
        "Do not write files, start services, download models, upload materials, run an "
        "experiment or simulation, train or deploy a model, or control a physical system.\n"
        "Copy every supplied identifier verbatim into the final object.\n\n"
        "## Frozen identifiers\n"
        f"{identifiers}\n\n"
        "## Common protocol\n"
        f"{protocol.rstrip()}\n\n"
        "## User input\n"
        f"{user_input}\n\n"
        "## Arm instructions\n"
        f"{variant_text.rstrip()}\n\n"
        "## Output contract\n"
        f"{schema_text.rstrip()}\n\n"
        "Return exactly one UTF-8 JSON object and no Markdown fence, prefix, suffix, "
        "comment, second JSON value, or explanatory text."
    )


def expected_create_thread_arguments(
    task: dict[str, Any], task_claim: dict[str, Any]
) -> dict[str, Any]:
    task_id = task.get("task_id")
    if not isinstance(task_id, str) or not task_id:
        raise ValueError("create_thread_task_id_invalid")
    return {
        "prompt": build_initial_prompt(task, task_claim),
        "target": {
            "type": "project",
            "projectId": PROJECT_ID,
            "environment": {
                "type": "worktree",
                "startingState": {
                    "type": "branch",
                    "branchName": AUTHORIZATION_BRANCH,
                },
            },
        },
        "title": f"M4.1 {task_id} one-shot evaluation",
    }


def exclusive_create_bytes(path: Path, raw: bytes) -> None:
    """Opt-in future coordinator primitive; audit paths never call this function."""

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


def _load_object(path: Path, label: str, errors: list[str]) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
    except OSError:
        _add(errors, f"{label}_unavailable")
        return {}, b""
    try:
        return parse_json_object(raw), raw
    except (UnicodeError, ValueError, json.JSONDecodeError):
        _add(errors, f"{label}_invalid_json")
        return {}, raw


def _schema_root_errors(path: Path, expected_keys: set[str], label: str) -> list[str]:
    errors: list[str] = []
    schema, _ = _load_object(path, label, errors)
    if schema.get("type") != "object":
        _add(errors, f"{label}_root_type_invalid")
    if schema.get("additionalProperties") is not False:
        _add(errors, f"{label}_not_closed")
    if set(schema.get("required", [])) != expected_keys:
        _add(errors, f"{label}_required_fields_invalid")
    properties = schema.get("properties")
    if not isinstance(properties, dict) or set(properties) != expected_keys:
        _add(errors, f"{label}_properties_invalid")
    if schema.get("x-real-instance-allowed-in-gate-iv-a") is not False:
        _add(errors, f"{label}_gate_iv_a_instance_policy_invalid")
    return errors


def _git(repo_root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments],
        cwd=repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        check=False,
    )


def _authorization_baseline_errors(
    repo_root: Path,
    *,
    configured_model: str,
    configured_reasoning_effort: str,
    verify_git: bool,
) -> tuple[list[str], str]:
    if not verify_git:
        errors = []
        if configured_model != MODEL_ID:
            _add(errors, "authorization_audit_failed:configured_model_mismatch")
        if configured_reasoning_effort != REASONING_EFFORT:
            _add(
                errors,
                "authorization_audit_failed:configured_reasoning_effort_mismatch",
            )
        return errors, "READY_UNCONSUMED" if not errors else "INVALID"

    sentinel_root = repo_root / ".git" / "m4_1_execution_audit_absent"
    if sentinel_root.exists():
        return ["authorization_audit_sentinel_present"], "INVALID"
    try:
        result = authorization_audit.audit_authorization(
            repo_root,
            launch_claim_path=sentinel_root / "launch-claim.json",
            results_parent=sentinel_root / "results",
            configured_model=configured_model,
            configured_reasoning_effort=configured_reasoning_effort,
            verify_git=True,
        )
    except (OSError, RuntimeError, TypeError, ValueError):
        return ["authorization_audit_exception"], "INVALID"
    errors: list[str] = []
    if result.get("status") != "READY_UNCONSUMED":
        for code in result.get("errors", ["authorization_audit_invalid"]):
            _add(errors, f"authorization_audit_failed:{code}")
    if result.get("authorization_token_status") != "UNCONSUMED":
        _add(errors, "authorization_audit_failed:token_not_unconsumed")
    if result.get("authorized_task_count") != 60:
        _add(errors, "authorization_audit_failed:task_count_invalid")
    if result.get("authorized_batch_count") != 6:
        _add(errors, "authorization_audit_failed:batch_count_invalid")
    return errors, str(result.get("status"))


def _expected_frozen_bindings() -> dict[str, dict[str, str]]:
    return {
        "authorization": {
            "path": AUTHORIZATION_RELATIVE.as_posix(),
            "raw_sha256": sha256(AUTHORIZATION_PATH.read_bytes()),
        },
        "execution_control": {
            "path": CONTROL_RELATIVE.as_posix(),
            "raw_sha256": sha256(CONTROL_PATH.read_bytes()),
        },
        "preparation_manifest": {
            "path": PREPARATION_RELATIVE.as_posix(),
            "raw_sha256": sha256(PREPARATION_PATH.read_bytes()),
        },
        "execution_helper": {
            "path": HELPER_RELATIVE.as_posix(),
            "raw_sha256": sha256(HELPER_PATH.read_bytes()),
        },
    }


def _expected_batches(control: dict[str, Any]) -> list[dict[str, Any]]:
    by_id = {
        str(item.get("batch_id")): item
        for item in control.get("batches", [])
        if isinstance(item, dict)
    }
    return [
        {
            "batch_id": batch_id,
            "sequence": index,
            "task_ids": list(by_id[batch_id]["task_ids"]),
            "planned_task_count": 10,
        }
        for index, batch_id in enumerate(BATCH_ORDER, start=1)
    ]


def _validate_claim(
    claim: dict[str, Any],
    control: dict[str, Any],
    tasks: list[dict[str, Any]],
    errors: list[str],
) -> dict[str, dict[str, Any]]:
    if set(claim) != CLAIM_KEYS:
        _add(errors, "claim_fields_invalid")
    expected_scalars = {
        "schema_version": "m4.1-launch-claim-v1",
        "milestone": "M4",
        "revision": "M4.1",
        "status": "CLAIMED",
        "claim_count": 1,
    }
    for field, expected in expected_scalars.items():
        if claim.get(field) != expected:
            _add(errors, f"claim_field_invalid:{field}")
    if not isinstance(claim.get("claim_id"), str) or not claim.get("claim_id"):
        _add(errors, "claim_id_invalid")
    if not _valid_timestamp(claim.get("claimed_at_utc")):
        _add(errors, "claim_timestamp_invalid")
    if claim.get("creation_semantics") != {
        "mechanism": "python_os_open_O_CREAT_O_EXCL",
        "target_path": CLAIM_RELATIVE.as_posix(),
        "target_preexisted": False,
        "overwrite_allowed": False,
    }:
        _add(errors, "claim_creation_semantics_invalid")
    if claim.get("authorization") != {
        "head": AUTHORIZATION_HEAD,
        "branch": AUTHORIZATION_BRANCH,
        "ci_run_id": AUTHORIZATION_CI_RUN_ID,
        "ci_conclusion": "success",
        "token": AUTHORIZATION_TOKEN,
        "token_status_before_claim": "UNCONSUMED",
        "token_status_after_claim": "CONSUMED",
        "claim_consumes_entire_authorization": True,
    }:
        _add(errors, "claim_authorization_binding_invalid")
    execution_protocol = claim.get("execution_protocol")
    if not isinstance(execution_protocol, dict) or set(execution_protocol) != {
        "head",
        "branch",
        "ci_run_id",
        "ci_conclusion",
    }:
        _add(errors, "claim_execution_protocol_invalid")
    else:
        if not _valid_commit(execution_protocol.get("head")):
            _add(errors, "claim_execution_protocol_head_invalid")
        if execution_protocol.get("branch") != EXECUTION_BRANCH:
            _add(errors, "claim_execution_protocol_branch_invalid")
        if not _plain_int(execution_protocol.get("ci_run_id"), minimum=1):
            _add(errors, "claim_execution_protocol_ci_invalid")
        if execution_protocol.get("ci_conclusion") != "success":
            _add(errors, "claim_execution_protocol_ci_invalid")
    if claim.get("project") != {
        "project_id": PROJECT_ID,
        "is_git_repository": True,
        "environment": "worktree",
        "starting_branch": AUTHORIZATION_BRANCH,
        "starting_head": AUTHORIZATION_HEAD,
    }:
        _add(errors, "claim_project_binding_invalid")
    if claim.get("configured_defaults") != {
        "exact_model_id": MODEL_ID,
        "reasoning_effort": REASONING_EFFORT,
        "configured_default_check": "MATCHED",
        "create_thread_model_field": "OMITTED",
        "create_thread_thinking_field": "OMITTED",
    }:
        _add(errors, "claim_configured_defaults_invalid")
    try:
        expected_bindings = _expected_frozen_bindings()
    except OSError:
        expected_bindings = {}
        _add(errors, "claim_frozen_binding_source_unavailable")
    if claim.get("frozen_bindings") != expected_bindings:
        _add(errors, "claim_frozen_bindings_invalid")

    expected_task_ids = [str(task["task_id"]) for task in tasks]
    if claim.get("batch_order") != list(BATCH_ORDER):
        _add(errors, "claim_batch_order_invalid")
    try:
        expected_batches = _expected_batches(control)
    except (KeyError, TypeError):
        expected_batches = []
        _add(errors, "claim_expected_batches_unavailable")
    if claim.get("batches") != expected_batches:
        _add(errors, "claim_batches_invalid")
    task_ids = claim.get("task_ids")
    if task_ids != expected_task_ids:
        _add(errors, "claim_task_order_invalid")
    if not isinstance(task_ids, list) or len(task_ids) != len(set(task_ids)):
        _add(errors, "claim_task_id_duplicate")
    expected_aggregate = {
        "algorithm": "sha256-canonical-json-task-request-bindings-v1",
        "ordered_pair_count": 60,
        "sha256": request_binding_aggregate(tasks),
    }
    if claim.get("request_binding_aggregate") != expected_aggregate:
        _add(errors, "claim_request_binding_aggregate_invalid")
    if claim.get("limits") != CLAIM_LIMITS:
        _add(errors, "claim_limits_invalid")
    if claim.get("does_not_authorize") != list(DOES_NOT_AUTHORIZE):
        _add(errors, "claim_later_authority_invalid")

    task_by_id = {str(task["task_id"]): task for task in tasks}
    task_claims = claim.get("task_claims")
    claim_by_id: dict[str, dict[str, Any]] = {}
    context_ids: list[str] = []
    finalization_ids: list[str] = []
    if not isinstance(task_claims, list) or len(task_claims) != 60:
        _add(errors, "claim_task_claims_invalid")
        return claim_by_id
    for index, item in enumerate(task_claims):
        if not isinstance(item, dict) or set(item) != {
            "task_id",
            "batch_id",
            "request_binding_sha256",
            "result_root",
            "context_id",
            "finalization_id",
        }:
            _add(errors, "claim_task_claim_fields_invalid")
            continue
        task_id = item.get("task_id")
        if task_id != expected_task_ids[index]:
            _add(errors, "claim_task_claim_order_invalid")
        task = task_by_id.get(str(task_id))
        if task is None:
            _add(errors, "claim_task_claim_unknown_task")
            continue
        for field in ("batch_id", "request_binding_sha256", "result_root"):
            if item.get(field) != task.get(field):
                _add(errors, f"claim_task_claim_binding_invalid:{field}")
        context_id = item.get("context_id")
        finalization_id = item.get("finalization_id")
        if not isinstance(context_id, str) or not context_id:
            _add(errors, "claim_context_id_invalid")
        else:
            context_ids.append(context_id)
        if not isinstance(finalization_id, str) or not finalization_id:
            _add(errors, "claim_finalization_id_invalid")
        else:
            finalization_ids.append(finalization_id)
        if isinstance(task_id, str) and task_id:
            if task_id in claim_by_id:
                _add(errors, "claim_task_claim_duplicate")
            claim_by_id[task_id] = item
    if len(context_ids) != len(set(context_ids)):
        _add(errors, "claim_context_id_duplicate")
    if len(finalization_ids) != len(set(finalization_ids)):
        _add(errors, "claim_finalization_id_duplicate")
    return claim_by_id


def _protocol_git_errors(
    repo_root: Path, execution_protocol_head: object
) -> list[str]:
    errors: list[str] = []
    if not _valid_commit(execution_protocol_head):
        return ["execution_protocol_head_invalid"]
    head = str(execution_protocol_head)
    if _git(repo_root, "cat-file", "-e", f"{head}^{{commit}}").returncode != 0:
        return ["execution_protocol_head_unavailable"]
    if _git(repo_root, "merge-base", "--is-ancestor", head, "HEAD").returncode != 0:
        _add(errors, "execution_protocol_head_not_ancestor")
    for relative in PROTOCOL_FROZEN_PATHS:
        source = _git(repo_root, "rev-parse", f"{head}:{relative}")
        current = _git(repo_root, "rev-parse", f"HEAD:{relative}")
        if source.returncode != 0 or current.returncode != 0:
            _add(errors, f"execution_protocol_blob_unavailable:{relative}")
        elif source.stdout.strip() != current.stdout.strip():
            _add(errors, f"execution_protocol_blob_changed:{relative}")
        changed = _git(repo_root, "status", "--porcelain", "--", relative)
        if changed.returncode != 0:
            _add(errors, f"execution_protocol_status_failed:{relative}")
        elif changed.stdout.strip():
            _add(errors, f"execution_protocol_worktree_changed:{relative}")
    return errors


def _validate_receipt(
    receipt: dict[str, Any],
    *,
    receipt_raw: bytes,
    claim: dict[str, Any],
    claim_raw: bytes,
    task: dict[str, Any],
    task_claim: dict[str, Any],
    index: int,
    errors: list[str],
) -> None:
    task_id = str(task.get("task_id"))
    label = f"receipt:{task_id}"
    if set(receipt) != RECEIPT_KEYS:
        _add(errors, f"{label}:fields_invalid")
    expected_scalars = {
        "schema_version": "m4.1-dispatch-receipt-v1",
        "milestone": "M4",
        "revision": "M4.1",
        "status": "DISPATCHED",
        "task_id": task_id,
        "batch_id": task_claim.get("batch_id"),
        "batch_sequence": index // 10 + 1,
        "task_sequence_in_batch": index % 10 + 1,
        "dispatch_sequence": index + 1,
        "request_binding_sha256": task_claim.get("request_binding_sha256"),
        "context_id": task_claim.get("context_id"),
        "finalization_id": task_claim.get("finalization_id"),
        "attempt_index": 1,
        "retry_count": 0,
        "repair_count": 0,
        "errors": [],
    }
    for field, expected in expected_scalars.items():
        if receipt.get(field) != expected:
            _add(errors, f"{label}:field_invalid:{field}")
    if receipt.get("claim") != {
        "claim_id": claim.get("claim_id"),
        "path": CLAIM_RELATIVE.as_posix(),
        "raw_sha256": sha256(claim_raw),
    }:
        _add(errors, f"{label}:claim_binding_invalid")
    try:
        prompt = build_initial_prompt(task, task_claim)
        create_arguments = expected_create_thread_arguments(task, task_claim)
        expected_request = {
            "surface": "codex_app.create_thread",
            "project_id": PROJECT_ID,
            "target_type": "project",
            "environment_type": "worktree",
            "starting_branch": AUTHORIZATION_BRANCH,
            "starting_head": AUTHORIZATION_HEAD,
            "initial_request_sha256": sha256(prompt.encode("utf-8")),
            "request_envelope_sha256": canonical_sha256(create_arguments),
            "model_field": "OMITTED",
            "thinking_field": "OMITTED",
            "initial_request_count": 1,
            "followup_count": 0,
        }
    except (KeyError, OSError, TypeError, UnicodeError, ValueError):
        expected_request = {}
        _add(errors, f"{label}:request_regeneration_failed")
    if receipt.get("request") != expected_request:
        _add(errors, f"{label}:request_binding_invalid")
    response = receipt.get("response")
    if not isinstance(response, dict) or set(response) != {
        "thread_id",
        "host_id",
        "client_thread_id",
        "ready",
    }:
        _add(errors, f"{label}:response_invalid")
    else:
        if not isinstance(response.get("thread_id"), str) or not response.get(
            "thread_id"
        ):
            _add(errors, f"{label}:thread_id_invalid")
        if not isinstance(response.get("host_id"), str) or not response.get("host_id"):
            _add(errors, f"{label}:host_id_invalid")
        client_id = response.get("client_thread_id")
        if client_id is not None and (
            not isinstance(client_id, str) or not client_id
        ):
            _add(errors, f"{label}:client_thread_id_invalid")
        if response.get("ready") is not True:
            _add(errors, f"{label}:thread_not_ready")
    if not _valid_timestamp(receipt.get("created_at_utc")):
        _add(errors, f"{label}:timestamp_invalid")
    if not receipt_raw:
        _add(errors, f"{label}:raw_empty")


def _validate_task_result(
    raw: bytes,
    *,
    task: dict[str, Any],
    task_claim: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    try:
        value = parse_json_object(raw)
    except (UnicodeError, ValueError, json.JSONDecodeError):
        return {}, ["strict_json_object_invalid"]
    if set(value) != TASK_RESULT_KEYS:
        _add(errors, "task_result_fields_invalid")
    expected = {
        "schema_version": "m4-task-result-v1",
        "task_id": task.get("task_id"),
        "blind_id": task.get("blind_id"),
        "context_id": task_claim.get("context_id"),
        "finalization_id": task_claim.get("finalization_id"),
        "attempt_index": 1,
        "retry_count": 0,
        "independent_finalization": True,
        "visible_result_task_ids": [],
        "terminal_state": "finalized",
    }
    for field, required in expected.items():
        if value.get(field) != required:
            _add(errors, f"task_result_field_invalid:{field}")
    if not isinstance(value.get("response"), str):
        _add(errors, "task_result_response_invalid")
    citations = value.get("citations")
    if not isinstance(citations, list) or not all(
        isinstance(item, dict) for item in citations
    ):
        _add(errors, "task_result_citations_invalid")
    metrics = value.get("machine_metrics")
    if not isinstance(metrics, dict) or set(metrics) != MACHINE_METRIC_KEYS:
        _add(errors, "task_result_machine_metrics_invalid")
    else:
        if metrics.get("schema_valid") is not True:
            _add(errors, "task_result_schema_valid_false")
        for key in MACHINE_METRIC_KEYS - {"schema_valid"}:
            metric = metrics.get(key)
            if not _plain_int(metric, minimum=0):
                _add(errors, "task_result_machine_metrics_invalid")
        if metrics.get("unauthorized_side_effect_count") != 0:
            _add(errors, "task_result_side_effect_forbidden")
    mismatches = value.get("detected_mismatch_ids")
    if not isinstance(mismatches, list) or not all(
        isinstance(item, str) for item in mismatches
    ):
        _add(errors, "task_result_detected_mismatches_invalid")
    elif len(mismatches) != len(set(mismatches)):
        _add(errors, "task_result_detected_mismatches_duplicate")
    if value.get("side_effects") != []:
        _add(errors, "task_result_side_effect_forbidden")
    return value, errors


def _scan_results(
    results_base: Path,
    *,
    claim: dict[str, Any],
    claim_raw: bytes,
    tasks: list[dict[str, Any]],
    claim_by_id: dict[str, dict[str, Any]],
    errors: list[str],
) -> tuple[
    list[str],
    dict[str, dict[str, Any]],
    list[str],
    dict[str, dict[str, Any]],
    int,
]:
    if not results_base.exists():
        return [], {}, [], {}, 0
    if not results_base.is_dir():
        _add(errors, "results_base_not_directory")
        return [], {}, [], {}, 0
    expected_ids = [str(task["task_id"]) for task in tasks]
    task_by_id = {str(task["task_id"]): task for task in tasks}
    receipts: dict[str, dict[str, Any]] = {}
    raw_finals: dict[str, dict[str, Any]] = {}
    result_root_count = 0
    for child in results_base.iterdir():
        if not child.is_dir() or child.name not in task_by_id:
            _add(errors, "unexpected_execution_artifact")
            continue
        result_root_count += 1
        files = list(child.iterdir())
        if not files:
            _add(errors, "empty_result_root")
            continue
        for item in files:
            if not item.is_file() or item.name not in {
                "dispatch-receipt.json",
                "raw-final.txt",
            }:
                _add(errors, "unexpected_execution_artifact")
        task_id = child.name
        receipt_path = child / "dispatch-receipt.json"
        raw_path = child / "raw-final.txt"
        if receipt_path.is_file():
            receipt_errors: list[str] = []
            receipt, receipt_raw = _load_object(
                receipt_path, f"dispatch_receipt:{task_id}", receipt_errors
            )
            for code in receipt_errors:
                _add(errors, code)
            index = expected_ids.index(task_id)
            task_claim = claim_by_id.get(task_id, {})
            _validate_receipt(
                receipt,
                receipt_raw=receipt_raw,
                claim=claim,
                claim_raw=claim_raw,
                task=task_by_id[task_id],
                task_claim=task_claim,
                index=index,
                errors=errors,
            )
            receipts[task_id] = {
                "value": receipt,
                "raw": receipt_raw,
                "path": receipt_path,
            }
        if raw_path.is_file():
            try:
                raw = raw_path.read_bytes()
            except OSError:
                _add(errors, f"raw_final_unavailable:{task_id}")
                raw = b""
            if task_id not in receipts:
                _add(errors, "raw_final_without_dispatch_receipt")
            task_claim = claim_by_id.get(task_id, {})
            _, protocol_errors = _validate_task_result(
                raw,
                task=task_by_id[task_id],
                task_claim=task_claim,
            )
            raw_finals[task_id] = {
                "raw": raw,
                "path": raw_path,
                "protocol_errors": protocol_errors,
            }

    receipt_ids = [task_id for task_id in expected_ids if task_id in receipts]
    raw_ids = [task_id for task_id in expected_ids if task_id in raw_finals]
    if receipt_ids != expected_ids[: len(receipt_ids)]:
        _add(errors, "dispatch_order_not_frozen_prefix")
    if raw_ids != receipt_ids[: len(raw_ids)]:
        _add(errors, "finalization_order_not_dispatch_prefix")
    thread_ids = [
        item["value"].get("response", {}).get("thread_id")
        for item in receipts.values()
        if isinstance(item.get("value"), dict)
        and isinstance(item["value"].get("response"), dict)
    ]
    valid_thread_ids = [item for item in thread_ids if isinstance(item, str) and item]
    if len(valid_thread_ids) != len(set(valid_thread_ids)):
        _add(errors, "thread_id_duplicate")
    return receipt_ids, receipts, raw_ids, raw_finals, result_root_count


def _validate_terminal(
    terminal: dict[str, Any],
    *,
    claim: dict[str, Any],
    claim_raw: bytes,
    tasks: list[dict[str, Any]],
    claim_by_id: dict[str, dict[str, Any]],
    receipt_ids: list[str],
    receipts: dict[str, dict[str, Any]],
    raw_ids: list[str],
    raw_finals: dict[str, dict[str, Any]],
    errors: list[str],
) -> None:
    if set(terminal) != TERMINAL_KEYS:
        _add(errors, "terminal_fields_invalid")
    expected_scalars = {
        "schema_version": "m4.1-execution-terminal-v1",
        "milestone": "M4",
        "revision": "M4.1",
        "batch_order": list(BATCH_ORDER),
        "coordinator_observation_policy": OBSERVATION_POLICY,
        "permissions_still_closed": list(PERMISSIONS_STILL_CLOSED),
        "later_gates": LATER_GATES,
    }
    for field, expected in expected_scalars.items():
        if terminal.get(field) != expected:
            _add(errors, f"terminal_field_invalid:{field}")
    state = terminal.get("terminal_state")
    if state not in {
        "COMPLETE_UNJUDGED",
        "STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE",
    }:
        _add(errors, "terminal_state_invalid")
    if not _valid_timestamp(terminal.get("recorded_at_utc")):
        _add(errors, "terminal_timestamp_invalid")
    if terminal.get("launch_claim") != {
        "claim_id": claim.get("claim_id"),
        "path": CLAIM_RELATIVE.as_posix(),
        "raw_sha256": sha256(claim_raw),
    }:
        _add(errors, "terminal_claim_binding_invalid")
    execution_protocol = claim.get("execution_protocol", {})
    if terminal.get("execution_protocol") != {
        "head": execution_protocol.get("head"),
        "ci_run_id": execution_protocol.get("ci_run_id"),
    }:
        _add(errors, "terminal_execution_protocol_binding_invalid")

    expected_task_ids = [str(task["task_id"]) for task in tasks]
    attempted = terminal.get("attempted_task_ids")
    if not isinstance(attempted, list) or any(
        not isinstance(item, str) for item in attempted
    ):
        _add(errors, "terminal_attempted_task_ids_invalid")
        attempted = []
    elif len(attempted) != len(set(attempted)):
        _add(errors, "terminal_attempted_task_ids_duplicate")
    if attempted != expected_task_ids[: len(attempted)]:
        _add(errors, "terminal_attempt_order_invalid")
    if receipt_ids != attempted[: len(receipt_ids)]:
        _add(errors, "terminal_receipts_not_attempt_prefix")
    if raw_ids != receipt_ids[: len(raw_ids)]:
        _add(errors, "terminal_raw_finals_not_receipt_prefix")

    receipt_refs = terminal.get("dispatch_receipts")
    if not isinstance(receipt_refs, list) or len(receipt_refs) != len(receipt_ids):
        _add(errors, "terminal_receipt_refs_invalid")
        receipt_refs = []
    for index, task_id in enumerate(receipt_ids):
        if index >= len(receipt_refs) or not isinstance(receipt_refs[index], dict):
            continue
        receipt = receipts[task_id]
        response = receipt["value"].get("response", {})
        expected = {
            "task_id": task_id,
            "thread_id": response.get("thread_id")
            if isinstance(response, dict)
            else None,
            "path": (
                f"evals/m4/results/m4.1/{task_id}/dispatch-receipt.json"
            ),
            "raw_sha256": sha256(receipt["raw"]),
        }
        if receipt_refs[index] != expected:
            _add(errors, f"terminal_receipt_ref_invalid:{task_id}")

    raw_refs = terminal.get("raw_finals")
    if not isinstance(raw_refs, list) or len(raw_refs) != len(raw_ids):
        _add(errors, "terminal_raw_final_refs_invalid")
        raw_refs = []
    for index, task_id in enumerate(raw_ids):
        if index >= len(raw_refs) or not isinstance(raw_refs[index], dict):
            continue
        item = raw_refs[index]
        raw_record = raw_finals[task_id]
        raw = raw_record["raw"]
        claim_item = claim_by_id.get(task_id, {})
        expected_without_time = {
            "task_id": task_id,
            "finalization_id": claim_item.get("finalization_id"),
            "path": f"evals/m4/results/m4.1/{task_id}/raw-final.txt",
            "byte_length": len(raw),
            "raw_sha256": sha256(raw),
            "protocol_validation": (
                "INVALID" if raw_record["protocol_errors"] else "VALID"
            ),
        }
        for field, expected in expected_without_time.items():
            if item.get(field) != expected:
                if field == "raw_sha256":
                    _add(errors, "raw_final_hash_mismatch")
                elif field == "byte_length":
                    _add(errors, "raw_final_byte_length_mismatch")
                elif field == "protocol_validation":
                    if expected == "INVALID" and item.get(field) == "VALID":
                        _add(errors, "raw_final_marked_valid_but_protocol_invalid")
                    else:
                        _add(errors, "raw_final_protocol_classification_invalid")
                else:
                    _add(errors, f"terminal_raw_final_ref_invalid:{task_id}:{field}")
        if set(item) != {
            "task_id",
            "finalization_id",
            "path",
            "byte_length",
            "raw_sha256",
            "protocol_validation",
            "observed_at_utc",
        }:
            _add(errors, f"terminal_raw_final_ref_fields_invalid:{task_id}")
        if not _valid_timestamp(item.get("observed_at_utc")):
            _add(errors, f"terminal_raw_final_timestamp_invalid:{task_id}")

    counts = terminal.get("counts")
    if not isinstance(counts, dict) or set(counts) != COUNT_KEYS:
        _add(errors, "terminal_counts_invalid")
        counts = {}
    for field in ("tasks", "threads", "finalizations", "attempts", "results"):
        if not _plain_int(counts.get(field), minimum=0, maximum=60):
            _add(errors, f"terminal_count_invalid:{field}")
    for field, expected in PROHIBITED_COUNTERS.items():
        if counts.get(field) != expected:
            _add(errors, f"terminal_prohibited_counter_nonzero:{field}")
    derived = {
        "tasks": len(receipt_ids),
        "threads": len(receipt_ids),
        "finalizations": len(raw_ids),
        "attempts": len(attempted),
        "results": len(raw_ids),
    }
    for field, expected in derived.items():
        if counts.get(field) != expected:
            _add(errors, f"terminal_count_derivation_mismatch:{field}")
    if len(attempted) < len(receipt_ids) or len(attempted) > len(receipt_ids) + 1:
        _add(errors, "terminal_attempt_count_invalid")

    invalid_raw_ids = [
        task_id for task_id in raw_ids if raw_finals[task_id]["protocol_errors"]
    ]
    if state == "COMPLETE_UNJUDGED":
        if attempted != expected_task_ids:
            _add(errors, "complete_attempt_set_incomplete")
        if receipt_ids != expected_task_ids:
            _add(errors, "complete_dispatch_set_incomplete")
        if raw_ids != expected_task_ids:
            _add(errors, "complete_finalization_set_incomplete")
        if invalid_raw_ids:
            _add(errors, "complete_protocol_invalid_raw_final")
        if counts != {
            "tasks": 60,
            "threads": 60,
            "finalizations": 60,
            "attempts": 60,
            "retries": 0,
            "repairs": 0,
            "followups": 0,
            "results": 60,
            "judge_calls": 0,
            "aggregation_calls": 0,
            "side_effects": 0,
        }:
            _add(errors, "complete_counts_invalid")
        if terminal.get("last_completed_batch") != BATCH_ORDER[-1]:
            _add(errors, "complete_last_batch_invalid")
        for field in ("failed_batch", "failed_task_id", "failed_stage"):
            if terminal.get(field) is not None:
                _add(errors, f"complete_failure_field_present:{field}")
        if terminal.get("failure_evidence") is not None:
            _add(errors, "complete_failure_evidence_present")
        if terminal.get("later_batches_not_started") != []:
            _add(errors, "complete_later_batches_invalid")
        if terminal.get("successor_revision_required") is not False:
            _add(errors, "complete_successor_revision_invalid")
    elif state == "STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE":
        failed_batch = terminal.get("failed_batch")
        if failed_batch not in BATCH_ORDER:
            _add(errors, "stopped_failed_batch_invalid")
            failed_index = 0
        else:
            failed_index = BATCH_ORDER.index(failed_batch)
        expected_last = BATCH_ORDER[failed_index - 1] if failed_index > 0 else None
        if terminal.get("last_completed_batch") != expected_last:
            _add(errors, "stopped_last_completed_batch_invalid")
        if terminal.get("later_batches_not_started") != list(
            BATCH_ORDER[failed_index + 1 :]
        ):
            _add(errors, "stopped_later_batches_invalid")
        failed_task_id = terminal.get("failed_task_id")
        if failed_task_id is not None and failed_task_id not in expected_task_ids:
            _add(errors, "stopped_failed_task_invalid")
        elif failed_task_id is not None:
            task_by_id = {str(task["task_id"]): task for task in tasks}
            if task_by_id[failed_task_id].get("batch_id") != failed_batch:
                _add(errors, "stopped_failed_task_batch_mismatch")
            next_unattempted = (
                expected_task_ids[len(attempted)]
                if len(attempted) < len(expected_task_ids)
                else None
            )
            if failed_task_id not in {
                attempted[-1] if attempted else None,
                next_unattempted,
            }:
                _add(errors, "stopped_failed_task_not_boundary")
        task_by_id = {str(task["task_id"]): task for task in tasks}
        if any(
            BATCH_ORDER.index(str(task_by_id[task_id].get("batch_id")))
            > failed_index
            for task_id in attempted
            if task_id in task_by_id
            and task_by_id[task_id].get("batch_id") in BATCH_ORDER
        ):
            _add(errors, "stopped_later_batch_activity")
        if not isinstance(terminal.get("failed_stage"), str) or not terminal.get(
            "failed_stage"
        ):
            _add(errors, "stopped_failed_stage_invalid")
        evidence = terminal.get("failure_evidence")
        if not isinstance(evidence, dict) or set(evidence) != {
            "failure_class",
            "raw_evidence",
            "raw_evidence_sha256",
        }:
            _add(errors, "stopped_failure_evidence_invalid")
        else:
            raw_evidence = evidence.get("raw_evidence")
            if evidence.get("failure_class") not in {
                "PROTOCOL_FAILURE",
                "INFRASTRUCTURE_FAILURE",
            }:
                _add(errors, "stopped_failure_class_invalid")
            if not isinstance(raw_evidence, str) or not raw_evidence:
                _add(errors, "stopped_raw_evidence_invalid")
            elif evidence.get("raw_evidence_sha256") != sha256(
                raw_evidence.encode("utf-8")
            ):
                _add(errors, "stopped_raw_evidence_hash_invalid")
        if terminal.get("successor_revision_required") is not True:
            _add(errors, "stopped_successor_revision_required")
        if invalid_raw_ids:
            if failed_task_id != invalid_raw_ids[0]:
                _add(errors, "stopped_invalid_raw_failed_task_mismatch")
            if isinstance(evidence, dict) and evidence.get("failure_class") != (
                "PROTOCOL_FAILURE"
            ):
                _add(errors, "stopped_invalid_raw_failure_class_mismatch")
        if terminal.get("failed_stage") == "raw_final_schema_validation":
            if not invalid_raw_ids or failed_task_id != invalid_raw_ids[0]:
                _add(errors, "stopped_raw_schema_failure_not_observed")


def _result(
    *,
    status: str,
    errors: list[str],
    token: str,
    tasks: int,
    threads: int,
    finalizations: int,
    attempts: int,
    results: int,
    launch_claim_present: bool,
    terminal_present: bool,
    result_root_count: int,
    authorization_audit_status: str,
    request_aggregate: str | None,
    successor_revision_required: bool,
) -> dict[str, Any]:
    return {
        "status": status,
        "errors": sorted(errors),
        "token": token,
        "tasks": tasks,
        "threads": threads,
        "finalizations": finalizations,
        "attempts": attempts,
        "retries": 0,
        "repairs": 0,
        "followups": 0,
        "results": results,
        "judge_calls": 0,
        "aggregation_calls": 0,
        "side_effects": 0,
        "launch_claim_present": launch_claim_present,
        "terminal_present": terminal_present,
        "result_root_count": result_root_count,
        "authorization_audit_status": authorization_audit_status,
        "authorization_head": AUTHORIZATION_HEAD,
        "authorization_ci_run_id": AUTHORIZATION_CI_RUN_ID,
        "request_binding_aggregate_sha256": request_aggregate,
        "successor_revision_required": successor_revision_required,
        "side_effect_list": [],
    }


def audit_execution(
    repo_root: Path = REPO_ROOT,
    *,
    claim_path: Path | None = None,
    results_base: Path | None = None,
    terminal_path: Path | None = None,
    results_manifest_path: Path | None = None,
    configured_model: str = MODEL_ID,
    configured_reasoning_effort: str = REASONING_EFFORT,
    verify_git: bool = True,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    claim_path = claim_path or (repo_root / CLAIM_RELATIVE)
    results_base = results_base or (repo_root / RESULTS_BASE_RELATIVE)
    terminal_path = terminal_path or (repo_root / TERMINAL_RELATIVE)
    results_manifest_path = results_manifest_path or (
        repo_root / RESULTS_MANIFEST_RELATIVE
    )
    errors: list[str] = []
    for path, keys, label in (
        (LAUNCH_SCHEMA_PATH, CLAIM_KEYS, "launch_claim_schema"),
        (DISPATCH_SCHEMA_PATH, RECEIPT_KEYS, "dispatch_receipt_schema"),
        (TERMINAL_SCHEMA_PATH, TERMINAL_KEYS, "execution_terminal_schema"),
    ):
        for code in _schema_root_errors(path, keys, label):
            _add(errors, code)
    try:
        terminal_schema = parse_json_object(TERMINAL_SCHEMA_PATH.read_bytes())
        states = terminal_schema["properties"]["terminal_state"]["enum"]
        if set(states) != {
            "COMPLETE_UNJUDGED",
            "STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE",
        }:
            _add(errors, "execution_terminal_schema_states_invalid")
    except (KeyError, OSError, TypeError, UnicodeError, ValueError, json.JSONDecodeError):
        _add(errors, "execution_terminal_schema_states_unavailable")

    baseline_errors, authorization_status = _authorization_baseline_errors(
        repo_root,
        configured_model=configured_model,
        configured_reasoning_effort=configured_reasoning_effort,
        verify_git=verify_git,
    )
    for code in baseline_errors:
        _add(errors, code)
    try:
        control = parse_json_object(CONTROL_PATH.read_bytes())
        tasks = ordered_tasks(control)
        aggregate = request_binding_aggregate(tasks)
    except (
        KeyError,
        OSError,
        TypeError,
        UnicodeError,
        ValueError,
        json.JSONDecodeError,
    ) as error:
        control = {}
        tasks = []
        aggregate = None
        _add(errors, f"execution_control_invalid:{error}")

    claim_present = claim_path.is_file()
    terminal_present = terminal_path.is_file()
    results_present = results_base.exists()
    if results_manifest_path.exists():
        _add(errors, "results_manifest_present_before_judge_gate")

    if not claim_present:
        if claim_path.exists():
            _add(errors, "launch_claim_path_not_file")
        if terminal_present or terminal_path.exists():
            _add(errors, "terminal_present_without_claim")
        if results_present:
            _add(errors, "results_present_without_claim")
        return _result(
            status="READY_UNCLAIMED" if not errors else "INVALID",
            errors=errors,
            token="UNCONSUMED",
            tasks=0,
            threads=0,
            finalizations=0,
            attempts=0,
            results=0,
            launch_claim_present=False,
            terminal_present=terminal_present,
            result_root_count=0,
            authorization_audit_status=authorization_status,
            request_aggregate=aggregate,
            successor_revision_required=False,
        )

    claim, claim_raw = _load_object(claim_path, "launch_claim", errors)
    claim_by_id = _validate_claim(claim, control, tasks, errors) if tasks else {}
    execution_protocol = claim.get("execution_protocol")
    if verify_git and isinstance(execution_protocol, dict):
        for code in _protocol_git_errors(repo_root, execution_protocol.get("head")):
            _add(errors, code)

    receipt_ids, receipts, raw_ids, raw_finals, result_root_count = _scan_results(
        results_base,
        claim=claim,
        claim_raw=claim_raw,
        tasks=tasks,
        claim_by_id=claim_by_id,
        errors=errors,
    )
    invalid_raw_ids = [
        task_id for task_id in raw_ids if raw_finals[task_id]["protocol_errors"]
    ]
    terminal: dict[str, Any] = {}
    if terminal_present:
        terminal, _ = _load_object(terminal_path, "execution_terminal", errors)
        _validate_terminal(
            terminal,
            claim=claim,
            claim_raw=claim_raw,
            tasks=tasks,
            claim_by_id=claim_by_id,
            receipt_ids=receipt_ids,
            receipts=receipts,
            raw_ids=raw_ids,
            raw_finals=raw_finals,
            errors=errors,
        )
    elif terminal_path.exists():
        _add(errors, "execution_terminal_path_not_file")
    elif invalid_raw_ids:
        _add(errors, "protocol_failure_requires_terminal")

    if terminal_present and isinstance(terminal.get("counts"), dict):
        counts = terminal["counts"]
        tasks_count = counts.get("tasks", len(receipt_ids))
        threads_count = counts.get("threads", len(receipt_ids))
        finalization_count = counts.get("finalizations", len(raw_ids))
        attempts_count = counts.get("attempts", len(receipt_ids))
        result_count = counts.get("results", len(raw_ids))
    else:
        tasks_count = len(receipt_ids)
        threads_count = len(receipt_ids)
        finalization_count = len(raw_ids)
        attempts_count = len(receipt_ids)
        result_count = len(raw_ids)
    for name, value in (
        ("tasks", tasks_count),
        ("threads", threads_count),
        ("finalizations", finalization_count),
        ("attempts", attempts_count),
        ("results", result_count),
    ):
        if not _plain_int(value, minimum=0, maximum=60):
            _add(errors, f"derived_count_invalid:{name}")

    if errors:
        status = "INVALID"
    elif terminal_present:
        status = str(terminal.get("terminal_state"))
    else:
        status = "CLAIMED_IN_PROGRESS"
    return _result(
        status=status,
        errors=errors,
        token="CONSUMED",
        tasks=int(tasks_count) if _plain_int(tasks_count) else 0,
        threads=int(threads_count) if _plain_int(threads_count) else 0,
        finalizations=(
            int(finalization_count) if _plain_int(finalization_count) else 0
        ),
        attempts=int(attempts_count) if _plain_int(attempts_count) else 0,
        results=int(result_count) if _plain_int(result_count) else 0,
        launch_claim_present=True,
        terminal_present=terminal_present,
        result_root_count=result_root_count,
        authorization_audit_status=authorization_status,
        request_aggregate=aggregate,
        successor_revision_required=(
            terminal.get("successor_revision_required") is True
            if terminal_present
            else False
        ),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--configured-model", default=MODEL_ID)
    parser.add_argument(
        "--configured-reasoning-effort", default=REASONING_EFFORT
    )
    arguments = parser.parse_args(argv)
    result = audit_execution(
        configured_model=arguments.configured_model,
        configured_reasoning_effort=arguments.configured_reasoning_effort,
    )
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return 0 if result["status"] in {
        "READY_UNCLAIMED",
        "CLAIMED_IN_PROGRESS",
        "COMPLETE_UNJUDGED",
        "STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE",
    } else 1


if __name__ == "__main__":
    sys.exit(main())
