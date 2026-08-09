from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
import sys
from collections.abc import Mapping
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
TERMINAL_CLOSURE_HEAD = "e6ae2be7695ce1d2613dcd39e379ff458c1b60fe"
TERMINAL_CLOSURE_CI_RUN_ID = 31301984766
TERMINAL_EVIDENCE_HEAD = "80b54697c3e27a5dad0a24d5318ce26c8fe46141"
SOURCE_PREPARATION_HEAD = "fedc5cdeebd7a2943afeb6767d39841305c55444"
SOURCE_PREPARATION_CI_RUN_ID = 31248424046

CLAIM_SHA256 = "c16a2e53aa2e9215e2325464d547356afdb73897bfc7d29605e0105b9987b3c6"
CLAIM_BYTE_LENGTH = 24078
CLAIM_BLOB = "794058739b96598955216b3960b95b0feea1208f"
TERMINAL_SHA256 = "7305d71ba94cd209f5bb0cb2c977db3bb157d95b907f8f59df9133c192f4d66e"
TERMINAL_BYTE_LENGTH = 3707
TERMINAL_BLOB = "76c7dc1ef88d587741d364536c86e389c296ad5c"
FAILURE_EVIDENCE_SHA256 = (
    "61a18842ac13637f9ba71a5dac6547d1fcbd4355127f97ea213e0ea44941f9c5"
)
SOURCE_PREPARATION_SHA256 = (
    "d66ad9d513d8e64307f9a1553242d9b7d840ea5432d084b06d86707c1b4c2b61"
)
SOURCE_PREPARATION_BYTE_LENGTH = 85962
SOURCE_PREPARATION_BLOB = "42a10d36e4d64ab98aa724114b904001107f557d"

M4_ROOT = Path("evals/m4")
SOURCE_MANIFEST_RELATIVE = M4_ROOT / "revisions/m4.1/preparation-manifest.json"
MANIFEST_RELATIVE = M4_ROOT / "revisions/m4.2/preparation-manifest.json"
HELPER_RELATIVE = M4_ROOT / "execution/prepare_m4_2_request_bundles.ps1"
CLAIM_RELATIVE = M4_ROOT / "execution/m4.1/launch-claim.json"
TERMINAL_RELATIVE = M4_ROOT / "execution/m4.1/execution-terminal.json"
TASK_PROTOCOL_RELATIVE = M4_ROOT / "task-protocol.md"
RUBRIC_RELATIVE = M4_ROOT / "judge-rubric.json"

FROZEN_M3_AND_SKILL_PATHS = (
    "evals/m3",
    "skills/engineering-research-copilot",
)
FROZEN_SHARED_M4_PATHS = (
    "evals/m4/cases",
    "evals/m4/variants",
    "evals/m4/schemas",
    "evals/m4/preparation-manifest.json",
    "evals/m4/build_preparation.py",
    "evals/m4/audit_preparation.py",
    "evals/m4/audit_results.py",
    "evals/m4/task-protocol.md",
    "evals/m4/judge-rubric.json",
    "evals/m4/authorization/gate-iv-review.json",
    "evals/m4/authorization/execution-authorization.json",
    "evals/m4/authorization/execution-control.json",
    "evals/m4/authorization/build_authorization.py",
    "evals/m4/authorization/audit_authorization.py",
    "evals/m4/authorization/execution-authorization.schema.json",
    "evals/m4/authorization/execution-control.schema.json",
    "evals/m4/execution/m4.0",
    "evals/m4/execution/audit_m4_0.py",
    "tests/test_m4_preparation.py",
    "tests/test_m4_results.py",
    "tests/test_m4_authorization.py",
    "tests/test_m4_execution.py",
)
FROZEN_M4_1_PATHS = (
    "evals/m4/build_m4_1_preparation.py",
    "evals/m4/audit_m4_1_preparation.py",
    "evals/m4/revisions/m4.1",
    "evals/m4/authorization/m4.1",
    "evals/m4/authorization/build_m4_1_authorization.py",
    "evals/m4/authorization/audit_m4_1_authorization.py",
    "evals/m4/execution/prepare_m4_1_request_bundles.ps1",
    "evals/m4/execution/audit_m4_1.py",
    "evals/m4/execution/audit_m4_1_launch_readiness.py",
    "evals/m4/execution/audit_m4_1_terminal.py",
    "evals/m4/execution/build_m4_1_launch_claim.py",
    "evals/m4/execution/record_m4_1_execution_evidence.py",
    "evals/m4/execution/m4.1",
    "tests/test_m4_1_preparation.py",
    "tests/test_m4_1_authorization.py",
    "tests/test_m4_1_authorization_builder.py",
    "tests/test_m4_1_execution.py",
    "tests/test_m4_1_launch_readiness.py",
    "tests/test_m4_1_terminal.py",
    "docs/superpowers/plans/2026-08-08-m4.1-successor-preparation-and-authorization.md",
    "docs/superpowers/plans/2026-08-08-m4.1-gate-iv-fresh-execution.md",
    "docs/superpowers/plans/2026-08-08-m4.1-gate-iv-b-launch-readiness.md",
    "docs/superpowers/plans/2026-08-09-m4.1-terminal-closure.md",
)
ALLOWED_CHANGE_PATHS = frozenset(
    {
        ".github/workflows/m1-validation.yml",
        "STATUS.md",
        "docs/superpowers/plans/2026-08-09-m4.2-successor-preparation.md",
        "evals/m4/audit_m4_2_preparation.py",
        "evals/m4/build_m4_2_preparation.py",
        "evals/m4/execution/prepare_m4_2_request_bundles.ps1",
        "evals/m4/revisions/m4.2/preparation-manifest.json",
        "evals/m4/revisions/m4.2/preparation-manifest.schema.json",
        "tests/test_m3_r5_erratum.py",
        "tests/test_m4_2_preparation.py",
    }
)
RAW_LOCKED_PREFIXES = (
    "evals/f04-upstream/",
    "evals/m4/",
    "evals/m3/forward-inputs-r2/",
    "evals/m3/results/forward-r2/",
    "evals/m3/forward-inputs-r3/",
    "evals/m3/results/forward-r3/",
    "evals/m3/forward-inputs-r4/",
    "evals/m3/results/forward-r4/",
    "evals/m3/fixtures/",
    "evals/m3/forward-inputs-r5.1-f02/",
    "evals/m3/results/forward-r5.1-f02/",
    "evals/m3/forward-inputs-r5.2-f02/",
    "evals/m3/results/forward-r5.2-f02/",
    "evals/m3/results/forward-r5.2-aggregate/",
)
RAW_LOCKED_FILES = frozenset(
    {
        "evals/m3/forward-cases-r3.md",
        "evals/m3/forward-cases-r4.md",
        "evals/m3/adversarial-cases.json",
        "evals/m3/r5_2_f02_protocol.py",
        "evals/m3/results/2026-08-05-forward-evaluation-r2.md",
        "evals/m3/results/2026-08-06-forward-evaluation-r3.md",
        "evals/m3/results/2026-08-08-m3.1.1-cross-revision-aggregate-validation.md",
        "evals/m3/results/2026-08-08-m3.1.1-closure-validation.md",
    }
)

