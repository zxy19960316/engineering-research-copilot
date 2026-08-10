#!/usr/bin/env python3
"""Independently audit candidate or issued M4.2 authorization state."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
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
LAUNCH_CLAIM_RELATIVE = "evals/m4/execution/m4.2/launch-claim.json"
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

FORBIDDEN_EXACT = (
    Path("evals/m4/authorization/m4.2/authorization-token.json"),
    Path("evals/m4/authorization/m4.2/acceptance-claim.json"),
    Path("evals/m4/results-manifest.json"),
)
FORBIDDEN_PREFIXES = (
    Path("evals/m4/execution/m4.2"),
    Path("evals/m4/results/m4.2"),
    Path("evals/m5"),
)

_BASELINE_BLOB_CACHE: dict[tuple[str, str], tuple[str, bytes]] = {}
_SOURCE_VALUES_CACHE: dict[str, Any] | None = None
_SOURCE_VALUES_ERRORS: tuple[str, ...] = ()
_EXPECTED_PAIR_CACHE: tuple[dict[str, Any], dict[str, Any], bytes] | None = None
_SCHEMA_CACHE: tuple[dict[str, Any], dict[str, Any]] | None = None
_HISTORICAL_TOKENS_CACHE: dict[str, set[str]] = {}


class DuplicateKeyError(ValueError):
    """Strict JSON duplicate-key signal."""


def add_error(errors: list[str], code: str) -> None:
    if code not in errors:
        errors.append(code)


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


def _strict_equal(left: object, right: object) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, dict) and isinstance(right, dict):
        return set(left) == set(right) and all(
            _strict_equal(left[key], right[key]) for key in left
        )
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(
            _strict_equal(a, b) for a, b in zip(left, right, strict=True)
        )
    return left == right


def _pairs_no_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise DuplicateKeyError("duplicate_key")
        value[key] = item
    return value


def _reject_constant(_value: str) -> object:
    raise ValueError("non_finite_number")


def load_json_bytes(raw: bytes, label: str, errors: list[str]) -> dict[str, Any]:
    if raw.startswith(b"\xef\xbb\xbf"):
        add_error(errors, f"{label}_utf8_bom_forbidden")
        return {}
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        add_error(errors, f"{label}_utf8_invalid")
        return {}
    try:
        value = json.loads(
            text,
            object_pairs_hook=_pairs_no_duplicates,
            parse_constant=_reject_constant,
        )
    except DuplicateKeyError:
        add_error(errors, f"{label}_duplicate_key")
        return {}
    except ValueError as error:
        suffix = "non_finite_number" if "non_finite_number" in str(error) else "json_invalid"
        add_error(errors, f"{label}_{suffix}")
        return {}
    if not isinstance(value, dict):
        add_error(errors, f"{label}_object_root_required")
        return {}
    return value


def _json_type_matches(value: object, expected: str | list[str]) -> bool:
    names = [expected] if isinstance(expected, str) else expected
    checks = {
        "object": lambda item: isinstance(item, dict),
        "array": lambda item: isinstance(item, list),
        "string": lambda item: isinstance(item, str),
        "integer": lambda item: type(item) is int,
        "number": lambda item: type(item) in {int, float},
        "boolean": lambda item: type(item) is bool,
        "null": lambda item: item is None,
    }
    return any(name in checks and checks[name](value) for name in names)


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
        if "const" in node and not _strict_equal(value, node["const"]):
            errors.append(f"{location}:const")
        enum = node.get("enum")
        if isinstance(enum, list) and not any(_strict_equal(value, item) for item in enum):
            errors.append(f"{location}:enum")
        pattern = node.get("pattern")
        if isinstance(pattern, str) and isinstance(value, str) and re.search(pattern, value) is None:
            errors.append(f"{location}:pattern")
        minimum_length = node.get("minLength")
        if isinstance(value, str) and type(minimum_length) is int and len(value) < minimum_length:
            errors.append(f"{location}:minLength")
        if isinstance(value, dict):
            properties = node.get("properties") if isinstance(node.get("properties"), dict) else {}
            required = node.get("required") if isinstance(node.get("required"), list) else []
            if set(required) - set(value):
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


def _git(repo_root: Path, *arguments: str) -> subprocess.CompletedProcess[bytes]:
    environment = os.environ.copy()
    environment["GIT_NO_REPLACE_OBJECTS"] = "1"
    return subprocess.run(
        ["git", "--no-replace-objects", *arguments],
        cwd=repo_root,
        env=environment,
        capture_output=True,
        check=False,
    )


def _git_text(repo_root: Path, *arguments: str) -> str | None:
    completed = _git(repo_root, *arguments)
    if completed.returncode != 0:
        return None
    try:
        return completed.stdout.decode("utf-8", errors="strict").strip()
    except UnicodeDecodeError:
        return None


def _safe_relative(relative: str) -> str | None:
    path = PurePosixPath(relative.replace("\\", "/"))
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        return None
    return path.as_posix()


def _blob_oid(repo_root: Path, head: str, relative: str, errors: list[str], label: str) -> str:
    safe = _safe_relative(relative)
    if safe is None:
        add_error(errors, f"{label}_unsafe_path")
        return ""
    cache_key = (str(repo_root), safe)
    if head == BASELINE_HEAD and cache_key in _BASELINE_BLOB_CACHE:
        return _BASELINE_BLOB_CACHE[cache_key][0]
    oid = _git_text(repo_root, "rev-parse", f"{head}:{safe}")
    if oid is None or re.fullmatch(r"[0-9a-f]{40}", oid) is None:
        add_error(errors, f"{label}_blob_unavailable")
        return ""
    return oid


def _blob(repo_root: Path, head: str, relative: str, errors: list[str], label: str) -> bytes:
    safe = _safe_relative(relative)
    cache_key = (str(repo_root), safe or relative)
    if head == BASELINE_HEAD and cache_key in _BASELINE_BLOB_CACHE:
        return _BASELINE_BLOB_CACHE[cache_key][1]
    oid = _blob_oid(repo_root, head, relative, errors, label)
    if not oid:
        return b""
    completed = _git(repo_root, "cat-file", "blob", oid)
    if completed.returncode != 0:
        add_error(errors, f"{label}_blob_unavailable")
        return b""
    raw = completed.stdout
    framed = f"blob {len(raw)}\0".encode("ascii") + raw
    if hashlib.sha1(framed).hexdigest() != oid:
        add_error(errors, f"{label}_blob_content_mismatch")
        return b""
    if head == BASELINE_HEAD and safe is not None:
        _BASELINE_BLOB_CACHE[cache_key] = (oid, raw)
    return raw


def _snapshot(
    repo_root: Path, relative: str, errors: list[str], verify_git: bool
) -> bytes:
    expected_oid, expected_hash, expected_length = SNAPSHOTS[relative]
    oid = _blob_oid(repo_root, BASELINE_HEAD, relative, errors, "snapshot")
    raw = _blob(repo_root, BASELINE_HEAD, relative, errors, "snapshot")
    if oid != expected_oid:
        add_error(errors, f"snapshot_blob_mismatch:{relative}")
    if len(raw) != expected_length:
        add_error(errors, f"snapshot_length_mismatch:{relative}")
    if sha256(raw) != expected_hash:
        add_error(errors, f"snapshot_sha256_mismatch:{relative}")
    if verify_git and _blob_oid(repo_root, "HEAD", relative, errors, "head_snapshot") != expected_oid:
        add_error(errors, f"snapshot_head_blob_mismatch:{relative}")
    return raw


def _request_binding(task: Mapping[str, object]) -> str:
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


def _source_values(
    repo_root: Path, errors: list[str], verify_git: bool
) -> dict[str, Any]:
    global _SOURCE_VALUES_CACHE, _SOURCE_VALUES_ERRORS
    if not verify_git and _SOURCE_VALUES_CACHE is not None:
        for code in _SOURCE_VALUES_ERRORS:
            add_error(errors, code)
        return _SOURCE_VALUES_CACHE
    starting_error_count = len(errors)
    for relative in SNAPSHOTS:
        _snapshot(repo_root, relative, errors, verify_git)
    manifest = load_json_bytes(
        _snapshot(repo_root, MANIFEST_RELATIVE, errors, verify_git), "manifest", errors
    )
    matrix = manifest.get("matrix")
    randomization = manifest.get("randomization")
    helper = manifest.get("execution_helper")
    authority = manifest.get("authority")
    counters = manifest.get("counters")
    tasks = manifest.get("tasks")
    if not all(isinstance(item, dict) for item in (matrix, randomization, helper, authority, counters)):
        add_error(errors, "manifest_shape_invalid")
        return {}
    if not isinstance(tasks, list) or not all(isinstance(task, dict) for task in tasks):
        add_error(errors, "manifest_tasks_invalid")
        return {}
    batches = matrix.get("batches")
    if not isinstance(batches, list) or not all(isinstance(batch, dict) for batch in batches):
        add_error(errors, "manifest_batches_invalid")
        return {}
    if (
        manifest.get("schema_version") != "m4.2-successor-preparation-v1"
        or manifest.get("milestone") != "M4"
        or manifest.get("revision") != "M4.2"
        or manifest.get("status") != "PREPARATION_ONLY"
    ):
        add_error(errors, "manifest_identity_mismatch")
    expected_matrix = {
        "case_count": 12,
        "arm_count": 5,
        "planned_task_count": 60,
        "batch_count": 6,
    }
    for key, expected in expected_matrix.items():
        if type(matrix.get(key)) is not int or matrix.get(key) != expected:
            add_error(errors, f"matrix_{key}_mismatch")
    task_ids = [task.get("task_id") for task in tasks]
    source_task_ids = [task.get("source_task_id") for task in tasks]
    root_task_ids = [task.get("root_task_id") for task in tasks]
    blind_ids = [task.get("blind_id") for task in tasks]
    batch_ids = [batch.get("batch_id") for batch in batches]
    if (
        len(tasks) != 60
        or len(set(task_ids)) != 60
        or len(set(source_task_ids)) != 60
        or len(set(root_task_ids)) != 60
        or len(set(blind_ids)) != 60
    ):
        add_error(errors, "matrix_task_identity_mismatch")
    if blind_ids != [f"M4-J{index:03d}" for index in range(121, 181)]:
        add_error(errors, "matrix_blind_order_mismatch")
    if len(batches) != 6 or len(set(batch_ids)) != 6:
        add_error(errors, "matrix_batch_identity_mismatch")
    if randomization.get("task_order") != task_ids or randomization.get("frozen") is not True:
        add_error(errors, "matrix_task_order_mismatch")
    try:
        expected_blind_mapping = dict(zip(task_ids, blind_ids, strict=True))
    except ValueError:
        expected_blind_mapping = {}
    if randomization.get("blind_mapping") != expected_blind_mapping:
        add_error(errors, "matrix_blind_mapping_mismatch")
    if randomization.get("judge_mapping_access_authorized") is not False:
        add_error(errors, "matrix_blind_authority_mismatch")
    expected_manifest_counters = {name: 0 for name in COUNTER_NAMES[:9]}
    if not _strict_equal(counters, expected_manifest_counters):
        add_error(errors, "manifest_counters_nonzero")
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
        add_error(errors, "manifest_authority_mismatch")
    if (
        helper.get("path") != HELPER_RELATIVE
        or helper.get("raw_sha256") != SNAPSHOTS[HELPER_RELATIVE][1]
        or helper.get("request_binding_count") != 60
        or helper.get("read_only") is not True
    ):
        add_error(errors, "manifest_helper_binding_mismatch")

    task_by_id = {task.get("task_id"): task for task in tasks}
    members: list[object] = []
    for batch in batches:
        task_members = batch.get("task_ids")
        if not isinstance(task_members, list) or len(task_members) != 10 or len(set(task_members)) != 10:
            add_error(errors, "matrix_batch_members_invalid")
            continue
        members.extend(task_members)
        if (
            batch.get("planned_task_count") != 10
            or batch.get("stop_on_infrastructure_or_protocol_failure") is not True
            or batch.get("later_batches_mutable_after_observation") is not False
        ):
            add_error(errors, "matrix_batch_policy_mismatch")
        for task_id in task_members:
            task = task_by_id.get(task_id)
            if not isinstance(task, dict) or task.get("batch_id") != batch.get("batch_id"):
                add_error(errors, "matrix_task_batch_membership_mismatch")
    if sorted(str(item) for item in members) != sorted(str(item) for item in task_ids):
        add_error(errors, "matrix_batch_roster_mismatch")

    root_manifest = load_json_bytes(
        _blob(repo_root, BASELINE_HEAD, ROOT_MANIFEST_RELATIVE, errors, "root_manifest"),
        "root_manifest",
        errors,
    )
    constraints = root_manifest.get("execution_constraints")
    constraints_hash = sha256(canonical_bytes(constraints)) if isinstance(constraints, dict) else ""
    if not constraints_hash:
        add_error(errors, "execution_constraints_missing")
    protocol_raw = _snapshot(repo_root, TASK_PROTOCOL_RELATIVE, errors, verify_git)
    rubric_raw = _snapshot(repo_root, RUBRIC_RELATIVE, errors, verify_git)
    cases: dict[str, tuple[bytes, dict[str, Any]]] = {}
    variants: dict[str, bytes] = {}
    bindings: list[str] = []
    case_ids: set[str] = set()
    arm_ids: set[str] = set()
    for task in tasks:
        task_id = task.get("task_id")
        case_ids.add(str(task.get("case_id")))
        arm_ids.add(str(task.get("arm_id")))
        if not isinstance(task_id, str) or task.get("result_root") != f"{RESULT_ROOT_PREFIX}/{task_id}":
            add_error(errors, "task_result_root_mismatch")
        if task.get("result_root_must_be_absent") is not True:
            add_error(errors, "task_result_root_policy_mismatch")
        case_path = task.get("case_path")
        safe_case = _safe_relative(case_path) if isinstance(case_path, str) else None
        if safe_case is None or not safe_case.startswith("evals/m4/cases/"):
            add_error(errors, "task_case_path_invalid")
            continue
        if safe_case not in cases:
            raw = _blob(repo_root, BASELINE_HEAD, safe_case, errors, "case")
            cases[safe_case] = (raw, load_json_bytes(raw, "case", errors))
        case_raw, case = cases[safe_case]
        user_input = case.get("user_input")
        if sha256(case_raw) != task.get("case_sha256"):
            add_error(errors, "task_case_sha256_mismatch")
        if not isinstance(user_input, str) or sha256(user_input.encode("utf-8")) != task.get("user_input_sha256"):
            add_error(errors, "task_user_input_sha256_mismatch")
        if sha256(protocol_raw) != task.get("task_protocol_sha256"):
            add_error(errors, "task_protocol_sha256_mismatch")
        if sha256(rubric_raw) != task.get("rubric_sha256"):
            add_error(errors, "task_rubric_sha256_mismatch")
        if constraints_hash != task.get("execution_constraints_sha256"):
            add_error(errors, "task_execution_constraints_sha256_mismatch")
        variant_path = task.get("variant_instruction_path")
        variant_hash = task.get("variant_instruction_sha256")
        if variant_path is None:
            if variant_hash is not None:
                add_error(errors, "task_variant_hash_without_path")
        elif isinstance(variant_path, str):
            safe_variant = _safe_relative(variant_path)
            if safe_variant is None or not safe_variant.startswith("evals/m4/variants/"):
                add_error(errors, "task_variant_path_invalid")
            else:
                if safe_variant not in variants:
                    variants[safe_variant] = _blob(repo_root, BASELINE_HEAD, safe_variant, errors, "variant")
                if sha256(variants[safe_variant]) != variant_hash:
                    add_error(errors, "task_variant_sha256_mismatch")
        else:
            add_error(errors, "task_variant_path_invalid")
        try:
            binding = _request_binding(task)
        except (KeyError, TypeError, ValueError):
            binding = ""
            add_error(errors, "request_binding_input_invalid")
        bindings.append(binding)
        if binding != task.get("request_binding_sha256"):
            add_error(errors, "task_request_binding_mismatch")
    if len(case_ids) != 12 or len(arm_ids) != 5:
        add_error(errors, "matrix_case_arm_cardinality_mismatch")
    if len(bindings) != 60 or len(set(bindings)) != 60:
        add_error(errors, "request_binding_uniqueness_mismatch")
    result = {
        "tasks": tasks,
        "batches": batches,
        "task_ids": task_ids,
        "batch_ids": batch_ids,
    }
    if not verify_git:
        _SOURCE_VALUES_CACHE = result
        _SOURCE_VALUES_ERRORS = tuple(errors[starting_error_count:])
    return result


def _unsigned_token(payload: Mapping[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("authorization_token", None)
    return "sha256:" + sha256(canonical_bytes(unsigned))


def _historical_tokens(repo_root: Path, errors: list[str]) -> set[str]:
    cache_key = str(repo_root)
    if cache_key in _HISTORICAL_TOKENS_CACHE:
        return _HISTORICAL_TOKENS_CACHE[cache_key]
    completed = _git(
        repo_root,
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
        add_error(errors, "historical_authorization_token_scan_failed")
        return set()
    try:
        values = completed.stdout.decode("ascii", errors="strict").splitlines()
    except UnicodeDecodeError:
        add_error(errors, "historical_authorization_token_scan_invalid")
        return set()
    tokens = {
        value for value in values if re.fullmatch(r"sha256:[0-9a-f]{64}", value)
    }
    _HISTORICAL_TOKENS_CACHE[cache_key] = tokens
    return tokens


def _expected_pair(values: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any], bytes]:
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
            "project_label": "engineering-research-copilot",
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
            "authorized_task_ids": list(values.get("task_ids", [])),
            "authorized_task_count": 60,
            "authorized_batch_ids": list(values.get("batch_ids", [])),
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
            "batch_order": list(values.get("batch_ids", [])),
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
    authorization["authorization_token"] = _unsigned_token(authorization)
    authorization_raw = json_bytes(authorization)
    controlled_tasks: list[dict[str, Any]] = []
    for task in values.get("tasks", []):
        allowed = [task["case_path"], TASK_PROTOCOL_RELATIVE]
        if task["variant_instruction_path"] is not None:
            allowed.append(task["variant_instruction_path"])
        controlled_tasks.append(
            {
                "task_id": task["task_id"],
                "source_task_id": task["source_task_id"],
                "root_task_id": task["root_task_id"],
                "blind_id": task["blind_id"],
                "batch_id": task["batch_id"],
                "case_path": task["case_path"],
                "task_protocol_path": TASK_PROTOCOL_RELATIVE,
                "variant_instruction_path": task["variant_instruction_path"],
                "request_binding_sha256": task["request_binding_sha256"],
                "result_root": task["result_root"],
                "result_root_must_be_absent": True,
                "allowed_context_paths": allowed,
                "forbidden_context_roots": ["evals/m4/results", "evals/m4/execution"],
                "attempt_limit": 1,
                "independent_finalization_required": True,
                "cross_task_result_visibility": False,
            }
        )
    controlled_batches = [
        {
            "batch_id": batch["batch_id"],
            "source_batch_id": batch["source_batch_id"],
            "domain": batch["domain"],
            "task_ids": batch["task_ids"],
            "planned_task_count": 10,
            "stop_on_infrastructure_or_protocol_failure": True,
            "later_batches_mutable_after_observation": False,
        }
        for batch in values.get("batches", [])
    ]
    control = {
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
        "batch_order": list(values.get("batch_ids", [])),
        "batches": controlled_batches,
        "tasks": controlled_tasks,
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
    return authorization, control, authorization_raw


def _changed_paths(repo_root: Path, errors: list[str]) -> set[str]:
    found: set[str] = set()
    committed = _git_text(
        repo_root, "diff", "--name-only", "--no-renames", BASELINE_HEAD, "HEAD", "--"
    )
    if committed is None:
        add_error(errors, "authorization_change_set_unavailable")
    else:
        found.update(line for line in committed.splitlines() if line)
    status = _git(repo_root, "status", "--porcelain=v1", "--untracked-files=all")
    if status.returncode != 0:
        add_error(errors, "authorization_change_set_unavailable")
    else:
        try:
            lines = status.stdout.decode("utf-8", errors="strict").splitlines()
        except UnicodeDecodeError:
            lines = []
            add_error(errors, "authorization_change_set_unavailable")
        for line in lines:
            path = line[3:]
            if " -> " in path:
                left, right = path.split(" -> ", 1)
                found.add(left.strip('"'))
                found.add(right.strip('"'))
            else:
                found.add(path.strip('"'))
    return {path.replace("\\", "/") for path in found}


def discover_forbidden_paths(
    repo_root: Path, present_paths: set[str] | None = None
) -> list[str]:
    found: set[str] = set()
    for relative in FORBIDDEN_EXACT:
        path = repo_root / relative
        if path.exists() or path.is_symlink():
            found.add(relative.as_posix())
    for relative in FORBIDDEN_PREFIXES:
        path = repo_root / relative
        if path.exists() or path.is_symlink():
            if path.is_file() or path.is_symlink():
                found.add(relative.as_posix())
            else:
                found.update(
                    item.relative_to(repo_root).as_posix()
                    for item in path.rglob("*")
                    if item.is_file() or item.is_symlink()
                )
    if present_paths:
        found.update(path.replace("\\", "/") for path in present_paths)
    return sorted(found)


def audit_authorization(
    repo_root: Path = REPO_ROOT,
    *,
    authorization_data: Mapping[str, object] | None = None,
    control_data: Mapping[str, object] | None = None,
    verify_git: bool = True,
    present_paths: set[str] | None = None,
) -> dict[str, object]:
    global _EXPECTED_PAIR_CACHE, _SCHEMA_CACHE
    repo_root = Path(repo_root).resolve(strict=False)
    authorization_path = repo_root / AUTHORIZATION_RELATIVE
    control_path = repo_root / CONTROL_RELATIVE
    errors: list[str] = []
    if verify_git:
        if _git(repo_root, "cat-file", "-e", f"{BASELINE_HEAD}^{{commit}}").returncode != 0:
            add_error(errors, "baseline_head_unavailable")
        if _git_text(repo_root, "rev-parse", f"{BASELINE_HEAD}^{{tree}}") != BASELINE_TREE:
            add_error(errors, "baseline_tree_mismatch")
        if _git(repo_root, "merge-base", "--is-ancestor", BASELINE_HEAD, "HEAD").returncode != 0:
            add_error(errors, "baseline_head_not_ancestor")
    values = _source_values(repo_root, errors, verify_git)
    if not verify_git and _EXPECTED_PAIR_CACHE is not None:
        expected_authorization, expected_control, expected_authorization_raw = _EXPECTED_PAIR_CACHE
    else:
        expected_authorization, expected_control, expected_authorization_raw = _expected_pair(values)
        if not verify_git:
            _EXPECTED_PAIR_CACHE = (
                expected_authorization,
                expected_control,
                expected_authorization_raw,
            )
    if not verify_git and _SCHEMA_CACHE is not None:
        authorization_schema, control_schema = _SCHEMA_CACHE
    else:
        authorization_schema = load_json_bytes(
            _snapshot(repo_root, AUTHORIZATION_SCHEMA_RELATIVE, errors, verify_git),
            "authorization_schema",
            errors,
        )
        control_schema = load_json_bytes(
            _snapshot(repo_root, CONTROL_SCHEMA_RELATIVE, errors, verify_git),
            "control_schema",
            errors,
        )
        if not verify_git:
            _SCHEMA_CACHE = (authorization_schema, control_schema)
    if schema_errors(expected_authorization, authorization_schema):
        add_error(errors, "BLOCKED_FROZEN_AUTHORIZATION_SCHEMA")
    if schema_errors(expected_control, control_schema):
        add_error(errors, "BLOCKED_FROZEN_AUTHORIZATION_SCHEMA")
    expected_token = str(expected_authorization.get("authorization_token", ""))
    if expected_token in _historical_tokens(repo_root, errors):
        add_error(errors, "authorization_token_reused")

    override = authorization_data is not None or control_data is not None
    authorization_present = authorization_data is not None or authorization_path.exists()
    control_present = control_data is not None or control_path.exists()
    if authorization_present != control_present:
        add_error(errors, "partial_authorization_pair_present")
    authorization: dict[str, Any] = {}
    control: dict[str, Any] = {}
    authorization_raw = b""
    if authorization_present and control_present:
        if override:
            if not isinstance(authorization_data, Mapping) or not isinstance(control_data, Mapping):
                add_error(errors, "authorization_pair_override_incomplete")
            else:
                authorization = dict(authorization_data)
                control = dict(control_data)
                authorization_raw = json_bytes(authorization)
        else:
            if authorization_path.is_symlink() or control_path.is_symlink():
                add_error(errors, "authorization_pair_symlink_forbidden")
            try:
                authorization_raw = authorization_path.read_bytes()
                control_raw = control_path.read_bytes()
            except OSError:
                authorization_raw = b""
                control_raw = b""
                add_error(errors, "authorization_pair_unreadable")
            authorization = load_json_bytes(authorization_raw, "authorization", errors)
            control = load_json_bytes(control_raw, "control", errors)
        if not _strict_equal(authorization, expected_authorization):
            add_error(errors, "authorization_instance_mismatch")
        if not _strict_equal(control, expected_control):
            add_error(errors, "control_instance_mismatch")
        for error in schema_errors(authorization, authorization_schema):
            add_error(errors, f"authorization_schema:{error}")
        for error in schema_errors(control, control_schema):
            add_error(errors, f"control_schema:{error}")
        if authorization.get("authorization_token") != _unsigned_token(authorization):
            add_error(errors, "authorization_token_invalid")
        authorization_link = control.get("authorization")
        if not isinstance(authorization_link, Mapping):
            add_error(errors, "control_authorization_link_invalid")
        else:
            if authorization_link.get("raw_sha256") != sha256(authorization_raw):
                add_error(errors, "control_authorization_raw_sha256_mismatch")
            if authorization_link.get("authorization_token") != authorization.get("authorization_token"):
                add_error(errors, "control_authorization_token_mismatch")

    forbidden_paths = discover_forbidden_paths(repo_root, present_paths)
    if forbidden_paths:
        add_error(errors, "forbidden_lifecycle_path_present")
    if verify_git:
        unexpected = _changed_paths(repo_root, errors) - ALLOWED_CHANGE_PATHS
        if unexpected:
            add_error(errors, "authorization_change_set_mismatch")
    if present_paths and any(path.replace("\\", "/") not in {AUTHORIZATION_RELATIVE, CONTROL_RELATIVE} for path in present_paths):
        add_error(errors, "authorization_change_set_mismatch")

    if errors:
        status = "BLOCKED"
    elif authorization_present and control_present:
        status = "M4_2_AUTHORIZED_UNCONSUMED_NOT_CLAIMED_NOT_EXECUTED"
    else:
        status = "M4_2_ONE_SHOT_AUTHORIZATION_CANDIDATE_READY_NOT_ISSUED"
    token = expected_token
    return {
        "status": status,
        "decision": (
            "APPROVE_M4_2_SEPARATE_ONE_SHOT_CLAIM_AND_EXECUTION_WORK_PACKAGE_ONLY"
            if status == "M4_2_AUTHORIZED_UNCONSUMED_NOT_CLAIMED_NOT_EXECUTED"
            else "NOT_ISSUED"
        ),
        "errors": sorted(errors),
        "baseline_head": BASELINE_HEAD,
        "baseline_tree": BASELINE_TREE,
        "authorization_artifact": "PRESENT" if authorization_present else "ABSENT",
        "execution_control": "PRESENT" if control_present else "ABSENT",
        "authorization_token_status": "UNCONSUMED" if authorization_present else "NOT_ISSUED",
        "token_fingerprint": token[:19] + "..." if token else "",
        "claim_count": 0,
        "launch_claim": "ABSENT",
        "authorized_task_count": 60,
        "authorized_batch_count": 6,
        "actual_counters": dict(ZERO_COUNTERS),
        "judge": "NOT_RUN",
        "blind_mapping": "NOT_ACCESSED",
        "aggregation": "NOT_RUN",
        "m4_closure": "NOT_RUN",
        "m5": "NOT_STARTED",
        "forbidden_path_count": len(forbidden_paths),
        "forbidden_paths": forbidden_paths,
        "expected_authorization_raw_sha256": sha256(expected_authorization_raw),
        "expected_control_raw_sha256": sha256(json_bytes(expected_control)),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    expectations = parser.add_mutually_exclusive_group()
    expectations.add_argument("--expect-candidate-not-issued", action="store_true")
    expectations.add_argument("--expect-authorized-unconsumed", action="store_true")
    arguments = parser.parse_args(argv)
    result = audit_authorization()
    expected = None
    if arguments.expect_candidate_not_issued:
        expected = "M4_2_ONE_SHOT_AUTHORIZATION_CANDIDATE_READY_NOT_ISSUED"
    elif arguments.expect_authorized_unconsumed:
        expected = "M4_2_AUTHORIZED_UNCONSUMED_NOT_CLAIMED_NOT_EXECUTED"
    if expected is not None and result["status"] != expected:
        result = dict(result)
        result["errors"] = sorted(set(result["errors"]) | {"expected_state_mismatch"})
        result["status"] = "BLOCKED"
    sys.stdout.buffer.write(canonical_bytes(result) + b"\n")
    return 0 if not result["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
