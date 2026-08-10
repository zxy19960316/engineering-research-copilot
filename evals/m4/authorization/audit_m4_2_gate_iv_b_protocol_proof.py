#!/usr/bin/env python3
"""Read-only offline proof of the M4.2 authorization/claim/dispatch protocol."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Mapping, Sequence


REPO_ROOT = Path(__file__).resolve().parents[3]
BASELINE_HEAD = "988b4332504549df2038f51532175effd696a445"
BASELINE_TREE = "38b1aeacd54b5e5a9ac115be1816206a7a3f8a4f"
R2_BRANCH = (
    "codex/m4-cross-engineering-forward-evaluation-m4.2-gate-iv-a-r2"
)
PROOF_BRANCH = (
    "codex/m4-cross-engineering-forward-evaluation-"
    "m4.2-gate-iv-b-protocol-proof"
)
PRIOR_REVIEW_HEAD = "ac6cc70714a90f73b4de09eaf0e521e699296890"
REPAIR_HEAD = "44d1004da1cbb2681ee0d423d1748f98fbaa13e4"

PROOF_PATH = Path(
    "evals/m4/authorization/m4.2/gate-iv-b-protocol-proof.json"
)
SCHEMA_PATH = Path(
    "evals/m4/authorization/m4.2/gate-iv-b-protocol-proof.schema.json"
)
R2_REVIEW_PATH = Path(
    "evals/m4/authorization/m4.2/gate-iv-a-review-r2.json"
)
R2_SCHEMA_PATH = Path(
    "evals/m4/authorization/m4.2/gate-iv-a-review-r2.schema.json"
)
PRIOR_REVIEW_PATH = Path(
    "evals/m4/authorization/m4.2/gate-iv-a-review.json"
)
M42_MANIFEST_PATH = Path("evals/m4/revisions/m4.2/preparation-manifest.json")
M41_MANIFEST_PATH = Path("evals/m4/revisions/m4.1/preparation-manifest.json")
M40_MANIFEST_PATH = Path("evals/m4/preparation-manifest.json")
HELPER_PATH = Path("evals/m4/execution/prepare_m4_2_request_bundles.ps1")
TASK_PROTOCOL_PATH = Path("evals/m4/task-protocol.md")
RUBRIC_PATH = Path("evals/m4/judge-rubric.json")
M41_CLAIM_PATH = Path("evals/m4/execution/m4.1/launch-claim.json")
M41_TERMINAL_PATH = Path("evals/m4/execution/m4.1/execution-terminal.json")

CASE_PATHS = tuple(
    Path(f"evals/m4/cases/{name}.json")
    for name in (
        "automation-control-a",
        "automation-control-b",
        "computer-data-a",
        "computer-data-b",
        "electrical-a",
        "electrical-b",
        "mechanical-a",
        "mechanical-b",
        "multiphysics-a",
        "multiphysics-b",
        "nuclear-a",
        "nuclear-b",
    )
)
VARIANT_PATHS = tuple(
    Path(f"evals/m4/variants/{arm}/instructions.md")
    for arm in ("A1", "A2", "A3", "F")
)
REPAIR_PATHS = (
    Path(".gitattributes"),
    Path("docs/superpowers/plans/2026-08-10-m4.2-windows-lifecycle-repair.md"),
    Path("evals/m4/audit_m4_2_preparation.py"),
    Path("tests/test_m3_raw_sha_eol_policy.py"),
)
SOURCE_ARTIFACT_SPECS = (
    (BASELINE_HEAD, R2_REVIEW_PATH),
    (BASELINE_HEAD, R2_SCHEMA_PATH),
    (PRIOR_REVIEW_HEAD, PRIOR_REVIEW_PATH),
    *((REPAIR_HEAD, path) for path in REPAIR_PATHS),
    (BASELINE_HEAD, M42_MANIFEST_PATH),
    (BASELINE_HEAD, M41_MANIFEST_PATH),
    (BASELINE_HEAD, M40_MANIFEST_PATH),
    (BASELINE_HEAD, HELPER_PATH),
    (BASELINE_HEAD, TASK_PROTOCOL_PATH),
    (BASELINE_HEAD, RUBRIC_PATH),
    (BASELINE_HEAD, M41_CLAIM_PATH),
    (BASELINE_HEAD, M41_TERMINAL_PATH),
    *((BASELINE_HEAD, path) for path in CASE_PATHS),
    *((BASELINE_HEAD, path) for path in VARIANT_PATHS),
)

BATCH_ORDER = (
    "M4.2-BATCH-NUC",
    "M4.2-BATCH-MEC",
    "M4.2-BATCH-ELE",
    "M4.2-BATCH-AUT",
    "M4.2-BATCH-COM",
    "M4.2-BATCH-MPH",
)
PRECONDITION_NAMES = (
    "model_binding_matches",
    "project_matches",
    "worktree_matches",
    "request_bindings_match",
    "head_is_fresh",
    "prerequisites_present",
)
PRECONDITION_SCENARIOS = (
    ("model_binding_mismatch", "model_binding_matches"),
    ("project_mismatch", "project_matches"),
    ("worktree_mismatch", "worktree_matches"),
    ("request_binding_mismatch", "request_bindings_match"),
    ("stale_head", "head_is_fresh"),
    ("missing_prerequisite", "prerequisites_present"),
)

EXPECTED_AUTHORITY = {
    "fresh_execution_authorized": False,
    "fresh_tasks_authorized": False,
    "result_writes_authorized": False,
    "retry_authorized": False,
    "repair_authorized": False,
    "authorization_artifact": None,
    "model_binding_status": "UNBOUND_UNTIL_SEPARATE_AUTHORIZATION",
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
)
EXPECTED_COUNTERS = {name: 0 for name in COUNTER_NAMES}
EXPECTED_CANDIDATE_FIXTURE = {
    "fixture_kind": "NON_EXECUTABLE_PROTOCOL_FIXTURE",
    "fresh_execution_authorized": False,
    "result_writes_authorized": False,
    "authorization_token_status": "NOT_ISSUED",
    "claim_authorized": False,
    "authorized_task_count": 0,
    "matrix_authority_task_count_if_later_authorized": 60,
    "partial_authorization_allowed": False,
}
ROOT_KEYS = {
    "schema_version",
    "milestone",
    "revision",
    "proof_kind",
    "baseline",
    "source_artifacts",
    "matrix_proof",
    "request_binding_proof",
    "candidate_authorization_fixture",
    "claim_semantics",
    "pre_dispatch_proofs",
    "batch_failure_proofs",
    "visibility_proof",
    "negative_authority",
    "delivery",
    "findings",
    "reviewer_side_effects",
    "decision",
    "status",
}
PROVISIONAL_DECISION = "PENDING_M4_2_GATE_IV_B_EXACT_HEAD_CI"
PROVISIONAL_STATUS = (
    "M4_2_GATE_IV_B_LOCAL_PROTOCOL_PROOF_PASSED_PENDING_EXACT_HEAD_CI"
)
FINAL_DECISION = "APPROVE_M4_2_AUTHORIZATION_PREPARATION_ONLY"
FINAL_STATUS = "M4_2_GATE_IV_B_PROTOCOL_PROOF_PASSED_NOT_AUTHORIZED"
ZERO_MARKERS = {"FAIL:": 0, "FAILED (": 0, "Traceback": 0, "##[error]": 0}

_OBJECT_BLOB_CACHE: dict[tuple[str, str, str], bytes] = {}

ALLOWED_CHANGE_PATHS = frozenset(
    {
        ".github/workflows/m1-validation.yml",
        "STATUS.md",
        "docs/superpowers/plans/2026-08-10-m4.2-gate-iv-b-protocol-proof.md",
        PROOF_PATH.as_posix(),
        SCHEMA_PATH.as_posix(),
        "evals/m4/authorization/audit_m4_2_gate_iv_b_protocol_proof.py",
        "tests/test_m3_r5_erratum.py",
        "tests/test_m4_2_gate_iv_b_protocol_proof.py",
    }
)
CLOSURE_CHANGE_PATHS = frozenset(
    {
        PROOF_PATH.as_posix(),
        "STATUS.md",
        "tests/test_m3_r5_erratum.py",
    }
)


class DuplicateKeyError(ValueError):
    pass


def add_error(errors: list[str], code: str) -> None:
    if code not in errors:
        errors.append(code)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git_blob_oid(raw: bytes) -> str:
    return hashlib.sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest()


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def canonical_sha256(value: object) -> str:
    return sha256(canonical_bytes(value))


def strict_equal(actual: object, expected: object) -> bool:
    if type(actual) is not type(expected):
        return False
    if isinstance(expected, dict):
        return set(actual) == set(expected) and all(
            strict_equal(actual[key], expected[key]) for key in expected
        )
    if isinstance(expected, list):
        return len(actual) == len(expected) and all(
            strict_equal(left, right) for left, right in zip(actual, expected)
        )
    return actual == expected


def pairs_no_duplicates(
    pairs: Sequence[tuple[str, object]],
) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(key)
        result[key] = value
    return result


def reject_constant(value: str) -> object:
    raise ValueError(f"non_finite_json_constant:{value}")


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
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        add_error(errors, f"{label}_invalid_json")
        return {}
    if not isinstance(value, dict):
        add_error(errors, f"{label}_not_object")
        return {}
    return value


def git_environment() -> dict[str, str]:
    environment = dict(os.environ)
    environment["GIT_NO_REPLACE_OBJECTS"] = "1"
    for key in (
        "GIT_DIR",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_COMMON_DIR",
        "GIT_WORK_TREE",
    ):
        environment.pop(key, None)
    return environment


def git(repo_root: Path, *arguments: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *arguments],
        cwd=repo_root,
        env=git_environment(),
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
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
    key = (str(repo_root), head, path.as_posix())
    if key in _OBJECT_BLOB_CACHE:
        return _OBJECT_BLOB_CACHE[key]
    raw = git_bytes(repo_root, "show", f"{head}:{path.as_posix()}")
    if raw is None:
        add_error(errors, f"{label}_git_object_missing")
        return b""
    _OBJECT_BLOB_CACHE[key] = raw
    return raw


def object_json(
    repo_root: Path,
    head: str,
    path: Path,
    label: str,
    errors: list[str],
) -> dict[str, Any]:
    return load_json_bytes(
        object_blob(repo_root, head, path, errors, label), label, errors
    )


def artifact_binding(
    repo_root: Path,
    head: str,
    path: Path,
    errors: list[str],
) -> dict[str, object]:
    raw = object_blob(repo_root, head, path, errors, "source_artifact")
    return {
        "head": head,
        "path": path.as_posix(),
        "git_blob_oid": git_blob_oid(raw),
        "raw_sha256": sha256(raw),
        "byte_length": len(raw),
    }


def source_artifact_bindings(
    repo_root: Path = REPO_ROOT,
    errors: list[str] | None = None,
) -> list[dict[str, object]]:
    active_errors = errors if errors is not None else []
    return [
        artifact_binding(repo_root, head, path, active_errors)
        for head, path in SOURCE_ARTIFACT_SPECS
    ]


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


def _task_list(manifest: Mapping[str, object]) -> list[dict[str, Any]]:
    tasks = manifest.get("tasks")
    if not isinstance(tasks, list) or not all(isinstance(task, dict) for task in tasks):
        return []
    return tasks


def _batch_list(manifest: Mapping[str, object]) -> list[dict[str, Any]]:
    matrix = manifest.get("matrix")
    if not isinstance(matrix, dict):
        return []
    batches = matrix.get("batches")
    if not isinstance(batches, list) or not all(
        isinstance(batch, dict) for batch in batches
    ):
        return []
    return batches


def matrix_projection(manifest: Mapping[str, object]) -> dict[str, object]:
    tasks = _task_list(manifest)
    batches = _batch_list(manifest)
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
    matrix_frame = {
        "algorithm": "m4.2-protocol-matrix-binding-v1",
        "task_order": task_ids,
        "blind_ids": blind_ids,
        "batches": batch_projection,
    }
    randomization = manifest.get("randomization")
    frozen_order = (
        randomization.get("task_order") if isinstance(randomization, dict) else None
    )
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


def _source_bytes_match_count(
    repo_root: Path,
    manifest: Mapping[str, object],
    errors: list[str],
) -> int:
    tasks = _task_list(manifest)
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
            case_cache[path] = (
                raw,
                load_json_bytes(raw, "case_source", errors),
            )
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
    tasks = _task_list(manifest)
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
    source_bytes_verified = _source_bytes_match_count(
        repo_root, manifest, active_errors
    )
    aggregate = sha256(("\n".join(recomputed) + "\n").encode("utf-8"))
    return {
        "algorithm": "m4.2-request-binding-v1",
        "independently_recomputed": len(recomputed),
        "matched": matched,
        "unique": len(set(recomputed)),
        "aggregate_sha256": aggregate,
        "source_bytes_verified": source_bytes_verified,
        "passed": bool(
            len(recomputed) == 60
            and matched == 60
            and len(set(recomputed)) == 60
            and source_bytes_verified == 60
        ),
    }


def _transition(
    decision: str,
    state_before: str,
    state_after: str,
    claim_count_delta: int,
    consumed_count: int,
    successor_revision_required: bool,
) -> dict[str, object]:
    return {
        "decision": decision,
        "virtual_state_before": state_before,
        "virtual_state_after": state_after,
        "simulated_claim_count_delta": claim_count_delta,
        "simulated_matrix_authority_consumed_count": consumed_count,
        "simulated_dispatched_tasks": 0,
        "simulated_retry_count": 0,
        "simulated_repair_count": 0,
        "simulated_followup_count": 0,
        "successor_revision_required": successor_revision_required,
    }


def simulate_claim(
    *,
    state: str,
    preconditions: Mapping[str, bool],
    requested_task_count: int,
    post_claim_failure: bool = False,
) -> dict[str, object]:
    if state != "VIRTUAL_UNCONSUMED":
        return _transition(
            "REJECTED_ALREADY_CONSUMED", state, state, 0, 0, True
        )
    if type(requested_task_count) is not int or requested_task_count != 60:
        return _transition(
            "REJECTED_PARTIAL_AUTHORITY", state, state, 0, 0, False
        )
    if set(preconditions) != set(PRECONDITION_NAMES) or any(
        type(preconditions[name]) is not bool for name in PRECONDITION_NAMES
    ):
        return _transition("REJECTED_PRE_DISPATCH", state, state, 0, 0, False)
    if not all(preconditions.values()):
        return _transition("REJECTED_PRE_DISPATCH", state, state, 0, 0, False)
    if post_claim_failure:
        return _transition(
            "STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE",
            state,
            "VIRTUAL_TERMINAL_FAILED",
            1,
            60,
            True,
        )
    return _transition(
        "SIMULATED_CLAIM_ACCEPTED",
        state,
        "VIRTUAL_CONSUMED",
        1,
        60,
        False,
    )


def _claim_input(
    state: str,
    requested_task_count: int,
    *,
    failed_precondition: str | None = None,
    post_claim_failure: bool = False,
) -> dict[str, object]:
    preconditions = {name: True for name in PRECONDITION_NAMES}
    if failed_precondition is not None:
        preconditions[failed_precondition] = False
    return {
        "virtual_state": state,
        "preconditions": preconditions,
        "requested_task_count": requested_task_count,
        "post_claim_failure": post_claim_failure,
    }


def _evaluate_claim_input(value: Mapping[str, object]) -> dict[str, object]:
    preconditions = value.get("preconditions")
    return simulate_claim(
        state=str(value.get("virtual_state")),
        preconditions=(
            preconditions if isinstance(preconditions, Mapping) else {}
        ),
        requested_task_count=value.get("requested_task_count", -1),
        post_claim_failure=value.get("post_claim_failure") is True,
    )


def claim_semantics_projection() -> dict[str, object]:
    definitions = (
        ("first_claim", _claim_input("VIRTUAL_UNCONSUMED", 60)),
        ("second_claim", _claim_input("VIRTUAL_CONSUMED", 60)),
        ("partial_authority", _claim_input("VIRTUAL_UNCONSUMED", 59)),
        (
            "post_claim_failure",
            _claim_input(
                "VIRTUAL_UNCONSUMED", 60, post_claim_failure=True
            ),
        ),
    )
    scenarios = [
        {"name": name, "input": value, "output": _evaluate_claim_input(value)}
        for name, value in definitions
    ]
    return {
        "simulator": "m4.2-offline-claim-state-machine-v1",
        "scenarios": scenarios,
        "passed": all(
            scenario["output"]["simulated_dispatched_tasks"] == 0
            for scenario in scenarios
        ),
    }


def pre_dispatch_projection() -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for name, failed in PRECONDITION_SCENARIOS:
        value = _claim_input(
            "VIRTUAL_UNCONSUMED", 60, failed_precondition=failed
        )
        result.append(
            {
                "name": name,
                "failed_precondition": failed,
                "input": value,
                "output": _evaluate_claim_input(value),
            }
        )
    return result


def simulate_batch_failure(batch_sequence: int) -> dict[str, object]:
    if type(batch_sequence) is not int or not 1 <= batch_sequence <= len(BATCH_ORDER):
        raise ValueError("batch_sequence_invalid")
    index = batch_sequence - 1
    return {
        "decision": "STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE",
        "failed_batch": BATCH_ORDER[index],
        "failed_batch_sequence": batch_sequence,
        "completed_prior_batches": list(BATCH_ORDER[:index]),
        "simulated_tasks_dispatched_before_failure": index * 10,
        "later_batches_not_started": list(BATCH_ORDER[index + 1 :]),
        "simulated_retry_count": 0,
        "simulated_repair_count": 0,
        "simulated_followup_count": 0,
        "successor_revision_required": True,
    }


def batch_failure_projection() -> list[dict[str, object]]:
    return [
        {
            "input": {"failed_batch_sequence": sequence},
            "output": simulate_batch_failure(sequence),
        }
        for sequence in range(1, len(BATCH_ORDER) + 1)
    ]


def visibility_projection() -> dict[str, object]:
    return {
        "task_context_allowed_inputs": [
            "case",
            "task_protocol",
            "selected_variant_instruction",
        ],
        "visible_result_task_ids": [],
        "cross_task_results_visible": False,
        "blind_mapping_available_to_task": False,
        "judge_available": False,
        "unblinding_available": False,
        "aggregation_available": False,
        "passed": True,
    }


def discover_forbidden_paths(
    repo_root: Path,
    present_paths: set[str] | None = None,
) -> list[str]:
    found: set[str] = set()
    exact = (
        Path("evals/m4/authorization/m4.2/execution-authorization.json"),
        Path("evals/m4/authorization/m4.2/execution-control.json"),
        Path("evals/m4/authorization/m4.2/authorization-token.json"),
        Path("evals/m4/authorization/m4.2/acceptance-claim.json"),
        Path("evals/m4/results-manifest.json"),
    )
    prefixes = (
        Path("evals/m4/execution/m4.2"),
        Path("evals/m4/results/m4.1"),
        Path("evals/m4/results/m4.2"),
        Path("evals/m5"),
    )
    for relative in exact:
        if (repo_root / relative).exists():
            found.add(relative.as_posix())
    for relative in prefixes:
        absolute = repo_root / relative
        if absolute.exists():
            if absolute.is_file() or absolute.is_symlink():
                found.add(relative.as_posix())
            else:
                for item in absolute.rglob("*"):
                    if item.is_file() or item.is_symlink():
                        found.add(item.relative_to(repo_root).as_posix())
    authorization_root = repo_root / "evals/m4/authorization/m4.2"
    allowed = {
        (repo_root / R2_REVIEW_PATH).resolve(strict=False),
        (repo_root / R2_SCHEMA_PATH).resolve(strict=False),
        (repo_root / PROOF_PATH).resolve(strict=False),
        (repo_root / SCHEMA_PATH).resolve(strict=False),
    }
    if authorization_root.exists():
        for item in authorization_root.rglob("*"):
            if (item.is_file() or item.is_symlink()) and item.resolve(
                strict=False
            ) not in allowed:
                found.add(item.relative_to(repo_root).as_posix())
    if present_paths:
        found.update(path.replace("\\", "/") for path in present_paths)
    return sorted(found)


def baseline_projection(
    repo_root: Path,
    errors: list[str],
) -> dict[str, object]:
    r2_raw = object_blob(
        repo_root, BASELINE_HEAD, R2_REVIEW_PATH, errors, "gate_iv_a_r2"
    )
    r2 = load_json_bytes(r2_raw, "gate_iv_a_r2", errors)
    prior_raw = object_blob(
        repo_root,
        PRIOR_REVIEW_HEAD,
        PRIOR_REVIEW_PATH,
        errors,
        "prior_blocked_review",
    )
    prior = load_json_bytes(prior_raw, "prior_blocked_review", errors)
    prior_section = r2.get("prior_blocked_review")
    repair = r2.get("repair_evidence")
    repair_ci = repair.get("ci") if isinstance(repair, dict) else None
    delivery = r2.get("review_delivery")
    zero_state = r2.get("zero_state")
    lifecycle = r2.get("lifecycle_requirements")
    prior_findings = prior.get("findings")
    return {
        "required_ancestor_head": BASELINE_HEAD,
        "required_ancestor_tree": BASELINE_TREE,
        "source_branch": R2_BRANCH,
        "gate_iv_a_r2_artifact": {
            "head": BASELINE_HEAD,
            "path": R2_REVIEW_PATH.as_posix(),
            "git_blob_oid": git_blob_oid(r2_raw),
            "raw_sha256": sha256(r2_raw),
            "byte_length": len(r2_raw),
        },
        "gate_iv_a_r2_decision": r2.get("decision"),
        "gate_iv_a_r2_status": r2.get("status"),
        "fresh_execution_authorized": (
            lifecycle.get("fresh_execution_authorized")
            if isinstance(lifecycle, dict)
            else None
        ),
        "prior_blocked_review": {
            "head": PRIOR_REVIEW_HEAD,
            "pull_request": (
                prior_section.get("pull_request")
                if isinstance(prior_section, dict)
                else None
            ),
            "decision": prior.get("decision"),
            "status": prior.get("status"),
            "finding_count": (
                len(prior_findings) if isinstance(prior_findings, list) else -1
            ),
            "preserved": bool(
                isinstance(prior_section, dict)
                and prior_section.get("head") == PRIOR_REVIEW_HEAD
                and prior_section.get("decision") == prior.get("decision")
            ),
        },
        "repair_evidence": {
            "head": REPAIR_HEAD,
            "pull_request": (
                repair_ci.get("pull_request")
                if isinstance(repair_ci, dict)
                else None
            ),
            "push_run_id": (
                repair_ci.get("push", {}).get("run_id")
                if isinstance(repair_ci, dict)
                and isinstance(repair_ci.get("push"), dict)
                else None
            ),
            "pull_request_run_id": (
                repair_ci.get("pull_request_run", {}).get("run_id")
                if isinstance(repair_ci, dict)
                and isinstance(repair_ci.get("pull_request_run"), dict)
                else None
            ),
            "preserved": bool(
                isinstance(repair, dict) and repair.get("parent_head") is not None
            ),
        },
        "r2_delivery": {
            "accepted_review_head": (
                delivery.get("accepted_review_head")
                if isinstance(delivery, dict)
                else None
            ),
            "push_run_id": (
                delivery.get("push", {}).get("run_id")
                if isinstance(delivery, dict)
                and isinstance(delivery.get("push"), dict)
                else None
            ),
            "pull_request_run_id": (
                delivery.get("pull_request", {}).get("run_id")
                if isinstance(delivery, dict)
                and isinstance(delivery.get("pull_request"), dict)
                else None
            ),
            "preserved": bool(
                isinstance(delivery, dict)
                and delivery.get("status") == "VERIFIED_TRUE_GREEN"
            ),
        },
        "zero_state_preserved": bool(
            isinstance(zero_state, dict)
            and zero_state.get("passed") is True
            and zero_state.get("authorization") == "ABSENT"
            and zero_state.get("claim") == "ABSENT"
            and zero_state.get("tasks") == 0
            and zero_state.get("results") == 0
        ),
    }


def negative_authority_projection(
    repo_root: Path,
    manifest: Mapping[str, object],
    present_paths: set[str] | None = None,
) -> dict[str, object]:
    authority = manifest.get("authority")
    counters = manifest.get("counters")
    forbidden_paths = discover_forbidden_paths(repo_root, present_paths)
    forbidden_states: list[str] = []
    if not strict_equal(authority, EXPECTED_AUTHORITY):
        forbidden_states.append("preparation_authority_mismatch")
    if not strict_equal(counters, EXPECTED_COUNTERS):
        forbidden_states.append("preparation_counters_mismatch")
    values = dict(counters) if isinstance(counters, dict) else {}
    result: dict[str, object] = {
        **{name: values.get(name, -1) for name in COUNTER_NAMES},
        "raw_model_finals": 0,
        "aggregation_calls": 0,
        "acceptance_claims": 0,
        "authorization_artifact": "ABSENT" if not forbidden_paths else "PRESENT",
        "execution_control": "ABSENT" if not forbidden_paths else "PRESENT",
        "authorization_token_status": "NOT_ISSUED",
        "launch_claim": "ABSENT" if not forbidden_paths else "PRESENT",
        "result_root": "ABSENT" if not forbidden_paths else "PRESENT",
        "judge": "NOT_RUN",
        "aggregation": "NOT_RUN",
        "closure": "NOT_RUN",
        "m5": "NOT_STARTED",
        "forbidden_paths": forbidden_paths,
        "forbidden_states": forbidden_states,
        "passed": not forbidden_paths and not forbidden_states,
    }
    return result


def provisional_delivery() -> dict[str, object]:
    return {
        "status": "PENDING_EXACT_HEAD_CI",
        "accepted_proof_head": None,
        "push": None,
        "pull_request": None,
        "powershell_5_1": None,
        "powershell_7": None,
        "semantic_results_match": None,
    }


def expected_proof(
    repo_root: Path = REPO_ROOT,
    *,
    delivery: Mapping[str, object] | None = None,
    present_paths: set[str] | None = None,
    errors: list[str] | None = None,
) -> dict[str, object]:
    active_errors = errors if errors is not None else []
    manifest = object_json(
        repo_root, BASELINE_HEAD, M42_MANIFEST_PATH, "m4_2_manifest", active_errors
    )
    selected_delivery = dict(delivery) if delivery is not None else provisional_delivery()
    is_final = selected_delivery.get("status") == "VERIFIED_TRUE_GREEN"
    return {
        "schema_version": "m4.2-gate-iv-b-protocol-proof-v1",
        "milestone": "M4",
        "revision": "M4.2",
        "proof_kind": "OFFLINE_PROTOCOL_PROOF_NOT_EXECUTION_AUTHORIZATION",
        "baseline": baseline_projection(repo_root, active_errors),
        "source_artifacts": source_artifact_bindings(repo_root, active_errors),
        "matrix_proof": matrix_projection(manifest),
        "request_binding_proof": request_binding_projection(
            manifest, repo_root, active_errors
        ),
        "candidate_authorization_fixture": dict(EXPECTED_CANDIDATE_FIXTURE),
        "claim_semantics": claim_semantics_projection(),
        "pre_dispatch_proofs": pre_dispatch_projection(),
        "batch_failure_proofs": batch_failure_projection(),
        "visibility_proof": visibility_projection(),
        "negative_authority": negative_authority_projection(
            repo_root, manifest, present_paths
        ),
        "delivery": selected_delivery,
        "findings": [],
        "reviewer_side_effects": [],
        "decision": FINAL_DECISION if is_final else PROVISIONAL_DECISION,
        "status": FINAL_STATUS if is_final else PROVISIONAL_STATUS,
    }


def schema_contract(schema: Mapping[str, object]) -> bool:
    if (
        schema.get("type") != "object"
        or schema.get("additionalProperties") is not False
        or set(schema.get("required", [])) != ROOT_KEYS
        or set(schema.get("properties", {})) != ROOT_KEYS
    ):
        return False
    definitions = schema.get("$defs")
    if not isinstance(definitions, dict):
        return False
    for definition in definitions.values():
        if isinstance(definition, dict) and definition.get("type") == "object":
            if definition.get("additionalProperties") is not False:
                return False
            if set(definition.get("required", [])) != set(
                definition.get("properties", {})
            ):
                return False
    return True


def _runtime_result_valid(value: object, runtime: str) -> bool:
    return bool(
        isinstance(value, dict)
        and set(value)
        == {"runtime", "status", "checked_task_count", "mismatches", "side_effects"}
        and value.get("runtime") == runtime
        and value.get("status") == "VERIFIED"
        and value.get("checked_task_count") == 60
        and value.get("mismatches") == []
        and value.get("side_effects") == []
    )


def _delivery_run_valid(value: object, event: str, head: str) -> bool:
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
        "M4.2 Gate IV-B protocol proof (NOT AUTHORIZED) (windows-latest)",
        "M4.2 Gate IV-B protocol proof (NOT AUTHORIZED) (ubuntu-latest)",
    }
    return bool(
        type(value.get("run_id")) is int
        and value.get("run_id", 0) > 0
        and value.get("event") == event
        and value.get("head") == head
        and value.get("branch") == PROOF_BRANCH
        and value.get("conclusion") == "success"
        and type(value.get("job_count")) is int
        and value.get("job_count", 0) >= 2
        and isinstance(jobs, list)
        and len(jobs) == value.get("job_count")
        and len({job.get("job_id") for job in jobs if isinstance(job, dict)})
        == len(jobs)
        and all(
            isinstance(job, dict)
            and type(job.get("job_id")) is int
            and job.get("job_id", 0) > 0
            and isinstance(job.get("name"), str)
            and bool(job.get("name"))
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


def delivery_state(
    repo_root: Path,
    delivery: object,
    errors: list[str],
    verify_git: bool,
) -> str:
    expected_keys = {
        "status",
        "accepted_proof_head",
        "push",
        "pull_request",
        "powershell_5_1",
        "powershell_7",
        "semantic_results_match",
    }
    if not isinstance(delivery, dict) or set(delivery) != expected_keys:
        add_error(errors, "delivery_keys_mismatch")
        return "INVALID"
    state = delivery.get("status")
    if state == "PENDING_EXACT_HEAD_CI":
        if not strict_equal(delivery, provisional_delivery()):
            add_error(errors, "provisional_delivery_mismatch")
        return "PROVISIONAL"
    if state != "VERIFIED_TRUE_GREEN":
        add_error(errors, "delivery_status_mismatch")
        return "INVALID"
    head = delivery.get("accepted_proof_head")
    if not isinstance(head, str) or len(head) != 40:
        add_error(errors, "accepted_proof_head_invalid")
        return "FINAL"
    push = delivery.get("push")
    pull = delivery.get("pull_request")
    if not _delivery_run_valid(push, "push", head):
        add_error(errors, "delivery_push_mismatch")
    if not _delivery_run_valid(pull, "pull_request", head):
        add_error(errors, "delivery_pull_request_mismatch")
    if isinstance(push, dict) and isinstance(pull, dict):
        if push.get("run_id") == pull.get("run_id"):
            add_error(errors, "delivery_run_reuse")
    if not _runtime_result_valid(
        delivery.get("powershell_5_1"), "Windows PowerShell 5.1"
    ):
        add_error(errors, "delivery_powershell_5_1_mismatch")
    if not _runtime_result_valid(
        delivery.get("powershell_7"), "PowerShell 7 on Ubuntu"
    ):
        add_error(errors, "delivery_powershell_7_mismatch")
    if delivery.get("semantic_results_match") is not True:
        add_error(errors, "delivery_semantics_mismatch")
    if verify_git:
        if git(repo_root, "cat-file", "-e", f"{head}^{{commit}}").returncode != 0:
            add_error(errors, "accepted_proof_head_unavailable")
        if git(repo_root, "merge-base", "--is-ancestor", head, "HEAD").returncode != 0:
            add_error(errors, "accepted_proof_head_not_ancestor")
        closure = git_text(
            repo_root, "diff", "--name-only", "--no-renames", head, "HEAD", "--"
        )
        closure_paths = set(closure.splitlines()) if closure else set()
        if closure_paths != CLOSURE_CHANGE_PATHS:
            add_error(errors, "closure_change_set_mismatch")
    return "FINAL"


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
        add_error(errors, "proof_branch_diff_unavailable")
    elif committed:
        found.update(committed.splitlines())
    status = git_bytes(
        repo_root, "status", "--porcelain=v1", "--untracked-files=all"
    )
    if status is None:
        add_error(errors, "proof_worktree_status_unavailable")
    elif status:
        try:
            lines = status.decode("utf-8", errors="strict").splitlines()
        except UnicodeDecodeError:
            lines = []
            add_error(errors, "proof_worktree_status_unavailable")
        for line in lines:
            path = line[3:]
            if " -> " in path:
                left, right = path.split(" -> ", 1)
                found.add(left.strip('"'))
                found.add(right.strip('"'))
            else:
                found.add(path.strip('"'))
    return {path.replace("\\", "/") for path in found}


def audit_protocol_proof(
    repo_root: Path = REPO_ROOT,
    *,
    proof_data: Mapping[str, object] | None = None,
    verify_git: bool = True,
    present_paths: set[str] | None = None,
) -> dict[str, object]:
    repo_root = Path(repo_root).resolve(strict=False)
    errors: list[str] = []
    if proof_data is None:
        try:
            proof_raw = (repo_root / PROOF_PATH).read_bytes()
        except OSError:
            proof_raw = b""
            add_error(errors, "proof_artifact_unreadable")
        proof = load_json_bytes(proof_raw, "proof_artifact", errors)
    elif isinstance(proof_data, Mapping):
        proof = dict(proof_data)
    else:
        proof = {}
        add_error(errors, "proof_artifact_not_object")

    try:
        schema_raw = (repo_root / SCHEMA_PATH).read_bytes()
    except OSError:
        schema_raw = b""
        add_error(errors, "proof_schema_unreadable")
    schema = load_json_bytes(schema_raw, "proof_schema", errors)
    if not schema_contract(schema):
        add_error(errors, "proof_schema_contract_mismatch")

    if set(proof) != ROOT_KEYS:
        add_error(errors, "proof_root_keys_mismatch")
    if proof.get("schema_version") != "m4.2-gate-iv-b-protocol-proof-v1":
        add_error(errors, "schema_version_mismatch")
    if proof.get("milestone") != "M4" or proof.get("revision") != "M4.2":
        add_error(errors, "proof_identity_mismatch")
    if (
        proof.get("proof_kind")
        != "OFFLINE_PROTOCOL_PROOF_NOT_EXECUTION_AUTHORIZATION"
    ):
        add_error(errors, "proof_kind_mismatch")

    delivery = proof.get("delivery")
    state = delivery_state(repo_root, delivery, errors, verify_git)
    expected = expected_proof(
        repo_root,
        delivery=delivery if isinstance(delivery, Mapping) else None,
        present_paths=present_paths,
        errors=errors,
    )
    section_errors = (
        ("baseline", "baseline_binding_mismatch"),
        ("source_artifacts", "source_artifact_bindings_mismatch"),
        ("matrix_proof", "matrix_proof_mismatch"),
        ("request_binding_proof", "request_binding_proof_mismatch"),
        (
            "candidate_authorization_fixture",
            "candidate_authorization_fixture_mismatch",
        ),
        ("claim_semantics", "claim_semantics_mismatch"),
        ("pre_dispatch_proofs", "pre_dispatch_proofs_mismatch"),
        ("batch_failure_proofs", "batch_failure_proofs_mismatch"),
        ("visibility_proof", "visibility_proof_mismatch"),
        ("negative_authority", "negative_authority_mismatch"),
    )
    for key, error in section_errors:
        if not strict_equal(proof.get(key), expected.get(key)):
            add_error(errors, error)

    negative = expected["negative_authority"]
    forbidden_paths = negative.get("forbidden_paths", [])
    if forbidden_paths:
        add_error(errors, "forbidden_future_path_present")
    if proof.get("findings") != []:
        add_error(errors, "proof_findings_present")
    if proof.get("reviewer_side_effects") != []:
        add_error(errors, "reviewer_side_effects_present")

    decision = proof.get("decision")
    artifact_status = proof.get("status")
    if isinstance(decision, str) and (
        decision == "AUTHORIZE_M4_2_EXECUTION"
        or decision.startswith("AUTHORIZE_M4_2_")
    ):
        add_error(errors, "decision_attempts_execution_authorization")
    if state == "PROVISIONAL":
        if decision != PROVISIONAL_DECISION or artifact_status != PROVISIONAL_STATUS:
            add_error(errors, "provisional_decision_status_mismatch")
    elif state == "FINAL":
        if decision != FINAL_DECISION or artifact_status != FINAL_STATUS:
            add_error(errors, "final_decision_status_mismatch")
    else:
        add_error(errors, "decision_status_state_mismatch")

    if verify_git:
        if git(
            repo_root, "cat-file", "-e", f"{BASELINE_HEAD}^{{commit}}"
        ).returncode != 0:
            add_error(errors, "baseline_head_unavailable")
        if git_text(repo_root, "rev-parse", f"{BASELINE_HEAD}^{{tree}}") != BASELINE_TREE:
            add_error(errors, "baseline_tree_mismatch")
        if git(
            repo_root, "merge-base", "--is-ancestor", BASELINE_HEAD, "HEAD"
        ).returncode != 0:
            add_error(errors, "baseline_head_not_ancestor")
        baseline_blob = git_text(
            repo_root, "rev-parse", f"{BASELINE_HEAD}:{R2_REVIEW_PATH.as_posix()}"
        )
        current_blob = git_text(
            repo_root, "rev-parse", f"HEAD:{R2_REVIEW_PATH.as_posix()}"
        )
        if baseline_blob != current_blob:
            add_error(errors, "gate_iv_a_r2_artifact_changed")
        unexpected = changed_paths(repo_root, errors) - ALLOWED_CHANGE_PATHS
        if unexpected:
            add_error(errors, "proof_change_set_mismatch")

    counters = negative if isinstance(negative, dict) else {}
    status = artifact_status if not errors else "BLOCKED"
    return {
        "status": status,
        "decision": decision,
        "errors": sorted(errors),
        "findings": list(proof.get("findings", []))
        if isinstance(proof.get("findings"), list)
        else [],
        "reviewer_side_effects": list(proof.get("reviewer_side_effects", []))
        if isinstance(proof.get("reviewer_side_effects"), list)
        else [],
        "baseline_head": BASELINE_HEAD,
        "planned_task_count": expected["matrix_proof"].get(
            "planned_task_count", 0
        ),
        "batch_count": expected["matrix_proof"].get("batch_count", 0),
        "request_binding_count": expected["request_binding_proof"].get(
            "matched", 0
        ),
        "forbidden_path_count": len(forbidden_paths),
        "forbidden_paths": list(forbidden_paths),
        **{name: counters.get(name, -1) for name in COUNTER_NAMES},
        "authorization_token_status": counters.get(
            "authorization_token_status", "INVALID"
        ),
        "authorization_artifact": counters.get(
            "authorization_artifact", "INVALID"
        ),
        "launch_claim": counters.get("launch_claim", "INVALID"),
        "result_root": counters.get("result_root", "INVALID"),
        "judge": counters.get("judge", "INVALID"),
        "aggregation": counters.get("aggregation", "INVALID"),
        "closure": counters.get("closure", "INVALID"),
        "m5": counters.get("m5", "INVALID"),
    }


def main() -> int:
    result = audit_protocol_proof()
    print(
        json.dumps(
            result,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0 if not result["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