TOP_LEVEL_KEYS = {
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
}
PREDECESSOR_KEYS = {
    "terminal_closure_head",
    "terminal_closure_ci_run_id",
    "terminal_closure_ci_conclusion",
    "terminal_evidence_head",
    "launch_claim",
    "execution_terminal",
    "failure_evidence",
    "authorization_token_status",
    "claim_count",
    "terminal_state",
    "failed_stage",
    "successor_revision_required",
    "counts",
    "later_gates",
}
TASK_KEYS = {
    "task_id",
    "source_task_id",
    "root_task_id",
    "blind_id",
    "source_blind_id",
    "root_blind_id",
    "case_id",
    "domain",
    "case_type",
    "arm_id",
    "batch_id",
    "source_batch_id",
    "root_batch_id",
    "case_path",
    "case_sha256",
    "user_input_sha256",
    "task_protocol_sha256",
    "variant_instruction_path",
    "variant_instruction_sha256",
    "rubric_sha256",
    "execution_constraints_sha256",
    "result_root",
    "result_root_must_be_absent",
    "request_binding_sha256",
}
BATCH_KEYS = {
    "batch_id",
    "source_batch_id",
    "root_batch_id",
    "domain",
    "task_ids",
    "source_task_ids",
    "root_task_ids",
    "planned_task_count",
    "stop_on_infrastructure_or_protocol_failure",
    "later_batches_mutable_after_observation",
}
MATRIX_KEYS = {
    "case_count",
    "arm_count",
    "planned_task_count",
    "batch_count",
    "batches",
}
COUNTER_NAMES = {
    "authorized_tasks",
    "created_contexts",
    "dispatched_tasks",
    "finalizations",
    "results_observed",
    "judge_scores",
    "retries",
    "repairs",
    "unauthorized_side_effects",
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
EXPECTED_LIFECYCLE = {
    "claim_aware_post_claim_confirmation_required": True,
    "post_claim_claim_absence_checks_authorized": False,
    "canonical_claim_path_integration_test_required": True,
    "same_revision_continuation_authorized": False,
}
DEFAULT_FORBIDDEN_RELATIVES = {
    "m4_1_results": M4_ROOT / "results/m4.1",
    "m4_2_authorization": M4_ROOT / "authorization/m4.2",
    "m4_2_execution": M4_ROOT / "execution/m4.2",
    "m4_2_results": M4_ROOT / "results/m4.2",
    "results_manifest": M4_ROOT / "results-manifest.json",
}


def _add(errors: list[str], code: str) -> None:
    if code not in errors:
        errors.append(code)


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _strict_equal(actual: object, expected: object) -> bool:
    if type(actual) is not type(expected):
        return False
    if isinstance(expected, dict):
        return set(actual) == set(expected) and all(
            _strict_equal(actual[key], value) for key, value in expected.items()
        )
    if isinstance(expected, list):
        return len(actual) == len(expected) and all(
            _strict_equal(left, right)
            for left, right in zip(actual, expected, strict=True)
        )
    return actual == expected


def _path_present(path: Any) -> bool:
    if path.exists() or path.is_symlink():
        return True
    is_junction = getattr(path, "is_junction", None)
    if callable(is_junction) and is_junction():
        return True
    try:
        return os.path.lexists(path)
    except TypeError:
        return False


def _git_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment["GIT_NO_REPLACE_OBJECTS"] = "1"
    return environment


@contextmanager
def _git_replacements_disabled():
    previous = os.environ.get("GIT_NO_REPLACE_OBJECTS")
    os.environ["GIT_NO_REPLACE_OBJECTS"] = "1"
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("GIT_NO_REPLACE_OBJECTS", None)
        else:
            os.environ["GIT_NO_REPLACE_OBJECTS"] = previous


def _validate_bound_input_bytes(
    repo_root: Path, tasks: list[dict[str, Any]], errors: list[str]
) -> None:
    canonical_root = repo_root.resolve(strict=False)
    cache: dict[str, bytes | None] = {}

    def read_relative(relative: object, label: str) -> bytes | None:
        if type(relative) is not str or not relative:
            _add(errors, f"{label}_path_invalid")
            return None
        if relative in cache:
            return cache[relative]
        candidate = (canonical_root / relative).resolve(strict=False)
        try:
            candidate.relative_to(canonical_root)
        except ValueError:
            _add(errors, f"{label}_path_invalid")
            cache[relative] = None
            return None
        try:
            raw = candidate.read_bytes()
        except OSError:
            _add(errors, f"{label}_missing")
            cache[relative] = None
            return None
        cache[relative] = raw
        return raw

    for task in tasks:
        case_raw = read_relative(task.get("case_path"), "case")
        if case_raw is not None:
            if not _strict_equal(_sha256(case_raw), task.get("case_sha256")):
                _add(errors, "case_raw_sha256_mismatch")
            try:
                case = json.loads(case_raw.decode("utf-8"))
            except (UnicodeError, json.JSONDecodeError):
                case = None
                _add(errors, "case_json_invalid")
            user_input = case.get("user_input") if isinstance(case, dict) else None
            if type(user_input) is not str:
                _add(errors, "case_user_input_invalid")
            elif not _strict_equal(
                _sha256(user_input.encode("utf-8")), task.get("user_input_sha256")
            ):
                _add(errors, "user_input_sha256_mismatch")

        protocol_raw = read_relative(
            TASK_PROTOCOL_RELATIVE.as_posix(), "task_protocol"
        )
        if protocol_raw is not None and not _strict_equal(
            _sha256(protocol_raw), task.get("task_protocol_sha256")
        ):
            _add(errors, "task_protocol_raw_sha256_mismatch")

        variant_relative = task.get("variant_instruction_path")
        variant_sha256 = task.get("variant_instruction_sha256")
        if variant_relative is None:
            if variant_sha256 is not None:
                _add(errors, "variant_instruction_binding_invalid")
        else:
            variant_raw = read_relative(variant_relative, "variant_instruction")
            if variant_raw is not None and not _strict_equal(
                _sha256(variant_raw), variant_sha256
            ):
                _add(errors, "variant_instruction_raw_sha256_mismatch")

        rubric_raw = read_relative(RUBRIC_RELATIVE.as_posix(), "rubric")
        if rubric_raw is not None and not _strict_equal(
            _sha256(rubric_raw), task.get("rubric_sha256")
        ):
            _add(errors, "rubric_raw_sha256_mismatch")


def _load_object(path: Path, label: str, errors: list[str]) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
    except OSError:
        _add(errors, f"{label}_missing")
        return {}, b""
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError):
        _add(errors, f"{label}_invalid_json")
        return {}, raw
    if not isinstance(value, dict):
        _add(errors, f"{label}_not_object")
        return {}, raw
    return value, raw


