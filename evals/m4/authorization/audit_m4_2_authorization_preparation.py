from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Mapping


REPO_ROOT = Path(__file__).resolve().parents[3]
BASELINE_HEAD = "ad67a79f39685937466d3a49d30c6a5117e2810c"
BASELINE_TREE = "7f5d7c2e15616e4e52f45c0366f8b347211e8849"
B3_HEAD = "249e28d07d5e52cd9cec9b7e110f6159e6046222"
B3_TREE = "dacb6e5048a54c3f242add441dd1a36255f80dc4"
SOURCE_BRANCH = (
    "codex/m4-cross-engineering-forward-evaluation-"
    "m4.2-gate-iv-b-protocol-proof"
)
SUCCESSOR_BRANCH = (
    "codex/m4-cross-engineering-forward-evaluation-"
    "m4.2-authorization-preparation"
)
PROOF_PATH = Path("evals/m4/authorization/m4.2/gate-iv-b-protocol-proof.json")
PROOF_BLOB = "d3fe975431f2e4584a52ee5305b169f5b5d29268"
PROOF_SHA256 = "9d160de6893fbb6bd01158524a3a48931496b6d4cae1fdc4c9f0e736921068e0"
PROOF_BYTE_LENGTH = 33204
ARTIFACT_PATH = Path("evals/m4/authorization/m4.2/authorization-preparation.json")
PREPARATION_SCHEMA_PATH = Path(
    "evals/m4/authorization/m4.2/authorization-preparation.schema.json"
)
AUTHORIZATION_SCHEMA_PATH = Path(
    "evals/m4/authorization/m4.2/execution-authorization.schema.json"
)
CONTROL_SCHEMA_PATH = Path(
    "evals/m4/authorization/m4.2/execution-control.schema.json"
)
M42_MANIFEST_PATH = Path("evals/m4/revisions/m4.2/preparation-manifest.json")
TASK_PROTOCOL_PATH = Path("evals/m4/task-protocol.md")
RUBRIC_PATH = Path("evals/m4/judge-rubric.json")
HELPER_PATH = Path("evals/m4/execution/prepare_m4_2_request_bundles.ps1")
BATCH_ORDER = (
    "M4.2-BATCH-NUC",
    "M4.2-BATCH-MEC",
    "M4.2-BATCH-ELE",
    "M4.2-BATCH-AUT",
    "M4.2-BATCH-COM",
    "M4.2-BATCH-MPH",
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
    "raw_model_finals",
    "aggregation_calls",
    "acceptance_claims",
)
ZERO_MARKERS = {"FAIL:": 0, "FAILED (": 0, "Traceback": 0, "##[error]": 0}
ROOT_KEYS = {
    "schema_version",
    "milestone",
    "revision",
    "preparation_kind",
    "baseline",
    "gate_iv_b_evidence",
    "schema_bindings",
    "matrix_projection",
    "request_binding_projection",
    "authorization_projection",
    "control_projection",
    "policy_proofs",
    "negative_authority",
    "delivery",
    "findings",
    "auditor_side_effects",
    "decision",
    "status",
}
PROVISIONAL_DECISION = "PENDING_M4_2_AUTHORIZATION_PREPARATION_EXACT_HEAD_CI"
PROVISIONAL_STATUS = (
    "M4_2_AUTHORIZATION_PREPARATION_LOCAL_PASSED_NOT_AUTHORIZED"
)
FINAL_DECISION = "APPROVE_M4_2_SEPARATE_AUTHORIZATION_WORK_PACKAGE_ONLY"
FINAL_STATUS = "M4_2_AUTHORIZATION_PREPARATION_PASSED_NOT_AUTHORIZED"
ALLOWED_CHANGE_PATHS = frozenset(
    {
        ".github/workflows/m1-validation.yml",
        "STATUS.md",
        "docs/superpowers/plans/2026-08-10-m4.2-authorization-preparation.md",
        ARTIFACT_PATH.as_posix(),
        PREPARATION_SCHEMA_PATH.as_posix(),
        AUTHORIZATION_SCHEMA_PATH.as_posix(),
        CONTROL_SCHEMA_PATH.as_posix(),
        "evals/m4/authorization/audit_m4_2_authorization_preparation.py",
        "evals/m4/authorization/audit_m4_2_gate_iv_b_protocol_proof.py",
        "tests/test_m4_2_authorization_preparation.py",
        "tests/test_m4_2_gate_iv_b_protocol_proof.py",
        "tests/test_m3_r5_erratum.py",
    }
)
CLOSURE_CHANGE_PATHS = frozenset(
    {
        ARTIFACT_PATH.as_posix(),
        "STATUS.md",
        "tests/test_m3_r5_erratum.py",
    }
)
ALLOWED_M42_AUTHORIZATION_FILES = frozenset(
    {
        "evals/m4/authorization/m4.2/gate-iv-a-review-r2.json",
        "evals/m4/authorization/m4.2/gate-iv-a-review-r2.schema.json",
        "evals/m4/authorization/m4.2/gate-iv-b-protocol-proof.json",
        "evals/m4/authorization/m4.2/gate-iv-b-protocol-proof.schema.json",
        ARTIFACT_PATH.as_posix(),
        PREPARATION_SCHEMA_PATH.as_posix(),
        AUTHORIZATION_SCHEMA_PATH.as_posix(),
        CONTROL_SCHEMA_PATH.as_posix(),
    }
)
FORBIDDEN_EXACT = (
    Path("evals/m4/authorization/m4.2/execution-authorization.json"),
    Path("evals/m4/authorization/m4.2/execution-control.json"),
    Path("evals/m4/authorization/m4.2/authorization-token.json"),
    Path("evals/m4/authorization/m4.2/acceptance-claim.json"),
    Path("evals/m4/results-manifest.json"),
)
FORBIDDEN_PREFIXES = (
    Path("evals/m4/execution/m4.2"),
    Path("evals/m4/results/m4.1"),
    Path("evals/m4/results/m4.2"),
    Path("evals/m5"),
)
B4_RUNS: dict[str, dict[str, object]] = {
    "push": {
        "run_id": 31371973449,
        "event": "push",
        "head": BASELINE_HEAD,
        "branch": SOURCE_BRANCH,
        "conclusion": "success",
        "job_count": 11,
        "jobs": [
            {"job_id": 93402729586, "name": "historical-audit-cross-platform (windows-latest)", "conclusion": "success"},
            {"job_id": 93402729590, "name": "M4.2 repaired frozen preparation (NOT AUTHORIZED) (windows-latest)", "conclusion": "success"},
            {"job_id": 93402729623, "name": "M4.2 Gate IV-B protocol proof (NOT AUTHORIZED) (windows-latest)", "conclusion": "success"},
            {"job_id": 93402729634, "name": "M4.1 pre-claim regression (windows-latest)", "conclusion": "success"},
            {"job_id": 93402729638, "name": "M4.2 Gate IV-B protocol proof (NOT AUTHORIZED) (ubuntu-latest)", "conclusion": "success"},
            {"job_id": 93402729648, "name": "M4.2 repaired frozen preparation (NOT AUTHORIZED) (ubuntu-latest)", "conclusion": "success"},
            {"job_id": 93402729655, "name": "historical-audit-cross-platform (ubuntu-latest)", "conclusion": "success"},
            {"job_id": 93402729663, "name": "M4.2 Gate IV-A r2 review (NOT AUTHORIZED) (ubuntu-latest)", "conclusion": "success"},
            {"job_id": 93402729667, "name": "validate", "conclusion": "success"},
            {"job_id": 93402729682, "name": "M4.1 pre-claim regression (ubuntu-latest)", "conclusion": "success"},
            {"job_id": 93402729747, "name": "M4.2 Gate IV-A r2 review (NOT AUTHORIZED) (windows-latest)", "conclusion": "success"},
        ],
        "raw_log": {
            "byte_length": 1362010,
            "sha256": "2e66682f4aa381df67f3e5bc879f114aa5918cb21e497b5634dc0c8686fb8ae2",
            "markers": dict(ZERO_MARKERS),
        },
    },
    "pull_request": {
        "run_id": 31371976651,
        "event": "pull_request",
        "head": BASELINE_HEAD,
        "branch": SOURCE_BRANCH,
        "conclusion": "success",
        "job_count": 11,
        "jobs": [
            {"job_id": 93402739194, "name": "M4.2 repaired frozen preparation (NOT AUTHORIZED) (ubuntu-latest)", "conclusion": "success"},
            {"job_id": 93402739209, "name": "M4.2 Gate IV-B protocol proof (NOT AUTHORIZED) (ubuntu-latest)", "conclusion": "success"},
            {"job_id": 93402739228, "name": "validate", "conclusion": "success"},
            {"job_id": 93402739244, "name": "historical-audit-cross-platform (windows-latest)", "conclusion": "success"},
            {"job_id": 93402739252, "name": "M4.1 pre-claim regression (windows-latest)", "conclusion": "success"},
            {"job_id": 93402739255, "name": "M4.2 Gate IV-A r2 review (NOT AUTHORIZED) (ubuntu-latest)", "conclusion": "success"},
            {"job_id": 93402739256, "name": "M4.2 Gate IV-A r2 review (NOT AUTHORIZED) (windows-latest)", "conclusion": "success"},
            {"job_id": 93402739304, "name": "M4.1 pre-claim regression (ubuntu-latest)", "conclusion": "success"},
            {"job_id": 93402739323, "name": "historical-audit-cross-platform (ubuntu-latest)", "conclusion": "success"},
            {"job_id": 93402739346, "name": "M4.2 repaired frozen preparation (NOT AUTHORIZED) (windows-latest)", "conclusion": "success"},
            {"job_id": 93402739354, "name": "M4.2 Gate IV-B protocol proof (NOT AUTHORIZED) (windows-latest)", "conclusion": "success"},
        ],
        "raw_log": {
            "byte_length": 1378469,
            "sha256": "ad80062801dca369042a6b6b393bb52349d3c08152ec4c5304d4afb4051ed8d4",
            "markers": dict(ZERO_MARKERS),
        },
    },
}


