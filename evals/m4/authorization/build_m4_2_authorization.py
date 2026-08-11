#!/usr/bin/env python3
"""Build or atomically issue the deterministic M4.2 authorization pair."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any, Mapping


REPO_ROOT = Path(__file__).resolve().parents[3]
BASELINE_HEAD = "4efa75c542172a95c6c72c8c1450fea77a8e2ff1"
BASELINE_TREE = "f7394004d9d5f0a9be22a62dca1d67bb5f2af52d"
PREPARATION_ACCEPTED_CANDIDATE = "44e6cd611ce67f362015c431d3c1d6ba069ad345"
GATE_IV_B_CLOSURE_HEAD = "ad67a79f39685937466d3a49d30c6a5117e2810c"
AUTHORIZATION_BRANCH = (
    "codex/m4-cross-engineering-forward-evaluation-m4.2-one-shot-authorization"
)
MODEL_ID = "gpt-5.6-sol"
REASONING_EFFORT = "max"
PROJECT_ID = "ff35b25f-4644-41c8-9073-74c697559439"
PROJECT_LABEL = "engineering-research-copilot"

PREPARATION_RELATIVE = (
    "evals/m4/authorization/m4.2/authorization-preparation.json"
)
PROOF_RELATIVE = "evals/m4/authorization/m4.2/gate-iv-b-protocol-proof.json"
AUTHORIZATION_SCHEMA_RELATIVE = (
    "evals/m4/authorization/m4.2/execution-authorization.schema.json"
)
CONTROL_SCHEMA_RELATIVE = (
    "evals/m4/authorization/m4.2/execution-control.schema.json"
)
HELPER_RELATIVE = "evals/m4/execution/prepare_m4_2_request_bundles.ps1"
MANIFEST_RELATIVE = "evals/m4/revisions/m4.2/preparation-manifest.json"
ROOT_MANIFEST_RELATIVE = "evals/m4/preparation-manifest.json"
TASK_PROTOCOL_RELATIVE = "evals/m4/task-protocol.md"
RUBRIC_RELATIVE = "evals/m4/judge-rubric.json"
AUTHORIZATION_RELATIVE = "evals/m4/authorization/m4.2/execution-authorization.json"
CONTROL_RELATIVE = "evals/m4/authorization/m4.2/execution-control.json"
TOKEN_RELATIVE = "evals/m4/authorization/m4.2/authorization-token.json"
ACCEPTANCE_CLAIM_RELATIVE = "evals/m4/authorization/m4.2/acceptance-claim.json"
LAUNCH_CLAIM_RELATIVE = "evals/m4/execution/m4.2/launch-claim.json"
RESULTS_MANIFEST_RELATIVE = "evals/m4/results-manifest.json"
RESULT_ROOT_PREFIX = "evals/m4/results/m4.2"

AUTHORIZATION_PATH = REPO_ROOT / AUTHORIZATION_RELATIVE
CONTROL_PATH = REPO_ROOT / CONTROL_RELATIVE

SNAPSHOTS: dict[str, tuple[str, str, int]] = {
    PREPARATION_RELATIVE: (
        "fe768c25100e6750ece90159d6b88109356cdf6e",
        "573ee113c5846ace7892607f953e2bd83985a104a43d268cc63b7a7425c5950d",
        20173,
    ),
    PROOF_RELATIVE: (
        "d3fe975431f2e4584a52ee5305b169f5b5d29268",
        "9d160de6893fbb6bd01158524a3a48931496b6d4cae1fdc4c9f0e736921068e0",
        33204,
    ),
    AUTHORIZATION_SCHEMA_RELATIVE: (
        "d3700fe3bfa039a9421b1d05e2cb1c99975ea0aa",
        "0cc09f3856e0812fd38d1c962adce6e2dbe5ec12067bc202d100290782bb38e8",
        9578,
    ),
    CONTROL_SCHEMA_RELATIVE: (
        "4bcf02ac9259ae9c93256ddbb29062dca6979d30",
        "e76a3071d8b00489afb9b5fd4fd798a6e08f23d376ddecff4d267687c4d9604e",
        10532,
    ),
    HELPER_RELATIVE: (
        "27e3e11d5790f28e32fee87693a5f88ef77b6bb7",
        "40b15ec3d1ce885f5f0d438377e298541974d46eb26efc934c0755b22b126712",
        8371,
    ),
    MANIFEST_RELATIVE: (
        "5d33fe292745a3a2f22e7b841b1499fefab6baf7",
        "bdd64dbe666f1b17c5c1bcad3ab148dced173331519a08b06087882060713a57",
        95902,
    ),
    TASK_PROTOCOL_RELATIVE: (
        "65fff58503e80422c64602e6a6eaab9f7298c1c0",
        "bf52fe558358036cffe37b6390bfeaf896aa45152b31a6777552de0f44b36468",
        1938,
    ),
    RUBRIC_RELATIVE: (
        "407a514c31bd33979e7d5c944224388890e0acac",
        "36056affa68cba4e39c8281ef88fc9460b39a1158b8c52b718a2235d2bc5196a",
        6683,
    ),
}

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
    "raw_model_finals",
    "aggregation_calls",
    "acceptance_claims",
)
ZERO_COUNTERS = {name: 0 for name in COUNTER_NAMES}

DOES_NOT_AUTHORIZE = [
    "a launch claim or consumption of this authorization",
    "a second claim or a partial-matrix claim",
    "a second attempt, retry, repair, continuation, or follow-up message",
    "a task outside the frozen 60-task M4.2 matrix",
    "cross-task or cross-arm result visibility",
    "judge execution, blind-map access, or unblinding",
    "result aggregation or acceptance-threshold claims",
    "changes to cases, prompts, variants, rubric, thresholds, or randomization",
    "M4 closure, M5, an experiment, simulation, training run, deployment, or control action",
]

ALLOWED_CHANGE_PATHS = frozenset(
    {
        ".github/workflows/m1-validation.yml",
        "STATUS.md",
        "docs/superpowers/plans/2026-08-10-m4.2-one-shot-authorization.md",
        "evals/m4/authorization/build_m4_2_authorization.py",
        "evals/m4/authorization/audit_m4_2_authorization.py",
        "evals/m4/authorization/audit_m4_2_authorization_preparation.py",
        "evals/m4/authorization/audit_m4_2_gate_iv_b_protocol_proof.py",
        "tests/test_m4_2_authorization.py",
        "tests/test_m4_2_authorization_preparation.py",
        "tests/test_m4_2_gate_iv_b_protocol_proof.py",
        "tests/test_m3_r5_erratum.py",
        AUTHORIZATION_RELATIVE,
        CONTROL_RELATIVE,
    }
)

_HISTORICAL_TOKEN_CACHE: set[str] | None = None
_BASELINE_BLOB_CACHE: dict[str, tuple[str, bytes]] = {}
_MANIFEST_VALUES_CACHE: dict[str, Any] | None = None


class DuplicateKeyError(ValueError):
    """Raised when strict JSON decoding sees a duplicate object key."""


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


def _pairs_no_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError("duplicate_key")
        result[key] = value
    return result


def _reject_constant(_value: str) -> object:
    raise ValueError("non_finite_number")


def parse_json_object(raw: bytes, label: str = "json") -> dict[str, Any]:
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ValueError(f"{label}_utf8_bom_forbidden")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise ValueError(f"{label}_utf8_invalid") from error
    try:
        value = json.loads(
            text,
            object_pairs_hook=_pairs_no_duplicates,
            parse_constant=_reject_constant,
        )
    except DuplicateKeyError as error:
        raise ValueError(f"{label}_duplicate_key") from error
    except (json.JSONDecodeError, ValueError) as error:
        code = "non_finite_number" if "non_finite_number" in str(error) else "json_invalid"
        raise ValueError(f"{label}_{code}") from error
    if not isinstance(value, dict):
        raise ValueError(f"{label}_object_root_required")
    return value


def _git(*arguments: str) -> subprocess.CompletedProcess[bytes]:
    environment = os.environ.copy()
    environment["GIT_NO_REPLACE_OBJECTS"] = "1"
    return subprocess.run(
        ["git", "--no-replace-objects", *arguments],
        cwd=REPO_ROOT,
        env=environment,
        capture_output=True,
        check=False,
    )


def _git_text(*arguments: str) -> str:
    completed = _git(*arguments)
    if completed.returncode != 0:
        raise ValueError(f"git_{arguments[0].replace('-', '_')}_failed")
    try:
        return completed.stdout.decode("utf-8", errors="strict").strip()
    except UnicodeDecodeError as error:
        raise ValueError("git_output_utf8_invalid") from error


def _safe_relative(relative: str) -> str:
    path = PurePosixPath(relative.replace("\\", "/"))
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("unsafe_source_path")
    return path.as_posix()


def git_blob_oid(head: str, relative: str) -> str:
    safe = _safe_relative(relative)
    if head == BASELINE_HEAD and safe in _BASELINE_BLOB_CACHE:
        return _BASELINE_BLOB_CACHE[safe][0]
    oid = _git_text("rev-parse", f"{head}:{safe}")
    if re.fullmatch(r"[0-9a-f]{40}", oid) is None:
        raise ValueError("git_blob_oid_invalid")
    return oid


def git_blob_bytes(head: str, relative: str) -> bytes:
    safe = _safe_relative(relative)
    if head == BASELINE_HEAD and safe in _BASELINE_BLOB_CACHE:
        return _BASELINE_BLOB_CACHE[safe][1]
    oid = git_blob_oid(head, relative)
    completed = _git("cat-file", "blob", oid)
    if completed.returncode != 0:
        raise ValueError("git_blob_unavailable")
    raw = completed.stdout
    framed = f"blob {len(raw)}\0".encode("ascii") + raw
    if hashlib.sha1(framed).hexdigest() != oid:
        raise ValueError("git_blob_content_oid_mismatch")
    if head == BASELINE_HEAD:
        _BASELINE_BLOB_CACHE[safe] = (oid, raw)
    return raw


def _assert_baseline() -> None:
    if _git("cat-file", "-e", f"{BASELINE_HEAD}^{{commit}}").returncode != 0:
        raise ValueError("baseline_head_unavailable")
    if _git_text("rev-parse", f"{BASELINE_HEAD}^{{tree}}") != BASELINE_TREE:
        raise ValueError("baseline_tree_mismatch")
    if _git("merge-base", "--is-ancestor", BASELINE_HEAD, "HEAD").returncode != 0:
        raise ValueError("baseline_head_not_ancestor")
    changed = _git_text("diff", "--name-only", "--no-renames", BASELINE_HEAD, "HEAD", "--")
    changed_paths = {line.replace("\\", "/") for line in changed.splitlines() if line}
    if not changed_paths <= ALLOWED_CHANGE_PATHS:
        raise ValueError("authorization_change_set_mismatch")


def _snapshot_bytes(relative: str) -> bytes:
    expected_oid, expected_hash, expected_length = SNAPSHOTS[relative]
    if git_blob_oid(BASELINE_HEAD, relative) != expected_oid:
        raise ValueError(f"snapshot_blob_mismatch:{relative}")
    raw = git_blob_bytes(BASELINE_HEAD, relative)
    if len(raw) != expected_length:
        raise ValueError(f"snapshot_length_mismatch:{relative}")
    if sha256(raw) != expected_hash:
        raise ValueError(f"snapshot_sha256_mismatch:{relative}")
    if git_blob_oid("HEAD", relative) != expected_oid:
        raise ValueError(f"snapshot_head_blob_mismatch:{relative}")
    return raw


def request_binding_sha256(task: Mapping[str, object]) -> str:
    fields = (
        "m4.2-request-binding-v1",
        str(task["task_id"]),
        str(task["source_task_id"]),
        str(task["root_task_id"]),
        str(task["blind_id"]),
        str(task["case_sha256"]),
        str(task["user_input_sha256"]),
        str(task["task_protocol_sha256"]),
        str(task["variant_instruction_sha256"] or "NONE"),
        str(task["rubric_sha256"]),
        str(task["execution_constraints_sha256"]),
    )
    return sha256(("\n".join(fields) + "\n").encode("utf-8"))


def _require_exact_type(value: object, expected: type, code: str) -> None:
    if type(value) is not expected:
        raise ValueError(code)


def _manifest_values() -> dict[str, Any]:
    global _MANIFEST_VALUES_CACHE
    if _MANIFEST_VALUES_CACHE is not None:
        return _MANIFEST_VALUES_CACHE
    manifest = parse_json_object(_snapshot_bytes(MANIFEST_RELATIVE), "manifest")
    if set(manifest) != {
        "schema_version",
        "milestone",
        "revision",
        "status",
        "predecessor",
        "source_preparation",
        "authority",
        "lifecycle_requirements",
        "matrix",
        "randomization",
        "execution_helper",
        "tasks",
        "counters",
    }:
        raise ValueError("manifest_root_keys_mismatch")
    if (
        manifest.get("schema_version") != "m4.2-successor-preparation-v1"
        or manifest.get("milestone") != "M4"
        or manifest.get("revision") != "M4.2"
        or manifest.get("status") != "PREPARATION_ONLY"
    ):
        raise ValueError("manifest_identity_mismatch")
    matrix = manifest.get("matrix")
    randomization = manifest.get("randomization")
    helper = manifest.get("execution_helper")
    authority = manifest.get("authority")
    counters = manifest.get("counters")
    tasks = manifest.get("tasks")
    if not all(isinstance(value, dict) for value in (matrix, randomization, helper, authority, counters)):
        raise ValueError("manifest_shape_invalid")
    if not isinstance(tasks, list) or not all(isinstance(task, dict) for task in tasks):
        raise ValueError("manifest_tasks_invalid")
    batches = matrix.get("batches")
    if not isinstance(batches, list) or not all(isinstance(batch, dict) for batch in batches):
        raise ValueError("manifest_batches_invalid")
    for key, expected in {
        "case_count": 12,
        "arm_count": 5,
        "planned_task_count": 60,
        "batch_count": 6,
    }.items():
        _require_exact_type(matrix.get(key), int, f"matrix_{key}_type_invalid")
        if matrix.get(key) != expected:
            raise ValueError(f"matrix_{key}_mismatch")
    if len(tasks) != 60 or len(batches) != 6:
        raise ValueError("matrix_cardinality_mismatch")

    task_ids = [task.get("task_id") for task in tasks]
    source_task_ids = [task.get("source_task_id") for task in tasks]
    root_task_ids = [task.get("root_task_id") for task in tasks]
    blind_ids = [task.get("blind_id") for task in tasks]
    batch_ids = [batch.get("batch_id") for batch in batches]
    if not all(isinstance(value, str) for values in (task_ids, source_task_ids, root_task_ids, blind_ids, batch_ids) for value in values):
        raise ValueError("matrix_identifier_type_invalid")
    if len(set(task_ids)) != 60 or len(set(source_task_ids)) != 60 or len(set(root_task_ids)) != 60:
        raise ValueError("matrix_task_identifier_duplicate")
    if len(set(blind_ids)) != 60 or blind_ids != [f"M4-J{index:03d}" for index in range(121, 181)]:
        raise ValueError("matrix_blind_identifier_mismatch")
    if len(set(batch_ids)) != 6:
        raise ValueError("matrix_batch_identifier_duplicate")
    if any(not value.startswith("M4.2-") for value in task_ids):
        raise ValueError("matrix_task_namespace_mismatch")
    if any(not value.startswith("M4.1-") for value in source_task_ids):
        raise ValueError("matrix_source_task_namespace_mismatch")
    if any(not value.startswith("M4-") for value in root_task_ids):
        raise ValueError("matrix_root_task_namespace_mismatch")
    if any(not value.startswith("M4.2-BATCH-") for value in batch_ids):
        raise ValueError("matrix_batch_namespace_mismatch")
    if randomization.get("frozen") is not True or randomization.get("task_order") != task_ids:
        raise ValueError("matrix_task_order_mismatch")
    if randomization.get("blind_mapping") != dict(zip(task_ids, blind_ids, strict=True)):
        raise ValueError("matrix_blind_mapping_mismatch")
    if randomization.get("judge_mapping_access_authorized") is not False:
        raise ValueError("matrix_blind_authority_mismatch")
    if counters != {name: 0 for name in COUNTER_NAMES[:9]}:
        raise ValueError("manifest_counters_nonzero")
    for key in (
        "fresh_execution_authorized",
        "fresh_tasks_authorized",
        "result_writes_authorized",
        "retry_authorized",
        "repair_authorized",
    ):
        if authority.get(key) is not False:
            raise ValueError(f"manifest_authority_mismatch:{key}")
    if (
        helper.get("path") != HELPER_RELATIVE
        or helper.get("raw_sha256") != SNAPSHOTS[HELPER_RELATIVE][1]
        or helper.get("request_binding_count") != 60
        or helper.get("read_only") is not True
        or helper.get("minimum_windows_powershell_version") != "5.1"
    ):
        raise ValueError("manifest_helper_binding_mismatch")

    batch_members: list[str] = []
    task_by_id = {str(task["task_id"]): task for task in tasks}
    for batch in batches:
        members = batch.get("task_ids")
        if not isinstance(members, list) or len(members) != 10 or len(set(members)) != 10:
            raise ValueError("matrix_batch_members_invalid")
        if batch.get("planned_task_count") != 10:
            raise ValueError("matrix_batch_size_mismatch")
        if batch.get("stop_on_infrastructure_or_protocol_failure") is not True:
            raise ValueError("matrix_batch_stop_policy_mismatch")
        if batch.get("later_batches_mutable_after_observation") is not False:
            raise ValueError("matrix_batch_mutability_mismatch")
        batch_members.extend(str(value) for value in members)
        for task_id in members:
            task = task_by_id.get(str(task_id))
            if task is None or task.get("batch_id") != batch.get("batch_id"):
                raise ValueError("matrix_task_batch_membership_mismatch")
    if sorted(batch_members) != sorted(str(value) for value in task_ids):
        raise ValueError("matrix_batch_roster_mismatch")

    root_manifest = parse_json_object(
        git_blob_bytes(BASELINE_HEAD, ROOT_MANIFEST_RELATIVE), "root_manifest"
    )
    constraints = root_manifest.get("execution_constraints")
    if not isinstance(constraints, dict):
        raise ValueError("execution_constraints_missing")
    constraints_hash = sha256(canonical_bytes(constraints))
    protocol_raw = _snapshot_bytes(TASK_PROTOCOL_RELATIVE)
    rubric_raw = _snapshot_bytes(RUBRIC_RELATIVE)
    case_cache: dict[str, tuple[bytes, dict[str, Any]]] = {}
    variant_cache: dict[str, bytes] = {}
    recomputed_bindings: list[str] = []
    case_ids: set[str] = set()
    arm_ids: set[str] = set()
    for task in tasks:
        task_id = str(task["task_id"])
        case_ids.add(str(task.get("case_id")))
        arm_ids.add(str(task.get("arm_id")))
        if task.get("result_root") != f"{RESULT_ROOT_PREFIX}/{task_id}":
            raise ValueError("task_result_root_mismatch")
        if task.get("result_root_must_be_absent") is not True:
            raise ValueError("task_result_root_policy_mismatch")
        case_path = task.get("case_path")
        if not isinstance(case_path, str):
            raise ValueError("task_case_path_invalid")
        case_path = _safe_relative(case_path)
        if not case_path.startswith("evals/m4/cases/"):
            raise ValueError("task_case_path_outside_frozen_root")
        if case_path not in case_cache:
            case_raw = git_blob_bytes(BASELINE_HEAD, case_path)
            case_cache[case_path] = (case_raw, parse_json_object(case_raw, "case"))
        case_raw, case = case_cache[case_path]
        user_input = case.get("user_input")
        if sha256(case_raw) != task.get("case_sha256"):
            raise ValueError("task_case_sha256_mismatch")
        if not isinstance(user_input, str) or sha256(user_input.encode("utf-8")) != task.get("user_input_sha256"):
            raise ValueError("task_user_input_sha256_mismatch")
        if sha256(protocol_raw) != task.get("task_protocol_sha256"):
            raise ValueError("task_protocol_sha256_mismatch")
        if sha256(rubric_raw) != task.get("rubric_sha256"):
            raise ValueError("task_rubric_sha256_mismatch")
        if constraints_hash != task.get("execution_constraints_sha256"):
            raise ValueError("task_execution_constraints_sha256_mismatch")
        variant_path = task.get("variant_instruction_path")
        variant_hash = task.get("variant_instruction_sha256")
        if variant_path is None:
            if variant_hash is not None:
                raise ValueError("task_variant_hash_without_path")
        elif isinstance(variant_path, str):
            variant_path = _safe_relative(variant_path)
            if not variant_path.startswith("evals/m4/variants/"):
                raise ValueError("task_variant_path_outside_frozen_root")
            if variant_path not in variant_cache:
                variant_cache[variant_path] = git_blob_bytes(BASELINE_HEAD, variant_path)
            if sha256(variant_cache[variant_path]) != variant_hash:
                raise ValueError("task_variant_sha256_mismatch")
        else:
            raise ValueError("task_variant_path_invalid")
        binding = request_binding_sha256(task)
        recomputed_bindings.append(binding)
        if binding != task.get("request_binding_sha256"):
            raise ValueError("task_request_binding_mismatch")
    if len(case_ids) != 12 or len(arm_ids) != 5:
        raise ValueError("matrix_case_arm_cardinality_mismatch")
    if len(set(recomputed_bindings)) != 60:
        raise ValueError("request_binding_uniqueness_mismatch")
    _MANIFEST_VALUES_CACHE = {
        "manifest": manifest,
        "tasks": tasks,
        "batches": batches,
        "task_ids": task_ids,
        "batch_ids": batch_ids,
        "helper": helper,
    }
    return _MANIFEST_VALUES_CACHE


def _historical_tokens() -> set[str]:
    global _HISTORICAL_TOKEN_CACHE
    if _HISTORICAL_TOKEN_CACHE is not None:
        return _HISTORICAL_TOKEN_CACHE
    completed = _git(
        "grep",
        "-h",
        "-o",
        "-E",
        r"sha256:[0-9a-f]{64}",
        BASELINE_HEAD,
        "--",
        "evals/m4",
    )
    if completed.returncode not in {0, 1}:
        raise ValueError("historical_authorization_token_scan_failed")
    try:
        values = completed.stdout.decode("ascii", errors="strict").splitlines()
    except UnicodeDecodeError as error:
        raise ValueError("historical_authorization_token_scan_invalid") from error
    _HISTORICAL_TOKEN_CACHE = {
        value for value in values if re.fullmatch(r"sha256:[0-9a-f]{64}", value)
    }
    return _HISTORICAL_TOKEN_CACHE


def _build_authorization(values: Mapping[str, Any]) -> dict[str, Any]:
    authorization: dict[str, Any] = {
        "schema_version": "m4.2-execution-authorization-v1",
        "milestone": "M4",
        "revision": "M4.2",
        "status": "AUTHORIZED_UNCONSUMED",
        "authorization_preparation": {
            "path": PREPARATION_RELATIVE,
            "accepted_candidate_head": PREPARATION_ACCEPTED_CANDIDATE,
            "git_blob_oid": SNAPSHOTS[PREPARATION_RELATIVE][0],
            "raw_sha256": SNAPSHOTS[PREPARATION_RELATIVE][1],
            "status": "M4_2_AUTHORIZATION_PREPARATION_PASSED_NOT_AUTHORIZED",
            "decision": "APPROVE_M4_2_SEPARATE_AUTHORIZATION_WORK_PACKAGE_ONLY",
        },
        "gate_iv_b_proof": {
            "closure_head": GATE_IV_B_CLOSURE_HEAD,
            "path": PROOF_RELATIVE,
            "git_blob_oid": SNAPSHOTS[PROOF_RELATIVE][0],
            "raw_sha256": SNAPSHOTS[PROOF_RELATIVE][1],
            "status": "M4_2_GATE_IV_B_PROTOCOL_PROOF_PASSED_NOT_AUTHORIZED",
            "decision": "APPROVE_M4_2_AUTHORIZATION_PREPARATION_ONLY",
        },
        "model_binding": {
            "exact_model_id": MODEL_ID,
            "reasoning_effort": REASONING_EFFORT,
            "configured_default_required": True,
            "model_argument_policy": "OMIT_AND_VERIFY_CONFIGURED_DEFAULT",
            "thinking_argument_policy": "OMIT_AND_VERIFY_CONFIGURED_DEFAULT",
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
            "whole_matrix_required": True,
            "partial_authority_allowed": False,
            "authorized_task_ids": list(values["task_ids"]),
            "authorized_task_count": 60,
            "authorized_batch_ids": list(values["batch_ids"]),
            "authorized_batch_count": 6,
            "fresh_contexts_authorized": 60,
            "independent_finalizations_authorized": 60,
            "attempts_per_task_id": 1,
            "result_writes_authorized": True,
            "result_write_root_prefix": RESULT_ROOT_PREFIX,
            "retry_authorized": False,
            "repair_authorized": False,
            "followup_message_authorized": False,
            "cross_task_result_visibility": False,
            "judge_execution_authorized": False,
            "blind_mapping_access_authorized": False,
            "aggregation_authorized": False,
            "threshold_claim_authorized": False,
            "closure_authorized": False,
        },
        "batch_policy": {
            "batch_order": list(values["batch_ids"]),
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
            "partial_authority_allowed": False,
            "second_claim_allowed": False,
            "terminal_failure_consumes_authority": True,
            "successor_revision_required_after_failure": True,
        },
        "does_not_authorize": list(DOES_NOT_AUTHORIZE),
        "authorization_token": "",
    }
    authorization["authorization_token"] = authorization_token(authorization)
    if authorization["authorization_token"] in _historical_tokens():
        raise ValueError("authorization_token_reused")
    return authorization


def _build_control(values: Mapping[str, Any], authorization_raw: bytes) -> dict[str, Any]:
    authorization = parse_json_object(authorization_raw, "authorization")
    tasks: list[dict[str, Any]] = []
    for source in values["tasks"]:
        allowed = [source["case_path"], TASK_PROTOCOL_RELATIVE]
        if source["variant_instruction_path"] is not None:
            allowed.append(source["variant_instruction_path"])
        tasks.append(
            {
                "task_id": source["task_id"],
                "source_task_id": source["source_task_id"],
                "root_task_id": source["root_task_id"],
                "blind_id": source["blind_id"],
                "batch_id": source["batch_id"],
                "case_path": source["case_path"],
                "task_protocol_path": TASK_PROTOCOL_RELATIVE,
                "variant_instruction_path": source["variant_instruction_path"],
                "request_binding_sha256": source["request_binding_sha256"],
                "result_root": source["result_root"],
                "result_root_must_be_absent": True,
                "allowed_context_paths": allowed,
                "forbidden_context_roots": ["evals/m4/results", "evals/m4/execution"],
                "attempt_limit": 1,
                "independent_finalization_required": True,
                "cross_task_result_visibility": False,
            }
        )
    batches = [
        {
            "batch_id": source["batch_id"],
            "source_batch_id": source["source_batch_id"],
            "domain": source["domain"],
            "task_ids": source["task_ids"],
            "planned_task_count": 10,
            "stop_on_infrastructure_or_protocol_failure": True,
            "later_batches_mutable_after_observation": False,
        }
        for source in values["batches"]
    ]
    return {
        "schema_version": "m4.2-execution-control-v1",
        "milestone": "M4",
        "revision": "M4.2",
        "status": "READY_UNCONSUMED",
        "authorization": {
            "path": AUTHORIZATION_RELATIVE,
            "raw_sha256": sha256(authorization_raw),
            "authorization_token": authorization["authorization_token"],
        },
        "preparation": {
            "path": PREPARATION_RELATIVE,
            "accepted_candidate_head": PREPARATION_ACCEPTED_CANDIDATE,
            "git_blob_oid": SNAPSHOTS[PREPARATION_RELATIVE][0],
            "raw_sha256": SNAPSHOTS[PREPARATION_RELATIVE][1],
            "request_binding_count": 60,
        },
        "execution_helper": {
            "path": HELPER_RELATIVE,
            "git_blob_oid": SNAPSHOTS[HELPER_RELATIVE][0],
            "raw_sha256": SNAPSHOTS[HELPER_RELATIVE][1],
            "minimum_windows_powershell_version": "5.1",
            "request_binding_count": 60,
            "read_only": True,
        },
        "request_policy": {
            "surface": "codex_app.create_thread",
            "target_type": "project",
            "project_id": PROJECT_ID,
            "environment_type": "worktree",
            "starting_branch": AUTHORIZATION_BRANCH,
            "one_new_thread_per_task_id": True,
            "one_independent_finalization_per_task_id": True,
            "cross_task_result_visibility": False,
        },
        "execution_constraints": {
            "exact_model_id": MODEL_ID,
            "reasoning_effort": REASONING_EFFORT,
            "attempts_per_task_id": 1,
            "whole_matrix_required": True,
            "partial_authority_allowed": False,
            "second_claim_allowed": False,
            "successor_revision_required_after_failure": True,
        },
        "batch_order": list(values["batch_ids"]),
        "batches": batches,
        "tasks": tasks,
        "launch_claim": {
            "path": LAUNCH_CLAIM_RELATIVE,
            "must_be_absent_before_execution": True,
            "claim_count_before_execution": 0,
            "claim_consumes_authorization_token": True,
            "claim_consumes_entire_matrix_authorization": True,
            "partial_authority_allowed": False,
            "second_claim_allowed": False,
            "must_be_created_before_first_task": True,
            "successor_revision_required_after_failure": True,
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


def _json_type_matches(value: object, expected: str | list[str]) -> bool:
    expected_types = [expected] if isinstance(expected, str) else expected
    mapping = {
        "object": lambda item: isinstance(item, dict),
        "array": lambda item: isinstance(item, list),
        "string": lambda item: isinstance(item, str),
        "integer": lambda item: type(item) is int,
        "number": lambda item: type(item) in {int, float},
        "boolean": lambda item: type(item) is bool,
        "null": lambda item: item is None,
    }
    return any(name in mapping and mapping[name](value) for name in expected_types)


def schema_errors(instance: object, schema: Mapping[str, object]) -> list[str]:
    definitions = schema.get("$defs") if isinstance(schema.get("$defs"), dict) else {}
    errors: list[str] = []

    def visit(value: object, node: Mapping[str, object], location: str) -> None:
        reference = node.get("$ref")
        if isinstance(reference, str):
            prefix = "#/$defs/"
            target = definitions.get(reference[len(prefix) :]) if reference.startswith(prefix) else None
            if not isinstance(target, dict):
                errors.append(f"{location}:ref_invalid")
                return
            visit(value, target, location)
            return
        expected_type = node.get("type")
        if isinstance(expected_type, (str, list)) and not _json_type_matches(value, expected_type):
            errors.append(f"{location}:type")
            return
        if "const" in node and canonical_bytes(value) != canonical_bytes(node["const"]):
            errors.append(f"{location}:const")
        enum = node.get("enum")
        if isinstance(enum, list) and not any(canonical_bytes(value) == canonical_bytes(item) for item in enum):
            errors.append(f"{location}:enum")
        pattern = node.get("pattern")
        if isinstance(pattern, str) and isinstance(value, str) and re.search(pattern, value) is None:
            errors.append(f"{location}:pattern")
        if isinstance(value, str) and type(node.get("minLength")) is int and len(value) < node["minLength"]:
            errors.append(f"{location}:minLength")
        if isinstance(value, dict):
            properties = node.get("properties") if isinstance(node.get("properties"), dict) else {}
            required = node.get("required") if isinstance(node.get("required"), list) else []
            missing = set(required) - set(value)
            if missing:
                errors.append(f"{location}:required")
            if node.get("additionalProperties") is False and not set(value) <= set(properties):
                errors.append(f"{location}:additionalProperties")
            for key, child in value.items():
                contract = properties.get(key)
                if isinstance(contract, dict):
                    visit(child, contract, f"{location}.{key}")
        if isinstance(value, list):
            minimum = node.get("minItems")
            maximum = node.get("maxItems")
            if type(minimum) is int and len(value) < minimum:
                errors.append(f"{location}:minItems")
            if type(maximum) is int and len(value) > maximum:
                errors.append(f"{location}:maxItems")
            if node.get("uniqueItems") is True and len({canonical_bytes(item) for item in value}) != len(value):
                errors.append(f"{location}:uniqueItems")
            item_schema = node.get("items")
            if isinstance(item_schema, dict):
                for index, item in enumerate(value):
                    visit(item, item_schema, f"{location}[{index}]")

    visit(instance, schema, "$")
    return sorted(set(errors))


def build_artifacts() -> dict[Path, bytes]:
    _assert_baseline()
    for relative in SNAPSHOTS:
        _snapshot_bytes(relative)
    values = _manifest_values()
    authorization = _build_authorization(values)
    authorization_raw = json_bytes(authorization)
    control = _build_control(values, authorization_raw)
    control_raw = json_bytes(control)
    authorization_schema = parse_json_object(
        _snapshot_bytes(AUTHORIZATION_SCHEMA_RELATIVE), "authorization_schema"
    )
    control_schema = parse_json_object(
        _snapshot_bytes(CONTROL_SCHEMA_RELATIVE), "control_schema"
    )
    if schema_errors(authorization, authorization_schema):
        raise ValueError("BLOCKED_FROZEN_AUTHORIZATION_SCHEMA")
    if schema_errors(control, control_schema):
        raise ValueError("BLOCKED_FROZEN_AUTHORIZATION_SCHEMA")
    return {AUTHORIZATION_PATH: authorization_raw, CONTROL_PATH: control_raw}


def _publish_pair(artifacts: Mapping[Path, bytes]) -> None:
    ordered = [(Path(path), raw) for path, raw in artifacts.items()]
    if len(ordered) != 2 or len({path for path, _raw in ordered}) != 2:
        raise ValueError("authorization_pair_required")
    parents = {path.parent.resolve() for path, _raw in ordered}
    if len(parents) != 1:
        raise ValueError("authorization_pair_parent_mismatch")
    parent = next(iter(parents))
    if not parent.is_dir():
        raise ValueError("authorization_parent_missing")
    if any(path.exists() for path, _raw in ordered):
        raise ValueError("already_issued")
    lock_path = parent / ".m4.2-authorization-issuance.lock"
    try:
        lock_descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as error:
        raise ValueError("issuance_in_progress") from error
    staged: list[tuple[Path, Path]] = []
    published: list[Path] = []
    try:
        for target, raw in ordered:
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{target.name}.", suffix=".tmp", dir=parent
            )
            temporary = Path(temporary_name)
            try:
                with os.fdopen(descriptor, "wb") as stream:
                    stream.write(raw)
                    stream.flush()
                    os.fsync(stream.fileno())
            except BaseException:
                try:
                    os.close(descriptor)
                except OSError:
                    pass
                temporary.unlink(missing_ok=True)
                raise
            staged.append((temporary, target))
        if any(target.exists() for _temporary, target in staged):
            raise ValueError("already_issued")
        for temporary, target in staged:
            os.replace(temporary, target)
            published.append(target)
    except BaseException:
        for target in reversed(published):
            target.unlink(missing_ok=True)
        raise
    finally:
        for temporary, _target in staged:
            temporary.unlink(missing_ok=True)
        os.close(lock_descriptor)
        lock_path.unlink(missing_ok=True)


def _forbidden_prelaunch_paths() -> list[str]:
    exact = (
        TOKEN_RELATIVE,
        ACCEPTANCE_CLAIM_RELATIVE,
        LAUNCH_CLAIM_RELATIVE,
        RESULTS_MANIFEST_RELATIVE,
    )
    prefixes = (
        "evals/m4/execution/m4.2",
        "evals/m4/results/m4.2",
        "evals/m5",
    )
    present = [relative for relative in exact if (REPO_ROOT / relative).exists()]
    present.extend(relative for relative in prefixes if (REPO_ROOT / relative).exists())
    return sorted(set(present))


def _assert_write_once_preconditions(accepted_candidate_head: str) -> None:
    if re.fullmatch(r"[0-9a-f]{40}", accepted_candidate_head) is None:
        raise ValueError("accepted_candidate_head_invalid")
    if _git_text("rev-parse", "HEAD") != accepted_candidate_head:
        raise ValueError("accepted_candidate_head_mismatch")
    if _git_text("branch", "--show-current") != AUTHORIZATION_BRANCH:
        raise ValueError("authorization_branch_mismatch")
    if _git("status", "--porcelain=v1", "--untracked-files=all").stdout:
        raise ValueError("working_tree_not_clean")
    if AUTHORIZATION_PATH.exists() or CONTROL_PATH.exists():
        raise ValueError("already_issued")
    if _forbidden_prelaunch_paths():
        raise ValueError("forbidden_prelaunch_path_present")


def _metadata(artifacts: Mapping[Path, bytes]) -> tuple[list[dict[str, object]], str]:
    authorization = parse_json_object(artifacts[AUTHORIZATION_PATH], "authorization")
    token = str(authorization["authorization_token"])
    records = [
        {
            "path": path.relative_to(REPO_ROOT).as_posix(),
            "byte_length": len(raw),
            "raw_sha256": sha256(raw),
        }
        for path, raw in artifacts.items()
    ]
    return records, token[:19] + "..."


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--dry-run", action="store_true")
    modes.add_argument("--check", action="store_true")
    modes.add_argument("--write-once", action="store_true")
    parser.add_argument("--accepted-candidate-head")
    arguments = parser.parse_args(argv)
    try:
        artifacts = build_artifacts()
        if arguments.write_once:
            if arguments.accepted_candidate_head is None:
                raise ValueError("accepted_candidate_head_required")
            _assert_write_once_preconditions(arguments.accepted_candidate_head)
            _publish_pair(artifacts)
            status = "issued_unconsumed"
        elif arguments.check:
            mismatches = [
                path.relative_to(REPO_ROOT).as_posix()
                for path, expected in artifacts.items()
                if not path.is_file() or path.read_bytes() != expected
            ]
            if mismatches:
                raise ValueError("artifact_bytes_mismatch")
            status = "issued_bytes_match"
        else:
            if arguments.accepted_candidate_head is not None:
                raise ValueError("accepted_candidate_head_without_write_once")
            status = "candidate_valid"
        records, fingerprint = _metadata(artifacts)
        result = {
            "status": status,
            "revision": "M4.2",
            "artifacts": records,
            "token_fingerprint": fingerprint,
            "claim_count": 0,
            "authorization_token_status": "UNCONSUMED" if status != "candidate_valid" else "NOT_ISSUED",
        }
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        return 0
    except ValueError as error:
        print(
            json.dumps(
                {"status": "invalid", "errors": [str(error)]},
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        return 1
    except (OSError, UnicodeError, json.JSONDecodeError):
        print('{"errors":["authorization_operation_failed"],"status":"invalid"}')
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