def _git(repo_root: Path, *arguments: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *arguments],
        cwd=repo_root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=_git_environment(),
    )


def _git_text(repo_root: Path, *arguments: str) -> str:
    completed = _git(repo_root, *arguments)
    if completed.returncode != 0:
        raise RuntimeError(
            completed.stderr.decode("utf-8", errors="replace").strip()
            or f"git {' '.join(arguments)} failed"
        )
    return completed.stdout.decode("utf-8").strip()


def _load_module(path: Path, name: str) -> ModuleType:
    source = path.read_bytes()
    module = ModuleType(name)
    module.__file__ = str(path)
    module.__package__ = name.rpartition(".")[0]
    previous = sys.modules.get(name)
    previous_dont_write_bytecode = sys.dont_write_bytecode
    sys.modules[name] = module
    sys.dont_write_bytecode = True
    try:
        exec(compile(source, str(path), "exec"), module.__dict__)
    finally:
        sys.dont_write_bytecode = previous_dont_write_bytecode
        if previous is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = previous
    return module


def _commit_is_available_and_ancestor(
    repo_root: Path, head: str, label: str, errors: list[str]
) -> bool:
    if _git(repo_root, "cat-file", "-e", f"{head}^{{commit}}").returncode != 0:
        _add(errors, f"{label}_unavailable")
        return False
    if _git(repo_root, "merge-base", "--is-ancestor", head, "HEAD").returncode != 0:
        _add(errors, f"{label}_not_ancestor")
        return False
    return True


def _collect_changed_paths(
    repo_root: Path,
    baseline: str,
    paths: tuple[str, ...],
    label: str,
    errors: list[str],
) -> list[str]:
    changed: set[str] = set()
    pathspec = ("--", *paths) if paths else ()
    for arguments in (
        (
            "diff",
            "--no-ext-diff",
            "--no-textconv",
            "--name-only",
            baseline,
            "HEAD",
            *pathspec,
        ),
        (
            "diff",
            "--cached",
            "--no-ext-diff",
            "--no-textconv",
            "--name-only",
            baseline,
            *pathspec,
        ),
        ("ls-files", "--others", "--exclude-standard", *pathspec),
    ):
        completed = _git(repo_root, *arguments)
        if completed.returncode != 0:
            _add(errors, f"{label}_git_check_failed")
            continue
        changed.update(
            line.strip()
            for line in completed.stdout.decode("utf-8").splitlines()
            if line.strip()
        )
    return sorted(changed)


def _changed_paths(
    repo_root: Path,
    baseline: str,
    paths: tuple[str, ...],
    label: str,
    errors: list[str],
) -> list[str]:
    changed = _collect_changed_paths(repo_root, baseline, paths, label, errors)
    if changed:
        _add(errors, f"{label}_changed")
    return changed


