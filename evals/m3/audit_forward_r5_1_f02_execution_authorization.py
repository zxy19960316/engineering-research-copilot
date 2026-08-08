#!/usr/bin/env python3
"""Audit the one-shot r5.1-f02 execution authorization without launching it."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from audit_forward_r5_1_f02_authorization import audit_authorization as readiness_audit
from r5_1_f02_execution_contract import (
    AUTHORIZATION_PATH,
    BINDING_KEYS,
    CASE_ID,
    EVIDENCE_HEAD,
    LAUNCH_CONTRACT_PATH,
    PREPARATION_BASELINE_HEAD,
    READINESS_CI_RUN_ID,
    READINESS_HEAD,
    READINESS_MANIFEST_PATH,
    RESULT_ROOT as RESULT_ROOT_RELATIVE,
    REVISION,
    canonical_sha256,
    parse_json_object,
    sha256,
    validate_execution_authorization_shape,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
AUTHORIZATION = REPO_ROOT / AUTHORIZATION_PATH
READINESS_MANIFEST = REPO_ROOT / READINESS_MANIFEST_PATH
LAUNCH_CONTRACT = REPO_ROOT / LAUNCH_CONTRACT_PATH
RESULT_ROOT = REPO_ROOT / RESULT_ROOT_RELATIVE


def _load(path: Path, errors: list[str], code: str) -> tuple[dict[str, Any] | None, bytes | None]:
    try:
        raw = path.read_bytes()
        return parse_json_object(raw), raw
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        errors.append(f"{code}_invalid_json")
        return None, None


def _git_blob(head: str, path: str) -> tuple[str, bytes] | None:
    try:
        commit = subprocess.run(
            ["git", "cat-file", "-e", f"{head}^{{commit}}"],
            cwd=REPO_ROOT,
            capture_output=True,
            check=False,
        )
        raw = subprocess.run(
            ["git", "show", f"{head}:{path}"],
            cwd=REPO_ROOT,
            capture_output=True,
            check=False,
        )
        oid = subprocess.run(
            ["git", "rev-parse", f"{head}:{path}"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
    except OSError:
        return None
    if commit.returncode != 0 or raw.returncode != 0 or oid.returncode != 0:
        return None
    return oid.stdout.strip(), raw.stdout


def _git_hash_object(raw: bytes) -> str | None:
    try:
        result = subprocess.run(
            ["git", "hash-object", "--stdin"],
            cwd=REPO_ROOT,
            input=raw,
            capture_output=True,
            check=False,
        )
    except OSError:
        return None
    return result.stdout.decode("ascii", errors="strict").strip() if result.returncode == 0 else None


def _verify_readiness_manifest(
    authorization: dict[str, Any], errors: list[str]
) -> dict[str, Any] | None:
    reference = authorization.get("readiness_authorization_manifest")
    if not isinstance(reference, dict):
        errors.append("readiness_manifest_reference_invalid")
        return None
    blob = _git_blob(READINESS_HEAD, READINESS_MANIFEST_PATH)
    if blob is None:
        errors.append("readiness_manifest_blob_unavailable")
        return None
    oid, raw = blob
    try:
        value = parse_json_object(raw)
    except (UnicodeError, json.JSONDecodeError, ValueError):
        errors.append("readiness_manifest_blob_invalid_json")
        return None
    expected = {
        "path": READINESS_MANIFEST_PATH,
        "git_blob_oid": oid,
        "raw_sha256": sha256(raw),
        "canonical_sha256": canonical_sha256(value),
    }
    for field, required in expected.items():
        if reference.get(field) != required:
            errors.append(f"readiness_manifest_{field}_mismatch")
    try:
        if READINESS_MANIFEST.read_bytes() != raw:
            errors.append("readiness_manifest_worktree_drift")
    except OSError:
        errors.append("readiness_manifest_worktree_unavailable")
    return value


def _verify_launch_contract(authorization: dict[str, Any], errors: list[str]) -> None:
    reference = authorization.get("launch_contract")
    if not isinstance(reference, dict):
        errors.append("launch_contract_reference_invalid")
        return
    value, raw = _load(LAUNCH_CONTRACT, errors, "launch_contract")
    if value is None or raw is None:
        return
    expected = {
        "path": LAUNCH_CONTRACT_PATH,
        "git_blob_oid": _git_hash_object(raw),
        "raw_sha256": sha256(raw),
        "canonical_sha256": canonical_sha256(value),
    }
    for field, required in expected.items():
        if reference.get(field) != required:
            errors.append(f"launch_contract_{field}_mismatch")
    if value.get("$id") != "m3.1-forward-r5.1-f02-launch-receipt-v1":
        errors.append("launch_contract_schema_id_invalid")
    properties = value.get("properties")
    if not isinstance(properties, dict):
        errors.append("launch_contract_properties_invalid")
        return
    required_constants = {
        "case_id": CASE_ID,
        "revision": REVISION,
        "launch_count": 1,
        "historical_task_reused": False,
        "no_retry": True,
    }
    for field, required in required_constants.items():
        field_schema = properties.get(field)
        if not isinstance(field_schema, dict) or field_schema.get("const") != required:
            errors.append(f"launch_contract_field_invalid:{field}")


def audit_execution_authorization(path: str | Path) -> dict[str, Any]:
    errors: list[str] = []
    authorization, _ = _load(Path(path), errors, "execution_authorization")
    if authorization is None:
        return {
            "status": "invalid",
            "case_id": CASE_ID,
            "revision": REVISION,
            "max_fresh_tasks": 1,
            "reserved_task_id": None,
            "counters": {},
            "result_artifact_count": 0,
            "historical_f02_retry_count": 0,
            "callback_invocations": 0,
            "side_effects": [],
            "errors": sorted(set(errors)),
            "evidence_gaps": [],
        }

    errors.extend(validate_execution_authorization_shape(authorization))
    readiness = _verify_readiness_manifest(authorization, errors)
    _verify_launch_contract(authorization, errors)

    if isinstance(readiness, dict):
        comparisons = {
            "preparation_manifest": "preparation_manifest",
            "input_binding": "input_binding",
            "source_input": "source_input",
            "prompt": "prompt",
            "replacement_contract": "replacement_contract",
            "base_contract": "base_contract",
            "m2_validation": "m2_validation",
            "eligibility": "eligibility",
            "supersession_policy": "supersession_policy",
            "route_condition_authority": "route_condition_authority",
        }
        bindings = authorization.get("bindings")
        if not isinstance(bindings, dict) or set(bindings) != BINDING_KEYS:
            errors.append("execution_authorization_bindings_invalid")
        else:
            for binding, readiness_field in comparisons.items():
                if bindings.get(binding) != readiness.get(readiness_field):
                    errors.append(f"readiness_binding_drift:{binding}")
        if authorization.get("future_paths") != readiness.get("future_paths"):
            errors.append("readiness_future_paths_drift")
        if authorization.get("counters") != readiness.get("counters"):
            errors.append("readiness_counters_drift")
        if authorization.get("historical_failed_task") != readiness.get(
            "historical_failed_task"
        ):
            errors.append("readiness_historical_task_drift")
        if authorization.get("result_root") != readiness.get("result_root"):
            errors.append("readiness_result_root_drift")

    predecessor = readiness_audit(READINESS_MANIFEST)
    if predecessor.get("status") != "ready_for_fresh_authorization":
        errors.append("readiness_audit_not_ready")
    if predecessor.get("result_artifact_count") != 0:
        errors.append("readiness_result_root_not_empty")
    predecessor_errors = predecessor.get("errors")
    if isinstance(predecessor_errors, list) and "immutable_r5_evidence_changed" in predecessor_errors:
        errors.append("immutable_r5_evidence_changed")
    if predecessor.get("historical_f02_retry_count") != 0:
        errors.append("historical_f02_retry_count_nonzero")
    predecessor_counters = predecessor.get("counters")
    if not isinstance(predecessor_counters, dict) or any(
        isinstance(value, bool) or value != 0 for value in predecessor_counters.values()
    ):
        errors.append("readiness_counters_nonzero")

    if authorization.get("readiness_head") != READINESS_HEAD:
        errors.append("readiness_head_mismatch")
    if authorization.get("readiness_ci_run_id") != READINESS_CI_RUN_ID:
        errors.append("readiness_ci_run_id_mismatch")
    if authorization.get("historical_evidence_head") != EVIDENCE_HEAD:
        errors.append("historical_evidence_head_mismatch")
    if authorization.get("preparation_baseline_head") != PREPARATION_BASELINE_HEAD:
        errors.append("preparation_baseline_head_mismatch")

    artifact_count = predecessor.get("result_artifact_count")
    if not isinstance(artifact_count, int) or isinstance(artifact_count, bool):
        artifact_count = -1
    historical_retry_count = predecessor.get("historical_f02_retry_count")
    return {
        "status": "ready_for_one_shot_fresh_execution" if not errors else "invalid",
        "case_id": authorization.get("authorized_case_id"),
        "revision": authorization.get("authorized_revision"),
        "readiness_head": authorization.get("readiness_head"),
        "readiness_ci_run_id": authorization.get("readiness_ci_run_id"),
        "historical_evidence_head": authorization.get("historical_evidence_head"),
        "preparation_baseline_head": authorization.get("preparation_baseline_head"),
        "authorization_token": authorization.get("authorization_token"),
        "max_fresh_tasks": authorization.get("max_fresh_tasks"),
        "reserved_task_id": authorization.get("reserved_task_id"),
        "counters": authorization.get("counters"),
        "result_artifact_count": artifact_count,
        "historical_f02_retry_count": historical_retry_count,
        "callback_invocations": 0,
        "side_effects": [],
        "errors": sorted(set(errors)),
        "evidence_gaps": [],
        "does_not_prove": [
            "No fresh context has been created or launched.",
            "No model final has been finalized, consumed, repaired, or accepted.",
            "Cross-revision aggregation, M3 closure, and M4 remain unauthorized.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) > 1:
        return 2
    path = Path(arguments[0]) if arguments else AUTHORIZATION
    result = audit_execution_authorization(path)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0 if result["status"] == "ready_for_one_shot_fresh_execution" else 1


if __name__ == "__main__":
    raise SystemExit(main())
