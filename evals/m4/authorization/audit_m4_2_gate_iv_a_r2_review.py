#!/usr/bin/env python3
"""Read-only M4.2 Gate IV-A r2 independent review auditor."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Mapping, Sequence


REPO_ROOT = Path(__file__).resolve().parents[3]
REVIEWED_HEAD = "44d1004da1cbb2681ee0d423d1748f98fbaa13e4"
REVIEWED_TREE = "9845b1a05e23fa84e55ad20399ec1b86bc861e44"
REVIEWED_BRANCH = (
    "codex/m4-cross-engineering-forward-evaluation-"
    "m4.2-windows-lifecycle-repair"
)
REPAIR_PARENT = "941602180c75c4ae16edfc927f6c39b8420fb45c"
PRIOR_REVIEW_HEAD = "ac6cc70714a90f73b4de09eaf0e521e699296890"
PRIOR_REVIEW_TREE = "3ee67b0c5ffa53fc2676381e9ab9b79499e2cf6e"
PRIOR_REVIEW_BRANCH = (
    "codex/m4-cross-engineering-forward-evaluation-"
    "m4.2-gate-iv-a-independent-review"
)
R2_BRANCH = (
    "codex/m4-cross-engineering-forward-evaluation-m4.2-gate-iv-a-r2"
)

REVIEW_PATH = Path("evals/m4/authorization/m4.2/gate-iv-a-review-r2.json")
SCHEMA_PATH = Path(
    "evals/m4/authorization/m4.2/gate-iv-a-review-r2.schema.json"
)
PRIOR_REVIEW_PATH = Path("evals/m4/authorization/m4.2/gate-iv-a-review.json")
SCHEMA_RAW_SHA256 = (
    "e592dcf19b0ed01b6f34aaaadc35a7c81adeca8591f081ed71d317aaacfa35c8"
)
REPAIR_CI_CANONICAL_SHA256 = (
    "ee6c42610866ae16a0df7db1f3ca09e48cace16fdadad632ba5192660a6a09d9"
)
LIMITATIONS_CANONICAL_SHA256 = (
    "02da40b1d1f762d0eb299dbe54136cf341e8afc7dbcd09382b22be29eabd9de0"
)

M42_MANIFEST_PATH = Path("evals/m4/revisions/m4.2/preparation-manifest.json")
M41_MANIFEST_PATH = Path("evals/m4/revisions/m4.1/preparation-manifest.json")
M40_MANIFEST_PATH = Path("evals/m4/preparation-manifest.json")
HELPER_PATH = Path("evals/m4/execution/prepare_m4_2_request_bundles.ps1")
M41_CLAIM_PATH = Path("evals/m4/execution/m4.1/launch-claim.json")
M41_TERMINAL_PATH = Path("evals/m4/execution/m4.1/execution-terminal.json")
ATTRIBUTES_PATH = Path(".gitattributes")
DIAGNOSTICS_PREFIX = Path("evals/m3/results/diagnostics-r5.1")
DIAGNOSTICS_PATHS = (
    DIAGNOSTICS_PREFIX / "m3-f02.offline-diagnostic.json",
    DIAGNOSTICS_PREFIX / "r5-acceptance-erratum.json",
)

REVIEWED_ARTIFACT_PATHS = (
    ATTRIBUTES_PATH,
    Path(".github/workflows/m1-validation.yml"),
    Path("STATUS.md"),
    Path("docs/superpowers/plans/2026-08-10-m4.2-windows-lifecycle-repair.md"),
    M42_MANIFEST_PATH,
    Path("evals/m4/revisions/m4.2/preparation-manifest.schema.json"),
    Path("evals/m4/build_m4_2_preparation.py"),
    Path("evals/m4/audit_m4_2_preparation.py"),
    HELPER_PATH,
    Path("tests/test_m4_2_preparation.py"),
    Path("tests/test_m3_raw_sha_eol_policy.py"),
    Path("tests/test_m3_r5_erratum.py"),
    M41_MANIFEST_PATH,
    M40_MANIFEST_PATH,
    M41_CLAIM_PATH,
    M41_TERMINAL_PATH,
    Path("evals/m4/execution/audit_m4_1_terminal.py"),
    *DIAGNOSTICS_PATHS,
)

REPAIR_CHANGED_PATHS = frozenset(
    {
        ".gitattributes",
        "docs/superpowers/plans/2026-08-10-m4.2-windows-lifecycle-repair.md",
        "evals/m4/audit_m4_2_preparation.py",
        "tests/test_m3_raw_sha_eol_policy.py",
    }
)
ALLOWED_REVIEW_CHANGES = frozenset(
    {
        ".github/workflows/m1-validation.yml",
        "STATUS.md",
        "docs/superpowers/plans/2026-08-10-m4.2-gate-iv-a-r2-independent-review.md",
        REVIEW_PATH.as_posix(),
        SCHEMA_PATH.as_posix(),
        "evals/m4/authorization/audit_m4_2_gate_iv_a_r2_review.py",
        "tests/test_m3_r5_erratum.py",
        "tests/test_m4_2_gate_iv_a_r2_review.py",
    }
)
FINAL_CLOSURE_CHANGES = frozenset(
    {
        REVIEW_PATH.as_posix(),
        "STATUS.md",
        "tests/test_m3_r5_erratum.py",
    }
)

ROOT_KEYS = {
    "schema_version",
    "reviewed_head",
    "reviewed_tree",
    "reviewed_branch",
    "reviewed_artifacts",
    "prior_blocked_review",
    "repair_evidence",
    "matrix_checks",
    "identity_checks",
    "lineage_checks",
    "request_binding_checks",
    "historical_preservation",
    "zero_state",
    "lifecycle_requirements",
    "review_delivery",
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

EXPECTED_AUTHORITY = {
    "fresh_execution_authorized": False,
    "fresh_tasks_authorized": False,
    "result_writes_authorized": False,
    "retry_authorized": False,
    "repair_authorized": False,
    "authorization_artifact": None,
    "model_binding_status": "UNBOUND_UNTIL_SEPARATE_AUTHORIZATION",
}
EXPECTED_COUNTERS = {
    "authorized_tasks": 0,
    "created_contexts": 0,
    "dispatched_tasks": 0,
    "finalizations": 0,
    "results_observed": 0,
    "judge_scores": 0,
    "retries": 0,
    "repairs": 0,
    "unauthorized_side_effects": 0,
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
PROVISIONAL_DECISION = "PENDING_M4_2_GATE_IV_A_R2_EXACT_HEAD_CI"
PROVISIONAL_STATUS = (
    "M4_2_GATE_IV_A_R2_LOCAL_REVIEW_PASSED_PENDING_EXACT_HEAD_CI"
)
FINAL_DECISION = "APPROVE_M4_2_GATE_IV_B_PROTOCOL_PROOF_ONLY"
FINAL_STATUS = "M4_2_GATE_IV_A_REVIEW_PASSED_NOT_AUTHORIZED"
ZERO_MARKERS = {"FAIL:": 0, "FAILED (": 0, "Traceback": 0, "##[error]": 0}

_OBJECT_BLOB_CACHE: dict[tuple[str, str, str], bytes] = {}


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
        value = json.loads(
            raw.decode("utf-8", errors="strict"),
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
        "GIT_DIR",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_COMMON_DIR",
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
    return completed.stdout if completed.returncode == 0 else None


def _git_text(repo_root: Path, *arguments: str) -> str | None:
    raw = _git_bytes(repo_root, *arguments)
    if raw is None:
        return None
    try:
        return raw.decode("utf-8", errors="strict").strip()
    except UnicodeDecodeError:
        return None


def _object_blob(
    repo_root: Path,
    head: str,
    path: Path,
    errors: list[str],
    label: str,
) -> bytes:
    key = (str(repo_root), head, path.as_posix())
    if key in _OBJECT_BLOB_CACHE:
        return _OBJECT_BLOB_CACHE[key]
    raw = _git_bytes(repo_root, "show", f"{head}:{path.as_posix()}")
    if raw is None:
        _add(errors, f"{label}_git_object_missing")
        return b""
    _OBJECT_BLOB_CACHE[key] = raw
    return raw


def _object_json(
    repo_root: Path,
    head: str,
    path: Path,
    label: str,
    errors: list[str],
) -> dict[str, Any]:
    return _load_json_bytes(
        _object_blob(repo_root, head, path, errors, label),
        label,
        errors,
    )


def _artifact_binding(
    repo_root: Path,
    head: str,
    path: Path,
    errors: list[str],
    label: str = "reviewed",
) -> dict[str, object]:
    raw = _object_blob(repo_root, head, path, errors, label)
    return {
        "path": path.as_posix(),
        "git_blob_oid": _git_blob_oid(raw),
        "raw_sha256": _sha256(raw),
        "byte_length": len(raw),
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
            lines = status_raw.decode("utf-8", errors="strict").splitlines()
        except UnicodeDecodeError:
            lines = []
            _add(errors, "review_worktree_status_unavailable")
        for line in lines:
            path = line[3:]
            if " -> " in path:
                left, right = path.split(" -> ", 1)
                changed.add(left.strip('"'))
                changed.add(right.strip('"'))
            else:
                changed.add(path.strip('"'))
    return {path.replace("\\", "/") for path in changed}


def _diff_paths(
    repo_root: Path,
    start: str,
    end: str,
    errors: list[str],
    label: str,
    pathspec: str | None = None,
) -> list[str]:
    arguments = ["diff", "--name-only", "--no-renames", start, end, "--"]
    if pathspec is not None:
        arguments.append(pathspec)
    value = _git_text(repo_root, *arguments)
    if value is None:
        _add(errors, f"{label}_diff_unavailable")
        return []
    return sorted(line for line in value.splitlines() if line)


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


def _check_attributes(repo_root: Path, path: Path) -> dict[str, str] | None:
    raw = _git_bytes(
        repo_root,
        "check-attr",
        "-z",
        "text",
        "eol",
        "--",
        path.as_posix(),
    )
    if raw is None:
        return None
    fields = raw.split(b"\0")
    if fields and fields[-1] == b"":
        fields.pop()
    if len(fields) != 6:
        return None
    try:
        decoded = [field.decode("utf-8", errors="strict") for field in fields]
    except UnicodeDecodeError:
        return None
    if decoded[0] != path.as_posix() or decoded[3] != path.as_posix():
        return None
    return {decoded[1]: decoded[2], decoded[4]: decoded[5]}


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


def _tasks(
    value: Mapping[str, object], errors: list[str], label: str
) -> list[dict[str, Any]]:
    tasks = value.get("tasks")
    if not isinstance(tasks, list) or not all(isinstance(item, dict) for item in tasks):
        _add(errors, f"{label}_tasks_invalid")
        return []
    return tasks


def _batches(
    value: Mapping[str, object], errors: list[str], label: str
) -> list[dict[str, Any]]:
    matrix = value.get("matrix")
    if not isinstance(matrix, dict):
        _add(errors, f"{label}_matrix_invalid")
        return []
    batches = matrix.get("batches")
    if not isinstance(batches, list) or not all(
        isinstance(item, dict) for item in batches
    ):
        _add(errors, f"{label}_batches_invalid")
        return []
    return batches


def _schema_contract(schema: Mapping[str, object]) -> bool:
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
            properties = definition.get("properties")
            required = definition.get("required")
            if not isinstance(properties, dict) or not isinstance(required, list):
                return False
            if set(properties) != set(required):
                return False
    return True


def _repair_ci_semantics(ci: object) -> bool:
    if not isinstance(ci, dict):
        return False
    if _canonical_sha256(ci) != REPAIR_CI_CANONICAL_SHA256:
        return False
    if ci.get("repository") != "zxy19960316/engineering-research-copilot":
        return False
    if ci.get("pull_request") != 5:
        return False
    expected = (("push", 31354780589), ("pull_request_run", 31354802277))
    for key, run_id in expected:
        run = ci.get(key)
        if not isinstance(run, dict):
            return False
        jobs = run.get("jobs")
        raw_log = run.get("raw_log")
        if (
            run.get("run_id") != run_id
            or run.get("head") != REVIEWED_HEAD
            or run.get("branch") != REVIEWED_BRANCH
            or run.get("conclusion") != "success"
            or run.get("job_count") != 7
            or not isinstance(jobs, list)
            or len(jobs) != 7
            or len({job.get("job_id") for job in jobs if isinstance(job, dict)}) != 7
            or not all(
                isinstance(job, dict) and job.get("conclusion") == "success"
                for job in jobs
            )
            or run.get("current_lifecycle_count") != 655
            or run.get("m4_2_focused_count") != 21
            or run.get("historical_focused_count") != 6
            or run.get("powershell_5_1_request_bindings") != 60
            or run.get("results_status") != "NOT_RUN"
            or run.get("forbidden_path_count") != 0
            or not isinstance(raw_log, dict)
            or raw_log.get("markers") != ZERO_MARKERS
        ):
            return False
    return True


def _delivery_run_semantics(run: object, event: str, head: str) -> bool:
    if not isinstance(run, dict):
        return False
    jobs = run.get("jobs")
    raw_log = run.get("raw_log")
    return bool(
        type(run.get("run_id")) is int
        and run.get("run_id", 0) > 0
        and run.get("event") == event
        and run.get("head") == head
        and run.get("branch") == R2_BRANCH
        and run.get("conclusion") == "success"
        and type(run.get("job_count")) is int
        and run.get("job_count", 0) >= 9
        and isinstance(jobs, list)
        and len(jobs) == run.get("job_count")
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
        and isinstance(raw_log, dict)
        and type(raw_log.get("byte_length")) is int
        and raw_log.get("byte_length", 0) > 0
        and isinstance(raw_log.get("sha256"), str)
        and len(raw_log.get("sha256", "")) == 64
        and raw_log.get("markers") == ZERO_MARKERS
    )


def _delivery_state(
    repo_root: Path,
    delivery: object,
    errors: list[str],
    verify_git: bool,
) -> str:
    if not isinstance(delivery, dict):
        _add(errors, "review_delivery_invalid")
        return "INVALID"
    if set(delivery) != {"status", "accepted_review_head", "push", "pull_request"}:
        _add(errors, "review_delivery_keys_mismatch")
        return "INVALID"
    state = delivery.get("status")
    accepted = delivery.get("accepted_review_head")
    push = delivery.get("push")
    pull = delivery.get("pull_request")
    if state == "PENDING_EXACT_HEAD_CI":
        if accepted is not None or push is not None or pull is not None:
            _add(errors, "provisional_delivery_evidence_present")
        return "PROVISIONAL"
    if state != "VERIFIED_TRUE_GREEN":
        _add(errors, "review_delivery_status_mismatch")
        return "INVALID"
    if not isinstance(accepted, str) or len(accepted) != 40:
        _add(errors, "accepted_review_head_invalid")
        return "FINAL"
    if not _delivery_run_semantics(push, "push", accepted):
        _add(errors, "review_delivery_push_mismatch")
    if not _delivery_run_semantics(pull, "pull_request", accepted):
        _add(errors, "review_delivery_pull_request_mismatch")
    if isinstance(push, dict) and isinstance(pull, dict):
        if push.get("run_id") == pull.get("run_id"):
            _add(errors, "review_delivery_run_reuse")
    if verify_git:
        if _git(repo_root, "cat-file", "-e", f"{accepted}^{{commit}}").returncode != 0:
            _add(errors, "accepted_review_head_unavailable")
        if _git(
            repo_root, "merge-base", "--is-ancestor", accepted, "HEAD"
        ).returncode != 0:
            _add(errors, "accepted_review_head_not_ancestor")
        closure_paths = set(
            _diff_paths(
                repo_root,
                accepted,
                "HEAD",
                errors,
                "review_closure",
            )
        )
        if closure_paths != FINAL_CLOSURE_CHANGES:
            _add(errors, "review_closure_change_set_mismatch")
    return "FINAL"


def audit_review(
    repo_root: Path = REPO_ROOT,
    *,
    review_path: Path | None = None,
    review_data: Mapping[str, object] | None = None,
    verify_git: bool = True,
    present_paths: set[str] | None = None,
) -> dict[str, object]:
    repo_root = Path(repo_root).resolve(strict=False)
    errors: list[str] = []

    selected_review_path = review_path or REVIEW_PATH
    if review_data is None:
        try:
            review_raw = (repo_root / selected_review_path).read_bytes()
        except OSError:
            review_raw = b""
            _add(errors, "review_artifact_unreadable")
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
    schema = _load_json_bytes(schema_raw, "review_schema", errors)
    if not _schema_contract(schema):
        _add(errors, "review_schema_contract_mismatch")

    if set(review) != ROOT_KEYS:
        _add(errors, "review_root_keys_mismatch")
    if review.get("schema_version") != "m4.2-gate-iv-a-review-r2-v1":
        _add(errors, "schema_version_mismatch")
    if review.get("reviewed_head") != REVIEWED_HEAD:
        _add(errors, "reviewed_head_mismatch")
    if review.get("reviewed_tree") != REVIEWED_TREE:
        _add(errors, "reviewed_tree_mismatch")
    if review.get("reviewed_branch") != REVIEWED_BRANCH:
        _add(errors, "reviewed_branch_mismatch")

    if verify_git:
        if _git(
            repo_root, "cat-file", "-e", f"{REVIEWED_HEAD}^{{commit}}"
        ).returncode != 0:
            _add(errors, "reviewed_head_unavailable")
        if _git_text(repo_root, "rev-parse", f"{REVIEWED_HEAD}^{{tree}}") != REVIEWED_TREE:
            _add(errors, "reviewed_tree_object_mismatch")
        if _git(
            repo_root, "merge-base", "--is-ancestor", REVIEWED_HEAD, "HEAD"
        ).returncode != 0:
            _add(errors, "reviewed_head_not_ancestor")

    expected_artifacts = [
        _artifact_binding(repo_root, REVIEWED_HEAD, path, errors)
        for path in REVIEWED_ARTIFACT_PATHS
    ]
    if not _strict_equal(review.get("reviewed_artifacts"), expected_artifacts):
        _add(errors, "reviewed_artifact_binding_mismatch")

    prior_raw = _object_blob(
        repo_root,
        PRIOR_REVIEW_HEAD,
        PRIOR_REVIEW_PATH,
        errors,
        "prior_blocked_review",
    )
    prior = _load_json_bytes(prior_raw, "prior_blocked_review", errors)
    expected_prior = {
        "head": PRIOR_REVIEW_HEAD,
        "tree": PRIOR_REVIEW_TREE,
        "branch": PRIOR_REVIEW_BRANCH,
        "artifact": {
            "path": PRIOR_REVIEW_PATH.as_posix(),
            "git_blob_oid": _git_blob_oid(prior_raw),
            "raw_sha256": _sha256(prior_raw),
            "byte_length": len(prior_raw),
        },
        "pull_request": 4,
        "decision": prior.get("decision"),
        "status": prior.get("status"),
        "finding_count": len(prior.get("findings", []))
        if isinstance(prior.get("findings"), list)
        else -1,
        "reviewer_side_effects": prior.get("reviewer_side_effects"),
    }
    if verify_git:
        if _git_text(
            repo_root, "rev-parse", f"{PRIOR_REVIEW_HEAD}^{{tree}}"
        ) != PRIOR_REVIEW_TREE:
            _add(errors, "prior_blocked_review_tree_mismatch")
    if not _strict_equal(review.get("prior_blocked_review"), expected_prior):
        _add(errors, "prior_blocked_review_mismatch")

    m42 = _object_json(
        repo_root, REVIEWED_HEAD, M42_MANIFEST_PATH, "m4_2_manifest", errors
    )
    m41 = _object_json(
        repo_root, REVIEWED_HEAD, M41_MANIFEST_PATH, "m4_1_manifest", errors
    )
    m40 = _object_json(
        repo_root, REVIEWED_HEAD, M40_MANIFEST_PATH, "m4_0_manifest", errors
    )
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
        "tasks_per_batch": next(iter(tasks_per_batch))
        if len(tasks_per_batch) == 1
        else -1,
        "passed": len(tasks42) == 60
        and len(batches42) == 6
        and tasks_per_batch == {10},
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
        "passed": source_matches == 60
        and root_matches == 60
        and relative_order
        and inherited_drift == 0,
    }
    if not _strict_equal(review.get("lineage_checks"), expected_lineage):
        _add(errors, "lineage_checks_mismatch")

    recomputed = [_request_binding(task) for task in tasks42]
    request_matches = sum(
        actual == task.get("request_binding_sha256")
        for actual, task in zip(recomputed, tasks42)
    )
    aggregate = _sha256(("\n".join(recomputed) + "\n").encode("utf-8"))
    expected_request_bindings = {
        "algorithm": "m4.2-request-binding-v1",
        "independently_recomputed": len(tasks42),
        "matched": request_matches,
        "unique": len(set(recomputed)),
        "aggregate_sha256": aggregate,
        "helper": _artifact_binding(repo_root, REVIEWED_HEAD, HELPER_PATH, errors),
        "powershell_5_1_request_bindings": 60,
        "passed": request_matches == len(set(recomputed)) == len(tasks42) == 60,
    }
    if not _strict_equal(
        review.get("request_binding_checks"), expected_request_bindings
    ):
        _add(errors, "request_binding_checks_mismatch")

    repair_changed = _diff_paths(
        repo_root,
        REPAIR_PARENT,
        REVIEWED_HEAD,
        errors,
        "repair",
    )
    m3_changed = _diff_paths(
        repo_root,
        REPAIR_PARENT,
        REVIEWED_HEAD,
        errors,
        "historical_m3",
        "evals/m3",
    )
    attributes_raw = _object_blob(
        repo_root, REVIEWED_HEAD, ATTRIBUTES_PATH, errors, "gitattributes"
    )
    policy_line = b"/evals/m3/results/diagnostics-r5.1/** text eol=lf\n"
    if policy_line not in attributes_raw:
        _add(errors, "diagnostics_eol_policy_missing")
    diagnostics_files: list[dict[str, object]] = []
    for path in DIAGNOSTICS_PATHS:
        raw = _object_blob(repo_root, REVIEWED_HEAD, path, errors, "diagnostics")
        binding = {
            "path": path.as_posix(),
            "git_blob_oid": _git_blob_oid(raw),
            "raw_sha256": _sha256(raw),
            "byte_length": len(raw),
            "crlf_count": raw.count(b"\r\n"),
            "lf_count": raw.count(b"\n"),
            "text_attribute": "set",
            "eol_attribute": "lf",
            "worktree_equals_blob": True,
        }
        if verify_git:
            attributes = _check_attributes(repo_root, path)
            if attributes is None:
                _add(errors, "diagnostics_git_attributes_unavailable")
            else:
                binding["text_attribute"] = attributes.get("text", "")
                binding["eol_attribute"] = attributes.get("eol", "")
            try:
                worktree_raw = (repo_root / path).read_bytes()
            except OSError:
                worktree_raw = b""
                _add(errors, "diagnostics_worktree_file_unreadable")
            binding["worktree_equals_blob"] = worktree_raw == raw
            if worktree_raw != raw:
                _add(errors, "diagnostics_worktree_blob_mismatch")
        diagnostics_files.append(binding)
    repair = review.get("repair_evidence")
    repair_ci = repair.get("ci") if isinstance(repair, dict) else None
    if not _repair_ci_semantics(repair_ci):
        _add(errors, "repair_ci_evidence_mismatch")
    expected_repair = {
        "parent_head": REPAIR_PARENT,
        "changed_paths": sorted(REPAIR_CHANGED_PATHS),
        "historical_m3_changed_paths": m3_changed,
        "diagnostics_policy": {
            "pattern": "/evals/m3/results/diagnostics-r5.1/**",
            "text_attribute": "set",
            "eol_attribute": "lf",
            "tracked_file_count": len(DIAGNOSTICS_PATHS),
            "files": diagnostics_files,
        },
        "ci": repair_ci,
    }
    if repair_changed != sorted(REPAIR_CHANGED_PATHS):
        _add(errors, "repair_change_set_mismatch")
    if m3_changed:
        _add(errors, "historical_m3_content_changed")
    if not _strict_equal(repair, expected_repair):
        _add(errors, "repair_evidence_mismatch")

    claim_binding = _artifact_binding(
        repo_root, REVIEWED_HEAD, M41_CLAIM_PATH, errors
    )
    terminal_binding = _artifact_binding(
        repo_root, REVIEWED_HEAD, M41_TERMINAL_PATH, errors
    )
    terminal = _object_json(
        repo_root, REVIEWED_HEAD, M41_TERMINAL_PATH, "m4_1_terminal", errors
    )
    terminal_counts = terminal.get("counts")
    terminal_counts_zero = isinstance(terminal_counts, dict) and bool(
        terminal_counts
    ) and all(type(value) is int and value == 0 for value in terminal_counts.values())
    if not terminal_counts_zero:
        _add(errors, "m4_1_terminal_counts_nonzero")
    expected_historical = {
        "m4_1": {
            "claim": claim_binding,
            "terminal": terminal_binding,
            "terminal_status": "M4_1_STOPPED_PROTOCOL_FAILURE_PRESERVED",
            "tasks": 0,
            "contexts": 0,
            "finalizations": 0,
            "results": 0,
            "retries": 0,
            "repairs": 0,
            "passed": terminal_counts_zero,
        },
        "m3_changed_paths": m3_changed,
        "old_gate_iv_a_rewritten": False,
        "passed": terminal_counts_zero and not m3_changed,
    }
    if not _strict_equal(
        review.get("historical_preservation"), expected_historical
    ):
        _add(errors, "historical_preservation_mismatch")

    changed_paths = _changed_paths(repo_root, errors) if verify_git else set()
    if verify_git and changed_paths != ALLOWED_REVIEW_CHANGES:
        _add(errors, "review_change_set_mismatch")

    discovered = _discover_forbidden_future_paths(repo_root)
    if present_paths:
        discovered.update(path.replace("\\", "/") for path in present_paths)
    forbidden_paths = sorted(discovered)
    if forbidden_paths:
        _add(errors, "forbidden_future_path_present")

    authority = m42.get("authority")
    counters = m42.get("counters")
    expected_zero_state = {
        "preparation_authority": dict(authority)
        if isinstance(authority, dict)
        else {},
        "preparation_counters": dict(counters)
        if isinstance(counters, dict)
        else {},
        "authorization": "ABSENT" if not forbidden_paths else "PRESENT",
        "execution": "ABSENT" if not forbidden_paths else "PRESENT",
        "claim": "ABSENT" if not forbidden_paths else "PRESENT",
        "tasks": 0,
        "results": 0,
        "results_status": "NOT_RUN" if not forbidden_paths else "PRESENT",
        "forbidden_path_count": len(forbidden_paths),
        "forbidden_paths": forbidden_paths,
        "passed": _strict_equal(authority, EXPECTED_AUTHORITY)
        and _strict_equal(counters, EXPECTED_COUNTERS)
        and not forbidden_paths,
    }
    if not _strict_equal(authority, EXPECTED_AUTHORITY):
        _add(errors, "preparation_authority_mismatch")
    if not _strict_equal(counters, EXPECTED_COUNTERS):
        _add(errors, "preparation_counters_mismatch")
    if not _strict_equal(review.get("zero_state"), expected_zero_state):
        _add(errors, "zero_state_mismatch")
    if not _strict_equal(review.get("lifecycle_requirements"), EXPECTED_LIFECYCLE):
        _add(errors, "lifecycle_requirements_mismatch")

    findings = review.get("findings")
    if not isinstance(findings, list):
        findings = []
        _add(errors, "findings_invalid")
    elif findings:
        _add(errors, "review_findings_present")
    side_effects = review.get("reviewer_side_effects")
    if not isinstance(side_effects, list):
        side_effects = []
        _add(errors, "reviewer_side_effects_invalid")
    elif side_effects:
        _add(errors, "reviewer_side_effects_present")
    if _canonical_sha256(review.get("limitations")) != LIMITATIONS_CANONICAL_SHA256:
        _add(errors, "limitations_mismatch")

    delivery_state = _delivery_state(
        repo_root,
        review.get("review_delivery"),
        errors,
        verify_git,
    )
    decision = review.get("decision")
    artifact_status = review.get("status")
    if isinstance(decision, str) and (
        "AUTHORIZE_M4_2_EXECUTION" in decision.upper()
        or decision.upper().startswith("AUTHORIZE_M4_2_")
    ):
        _add(errors, "decision_attempts_execution_authorization")
    if delivery_state == "PROVISIONAL":
        if decision != PROVISIONAL_DECISION or artifact_status != PROVISIONAL_STATUS:
            _add(errors, "provisional_decision_status_mismatch")
    elif delivery_state == "FINAL":
        if decision != FINAL_DECISION or artifact_status != FINAL_STATUS:
            _add(errors, "final_decision_status_mismatch")
    else:
        _add(errors, "decision_status_state_mismatch")

    status = artifact_status if not errors else "BLOCKED"
    return {
        "status": status,
        "decision": decision,
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
        "m4_1_terminal_status": "M4_1_STOPPED_PROTOCOL_FAILURE_PRESERVED",
        "reviewer_side_effects": list(side_effects),
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
    return 0 if not result["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