def _worktree_changed_paths(
    repo_root: Path,
    baseline: str,
    paths: tuple[str, ...],
    label: str,
    errors: list[str],
    *,
    excluded_paths: frozenset[str] = frozenset(),
) -> list[str]:
    tree = _git(repo_root, "ls-tree", "-r", "-z", baseline, "--", *paths)
    if tree.returncode != 0:
        _add(errors, f"{label}_git_check_failed")
        return []

    entries: list[tuple[str, str, str]] = []
    try:
        for record in tree.stdout.split(b"\0"):
            if not record:
                continue
            metadata, path_bytes = record.split(b"\t", 1)
            mode, object_type, oid = metadata.split(b" ", 2)
            if object_type != b"blob":
                raise ValueError("non_blob_entry")
            path = path_bytes.decode("utf-8")
            if "\n" in path or "\r" in path:
                raise ValueError("unsupported_path")
            if path not in excluded_paths:
                entries.append(
                    (mode.decode("ascii"), oid.decode("ascii"), path)
                )
    except (UnicodeError, ValueError):
        _add(errors, f"{label}_tree_parse_failed")
        return []
    if not entries:
        return []

    batch_input = b"".join(f"{oid}\n".encode("ascii") for _mode, oid, _path in entries)
    batch = subprocess.run(
        ["git", "cat-file", "--batch"],
        cwd=repo_root,
        check=False,
        input=batch_input,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=_git_environment(),
    )
    if batch.returncode != 0:
        _add(errors, f"{label}_blob_check_failed")
        return []

    expected_by_path: dict[str, bytes] = {}
    offset = 0
    try:
        for _mode, oid, path in entries:
            header_end = batch.stdout.index(b"\n", offset)
            header = batch.stdout[offset:header_end].split()
            if len(header) != 3 or header[0].decode("ascii") != oid:
                raise ValueError("batch_header_invalid")
            size = int(header[2].decode("ascii"))
            content_start = header_end + 1
            content_end = content_start + size
            if content_end >= len(batch.stdout) or batch.stdout[content_end] != 10:
                raise ValueError("batch_content_invalid")
            expected_by_path[path] = batch.stdout[content_start:content_end]
            offset = content_end + 1
        if offset != len(batch.stdout):
            raise ValueError("batch_trailing_output")
    except (UnicodeError, ValueError):
        _add(errors, f"{label}_blob_parse_failed")
        return []

    changed: list[str] = []
    for mode, _oid, path in entries:
        candidate = repo_root / path
        is_junction = getattr(candidate, "is_junction", None)
        try:
            metadata = candidate.lstat()
        except OSError:
            changed.append(path)
            continue
        if mode == "120000":
            if not candidate.is_symlink():
                changed.append(path)
                continue
            try:
                actual = os.fsencode(os.readlink(candidate))
            except OSError:
                changed.append(path)
                continue
        elif mode in {"100644", "100755"}:
            if (
                not stat.S_ISREG(metadata.st_mode)
                or candidate.is_symlink()
                or (callable(is_junction) and is_junction())
            ):
                changed.append(path)
                continue
            if os.name != "nt":
                expected_executable = mode == "100755"
                actual_executable = bool(
                    metadata.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                )
                if actual_executable != expected_executable:
                    changed.append(path)
                    continue
            try:
                actual = candidate.read_bytes()
            except OSError:
                changed.append(path)
                continue
        else:
            changed.append(path)
            continue
        expected = expected_by_path[path]
        raw_locked = path in RAW_LOCKED_FILES or any(
            path.startswith(prefix) for prefix in RAW_LOCKED_PREFIXES
        )
        if raw_locked:
            matches = actual == expected
        else:
            try:
                actual.decode("utf-8")
                expected.decode("utf-8")
            except UnicodeError:
                matches = actual == expected
            else:
                matches = actual.replace(b"\r\n", b"\n") == expected.replace(
                    b"\r\n", b"\n"
                )
        if not matches:
            changed.append(path)
    changed = sorted(set(changed))
    if changed:
        _add(errors, f"{label}_changed")
    return changed


def _frozen_changed_paths(
    repo_root: Path,
    baseline: str,
    paths: tuple[str, ...],
    label: str,
    errors: list[str],
) -> list[str]:
    canonical = _changed_paths(repo_root, baseline, paths, label, errors)
    worktree = _worktree_changed_paths(
        repo_root, baseline, paths, f"{label}_worktree", errors
    )
    return sorted(set(canonical) | set(worktree))


def _unexpected_repo_changes(
    repo_root: Path, baseline: str, errors: list[str]
) -> list[str]:
    changed = _collect_changed_paths(repo_root, baseline, (), "repository", errors)
    changed.extend(
        _worktree_changed_paths(
            repo_root,
            baseline,
            (),
            "repository_worktree",
            errors,
            excluded_paths=ALLOWED_CHANGE_PATHS,
        )
    )
    unexpected = sorted(set(changed) - ALLOWED_CHANGE_PATHS)
    if unexpected:
        _add(errors, "unexpected_repository_change")
    return unexpected


def _expected_task_id(source_task_id: str) -> str | None:
    if not source_task_id.startswith("M4.1-") or source_task_id.startswith(
        "M4.1-BATCH-"
    ):
        return None
    return "M4.2-" + source_task_id.removeprefix("M4.1-")


def _expected_batch_id(source_batch_id: str) -> str | None:
    if not source_batch_id.startswith("M4.1-BATCH-"):
        return None
    return "M4.2-BATCH-" + source_batch_id.removeprefix("M4.1-BATCH-")


def _expected_request_hash(task: Mapping[str, object]) -> str:
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
    return _sha256(("\n".join(fields) + "\n").encode("utf-8"))


