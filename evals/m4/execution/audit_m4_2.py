#!/usr/bin/env python3
"""Read-only M4.2 whole-matrix claim/execution lifecycle auditor.

Gate A deliberately leaves every real execution path absent.  This module
contains the post-claim state machine used by future Gate B work, but its CLI
is read-only and defaults to the repository's READY_UNCLAIMED state.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence


REPO_ROOT = Path(__file__).resolve().parents[3]
REVISION = "M4.2"
MILESTONE = "M4"
AUTHORIZATION_CLOSURE_HEAD = "88410ce0ee640645aa44e1ba1289789532fd647a"
AUTHORIZATION_CLOSURE_TREE = "77925b9a3df09d03f9ca7848caced78e34e10a35"
GATE_A_BASELINE_HEAD = "214acacfb984b3f9e41d35dde8841a4ffb342b34"
GATE_A_BASELINE_TREE = "7671e69844ea59a84411b6bcbfb9abf0feb64ae9"
AUTHORIZATION_BRANCH = (
    "codex/m4-cross-engineering-forward-evaluation-m4.2-one-shot-authorization"
)
EXECUTION_BRANCH = (
    "codex/m4-cross-engineering-forward-evaluation-m4.2-one-shot-claim-and-execution"
)
MODEL_ID = "gpt-5.6-sol"
REASONING_EFFORT = "max"
PROJECT_ID = "ff35b25f-4644-41c8-9073-74c697559439"

AUTHORIZATION_RELATIVE = Path(
    "evals/m4/authorization/m4.2/execution-authorization.json"
)
CONTROL_RELATIVE = Path("evals/m4/authorization/m4.2/execution-control.json")
AUTHORIZATION_PATH = REPO_ROOT / AUTHORIZATION_RELATIVE
CONTROL_PATH = REPO_ROOT / CONTROL_RELATIVE
AUTHORIZATION_BLOB = "0b83a74642a89440cf7df22c3eeb92ec180c8d5a"
CONTROL_BLOB = "04ca77769553f50c0b74f50ab8f239950a2b9a6d"
AUTHORIZATION_RAW_SHA256 = (
    "dc73c9376bdd78cf7e0d355701c8c3fe6966c34db5a1203544b9d95ab88e719b"
)
CONTROL_RAW_SHA256 = (
    "c482386a03895fb3820a8fd5b87f52cbd9ae80c5daeb64483dbfd7ea11c62b56"
)

CLAIM_RELATIVE = Path("evals/m4/execution/m4.2/launch-claim.json")
TERMINAL_RELATIVE = Path("evals/m4/execution/m4.2/execution-terminal.json")
OBSERVATIONS_BASE_RELATIVE = Path(
    "evals/m4/execution/m4.2/platform-observations"
)
RESULTS_BASE_RELATIVE = Path("evals/m4/results/m4.2")
RESULTS_MANIFEST_RELATIVE = Path("evals/m4/results-manifest.json")
M5_RELATIVE = Path("evals/m5")
PLAN_RELATIVE = Path(
    "docs/superpowers/plans/2026-08-12-m4.2-one-shot-claim-and-execution.md"
)
TASK_PROTOCOL_RELATIVE = Path("evals/m4/task-protocol.md")
RESULT_SCHEMA_RELATIVE = Path("evals/m4/schemas/task-result.schema.json")

LAUNCH_SCHEMA_RELATIVE = Path("evals/m4/execution/m4.2/launch-claim.schema.json")
DISPATCH_SCHEMA_RELATIVE = Path(
    "evals/m4/execution/m4.2/dispatch-receipt.schema.json"
)
RESPONSE_ATTESTATION_SCHEMA_RELATIVE = Path(
    "evals/m4/execution/m4.2/create-thread-response-attestation.schema.json"
)
TERMINAL_SCHEMA_RELATIVE = Path(
    "evals/m4/execution/m4.2/execution-terminal.schema.json"
)

LAUNCH_SCHEMA_PATH = REPO_ROOT / LAUNCH_SCHEMA_RELATIVE
DISPATCH_SCHEMA_PATH = REPO_ROOT / DISPATCH_SCHEMA_RELATIVE
RESPONSE_ATTESTATION_SCHEMA_PATH = REPO_ROOT / RESPONSE_ATTESTATION_SCHEMA_RELATIVE
TERMINAL_SCHEMA_PATH = REPO_ROOT / TERMINAL_SCHEMA_RELATIVE

BATCH_ORDER = (
    "M4.2-BATCH-NUC",
    "M4.2-BATCH-MEC",
    "M4.2-BATCH-ELE",
    "M4.2-BATCH-AUT",
    "M4.2-BATCH-COM",
    "M4.2-BATCH-MPH",
)

ZERO_COUNTER_NAMES = (
    "acceptance_claims",
    "aggregation_calls",
    "authorized_tasks",
    "created_contexts",
    "dispatched_tasks",
    "finalizations",
    "judge_scores",
    "raw_model_finals",
    "repairs",
    "results_observed",
    "retries",
    "unauthorized_side_effects",
)

CLAIM_LIMITS: dict[str, int] = {
    "attempts_per_task_id": 1,
    "retries": 0,
    "repairs": 0,
    "followups": 0,
    "judge_calls": 0,
    "aggregation_calls": 0,
    "cross_task_result_reads": 0,
    "blind_map_reads": 0,
}

PERMISSIONS_STILL_CLOSED = (
    "second claim",
    "partial-matrix claim",
    "retry",
    "repair",
    "follow-up message",
    "cross-task result read",
    "cross-arm result read",
    "blind-map access",
    "unblinding",
    "judge execution",
    "aggregation",
    "threshold decision",
    "M4 closure",
    "M5",
)

GATE_A_ALLOWED_PATHS = frozenset(
    {
        PLAN_RELATIVE.as_posix(),
        LAUNCH_SCHEMA_RELATIVE.as_posix(),
        DISPATCH_SCHEMA_RELATIVE.as_posix(),
        RESPONSE_ATTESTATION_SCHEMA_RELATIVE.as_posix(),
        TERMINAL_SCHEMA_RELATIVE.as_posix(),
        "evals/m4/execution/audit_m4_2.py",
        "evals/m4/execution/build_m4_2_launch_claim.py",
        "evals/m4/execution/record_m4_2_execution_evidence.py",
        "evals/m4/execution/audit_m4_2_launch_readiness.py",
        "tests/test_m4_2_execution.py",
        "tests/test_m4_2_launch_readiness.py",
        ".github/workflows/m1-validation.yml",
        "STATUS.md",
        "tests/test_m3_r5_erratum.py",
    }
)

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
OID_RE = re.compile(r"^[0-9a-f]{40}$")
TASK_ID_RE = re.compile(r"^M4\.2-[A-Z]{3}-[AB]-(?:F|N|A[123])$")
BLIND_ID_RE = re.compile(r"^M4-J\d{3}$")
ISO_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


class ContractError(ValueError):
    """One stable fail-closed contract error."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


class DuplicateKeyError(ValueError):
    pass


@dataclass(frozen=True)
class LifecyclePaths:
    claim: Path
    observations: Path
    results: Path
    terminal: Path
    results_manifest: Path
    m5: Path


@dataclass(frozen=True)
class FrozenPolicy:
    enforce_raw_hashes: bool = True
    verify_git: bool = True


def default_paths(repo_root: Path) -> LifecyclePaths:
    return LifecyclePaths(
        claim=repo_root / CLAIM_RELATIVE,
        observations=repo_root / OBSERVATIONS_BASE_RELATIVE,
        results=repo_root / RESULTS_BASE_RELATIVE,
        terminal=repo_root / TERMINAL_RELATIVE,
        results_manifest=repo_root / RESULTS_MANIFEST_RELATIVE,
        m5=repo_root / M5_RELATIVE,
    )


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


def json_bytes(value: object) -> bytes:
    return canonical_bytes(value) + b"\n"


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def token_fingerprint(token: str) -> str:
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", token):
        raise ContractError("authorization_token_invalid")
    return token[:19] + "..."


