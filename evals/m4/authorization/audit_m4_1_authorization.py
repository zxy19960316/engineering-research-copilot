#!/usr/bin/env python3
"""Read-only audit for the separately reviewed M4.1 Gate IV authorization."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


AUTHORIZATION_ROOT = Path(__file__).resolve().parent
M4_ROOT = AUTHORIZATION_ROOT.parent
for search_root in (AUTHORIZATION_ROOT, M4_ROOT):
    if str(search_root) not in sys.path:
        sys.path.insert(0, str(search_root))

import audit_m4_1_preparation as preparation_audit  # noqa: E402
import build_m4_1_authorization as build  # noqa: E402


REPO_ROOT = build.REPO_ROOT
REVIEW_PATH = build.REVIEW_PATH
AUTHORIZATION_PATH = build.AUTHORIZATION_PATH
CONTROL_PATH = build.CONTROL_PATH
AUTHORIZATION_SCHEMA_PATH = build.AUTHORIZATION_ROOT / "m4.1" / (
    "execution-authorization.schema.json"
)
CONTROL_SCHEMA_PATH = build.AUTHORIZATION_ROOT / "m4.1" / (
    "execution-control.schema.json"
)
ZERO_COUNTERS = build.ZERO_COUNTERS

REVIEW_KEYS = {
    "schema_version",
    "review_date",
    "status",
    "preparation_head",
    "preparation_ci_run_id",
    "preparation_ci_conclusion",
    "reviewed_manifest",
    "reviewed_helper",
    "checks",
    "findings",
    "decision",
    "limitations",
    "reviewer_side_effects",
}
AUTHORIZATION_KEYS = {
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
CONTROL_KEYS = {
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

FROZEN_PREPARATION_PATHS = (
    "evals/m4/build_m4_1_preparation.py",
    "evals/m4/audit_m4_1_preparation.py",
    "evals/m4/execution/prepare_m4_1_request_bundles.ps1",
    "evals/m4/revisions/m4.1/preparation-manifest.json",
    "evals/m4/revisions/m4.1/preparation-manifest.schema.json",
    "tests/test_m4_1_preparation.py",
)


def _add(errors: list[str], code: str) -> None:
    if code not in errors:
        errors.append(code)


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _load(path: Path, label: str, errors: list[str]) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
    except OSError:
        _add(errors, f"{label}_unavailable")
        return {}, b""
    try:
        value = build.parse_json_object(raw)
    except (UnicodeError, ValueError, json.JSONDecodeError):
        _add(errors, f"{label}_invalid_json")
        return {}, raw
    return value, raw


def _git_text(repo_root: Path, *arguments: str) -> tuple[int, str]:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        check=False,
    )
    return completed.returncode, completed.stdout.strip()


def _git_bytes(repo_root: Path, *arguments: str) -> tuple[int, bytes]:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=repo_root,
        capture_output=True,
        check=False,
    )
    return completed.returncode, completed.stdout


def _schema_errors(
    path: Path, expected_keys: set[str], label: str
) -> list[str]:
    errors: list[str] = []
    value, _ = _load(path, label, errors)
    if value.get("type") != "object":
        _add(errors, f"{label}_root_type_invalid")
    if value.get("additionalProperties") is not False:
        _add(errors, f"{label}_not_closed")
    if set(value.get("required", [])) != expected_keys:
        _add(errors, f"{label}_required_fields_invalid")
    properties = value.get("properties")
    if not isinstance(properties, dict) or set(properties) != expected_keys:
        _add(errors, f"{label}_properties_invalid")
    return errors


def _git_snapshot_errors(repo_root: Path = REPO_ROOT) -> list[str]:
    errors: list[str] = []
    returncode, _ = _git_text(
        repo_root, "cat-file", "-e", f"{build.PREPARATION_HEAD}^{{commit}}"
    )
    if returncode != 0:
        return ["preparation_head_unavailable"]
    returncode, _ = _git_text(
        repo_root, "merge-base", "--is-ancestor", build.PREPARATION_HEAD, "HEAD"
    )
    if returncode != 0:
        _add(errors, "preparation_head_not_ancestor")

    for relative in FROZEN_PREPARATION_PATHS:
        returncode, prepared_blob = _git_text(
            repo_root, "rev-parse", f"{build.PREPARATION_HEAD}:{relative}"
        )
        if returncode != 0:
            _add(errors, f"frozen_preparation_blob_unavailable:{relative}")
            continue
        returncode, current_blob = _git_text(repo_root, "rev-parse", f"HEAD:{relative}")
        if returncode != 0:
            _add(errors, f"frozen_preparation_blob_unavailable:{relative}")
        elif current_blob != prepared_blob:
            _add(errors, f"frozen_preparation_blob_changed:{relative}")
        returncode, prepared_raw = _git_bytes(
            repo_root, "show", f"{build.PREPARATION_HEAD}:{relative}"
        )
        path = repo_root / relative
        try:
            working_raw = path.read_bytes()
        except OSError:
            _add(errors, f"frozen_preparation_worktree_unavailable:{relative}")
            continue
        if returncode != 0 or prepared_raw != working_raw:
            _add(errors, f"frozen_preparation_worktree_changed:{relative}")
    return errors


def _m4_0_evidence_errors(repo_root: Path = REPO_ROOT) -> list[str]:
    """Recheck immutable M4.0 raw bytes, blobs, and frozen-path diffs."""

    errors: list[str] = []
    evidence = (
        (
            preparation_audit.M4_0_CLAIM_RELATIVE,
            preparation_audit.CLAIM_SHA256,
            preparation_audit.CLAIM_BLOB_OID,
            "m4_0_claim",
        ),
        (
            preparation_audit.M4_0_FAILURE_RELATIVE,
            preparation_audit.FAILURE_SHA256,
            preparation_audit.FAILURE_BLOB_OID,
            "m4_0_failure",
        ),
    )
    for relative, expected_sha, expected_blob, label in evidence:
        try:
            raw = (repo_root / relative).read_bytes()
        except OSError:
            _add(errors, f"{label}_unavailable")
            continue
        if _sha256(raw) != expected_sha:
            _add(errors, f"{label}_raw_sha256_mismatch")
        for revision, revision_label in (
            ("HEAD", "head"),
            (preparation_audit.TERMINAL_HEAD, "terminal"),
        ):
            returncode, blob = _git_text(
                repo_root, "rev-parse", f"{revision}:{relative.as_posix()}"
            )
            if returncode != 0 or blob != expected_blob:
                _add(errors, f"{label}_{revision_label}_blob_mismatch")

    frozen_groups = (
        (
            preparation_audit.FROZEN_M3_AND_SKILL_PATHS,
            "m3_or_skill",
        ),
        (
            preparation_audit.FROZEN_BASE_PREPARATION_PATHS,
            "base_preparation",
        ),
        (
            preparation_audit.FROZEN_ROOT_AUTHORIZATION_PATHS,
            "m4_0_authorization",
        ),
        (
            preparation_audit.FROZEN_M4_0_EVIDENCE_PATHS,
            "m4_0_evidence",
        ),
    )
    for paths, label in frozen_groups:
        returncode, changed = _git_text(
            repo_root,
            "diff",
            "--name-only",
            preparation_audit.TERMINAL_HEAD,
            "HEAD",
            "--",
            *paths,
        )
        if returncode != 0:
            _add(errors, f"{label}_diff_failed")
        elif changed:
            _add(errors, f"{label}_changed")
        returncode, changed = _git_text(
            repo_root,
            "status",
            "--porcelain",
            "--untracked-files=all",
            "--",
            *paths,
        )
        if returncode != 0:
            _add(errors, f"{label}_status_failed")
        elif changed:
            _add(errors, f"{label}_worktree_changed")
    return errors


def _expected_values(
    preparation: dict[str, Any], errors: list[str]
) -> dict[str, Any]:
    matrix = preparation.get("matrix")
    randomization = preparation.get("randomization")
    tasks = preparation.get("tasks")
    counters = preparation.get("counters")
    if not isinstance(matrix, dict):
        matrix = {}
        _add(errors, "preparation_matrix_invalid")
    if not isinstance(randomization, dict):
        randomization = {}
        _add(errors, "preparation_randomization_invalid")
    if not isinstance(tasks, list) or not all(isinstance(task, dict) for task in tasks):
        tasks = []
        _add(errors, "preparation_tasks_invalid")
    batches = matrix.get("batches")
    if not isinstance(batches, list) or not all(
        isinstance(batch, dict) for batch in batches
    ):
        batches = []
        _add(errors, "preparation_batches_invalid")
    task_ids = [task.get("task_id") for task in tasks]
    batch_ids = [batch.get("batch_id") for batch in batches]
    request_bindings = [task.get("request_binding_sha256") for task in tasks]
    if (
        len(tasks) != 60
        or len(set(task_ids)) != 60
        or randomization.get("task_order") != task_ids
    ):
        _add(errors, "preparation_task_order_invalid")
    if len(batches) != 6 or len(set(batch_ids)) != 6:
        _add(errors, "preparation_batch_order_invalid")
    if len(set(request_bindings)) != 60:
        _add(errors, "preparation_request_bindings_invalid")
    if counters != ZERO_COUNTERS:
        _add(errors, "preparation_counters_nonzero")
    return {
        "matrix": matrix,
        "randomization": randomization,
        "tasks": tasks,
        "batches": batches,
        "task_ids": task_ids,
        "batch_ids": batch_ids,
        "request_bindings": request_bindings,
    }


def _validate_review(
    review: dict[str, Any], preparation: dict[str, Any], errors: list[str]
) -> None:
    if set(review) != REVIEW_KEYS:
        _add(errors, "review_fields_invalid")
    expected_scalars = {
        "schema_version": "m4.1-gate-iv-independent-review-v1",
        "review_date": "2026-08-08",
        "status": "PASSED",
        "preparation_head": build.PREPARATION_HEAD,
        "preparation_ci_run_id": build.PREPARATION_CI_RUN_ID,
        "preparation_ci_conclusion": "success",
        "decision": "AUTHORIZE_M4_1_GATE_IV_ONE_SHOT_MATRIX",
    }
    for field, expected in expected_scalars.items():
        if review.get(field) != expected:
            _add(errors, f"review_field_invalid:{field}")
    if review.get("findings") != []:
        _add(errors, "review_findings_nonempty")
    if review.get("reviewer_side_effects") != []:
        _add(errors, "review_side_effects_nonempty")

    manifest_relative = build.PREPARATION_PATH.relative_to(REPO_ROOT).as_posix()
    helper_relative = build.HELPER_RELATIVE
    expected_manifest = {
        "path": manifest_relative,
        "raw_sha256": _sha256(build.PREPARATION_PATH.read_bytes()),
        "git_blob_oid": build.git_blob_oid(build.PREPARATION_HEAD, manifest_relative),
    }
    expected_helper = {
        "path": helper_relative,
        "raw_sha256": _sha256((REPO_ROOT / helper_relative).read_bytes()),
        "git_blob_oid": build.git_blob_oid(build.PREPARATION_HEAD, helper_relative),
    }
    if review.get("reviewed_manifest") != expected_manifest:
        _add(errors, "reviewed_manifest_invalid")
    if review.get("reviewed_helper") != expected_helper:
        _add(errors, "reviewed_helper_invalid")

    checks = review.get("checks")
    if not isinstance(checks, dict):
        _add(errors, "review_checks_invalid")
        return
    configured = checks.get("configured_defaults", {})
    if configured != {
        "matched": True,
        "model": build.MODEL_ID,
        "reasoning_effort": build.REASONING_EFFORT,
    }:
        _add(errors, "review_configured_defaults_invalid")
    exact_ci = checks.get("exact_head_ci", {})
    if (
        not isinstance(exact_ci, dict)
        or exact_ci.get("head_sha_match") is not True
        or exact_ci.get("run_id") != build.PREPARATION_CI_RUN_ID
        or exact_ci.get("validate", {}).get("conclusion") != "success"
        or exact_ci.get("ubuntu_historical_audit", {}).get("conclusion")
        != "success"
        or exact_ci.get("windows_historical_audit", {}).get("conclusion")
        != "success"
    ):
        _add(errors, "review_exact_head_ci_invalid")
    matrix = checks.get("m4_1_matrix", {})
    expected_matrix_scalars = {
        "cases": 12,
        "arms": 5,
        "tasks": 60,
        "batches": 6,
        "tasks_per_batch": 10,
        "new_task_ids": 60,
        "relative_order_inherited": True,
        "inherited_field_drift": 0,
    }
    if not isinstance(matrix, dict) or any(
        matrix.get(key) != value for key, value in expected_matrix_scalars.items()
    ):
        _add(errors, "review_matrix_invalid")
    bindings = checks.get("request_bindings", {})
    if not isinstance(bindings, dict) or any(
        bindings.get(key) != value
        for key, value in {
            "matched": 60,
            "independently_recomputed": 60,
            "unique": 60,
            "powershell_5_1_compatible": True,
            "write_network_process_api_hits": [],
        }.items()
    ):
        _add(errors, "review_request_bindings_invalid")
    zero = checks.get("zero_state", {})
    if not isinstance(zero, dict) or any(
        zero.get(key) != value
        for key, value in {
            "all_counters_zero": True,
            "fresh_execution_authorized": False,
            "global_results_manifest_present": False,
            "m4_1_authorization_artifacts_present": False,
            "m4_1_launch_claim_present": False,
            "result_roots_present": 0,
        }.items()
    ):
        _add(errors, "review_zero_state_invalid")
    later = checks.get("later_gates", {})
    if not isinstance(later, dict) or set(later.values()) != {False}:
        _add(errors, "review_later_gates_invalid")
    preserved = checks.get("m4_0_preservation", {})
    if not isinstance(preserved, dict) or any(
        preserved.get(key) != value
        for key, value in {
            "terminal_head": preparation_audit.TERMINAL_HEAD,
            "terminal_audit": "PRE_DISPATCH_FAILED_PRESERVED",
            "claim_sha256": preparation_audit.CLAIM_SHA256,
            "claim_blob": preparation_audit.CLAIM_BLOB_OID,
            "failure_sha256": preparation_audit.FAILURE_SHA256,
            "failure_blob": preparation_audit.FAILURE_BLOB_OID,
            "authorization_token": "CONSUMED",
            "fresh_result_state": "NOT_RUN",
            "frozen_path_diff_count": 0,
            "m4_0_authorization_diff_count": 0,
        }.items()
    ):
        _add(errors, "review_m4_0_preservation_invalid")


def _validate_authorization(
    authorization: dict[str, Any],
    authorization_raw: bytes,
    review_raw: bytes,
    expected: dict[str, Any],
    values: dict[str, Any],
    configured_model: str | None,
    configured_reasoning_effort: str | None,
    errors: list[str],
) -> str:
    if set(authorization) != AUTHORIZATION_KEYS:
        _add(errors, "authorization_fields_invalid")
    for field, value in {
        "schema_version": "m4.1-execution-authorization-v1",
        "milestone": "M4",
        "revision": "M4.1",
        "status": "AUTHORIZED_UNCONSUMED",
    }.items():
        if authorization.get(field) != value:
            _add(errors, f"authorization_field_invalid:{field}")
    if authorization.get("authorization_token") != build.authorization_token(
        authorization
    ):
        _add(errors, "authorization_token_invalid")
    if authorization.get("authorization_token") == build.OLD_AUTHORIZATION_TOKEN:
        _add(errors, "authorization_token_reused")

    configured_check = "NOT_REQUESTED"
    if configured_model is not None or configured_reasoning_effort is not None:
        configured_check = "MATCHED"
        if configured_model != build.MODEL_ID:
            _add(errors, "configured_model_mismatch")
            configured_check = "MISMATCH"
        if configured_reasoning_effort != build.REASONING_EFFORT:
            _add(errors, "configured_reasoning_effort_mismatch")
            configured_check = "MISMATCH"

    model_binding = authorization.get("model_binding")
    if (
        model_binding != expected.get("model_binding")
        or not isinstance(model_binding, dict)
        or model_binding.get("exact_model_id") != build.MODEL_ID
        or model_binding.get("reasoning_effort") != build.REASONING_EFFORT
        or model_binding.get("configured_default_required") is not True
    ):
        _add(errors, "model_binding_invalid")
    if authorization.get("preparation_baseline") != expected.get(
        "preparation_baseline"
    ):
        _add(errors, "preparation_baseline_invalid")
    if authorization.get("review") != expected.get("review"):
        _add(errors, "review_reference_invalid")
    if authorization.get("execution_helper") != expected.get("execution_helper"):
        _add(errors, "execution_helper_reference_invalid")
    if authorization.get("execution_surface") != expected.get("execution_surface"):
        _add(errors, "execution_surface_invalid")

    authority = authorization.get("authority")
    if not isinstance(authority, dict):
        authority = {}
        _add(errors, "authority_shape_invalid")
    if authority.get("authorized_task_ids") != values["task_ids"]:
        _add(errors, "authorized_task_ids_invalid")
    if authority.get("authorized_batch_ids") != values["batch_ids"]:
        _add(errors, "authorized_batch_ids_invalid")
    for field, value in {
        "authorized_task_count": 60,
        "authorized_batch_count": 6,
        "fresh_contexts_authorized": 60,
        "independent_finalizations_authorized": 60,
        "attempts_per_task_id": 1,
    }.items():
        if authority.get(field) != value:
            _add(errors, f"authority_limit_invalid:{field}")
    if authority.get("fresh_execution_authorized") is not True:
        _add(errors, "fresh_execution_authority_missing")
    if authority.get("result_writes_authorized") is not True:
        _add(errors, "result_write_authority_missing")
    if authority.get("result_write_root_prefix") != build.RESULT_ROOT_PREFIX:
        _add(errors, "result_write_root_prefix_invalid")
    for field in ("retry_authorized", "repair_authorized"):
        if authority.get(field) is not False:
            _add(errors, "retry_or_repair_authority_forbidden")
    if authority.get("followup_message_authorized") is not False:
        _add(errors, "followup_authority_forbidden")
    for field in ("judge_execution_authorized", "blind_mapping_access_authorized"):
        if authority.get(field) is not False:
            _add(errors, "judge_or_unblind_authority_forbidden")
    for field in (
        "aggregation_authorized",
        "threshold_claim_authorized",
        "closure_authorized",
    ):
        if authority.get(field) is not False:
            _add(errors, "later_gate_authority_forbidden")
    if authorization.get("batch_policy") != expected.get("batch_policy"):
        _add(errors, "batch_policy_invalid")
    if authorization.get("prelaunch_counters") != ZERO_COUNTERS:
        _add(errors, "prelaunch_counters_nonzero")
    expected_consumption = {
        "authorization_token_status": "UNCONSUMED",
        "claim_count": 0,
        "launch_claim_path": build.LAUNCH_CLAIM_RELATIVE,
        "launch_claim_must_be_absent": True,
        "claim_consumes_entire_matrix_authorization": True,
        "partial_or_failed_matrix_requires_new_revision": True,
    }
    if authorization.get("consumption") != expected_consumption:
        _add(errors, "consumption_state_invalid")
    if authorization.get("does_not_authorize") != build.DOES_NOT_AUTHORIZE:
        _add(errors, "does_not_authorize_invalid")
    if not authorization_raw or not review_raw:
        _add(errors, "authorization_binding_raw_empty")
    return configured_check


def _validate_control(
    control: dict[str, Any],
    expected: dict[str, Any],
    values: dict[str, Any],
    errors: list[str],
) -> None:
    if set(control) != CONTROL_KEYS:
        _add(errors, "control_fields_invalid")
    for field, value in {
        "schema_version": "m4.1-execution-control-v1",
        "milestone": "M4",
        "revision": "M4.1",
        "status": "READY_UNCONSUMED",
    }.items():
        if control.get(field) != value:
            _add(errors, f"control_field_invalid:{field}")
    for field, code in (
        ("authorization", "control_authorization_reference_invalid"),
        ("preparation", "control_preparation_reference_invalid"),
        ("execution_helper", "execution_helper_reference_invalid"),
        ("task_protocol", "task_protocol_reference_invalid"),
        ("request_policy", "request_policy_invalid"),
        ("execution_constraints", "execution_constraints_invalid"),
        ("launch_claim", "launch_claim_control_invalid"),
    ):
        if control.get(field) != expected.get(field):
            _add(errors, code)
    if control.get("batch_order") != values["batch_ids"]:
        _add(errors, "batch_order_invalid")

    batches = control.get("batches")
    if not isinstance(batches, list) or len(batches) != 6:
        batches = []
        _add(errors, "batch_roster_invalid")
    for prepared, controlled in zip(values["batches"], batches):
        if not isinstance(controlled, dict):
            _add(errors, "batch_roster_invalid")
            continue
        if controlled.get("batch_id") != prepared.get("batch_id"):
            _add(errors, "batch_roster_invalid")
        if controlled.get("task_ids") != prepared.get("task_ids"):
            _add(errors, "batch_task_roster_invalid")
        if controlled.get("planned_task_count") != 10:
            _add(errors, "batch_size_invalid")
        if controlled.get("stop_on_infrastructure_or_protocol_failure") is not True:
            _add(errors, "batch_stop_policy_invalid")
        if controlled.get("later_batches_mutable_after_observation") is not False:
            _add(errors, "batch_mutation_policy_invalid")

    tasks = control.get("tasks")
    if not isinstance(tasks, list) or len(tasks) != 60:
        tasks = []
        _add(errors, "control_task_roster_invalid")
    if [task.get("task_id") for task in tasks if isinstance(task, dict)] != values[
        "task_ids"
    ]:
        _add(errors, "control_task_roster_invalid")
    projection_fields = (
        "task_id",
        "source_task_id",
        "blind_id",
        "case_id",
        "domain",
        "case_type",
        "arm_id",
        "batch_id",
        "case_path",
        "case_sha256",
        "user_input_sha256",
        "variant_instruction_path",
        "variant_instruction_sha256",
        "task_protocol_sha256",
        "rubric_sha256",
        "execution_constraints_sha256",
        "result_root",
    )
    for prepared, controlled in zip(values["tasks"], tasks):
        if not isinstance(controlled, dict):
            _add(errors, "control_task_shape_invalid")
            continue
        task_id = str(prepared.get("task_id"))
        for field in projection_fields:
            if controlled.get(field) != prepared.get(field):
                _add(errors, f"task_projection_invalid:{task_id}:{field}")
        if controlled.get("request_binding_sha256") != prepared.get(
            "request_binding_sha256"
        ):
            _add(errors, "request_binding_mismatch")
        if controlled.get("attempt_limit") != 1:
            _add(errors, "task_attempt_limit_invalid")
        if controlled.get("independent_finalization_required") is not True:
            _add(errors, "task_finalization_policy_invalid")
        if controlled.get("cross_task_result_visibility") is not False:
            _add(errors, "cross_task_result_visibility_forbidden")
        if controlled.get("forbidden_context_roots") != [
            "evals/m4/results",
            "evals/m4/execution",
        ]:
            _add(errors, "task_context_isolation_invalid")

    expected_permissions = {
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
    }
    if control.get("permissions") != expected_permissions:
        _add(errors, "control_permissions_invalid")
    if control.get("prelaunch_counters") != ZERO_COUNTERS:
        _add(errors, "control_prelaunch_counters_nonzero")
    if control.get("does_not_authorize") != build.DOES_NOT_AUTHORIZE:
        _add(errors, "control_does_not_authorize_invalid")


def audit_authorization(
    repo_root: Path = REPO_ROOT,
    *,
    review_path: Path | None = None,
    authorization_path: Path | None = None,
    control_path: Path | None = None,
    launch_claim_path: Path | None = None,
    results_parent: Path | None = None,
    configured_model: str | None = None,
    configured_reasoning_effort: str | None = None,
    verify_git: bool = True,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    errors: list[str] = []
    review_path = review_path or REVIEW_PATH
    authorization_path = authorization_path or AUTHORIZATION_PATH
    control_path = control_path or CONTROL_PATH
    launch_claim_path = launch_claim_path or (repo_root / build.LAUNCH_CLAIM_RELATIVE)
    results_parent = results_parent or (repo_root / "evals/m4/results")

    preparation, _ = _load(build.PREPARATION_PATH, "preparation_manifest", errors)
    review, review_raw = _load(review_path, "gate_iv_review", errors)
    authorization, authorization_raw = _load(
        authorization_path, "execution_authorization", errors
    )
    control, control_raw = _load(control_path, "execution_control", errors)
    values = _expected_values(preparation, errors)

    expected_artifacts: dict[Path, bytes] = {}
    expected_authorization: dict[str, Any] = {}
    expected_control: dict[str, Any] = {}
    try:
        expected_artifacts = build.build_artifacts(repo_root)
        if set(expected_artifacts) != {AUTHORIZATION_PATH, CONTROL_PATH}:
            _add(errors, "authorization_artifact_set_invalid")
        expected_authorization = build.parse_json_object(
            expected_artifacts[AUTHORIZATION_PATH]
        )
        expected_control = build.parse_json_object(expected_artifacts[CONTROL_PATH])
    except (
        KeyError,
        OSError,
        TypeError,
        UnicodeError,
        ValueError,
        json.JSONDecodeError,
    ):
        _add(errors, "authorization_regeneration_failed")

    _validate_review(review, preparation, errors)
    configured_check = _validate_authorization(
        authorization,
        authorization_raw,
        review_raw,
        expected_authorization,
        values,
        configured_model,
        configured_reasoning_effort,
        errors,
    )
    _validate_control(control, expected_control, values, errors)

    for code in _schema_errors(
        AUTHORIZATION_SCHEMA_PATH, AUTHORIZATION_KEYS, "authorization_schema"
    ):
        _add(errors, code)
    for code in _schema_errors(CONTROL_SCHEMA_PATH, CONTROL_KEYS, "control_schema"):
        _add(errors, code)
    for path, actual, code in (
        (
            AUTHORIZATION_PATH,
            authorization_raw,
            "authorization_regeneration_mismatch",
        ),
        (CONTROL_PATH, control_raw, "control_regeneration_mismatch"),
    ):
        expected_raw = expected_artifacts.get(path)
        if expected_raw is not None and actual != expected_raw:
            _add(errors, code)

    if verify_git:
        for code in _git_snapshot_errors(repo_root):
            _add(errors, code)
    for code in _m4_0_evidence_errors(repo_root):
        _add(errors, code)

    try:
        preparation_result = preparation_audit.audit_preparation(
            repo_root,
            results_base=results_parent,
            launch_claim_path=launch_claim_path,
            verify_git=verify_git,
        )
    except (OSError, RuntimeError, TypeError, ValueError):
        preparation_result = {"status": "INVALID", "errors": ["audit_exception"]}
    if preparation_result.get("status") != "PREPARED_NOT_AUTHORIZED":
        for code in preparation_result.get("errors", ["preparation_audit_failed"]):
            _add(errors, f"preparation_audit_failed:{code}")

    results_parent_present = results_parent.exists()
    if results_parent_present:
        _add(errors, "results_parent_present_before_launch")
    existing_result_roots = []
    for task in values["tasks"]:
        result_root = repo_root / str(task.get("result_root", ""))
        if result_root.exists():
            existing_result_roots.append(str(task.get("task_id")))
    if existing_result_roots:
        _add(errors, "result_root_present_before_launch")
    if (repo_root / build.RESULTS_MANIFEST_RELATIVE).exists():
        _add(errors, "results_manifest_present_before_launch")
    launch_claim_present = launch_claim_path.exists()
    if launch_claim_present:
        _add(errors, "authorization_already_claimed")

    consumption = authorization.get("consumption")
    token_status = (
        consumption.get("authorization_token_status")
        if isinstance(consumption, dict)
        else None
    )
    return {
        "status": "READY_UNCONSUMED" if not errors else "INVALID",
        "errors": sorted(errors),
        "review_status": review.get("status"),
        "authorization_token": authorization.get("authorization_token"),
        "authorization_token_status": token_status,
        "configured_default_check": configured_check,
        "bound_model": authorization.get("model_binding", {}).get("exact_model_id")
        if isinstance(authorization.get("model_binding"), dict)
        else None,
        "bound_reasoning_effort": authorization.get("model_binding", {}).get(
            "reasoning_effort"
        )
        if isinstance(authorization.get("model_binding"), dict)
        else None,
        "authorized_task_count": len(values["task_ids"]),
        "authorized_batch_count": len(values["batch_ids"]),
        "request_binding_count": len(set(values["request_bindings"])),
        "execution_counters": authorization.get("prelaunch_counters", {}),
        "existing_result_root_count": len(existing_result_roots),
        "results_parent_present": results_parent_present,
        "launch_claim_present": launch_claim_present,
        "result_state": "NOT_RUN",
        "callback_invocations": 0,
        "network_calls": 0,
        "side_effects": [],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--configured-model")
    parser.add_argument("--configured-reasoning-effort")
    parser.add_argument("--require-configured-defaults", action="store_true")
    arguments = parser.parse_args(argv)
    if arguments.require_configured_defaults and (
        arguments.configured_model is None
        or arguments.configured_reasoning_effort is None
    ):
        print(
            json.dumps(
                {"status": "INVALID", "errors": ["configured_defaults_required"]},
                separators=(",", ":"),
            )
        )
        return 1
    result = audit_authorization(
        configured_model=arguments.configured_model,
        configured_reasoning_effort=arguments.configured_reasoning_effort,
    )
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return 0 if result["status"] == "READY_UNCONSUMED" else 1


if __name__ == "__main__":
    sys.exit(main())
