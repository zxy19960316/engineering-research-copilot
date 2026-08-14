#!/usr/bin/env python3
"""Read-only audit and preflight for the unconsumed M4 Gate IV authorization."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


AUTHORIZATION_ROOT = Path(__file__).resolve().parent
M4_ROOT = AUTHORIZATION_ROOT.parent
if str(M4_ROOT) not in sys.path:
    sys.path.insert(0, str(M4_ROOT))

import build_authorization as build  # noqa: E402
from audit_preparation import audit_preparation  # noqa: E402


REPO_ROOT = build.REPO_ROOT
REVIEW_PATH = build.REVIEW_PATH
AUTHORIZATION_PATH = build.AUTHORIZATION_PATH
CONTROL_PATH = build.CONTROL_PATH
AUTHORIZATION_SCHEMA_PATH = AUTHORIZATION_ROOT / "execution-authorization.schema.json"
CONTROL_SCHEMA_PATH = AUTHORIZATION_ROOT / "execution-control.schema.json"
ZERO_COUNTERS = build.ZERO_COUNTERS

REVIEW_KEYS = {
    "schema_version",
    "review_date",
    "status",
    "preparation_head",
    "preparation_ci_run_id",
    "preparation_ci_conclusion",
    "reviewed_manifest",
    "checks",
    "execution_surface_observation",
    "official_model_capability",
    "findings",
    "decision",
    "limitations",
}
AUTHORIZATION_KEYS = {
    "schema_version",
    "milestone",
    "revision",
    "status",
    "preparation_baseline",
    "review",
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

EXPECTED_MODEL_BINDING = {
    "exact_model_id": build.MODEL_ID,
    "reasoning_effort": build.REASONING_EFFORT,
    "configured_default_required": True,
    "model_argument_policy": "OMIT_AND_VERIFY_CONFIGURED_DEFAULT",
    "thinking_argument_policy": "OMIT_AND_VERIFY_CONFIGURED_DEFAULT",
    "official_model_reference": build.OFFICIAL_MODEL_REFERENCE,
    "model_context_window_tokens": build.MODEL_CONTEXT_WINDOW_TOKENS,
    "model_max_output_tokens": build.MODEL_MAX_OUTPUT_TOKENS,
}


def _add(errors: list[str], code: str) -> None:
    if code not in errors:
        errors.append(code)


def _load(
    path: Path, code: str, errors: list[str]
) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
    except OSError:
        _add(errors, f"{code}_unavailable")
        return {}, b""
    try:
        value = build.parse_json_object(raw)
    except (UnicodeError, ValueError, json.JSONDecodeError):
        _add(errors, f"{code}_invalid_json")
        return {}, raw
    return value, raw


def _schema_errors(
    path: Path, expected_required: set[str], code: str
) -> list[str]:
    errors: list[str] = []
    value, _ = _load(path, code, errors)
    if value.get("type") != "object":
        _add(errors, f"{code}_root_type_invalid")
    if value.get("additionalProperties") is not False:
        _add(errors, f"{code}_not_closed")
    if set(value.get("required", [])) != expected_required:
        _add(errors, f"{code}_required_fields_invalid")
    properties = value.get("properties")
    if not isinstance(properties, dict) or set(properties) != expected_required:
        _add(errors, f"{code}_properties_invalid")
    return errors


def _git_snapshot_errors(preparation: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", build.PREPARATION_HEAD, "HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
    )
    if ancestor.returncode != 0:
        _add(errors, "preparation_head_not_ancestor")
    for relative in build.frozen_preparation_paths(preparation):
        try:
            prepared = build.git_blob_oid(build.PREPARATION_HEAD, relative)
            current = build.git_blob_oid("HEAD", relative)
        except ValueError:
            _add(errors, f"frozen_preparation_blob_unavailable:{relative}")
            continue
        if prepared != current:
            _add(errors, f"frozen_preparation_blob_changed:{relative}")
    try:
        build._assert_m3_and_skill_unchanged()
    except ValueError:
        _add(errors, "m3_or_skill_tree_changed")
    return errors


def _expected_values(
    preparation: dict[str, Any], errors: list[str]
) -> dict[str, Any]:
    try:
        return build._preparation_values(preparation)
    except ValueError as error:
        _add(errors, f"preparation_invalid:{error}")
        return {
            "task_ids": [],
            "batch_ids": [],
            "tasks": [],
            "batches": [],
            "counters": {},
            "matrix": {},
            "randomization": {},
            "constraints": {},
            "result_roots": [],
        }


def _validate_review(
    review: dict[str, Any], preparation: dict[str, Any], errors: list[str]
) -> None:
    if set(review) != REVIEW_KEYS:
        _add(errors, "review_fields_invalid")
    expected_scalars = {
        "schema_version": "m4-gate-iv-review-v1",
        "review_date": "2026-08-08",
        "status": "PASSED",
        "preparation_head": build.PREPARATION_HEAD,
        "preparation_ci_run_id": build.PREPARATION_CI_RUN_ID,
        "preparation_ci_conclusion": "success",
        "decision": "AUTHORIZE_GATE_IV_ONE_SHOT_MATRIX",
    }
    for field, expected in expected_scalars.items():
        if review.get(field) != expected:
            _add(errors, f"review_field_invalid:{field}")
    if review.get("findings") != []:
        _add(errors, "review_findings_nonempty")
    checks = review.get("checks")
    matrix = preparation.get("matrix", {})
    expected_checks = {
        "case_count": matrix.get("case_count"),
        "arm_count": matrix.get("arm_count"),
        "planned_task_count": matrix.get("planned_task_count"),
        "domain_batch_count": 6,
        "unique_task_id_count": 60,
        "unique_blind_id_count": 60,
        "frozen_artifact_count": len(preparation.get("artifacts", {})),
        "all_artifact_hashes_valid": True,
        "randomization_frozen": True,
        "judge_rubric_frozen": True,
        "prelaunch_counters_zero": True,
        "result_root_count": 0,
        "results_manifest_present": False,
        "launch_claim_present": False,
        "m3_evidence_changed_paths": [],
        "skill_changed_paths": [],
    }
    if checks != expected_checks:
        _add(errors, "review_checks_invalid")


def _validate_authorization(
    authorization: dict[str, Any],
    authorization_raw: bytes,
    review_raw: bytes,
    values: dict[str, Any],
    configured_model: str | None,
    configured_reasoning_effort: str | None,
    errors: list[str],
) -> str:
    if set(authorization) != AUTHORIZATION_KEYS:
        _add(errors, "authorization_fields_invalid")
    expected_scalars = {
        "schema_version": "m4-execution-authorization-v1",
        "milestone": "M4",
        "revision": build.REVISION,
        "status": "AUTHORIZED_UNCONSUMED",
    }
    for field, expected in expected_scalars.items():
        if authorization.get(field) != expected:
            _add(errors, f"authorization_field_invalid:{field}")
    if authorization.get("authorization_token") != build.authorization_token(
        authorization
    ):
        _add(errors, "authorization_token_invalid")
    if authorization.get("model_binding") != EXPECTED_MODEL_BINDING:
        _add(errors, "model_binding_invalid")

    configured_check = "NOT_REQUESTED"
    if configured_model is not None or configured_reasoning_effort is not None:
        configured_check = "MATCHED"
        if configured_model != build.MODEL_ID:
            _add(errors, "configured_model_mismatch")
            configured_check = "MISMATCH"
        if configured_reasoning_effort != build.REASONING_EFFORT:
            _add(errors, "configured_reasoning_effort_mismatch")
            configured_check = "MISMATCH"

    review_reference = authorization.get("review")
    if review_reference != {
        "path": "evals/m4/authorization/gate-iv-review.json",
        "raw_sha256": build.sha256(review_raw),
        "status": "PASSED",
    }:
        _add(errors, "review_reference_invalid")

    baseline = authorization.get("preparation_baseline")
    expected_baseline = {
        "head": build.PREPARATION_HEAD,
        "ci_run_id": build.PREPARATION_CI_RUN_ID,
        "ci_conclusion": "success",
        "manifest_path": "evals/m4/preparation-manifest.json",
        "manifest_git_blob_oid": build.git_blob_oid(
            build.PREPARATION_HEAD, "evals/m4/preparation-manifest.json"
        ),
        "manifest_raw_sha256": build.sha256(build.PREPARATION_PATH.read_bytes()),
    }
    if baseline != expected_baseline:
        _add(errors, "preparation_baseline_invalid")

    authority = authorization.get("authority")
    if not isinstance(authority, dict):
        authority = {}
        _add(errors, "authority_shape_invalid")
    if authority.get("authorized_task_ids") != values["task_ids"]:
        _add(errors, "authorized_task_ids_invalid")
    if authority.get("authorized_batch_ids") != values["batch_ids"]:
        _add(errors, "authorized_batch_ids_invalid")
    expected_counts = {
        "authorized_task_count": 60,
        "authorized_batch_count": 6,
        "fresh_contexts_authorized": 60,
        "independent_finalizations_authorized": 60,
        "attempts_per_task_id": 1,
    }
    for field, expected in expected_counts.items():
        if authority.get(field) != expected:
            _add(errors, f"authority_limit_invalid:{field}")
    if authority.get("fresh_execution_authorized") is not True:
        _add(errors, "fresh_execution_authority_missing")
    if authority.get("result_writes_authorized") is not True:
        _add(errors, "result_write_authority_missing")
    if authority.get("result_write_root_prefix") != build.RESULT_ROOT_PREFIX:
        _add(errors, "result_write_root_prefix_invalid")
    for field in (
        "retry_authorized",
        "repair_authorized",
    ):
        if authority.get(field) is not False:
            _add(errors, "retry_or_repair_authority_forbidden")
    for field in (
        "judge_execution_authorized",
        "blind_mapping_access_authorized",
    ):
        if authority.get(field) is not False:
            _add(errors, "judge_authority_forbidden")
    for field in ("aggregation_authorized", "closure_authorized"):
        if authority.get(field) is not False:
            _add(errors, "later_gate_authority_forbidden")

    if authorization.get("prelaunch_counters") != ZERO_COUNTERS:
        _add(errors, "prelaunch_counters_nonzero")
    consumption = authorization.get("consumption")
    expected_consumption = {
        "authorization_token_status": "UNCONSUMED",
        "claim_count": 0,
        "launch_claim_path": build.LAUNCH_CLAIM_RELATIVE,
        "launch_claim_must_be_absent": True,
        "claim_consumes_entire_matrix_authorization": True,
        "partial_or_failed_matrix_requires_new_revision": True,
    }
    if consumption != expected_consumption:
        _add(errors, "consumption_state_invalid")
    if authorization.get("does_not_authorize") != build.DOES_NOT_AUTHORIZE:
        _add(errors, "does_not_authorize_invalid")
    if not authorization_raw:
        _add(errors, "authorization_raw_empty")
    return configured_check


def _validate_control(
    control: dict[str, Any],
    authorization_raw: bytes,
    preparation_raw: bytes,
    values: dict[str, Any],
    errors: list[str],
) -> None:
    if set(control) != CONTROL_KEYS:
        _add(errors, "control_fields_invalid")
    expected_scalars = {
        "schema_version": "m4-execution-control-v1",
        "milestone": "M4",
        "revision": build.REVISION,
        "status": "READY_UNCONSUMED",
    }
    for field, expected in expected_scalars.items():
        if control.get(field) != expected:
            _add(errors, f"control_field_invalid:{field}")
    if control.get("authorization") != {
        "path": "evals/m4/authorization/execution-authorization.json",
        "raw_sha256": build.sha256(authorization_raw),
    }:
        _add(errors, "control_authorization_reference_invalid")
    preparation_reference = control.get("preparation")
    if preparation_reference != {
        "path": "evals/m4/preparation-manifest.json",
        "head": build.PREPARATION_HEAD,
        "raw_sha256": build.sha256(preparation_raw),
    }:
        _add(errors, "control_preparation_reference_invalid")
    if control.get("batch_order") != values["batch_ids"]:
        _add(errors, "batch_order_invalid")
    batches = control.get("batches")
    if not isinstance(batches, list) or len(batches) != 6:
        _add(errors, "batch_roster_invalid")
    else:
        for prepared, controlled in zip(values["batches"], batches):
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
        _add(errors, "control_task_roster_invalid")
        tasks = []
    if [task.get("task_id") for task in tasks if isinstance(task, dict)] != values[
        "task_ids"
    ]:
        _add(errors, "control_task_roster_invalid")
    expected_roots = {
        task["task_id"]: task["result_root"] for task in values["tasks"]
    }
    for task in tasks:
        if not isinstance(task, dict):
            _add(errors, "control_task_shape_invalid")
            continue
        if task.get("attempt_limit") != 1:
            _add(errors, "task_attempt_limit_invalid")
        if task.get("independent_finalization_required") is not True:
            _add(errors, "task_finalization_policy_invalid")
        if task.get("cross_task_result_visibility") is not False:
            _add(errors, "cross_task_result_visibility_forbidden")
        if task.get("result_root") != expected_roots.get(task.get("task_id")):
            _add(errors, "task_result_root_invalid")
        if task.get("forbidden_context_roots") != [
            "evals/m4/results",
            "evals/m4/execution",
        ]:
            _add(errors, "task_context_isolation_invalid")

    request_policy = control.get("request_policy")
    expected_request = {
        "surface": "codex_app.create_thread",
        "target_type": "project",
        "project_id": build.PROJECT_ID,
        "environment_type": "worktree",
        "starting_branch": build.AUTHORIZATION_BRANCH,
        "model_field": "OMITTED",
        "thinking_field": "OMITTED",
        "configured_default_model_required": build.MODEL_ID,
        "configured_default_reasoning_effort_required": build.REASONING_EFFORT,
        "one_new_thread_per_task_id": True,
        "one_independent_finalization_per_task_id": True,
    }
    if request_policy != expected_request:
        _add(errors, "request_policy_invalid")
    permissions = control.get("permissions")
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
    if permissions != expected_permissions:
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
    results_base: Path | None = None,
    configured_model: str | None = None,
    configured_reasoning_effort: str | None = None,
    verify_git: bool = True,
) -> dict[str, Any]:
    errors: list[str] = []
    review_path = review_path or REVIEW_PATH
    authorization_path = authorization_path or AUTHORIZATION_PATH
    control_path = control_path or CONTROL_PATH
    launch_claim_path = launch_claim_path or (repo_root / build.LAUNCH_CLAIM_RELATIVE)

    preparation, preparation_raw = _load(
        repo_root / "evals" / "m4" / "preparation-manifest.json",
        "preparation_manifest",
        errors,
    )
    review, review_raw = _load(review_path, "gate_iv_review", errors)
    authorization, authorization_raw = _load(
        authorization_path, "execution_authorization", errors
    )
    control, control_raw = _load(control_path, "execution_control", errors)
    values = _expected_values(preparation, errors)

    _validate_review(review, preparation, errors)
    configured_check = _validate_authorization(
        authorization,
        authorization_raw,
        review_raw,
        values,
        configured_model,
        configured_reasoning_effort,
        errors,
    )
    _validate_control(
        control, authorization_raw, preparation_raw, values, errors
    )

    for code in _schema_errors(
        AUTHORIZATION_SCHEMA_PATH, AUTHORIZATION_KEYS, "authorization_schema"
    ):
        _add(errors, code)
    for code in _schema_errors(CONTROL_SCHEMA_PATH, CONTROL_KEYS, "control_schema"):
        _add(errors, code)

    try:
        expected_artifacts = build.build_artifacts(repo_root)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as error:
        expected_artifacts = {}
        _add(errors, f"authorization_regeneration_failed:{error}")
    comparisons = (
        (review_raw, expected_artifacts.get(REVIEW_PATH), "review_regeneration_mismatch"),
        (
            authorization_raw,
            expected_artifacts.get(AUTHORIZATION_PATH),
            "authorization_regeneration_mismatch",
        ),
        (control_raw, expected_artifacts.get(CONTROL_PATH), "control_regeneration_mismatch"),
    )
    for actual, expected, code in comparisons:
        if expected is not None and actual != expected:
            _add(errors, code)

    if verify_git:
        for code in _git_snapshot_errors(preparation):
            _add(errors, code)

    preparation_audit = audit_preparation(repo_root)
    if preparation_audit.get("status") != "prepared":
        for code in preparation_audit.get("errors", ["preparation_audit_failed"]):
            _add(errors, f"preparation_audit_failed:{code}")

    existing_result_roots: list[str] = []
    for task in values["tasks"]:
        if results_base is None:
            path = repo_root / task["result_root"]
        else:
            path = results_base / task["task_id"]
        if path.exists():
            existing_result_roots.append(task["task_id"])
    if existing_result_roots:
        _add(errors, "result_root_present_before_launch")
    if (repo_root / build.RESULTS_MANIFEST_RELATIVE).exists():
        _add(errors, "results_manifest_present_before_launch")

    launch_claim_present = launch_claim_path.exists()
    if launch_claim_present:
        _add(errors, "authorization_already_claimed")

    return {
        "status": "READY_UNCONSUMED" if not errors else "INVALID",
        "errors": sorted(errors),
        "review_status": review.get("status"),
        "authorization_token": authorization.get("authorization_token"),
        "authorization_token_status": authorization.get("consumption", {}).get(
            "authorization_token_status"
        )
        if isinstance(authorization.get("consumption"), dict)
        else None,
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
        "execution_counters": authorization.get("prelaunch_counters", {}),
        "existing_result_root_count": len(existing_result_roots),
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
                {
                    "status": "INVALID",
                    "errors": ["configured_defaults_required"],
                },
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