def _validate_predecessor(
    manifest: dict[str, Any], terminal: dict[str, Any], errors: list[str]
) -> None:
    predecessor = manifest.get("predecessor")
    if not isinstance(predecessor, dict):
        _add(errors, "predecessor_invalid")
        return
    if set(predecessor) != PREDECESSOR_KEYS:
        _add(errors, "predecessor_shape_invalid")
    expected_claim = {
        "path": CLAIM_RELATIVE.as_posix(),
        "byte_length": CLAIM_BYTE_LENGTH,
        "sha256": CLAIM_SHA256,
        "git_blob_oid": CLAIM_BLOB,
    }
    expected_terminal = {
        "path": TERMINAL_RELATIVE.as_posix(),
        "byte_length": TERMINAL_BYTE_LENGTH,
        "sha256": TERMINAL_SHA256,
        "git_blob_oid": TERMINAL_BLOB,
    }
    expected_failure = {
        "raw_evidence_sha256": FAILURE_EVIDENCE_SHA256,
        "observed_protocol_error": "authorization_already_claimed",
    }
    if not _strict_equal(predecessor.get("launch_claim"), expected_claim):
        _add(errors, "predecessor_claim_binding_invalid")
    if not _strict_equal(predecessor.get("execution_terminal"), expected_terminal):
        _add(errors, "predecessor_terminal_binding_invalid")
    if not _strict_equal(predecessor.get("failure_evidence"), expected_failure):
        _add(errors, "predecessor_failure_evidence_invalid")
    expected_scalar = {
        "terminal_closure_head": TERMINAL_CLOSURE_HEAD,
        "terminal_closure_ci_run_id": TERMINAL_CLOSURE_CI_RUN_ID,
        "terminal_closure_ci_conclusion": "success",
        "terminal_evidence_head": TERMINAL_EVIDENCE_HEAD,
        "authorization_token_status": "CONSUMED",
        "claim_count": 1,
        "terminal_state": "STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE",
        "failed_stage": "post_claim_dual_confirmation",
        "successor_revision_required": True,
    }
    if any(
        not _strict_equal(predecessor.get(key), value)
        for key, value in expected_scalar.items()
    ):
        _add(errors, "predecessor_invalid")
    if not _strict_equal(predecessor.get("counts"), terminal.get("counts")):
        _add(errors, "predecessor_counts_invalid")
    if not _strict_equal(predecessor.get("later_gates"), terminal.get("later_gates")):
        _add(errors, "predecessor_later_gates_invalid")


def _validate_source_binding(
    manifest: dict[str, Any], source_tasks: list[dict[str, Any]], errors: list[str]
) -> None:
    source_ids = [str(task.get("task_id")) for task in source_tasks]
    expected = {
        "path": SOURCE_MANIFEST_RELATIVE.as_posix(),
        "head": SOURCE_PREPARATION_HEAD,
        "ci_run_id": SOURCE_PREPARATION_CI_RUN_ID,
        "ci_conclusion": "success",
        "byte_length": SOURCE_PREPARATION_BYTE_LENGTH,
        "raw_sha256": SOURCE_PREPARATION_SHA256,
        "git_blob_oid": SOURCE_PREPARATION_BLOB,
        "task_count": 60,
        "source_order_sha256": _sha256(
            ("\n".join(source_ids) + "\n").encode("utf-8")
        ),
    }
    if not _strict_equal(manifest.get("source_preparation"), expected):
        _add(errors, "source_preparation_binding_invalid")


