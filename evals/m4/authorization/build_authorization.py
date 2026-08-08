#!/usr/bin/env python3
"""Build the deterministic, unconsumed M4 Gate IV authorization artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
M4_ROOT = REPO_ROOT / "evals" / "m4"
AUTHORIZATION_ROOT = M4_ROOT / "authorization"
PREPARATION_PATH = M4_ROOT / "preparation-manifest.json"
REVIEW_PATH = AUTHORIZATION_ROOT / "gate-iv-review.json"
AUTHORIZATION_PATH = AUTHORIZATION_ROOT / "execution-authorization.json"
CONTROL_PATH = AUTHORIZATION_ROOT / "execution-control.json"

PREPARATION_HEAD = "c56c3c1ab384f65e51a70e9582672c6320d19121"
PREPARATION_CI_RUN_ID = 31237480839
PREPARATION_CI_CONCLUSION = "success"
REVISION = "M4.0"
MODEL_ID = "gpt-5.6-sol"
REASONING_EFFORT = "max"
PROJECT_ID = "ff35b25f-4644-41c8-9073-74c697559439"
PROJECT_LABEL = "engineering-research-copilot"
AUTHORIZATION_BRANCH = (
    "codex/m4-cross-engineering-forward-evaluation-one-shot-authorization"
)
OFFICIAL_MODEL_REFERENCE = (
    "https://developers.openai.com/api/docs/models/gpt-5.6-sol"
)
MODEL_CONTEXT_WINDOW_TOKENS = 1_050_000
MODEL_MAX_OUTPUT_TOKENS = 128_000
LAUNCH_CLAIM_RELATIVE = "evals/m4/execution/m4.0/launch-claim.json"
RESULTS_MANIFEST_RELATIVE = "evals/m4/results-manifest.json"
RESULT_ROOT_PREFIX = "evals/m4/results/m4.0"

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

DOES_NOT_AUTHORIZE = [
    "a second attempt for any task ID",
    "a retry, repair, continuation, or follow-up message",
    "a task outside the frozen 60-task M4.0 matrix",
    "cross-task or cross-arm result visibility",
    "judge execution, blind-map access, or unblinding",
    "result aggregation or acceptance-threshold claims",
    "changes to cases, prompts, variants, rubric, thresholds, or randomization",
    "M4 closure, M5, an experiment, simulation, training run, deployment, or control action",
]

EXTRA_FROZEN_PREPARATION_PATHS = (
    "evals/m4/preparation-manifest.json",
    "evals/m4/build_preparation.py",
    "evals/m4/audit_preparation.py",
    "evals/m4/audit_results.py",
    "tests/test_m4_preparation.py",
    "tests/test_m4_results.py",
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


def authorization_token(payload: dict[str, object]) -> str:
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


def frozen_preparation_paths(preparation: dict[str, Any]) -> list[str]:
    artifacts = preparation.get("artifacts")
    if not isinstance(artifacts, dict):
        raise ValueError("preparation_artifacts_invalid")
    return sorted(set(artifacts) | set(EXTRA_FROZEN_PREPARATION_PATHS))


def _preparation_values(preparation: dict[str, Any]) -> dict[str, Any]:
    matrix = preparation.get("matrix")
    authority = preparation.get("authority")
    randomization = preparation.get("randomization")
    constraints = preparation.get("execution_constraints")
    counters = preparation.get("counters")
    tasks = preparation.get("tasks")
    if not all(
        isinstance(value, dict)
        for value in (matrix, authority, randomization, constraints, counters)
    ) or not isinstance(tasks, list):
        raise ValueError("preparation_shape_invalid")

    batches = matrix.get("batches")
    if not isinstance(batches, list):
        raise ValueError("preparation_batches_invalid")
    task_ids = [task.get("task_id") for task in tasks if isinstance(task, dict)]
    blind_ids = [task.get("blind_id") for task in tasks if isinstance(task, dict)]
    batch_ids = [batch.get("batch_id") for batch in batches if isinstance(batch, dict)]
    result_roots = [task.get("result_root") for task in tasks if isinstance(task, dict)]

    errors: list[str] = []
    expected_counts = {
        "case_count": 12,
        "arm_count": 5,
        "planned_task_count": 60,
    }
    for key, expected in expected_counts.items():
        if matrix.get(key) != expected:
            errors.append(f"preparation_{key}_invalid")
    if len(tasks) != 60 or len(task_ids) != 60 or len(set(task_ids)) != 60:
        errors.append("preparation_task_ids_invalid")
    if len(blind_ids) != 60 or len(set(blind_ids)) != 60:
        errors.append("preparation_blind_ids_invalid")
    if len(batches) != 6 or len(batch_ids) != 6 or len(set(batch_ids)) != 6:
        errors.append("preparation_batch_ids_invalid")
    if any(batch.get("planned_task_count") != 10 for batch in batches):
        errors.append("preparation_batch_size_invalid")
    if randomization.get("frozen") is not True:
        errors.append("preparation_randomization_not_frozen")
    if randomization.get("task_order") != task_ids:
        errors.append("preparation_task_order_invalid")
    mapping = randomization.get("blind_mapping")
    if not isinstance(mapping, dict) or mapping != dict(zip(task_ids, blind_ids)):
        errors.append("preparation_blind_mapping_invalid")
    if randomization.get("judge_mapping_access_authorized") is not False:
        errors.append("preparation_judge_mapping_authority_invalid")
    for key in (
        "fresh_execution_authorized",
        "fresh_tasks_authorized",
        "result_writes_authorized",
        "retry_authorized",
        "repair_authorized",
    ):
        if authority.get(key) is not False:
            errors.append(f"preparation_authority_invalid:{key}")
    if constraints.get("exact_model_id") is not None:
        errors.append("preparation_model_already_bound")
    if counters != ZERO_COUNTERS:
        errors.append("preparation_counters_nonzero")
    if len(result_roots) != 60 or len(set(result_roots)) != 60:
        errors.append("preparation_result_roots_invalid")
    if any((REPO_ROOT / str(relative)).exists() for relative in result_roots):
        errors.append("preparation_result_root_present")
    if (REPO_ROOT / RESULTS_MANIFEST_RELATIVE).exists():
        errors.append("preparation_results_manifest_present")
    if (REPO_ROOT / LAUNCH_CLAIM_RELATIVE).exists():
        errors.append("preparation_launch_claim_present")

    artifacts = preparation.get("artifacts", {})
    if isinstance(artifacts, dict):
        for relative, record in artifacts.items():
            path = REPO_ROOT / relative
            if not isinstance(record, dict) or not path.is_file():
                errors.append(f"preparation_artifact_unavailable:{relative}")
                continue
            if sha256(path.read_bytes()) != record.get("sha256"):
                errors.append(f"preparation_artifact_hash_mismatch:{relative}")

    if errors:
        raise ValueError(";".join(sorted(errors)))
    return {
        "matrix": matrix,
        "authority": authority,
        "randomization": randomization,
        "constraints": constraints,
        "counters": counters,
        "tasks": tasks,
        "batches": batches,
        "task_ids": task_ids,
        "blind_ids": blind_ids,
        "batch_ids": batch_ids,
        "result_roots": result_roots,
    }


def _assert_frozen_git_blobs(preparation: dict[str, Any]) -> None:
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", PREPARATION_HEAD, "HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        check=False,
    )
    if ancestor.returncode != 0:
        raise ValueError("preparation_head_not_ancestor")
    for relative in frozen_preparation_paths(preparation):
        if git_blob_oid(PREPARATION_HEAD, relative) != git_blob_oid("HEAD", relative):
            raise ValueError(f"frozen_preparation_blob_changed:{relative}")


def _assert_m3_and_skill_unchanged() -> None:
    changed = _git_output(
        "diff",
        "--name-only",
        PREPARATION_HEAD,
        "--",
        "evals/m3",
        "skills/engineering-research-copilot",
    )
    if changed:
        raise ValueError("m3_or_skill_tree_changed")


def build_review(
    preparation: dict[str, Any], values: dict[str, Any]
) -> dict[str, Any]:
    artifacts = preparation["artifacts"]
    return {
        "schema_version": "m4-gate-iv-review-v1",
        "review_date": "2026-08-08",
        "status": "PASSED",
        "preparation_head": PREPARATION_HEAD,
        "preparation_ci_run_id": PREPARATION_CI_RUN_ID,
        "preparation_ci_conclusion": PREPARATION_CI_CONCLUSION,
        "reviewed_manifest": {
            "path": "evals/m4/preparation-manifest.json",
            "git_blob_oid": git_blob_oid(
                PREPARATION_HEAD, "evals/m4/preparation-manifest.json"
            ),
            "raw_sha256": sha256(PREPARATION_PATH.read_bytes()),
        },
        "checks": {
            "case_count": values["matrix"]["case_count"],
            "arm_count": values["matrix"]["arm_count"],
            "planned_task_count": values["matrix"]["planned_task_count"],
            "domain_batch_count": len(values["batch_ids"]),
            "unique_task_id_count": len(set(values["task_ids"])),
            "unique_blind_id_count": len(set(values["blind_ids"])),
            "frozen_artifact_count": len(artifacts),
            "all_artifact_hashes_valid": True,
            "randomization_frozen": True,
            "judge_rubric_frozen": True,
            "prelaunch_counters_zero": True,
            "result_root_count": 0,
            "results_manifest_present": False,
            "launch_claim_present": False,
            "m3_evidence_changed_paths": [],
            "skill_changed_paths": [],
        },
        "execution_surface_observation": {
            "tool": "codex_app.create_thread",
            "project_id": PROJECT_ID,
            "project_label": PROJECT_LABEL,
            "project_is_git_repository": True,
            "model_supported": MODEL_ID,
            "reasoning_effort_supported": REASONING_EFFORT,
            "configured_default_model": MODEL_ID,
            "configured_default_reasoning_effort": REASONING_EFFORT,
        },
        "official_model_capability": {
            "reference": OFFICIAL_MODEL_REFERENCE,
            "context_window_tokens": MODEL_CONTEXT_WINDOW_TOKENS,
            "max_output_tokens": MODEL_MAX_OUTPUT_TOKENS,
            "frozen_input_context_token_ceiling": values["constraints"][
                "input_context_token_ceiling"
            ],
            "frozen_output_token_ceiling": values["constraints"][
                "output_token_ceiling"
            ],
        },
        "findings": [],
        "decision": "AUTHORIZE_GATE_IV_ONE_SHOT_MATRIX",
        "limitations": [
            "This review establishes protocol readiness only and contains no model result.",
            "The authorization HEAD must pass exact-HEAD CI before a launch claim may be created.",
            "Judge execution, aggregation, acceptance, and M4 closure remain unauthorized.",
        ],
    }


def build_authorization(
    preparation: dict[str, Any], values: dict[str, Any], review_raw: bytes
) -> dict[str, Any]:
    task_ids = values["task_ids"]
    batch_ids = values["batch_ids"]
    authorization: dict[str, Any] = {
        "schema_version": "m4-execution-authorization-v1",
        "milestone": "M4",
        "revision": REVISION,
        "status": "AUTHORIZED_UNCONSUMED",
        "preparation_baseline": {
            "head": PREPARATION_HEAD,
            "ci_run_id": PREPARATION_CI_RUN_ID,
            "ci_conclusion": PREPARATION_CI_CONCLUSION,
            "manifest_path": "evals/m4/preparation-manifest.json",
            "manifest_git_blob_oid": git_blob_oid(
                PREPARATION_HEAD, "evals/m4/preparation-manifest.json"
            ),
            "manifest_raw_sha256": sha256(PREPARATION_PATH.read_bytes()),
        },
        "review": {
            "path": "evals/m4/authorization/gate-iv-review.json",
            "raw_sha256": sha256(review_raw),
            "status": "PASSED",
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
            "authorized_task_count": len(task_ids),
            "authorized_batch_ids": batch_ids,
            "authorized_batch_count": len(batch_ids),
            "fresh_contexts_authorized": len(task_ids),
            "independent_finalizations_authorized": len(task_ids),
            "attempts_per_task_id": 1,
            "result_writes_authorized": True,
            "result_write_root_prefix": RESULT_ROOT_PREFIX,
            "retry_authorized": False,
            "repair_authorized": False,
            "judge_execution_authorized": False,
            "blind_mapping_access_authorized": False,
            "aggregation_authorized": False,
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
    return authorization


def build_control(
    preparation: dict[str, Any],
    values: dict[str, Any],
    authorization_raw: bytes,
) -> dict[str, Any]:
    constraints = dict(values["constraints"])
    constraints["exact_model_id"] = MODEL_ID
    constraints["model_binding_status"] = "BOUND_BY_GATE_IV_AUTHORIZATION"
    constraints["reasoning_effort"] = REASONING_EFFORT
    batches = [
        {
            "batch_id": batch["batch_id"],
            "domain": batch["domain"],
            "task_ids": batch["task_ids"],
            "planned_task_count": batch["planned_task_count"],
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
                "task_id": task["task_id"],
                "case_id": task["case_id"],
                "domain": task["domain"],
                "case_type": task["case_type"],
                "arm_id": task["arm_id"],
                "batch_id": task["batch_id"],
                "blind_id": task["blind_id"],
                "case_path": task["case_path"],
                "case_sha256": task["case_sha256"],
                "user_input_sha256": task["user_input_sha256"],
                "variant_instruction_path": task["variant_instruction_path"],
                "variant_instruction_sha256": task["variant_instruction_sha256"],
                "task_protocol_sha256": task["task_protocol_sha256"],
                "rubric_sha256": task["rubric_sha256"],
                "execution_constraints_sha256": task[
                    "execution_constraints_sha256"
                ],
                "allowed_context_paths": allowed_paths,
                "forbidden_context_roots": [
                    "evals/m4/results",
                    "evals/m4/execution",
                ],
                "result_root": task["result_root"],
                "attempt_limit": 1,
                "independent_finalization_required": True,
                "cross_task_result_visibility": False,
            }
        )

    return {
        "schema_version": "m4-execution-control-v1",
        "milestone": "M4",
        "revision": REVISION,
        "status": "READY_UNCONSUMED",
        "authorization": {
            "path": "evals/m4/authorization/execution-authorization.json",
            "raw_sha256": sha256(authorization_raw),
        },
        "preparation": {
            "path": "evals/m4/preparation-manifest.json",
            "head": PREPARATION_HEAD,
            "raw_sha256": sha256(PREPARATION_PATH.read_bytes()),
        },
        "task_protocol": {
            "path": "evals/m4/task-protocol.md",
            "raw_sha256": preparation["artifacts"]["evals/m4/task-protocol.md"][
                "sha256"
            ],
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
    preparation_raw = PREPARATION_PATH.read_bytes()
    preparation = parse_json_object(preparation_raw)
    values = _preparation_values(preparation)
    _assert_frozen_git_blobs(preparation)
    _assert_m3_and_skill_unchanged()
    review = build_review(preparation, values)
    review_raw = json_bytes(review)
    authorization = build_authorization(preparation, values, review_raw)
    authorization_raw = json_bytes(authorization)
    control = build_control(preparation, values, authorization_raw)
    return {
        REVIEW_PATH: review_raw,
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
        print(
            json.dumps(
                {"status": "invalid", "errors": [str(error)]},
                ensure_ascii=False,
                separators=(",", ":"),
            )
        )
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

    preparation = parse_json_object(PREPARATION_PATH.read_bytes())
    result = {
        "status": "valid" if not mismatches else "invalid",
        "mismatches": mismatches,
        "case_count": preparation["matrix"]["case_count"],
        "arm_count": preparation["matrix"]["arm_count"],
        "authorized_task_count": preparation["matrix"]["planned_task_count"],
        "batch_count": len(preparation["matrix"]["batches"]),
        "authorization_token_status": "UNCONSUMED",
        "fresh_tasks_created": 0,
    }
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return 0 if not mismatches else 1


if __name__ == "__main__":
    sys.exit(main())
