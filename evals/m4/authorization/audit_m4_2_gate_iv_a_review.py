#!/usr/bin/env python3
"""Read-only M4.2 Gate IV-A independent review auditor."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence


REPO_ROOT = Path(__file__).resolve().parents[3]
REVIEWED_HEAD = "941602180c75c4ae16edfc927f6c39b8420fb45c"
REVIEWED_TREE = "43357e6fa252abbb84095aebb577974974527791"
REVIEWED_BRANCH = (
    "codex/m4-cross-engineering-forward-evaluation-m4.2-successor-preparation"
)
REVIEW_PATH = Path("evals/m4/authorization/m4.2/gate-iv-a-review.json")
SCHEMA_PATH = Path("evals/m4/authorization/m4.2/gate-iv-a-review.schema.json")
REVIEW_RAW_SHA256 = (
    "cd68d10a140606d4f7dd0ee6d09ebe49c1b4566aa54345cfe91728eaac06b373"
)
SCHEMA_RAW_SHA256 = (
    "5636da08c195e6570f0e0aa24626e7f40c035898828587d6cd7ab83382b331d2"
)
CI_EVIDENCE_CANONICAL_SHA256 = (
    "7da848ec90f11849390aa64d03f67c8eec3b45827bd6b8fe1684af6dbeddda16"
)
LIMITATIONS_CANONICAL_SHA256 = (
    "548e6b053fb2d96056c981b5ec89a2d9ae05a3e97779a4c0cc913901ab3bbd48"
)

M42_MANIFEST_PATH = Path("evals/m4/revisions/m4.2/preparation-manifest.json")
M41_MANIFEST_PATH = Path("evals/m4/revisions/m4.1/preparation-manifest.json")
M40_MANIFEST_PATH = Path("evals/m4/preparation-manifest.json")
HELPER_PATH = Path("evals/m4/execution/prepare_m4_2_request_bundles.ps1")
WORKFLOW_PATH = Path(".github/workflows/m1-validation.yml")
PREPARATION_TEST_PATH = Path("tests/test_m4_2_preparation.py")
STATUS_PATH = Path("STATUS.md")
M41_CLAIM_PATH = Path("evals/m4/execution/m4.1/launch-claim.json")
M41_TERMINAL_PATH = Path("evals/m4/execution/m4.1/execution-terminal.json")

REVIEWED_ARTIFACT_PATHS = (
    M42_MANIFEST_PATH,
    Path("evals/m4/revisions/m4.2/preparation-manifest.schema.json"),
    Path("evals/m4/build_m4_2_preparation.py"),
    Path("evals/m4/audit_m4_2_preparation.py"),
    HELPER_PATH,
    PREPARATION_TEST_PATH,
    WORKFLOW_PATH,
    STATUS_PATH,
    M41_CLAIM_PATH,
    M41_TERMINAL_PATH,
    Path("evals/m4/execution/audit_m4_1_terminal.py"),
)

ALLOWED_REVIEW_CHANGES = frozenset(
    {
        "docs/superpowers/plans/2026-08-09-m4.2-gate-iv-a-independent-review.md",
        SCHEMA_PATH.as_posix(),
        REVIEW_PATH.as_posix(),
        "evals/m4/authorization/audit_m4_2_gate_iv_a_review.py",
        "tests/test_m4_2_gate_iv_a_review.py",
        WORKFLOW_PATH.as_posix(),
        STATUS_PATH.as_posix(),
        "tests/test_m3_r5_erratum.py",
    }
)

REVIEW_KEYS = {
    "schema_version",
    "reviewed_head",
    "reviewed_tree",
    "reviewed_branch",
    "reviewed_artifacts",
    "ci_evidence",
    "matrix_checks",
    "identity_checks",
    "lineage_checks",
    "request_binding_checks",
    "ci_integrity_checks",
    "historical_preservation",
    "zero_state",
    "lifecycle_requirements",
    "findings",
    "limitations",
    "reviewer_side_effects",
    "decision",
    "status",
}

INHERITED_TASK_KEYS = (
    "case_id",
    "domain",
    "case_type",
    "arm_id",
    "case_path",
    "case_sha256",
    "user_input_sha256",
    "task_protocol_sha256",
    "variant_instruction_path",
    "variant_instruction_sha256",
    "rubric_sha256",
    "execution_constraints_sha256",
)

EXPECTED_PREPARATION_AUTHORITY = {
    "fresh_execution_authorized": False,
    "fresh_tasks_authorized": False,
    "result_writes_authorized": False,
    "retry_authorized": False,
    "repair_authorized": False,
    "authorization_artifact": None,
}

EXPECTED_LIFECYCLE = {
    "fresh_execution_authorized": False,
    "authorization_created": False,
    "execution_created": False,
    "claim_created": False,
    "protocol_proof_only": True,
    "judge": "NOT_RUN",
    "aggregation": "NOT_RUN",
    "closure": "NOT_RUN",
    "m5": "NOT_STARTED",
}

EXPECTED_CI_RUNS = {
    31316090614,
    31316093185,
    31316592412,
    31316593775,
}
EXPECTED_FALSE_GREEN_RUNS = {31311637459, 31313212880}
CRLF_MISMATCH_CODES = [
    "case_raw_sha256_mismatch",
    "task_protocol_raw_sha256_mismatch",
    "variant_instruction_raw_sha256_mismatch",
    "rubric_raw_sha256_mismatch",
]

_BASELINE_BLOB_CACHE: dict[tuple[str, str], bytes] = {}


class DuplicateKeyError(ValueError):
    pass


def _add(errors: list[str], code: str) -> None:
    if code not in errors:
        errors.append(code)


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _git_blob_oid(raw: bytes) -> str:
    header = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(header + raw).hexdigest()


def _canonical_sha256(value: object) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return _sha256(raw)


def _strict_equal(actual: object, expected: object) -> bool:
    if type(actual) is not type(expected):
        return False
    if isinstance(expected, dict):
        return set(actual) == set(expected) and all(
            _strict_equal(actual[key], expected[key]) for key in expected
        )
    if isinstance(expected, list):
        return len(actual) == len(expected) and all(
            _strict_equal(left, right) for left, right in zip(actual, expected)
        )
    return actual == expected


def _pairs_no_duplicates(pairs: Sequence[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(key)
        result[key] = value
    return result


def _reject_constant(value: str) -> object:
    raise ValueError(f"non_finite_json_constant:{value}")


def _load_json_bytes(raw: bytes, label: str, errors: list[str]) -> dict[str, Any]:
    if raw.startswith(b"\xef\xbb\xbf"):
        _add(errors, f"{label}_bom_forbidden")
        return {}
    try:
        text = raw.decode("utf-8", errors="strict")
        value = json.loads(
            text,
            object_pairs_hook=_pairs_no_duplicates,
            parse_constant=_reject_constant,
        )
    except DuplicateKeyError:
        _add(errors, f"{label}_duplicate_key")
        return {}
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        _add(errors, f"{label}_invalid_json")
        return {}
    if not isinstance(value, dict):
        _add(errors, f"{label}_not_object")
        return {}
    return value


def _git_environment() -> dict[str, str]:
    environment = dict(os.environ)
    environment["GIT_NO_REPLACE_OBJECTS"] = "1"
    for key in (
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_WORK_TREE",
    ):
        environment.pop(key, None)
    return environment


def _git(repo_root: Path, *arguments: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *arguments],
        cwd=repo_root,
        env=_git_environment(),
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _git_bytes(repo_root: Path, *arguments: str) -> bytes | None:
    completed = _git(repo_root, *arguments)
    if completed.returncode != 0:
        return None
    return completed.stdout


def _git_text(repo_root: Path, *arguments: str) -> str | None:
    raw = _git_bytes(repo_root, *arguments)
    if raw is None:
        return None
    try:
        return raw.decode("utf-8", errors="strict").strip()
    except UnicodeDecodeError:
        return None


def _baseline_blob(repo_root: Path, path: Path, errors: list[str]) -> bytes:
    key = (str(repo_root), path.as_posix())
    if key in _BASELINE_BLOB_CACHE:
        return _BASELINE_BLOB_CACHE[key]
    raw = _git_bytes(repo_root, "show", f"{REVIEWED_HEAD}:{path.as_posix()}")
    if raw is None:
        _add(errors, "reviewed_git_object_missing")
        return b""
    _BASELINE_BLOB_CACHE[key] = raw
    return raw


def _baseline_object(
    repo_root: Path,
    path: Path,
    label: str,
    errors: list[str],
) -> dict[str, Any]:
    return _load_json_bytes(_baseline_blob(repo_root, path, errors), label, errors)


def _artifact_binding(repo_root: Path, path: Path, errors: list[str]) -> dict[str, object]:
    raw = _baseline_blob(repo_root, path, errors)
    return {
        "path": path.as_posix(),
        "byte_length": len(raw),
        "raw_sha256": _sha256(raw),
        "git_blob_oid": _git_blob_oid(raw),
    }


def _changed_paths(repo_root: Path, errors: list[str]) -> set[str]:
    changed: set[str] = set()
    committed = _git_text(
        repo_root,
        "diff",
        "--name-only",
        "--no-renames",
        REVIEWED_HEAD,
        "HEAD",
        "--",
    )
    if committed is None:
        _add(errors, "review_branch_diff_unavailable")
    elif committed:
        changed.update(line for line in committed.splitlines() if line)

    status_raw = _git_bytes(
        repo_root,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    )
    if status_raw is None:
        _add(errors, "review_worktree_status_unavailable")
    elif status_raw:
        try:
            status_lines = status_raw.decode("utf-8", errors="strict").splitlines()
        except UnicodeDecodeError:
            status_lines = []
            _add(errors, "review_worktree_status_unavailable")
        for line in status_lines:
            path = line[3:]
            if " -> " in path:
                left, right = path.split(" -> ", 1)
                changed.add(left.strip('"'))
                changed.add(right.strip('"'))
            else:
                changed.add(path.strip('"'))
    return {path.replace("\\", "/") for path in changed}


def _discover_forbidden_future_paths(repo_root: Path) -> set[str]:
    found: set[str] = set()
    exact = (
        Path("evals/m4/authorization/m4.2/execution-authorization.json"),
        Path("evals/m4/authorization/m4.2/execution-control.json"),
        Path("evals/m4/results-manifest.json"),
    )
    for relative in exact:
        if (repo_root / relative).exists():
            found.add(relative.as_posix())

    prefixes = (
        Path("evals/m4/execution/m4.2"),
        Path("evals/m4/results/m4.1"),
        Path("evals/m4/results/m4.2"),
    )
    for relative in prefixes:
        absolute = repo_root / relative
        if absolute.exists():
            if absolute.is_file():
                found.add(relative.as_posix())
            else:
                for item in absolute.rglob("*"):
                    if item.is_file() or item.is_symlink():
                        found.add(item.relative_to(repo_root).as_posix())

    authorization_root = repo_root / "evals/m4/authorization/m4.2"
    allowed = {
        (repo_root / REVIEW_PATH).resolve(strict=False),
        (repo_root / SCHEMA_PATH).resolve(strict=False),
    }
    if authorization_root.exists():
        for item in authorization_root.rglob("*"):
            if (item.is_file() or item.is_symlink()) and item.resolve(
                strict=False
            ) not in allowed:
                found.add(item.relative_to(repo_root).as_posix())
    return found


def _request_binding(task: Mapping[str, object]) -> str:
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
    return _sha256(("\n".join(frame) + "\n").encode("utf-8"))


def _tasks(value: Mapping[str, object], errors: list[str], label: str) -> list[dict[str, Any]]:
    tasks = value.get("tasks")
    if not isinstance(tasks, list) or not all(isinstance(item, dict) for item in tasks):
        _add(errors, f"{label}_tasks_invalid")
        return []
    return tasks


def _batches(value: Mapping[str, object], errors: list[str], label: str) -> list[dict[str, Any]]:
    matrix = value.get("matrix")
    if not isinstance(matrix, dict):
        _add(errors, f"{label}_matrix_invalid")
        return []
    batches = matrix.get("batches")
    if not isinstance(batches, list) or not all(isinstance(item, dict) for item in batches):
        _add(errors, f"{label}_batches_invalid")
        return []
    return batches


def _ci_semantics(ci: object) -> tuple[bool, bool]:
    if not isinstance(ci, dict):
        return False, False
    accepted_clean = True
    run_ids: set[int] = set()
    for phase_name in ("implementation", "closure"):
        phase = ci.get(phase_name)
        if not isinstance(phase, dict):
            return False, False
        for event_name in ("push", "pull_request"):
            run = phase.get(event_name)
            if not isinstance(run, dict):
                return False, False
            run_id = run.get("run_id")
            if type(run_id) is not int:
                return False, False
            run_ids.add(run_id)
            jobs = run.get("jobs")
            raw_log = run.get("raw_log")
            powershell = run.get("windows_powershell_5_1")
            if not isinstance(jobs, list) or len(jobs) != 7:
                accepted_clean = False
            if run.get("job_count") != 7 or run.get("conclusion") != "success":
                accepted_clean = False
            if not isinstance(raw_log, dict) or raw_log.get(
                "banned_pattern_counts"
            ) != {"FAIL:": 0, "FAILED (": 0, "Traceback": 0, "##[error]": 0}:
                accepted_clean = False
            if not isinstance(powershell, dict) or powershell.get(
                "checked_task_count"
            ) != 60:
                accepted_clean = False
    false_green = ci.get("historical_false_green")
    if not isinstance(false_green, list):
        return False, False
    false_green_ids = {
        entry.get("run_id") for entry in false_green if isinstance(entry, dict)
    }
    false_green_preserved = false_green_ids == EXPECTED_FALSE_GREEN_RUNS and all(
        isinstance(entry, dict)
        and entry.get("acceptance") == "NOT_ACCEPTED"
        and entry.get("classification") == "FALSE_GREEN"
        and entry.get("run_conclusion") == "success"
        and entry.get("subsequent_commands_continued") is True
        for entry in false_green
    )
    return accepted_clean and run_ids == EXPECTED_CI_RUNS, false_green_preserved


def audit_review(
    repo_root: Path = REPO_ROOT,
    *,
    review_data: Mapping[str, object] | None = None,
    verify_git: bool = True,
    present_paths: set[str] | None = None,
) -> dict[str, object]:
    repo_root = Path(repo_root).resolve(strict=False)
    errors: list[str] = []

    if review_data is None:
        try:
            review_raw = (repo_root / REVIEW_PATH).read_bytes()
        except OSError:
            review_raw = b""
            _add(errors, "review_artifact_unreadable")
        if _sha256(review_raw) != REVIEW_RAW_SHA256:
            _add(errors, "review_artifact_raw_hash_mismatch")
        review = _load_json_bytes(review_raw, "review_artifact", errors)
    elif isinstance(review_data, Mapping):
        review = dict(review_data)
    else:
        review = {}
        _add(errors, "review_artifact_not_object")

    try:
        schema_raw = (repo_root / SCHEMA_PATH).read_bytes()
    except OSError:
        schema_raw = b""
        _add(errors, "review_schema_unreadable")
    if _sha256(schema_raw) != SCHEMA_RAW_SHA256:
        _add(errors, "review_schema_raw_hash_mismatch")

    if set(review) != REVIEW_KEYS:
        _add(errors, "review_root_keys_mismatch")
    if review.get("schema_version") != "m4.2-gate-iv-a-independent-review-v1":
        _add(errors, "schema_version_mismatch")
    if review.get("reviewed_head") != REVIEWED_HEAD:
        _add(errors, "reviewed_head_mismatch")
    if review.get("reviewed_tree") != REVIEWED_TREE:
        _add(errors, "reviewed_tree_mismatch")
    if review.get("reviewed_branch") != REVIEWED_BRANCH:
        _add(errors, "reviewed_branch_mismatch")

    if verify_git:
        commit = _git(repo_root, "cat-file", "-e", f"{REVIEWED_HEAD}^{{commit}}")
        if commit.returncode != 0:
            _add(errors, "reviewed_head_unavailable")
        tree = _git_text(repo_root, "rev-parse", f"{REVIEWED_HEAD}^{{tree}}")
        if tree != REVIEWED_TREE:
            _add(errors, "reviewed_tree_object_mismatch")
        ancestor = _git(repo_root, "merge-base", "--is-ancestor", REVIEWED_HEAD, "HEAD")
        if ancestor.returncode != 0:
            _add(errors, "reviewed_head_not_ancestor")

    expected_artifacts = [
        _artifact_binding(repo_root, path, errors) for path in REVIEWED_ARTIFACT_PATHS
    ]
    if not _strict_equal(review.get("reviewed_artifacts"), expected_artifacts):
        _add(errors, "reviewed_artifact_binding_mismatch")

    m42 = _baseline_object(repo_root, M42_MANIFEST_PATH, "m4_2_manifest", errors)
    m41 = _baseline_object(repo_root, M41_MANIFEST_PATH, "m4_1_manifest", errors)
    m40 = _baseline_object(repo_root, M40_MANIFEST_PATH, "m4_0_manifest", errors)
    tasks42 = _tasks(m42, errors, "m4_2")
    tasks41 = _tasks(m41, errors, "m4_1")
    tasks40 = _tasks(m40, errors, "m4_0")
    batches42 = _batches(m42, errors, "m4_2")
    batches41 = _batches(m41, errors, "m4_1")
    batches40 = _batches(m40, errors, "m4_0")

    tasks_per_batch = {
        len(batch.get("task_ids", []))
        for batch in batches42
        if isinstance(batch.get("task_ids"), list)
    }
    expected_matrix = {
        "case_count": 12,
        "arm_count": 5,
        "planned_task_count": len(tasks42),
        "batch_count": len(batches42),
        "tasks_per_batch": next(iter(tasks_per_batch)) if len(tasks_per_batch) == 1 else -1,
        "passed": len(tasks42) == 60 and len(batches42) == 6 and tasks_per_batch == {10},
    }
    if not _strict_equal(review.get("matrix_checks"), expected_matrix):
        _add(errors, "matrix_checks_mismatch")

    task_ids42 = [str(task.get("task_id")) for task in tasks42]
    task_ids41 = {str(task.get("task_id")) for task in tasks41}
    task_ids40 = {str(task.get("task_id")) for task in tasks40}
    blind_ids42 = [str(task.get("blind_id")) for task in tasks42]
    blind_ids41 = {str(task.get("blind_id")) for task in tasks41}
    blind_ids40 = {str(task.get("blind_id")) for task in tasks40}
    batch_ids42 = [str(batch.get("batch_id")) for batch in batches42]
    batch_ids41 = {str(batch.get("batch_id")) for batch in batches41}
    batch_ids40 = {str(batch.get("batch_id")) for batch in batches40}
    reused_tasks = sorted(set(task_ids42) & (task_ids41 | task_ids40))
    reused_blinds = sorted(set(blind_ids42) & (blind_ids41 | blind_ids40))
    reused_batches = sorted(set(batch_ids42) & (batch_ids41 | batch_ids40))
    expected_identity = {
        "unique_task_id_count": len(set(task_ids42)),
        "new_task_id_count": len(set(task_ids42)) - len(reused_tasks),
        "reused_task_ids": reused_tasks,
        "unique_blind_id_count": len(set(blind_ids42)),
        "blind_id_range": (
            f"{blind_ids42[0]}..{blind_ids42[-1]}" if blind_ids42 else ""
        ),
        "reused_blind_ids": reused_blinds,
        "unique_batch_id_count": len(set(batch_ids42)),
        "reused_batch_ids": reused_batches,
        "passed": (
            len(set(task_ids42)) == 60
            and len(set(blind_ids42)) == 60
            and blind_ids42 == [f"M4-J{index:03d}" for index in range(121, 181)]
            and len(set(batch_ids42)) == 6
            and not reused_tasks
            and not reused_blinds
            and not reused_batches
        ),
    }
    if not _strict_equal(review.get("identity_checks"), expected_identity):
        _add(errors, "identity_checks_mismatch")

    source_matches = sum(
        1
        for task, source in zip(tasks42, tasks41)
        if task.get("source_task_id") == source.get("task_id")
    )
    root_matches = sum(
        1
        for task, source in zip(tasks42, tasks41)
        if task.get("root_task_id") == source.get("source_task_id")
    )
    inherited_drift = sum(
        1
        for task, source in zip(tasks42, tasks41)
        for key in INHERITED_TASK_KEYS
        if task.get(key) != source.get(key)
    )
    relative_order = [task.get("source_task_id") for task in tasks42] == [
        task.get("task_id") for task in tasks41
    ]
    expected_lineage = {
        "direct_lineage": "M4.1",
        "root_lineage": "M4.0",
        "source_task_matches": source_matches,
        "root_task_matches": root_matches,
        "relative_order_preserved": relative_order,
        "inherited_field_drift_count": inherited_drift,
        "passed": (
            source_matches == 60
            and root_matches == 60
            and relative_order
            and inherited_drift == 0
        ),
    }
    if not _strict_equal(review.get("lineage_checks"), expected_lineage):
        _add(errors, "lineage_checks_mismatch")

    request_matches = sum(
        1
        for task in tasks42
        if task.get("request_binding_sha256") == _request_binding(task)
    )
    unique_requests = len(
        {str(task.get("request_binding_sha256")) for task in tasks42}
    )
    helper_binding = _artifact_binding(repo_root, HELPER_PATH, errors)
    expected_request_bindings = {
        "algorithm": "m4.2-request-binding-v1",
        "independently_recomputed": len(tasks42),
        "matched": request_matches,
        "unique": unique_requests,
        "helper": helper_binding,
        "powershell_5_1_request_bindings": 60,
        "passed": request_matches == unique_requests == len(tasks42) == 60,
    }
    if not _strict_equal(
        review.get("request_binding_checks"), expected_request_bindings
    ):
        _add(errors, "request_binding_checks_mismatch")

    ci = review.get("ci_evidence")
    if _canonical_sha256(ci) != CI_EVIDENCE_CANONICAL_SHA256:
        _add(errors, "ci_evidence_mismatch")
    accepted_logs_clean, false_green_preserved = _ci_semantics(ci)

    workflow = _baseline_blob(repo_root, WORKFLOW_PATH, errors).decode(
        "utf-8", errors="replace"
    )
    preparation_tests = _baseline_blob(repo_root, PREPARATION_TEST_PATH, errors).decode(
        "utf-8", errors="replace"
    )
    contract_marker = "      - name: Validate M4.2 preparation-only contract\n"
    next_marker = "      - name: Verify M4.2 request preflight with PowerShell 7\n"
    contract_step = ""
    if contract_marker in workflow and next_marker in workflow:
        contract_step = workflow.split(contract_marker, 1)[1].split(next_marker, 1)[0]
    expected_ci_integrity = {
        "workflow": {
            "shell_bash": "        shell: bash\n" in contract_step,
            "strict_mode": "set -euo pipefail",
            "continue_on_error_present": "continue-on-error" in workflow,
        },
        "canonical_root_alias_regression": (
            "PASSED"
            if "test_bound_input_validation_canonicalizes_repo_root_alias"
            in preparation_tests
            else "MISSING"
        ),
        "crlf_raw_sha256_mismatch_codes": [
            code for code in CRLF_MISMATCH_CODES if code in preparation_tests
        ],
        "escape_regressions": {
            "sibling": (
                "REJECTED"
                if "test_bound_input_validation_rejects_sibling_escape"
                in preparation_tests
                else "MISSING"
            ),
            "symlink": (
                "REJECTED"
                if "test_bound_input_validation_rejects_symlink_escape"
                in preparation_tests
                else "MISSING"
            ),
            "junction": (
                "REJECTED"
                if "test_bound_input_validation_rejects_junction_escape"
                in preparation_tests
                else "MISSING"
            ),
        },
        "accepted_raw_logs_clean": accepted_logs_clean,
        "false_green_history_preserved": false_green_preserved,
        "passed": (
            "        shell: bash\n" in contract_step
            and "set -euo pipefail" in contract_step
            and "continue-on-error" not in workflow
            and all(code in preparation_tests for code in CRLF_MISMATCH_CODES)
            and accepted_logs_clean
            and false_green_preserved
        ),
    }
    if not _strict_equal(review.get("ci_integrity_checks"), expected_ci_integrity):
        _add(errors, "ci_integrity_checks_mismatch")

    claim_raw = _baseline_blob(repo_root, M41_CLAIM_PATH, errors)
    terminal_raw = _baseline_blob(repo_root, M41_TERMINAL_PATH, errors)
    claim = _load_json_bytes(claim_raw, "m4_1_claim", errors)
    terminal = _load_json_bytes(terminal_raw, "m4_1_terminal", errors)
    terminal_counts = terminal.get("counts")
    terminal_counts_zero = isinstance(terminal_counts, dict) and all(
        type(value) is int and value == 0 for value in terminal_counts.values()
    )
    token_status = None
    authorization = claim.get("authorization")
    if isinstance(authorization, dict):
        token_status = authorization.get("token_status_after_claim")
    terminal_binding = {
        "status": "M4_1_STOPPED_PROTOCOL_FAILURE_PRESERVED",
        "claim_count": claim.get("claim_count"),
        "authorization_token_status": token_status,
        "claim_sha256": _sha256(claim_raw),
        "claim_blob": _git_blob_oid(claim_raw),
        "terminal_sha256": _sha256(terminal_raw),
        "terminal_blob": _git_blob_oid(terminal_raw),
        "terminal_state": terminal.get("terminal_state"),
        "all_counts_zero": terminal_counts_zero,
    }

    changed_paths = _changed_paths(repo_root, errors) if verify_git else set()
    prohibited_changes = sorted(changed_paths - ALLOWED_REVIEW_CHANGES)
    if prohibited_changes:
        _add(errors, "prohibited_baseline_path_drift")
    expected_historical = {
        "m4_1_terminal": terminal_binding,
        "prohibited_baseline_path_drift_count": len(prohibited_changes),
        "passed": not prohibited_changes and terminal_counts_zero,
    }
    if not _strict_equal(
        review.get("historical_preservation"), expected_historical
    ):
        _add(errors, "historical_preservation_mismatch")

    discovered = _discover_forbidden_future_paths(repo_root)
    if present_paths:
        discovered.update(path.replace("\\", "/") for path in present_paths)
    forbidden_paths = sorted(discovered)
    if forbidden_paths:
        _add(errors, "forbidden_future_path_present")

    authority = m42.get("authority")
    expected_authority = {
        key: authority.get(key) if isinstance(authority, dict) else None
        for key in EXPECTED_PREPARATION_AUTHORITY
    }
    counters = m42.get("counters")
    expected_counters = dict(counters) if isinstance(counters, dict) else {}
    expected_zero_state = {
        "preparation_authority": expected_authority,
        "preparation_counters": expected_counters,
        "authorization": "ABSENT" if not forbidden_paths else "PRESENT",
        "execution": "ABSENT" if not forbidden_paths else "PRESENT",
        "claim": "ABSENT" if not forbidden_paths else "PRESENT",
        "tasks": 0,
        "results": 0,
        "results_status": "NOT_RUN" if not forbidden_paths else "PRESENT",
        "forbidden_path_count": len(forbidden_paths),
        "forbidden_paths": forbidden_paths,
        "passed": (
            _strict_equal(expected_authority, EXPECTED_PREPARATION_AUTHORITY)
            and bool(expected_counters)
            and all(
                type(value) is int and value == 0
                for value in expected_counters.values()
            )
            and not forbidden_paths
        ),
    }
    if not _strict_equal(review.get("zero_state"), expected_zero_state):
        _add(errors, "zero_state_mismatch")

    if not _strict_equal(review.get("lifecycle_requirements"), EXPECTED_LIFECYCLE):
        _add(errors, "lifecycle_requirements_mismatch")

    findings = review.get("findings")
    if not isinstance(findings, list):
        findings = []
        _add(errors, "findings_invalid")
    recorded_side_effects = review.get("reviewer_side_effects")
    if not isinstance(recorded_side_effects, list):
        recorded_side_effects = []
        _add(errors, "reviewer_side_effects_invalid")
    decision = review.get("decision")
    blocked_evidence = bool(findings or recorded_side_effects)
    if isinstance(decision, str) and (
        "EXECUTION" in decision.upper()
        or decision.upper().startswith("AUTHORIZE_M4_2")
    ):
        _add(errors, "decision_attempts_execution_authorization")
    elif blocked_evidence:
        if decision != "BLOCKED":
            _add(errors, "decision_mismatch")
    elif decision != "APPROVE_M4_2_GATE_IV_B_PROTOCOL_PROOF_ONLY":
        _add(errors, "decision_mismatch")

    review_status = review.get("status")
    if blocked_evidence:
        if review_status == "M4_2_GATE_IV_A_REVIEW_PASSED_NOT_AUTHORIZED":
            if findings:
                _add(errors, "passed_with_findings")
            if recorded_side_effects:
                _add(errors, "passed_with_reviewer_side_effects")
        elif review_status != "BLOCKED":
            _add(errors, "review_status_mismatch")
    elif review_status != "M4_2_GATE_IV_A_REVIEW_PASSED_NOT_AUTHORIZED":
        _add(errors, "review_status_mismatch")
    if _canonical_sha256(review.get("limitations")) != LIMITATIONS_CANONICAL_SHA256:
        _add(errors, "limitations_mismatch")

    status = (
        "M4_2_GATE_IV_A_REVIEW_PASSED_NOT_AUTHORIZED"
        if not errors and not blocked_evidence
        else "BLOCKED"
    )
    return {
        "status": status,
        "errors": sorted(errors),
        "findings": list(findings),
        "reviewed_head": REVIEWED_HEAD,
        "reviewed_tree": REVIEWED_TREE,
        "planned_task_count": len(tasks42),
        "batch_count": len(batches42),
        "request_binding_count": request_matches,
        "reused_task_id_count": len(reused_tasks),
        "forbidden_path_count": len(forbidden_paths),
        "forbidden_paths": forbidden_paths,
        "fresh_execution_authorized": False,
        "authorization_created": False,
        "execution_created": False,
        "claim_created": False,
        "m4_1_terminal_status": terminal_binding["status"],
        "reviewer_side_effects": list(recorded_side_effects),
    }


def main() -> int:
    result = audit_review()
    print(
        json.dumps(
            result,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0 if result["status"] == "M4_2_GATE_IV_A_REVIEW_PASSED_NOT_AUTHORIZED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