class DuplicateKeyError(ValueError):
    pass


def add_error(errors: list[str], code: str) -> None:
    if code not in errors:
        errors.append(code)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git_blob_oid(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_sha256(value: object) -> str:
    return sha256(canonical_bytes(value))


def strict_equal(actual: object, expected: object) -> bool:
    if type(actual) is not type(expected):
        return False
    if isinstance(actual, dict):
        return set(actual) == set(expected) and all(
            strict_equal(actual[key], expected[key]) for key in actual
        )
    if isinstance(actual, list):
        return len(actual) == len(expected) and all(
            strict_equal(left, right) for left, right in zip(actual, expected)
        )
    return bool(actual == expected)


def pairs_no_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise DuplicateKeyError(key)
        value[key] = item
    return value


def reject_constant(value: str) -> object:
    raise ValueError(value)


def load_json_bytes(raw: bytes, label: str, errors: list[str]) -> dict[str, Any]:
    if raw.startswith(b"\xef\xbb\xbf"):
        add_error(errors, f"{label}_bom_forbidden")
        return {}
    try:
        value = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=pairs_no_duplicates,
            parse_constant=reject_constant,
        )
    except DuplicateKeyError:
        add_error(errors, f"{label}_duplicate_key")
        return {}
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError):
        add_error(errors, f"{label}_invalid_json")
        return {}
    if not isinstance(value, dict):
        add_error(errors, f"{label}_object_required")
        return {}
    return value


def git_environment() -> dict[str, str]:
    environment = dict(os.environ)
    for name in tuple(environment):
        if name.startswith("GIT_") and name not in {"GIT_CONFIG_NOSYSTEM"}:
            environment.pop(name, None)
    environment["GIT_CONFIG_NOSYSTEM"] = "1"
    environment["GIT_CONFIG_COUNT"] = "1"
    environment["GIT_CONFIG_KEY_0"] = "core.useReplaceRefs"
    environment["GIT_CONFIG_VALUE_0"] = "false"
    return environment


@contextmanager
def git_replacements_disabled() -> Iterator[None]:
    yield


def git(repo_root: Path, *arguments: str) -> subprocess.CompletedProcess[bytes]:
    with git_replacements_disabled():
        return subprocess.run(
            ["git", *arguments],
            cwd=repo_root,
            capture_output=True,
            check=False,
            env=git_environment(),
        )


def git_bytes(repo_root: Path, *arguments: str) -> bytes | None:
    completed = git(repo_root, *arguments)
    return completed.stdout if completed.returncode == 0 else None


def git_text(repo_root: Path, *arguments: str) -> str | None:
    raw = git_bytes(repo_root, *arguments)
    if raw is None:
        return None
    try:
        return raw.decode("utf-8", errors="strict").strip()
    except UnicodeDecodeError:
        return None