def _reject_constant(_value: str) -> object:
    raise ValueError("non_finite_number")


def _no_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(key)
        result[key] = value
    return result


def parse_json_object(raw: bytes, *, label: str = "json") -> dict[str, Any]:
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ContractError(f"{label}_utf8_bom_forbidden")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise ContractError(f"{label}_utf8_invalid") from error
    try:
        value = json.loads(
            text,
            object_pairs_hook=_no_duplicates,
            parse_constant=_reject_constant,
        )
    except DuplicateKeyError as error:
        raise ContractError(f"{label}_duplicate_key") from error
    except (json.JSONDecodeError, ValueError) as error:
        suffix = "non_finite_number" if "non_finite_number" in str(error) else "json_invalid"
        raise ContractError(f"{label}_{suffix}") from error
    if not isinstance(value, dict):
        raise ContractError(f"{label}_root_not_object")
    return value


def strict_equal(left: object, right: object) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return set(left) == set(right) and all(
            strict_equal(left[key], right[key]) for key in left
        )
    if isinstance(left, list):
        return len(left) == len(right) and all(
            strict_equal(a, b) for a, b in zip(left, right, strict=True)
        )
    return left == right


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _add(errors: list[str], code: str) -> None:
    if code not in errors:
        errors.append(code)


def _git(repo_root: Path, *args: str) -> tuple[int, bytes, bytes]:
    try:
        result = subprocess.run(
            ["git", "--no-replace-objects", *args],
            cwd=repo_root,
            check=False,
            capture_output=True,
        )
    except OSError:
        return 127, b"", b"git_unavailable"
    return result.returncode, result.stdout, result.stderr


def _git_text(repo_root: Path, *args: str) -> str | None:
    code, out, _ = _git(repo_root, *args)
    if code != 0:
        return None
    try:
        return out.decode("utf-8", errors="strict").strip()
    except UnicodeDecodeError:
        return None


def _safe_repo_path(repo_root: Path, relative: str | Path) -> Path:
    text = relative.as_posix() if isinstance(relative, Path) else relative
    if "\\" in text:
        raise ContractError("path_backslash_forbidden")
    pure = PurePosixPath(text)
    if pure.is_absolute() or not pure.parts or any(part in {"", ".", ".."} for part in pure.parts):
        raise ContractError("path_escape")
    candidate = repo_root.joinpath(*pure.parts)
    root_resolved = repo_root.resolve(strict=True)
    parent = candidate.parent
    parent_resolved = parent.resolve(strict=False)
    try:
        parent_resolved.relative_to(root_resolved)
    except ValueError as error:
        raise ContractError("path_escape") from error
    current = root_resolved
    for part in pure.parts[:-1]:
        current = current / part
        if current.is_symlink():
            raise ContractError("path_symlink_forbidden")
    return candidate