def _validate_tasks(
    manifest: dict[str, Any], source: dict[str, Any], errors: list[str]
) -> tuple[list[dict[str, Any]], int]:
    source_tasks_value = source.get("tasks")
    source_tasks = (
        [item for item in source_tasks_value if isinstance(item, dict)]
        if isinstance(source_tasks_value, list)
        else []
    )
    tasks_value = manifest.get("tasks")
    tasks = (
        [item for item in tasks_value if isinstance(item, dict)]
        if isinstance(tasks_value, list)
        else []
    )
    if len(source_tasks) != 60:
        _add(errors, "source_task_count_invalid")
    if len(tasks) != 60 or len(tasks) != len(tasks_value or []):
        _add(errors, "planned_task_count_invalid")
    source_ids = {str(task.get("task_id")) for task in source_tasks}
    root_ids = {str(task.get("source_task_id")) for task in source_tasks}
    source_blinds = {str(task.get("blind_id")) for task in source_tasks}
    root_blinds = {str(task.get("source_blind_id")) for task in source_tasks}
    reused_task_id_count = 0
    if len(tasks) == len(source_tasks):
        for index, (task, source_task) in enumerate(
            zip(tasks, source_tasks, strict=True), start=121
        ):
            if set(task) != TASK_KEYS:
                _add(errors, "task_shape_invalid")
            task_id = str(task.get("task_id"))
            source_task_id = str(source_task.get("task_id"))
            root_task_id = str(source_task.get("source_task_id"))
            expected_task_id = _expected_task_id(source_task_id)
            if task_id in source_ids or task_id in root_ids:
                reused_task_id_count += 1
                _add(errors, "task_id_reused")
            if task_id != expected_task_id:
                _add(errors, "task_id_projection_invalid")
            if not _strict_equal(task.get("source_task_id"), source_task_id):
                _add(errors, "source_task_lineage_invalid")
            if not _strict_equal(task.get("root_task_id"), root_task_id):
                _add(errors, "root_task_lineage_invalid")
            expected_blind = f"M4-J{index:03d}"
            blind = str(task.get("blind_id"))
            if blind in source_blinds or blind in root_blinds:
                _add(errors, "blind_id_reused")
            if blind != expected_blind:
                _add(errors, "blind_id_projection_invalid")
            if not _strict_equal(task.get("source_blind_id"), source_task.get("blind_id")):
                _add(errors, "source_blind_lineage_invalid")
            if not _strict_equal(
                task.get("root_blind_id"), source_task.get("source_blind_id")
            ):
                _add(errors, "root_blind_lineage_invalid")
            expected_batch = _expected_batch_id(str(source_task.get("batch_id")))
            if task.get("batch_id") != expected_batch:
                _add(errors, "task_batch_projection_invalid")
            if not _strict_equal(task.get("source_batch_id"), source_task.get("batch_id")):
                _add(errors, "task_source_batch_lineage_invalid")
            if not _strict_equal(
                task.get("root_batch_id"), source_task.get("source_batch_id")
            ):
                _add(errors, "task_root_batch_lineage_invalid")
            for key in INHERITED_TASK_KEYS:
                if not _strict_equal(task.get(key), source_task.get(key)):
                    _add(errors, "inherited_task_input_changed")
            expected_root = f"evals/m4/results/m4.2/{expected_task_id}"
            if task.get("result_root") != expected_root:
                _add(errors, "result_root_invalid")
            if task.get("result_root_must_be_absent") is not True:
                _add(errors, "result_root_absence_gate_missing")
            try:
                expected_hash = _expected_request_hash(task)
            except (KeyError, TypeError, ValueError):
                expected_hash = None
                _add(errors, "request_binding_input_invalid")
            if task.get("request_binding_sha256") != expected_hash:
                _add(errors, "request_binding_mismatch")
        if [task.get("source_task_id") for task in tasks] != [
            task.get("task_id") for task in source_tasks
        ]:
            _add(errors, "task_order_changed")
    if len({str(task.get("task_id")) for task in tasks}) != len(tasks):
        _add(errors, "task_id_duplicate")
    if len({str(task.get("blind_id")) for task in tasks}) != len(tasks):
        _add(errors, "blind_id_duplicate")
    return tasks, reused_task_id_count


def _validate_batches(
    manifest: dict[str, Any], source: dict[str, Any], tasks: list[dict[str, Any]], errors: list[str]
) -> int:
    matrix = manifest.get("matrix")
    source_matrix = source.get("matrix")
    if not isinstance(matrix, dict) or not isinstance(source_matrix, dict):
        _add(errors, "matrix_invalid")
        return 0
    if set(matrix) != MATRIX_KEYS:
        _add(errors, "matrix_shape_invalid")
    scalar_expected = {
        "case_count": 12,
        "arm_count": 5,
        "planned_task_count": 60,
        "batch_count": 6,
    }
    if any(
        not _strict_equal(matrix.get(key), value)
        for key, value in scalar_expected.items()
    ):
        _add(errors, "matrix_counts_invalid")
    batches_value = matrix.get("batches")
    source_batches_value = source_matrix.get("batches")
    batches = (
        [item for item in batches_value if isinstance(item, dict)]
        if isinstance(batches_value, list)
        else []
    )
    source_batches = (
        [item for item in source_batches_value if isinstance(item, dict)]
        if isinstance(source_batches_value, list)
        else []
    )
    if len(batches) != 6 or len(source_batches) != 6:
        _add(errors, "batch_count_invalid")
        return len(batches)
    task_map = {str(task.get("source_task_id")): task for task in tasks}
    source_batch_ids = {str(batch.get("batch_id")) for batch in source_batches}
    root_batch_ids = {str(batch.get("source_batch_id")) for batch in source_batches}
    for batch, source_batch in zip(batches, source_batches, strict=True):
        if set(batch) != BATCH_KEYS:
            _add(errors, "batch_shape_invalid")
        batch_id = str(batch.get("batch_id"))
        source_batch_id = str(source_batch.get("batch_id"))
        root_batch_id = str(source_batch.get("source_batch_id"))
        if batch_id in source_batch_ids or batch_id in root_batch_ids:
            _add(errors, "batch_id_reused")
        if batch_id != _expected_batch_id(source_batch_id):
            _add(errors, "batch_id_projection_invalid")
        if not _strict_equal(batch.get("source_batch_id"), source_batch_id):
            _add(errors, "source_batch_lineage_invalid")
        if not _strict_equal(batch.get("root_batch_id"), root_batch_id):
            _add(errors, "root_batch_lineage_invalid")
        if not _strict_equal(batch.get("domain"), source_batch.get("domain")):
            _add(errors, "batch_domain_changed")
        source_task_ids = [str(value) for value in source_batch.get("task_ids", [])]
        root_task_ids = [str(value) for value in source_batch.get("source_task_ids", [])]
        expected_task_ids = [
            str(task_map.get(value, {}).get("task_id")) for value in source_task_ids
        ]
        if not _strict_equal(batch.get("task_ids"), expected_task_ids):
            _add(errors, "batch_task_ids_invalid")
        if not _strict_equal(batch.get("source_task_ids"), source_task_ids):
            _add(errors, "batch_source_task_ids_invalid")
        if not _strict_equal(batch.get("root_task_ids"), root_task_ids):
            _add(errors, "batch_root_task_ids_invalid")
        if not _strict_equal(batch.get("planned_task_count"), 10):
            _add(errors, "batch_planned_task_count_invalid")
        if batch.get("stop_on_infrastructure_or_protocol_failure") is not True:
            _add(errors, "batch_stop_policy_invalid")
        if batch.get("later_batches_mutable_after_observation") is not False:
            _add(errors, "batch_mutability_invalid")
    return len(batches)