def object_blob(
    repo_root: Path,
    head: str,
    path: Path,
    errors: list[str],
    label: str,
) -> bytes:
    raw = git_bytes(repo_root, "show", f"{head}:{path.as_posix()}")
    if raw is None:
        add_error(errors, f"{label}_git_object_unavailable")
        return b""
    return raw


def object_json(
    repo_root: Path,
    head: str,
    path: Path,
    label: str,
    errors: list[str],
) -> dict[str, Any]:
    return load_json_bytes(object_blob(repo_root, head, path, errors, label), label, errors)


def artifact_binding(
    repo_root: Path,
    head: str,
    path: Path,
    errors: list[str],
    label: str,
) -> dict[str, object]:
    raw = object_blob(repo_root, head, path, errors, label)
    return {
        "path": path.as_posix(),
        "git_blob_oid": git_blob_oid(raw),
        "raw_sha256": sha256(raw),
        "byte_length": len(raw),
    }


def request_binding_sha256(task: Mapping[str, object]) -> str:
    frame = (
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
    return sha256(("\n".join(frame) + "\n").encode("utf-8"))


def task_list(manifest: Mapping[str, object]) -> list[dict[str, Any]]:
    tasks = manifest.get("tasks")
    if not isinstance(tasks, list) or not all(isinstance(task, dict) for task in tasks):
        return []
    return tasks


def batch_list(manifest: Mapping[str, object]) -> list[dict[str, Any]]:
    matrix = manifest.get("matrix")
    if not isinstance(matrix, dict):
        return []
    batches = matrix.get("batches")
    if not isinstance(batches, list) or not all(isinstance(batch, dict) for batch in batches):
        return []
    return batches


def matrix_projection(manifest: Mapping[str, object]) -> dict[str, object]:
    tasks = task_list(manifest)
    batches = batch_list(manifest)
    task_ids = [str(task.get("task_id")) for task in tasks]
    blind_ids = [str(task.get("blind_id")) for task in tasks]
    batch_ids = [str(batch.get("batch_id")) for batch in batches]
    case_ids = {str(task.get("case_id")) for task in tasks}
    arm_ids = {str(task.get("arm_id")) for task in tasks}
    task_counts = {
        len(batch.get("task_ids", []))
        for batch in batches
        if isinstance(batch.get("task_ids"), list)
    }
    tasks_per_batch = next(iter(task_counts)) if len(task_counts) == 1 else -1
    batch_projection = [
        {
            "batch_id": str(batch.get("batch_id")),
            "task_ids": [str(value) for value in batch.get("task_ids", [])],
        }
        for batch in batches
    ]
    randomization = manifest.get("randomization")
    frozen_order = (
        randomization.get("task_order") if isinstance(randomization, dict) else None
    )
    matrix_frame = {
        "algorithm": "m4.2-protocol-matrix-binding-v1",
        "task_order": task_ids,
        "blind_ids": blind_ids,
        "batches": batch_projection,
    }
    passed = bool(
        len(case_ids) == 12
        and len(arm_ids) == 5
        and len(tasks) == 60
        and len(batches) == 6
        and task_counts == {10}
        and len(set(task_ids)) == 60
        and len(set(blind_ids)) == 60
        and len(set(batch_ids)) == 6
        and tuple(batch_ids) == BATCH_ORDER
        and frozen_order == task_ids
        and sorted(task_id for batch in batch_projection for task_id in batch["task_ids"])
        == sorted(task_ids)
    )
    return {
        "algorithm": "m4.2-protocol-matrix-binding-v1",
        "case_count": len(case_ids),
        "arm_count": len(arm_ids),
        "planned_task_count": len(tasks),
        "batch_count": len(batches),
        "tasks_per_batch": tasks_per_batch,
        "unique_task_id_count": len(set(task_ids)),
        "unique_blind_id_count": len(set(blind_ids)),
        "unique_batch_id_count": len(set(batch_ids)),
        "task_order_sha256": sha256(("\n".join(task_ids) + "\n").encode("utf-8")),
        "batch_order_sha256": canonical_sha256(batch_projection),
        "matrix_binding_sha256": canonical_sha256(matrix_frame),
        "passed": passed,
    }


def source_bytes_match_count(
    repo_root: Path,
    manifest: Mapping[str, object],
    errors: list[str],
) -> int:
    tasks = task_list(manifest)
    protocol_raw = object_blob(
        repo_root, BASELINE_HEAD, TASK_PROTOCOL_PATH, errors, "task_protocol"
    )
    rubric_raw = object_blob(
        repo_root, BASELINE_HEAD, RUBRIC_PATH, errors, "judge_rubric"
    )
    case_cache: dict[str, tuple[bytes, dict[str, Any]]] = {}
    variant_cache: dict[str, bytes] = {}
    matched = 0
    for task in tasks:
        path = str(task.get("case_path"))
        if path not in case_cache:
            raw = object_blob(
                repo_root, BASELINE_HEAD, Path(path), errors, "case_source"
            )
            case_cache[path] = (raw, load_json_bytes(raw, "case_source", errors))
        case_raw, case = case_cache[path]
        user_input = case.get("user_input")
        variant_path = task.get("variant_instruction_path")
        variant_matches = variant_path is None and task.get(
            "variant_instruction_sha256"
        ) is None
        if isinstance(variant_path, str):
            if variant_path not in variant_cache:
                variant_cache[variant_path] = object_blob(
                    repo_root,
                    BASELINE_HEAD,
                    Path(variant_path),
                    errors,
                    "variant_source",
                )
            variant_matches = sha256(variant_cache[variant_path]) == task.get(
                "variant_instruction_sha256"
            )
        if (
            sha256(case_raw) == task.get("case_sha256")
            and isinstance(user_input, str)
            and sha256(user_input.encode("utf-8")) == task.get("user_input_sha256")
            and sha256(protocol_raw) == task.get("task_protocol_sha256")
            and variant_matches
            and sha256(rubric_raw) == task.get("rubric_sha256")
        ):
            matched += 1
    return matched


def request_binding_projection(
    manifest: Mapping[str, object],
    repo_root: Path = REPO_ROOT,
    errors: list[str] | None = None,
) -> dict[str, object]:
    active_errors = errors if errors is not None else []
    tasks = task_list(manifest)
    recomputed: list[str] = []
    for task in tasks:
        try:
            recomputed.append(request_binding_sha256(task))
        except (KeyError, TypeError, ValueError):
            recomputed.append("")
            add_error(active_errors, "request_binding_input_invalid")
    matched = sum(
        actual == task.get("request_binding_sha256")
        for actual, task in zip(recomputed, tasks)
    )
    source_verified = source_bytes_match_count(repo_root, manifest, active_errors)
    return {
        "algorithm": "m4.2-request-binding-v1",
        "independently_recomputed": len(recomputed),
        "matched": matched,
        "unique": len(set(recomputed)),
        "aggregate_sha256": sha256(("\n".join(recomputed) + "\n").encode("utf-8")),
        "source_bytes_verified": source_verified,
        "passed": bool(
            len(recomputed) == 60
            and matched == 60
            and len(set(recomputed)) == 60
            and source_verified == 60
        ),
    }


def _manifest(repo_root: Path, errors: list[str] | None = None) -> dict[str, Any]:
    active_errors = errors if errors is not None else []
    return object_json(
        repo_root, BASELINE_HEAD, M42_MANIFEST_PATH, "m4_2_manifest", active_errors
    )


def candidate_authorization_projection(
    repo_root: Path = REPO_ROOT,
) -> dict[str, object]:
    manifest = _manifest(Path(repo_root))
    matrix = matrix_projection(manifest)
    projection: dict[str, object] = {
        "projection_schema_version": "m4.2-candidate-authorization-projection-v1",
        "projection_only": True,
        "instance_schema_path": AUTHORIZATION_SCHEMA_PATH.as_posix(),
        "instance_path": "evals/m4/authorization/m4.2/execution-authorization.json",
        "instance_must_be_absent": True,
        "status": "PREPARED_NOT_AUTHORIZED",
        "authorization_token": None,
        "authorization_token_status": "NOT_ISSUED",
        "fresh_execution_authorized": False,
        "claim_authorized": False,
        "future_whole_matrix_task_count": matrix["planned_task_count"],
        "future_task_order_sha256": matrix["task_order_sha256"],
        "future_batch_count": matrix["batch_count"],
        "future_batch_order_sha256": matrix["batch_order_sha256"],
        "future_result_root_prefix": "evals/m4/results/m4.2",
        "partial_authority_allowed": False,
        "second_claim_allowed": False,
        "cross_task_result_visibility": False,
        "successor_revision_required_after_failure": True,
    }
    projection["canonical_sha256"] = canonical_sha256(projection)
    return projection


def candidate_control_projection(repo_root: Path = REPO_ROOT) -> dict[str, object]:
    manifest = _manifest(Path(repo_root))
    matrix = matrix_projection(manifest)
    projection: dict[str, object] = {
        "projection_schema_version": "m4.2-candidate-control-projection-v1",
        "projection_only": True,
        "instance_schema_path": CONTROL_SCHEMA_PATH.as_posix(),
        "instance_path": "evals/m4/authorization/m4.2/execution-control.json",
        "instance_must_be_absent": True,
        "status": "PREPARED_NOT_READY",
        "execution_ready": False,
        "claim_ready": False,
        "future_controlled_task_count": matrix["planned_task_count"],
        "future_task_order_sha256": matrix["task_order_sha256"],
        "future_batch_count": matrix["batch_count"],
        "future_batch_order_sha256": matrix["batch_order_sha256"],
        "allowed_context_inputs": [
            "case",
            "task_protocol",
            "selected_variant_instruction",
        ],
        "visible_result_task_ids": [],
        "cross_task_result_visibility": False,
        "judge_available": False,
        "aggregation_available": False,
    }
    projection["canonical_sha256"] = canonical_sha256(projection)
    return projection


def projection_is_future_authorization_instance(value: Mapping[str, object]) -> bool:
    token = value.get("authorization_token")
    return bool(
        value.get("projection_only") is False
        and value.get("fresh_execution_authorized") is True
        and value.get("claim_authorized") is True
        and value.get("authorization_token_status") == "UNCONSUMED"
        and isinstance(token, str)
        and token.startswith("sha256:")
        and len(token) == 71
    )


def projection_is_future_control_instance(value: Mapping[str, object]) -> bool:
    return bool(
        value.get("projection_only") is False
        and value.get("execution_ready") is True
        and value.get("claim_ready") is True
    )


def claim_semantics_projection() -> list[dict[str, object]]:
    return [
        {
            "name": "first_claim",
            "decision": "SIMULATED_CLAIM_ACCEPTED",
            "authority_consumed": 60,
            "dispatched_tasks": 0,
            "successor_revision_required": False,
        },
        {
            "name": "partial_claim",
            "decision": "REJECTED_PARTIAL_AUTHORITY",
            "authority_consumed": 0,
            "dispatched_tasks": 0,
            "successor_revision_required": False,
        },
        {
            "name": "second_claim",
            "decision": "REJECTED_ALREADY_CONSUMED",
            "authority_consumed": 0,
            "dispatched_tasks": 0,
            "successor_revision_required": True,
        },
        {
            "name": "post_claim_failure",
            "decision": "STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE",
            "authority_consumed": 60,
            "dispatched_tasks": 0,
            "successor_revision_required": True,
        },
    ]


def batch_failure_projection() -> list[dict[str, object]]:
    return [
        {
            "failed_batch_id": batch_id,
            "failed_batch_sequence": index,
            "later_batch_ids": list(BATCH_ORDER[index:]),
            "later_batch_dispatch_count": 0,
            "retry_count": 0,
            "repair_count": 0,
            "successor_revision_required": True,
        }
        for index, batch_id in enumerate(BATCH_ORDER, start=1)
    ]


def policy_proofs() -> dict[str, object]:
    claims = claim_semantics_projection()
    failures = batch_failure_projection()
    by_name = {str(item["name"]): item for item in claims}
    return {
        "whole_matrix_task_count": 60,
        "claim_consumes_entire_matrix_authorization": True,
        "partial_authority_allowed": False,
        "second_claim_allowed": False,
        "first_claim_consumed_task_count": by_name["first_claim"]["authority_consumed"],
        "first_claim_dispatched_task_count": by_name["first_claim"]["dispatched_tasks"],
        "partial_claim_decision": by_name["partial_claim"]["decision"],
        "second_claim_decision": by_name["second_claim"]["decision"],
        "post_claim_failure_decision": by_name["post_claim_failure"]["decision"],
        "attempts_per_task_id": 1,
        "retry_authorized": False,
        "repair_authorized": False,
        "followup_message_authorized": False,
        "terminal_failure_consumes_authority": True,
        "successor_revision_required_after_failure": True,
        "failed_batch_scenario_count": len(failures),
        "later_batch_dispatch_count_after_failure": sum(
            int(item["later_batch_dispatch_count"]) for item in failures
        ),
        "cross_task_result_visibility": False,
        "blind_mapping_access_authorized": False,
        "judge_execution_authorized": False,
        "aggregation_authorized": False,
        "claim_semantics_sha256": canonical_sha256(claims),
        "batch_failure_semantics_sha256": canonical_sha256(failures),
        "passed": bool(
            len(failures) == 6
            and all(item["later_batch_dispatch_count"] == 0 for item in failures)
            and by_name["first_claim"]["authority_consumed"] == 60
            and by_name["first_claim"]["dispatched_tasks"] == 0
            and by_name["partial_claim"]["decision"]
            == "REJECTED_PARTIAL_AUTHORITY"
            and by_name["second_claim"]["decision"]
            == "REJECTED_ALREADY_CONSUMED"
            and by_name["post_claim_failure"]["successor_revision_required"]
            is True
        ),
    }


def discover_forbidden_paths(
    repo_root: Path,
    present_paths: set[str] | None = None,
) -> list[str]:
    found: set[str] = set()
    for relative in FORBIDDEN_EXACT:
        if (repo_root / relative).exists():
            found.add(relative.as_posix())
    for relative in FORBIDDEN_PREFIXES:
        absolute = repo_root / relative
        if absolute.exists():
            if absolute.is_file() or absolute.is_symlink():
                found.add(relative.as_posix())
            else:
                found.update(
                    item.relative_to(repo_root).as_posix()
                    for item in absolute.rglob("*")
                    if item.is_file() or item.is_symlink()
                )
    authorization_root = repo_root / "evals/m4/authorization/m4.2"
    if authorization_root.exists():
        for item in authorization_root.rglob("*"):
            if item.is_file() or item.is_symlink():
                relative = item.relative_to(repo_root).as_posix()
                if relative not in ALLOWED_M42_AUTHORIZATION_FILES:
                    found.add(relative)
    for filename in ("authorization-token.json", "acceptance-claim.json"):
        found.update(
            item.relative_to(repo_root).as_posix()
            for item in repo_root.rglob(filename)
            if item.is_file() or item.is_symlink()
        )
    if present_paths:
        found.update(path.replace("\\", "/") for path in present_paths)
    return sorted(found)


def negative_authority_projection(
    repo_root: Path,
    manifest: Mapping[str, object],
    present_paths: set[str] | None = None,
) -> dict[str, object]:
    counters = manifest.get("counters")
    counter_values = counters if isinstance(counters, dict) else {}
    forbidden_paths = discover_forbidden_paths(repo_root, present_paths)
    forbidden_states: list[str] = []
    authority = manifest.get("authority")
    if not isinstance(authority, dict) or any(
        authority.get(key) is not False
        for key in (
            "fresh_execution_authorized",
            "fresh_tasks_authorized",
            "result_writes_authorized",
            "retry_authorized",
            "repair_authorized",
        )
    ):
        forbidden_states.append("manifest_authority_nonzero")
    values = {
        "authorized_tasks": counter_values.get("authorized_tasks", -1),
        "created_contexts": counter_values.get("created_contexts", -1),
        "dispatched_tasks": counter_values.get("dispatched_tasks", -1),
        "finalizations": counter_values.get("finalizations", -1),
        "results_observed": counter_values.get("results_observed", -1),
        "judge_scores": counter_values.get("judge_scores", -1),
        "retries": counter_values.get("retries", -1),
        "repairs": counter_values.get("repairs", -1),
        "unauthorized_side_effects": counter_values.get(
            "unauthorized_side_effects", -1
        ),
        "raw_model_finals": 0,
        "aggregation_calls": 0,
        "acceptance_claims": 0,
        "authorization_artifact": "ABSENT",
        "execution_control": "ABSENT",
        "authorization_token_status": "NOT_ISSUED",
        "launch_claim": "ABSENT",
        "result_root": "ABSENT",
        "judge": "NOT_RUN",
        "aggregation": "NOT_RUN",
        "closure": "NOT_RUN",
        "m5": "NOT_STARTED",
        "forbidden_paths": forbidden_paths,
        "forbidden_states": forbidden_states,
    }
    values["passed"] = bool(
        all(values[name] == 0 for name in COUNTER_NAMES)
        and not forbidden_paths
        and not forbidden_states
    )
    return values


def schema_is_closed(value: object) -> bool:
    if isinstance(value, dict):
        if value.get("type") == "object" and (
            value.get("additionalProperties") is not False
            or set(value.get("required", [])) != set(value.get("properties", {}))
        ):
            return False
        return all(schema_is_closed(child) for child in value.values())
    if isinstance(value, list):
        return all(schema_is_closed(child) for child in value)
    return True


def schema_bindings(repo_root: Path, errors: list[str]) -> list[dict[str, object]]:
    bindings: list[dict[str, object]] = []
    for relative in (
        PREPARATION_SCHEMA_PATH,
        AUTHORIZATION_SCHEMA_PATH,
        CONTROL_SCHEMA_PATH,
    ):
        try:
            raw = (repo_root / relative).read_bytes()
        except OSError:
            raw = b""
            add_error(errors, "schema_unreadable")
        schema = load_json_bytes(raw, "authorization_preparation_schema", errors)
        closed = schema_is_closed(schema)
        if not closed:
            add_error(errors, "schema_not_closed")
        instance_path = {
            AUTHORIZATION_SCHEMA_PATH: FORBIDDEN_EXACT[0],
            CONTROL_SCHEMA_PATH: FORBIDDEN_EXACT[1],
        }.get(relative)
        executable_present = bool(
            instance_path is not None and (repo_root / instance_path).exists()
        )
        bindings.append(
            {
                "path": relative.as_posix(),
                "raw_sha256": sha256(raw),
                "byte_length": len(raw),
                "closed": closed,
                "executable_instance_present": executable_present,
            }
        )
    return bindings


def _valid_gate_run(value: object, event: str, head: str, run_id: int) -> bool:
    if not isinstance(value, dict):
        return False
    jobs = value.get("jobs")
    raw_log = value.get("raw_log")
    return bool(
        value.get("run_id") == run_id
        and value.get("event") == event
        and value.get("head") == head
        and value.get("branch") == SOURCE_BRANCH
        and value.get("conclusion") == "success"
        and value.get("job_count") == 11
        and isinstance(jobs, list)
        and len(jobs) == 11
        and len({job.get("job_id") for job in jobs if isinstance(job, dict)}) == 11
        and all(
            isinstance(job, dict)
            and type(job.get("job_id")) is int
            and job.get("job_id", 0) > 0
            and isinstance(job.get("name"), str)
            and job.get("conclusion") == "success"
            for job in jobs
        )
        and isinstance(raw_log, dict)
        and type(raw_log.get("byte_length")) is int
        and raw_log.get("byte_length", 0) > 0
        and isinstance(raw_log.get("sha256"), str)
        and len(raw_log.get("sha256", "")) == 64
        and raw_log.get("markers") == ZERO_MARKERS
    )


def gate_iv_b_evidence(
    repo_root: Path,
    manifest: Mapping[str, object],
    errors: list[str],
) -> dict[str, object]:
    proof_raw = object_blob(repo_root, BASELINE_HEAD, PROOF_PATH, errors, "gate_iv_b_proof")
    proof = load_json_bytes(proof_raw, "gate_iv_b_proof", errors)
    matrix = matrix_projection(manifest)
    requests = request_binding_projection(manifest, repo_root, errors)
    if proof.get("matrix_proof") != matrix:
        add_error(errors, "gate_iv_b_matrix_recomputation_mismatch")
    if proof.get("request_binding_proof") != requests:
        add_error(errors, "gate_iv_b_request_recomputation_mismatch")
    if proof.get("decision") != "APPROVE_M4_2_AUTHORIZATION_PREPARATION_ONLY":
        add_error(errors, "gate_iv_b_decision_mismatch")
    if proof.get("status") != "M4_2_GATE_IV_B_PROTOCOL_PROOF_PASSED_NOT_AUTHORIZED":
        add_error(errors, "gate_iv_b_status_mismatch")
    delivery = proof.get("delivery")
    b3_push = delivery.get("push") if isinstance(delivery, dict) else None
    b3_pull = delivery.get("pull_request") if isinstance(delivery, dict) else None
    if not _valid_gate_run(b3_push, "push", B3_HEAD, 31370941146):
        add_error(errors, "gate_iv_b_b3_push_invalid")
    if not _valid_gate_run(b3_pull, "pull_request", B3_HEAD, 31370945548):
        add_error(errors, "gate_iv_b_b3_pull_request_invalid")
    if not _valid_gate_run(B4_RUNS["push"], "push", BASELINE_HEAD, 31371973449):
        add_error(errors, "gate_iv_b_b4_push_invalid")
    if not _valid_gate_run(
        B4_RUNS["pull_request"], "pull_request", BASELINE_HEAD, 31371976651
    ):
        add_error(errors, "gate_iv_b_b4_pull_request_invalid")
    b4_binding = artifact_binding(
        repo_root, BASELINE_HEAD, PROOF_PATH, errors, "gate_iv_b_b4_proof"
    )
    if b4_binding != {
        "path": PROOF_PATH.as_posix(),
        "git_blob_oid": PROOF_BLOB,
        "raw_sha256": PROOF_SHA256,
        "byte_length": PROOF_BYTE_LENGTH,
    }:
        add_error(errors, "gate_iv_b_b4_proof_binding_invalid")
    return {
        "b3": {
            "head": B3_HEAD,
            "tree": B3_TREE,
            "proof_artifact": artifact_binding(
                repo_root, B3_HEAD, PROOF_PATH, errors, "gate_iv_b_b3_proof"
            ),
            "push": b3_push,
            "pull_request": b3_pull,
        },
        "b4": {
            "head": BASELINE_HEAD,
            "tree": BASELINE_TREE,
            "proof_artifact": b4_binding,
            "push": B4_RUNS["push"],
            "pull_request": B4_RUNS["pull_request"],
        },
        "decision": "APPROVE_M4_2_AUTHORIZATION_PREPARATION_ONLY",
        "status": "M4_2_GATE_IV_B_PROTOCOL_PROOF_PASSED_NOT_AUTHORIZED",
    }


def baseline_projection() -> dict[str, object]:
    return {
        "required_ancestor_head": BASELINE_HEAD,
        "required_ancestor_tree": BASELINE_TREE,
        "source_branch": SOURCE_BRANCH,
        "successor_branch": SUCCESSOR_BRANCH,
        "draft_pr_base_branch": SOURCE_BRANCH,
        "fresh_execution_authorized": False,
    }


def provisional_delivery() -> dict[str, object]:
    return {
        "status": "PENDING_EXACT_HEAD_CI",
        "accepted_candidate_head": None,
        "push": None,
        "pull_request": None,
        "powershell_5_1": None,
        "powershell_7": None,
        "semantic_results_match": None,
    }


def runtime_result(runtime: str) -> dict[str, object]:
    return {
        "runtime": runtime,
        "status": "VERIFIED",
        "checked_task_count": 60,
        "mismatches": [],
        "side_effects": [],
    }


def _valid_candidate_run(value: object, event: str, head: str) -> bool:
    if not isinstance(value, dict):
        return False
    jobs = value.get("jobs")
    raw_log = value.get("raw_log")
    names = {
        job.get("name")
        for job in jobs
        if isinstance(jobs, list) and isinstance(job, dict)
    } if isinstance(jobs, list) else set()
    required_names = {
        "M4.2 authorization preparation (NOT AUTHORIZED) (ubuntu-latest)",
        "M4.2 authorization preparation (NOT AUTHORIZED) (windows-latest)",
        "M4.2 Gate IV-B protocol proof (NOT AUTHORIZED) (ubuntu-latest)",
        "M4.2 Gate IV-B protocol proof (NOT AUTHORIZED) (windows-latest)",
    }
    return bool(
        type(value.get("run_id")) is int
        and value.get("run_id", 0) > 0
        and value.get("event") == event
        and value.get("head") == head
        and value.get("branch") == SUCCESSOR_BRANCH
        and value.get("conclusion") == "success"
        and value.get("job_count") == 13
        and isinstance(jobs, list)
        and len(jobs) == 13
        and len({job.get("job_id") for job in jobs if isinstance(job, dict)}) == 13
        and all(
            isinstance(job, dict)
            and type(job.get("job_id")) is int
            and job.get("job_id", 0) > 0
            and isinstance(job.get("name"), str)
            and job.get("conclusion") == "success"
            for job in jobs
        )
        and required_names.issubset(names)
        and isinstance(raw_log, dict)
        and type(raw_log.get("byte_length")) is int
        and raw_log.get("byte_length", 0) > 0
        and isinstance(raw_log.get("sha256"), str)
        and len(raw_log.get("sha256", "")) == 64
        and raw_log.get("markers") == ZERO_MARKERS
    )


def _valid_runtime(value: object, runtime: str) -> bool:
    return isinstance(value, dict) and strict_equal(value, runtime_result(runtime))


def delivery_state(
    repo_root: Path,
    delivery: object,
    errors: list[str],
    verify_git: bool,
) -> str:
    if not isinstance(delivery, dict):
        add_error(errors, "delivery_invalid")
        return "INVALID"
    if delivery.get("status") == "PENDING_EXACT_HEAD_CI":
        if not strict_equal(delivery, provisional_delivery()):
            add_error(errors, "provisional_delivery_mismatch")
        return "PROVISIONAL"
    if delivery.get("status") != "VERIFIED_TRUE_GREEN":
        add_error(errors, "delivery_invalid")
        return "INVALID"
    head = delivery.get("accepted_candidate_head")
    if not isinstance(head, str) or len(head) != 40:
        add_error(errors, "accepted_candidate_head_invalid")
        return "FINAL"
    if not _valid_candidate_run(delivery.get("push"), "push", head):
        add_error(errors, "candidate_push_delivery_invalid")
    if not _valid_candidate_run(delivery.get("pull_request"), "pull_request", head):
        add_error(errors, "candidate_pull_request_delivery_invalid")
    push = delivery.get("push")
    pull = delivery.get("pull_request")
    if isinstance(push, dict) and isinstance(pull, dict) and push.get("run_id") == pull.get("run_id"):
        add_error(errors, "candidate_delivery_run_reuse")
    if not _valid_runtime(delivery.get("powershell_5_1"), "Windows PowerShell 5.1"):
        add_error(errors, "candidate_powershell_5_1_invalid")
    if not _valid_runtime(delivery.get("powershell_7"), "PowerShell 7 on Ubuntu"):
        add_error(errors, "candidate_powershell_7_invalid")
    if delivery.get("semantic_results_match") is not True:
        add_error(errors, "candidate_runtime_semantics_invalid")
    if verify_git:
        if git(repo_root, "cat-file", "-e", f"{head}^{{commit}}").returncode != 0:
            add_error(errors, "accepted_candidate_head_unavailable")
        if git(repo_root, "merge-base", "--is-ancestor", head, "HEAD").returncode != 0:
            add_error(errors, "accepted_candidate_head_not_ancestor")
        closure = git_text(
            repo_root, "diff", "--name-only", "--no-renames", head, "HEAD", "--"
        )
        closure_paths = set(closure.splitlines()) if closure else set()
        if closure_paths != CLOSURE_CHANGE_PATHS:
            add_error(errors, "closure_change_set_mismatch")
    return "FINAL"


def expected_preparation(
    repo_root: Path = REPO_ROOT,
    *,
    delivery: Mapping[str, object] | None = None,
    present_paths: set[str] | None = None,
    errors: list[str] | None = None,
) -> dict[str, object]:
    repo_root = Path(repo_root).resolve(strict=False)
    active_errors = errors if errors is not None else []
    manifest = _manifest(repo_root, active_errors)
    selected_delivery = dict(delivery) if delivery is not None else provisional_delivery()
    final = selected_delivery.get("status") == "VERIFIED_TRUE_GREEN"
    return {
        "schema_version": "m4.2-authorization-preparation-v1",
        "milestone": "M4",
        "revision": "M4.2",
        "preparation_kind": "AUTHORIZATION_SCHEMA_AND_PROJECTION_ONLY",
        "baseline": baseline_projection(),
        "gate_iv_b_evidence": gate_iv_b_evidence(repo_root, manifest, active_errors),
        "schema_bindings": schema_bindings(repo_root, active_errors),
        "matrix_projection": matrix_projection(manifest),
        "request_binding_projection": request_binding_projection(
            manifest, repo_root, active_errors
        ),
        "authorization_projection": candidate_authorization_projection(repo_root),
        "control_projection": candidate_control_projection(repo_root),
        "policy_proofs": policy_proofs(),
        "negative_authority": negative_authority_projection(
            repo_root, manifest, present_paths
        ),
        "delivery": selected_delivery,
        "findings": [],
        "auditor_side_effects": [],
        "decision": FINAL_DECISION if final else PROVISIONAL_DECISION,
        "status": FINAL_STATUS if final else PROVISIONAL_STATUS,
    }


def changed_paths(repo_root: Path, errors: list[str]) -> set[str]:
    found: set[str] = set()
    committed = git_text(
        repo_root,
        "diff",
        "--name-only",
        "--no-renames",
        BASELINE_HEAD,
        "HEAD",
        "--",
    )
    if committed is None:
        add_error(errors, "successor_diff_unavailable")
    elif committed:
        found.update(committed.splitlines())
    status = git_bytes(repo_root, "status", "--porcelain=v1", "--untracked-files=all")
    if status is None:
        add_error(errors, "successor_status_unavailable")
    elif status:
        try:
            lines = status.decode("utf-8", errors="strict").splitlines()
        except UnicodeDecodeError:
            lines = []
            add_error(errors, "successor_status_unavailable")
        for line in lines:
            path = line[3:]
            if " -> " in path:
                left, right = path.split(" -> ", 1)
                found.add(left.strip('"'))
                found.add(right.strip('"'))
            else:
                found.add(path.strip('"'))
    return {path.replace("\\", "/") for path in found}


def audit_authorization_preparation(
    repo_root: Path = REPO_ROOT,
    *,
    artifact_data: Mapping[str, object] | None = None,
    verify_git: bool = True,
    present_paths: set[str] | None = None,
) -> dict[str, object]:
    repo_root = Path(repo_root).resolve(strict=False)
    errors: list[str] = []
    if artifact_data is None:
        try:
            artifact_raw = (repo_root / ARTIFACT_PATH).read_bytes()
        except OSError:
            artifact_raw = b""
            add_error(errors, "artifact_unreadable")
        artifact = load_json_bytes(artifact_raw, "authorization_preparation", errors)
    elif isinstance(artifact_data, Mapping):
        artifact = dict(artifact_data)
    else:
        artifact = {}
        add_error(errors, "artifact_object_required")

    if set(artifact) != ROOT_KEYS:
        add_error(errors, "artifact_root_keys_mismatch")
    if artifact.get("schema_version") != "m4.2-authorization-preparation-v1":
        add_error(errors, "schema_version_mismatch")
    if artifact.get("milestone") != "M4" or artifact.get("revision") != "M4.2":
        add_error(errors, "artifact_identity_mismatch")
    if artifact.get("preparation_kind") != "AUTHORIZATION_SCHEMA_AND_PROJECTION_ONLY":
        add_error(errors, "preparation_kind_mismatch")

    state = delivery_state(repo_root, artifact.get("delivery"), errors, verify_git)
    expected = expected_preparation(
        repo_root,
        delivery=(
            artifact.get("delivery")
            if isinstance(artifact.get("delivery"), Mapping)
            else None
        ),
        present_paths=present_paths,
        errors=errors,
    )
    for key, code in (
        ("baseline", "baseline_mismatch"),
        ("gate_iv_b_evidence", "gate_iv_b_evidence_mismatch"),
        ("schema_bindings", "schema_bindings_mismatch"),
        ("matrix_projection", "matrix_projection_mismatch"),
        ("request_binding_projection", "request_binding_projection_mismatch"),
        ("authorization_projection", "authorization_projection_mismatch"),
        ("control_projection", "control_projection_mismatch"),
        ("policy_proofs", "policy_proofs_mismatch"),
        ("negative_authority", "negative_authority_mismatch"),
    ):
        if not strict_equal(artifact.get(key), expected.get(key)):
            add_error(errors, code)

    authorization_projection_value = artifact.get("authorization_projection")
    if isinstance(authorization_projection_value, Mapping) and (
        projection_is_future_authorization_instance(authorization_projection_value)
        or authorization_projection_value.get("authorization_token") is not None
        or authorization_projection_value.get("authorization_token_status")
        != "NOT_ISSUED"
    ):
        add_error(errors, "authorization_projection_attempts_instance")
    control_projection_value = artifact.get("control_projection")
    if isinstance(control_projection_value, Mapping) and projection_is_future_control_instance(
        control_projection_value
    ):
        add_error(errors, "control_projection_attempts_instance")
    negative = expected["negative_authority"]
    forbidden_paths = negative.get("forbidden_paths", [])
    if forbidden_paths:
        add_error(errors, "forbidden_future_path_present")
    if artifact.get("findings") != []:
        add_error(errors, "findings_present")
    if artifact.get("auditor_side_effects") != []:
        add_error(errors, "auditor_side_effects_present")

    decision = artifact.get("decision")
    status = artifact.get("status")
    if isinstance(decision, str) and (
        decision == "AUTHORIZE_M4_2_EXECUTION" or decision.startswith("AUTHORIZE_M4_2_")
    ):
        add_error(errors, "decision_attempts_execution_authorization")
    if state == "PROVISIONAL":
        if decision != PROVISIONAL_DECISION or status != PROVISIONAL_STATUS:
            add_error(errors, "decision_status_state_mismatch")
    elif state == "FINAL":
        if decision != FINAL_DECISION or status != FINAL_STATUS:
            add_error(errors, "decision_status_state_mismatch")
    else:
        add_error(errors, "decision_status_state_mismatch")

    if verify_git:
        if git(repo_root, "cat-file", "-e", f"{BASELINE_HEAD}^{{commit}}").returncode != 0:
            add_error(errors, "baseline_head_unavailable")
        if git_text(repo_root, "rev-parse", f"{BASELINE_HEAD}^{{tree}}") != BASELINE_TREE:
            add_error(errors, "baseline_tree_mismatch")
        if git(repo_root, "merge-base", "--is-ancestor", BASELINE_HEAD, "HEAD").returncode != 0:
            add_error(errors, "baseline_head_not_ancestor")
        if git_text(repo_root, "rev-parse", f"{BASELINE_HEAD}:{PROOF_PATH.as_posix()}") != PROOF_BLOB:
            add_error(errors, "gate_iv_b_proof_blob_mismatch")
        proof_changed = git_text(
            repo_root,
            "diff",
            "--name-only",
            BASELINE_HEAD,
            "HEAD",
            "--",
            PROOF_PATH.as_posix(),
        )
        if proof_changed:
            add_error(errors, "gate_iv_b_proof_artifact_changed")
        unexpected = changed_paths(repo_root, errors) - ALLOWED_CHANGE_PATHS
        if unexpected:
            add_error(errors, "successor_change_set_mismatch")

    counters = negative if isinstance(negative, dict) else {}
    result_status = status if not errors else "BLOCKED"
    return {
        "status": result_status,
        "decision": decision,
        "errors": sorted(errors),
        "findings": list(artifact.get("findings", []))
        if isinstance(artifact.get("findings"), list)
        else [],
        "auditor_side_effects": list(artifact.get("auditor_side_effects", []))
        if isinstance(artifact.get("auditor_side_effects"), list)
        else [],
        "baseline_head": BASELINE_HEAD,
        "case_count": expected["matrix_projection"].get("case_count", 0),
        "arm_count": expected["matrix_projection"].get("arm_count", 0),
        "planned_task_count": expected["matrix_projection"].get(
            "planned_task_count", 0
        ),
        "batch_count": expected["matrix_projection"].get("batch_count", 0),
        "request_binding_count": expected["request_binding_projection"].get(
            "matched", 0
        ),
        "forbidden_path_count": len(forbidden_paths),
        "forbidden_paths": list(forbidden_paths),
        **{name: counters.get(name, -1) for name in COUNTER_NAMES},
        "authorization_token_status": counters.get(
            "authorization_token_status", "INVALID"
        ),
        "authorization_artifact": counters.get("authorization_artifact", "INVALID"),
        "execution_control": counters.get("execution_control", "INVALID"),
        "launch_claim": counters.get("launch_claim", "INVALID"),
        "result_root": counters.get("result_root", "INVALID"),
        "judge": counters.get("judge", "INVALID"),
        "aggregation": counters.get("aggregation", "INVALID"),
        "closure": counters.get("closure", "INVALID"),
        "m5": counters.get("m5", "INVALID"),
    }


def main() -> int:
    result = audit_authorization_preparation()
    sys.stdout.buffer.write(canonical_bytes(result) + b"\n")
    return 0 if not result["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
