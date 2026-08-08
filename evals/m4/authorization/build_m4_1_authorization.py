#!/usr/bin/env python3
"""Build deterministic, unconsumed M4.1 Gate IV authorization artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping


REPO_ROOT = Path(__file__).resolve().parents[3]
M4_ROOT = REPO_ROOT / "evals" / "m4"
AUTHORIZATION_ROOT = M4_ROOT / "authorization"
M4_1_ROOT = AUTHORIZATION_ROOT / "m4.1"
PREPARATION_RELATIVE = "evals/m4/revisions/m4.1/preparation-manifest.json"
PREPARATION_PATH = REPO_ROOT / PREPARATION_RELATIVE
BASE_PREPARATION_RELATIVE = "evals/m4/preparation-manifest.json"
BASE_PREPARATION_PATH = REPO_ROOT / BASE_PREPARATION_RELATIVE
REVIEW_RELATIVE = "evals/m4/authorization/m4.1/gate-iv-review.json"
REVIEW_PATH = REPO_ROOT / REVIEW_RELATIVE
AUTHORIZATION_RELATIVE = "evals/m4/authorization/m4.1/execution-authorization.json"
AUTHORIZATION_PATH = REPO_ROOT / AUTHORIZATION_RELATIVE
CONTROL_RELATIVE = "evals/m4/authorization/m4.1/execution-control.json"
CONTROL_PATH = REPO_ROOT / CONTROL_RELATIVE
AUTHORIZATION_SCHEMA_RELATIVE = (
    "evals/m4/authorization/m4.1/execution-authorization.schema.json"
)
AUTHORIZATION_SCHEMA_PATH = REPO_ROOT / AUTHORIZATION_SCHEMA_RELATIVE
CONTROL_SCHEMA_RELATIVE = (
    "evals/m4/authorization/m4.1/execution-control.schema.json"
)
CONTROL_SCHEMA_PATH = REPO_ROOT / CONTROL_SCHEMA_RELATIVE
M4_0_AUTHORIZATION_PATH = AUTHORIZATION_ROOT / "execution-authorization.json"

PREPARATION_HEAD = "fedc5cdeebd7a2943afeb6767d39841305c55444"
PREPARATION_CI_RUN_ID = 31248424046
PREPARATION_CI_CONCLUSION = "success"
REVIEW_HEAD = "4fe3785ffd4db9cbf966d8c7ec1451079717da24"
REVIEW_RAW_SHA256 = (
    "5eb1279ae08c8d8fd8f0f7feb0f3207607b8b8c4cbad7155c844bff6fb4aa3b0"
)
REVIEW_BLOB_OID = "e38f3fc2305efefb070e3be20413c55156e8b186"
SCHEMA_HEAD = "5d781ea352e67ab44631844c37cf9b6552cfce77"
AUTHORIZATION_SCHEMA_RAW_SHA256 = (
    "af5d578dfd2f559453f2b86269a90e57cfcb4aeaee3736a2d12ee54f61ce47c0"
)
AUTHORIZATION_SCHEMA_BLOB_OID = "cc20e968e94135a3e94d8807c302b558f512b446"
CONTROL_SCHEMA_RAW_SHA256 = (
    "c2d8c2737adaf45f51ddde363d613b131b67cea50de7a12ed4d9f5a94292e000"
)
CONTROL_SCHEMA_BLOB_OID = "3ff5a850989c519624264935ba0267c27b6bfdc6"
REVISION = "M4.1"
MODEL_ID = "gpt-5.6-sol"
REASONING_EFFORT = "max"
PROJECT_ID = "ff35b25f-4644-41c8-9073-74c697559439"
PROJECT_LABEL = "engineering-research-copilot"
AUTHORIZATION_BRANCH = (
    "codex/m4-cross-engineering-forward-evaluation-m4.1-one-shot-authorization"
)
OFFICIAL_MODEL_REFERENCE = "https://developers.openai.com/api/docs/models/gpt-5.6-sol"
MODEL_CONTEXT_WINDOW_TOKENS = 1_050_000
MODEL_MAX_OUTPUT_TOKENS = 128_000
HELPER_RELATIVE = "evals/m4/execution/prepare_m4_1_request_bundles.ps1"
LAUNCH_CLAIM_RELATIVE = "evals/m4/execution/m4.1/launch-claim.json"
RESULTS_MANIFEST_RELATIVE = "evals/m4/results-manifest.json"
RESULTS_PARENT_RELATIVE = "evals/m4/results"
RESULT_ROOT_PREFIX = "evals/m4/results/m4.1"
OLD_AUTHORIZATION_TOKEN = (
    "sha256:09c940955104f2ae9278b55d155bc43a47d43a0eb9e80e4f90d7425eb3c0e292"
)

COUNTER_NAMES = (
    "authorized_tasks",
    "created_contexts",
    "dispatched_tasks",
    "finalizations",
    "results_observed",
    "judge_scores",
    "retries",
    "repairs",
    "unauthorized_side_effects",
)
ZERO_COUNTERS = {name: 0 for name in COUNTER_NAMES}

AUTHORIZATION_KEYS = frozenset(
    {
        "schema_version",
        "milestone",
        "revision",
        "status",
        "preparation_baseline",
        "review",
        "execution_helper",
        "model_binding",
        "execution_surface",
        "authority",
        "batch_policy",
        "prelaunch_counters",
        "consumption",
        "does_not_authorize",
        "authorization_token",
    }
)
CONTROL_KEYS = frozenset(
    {
        "schema_version",
        "milestone",
        "revision",
        "status",
        "authorization",
        "preparation",
        "execution_helper",
        "task_protocol",
        "request_policy",
        "execution_constraints",
        "batch_order",
        "batches",
        "tasks",
        "launch_claim",
        "permissions",
        "prelaunch_counters",
        "does_not_authorize",
    }
)

DOES_NOT_AUTHORIZE = [
    "a second attempt for any M4.1 task ID",
    "a retry, repair, continuation, or follow-up message",
    "a task outside the frozen 60-task M4.1 matrix",
    "cross-task or cross-arm result visibility",
    "judge execution, blind-map access, or unblinding",
    "result aggregation or acceptance-threshold claims",
    "changes to cases, prompts, variants, rubric, thresholds, or randomization",
    "M4 closure, M5, an experiment, simulation, training run, deployment, or control action",
]

FROZEN_PATHS = (
    "evals/m3",
    "skills/engineering-research-copilot",
    "evals/m4/cases",
    "evals/m4/variants",
    "evals/m4/schemas",
    "evals/m4/preparation-manifest.json",
    "evals/m4/build_preparation.py",
    "evals/m4/audit_preparation.py",
    "evals/m4/audit_results.py",
    "evals/m4/task-protocol.md",
    "evals/m4/judge-rubric.json",
    "evals/m4/acceptance-thresholds.json",
    "evals/m4/authorization/execution-authorization.json",
    "evals/m4/authorization/execution-control.json",
    "evals/m4/authorization/gate-iv-review.json",
    "evals/m4/execution/m4.0",
    PREPARATION_RELATIVE,
    "evals/m4/build_m4_1_preparation.py",
    "evals/m4/audit_m4_1_preparation.py",
    HELPER_RELATIVE,
    "evals/m4/revisions/m4.1/preparation-manifest.schema.json",
    "tests/test_m4_1_preparation.py",
)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def json_bytes(value: object) -> bytes:
    return canonical_bytes(value) + b"\n"


def authorization_token(payload: Mapping[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("authorization_token", None)
    return "sha256:" + sha256(canonical_bytes(unsigned))


def parse_json_object(raw: bytes) -> dict[str, Any]:
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ValueError("utf8_bom_forbidden")
    value = json.loads(raw.decode("utf-8", errors="strict"))
    if not isinstance(value, dict):
        raise ValueError("json_object_required")
    return value


def _git_output(*arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        check=False,
    )
    if completed.returncode != 0:
        raise ValueError(f"git_command_failed:{arguments[0]}")
    return completed.stdout.strip()


def git_blob_oid(head: str, relative: str) -> str:
    return _git_output("rev-parse", f"{head}:{relative}")


def _assert_commit_ancestor(commit: str, label: str) -> None:
    available = subprocess.run(
        ["git", "cat-file", "-e", f"{commit}^{{commit}}"],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
    )
    if available.returncode != 0:
        raise ValueError(f"{label}_unavailable")
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, "HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
    )
    if ancestor.returncode != 0:
        raise ValueError(f"{label}_not_ancestor")


def _assert_path_snapshot(
    *,
    source_head: str,
    relative: str,
    expected_blob: str,
    expected_raw_sha256: str,
    label: str,
) -> None:
    if git_blob_oid(source_head, relative) != expected_blob:
        raise ValueError(f"{label}_source_blob_mismatch")
    if git_blob_oid("HEAD", relative) != expected_blob:
        raise ValueError(f"{label}_head_blob_mismatch")
    try:
        raw = (REPO_ROOT / relative).read_bytes()
    except OSError as error:
        raise ValueError(f"{label}_worktree_unavailable") from error
    if sha256(raw) != expected_raw_sha256:
        raise ValueError(f"{label}_raw_sha256_mismatch")
    committed_diff = _git_output(
        "diff", "--name-only", source_head, "HEAD", "--", relative
    )
    worktree_diff = _git_output("diff", "--name-only", "--", relative)
    index_diff = _git_output("diff", "--cached", "--name-only", "--", relative)
    if committed_diff or worktree_diff or index_diff:
        raise ValueError(f"{label}_diff_present")


def _assert_review_and_schema_snapshots() -> None:
    _assert_commit_ancestor(REVIEW_HEAD, "review_head")
    _assert_path_snapshot(
        source_head=REVIEW_HEAD,
        relative=REVIEW_RELATIVE,
        expected_blob=REVIEW_BLOB_OID,
        expected_raw_sha256=REVIEW_RAW_SHA256,
        label="review",
    )
    _assert_commit_ancestor(SCHEMA_HEAD, "schema_head")
    for relative, expected_blob, expected_raw, label in (
        (
            AUTHORIZATION_SCHEMA_RELATIVE,
            AUTHORIZATION_SCHEMA_BLOB_OID,
            AUTHORIZATION_SCHEMA_RAW_SHA256,
            "authorization_schema",
        ),
        (
            CONTROL_SCHEMA_RELATIVE,
            CONTROL_SCHEMA_BLOB_OID,
            CONTROL_SCHEMA_RAW_SHA256,
            "control_schema",
        ),
    ):
        _assert_path_snapshot(
            source_head=SCHEMA_HEAD,
            relative=relative,
            expected_blob=expected_blob,
            expected_raw_sha256=expected_raw,
            label=label,
        )


def request_binding_sha256(task: Mapping[str, object]) -> str:
    fields = (
        "m4.1-request-binding-v1",
        str(task["task_id"]),
        str(task["source_task_id"]),
        str(task["blind_id"]),
        str(task["case_sha256"]),
        str(task["user_input_sha256"]),
        str(task["task_protocol_sha256"]),
        str(task["variant_instruction_sha256"] or "NONE"),
        str(task["rubric_sha256"]),
        str(task["execution_constraints_sha256"]),
    )
    return sha256(("\n".join(fields) + "\n").encode("utf-8"))


def _assert_git_baseline() -> None:
    _assert_commit_ancestor(PREPARATION_HEAD, "preparation_head")
    changed = _git_output("diff", "--name-only", PREPARATION_HEAD, "--", *FROZEN_PATHS)
    if changed:
        raise ValueError("frozen_preparation_paths_changed:" + changed.replace("\n", ","))
    _assert_review_and_schema_snapshots()


def _require_file_hash(relative: str, expected: object, error: str) -> bytes:
    path = REPO_ROOT / relative
    raw = path.read_bytes()
    if sha256(raw) != expected:
        raise ValueError(error)
    return raw


def _preparation_values(preparation: dict[str, Any]) -> dict[str, Any]:
    if preparation.get("schema_version") != "m4.1-successor-preparation-v1":
        raise ValueError("preparation_schema_invalid")
    if preparation.get("revision") != REVISION or preparation.get("status") != "PREPARATION_ONLY":
        raise ValueError("preparation_state_invalid")
    matrix = preparation.get("matrix")
    authority = preparation.get("authority")
    randomization = preparation.get("randomization")
    helper = preparation.get("execution_helper")
    counters = preparation.get("counters")
    tasks = preparation.get("tasks")
    base_reference = preparation.get("base_preparation")
    if not all(
        isinstance(value, dict)
        for value in (matrix, authority, randomization, helper, counters, base_reference)
    ) or not isinstance(tasks, list):
        raise ValueError("preparation_shape_invalid")
    batches = matrix.get("batches")
    if not isinstance(batches, list):
        raise ValueError("preparation_batches_invalid")

    task_ids = [task.get("task_id") for task in tasks if isinstance(task, dict)]
    source_task_ids = [task.get("source_task_id") for task in tasks if isinstance(task, dict)]
    blind_ids = [task.get("blind_id") for task in tasks if isinstance(task, dict)]
    batch_ids = [batch.get("batch_id") for batch in batches if isinstance(batch, dict)]
    errors: list[str] = []
    if any(matrix.get(key) != expected for key, expected in {
        "case_count": 12,
        "arm_count": 5,
        "planned_task_count": 60,
        "batch_count": 6,
    }.items()):
        errors.append("preparation_matrix_invalid")
    if len(tasks) != 60 or len(task_ids) != 60 or len(set(task_ids)) != 60:
        errors.append("preparation_task_ids_invalid")
    if len(source_task_ids) != 60 or len(set(source_task_ids)) != 60:
        errors.append("preparation_source_task_ids_invalid")
    if any(not isinstance(value, str) or not value.startswith("M4.1-") for value in task_ids):
        errors.append("preparation_task_namespace_invalid")
    if set(task_ids) & set(source_task_ids):
        errors.append("preparation_task_ids_reused")
    if blind_ids != [f"M4-J{index:03d}" for index in range(61, 121)]:
        errors.append("preparation_blind_ids_invalid")
    if len(batches) != 6 or len(batch_ids) != 6 or len(set(batch_ids)) != 6:
        errors.append("preparation_batch_ids_invalid")
    if any(
        not isinstance(value, str) or not value.startswith("M4.1-BATCH-")
        for value in batch_ids
    ):
        errors.append("preparation_batch_namespace_invalid")
    if any(batch.get("planned_task_count") != 10 for batch in batches):
        errors.append("preparation_batch_size_invalid")
    if randomization.get("frozen") is not True or randomization.get("task_order") != task_ids:
        errors.append("preparation_task_order_invalid")
    if randomization.get("blind_mapping") != dict(zip(task_ids, blind_ids, strict=True)):
        errors.append("preparation_blind_mapping_invalid")
    if randomization.get("judge_mapping_access_authorized") is not False:
        errors.append("preparation_blind_authority_invalid")
    for key in (
        "fresh_execution_authorized",
        "fresh_tasks_authorized",
        "result_writes_authorized",
        "retry_authorized",
        "repair_authorized",
    ):
        if authority.get(key) is not False:
            errors.append(f"preparation_authority_invalid:{key}")
    if counters != ZERO_COUNTERS:
        errors.append("preparation_counters_nonzero")
    if helper.get("path") != HELPER_RELATIVE or helper.get("request_binding_count") != 60:
        errors.append("execution_helper_reference_invalid")

    base_raw = _require_file_hash(
        BASE_PREPARATION_RELATIVE,
        base_reference.get("raw_sha256"),
        "base_preparation_hash_mismatch",
    )
    if base_reference.get("git_blob_oid") != git_blob_oid(
        str(base_reference.get("head")), BASE_PREPARATION_RELATIVE
    ):
        errors.append("base_preparation_blob_mismatch")
    helper_raw = _require_file_hash(
        HELPER_RELATIVE, helper.get("raw_sha256"), "execution_helper_hash_mismatch"
    )
    if git_blob_oid(PREPARATION_HEAD, HELPER_RELATIVE) != git_blob_oid("HEAD", HELPER_RELATIVE):
        errors.append("execution_helper_blob_changed")

    base = parse_json_object(base_raw)
    constraints = base.get("execution_constraints")
    artifacts = base.get("artifacts")
    if not isinstance(constraints, dict) or not isinstance(artifacts, dict):
        errors.append("base_preparation_shape_invalid")
        constraints = {}
        artifacts = {}
    constraints_hash = sha256(canonical_bytes(constraints))
    protocol_hash = artifacts.get("evals/m4/task-protocol.md", {}).get("sha256")
    rubric_hash = artifacts.get("evals/m4/judge-rubric.json", {}).get("sha256")

    for task in tasks:
        if not isinstance(task, dict):
            errors.append("prepared_task_invalid")
            continue
        task_id = task.get("task_id")
        expected_root = f"{RESULT_ROOT_PREFIX}/{task_id}"
        if (
            task.get("result_root") != expected_root
            or task.get("result_root_must_be_absent") is not True
        ):
            errors.append("prepared_result_root_invalid")
        if task.get("request_binding_sha256") != request_binding_sha256(task):
            errors.append("request_binding_mismatch")
        if task.get("execution_constraints_sha256") != constraints_hash:
            errors.append("execution_constraints_hash_mismatch")
        if (
            task.get("task_protocol_sha256") != protocol_hash
            or task.get("rubric_sha256") != rubric_hash
        ):
            errors.append("shared_artifact_hash_mismatch")
        case_path = task.get("case_path")
        if not isinstance(case_path, str):
            errors.append("case_path_invalid")
            continue
        try:
            case_raw = _require_file_hash(case_path, task.get("case_sha256"), "case_hash_mismatch")
            case = parse_json_object(case_raw)
            user_input = case.get("user_input")
            if not isinstance(user_input, str) or sha256(
                user_input.encode("utf-8")
            ) != task.get("user_input_sha256"):
                errors.append("user_input_hash_mismatch")
        except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as error:
            errors.append(str(error))
        variant_path = task.get("variant_instruction_path")
        variant_hash = task.get("variant_instruction_sha256")
        if variant_path is None:
            if variant_hash is not None:
                errors.append("variant_hash_without_path")
        elif not isinstance(variant_path, str):
            errors.append("variant_path_invalid")
        else:
            try:
                _require_file_hash(variant_path, variant_hash, "variant_hash_mismatch")
            except OSError:
                errors.append("variant_unavailable")

    if (REPO_ROOT / RESULTS_PARENT_RELATIVE).exists():
        errors.append("results_parent_present_before_launch")
    if (REPO_ROOT / RESULTS_MANIFEST_RELATIVE).exists():
        errors.append("results_manifest_present_before_launch")
    if (REPO_ROOT / LAUNCH_CLAIM_RELATIVE).exists():
        errors.append("authorization_already_claimed")
    if errors:
        raise ValueError(";".join(sorted(set(errors))))
    return {
        "matrix": matrix,
        "batches": batches,
        "tasks": tasks,
        "task_ids": task_ids,
        "blind_ids": blind_ids,
        "batch_ids": batch_ids,
        "helper": helper,
        "helper_raw": helper_raw,
        "base": base,
        "constraints": constraints,
        "artifacts": artifacts,
    }


def validate_review(
    review: Mapping[str, object],
    preparation: Mapping[str, object],
    review_raw: bytes | None = None,
) -> None:
    if review_raw is not None and sha256(review_raw) != REVIEW_RAW_SHA256:
        raise ValueError("review_raw_sha256_mismatch")
    if review.get("schema_version") != "m4.1-gate-iv-independent-review-v1":
        raise ValueError("review_schema_invalid")
    if review.get("status") != "PASSED":
        raise ValueError("review_status_invalid")
    if review.get("findings") != []:
        raise ValueError("review_findings_nonempty")
    if review.get("decision") != "AUTHORIZE_M4_1_GATE_IV_ONE_SHOT_MATRIX":
        raise ValueError("review_decision_invalid")
    if review.get("preparation_head") != PREPARATION_HEAD:
        raise ValueError("review_preparation_head_invalid")
    if review.get("preparation_ci_run_id") != PREPARATION_CI_RUN_ID:
        raise ValueError("review_preparation_ci_invalid")
    if review.get("preparation_ci_conclusion") != PREPARATION_CI_CONCLUSION:
        raise ValueError("review_preparation_ci_invalid")
    reviewed_manifest = review.get("reviewed_manifest")
    reviewed_helper = review.get("reviewed_helper")
    checks = review.get("checks")
    if not all(
        isinstance(value, Mapping)
        for value in (reviewed_manifest, reviewed_helper, checks)
    ):
        raise ValueError("review_shape_invalid")
    manifest_raw = PREPARATION_PATH.read_bytes()
    if dict(reviewed_manifest) != {
        "path": PREPARATION_RELATIVE,
        "git_blob_oid": git_blob_oid(PREPARATION_HEAD, PREPARATION_RELATIVE),
        "raw_sha256": sha256(manifest_raw),
    }:
        raise ValueError("review_manifest_binding_invalid")
    helper = preparation.get("execution_helper")
    if not isinstance(helper, Mapping) or dict(reviewed_helper) != {
        "path": HELPER_RELATIVE,
        "git_blob_oid": git_blob_oid(PREPARATION_HEAD, HELPER_RELATIVE),
        "raw_sha256": helper.get("raw_sha256"),
    }:
        raise ValueError("review_helper_binding_invalid")
    configured = checks.get("configured_defaults")
    matrix = checks.get("m4_1_matrix")
    zero_state = checks.get("zero_state")
    later_gates = checks.get("later_gates")
    if not isinstance(configured, Mapping) or dict(configured) != {
        "matched": True,
        "model": MODEL_ID,
        "reasoning_effort": REASONING_EFFORT,
    }:
        raise ValueError("review_configured_defaults_invalid")
    if not isinstance(matrix, Mapping) or any(
        matrix.get(key) != expected
        for key, expected in {
            "cases": 12,
            "arms": 5,
            "tasks": 60,
            "batches": 6,
            "new_task_ids": 60,
            "relative_order_inherited": True,
        }.items()
    ):
        raise ValueError("review_matrix_invalid")
    if not isinstance(zero_state, Mapping) or any(
        zero_state.get(key) != expected
        for key, expected in {
            "all_counters_zero": True,
            "m4_1_launch_claim_present": False,
            "global_results_manifest_present": False,
            "result_roots_present": 0,
        }.items()
    ):
        raise ValueError("review_zero_state_invalid")
    if not isinstance(later_gates, Mapping) or any(
        value is not False for value in later_gates.values()
    ):
        raise ValueError("review_later_gates_invalid")
    if review.get("reviewer_side_effects") != []:
        raise ValueError("review_side_effects_nonempty")


def build_authorization(
    preparation: dict[str, Any], values: dict[str, Any], review_raw: bytes
) -> dict[str, Any]:
    if sha256(review_raw) != REVIEW_RAW_SHA256:
        raise ValueError("review_raw_sha256_mismatch")
    task_ids = values["task_ids"]
    batch_ids = values["batch_ids"]
    helper = values["helper"]
    authorization: dict[str, Any] = {
        "schema_version": "m4.1-execution-authorization-v1",
        "milestone": "M4",
        "revision": REVISION,
        "status": "AUTHORIZED_UNCONSUMED",
        "preparation_baseline": {
            "head": PREPARATION_HEAD,
            "ci_run_id": PREPARATION_CI_RUN_ID,
            "ci_conclusion": PREPARATION_CI_CONCLUSION,
            "audit_status": "PREPARED_NOT_AUTHORIZED",
            "manifest_path": PREPARATION_RELATIVE,
            "manifest_git_blob_oid": git_blob_oid(PREPARATION_HEAD, PREPARATION_RELATIVE),
            "manifest_raw_sha256": sha256(PREPARATION_PATH.read_bytes()),
        },
        "review": {
            "path": REVIEW_RELATIVE,
            "git_blob_oid": git_blob_oid(REVIEW_HEAD, REVIEW_RELATIVE),
            "raw_sha256": REVIEW_RAW_SHA256,
            "schema_version": "m4.1-gate-iv-independent-review-v1",
            "status": "PASSED",
            "decision": "AUTHORIZE_M4_1_GATE_IV_ONE_SHOT_MATRIX",
            "finding_count": 0,
        },
        "execution_helper": {
            "path": HELPER_RELATIVE,
            "git_blob_oid": git_blob_oid(PREPARATION_HEAD, HELPER_RELATIVE),
            "raw_sha256": helper["raw_sha256"],
            "minimum_windows_powershell_version": "5.1",
            "request_binding_count": 60,
            "read_only": True,
        },
        "model_binding": {
            "exact_model_id": MODEL_ID,
            "reasoning_effort": REASONING_EFFORT,
            "configured_default_required": True,
            "model_argument_policy": "OMIT_AND_VERIFY_CONFIGURED_DEFAULT",
            "thinking_argument_policy": "OMIT_AND_VERIFY_CONFIGURED_DEFAULT",
            "official_model_reference": OFFICIAL_MODEL_REFERENCE,
            "model_context_window_tokens": MODEL_CONTEXT_WINDOW_TOKENS,
            "model_max_output_tokens": MODEL_MAX_OUTPUT_TOKENS,
        },
        "execution_surface": {
            "tool": "codex_app.create_thread",
            "project_id": PROJECT_ID,
            "project_label": PROJECT_LABEL,
            "project_is_git_repository": True,
            "environment": "worktree",
            "starting_branch": AUTHORIZATION_BRANCH,
            "task_context_isolation": "ONE_NEW_THREAD_PER_TASK_ID",
            "cross_task_result_visibility": False,
        },
        "authority": {
            "fresh_execution_authorized": True,
            "authorized_task_ids": task_ids,
            "authorized_task_count": 60,
            "authorized_batch_ids": batch_ids,
            "authorized_batch_count": 6,
            "fresh_contexts_authorized": 60,
            "independent_finalizations_authorized": 60,
            "attempts_per_task_id": 1,
            "result_writes_authorized": True,
            "result_write_root_prefix": RESULT_ROOT_PREFIX,
            "retry_authorized": False,
            "repair_authorized": False,
            "followup_message_authorized": False,
            "judge_execution_authorized": False,
            "blind_mapping_access_authorized": False,
            "aggregation_authorized": False,
            "threshold_claim_authorized": False,
            "closure_authorized": False,
        },
        "batch_policy": {
            "batch_order": batch_ids,
            "tasks_per_batch": 10,
            "stop_current_batch_on_infrastructure_or_protocol_failure": True,
            "later_batches_mutable_after_observation": False,
            "failure_preservation_required": True,
            "successor_revision_required_after_failure": True,
        },
        "prelaunch_counters": dict(ZERO_COUNTERS),
        "consumption": {
            "authorization_token_status": "UNCONSUMED",
            "claim_count": 0,
            "launch_claim_path": LAUNCH_CLAIM_RELATIVE,
            "launch_claim_must_be_absent": True,
            "claim_consumes_entire_matrix_authorization": True,
            "partial_or_failed_matrix_requires_new_revision": True,
        },
        "does_not_authorize": list(DOES_NOT_AUTHORIZE),
        "authorization_token": "",
    }
    authorization["authorization_token"] = authorization_token(authorization)
    if authorization["authorization_token"] == OLD_AUTHORIZATION_TOKEN:
        raise ValueError("authorization_token_reused")
    return authorization


def build_control(
    preparation: dict[str, Any],
    values: dict[str, Any],
    authorization_raw: bytes,
) -> dict[str, Any]:
    constraints = dict(values["constraints"])
    constraints.update(
        {
            "exact_model_id": MODEL_ID,
            "model_binding_status": "BOUND_BY_M4_1_GATE_IV_AUTHORIZATION",
            "reasoning_effort": REASONING_EFFORT,
        }
    )
    batches = [
        {
            "batch_id": batch["batch_id"],
            "source_batch_id": batch["source_batch_id"],
            "domain": batch["domain"],
            "task_ids": batch["task_ids"],
            "source_task_ids": batch["source_task_ids"],
            "planned_task_count": 10,
            "stop_on_infrastructure_or_protocol_failure": True,
            "later_batches_mutable_after_observation": False,
        }
        for batch in values["batches"]
    ]
    controlled_tasks = []
    for task in values["tasks"]:
        allowed_paths = [task["case_path"], "evals/m4/task-protocol.md"]
        if task["variant_instruction_path"] is not None:
            allowed_paths.append(task["variant_instruction_path"])
        controlled_tasks.append(
            {
                **task,
                "allowed_context_paths": allowed_paths,
                "forbidden_context_roots": [
                    "evals/m4/results",
                    "evals/m4/execution",
                ],
                "attempt_limit": 1,
                "independent_finalization_required": True,
                "cross_task_result_visibility": False,
            }
        )
    helper = values["helper"]
    return {
        "schema_version": "m4.1-execution-control-v1",
        "milestone": "M4",
        "revision": REVISION,
        "status": "READY_UNCONSUMED",
        "authorization": {
            "path": AUTHORIZATION_RELATIVE,
            "raw_sha256": sha256(authorization_raw),
            "authorization_token": parse_json_object(authorization_raw)["authorization_token"],
        },
        "preparation": {
            "path": PREPARATION_RELATIVE,
            "head": PREPARATION_HEAD,
            "ci_run_id": PREPARATION_CI_RUN_ID,
            "git_blob_oid": git_blob_oid(PREPARATION_HEAD, PREPARATION_RELATIVE),
            "raw_sha256": sha256(PREPARATION_PATH.read_bytes()),
            "request_binding_count": 60,
        },
        "execution_helper": {
            "path": HELPER_RELATIVE,
            "git_blob_oid": git_blob_oid(PREPARATION_HEAD, HELPER_RELATIVE),
            "raw_sha256": helper["raw_sha256"],
            "minimum_windows_powershell_version": "5.1",
            "modes": helper["modes"],
            "request_binding_count": 60,
            "read_only": True,
        },
        "task_protocol": {
            "path": "evals/m4/task-protocol.md",
            "raw_sha256": values["tasks"][0]["task_protocol_sha256"],
        },
        "request_policy": {
            "surface": "codex_app.create_thread",
            "target_type": "project",
            "project_id": PROJECT_ID,
            "environment_type": "worktree",
            "starting_branch": AUTHORIZATION_BRANCH,
            "model_field": "OMITTED",
            "thinking_field": "OMITTED",
            "configured_default_model_required": MODEL_ID,
            "configured_default_reasoning_effort_required": REASONING_EFFORT,
            "one_new_thread_per_task_id": True,
            "one_independent_finalization_per_task_id": True,
        },
        "execution_constraints": constraints,
        "batch_order": values["batch_ids"],
        "batches": batches,
        "tasks": controlled_tasks,
        "launch_claim": {
            "path": LAUNCH_CLAIM_RELATIVE,
            "must_be_absent_before_execution": True,
            "claim_count_before_execution": 0,
            "claim_consumes_authorization_token": True,
            "must_be_created_before_first_task": True,
        },
        "permissions": {
            "fresh_task_creation": True,
            "result_writes_below_frozen_roots": True,
            "retry": False,
            "repair": False,
            "followup_message": False,
            "cross_task_result_read": False,
            "judge_execution": False,
            "blind_mapping_access": False,
            "aggregation": False,
            "threshold_claim": False,
            "m4_closure": False,
        },
        "prelaunch_counters": dict(ZERO_COUNTERS),
        "does_not_authorize": list(DOES_NOT_AUTHORIZE),
    }


def build_artifacts(repo_root: Path = REPO_ROOT) -> dict[Path, bytes]:
    if repo_root.resolve() != REPO_ROOT.resolve():
        raise ValueError("alternate_repo_root_not_supported_by_builder")
    _assert_git_baseline()
    preparation = parse_json_object(PREPARATION_PATH.read_bytes())
    values = _preparation_values(preparation)
    review_raw = REVIEW_PATH.read_bytes()
    review = parse_json_object(review_raw)
    validate_review(review, preparation, review_raw)
    authorization = build_authorization(preparation, values, review_raw)
    authorization_raw = json_bytes(authorization)
    control = build_control(preparation, values, authorization_raw)
    return {
        AUTHORIZATION_PATH: authorization_raw,
        CONTROL_PATH: json_bytes(control),
    }


def _write_atomic(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_name, path)
    finally:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args(argv)
    try:
        artifacts = build_artifacts()
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"status": "invalid", "errors": [str(error)]}, separators=(",", ":")))
        return 1
    mismatches: list[str] = []
    for path, expected in artifacts.items():
        if arguments.check:
            try:
                actual = path.read_bytes()
            except OSError:
                actual = None
            if actual != expected:
                mismatches.append(path.relative_to(REPO_ROOT).as_posix())
        else:
            _write_atomic(path, expected)
    result = {
        "status": "valid" if not mismatches else "invalid",
        "revision": REVISION,
        "mismatches": mismatches,
        "authorized_task_count": 60,
        "batch_count": 6,
        "authorization_token_status": "UNCONSUMED",
        "fresh_tasks_created": 0,
        "review_generated": False,
    }
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return 0 if not mismatches else 1


if __name__ == "__main__":
    sys.exit(main())