def _validate_randomization_and_helper(
    repo_root: Path,
    manifest: dict[str, Any],
    source: dict[str, Any],
    tasks: list[dict[str, Any]],
    errors: list[str],
) -> int:
    source_order = source.get("randomization", {}).get("task_order")
    source_to_task = {
        str(task.get("source_task_id")): str(task.get("task_id")) for task in tasks
    }
    expected_order = (
        [source_to_task.get(str(value)) for value in source_order]
        if isinstance(source_order, list)
        else []
    )
    expected_randomization = {
        "frozen": True,
        "policy": "INHERITED_M4_1_RELATIVE_ORDER_WITH_DISJOINT_IDENTITIES",
        "source_seed": source.get("randomization", {}).get("source_seed"),
        "task_order": expected_order,
        "blind_mapping": {
            str(task.get("task_id")): str(task.get("blind_id")) for task in tasks
        },
        "judge_mapping_access_authorized": False,
    }
    if not _strict_equal(manifest.get("randomization"), expected_randomization):
        _add(errors, "randomization_invalid")
    helper = manifest.get("execution_helper")
    helper_path = repo_root / HELPER_RELATIVE
    try:
        helper_hash = _sha256(helper_path.read_bytes())
    except OSError:
        helper_hash = None
        _add(errors, "execution_helper_missing")
    expected_helper = {
        "path": HELPER_RELATIVE.as_posix(),
        "raw_sha256": helper_hash,
        "read_only": True,
        "minimum_windows_powershell_version": "5.1",
        "request_binding_count": 60,
    }
    if not _strict_equal(helper, expected_helper):
        _add(errors, "execution_helper_binding_invalid")
    return len(
        {
            task.get("request_binding_sha256")
            for task in tasks
            if isinstance(task.get("request_binding_sha256"), str)
        }
    )