def exclusive_create_bytes(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(path, flags, 0o600)
    try:
        with os.fdopen(descriptor, "wb", closefd=True) as stream:
            descriptor = -1
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def exclusive_create_json(path: Path, value: object) -> bytes:
    raw = json_bytes(value)
    exclusive_create_bytes(path, raw)
    return raw


def _type_matches(value: object, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return _is_int(value)
    if expected == "number":
        return (isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value))
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    return False


def validate_schema(value: object, schema: Mapping[str, Any], *, path: str = "$") -> list[str]:
    """Small Draft-2020-12 subset sufficient for the four frozen contracts."""
    errors: list[str] = []
    if "anyOf" in schema:
        branches = schema.get("anyOf")
        if not isinstance(branches, list) or not any(
            not validate_schema(value, branch, path=path)
            for branch in branches
            if isinstance(branch, dict)
        ):
            errors.append(f"{path}:anyOf")
        return errors
    if "const" in schema and not strict_equal(value, schema["const"]):
        errors.append(f"{path}:const")
        return errors
    if "enum" in schema and not any(strict_equal(value, item) for item in schema["enum"]):
        errors.append(f"{path}:enum")
        return errors
    expected_type = schema.get("type")
    if expected_type is not None:
        types = [expected_type] if isinstance(expected_type, str) else expected_type
        if not isinstance(types, list) or not any(
            isinstance(item, str) and _type_matches(value, item) for item in types
        ):
            errors.append(f"{path}:type")
            return errors
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        if isinstance(required, list):
            for key in required:
                if key not in value:
                    errors.append(f"{path}.{key}:required")
        if schema.get("additionalProperties") is False and isinstance(properties, dict):
            for key in value:
                if key not in properties:
                    errors.append(f"{path}.{key}:additional")
        if isinstance(properties, dict):
            for key, child in properties.items():
                if key in value and isinstance(child, dict):
                    errors.extend(validate_schema(value[key], child, path=f"{path}.{key}"))
    elif isinstance(value, list):
        if _is_int(schema.get("minItems")) and len(value) < schema["minItems"]:
            errors.append(f"{path}:minItems")
        if _is_int(schema.get("maxItems")) and len(value) > schema["maxItems"]:
            errors.append(f"{path}:maxItems")
        if schema.get("uniqueItems") is True:
            seen: set[bytes] = set()
            for item in value:
                encoded = canonical_bytes(item)
                if encoded in seen:
                    errors.append(f"{path}:uniqueItems")
                    break
                seen.add(encoded)
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                errors.extend(validate_schema(item, item_schema, path=f"{path}[{index}]"))
    elif isinstance(value, str):
        min_length = schema.get("minLength")
        if _is_int(min_length) and len(value) < min_length:
            errors.append(f"{path}:minLength")
        pattern = schema.get("pattern")
        if isinstance(pattern, str) and re.search(pattern, value) is None:
            errors.append(f"{path}:pattern")
        if schema.get("format") == "uuid":
            try:
                parsed = uuid.UUID(value)
            except (ValueError, AttributeError, TypeError):
                errors.append(f"{path}:uuid")
            else:
                if str(parsed) != value.lower():
                    errors.append(f"{path}:uuid-canonical")
    elif _is_int(value):
        minimum = schema.get("minimum")
        maximum = schema.get("maximum")
        if _is_int(minimum) and value < minimum:
            errors.append(f"{path}:minimum")
        if _is_int(maximum) and value > maximum:
            errors.append(f"{path}:maximum")
    return errors


def recursively_closed_schema(schema: object) -> bool:
    if isinstance(schema, dict):
        if schema.get("type") == "object" and schema.get("additionalProperties") is not False:
            return False
        return all(recursively_closed_schema(value) for value in schema.values())
    if isinstance(schema, list):
        return all(recursively_closed_schema(value) for value in schema)
    return True


def _load_schema(repo_root: Path, relative: Path) -> dict[str, Any]:
    path = _safe_repo_path(repo_root, relative)
    return parse_json_object(path.read_bytes(), label=relative.stem)


def ordered_tasks(control: Mapping[str, Any]) -> list[dict[str, Any]]:
    tasks = control.get("tasks")
    batches = control.get("batches")
    order = control.get("batch_order")
    if not isinstance(tasks, list) or not all(isinstance(item, dict) for item in tasks):
        raise ContractError("control_tasks_invalid")
    if not isinstance(batches, list) or not all(isinstance(item, dict) for item in batches):
        raise ContractError("control_batches_invalid")
    if not isinstance(order, list):
        raise ContractError("control_batch_order_invalid")
    by_task: dict[str, dict[str, Any]] = {}
    for task in tasks:
        task_id = task.get("task_id")
        if not isinstance(task_id, str) or task_id in by_task:
            raise ContractError("control_task_id_invalid_or_duplicate")
        by_task[task_id] = task
    by_batch: dict[str, dict[str, Any]] = {}
    for batch in batches:
        batch_id = batch.get("batch_id")
        if not isinstance(batch_id, str) or batch_id in by_batch:
            raise ContractError("control_batch_id_invalid_or_duplicate")
        by_batch[batch_id] = batch
    flattened: list[dict[str, Any]] = []
    seen: set[str] = set()
    for batch_id in order:
        if not isinstance(batch_id, str) or batch_id not in by_batch:
            raise ContractError("control_batch_order_unknown")
        task_ids = by_batch[batch_id].get("task_ids")
        if not isinstance(task_ids, list):
            raise ContractError("control_batch_task_ids_invalid")
        for task_id in task_ids:
            if not isinstance(task_id, str) or task_id not in by_task:
                raise ContractError("control_batch_task_unknown")
            if task_id in seen:
                raise ContractError("control_task_order_duplicate")
            seen.add(task_id)
            flattened.append(by_task[task_id])
    if set(by_task) != seen:
        raise ContractError("control_task_order_incomplete")
    return flattened


def request_binding_aggregate(tasks: Sequence[Mapping[str, Any]]) -> str:
    pairs = [
        {
            "task_id": task.get("task_id"),
            "request_binding_sha256": task.get("request_binding_sha256"),
        }
        for task in tasks
    ]
    return canonical_sha256(pairs)


def _read_context(repo_root: Path, relative: str | None, label: str) -> str:
    if relative is None:
        return ""
    path = _safe_repo_path(repo_root, relative)
    if not path.is_file():
        raise ContractError(f"{label}_missing")
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ContractError(f"{label}_bom_forbidden")
    try:
        return raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise ContractError(f"{label}_utf8_invalid") from error


def build_initial_prompt(
    repo_root: Path,
    task: Mapping[str, Any],
    task_claim: Mapping[str, Any],
) -> str:
    case_text = _read_context(repo_root, task.get("case_path"), "case")
    protocol_text = _read_context(
        repo_root, task.get("task_protocol_path"), "task_protocol"
    )
    variant_path = task.get("variant_instruction_path")
    if variant_path is not None and not isinstance(variant_path, str):
        raise ContractError("variant_path_invalid")
    variant_text = _read_context(repo_root, variant_path, "variant")
    result_schema_text = _read_context(
        repo_root, RESULT_SCHEMA_RELATIVE.as_posix(), "result_schema"
    )
    parts = [
        "M4.2 FROZEN CROSS-ENGINEERING EVALUATION TASK",
        f"task_id: {task_claim['task_id']}",
        f"blind_id: {task_claim['blind_id']}",
        f"context_id: {task_claim['context_id']}",
        f"finalization_id: {task_claim['finalization_id']}",
        "attempt_index: 1",
        "retry_count: 0",
        "independent_finalization: true",
        "visible_result_task_ids: []",
        "",
        "[FROZEN CASE]",
        case_text.rstrip("\n"),
        "",
        "[COMMON TASK PROTOCOL]",
        protocol_text.rstrip("\n"),
    ]
    if variant_text:
        parts.extend(["", "[SELECTED VARIANT INSTRUCTION]", variant_text.rstrip("\n")])
    parts.extend(
        [
            "",
            "[REQUIRED RESULT SCHEMA]",
            result_schema_text.rstrip("\n"),
            "",
            "Return exactly one UTF-8 JSON object and no surrounding prose or fence.",
            "The JSON object must bind the task, blind, context, and finalization identifiers above.",
            "Do not inspect or mention any other task result.",
        ]
    )
    return "\n".join(parts) + "\n"


def expected_create_thread_arguments(
    repo_root: Path,
    task: Mapping[str, Any],
    task_claim: Mapping[str, Any],
) -> dict[str, Any]:
    prompt = build_initial_prompt(repo_root, task, task_claim)
    return {
        "prompt": prompt,
        "target": {
            "type": "project",
            "projectId": PROJECT_ID,
            "environment": {
                "type": "worktree",
                "startingState": {
                    "type": "branch",
                    "branchName": AUTHORIZATION_BRANCH,
                },
            },
        },
        "title": f"M4.2 {task_claim['blind_id']} {task_claim['task_id']}",
    }


def _validate_zero_counters(value: object, label: str, errors: list[str]) -> None:
    if not isinstance(value, dict):
        _add(errors, f"{label}_invalid")
        return
    if set(value) != set(ZERO_COUNTER_NAMES):
        _add(errors, f"{label}_keys_invalid")
    for name in ZERO_COUNTER_NAMES:
        if not _is_int(value.get(name)) or value.get(name) != 0:
            _add(errors, f"{label}_{name}_nonzero_or_invalid")


def _verify_git_bindings(repo_root: Path, errors: list[str]) -> None:
    if _git_text(repo_root, "rev-parse", f"{AUTHORIZATION_CLOSURE_HEAD}^{{tree}}") != AUTHORIZATION_CLOSURE_TREE:
        _add(errors, "authorization_closure_tree_mismatch")
    code, _, _ = _git(
        repo_root,
        "merge-base",
        "--is-ancestor",
        AUTHORIZATION_CLOSURE_HEAD,
        "HEAD",
    )
    if code != 0:
        _add(errors, "authorization_closure_not_ancestor")
    expected = (
        (AUTHORIZATION_RELATIVE, AUTHORIZATION_BLOB),
        (CONTROL_RELATIVE, CONTROL_BLOB),
    )
    for relative, blob in expected:
        observed = _git_text(repo_root, "rev-parse", f"HEAD:{relative.as_posix()}")
        if observed != blob:
            _add(errors, f"{relative.name}_git_blob_mismatch")


def load_frozen_inputs(
    repo_root: Path,
    *,
    policy: FrozenPolicy = FrozenPolicy(),
    authorization_path: Path | None = None,
    control_path: Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any], bytes, bytes, list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    authorization_path = authorization_path or repo_root / AUTHORIZATION_RELATIVE
    control_path = control_path or repo_root / CONTROL_RELATIVE
    try:
        authorization_raw = authorization_path.read_bytes()
    except OSError:
        return {}, {}, b"", b"", [], ["authorization_missing"]
    try:
        control_raw = control_path.read_bytes()
    except OSError:
        return {}, {}, authorization_raw, b"", [], ["control_missing"]
    if policy.enforce_raw_hashes:
        if sha256(authorization_raw) != AUTHORIZATION_RAW_SHA256:
            _add(errors, "authorization_raw_sha256_mismatch")
        if sha256(control_raw) != CONTROL_RAW_SHA256:
            _add(errors, "control_raw_sha256_mismatch")
    try:
        authorization = parse_json_object(authorization_raw, label="authorization")
    except ContractError as error:
        _add(errors, error.code)
        authorization = {}
    try:
        control = parse_json_object(control_raw, label="control")
    except ContractError as error:
        _add(errors, error.code)
        control = {}
    if policy.verify_git:
        _verify_git_bindings(repo_root, errors)

    if authorization.get("schema_version") != "m4.2-execution-authorization-v1":
        _add(errors, "authorization_schema_version_invalid")
    if authorization.get("revision") != REVISION:
        _add(errors, "authorization_revision_invalid")
    if authorization.get("status") != "AUTHORIZED_UNCONSUMED":
        _add(errors, "authorization_status_invalid")
    token = authorization.get("authorization_token")
    if not isinstance(token, str) or re.fullmatch(r"sha256:[0-9a-f]{64}", token) is None:
        _add(errors, "authorization_token_invalid")
    if control.get("schema_version") != "m4.2-execution-control-v1":
        _add(errors, "control_schema_version_invalid")
    if control.get("revision") != REVISION:
        _add(errors, "control_revision_invalid")
    if control.get("status") != "READY_UNCONSUMED":
        _add(errors, "control_status_invalid")
    control_authorization = control.get("authorization")
    if not isinstance(control_authorization, dict):
        _add(errors, "control_authorization_invalid")
    else:
        if control_authorization.get("authorization_token") != token:
            _add(errors, "control_authorization_token_mismatch")
        if policy.enforce_raw_hashes and control_authorization.get("raw_sha256") != AUTHORIZATION_RAW_SHA256:
            _add(errors, "control_authorization_raw_sha256_mismatch")
        if control_authorization.get("path") != AUTHORIZATION_RELATIVE.as_posix():
            _add(errors, "control_authorization_path_mismatch")
    if control.get("batch_order") != list(BATCH_ORDER):
        _add(errors, "control_batch_order_invalid")
    batches = control.get("batches")
    if not isinstance(batches, list) or len(batches) != 6:
        _add(errors, "control_batch_count_invalid")
    else:
        by_id = {item.get("batch_id"): item for item in batches if isinstance(item, dict)}
        if set(by_id) != set(BATCH_ORDER):
            _add(errors, "control_batch_ids_invalid")
        for batch_id in BATCH_ORDER:
            item = by_id.get(batch_id)
            if not isinstance(item, dict):
                continue
            if item.get("planned_task_count") != 10:
                _add(errors, "control_batch_task_count_invalid")
            task_ids = item.get("task_ids")
            if not isinstance(task_ids, list) or len(task_ids) != 10 or len(set(task_ids)) != 10:
                _add(errors, "control_batch_task_ids_invalid")
            if item.get("stop_on_infrastructure_or_protocol_failure") is not True:
                _add(errors, "control_batch_stop_policy_invalid")
            if item.get("later_batches_mutable_after_observation") is not False:
                _add(errors, "control_later_batch_mutability_invalid")
    try:
        tasks = ordered_tasks(control)
    except ContractError as error:
        _add(errors, error.code)
        tasks = []
    if len(tasks) != 60:
        _add(errors, "control_task_count_invalid")
    for task in tasks:
        task_id = task.get("task_id")
        if not isinstance(task_id, str) or TASK_ID_RE.fullmatch(task_id) is None:
            _add(errors, "control_task_id_shape_invalid")
            continue
        if task.get("batch_id") not in BATCH_ORDER:
            _add(errors, "control_task_batch_invalid")
        blind_id = task.get("blind_id")
        if not isinstance(blind_id, str) or BLIND_ID_RE.fullmatch(blind_id) is None:
            _add(errors, "control_blind_id_invalid")
        binding = task.get("request_binding_sha256")
        if not isinstance(binding, str) or SHA256_RE.fullmatch(binding) is None:
            _add(errors, "control_request_binding_invalid")
        expected_root = f"evals/m4/results/m4.2/{task_id}"
        if task.get("result_root") != expected_root:
            _add(errors, "control_result_root_invalid")
        if task.get("result_root_must_be_absent") is not True:
            _add(errors, "control_result_absence_policy_invalid")
        if task.get("attempt_limit") != 1:
            _add(errors, "control_attempt_limit_invalid")
        if task.get("cross_task_result_visibility") is not False:
            _add(errors, "control_cross_task_visibility_invalid")
        if task.get("independent_finalization_required") is not True:
            _add(errors, "control_finalization_policy_invalid")
        for key in ("case_path", "task_protocol_path"):
            if not isinstance(task.get(key), str):
                _add(errors, f"control_{key}_invalid")
    if len({task.get("blind_id") for task in tasks}) != len(tasks):
        _add(errors, "control_blind_id_duplicate")
    _validate_zero_counters(authorization.get("prelaunch_counters"), "authorization_prelaunch", errors)
    _validate_zero_counters(control.get("prelaunch_counters"), "control_prelaunch", errors)
    authority = authorization.get("authority")
    if not isinstance(authority, dict):
        _add(errors, "authorization_authority_invalid")
    else:
        expected_bool = {
            "fresh_execution_authorized": True,
            "whole_matrix_required": True,
            "partial_authority_allowed": False,
            "retry_authorized": False,
            "repair_authorized": False,
            "followup_message_authorized": False,
            "judge_execution_authorized": False,
            "aggregation_authorized": False,
            "blind_mapping_access_authorized": False,
            "cross_task_result_visibility": False,
            "closure_authorized": False,
            "threshold_claim_authorized": False,
        }
        for key, expected_value in expected_bool.items():
            if authority.get(key) is not expected_value:
                _add(errors, f"authorization_authority_{key}_invalid")
        if authority.get("authorized_task_count") != 60:
            _add(errors, "authorization_task_count_invalid")
        if authority.get("authorized_batch_count") != 6:
            _add(errors, "authorization_batch_count_invalid")
        if set(authority.get("authorized_task_ids", [])) != {task.get("task_id") for task in tasks}:
            _add(errors, "authorization_task_roster_invalid")
        if authority.get("authorized_batch_ids") != list(BATCH_ORDER):
            _add(errors, "authorization_batch_roster_invalid")
    model = authorization.get("model_binding")
    if not isinstance(model, dict) or model.get("exact_model_id") != MODEL_ID or model.get("reasoning_effort") != REASONING_EFFORT:
        _add(errors, "authorization_model_binding_invalid")
    surface = authorization.get("execution_surface")
    if not isinstance(surface, dict):
        _add(errors, "authorization_execution_surface_invalid")
    else:
        expected_surface = {
            "project_id": PROJECT_ID,
            "environment": "worktree",
            "starting_branch": AUTHORIZATION_BRANCH,
            "tool": "codex_app.create_thread",
            "cross_task_result_visibility": False,
        }
        for key, expected_value in expected_surface.items():
            if surface.get(key) != expected_value:
                _add(errors, f"authorization_execution_surface_{key}_invalid")
    request_policy = control.get("request_policy")
    if not isinstance(request_policy, dict):
        _add(errors, "control_request_policy_invalid")
    else:
        expected_policy = {
            "project_id": PROJECT_ID,
            "environment_type": "worktree",
            "starting_branch": AUTHORIZATION_BRANCH,
            "surface": "codex_app.create_thread",
            "target_type": "project",
            "cross_task_result_visibility": False,
            "one_new_thread_per_task_id": True,
            "one_independent_finalization_per_task_id": True,
        }
        for key, expected_value in expected_policy.items():
            if request_policy.get(key) != expected_value:
                _add(errors, f"control_request_policy_{key}_invalid")
    permissions = control.get("permissions")
    if not isinstance(permissions, dict):
        _add(errors, "control_permissions_invalid")
    else:
        expected_permissions = {
            "fresh_task_creation": True,
            "result_writes_below_frozen_roots": True,
            "retry": False,
            "repair": False,
            "followup_message": False,
            "judge_execution": False,
            "aggregation": False,
            "blind_mapping_access": False,
            "cross_task_result_read": False,
            "threshold_claim": False,
            "m4_closure": False,
        }
        for key, expected_value in expected_permissions.items():
            if permissions.get(key) is not expected_value:
                _add(errors, f"control_permission_{key}_invalid")
    return authorization, control, authorization_raw, control_raw, tasks, errors


def deterministic_uuid_namespace(
    authorization_raw_sha256: str,
    control_raw_sha256: str,
    gate_a_head: str,
) -> uuid.UUID:
    seed = f"M4.2|{authorization_raw_sha256}|{control_raw_sha256}|{gate_a_head}"
    return uuid.uuid5(uuid.NAMESPACE_URL, seed)


def deterministic_claim_id(
    authorization_raw_sha256: str,
    control_raw_sha256: str,
    gate_a_head: str,
) -> str:
    namespace = deterministic_uuid_namespace(
        authorization_raw_sha256, control_raw_sha256, gate_a_head
    )
    return str(uuid.uuid5(namespace, "whole-matrix-claim"))


def deterministic_task_uuid(
    kind: str,
    task_id: str,
    authorization_raw_sha256: str,
    control_raw_sha256: str,
    gate_a_head: str,
) -> str:
    if kind not in {"context", "finalization"}:
        raise ValueError("kind")
    namespace = deterministic_uuid_namespace(
        authorization_raw_sha256, control_raw_sha256, gate_a_head
    )
    return str(uuid.uuid5(namespace, f"{kind}|{task_id}"))


def _claim_task_expectations(
    tasks: Sequence[Mapping[str, Any]],
    authorization_raw_sha256: str,
    control_raw_sha256: str,
    gate_a_head: str,
) -> list[dict[str, Any]]:
    expected: list[dict[str, Any]] = []
    for index, task in enumerate(tasks):
        task_id = str(task["task_id"])
        expected.append(
            {
                "task_id": task_id,
                "batch_id": task["batch_id"],
                "batch_sequence": index // 10 + 1,
                "task_sequence_in_batch": index % 10 + 1,
                "dispatch_sequence": index + 1,
                "blind_id": task["blind_id"],
                "request_binding_sha256": task["request_binding_sha256"],
                "result_root": task["result_root"],
                "context_id": deterministic_task_uuid(
                    "context",
                    task_id,
                    authorization_raw_sha256,
                    control_raw_sha256,
                    gate_a_head,
                ),
                "finalization_id": deterministic_task_uuid(
                    "finalization",
                    task_id,
                    authorization_raw_sha256,
                    control_raw_sha256,
                    gate_a_head,
                ),
            }
        )
    return expected


def _validate_claim(
    repo_root: Path,
    claim: Mapping[str, Any],
    authorization: Mapping[str, Any],
    control: Mapping[str, Any],
    authorization_raw: bytes,
    control_raw: bytes,
    tasks: Sequence[Mapping[str, Any]],
    errors: list[str],
) -> None:
    try:
        schema = _load_schema(repo_root, LAUNCH_SCHEMA_RELATIVE)
    except (OSError, ContractError) as error:
        _add(errors, "launch_claim_schema_unavailable")
    else:
        if not recursively_closed_schema(schema):
            _add(errors, "launch_claim_schema_not_recursively_closed")
        if validate_schema(claim, schema):
            _add(errors, "launch_claim_schema_invalid")
    if claim.get("schema_version") != "m4.2-launch-claim-v1":
        _add(errors, "claim_schema_version_invalid")
    if claim.get("claim_count") != 1:
        _add(errors, "claim_count_invalid")
    gate_a = claim.get("gate_a_acceptance")
    if not isinstance(gate_a, dict):
        _add(errors, "claim_gate_a_acceptance_invalid")
        gate_a = {}
    gate_a_head = gate_a.get("candidate_head")
    if not isinstance(gate_a_head, str) or OID_RE.fullmatch(gate_a_head) is None:
        _add(errors, "claim_gate_a_head_invalid")
        gate_a_head = "0" * 40
    expected_claim_id = deterministic_claim_id(
        sha256(authorization_raw), sha256(control_raw), gate_a_head
    )
    if claim.get("claim_id") != expected_claim_id:
        _add(errors, "claim_id_invalid")
    authorization_claim = claim.get("authorization")
    if not isinstance(authorization_claim, dict):
        _add(errors, "claim_authorization_invalid")
    else:
        expected_values = {
            "closure_head": AUTHORIZATION_CLOSURE_HEAD,
            "closure_tree": AUTHORIZATION_CLOSURE_TREE,
            "branch": AUTHORIZATION_BRANCH,
            "token_status_before_claim": "UNCONSUMED",
            "token_status_after_claim": "CONSUMED",
            "claim_consumes_entire_authorization": True,
        }
        for key, expected_value in expected_values.items():
            if authorization_claim.get(key) != expected_value:
                _add(errors, f"claim_authorization_{key}_invalid")
        token = authorization.get("authorization_token")
        if isinstance(token, str):
            try:
                expected_fingerprint = token_fingerprint(token)
            except ContractError:
                expected_fingerprint = None
            if authorization_claim.get("token_fingerprint") != expected_fingerprint:
                _add(errors, "claim_token_fingerprint_invalid")
        for key, relative, expected_blob, raw in (
            (
                "execution_authorization",
                AUTHORIZATION_RELATIVE,
                AUTHORIZATION_BLOB,
                authorization_raw,
            ),
            ("execution_control", CONTROL_RELATIVE, CONTROL_BLOB, control_raw),
        ):
            reference = authorization_claim.get(key)
            if not isinstance(reference, dict):
                _add(errors, f"claim_{key}_invalid")
                continue
            if reference.get("path") != relative.as_posix():
                _add(errors, f"claim_{key}_path_invalid")
            if reference.get("raw_sha256") != sha256(raw):
                _add(errors, f"claim_{key}_raw_sha256_invalid")
            if reference.get("git_blob_oid") != expected_blob:
                # Synthetic fixtures may deliberately use all-zero placeholders only
                # when the frozen raw hashes are not enforced.
                if reference.get("git_blob_oid") != "0" * 40:
                    _add(errors, f"claim_{key}_blob_invalid")
    project = claim.get("project")
    if not isinstance(project, dict) or project.get("starting_head") != AUTHORIZATION_CLOSURE_HEAD:
        _add(errors, "claim_project_starting_head_invalid")
    defaults = claim.get("configured_defaults")
    if not isinstance(defaults, dict):
        _add(errors, "claim_configured_defaults_invalid")
    else:
        expected_defaults = {
            "exact_model_id": MODEL_ID,
            "reasoning_effort": REASONING_EFFORT,
            "configured_default_check": "MATCHED",
            "create_thread_model_field": "OMITTED",
            "create_thread_thinking_field": "OMITTED",
        }
        for key, expected_value in expected_defaults.items():
            if defaults.get(key) != expected_value:
                _add(errors, f"claim_configured_defaults_{key}_invalid")
    if claim.get("batch_order") != list(BATCH_ORDER):
        _add(errors, "claim_batch_order_invalid")
    expected_task_ids = [str(task["task_id"]) for task in tasks]
    if claim.get("task_ids") != expected_task_ids:
        _add(errors, "claim_task_order_invalid")
    expected_task_claims = _claim_task_expectations(
        tasks, sha256(authorization_raw), sha256(control_raw), gate_a_head
    )
    if not strict_equal(claim.get("task_claims"), expected_task_claims):
        _add(errors, "claim_task_claims_invalid")
    task_claims = claim.get("task_claims")
    if isinstance(task_claims, list):
        context_ids = [item.get("context_id") for item in task_claims if isinstance(item, dict)]
        finalization_ids = [item.get("finalization_id") for item in task_claims if isinstance(item, dict)]
        if len(context_ids) != 60 or len(set(context_ids)) != 60:
            _add(errors, "claim_context_id_duplicate_or_missing")
        if len(finalization_ids) != 60 or len(set(finalization_ids)) != 60:
            _add(errors, "claim_finalization_id_duplicate_or_missing")
    if not strict_equal(claim.get("limits"), CLAIM_LIMITS):
        _add(errors, "claim_limits_invalid")
    if claim.get("permissions_still_closed") != list(PERMISSIONS_STILL_CLOSED):
        _add(errors, "claim_permissions_invalid")
    aggregate = claim.get("request_binding_aggregate")
    if not isinstance(aggregate, dict) or aggregate.get("sha256") != request_binding_aggregate(tasks):
        _add(errors, "claim_request_binding_aggregate_invalid")
    batches = claim.get("batches")
    expected_batches = []
    control_batches = {
        item["batch_id"]: item
        for item in control.get("batches", [])
        if isinstance(item, dict) and isinstance(item.get("batch_id"), str)
    }
    for sequence, batch_id in enumerate(BATCH_ORDER, start=1):
        source = control_batches.get(batch_id, {})
        expected_batches.append(
            {
                "batch_id": batch_id,
                "sequence": sequence,
                "planned_task_count": 10,
                "task_ids": source.get("task_ids"),
            }
        )
    if not strict_equal(batches, expected_batches):
        _add(errors, "claim_batches_invalid")


def _validate_task_result(
    raw: bytes,
    task: Mapping[str, Any],
    task_claim: Mapping[str, Any],
) -> list[str]:
    errors: list[str] = []
    try:
        value = parse_json_object(raw, label="raw_final")
    except ContractError as error:
        return [error.code]
    expected_keys = {
        "schema_version",
        "task_id",
        "blind_id",
        "context_id",
        "finalization_id",
        "attempt_index",
        "retry_count",
        "independent_finalization",
        "visible_result_task_ids",
        "response",
        "citations",
        "machine_metrics",
        "detected_mismatch_ids",
        "side_effects",
        "terminal_state",
    }
    if set(value) != expected_keys:
        _add(errors, "raw_final_keys_invalid")
    expected = {
        "schema_version": "m4-task-result-v1",
        "task_id": task_claim.get("task_id"),
        "blind_id": task.get("blind_id"),
        "context_id": task_claim.get("context_id"),
        "finalization_id": task_claim.get("finalization_id"),
        "attempt_index": 1,
        "retry_count": 0,
        "independent_finalization": True,
        "visible_result_task_ids": [],
        "side_effects": [],
        "terminal_state": "finalized",
    }
    for key, expected_value in expected.items():
        if not strict_equal(value.get(key), expected_value):
            _add(errors, f"raw_final_{key}_invalid")
    if not isinstance(value.get("response"), str):
        _add(errors, "raw_final_response_invalid")
    if not isinstance(value.get("citations"), list):
        _add(errors, "raw_final_citations_invalid")
    if not isinstance(value.get("detected_mismatch_ids"), list):
        _add(errors, "raw_final_mismatch_ids_invalid")
    metrics = value.get("machine_metrics")
    if not isinstance(metrics, dict):
        _add(errors, "raw_final_machine_metrics_invalid")
    else:
        if metrics.get("unauthorized_side_effect_count") != 0:
            _add(errors, "raw_final_unauthorized_side_effect")
    return errors


def _scan_tree(base: Path) -> list[str]:
    if not base.exists():
        return []
    if not base.is_dir() or base.is_symlink():
        return ["<invalid-root>"]
    return sorted(path.relative_to(base).as_posix() for path in base.rglob("*"))


def _load_json_file(path: Path, label: str, errors: list[str]) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
    except OSError:
        _add(errors, f"{label}_missing")
        return {}, b""
    try:
        return parse_json_object(raw, label=label), raw
    except ContractError as error:
        _add(errors, error.code)
        return {}, raw


def _validate_evidence(
    repo_root: Path,
    paths: LifecyclePaths,
    claim: Mapping[str, Any],
    claim_raw: bytes,
    tasks: Sequence[Mapping[str, Any]],
    errors: list[str],
    *,
    allow_terminal_failure_prefix: bool,
) -> dict[str, Any]:
    task_claims = claim.get("task_claims")
    if not isinstance(task_claims, list) or len(task_claims) != 60:
        return {
            "receipt_count": 0,
            "response_count": 0,
            "ready_response_count": 0,
            "final_count": 0,
            "threads": [],
            "receipts": [],
            "responses": [],
            "finals": [],
            "protocol_errors": {},
        }
    allowed_ids = [str(task["task_id"]) for task in tasks]
    allowed_set = set(allowed_ids)
    result_entries = _scan_tree(paths.results)
    observation_entries = _scan_tree(paths.observations)
    for entry in result_entries:
        if entry == "<invalid-root>":
            _add(errors, "results_root_invalid")
            continue
        parts = PurePosixPath(entry).parts
        if len(parts) == 1 and parts[0] in allowed_set:
            continue
        if len(parts) == 2 and parts[0] in allowed_set and parts[1] in {
            "dispatch-receipt.json",
            "raw-final.txt",
        }:
            continue
        _add(errors, "unexpected_execution_artifact")
    for entry in observation_entries:
        if entry == "<invalid-root>":
            _add(errors, "observations_root_invalid")
            continue
        parts = PurePosixPath(entry).parts
        if len(parts) == 1 and parts[0] in allowed_set:
            continue
        if len(parts) == 2 and parts[0] in allowed_set and parts[1] in {
            "create-thread-response.json",
            "create-thread-response-attestation.json",
        }:
            continue
        _add(errors, "unexpected_execution_artifact")
    receipts: list[dict[str, Any]] = []
    responses: list[dict[str, Any]] = []
    finals: list[dict[str, Any]] = []
    thread_ids: list[str] = []
    ready_response_count = 0
    protocol_errors: dict[str, list[str]] = {}
    receipt_gap = False
    response_gap = False
    final_gap = False
    for index, task_id in enumerate(allowed_ids):
        task = tasks[index]
        task_claim = task_claims[index]
        receipt_path = paths.results / task_id / "dispatch-receipt.json"
        final_path = paths.results / task_id / "raw-final.txt"
        response_path = paths.observations / task_id / "create-thread-response.json"
        attestation_path = (
            paths.observations / task_id / "create-thread-response-attestation.json"
        )
        receipt_exists = receipt_path.is_file()
        response_exists = response_path.is_file()
        attestation_exists = attestation_path.is_file()
        final_exists = final_path.is_file()
        if receipt_exists and receipt_gap:
            _add(errors, "dispatch_receipt_not_prefix")
        if response_exists and response_gap:
            _add(errors, "create_thread_response_not_prefix")
        if final_exists and final_gap:
            _add(errors, "raw_final_not_prefix")
        if not receipt_exists:
            receipt_gap = True
        if not response_exists:
            response_gap = True
        if not final_exists:
            final_gap = True
        if receipt_exists:
            receipt, receipt_raw = _load_json_file(
                receipt_path, f"dispatch_receipt_{task_id}", errors
            )
            try:
                dispatch_schema = _load_schema(repo_root, DISPATCH_SCHEMA_RELATIVE)
            except (OSError, ContractError):
                _add(errors, "dispatch_schema_unavailable")
            else:
                if validate_schema(receipt, dispatch_schema):
                    _add(errors, "dispatch_receipt_schema_invalid")
            expected_core = {
                "task_id": task_id,
                "batch_id": task_claim.get("batch_id"),
                "batch_sequence": index // 10 + 1,
                "task_sequence_in_batch": index % 10 + 1,
                "dispatch_sequence": index + 1,
                "request_binding_sha256": task_claim.get("request_binding_sha256"),
                "blind_id": task_claim.get("blind_id"),
                "context_id": task_claim.get("context_id"),
                "finalization_id": task_claim.get("finalization_id"),
                "attempt_index": 1,
                "retry_count": 0,
                "repair_count": 0,
                "errors": [],
            }
            for key, expected_value in expected_core.items():
                if not strict_equal(receipt.get(key), expected_value):
                    _add(errors, f"dispatch_receipt_{key}_invalid")
            claim_ref = receipt.get("claim")
            if not isinstance(claim_ref, dict) or claim_ref.get("claim_id") != claim.get("claim_id") or claim_ref.get("raw_sha256") != sha256(claim_raw):
                _add(errors, "dispatch_receipt_claim_binding_invalid")
            request = receipt.get("request")
            expected_request = expected_create_thread_arguments(repo_root, task, task_claim)
            if not isinstance(request, dict):
                _add(errors, "dispatch_receipt_request_invalid")
            else:
                if request.get("initial_request_sha256") != sha256(expected_request["prompt"].encode("utf-8")):
                    _add(errors, "dispatch_receipt_prompt_hash_invalid")
                if request.get("request_envelope_sha256") != canonical_sha256(expected_request):
                    _add(errors, "dispatch_receipt_envelope_hash_invalid")
                if request.get("model_field") != "OMITTED" or request.get("thinking_field") != "OMITTED":
                    _add(errors, "dispatch_receipt_model_override_invalid")
            response = receipt.get("response")
            if not isinstance(response, dict):
                _add(errors, "dispatch_receipt_response_invalid")
            else:
                thread_id = response.get("thread_id")
                if not isinstance(thread_id, str) or not thread_id:
                    _add(errors, "dispatch_receipt_thread_id_invalid")
                else:
                    thread_ids.append(thread_id)
            receipts.append(
                {
                    "task_id": task_id,
                    "thread_id": response.get("thread_id") if isinstance(response, dict) else None,
                    "path": f"evals/m4/results/m4.2/{task_id}/dispatch-receipt.json",
                    "raw_sha256": sha256(receipt_raw),
                }
            )
        if response_exists:
            response_raw = response_path.read_bytes()
            if not attestation_exists:
                _add(errors, "create_thread_attestation_missing")
            else:
                attestation, attestation_raw = _load_json_file(
                    attestation_path, f"response_attestation_{task_id}", errors
                )
                try:
                    attestation_schema = _load_schema(
                        repo_root, RESPONSE_ATTESTATION_SCHEMA_RELATIVE
                    )
                except (OSError, ContractError):
                    _add(errors, "response_attestation_schema_unavailable")
                else:
                    if validate_schema(attestation, attestation_schema):
                        _add(errors, "response_attestation_schema_invalid")
                if attestation.get("task_id") != task_id:
                    _add(errors, "response_attestation_task_invalid")
                if attestation.get("raw_response_sha256") != sha256(response_raw):
                    _add(errors, "response_attestation_raw_hash_invalid")
                response_parse_error: str | None = None
                try:
                    response_value = parse_json_object(
                        response_raw, label=f"create_thread_response_{task_id}"
                    )
                except ContractError as error:
                    response_parse_error = error.code
                    response_value = None
                if response_value is not None and attestation.get("canonical_response_sha256") != canonical_sha256(response_value):
                    _add(errors, "response_attestation_canonical_hash_invalid")
                attestation_status = attestation.get("status")
                attestation_errors = attestation.get("errors")
                if attestation_status == "VALID":
                    if response_parse_error is not None:
                        _add(errors, "response_attestation_valid_but_raw_invalid")
                    if attestation.get("ready_identifiers_validated") is not True:
                        _add(errors, "response_attestation_ready_invalid")
                    else:
                        ready_response_count += 1
                elif attestation_status == "INVALID":
                    if not allow_terminal_failure_prefix:
                        _add(errors, "invalid_response_without_terminal")
                    if not isinstance(attestation_errors, list) or not attestation_errors:
                        _add(errors, "invalid_response_attestation_errors_missing")
                else:
                    _add(errors, "response_attestation_status_invalid")
                responses.append(
                    {
                        "task_id": task_id,
                        "path": f"evals/m4/execution/m4.2/platform-observations/{task_id}/create-thread-response.json",
                        "attestation_path": f"evals/m4/execution/m4.2/platform-observations/{task_id}/create-thread-response-attestation.json",
                        "raw_sha256": sha256(response_raw),
                    }
                )
        elif attestation_exists:
            _add(errors, "response_attestation_without_raw")
        if receipt_exists != (response_exists and attestation_exists):
            if not allow_terminal_failure_prefix:
                _add(errors, "dispatch_response_pair_incomplete")
        if final_exists:
            if not receipt_exists:
                _add(errors, "raw_final_without_dispatch")
            final_raw = final_path.read_bytes()
            final_errors = _validate_task_result(final_raw, task, task_claim)
            protocol_errors[task_id] = final_errors
            finals.append(
                {
                    "task_id": task_id,
                    "finalization_id": task_claim.get("finalization_id"),
                    "path": f"evals/m4/results/m4.2/{task_id}/raw-final.txt",
                    "byte_length": len(final_raw),
                    "raw_sha256": sha256(final_raw),
                    "protocol_validation": "VALID" if not final_errors else "INVALID",
                    "protocol_errors": final_errors,
                    "observed_at_utc": "2000-01-01T00:00:00Z",
                }
            )
    if len(thread_ids) != len(set(thread_ids)):
        _add(errors, "thread_id_duplicate")
    receipt_count = len(receipts)
    response_count = len(responses)
    final_count = len(finals)
    if receipt_count != ready_response_count:
        _add(errors, "receipt_ready_response_count_mismatch")
    if response_count not in {receipt_count, receipt_count + (1 if allow_terminal_failure_prefix else 0)}:
        _add(errors, "raw_response_count_invalid")
    if final_count > receipt_count:
        _add(errors, "final_count_exceeds_receipts")
    if receipt_count - final_count > 1:
        _add(errors, "multiple_dispatched_without_finalization")
    return {
        "receipt_count": receipt_count,
        "response_count": response_count,
        "ready_response_count": ready_response_count,
        "final_count": final_count,
        "threads": thread_ids,
        "receipts": receipts,
        "responses": responses,
        "finals": finals,
        "protocol_errors": protocol_errors,
    }


def _validate_terminal(
    repo_root: Path,
    terminal: Mapping[str, Any],
    terminal_raw: bytes,
    claim: Mapping[str, Any],
    claim_raw: bytes,
    tasks: Sequence[Mapping[str, Any]],
    evidence: Mapping[str, Any],
    errors: list[str],
) -> str:
    try:
        schema = _load_schema(repo_root, TERMINAL_SCHEMA_RELATIVE)
    except (OSError, ContractError):
        _add(errors, "terminal_schema_unavailable")
    else:
        if validate_schema(terminal, schema):
            _add(errors, "terminal_schema_invalid")
    claim_ref = terminal.get("launch_claim")
    if not isinstance(claim_ref, dict) or claim_ref.get("claim_id") != claim.get("claim_id") or claim_ref.get("raw_sha256") != sha256(claim_raw):
        _add(errors, "terminal_claim_binding_invalid")
    if terminal.get("batch_order") != list(BATCH_ORDER):
        _add(errors, "terminal_batch_order_invalid")
    counts = terminal.get("counts")
    if not isinstance(counts, dict):
        _add(errors, "terminal_counts_invalid")
        counts = {}
    expected_counts = {
        "tasks": evidence["receipt_count"],
        "threads": evidence["ready_response_count"],
        "finalizations": evidence["final_count"],
        "results": evidence["final_count"],
        "retries": 0,
        "repairs": 0,
        "followups": 0,
        "judge_calls": 0,
        "aggregation_calls": 0,
        "side_effects": 0,
    }
    for key, expected_value in expected_counts.items():
        if counts.get(key) != expected_value:
            _add(errors, f"terminal_count_{key}_invalid")
    attempted = terminal.get("attempted_task_ids")
    if not isinstance(attempted, list):
        _add(errors, "terminal_attempted_tasks_invalid")
        attempted = []
    expected_order = [str(task["task_id"]) for task in tasks]
    if attempted != expected_order[: len(attempted)]:
        _add(errors, "terminal_attempted_tasks_not_prefix")
    if terminal.get("dispatch_receipts") != evidence["receipts"]:
        _add(errors, "terminal_dispatch_receipts_invalid")
    if terminal.get("create_thread_responses") != evidence["responses"]:
        _add(errors, "terminal_create_thread_responses_invalid")
    terminal_finals = terminal.get("raw_finals")
    if not isinstance(terminal_finals, list) or len(terminal_finals) != len(evidence["finals"]):
        _add(errors, "terminal_raw_finals_invalid")
    else:
        for recorded, observed in zip(terminal_finals, evidence["finals"], strict=True):
            if not isinstance(recorded, dict):
                _add(errors, "terminal_raw_final_ref_invalid")
                continue
            for key in (
                "task_id",
                "finalization_id",
                "path",
                "byte_length",
                "raw_sha256",
                "protocol_validation",
                "protocol_errors",
            ):
                if not strict_equal(recorded.get(key), observed.get(key)):
                    _add(errors, f"terminal_raw_final_{key}_invalid")
    state = terminal.get("terminal_state")
    if state == "COMPLETE_UNJUDGED":
        if evidence["receipt_count"] != 60 or evidence["response_count"] != 60 or evidence["ready_response_count"] != 60 or evidence["final_count"] != 60:
            _add(errors, "complete_terminal_incomplete_matrix")
        if any(evidence["protocol_errors"].values()):
            _add(errors, "complete_terminal_protocol_error_present")
        if attempted != expected_order:
            _add(errors, "complete_terminal_attempted_tasks_invalid")
        if counts.get("attempts") != 60:
            _add(errors, "complete_terminal_attempt_count_invalid")
        if terminal.get("failed_task_id") is not None or terminal.get("failed_stage") is not None or terminal.get("failure_evidence") is not None:
            _add(errors, "complete_terminal_failure_fields_present")
        if terminal.get("successor_revision_required") is not False:
            _add(errors, "complete_terminal_successor_flag_invalid")
        if terminal.get("later_batches_not_started") != []:
            _add(errors, "complete_terminal_later_batches_invalid")
    elif state == "STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE":
        if terminal.get("successor_revision_required") is not True:
            _add(errors, "stopped_terminal_successor_flag_invalid")
        failure = terminal.get("failure_evidence")
        if not isinstance(failure, dict):
            _add(errors, "stopped_terminal_failure_evidence_missing")
        if not isinstance(terminal.get("failed_stage"), str):
            _add(errors, "stopped_terminal_failed_stage_missing")
        failed_task = terminal.get("failed_task_id")
        if failed_task is not None and failed_task not in expected_order:
            _add(errors, "stopped_terminal_failed_task_invalid")
        attempts = counts.get("attempts")
        if not _is_int(attempts) or attempts not in {evidence["receipt_count"], evidence["receipt_count"] + 1}:
            _add(errors, "stopped_terminal_attempt_count_invalid")
        invalid_finals = [item for item in evidence["finals"] if item["protocol_validation"] == "INVALID"]
        failure_class = failure.get("failure_class") if isinstance(failure, dict) else None
        if invalid_finals and failure_class != "PROTOCOL_FAILURE":
            _add(errors, "stopped_terminal_failure_class_invalid")
        if evidence["final_count"] == 60 and not invalid_finals:
            _add(errors, "stopped_terminal_after_complete_matrix")
    else:
        _add(errors, "terminal_state_invalid")
        return "INVALID"
    if terminal.get("permissions_still_closed") != list(PERMISSIONS_STILL_CLOSED):
        _add(errors, "terminal_permissions_invalid")
    return str(state)


def audit_execution(
    repo_root: Path = REPO_ROOT,
    *,
    claim_path: Path | None = None,
    observations_base: Path | None = None,
    results_base: Path | None = None,
    terminal_path: Path | None = None,
    results_manifest_path: Path | None = None,
    m5_path: Path | None = None,
    verify_git: bool = True,
    enforce_frozen_hashes: bool = True,
    authorization_path: Path | None = None,
    control_path: Path | None = None,
) -> dict[str, Any]:
    repo_root = repo_root.resolve(strict=True)
    defaults = default_paths(repo_root)
    paths = LifecyclePaths(
        claim=claim_path or defaults.claim,
        observations=observations_base or defaults.observations,
        results=results_base or defaults.results,
        terminal=terminal_path or defaults.terminal,
        results_manifest=results_manifest_path or defaults.results_manifest,
        m5=m5_path or defaults.m5,
    )
    policy = FrozenPolicy(
        enforce_raw_hashes=enforce_frozen_hashes,
        verify_git=verify_git,
    )
    (
        authorization,
        control,
        authorization_raw,
        control_raw,
        tasks,
        errors,
    ) = load_frozen_inputs(
        repo_root,
        policy=policy,
        authorization_path=authorization_path,
        control_path=control_path,
    )
    if paths.results_manifest.exists():
        _add(errors, "results_manifest_forbidden")
    if paths.m5.exists():
        _add(errors, "m5_path_forbidden")
    token_status = "UNCONSUMED"
    claim_count = 0
    claim_present = paths.claim.is_file()
    terminal_present = paths.terminal.is_file()
    result_root_count = 0
    if paths.results.exists() and paths.results.is_dir():
        result_root_count = sum(1 for path in paths.results.iterdir() if path.is_dir())
    if not claim_present:
        for label, path in (
            ("observations", paths.observations),
            ("results", paths.results),
            ("terminal", paths.terminal),
        ):
            if path.exists():
                _add(errors, f"{label}_present_without_claim")
        status = "READY_UNCLAIMED" if not errors else "INVALID"
        return {
            "status": status,
            "errors": errors,
            "token": token_status,
            "claim_count": claim_count,
            "tasks": 0,
            "threads": 0,
            "finalizations": 0,
            "attempts": 0,
            "retries": 0,
            "repairs": 0,
            "followups": 0,
            "results": 0,
            "judge_calls": 0,
            "aggregation_calls": 0,
            "side_effects": 0,
            "launch_claim_present": False,
            "terminal_present": False,
            "result_root_count": 0,
            "authorization_audit_status": (
                "READY_UNCONSUMED" if not errors else "INVALID"
            ),
            "request_binding_aggregate_sha256": (
                request_binding_aggregate(tasks) if len(tasks) == 60 else None
            ),
            "successor_revision_required": False,
        }
    claim_count = 1
    token_status = "CONSUMED"
    claim, claim_raw = _load_json_file(paths.claim, "launch_claim", errors)
    _validate_claim(
        repo_root,
        claim,
        authorization,
        control,
        authorization_raw,
        control_raw,
        tasks,
        errors,
    )
    evidence = _validate_evidence(
        repo_root,
        paths,
        claim,
        claim_raw,
        tasks,
        errors,
        allow_terminal_failure_prefix=terminal_present,
    )
    state = "CLAIMED_IN_PROGRESS"
    successor_required = False
    attempts = max(evidence["receipt_count"], evidence["response_count"])
    if terminal_present:
        terminal, terminal_raw = _load_json_file(
            paths.terminal, "execution_terminal", errors
        )
        state = _validate_terminal(
            repo_root,
            terminal,
            terminal_raw,
            claim,
            claim_raw,
            tasks,
            evidence,
            errors,
        )
        counts = terminal.get("counts") if isinstance(terminal, dict) else None
        if isinstance(counts, dict) and _is_int(counts.get("attempts")):
            attempts = counts["attempts"]
        successor_required = bool(terminal.get("successor_revision_required"))
    else:
        if any(evidence["protocol_errors"].values()):
            _add(errors, "invalid_raw_final_without_terminal")
        if evidence["final_count"] == 60:
            _add(errors, "complete_matrix_without_terminal")
    if errors:
        state = "INVALID"
    return {
        "status": state,
        "errors": errors,
        "token": token_status,
        "claim_count": claim_count,
        "tasks": evidence["receipt_count"],
        "threads": evidence["ready_response_count"],
        "finalizations": evidence["final_count"],
        "attempts": attempts,
        "retries": 0,
        "repairs": 0,
        "followups": 0,
        "results": evidence["final_count"],
        "judge_calls": 0,
        "aggregation_calls": 0,
        "side_effects": 0,
        "launch_claim_present": True,
        "terminal_present": terminal_present,
        "result_root_count": result_root_count,
        "authorization_audit_status": "CONSUMED_BY_CLAIM",
        "request_binding_aggregate_sha256": (
            request_binding_aggregate(tasks) if len(tasks) == 60 else None
        ),
        "successor_revision_required": successor_required,
    }


def gate_a_changed_paths(repo_root: Path = REPO_ROOT) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    observed_tree = _git_text(
        repo_root, "rev-parse", f"{GATE_A_BASELINE_HEAD}^{{tree}}"
    )
    if observed_tree != GATE_A_BASELINE_TREE:
        errors.append("gate_a_baseline_tree_mismatch")
    ancestor_code, _, _ = _git(
        repo_root, "merge-base", "--is-ancestor", GATE_A_BASELINE_HEAD, "HEAD"
    )
    if ancestor_code != 0:
        errors.append("gate_a_baseline_not_ancestor")
    code, out, _ = _git(
        repo_root,
        "diff",
        "--name-only",
        "--no-renames",
        GATE_A_BASELINE_HEAD,
        "HEAD",
        "--",
    )
    if code != 0:
        errors.append("gate_a_diff_unavailable")
        return [], errors
    try:
        paths = [line for line in out.decode("utf-8", errors="strict").splitlines() if line]
    except UnicodeDecodeError:
        return [], ["gate_a_diff_utf8_invalid"]
    unexpected = sorted(set(paths) - GATE_A_ALLOWED_PATHS)
    if unexpected:
        errors.append("gate_a_unexpected_changed_paths:" + ",".join(unexpected))
    return sorted(paths), errors


def _compact(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--expect-ready-unclaimed",
        action="store_true",
        help="Require the Gate A repository state.",
    )
    args = parser.parse_args(argv)
    result = audit_execution(REPO_ROOT)
    print(_compact(result))
    if args.expect_ready_unclaimed and result.get("status") != "READY_UNCLAIMED":
        return 1
    return 0 if result.get("status") != "INVALID" else 1


if __name__ == "__main__":
    raise SystemExit(main())