def audit_preparation(
    repo_root: Path = REPO_ROOT,
    *,
    manifest_path: Path | None = None,
    forbidden_path_overrides: Mapping[str, Path] | None = None,
    verify_git: bool = True,
) -> dict[str, object]:
    """Return one deterministic preparation-only audit result without writing."""

    repo_root = repo_root.resolve()
    manifest_path = manifest_path or (repo_root / MANIFEST_RELATIVE)
    errors: list[str] = []
    manifest, _manifest_raw = _load_object(manifest_path, "preparation_manifest", errors)
    source, source_raw = _load_object(
        repo_root / SOURCE_MANIFEST_RELATIVE, "source_preparation", errors
    )
    _claim, claim_raw = _load_object(repo_root / CLAIM_RELATIVE, "m4_1_claim", errors)
    terminal, terminal_raw = _load_object(
        repo_root / TERMINAL_RELATIVE, "m4_1_terminal", errors
    )
    if len(source_raw) != SOURCE_PREPARATION_BYTE_LENGTH or _sha256(
        source_raw
    ) != SOURCE_PREPARATION_SHA256:
        _add(errors, "source_preparation_raw_binding_invalid")
    if len(claim_raw) != CLAIM_BYTE_LENGTH or _sha256(claim_raw) != CLAIM_SHA256:
        _add(errors, "m4_1_claim_raw_binding_invalid")
    if len(terminal_raw) != TERMINAL_BYTE_LENGTH or _sha256(
        terminal_raw
    ) != TERMINAL_SHA256:
        _add(errors, "m4_1_terminal_raw_binding_invalid")

    if set(manifest) != TOP_LEVEL_KEYS:
        _add(errors, "preparation_shape_invalid")
    if manifest.get("schema_version") != "m4.2-successor-preparation-v1":
        _add(errors, "preparation_schema_version_invalid")
    if (
        manifest.get("milestone") != "M4"
        or manifest.get("revision") != "M4.2"
        or manifest.get("status") != "PREPARATION_ONLY"
    ):
        _add(errors, "preparation_identity_invalid")

    _validate_predecessor(manifest, terminal, errors)
    source_tasks_value = source.get("tasks")
    source_tasks = (
        [item for item in source_tasks_value if isinstance(item, dict)]
        if isinstance(source_tasks_value, list)
        else []
    )
    _validate_source_binding(manifest, source_tasks, errors)
    if not _strict_equal(manifest.get("authority"), EXPECTED_AUTHORITY):
        _add(errors, "preparation_authority_invalid")
    fresh_execution_authorized = (
        manifest.get("authority", {}).get("fresh_execution_authorized")
        if isinstance(manifest.get("authority"), dict)
        else None
    )
    if fresh_execution_authorized is not False:
        _add(errors, "fresh_execution_authorized")
    if not _strict_equal(manifest.get("lifecycle_requirements"), EXPECTED_LIFECYCLE):
        _add(errors, "lifecycle_requirements_invalid")
    counters = manifest.get("counters")
    if not isinstance(counters, dict) or set(counters) != COUNTER_NAMES:
        _add(errors, "execution_counters_invalid")
        counters = counters if isinstance(counters, dict) else {}
    if any(type(value) is not int for value in counters.values()):
        _add(errors, "execution_counter_type_invalid")
    if any(type(value) is int and value != 0 for value in counters.values()):
        _add(errors, "execution_counter_nonzero")

    tasks, reused_task_id_count = _validate_tasks(manifest, source, errors)
    _validate_bound_input_bytes(repo_root, tasks, errors)
    batch_count = _validate_batches(manifest, source, tasks, errors)
    request_binding_count = _validate_randomization_and_helper(
        repo_root, manifest, source, tasks, errors
    )
    try:
        builder = _load_module(
            repo_root / "evals/m4/build_m4_2_preparation.py",
            "m4_2_preparation_builder_for_audit",
        )
        with _git_replacements_disabled():
            regenerated = builder.build_preparation(repo_root, write=False)
        if manifest != regenerated:
            _add(errors, "preparation_manifest_regeneration_mismatch")
    except (
        AttributeError,
        OSError,
        TypeError,
        UnicodeError,
        json.JSONDecodeError,
        RuntimeError,
        ValueError,
    ):
        _add(errors, "preparation_regeneration_failed")

    forbidden_paths = {
        key: repo_root / relative for key, relative in DEFAULT_FORBIDDEN_RELATIVES.items()
    }
    if forbidden_path_overrides:
        for key, path in forbidden_path_overrides.items():
            if key in forbidden_paths:
                forbidden_paths[key] = path
    present_forbidden: list[str] = []
    for key, path in forbidden_paths.items():
        if _path_present(path):
            present_forbidden.append(key)
            _add(errors, f"{key}_present")

    m4_1_terminal_status: object = None
    try:
        terminal_module = _load_module(
            repo_root / "evals/m4/execution/audit_m4_1_terminal.py",
            "m4_1_terminal_audit_for_m4_2",
        )
        with _git_replacements_disabled():
            terminal_audit = terminal_module.audit_terminal(
                repo_root, verify_git=verify_git
            )
        m4_1_terminal_status = terminal_audit.get("status")
        if m4_1_terminal_status != "M4_1_STOPPED_PROTOCOL_FAILURE_PRESERVED":
            _add(errors, "m4_1_terminal_audit_failed")
    except (ImportError, OSError, RuntimeError, TypeError, ValueError):
        _add(errors, "m4_1_terminal_audit_failed")

    m3_or_skill_changed_paths: list[str] = []
    shared_m4_changed_paths: list[str] = []
    m4_1_changed_paths: list[str] = []
    unexpected_changed_paths: list[str] = []
    if verify_git:
        closure_available = _commit_is_available_and_ancestor(
            repo_root, TERMINAL_CLOSURE_HEAD, "terminal_closure_head", errors
        )
        evidence_available = _commit_is_available_and_ancestor(
            repo_root, TERMINAL_EVIDENCE_HEAD, "terminal_evidence_head", errors
        )
        source_available = _commit_is_available_and_ancestor(
            repo_root, SOURCE_PREPARATION_HEAD, "source_preparation_head", errors
        )
        if evidence_available:
            try:
                if (
                    _git_text(
                        repo_root,
                        "rev-parse",
                        f"{TERMINAL_EVIDENCE_HEAD}:{CLAIM_RELATIVE.as_posix()}",
                    )
                    != CLAIM_BLOB
                ):
                    _add(errors, "m4_1_claim_git_blob_mismatch")
                if (
                    _git_text(
                        repo_root,
                        "rev-parse",
                        f"{TERMINAL_EVIDENCE_HEAD}:{TERMINAL_RELATIVE.as_posix()}",
                    )
                    != TERMINAL_BLOB
                ):
                    _add(errors, "m4_1_terminal_git_blob_mismatch")
            except RuntimeError:
                _add(errors, "terminal_evidence_git_lookup_failed")
        if source_available:
            try:
                if (
                    _git_text(
                        repo_root,
                        "rev-parse",
                        f"{SOURCE_PREPARATION_HEAD}:{SOURCE_MANIFEST_RELATIVE.as_posix()}",
                    )
                    != SOURCE_PREPARATION_BLOB
                ):
                    _add(errors, "source_preparation_git_blob_mismatch")
            except RuntimeError:
                _add(errors, "source_preparation_git_lookup_failed")
        if closure_available:
            unexpected_changed_paths = _unexpected_repo_changes(
                repo_root, TERMINAL_CLOSURE_HEAD, errors
            )
            m3_or_skill_changed_paths = _frozen_changed_paths(
                repo_root,
                TERMINAL_CLOSURE_HEAD,
                FROZEN_M3_AND_SKILL_PATHS,
                "m3_or_skill",
                errors,
            )
            shared_m4_changed_paths = _frozen_changed_paths(
                repo_root,
                TERMINAL_CLOSURE_HEAD,
                FROZEN_SHARED_M4_PATHS,
                "shared_m4",
                errors,
            )
            m4_1_changed_paths = _frozen_changed_paths(
                repo_root,
                TERMINAL_CLOSURE_HEAD,
                FROZEN_M4_1_PATHS,
                "m4_1",
                errors,
            )

    return {
        "status": "M4_2_PREPARED_NOT_AUTHORIZED" if not errors else "INVALID",
        "errors": sorted(errors),
        "planned_task_count": len(tasks),
        "reused_task_id_count": reused_task_id_count,
        "batch_count": batch_count,
        "request_binding_count": request_binding_count,
        "fresh_execution_authorized": fresh_execution_authorized,
        "execution_counters": counters,
        "forbidden_path_count": len(present_forbidden),
        "forbidden_paths": sorted(present_forbidden),
        "m4_1_terminal_status": m4_1_terminal_status,
        "terminal_closure_head": TERMINAL_CLOSURE_HEAD,
        "m3_or_skill_changed_paths": m3_or_skill_changed_paths,
        "shared_m4_changed_paths": shared_m4_changed_paths,
        "m4_1_changed_paths": m4_1_changed_paths,
        "unexpected_changed_paths": unexpected_changed_paths,
        "side_effects": [],
    }


def main() -> int:
    result = audit_preparation()
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return 0 if result["status"] == "M4_2_PREPARED_NOT_AUTHORIZED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
