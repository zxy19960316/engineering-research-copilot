#!/usr/bin/env python3
"""Audit r5.1-f02 authorization readiness without authorizing or consuming it."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from audit_forward_r5_1_f02_preparation import audit_preparation
from r5_dispatch_contract import COUNTER_KEYS, validate_future_paths


REPO_ROOT = Path(__file__).resolve().parents[2]
PREPARATION_BASELINE_HEAD = "bbf54721b090d9d91b269d88e31919ae00fb0a39"
EVIDENCE_HEAD = "1b696bce53ee0a11163bfe4f91a9a49ab3af6f49"
HISTORICAL_TASK_ID = "019fd687-5575-7143-8cf3-1ab3069611f5"
HISTORICAL_RESULT_ROOT = "evals/m3/results/forward-r5"
RESULT_ROOT = REPO_ROOT / "evals" / "m3" / "results" / "forward-r5.1-f02"
CASE_ID = "m3-f02"
REVISION = "r5.1-f02"
SCHEMA_VERSION = "m3.1-forward-r5.1-f02-authorization-readiness-v1"
CONDITION_FIELDS = ["criterion_type", "metric_id", "operator", "value", "unit"]

EXPECTED_PATHS = {
    "preparation_manifest": "evals/m3/forward-inputs-r5.1-f02/manifest.json",
    "input_binding": "evals/m3/forward-inputs-r5.1-f02/m3-f02.input-binding.json",
    "source_input": "evals/m3/forward-inputs-r2/m3-f02-route-compatible.bundle.json",
    "prompt": "evals/m3/forward-inputs-r5.1-f02/m3-f02.prompt.txt",
    "replacement_contract": "evals/m3/forward-inputs-r5.1-f02/m3-model-output-contract.schema.json",
    "base_contract": "evals/m3/forward-inputs-r5/m3-model-output-contract.schema.json",
    "m2_validation": "evals/m3/forward-inputs-r4/m3-f02.m2-validation.json",
    "eligibility": "evals/m3/forward-inputs-r4/m3-f02.eligibility.json",
    "supersession_policy": "evals/m3/results/diagnostics-r5.1/r5-acceptance-erratum.json",
}


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _canonical_sha256(value: Any) -> str:
    return _sha256(_canonical_bytes(value))


def _parse_json(raw: bytes) -> dict[str, Any]:
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ValueError("utf8_bom_forbidden")
    value = json.loads(raw.decode("utf-8", errors="strict"))
    if not isinstance(value, dict):
        raise ValueError("json_object_required")
    return value


def _load_manifest(path: Path, errors: list[str]) -> dict[str, Any] | None:
    try:
        return _parse_json(path.read_bytes())
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        errors.append("authorization_manifest_invalid_json")
        return None


def _git_blob(head: str, path: str, errors: list[str], code: str) -> tuple[str, bytes] | None:
    try:
        commit = subprocess.run(
            ["git", "cat-file", "-e", f"{head}^{{commit}}"],
            cwd=REPO_ROOT,
            capture_output=True,
            check=False,
        )
        if commit.returncode != 0:
            errors.append(f"{code}_head_unavailable")
            return None
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
        errors.append(f"{code}_head_unavailable")
        return None
    if raw.returncode != 0 or oid.returncode != 0:
        errors.append(f"{code}_blob_missing")
        return None
    return oid.stdout.strip(), raw.stdout


def _verify_reference(
    value: object,
    code: str,
    errors: list[str],
    *,
    json_required: bool,
) -> tuple[dict[str, Any] | None, bytes | None]:
    if not isinstance(value, dict):
        errors.append(f"{code}_reference_invalid")
        return None, None
    expected_path = EXPECTED_PATHS[code]
    if value.get("path") != expected_path:
        errors.append(f"{code}_path_mismatch")
        return None, None
    blob = _git_blob(PREPARATION_BASELINE_HEAD, expected_path, errors, code)
    if blob is None:
        return None, None
    oid, raw = blob
    if value.get("git_blob_oid") != oid:
        errors.append(f"{code}_git_blob_oid_mismatch")
    if value.get("raw_sha256") != _sha256(raw):
        errors.append(f"{code}_raw_sha256_mismatch")
    parsed: dict[str, Any] | None = None
    if json_required:
        try:
            parsed = _parse_json(raw)
        except (UnicodeError, json.JSONDecodeError, ValueError):
            errors.append(f"{code}_blob_invalid_json")
        if parsed is not None and value.get("canonical_sha256") != _canonical_sha256(parsed):
            errors.append(f"{code}_canonical_sha256_mismatch")
    return parsed, raw


def _r5_evidence_tree_clean() -> bool:
    try:
        result = subprocess.run(
            [
                "git",
                "diff",
                "--quiet",
                EVIDENCE_HEAD,
                "--",
                HISTORICAL_RESULT_ROOT,
            ],
            cwd=REPO_ROOT,
            check=False,
        )
    except OSError:
        return False
    return result.returncode == 0


def _check_result_root(manifest: dict[str, Any], errors: list[str]) -> int:
    declared = manifest.get("result_root")
    if declared == HISTORICAL_RESULT_ROOT:
        errors.append("historical_result_root_reuse_forbidden")
    try:
        resolved = (REPO_ROOT / declared).resolve() if isinstance(declared, str) else None
    except (OSError, ValueError):
        resolved = None
    if resolved != RESULT_ROOT.resolve():
        errors.append("result_root_not_canonical")
    if not RESULT_ROOT.is_dir() or RESULT_ROOT.is_symlink():
        errors.append("result_root_missing")
        return 0
    marker = RESULT_ROOT / ".gitkeep"
    try:
        marker_valid = marker.is_file() and not marker.is_symlink() and marker.read_bytes() == b""
    except OSError:
        marker_valid = False
    if not marker_valid:
        errors.append("result_root_marker_invalid")
    artifacts = [path for path in RESULT_ROOT.iterdir() if path.name != ".gitkeep"]
    if artifacts:
        errors.append("result_root_not_empty")
    return len(artifacts)


def _check_counters(value: object, errors: list[str]) -> dict[str, int]:
    counters = value if isinstance(value, dict) else {}
    if set(counters) != set(COUNTER_KEYS):
        errors.append("authorization_counter_keys_invalid")
    result: dict[str, int] = {}
    for key in COUNTER_KEYS:
        raw = counters.get(key)
        result[key] = raw if isinstance(raw, int) and not isinstance(raw, bool) else -1
        if raw != 0:
            errors.append(f"authorization_counter_nonzero:{key}")
    return result


def _same_fields(left: object, right: object, fields: tuple[str, ...]) -> bool:
    return isinstance(left, dict) and isinstance(right, dict) and all(
        left.get(field) == right.get(field) for field in fields
    )


def audit_authorization(manifest_path: str | Path) -> dict[str, Any]:
    errors: list[str] = []
    manifest = _load_manifest(Path(manifest_path), errors)
    if manifest is None:
        return {
            "status": "invalid",
            "case_id": CASE_ID,
            "revision": REVISION,
            "new_fresh_run_authorized": False,
            "reserved_task_id": None,
            "counters": {key: 0 for key in COUNTER_KEYS},
            "result_artifact_count": 0,
            "side_effects": [],
            "errors": sorted(set(errors)),
            "evidence_gaps": [],
        }

    if manifest.get("schema_version") != SCHEMA_VERSION:
        errors.append("authorization_schema_version_invalid")
    if manifest.get("status") != "ready_for_fresh_authorization":
        errors.append("authorization_status_invalid")
    if manifest.get("preparation_baseline_head") != PREPARATION_BASELINE_HEAD:
        errors.append("preparation_baseline_head_drift")
    if manifest.get("historical_evidence_head") != EVIDENCE_HEAD:
        errors.append("historical_evidence_head_drift")
    if manifest.get("case_id") != CASE_ID or manifest.get("revision") != REVISION:
        errors.append("replacement_identity_invalid")
    if (
        manifest.get("m3_status") != "IN_PROGRESS"
        or manifest.get("historical_r5_status") != "BLOCKED_NOT_ACCEPTED"
        or manifest.get("m4_status") != "NOT_STARTED"
    ):
        errors.append("milestone_status_drift")
    if manifest.get("new_fresh_run_authorized") is not False:
        errors.append("fresh_run_authorization_must_be_false")
    reserved_task_id = manifest.get("reserved_task_id")
    if reserved_task_id is not None:
        errors.append("reserved_task_id_forbidden_before_authorization")
    if reserved_task_id == HISTORICAL_TASK_ID:
        errors.append("historical_task_id_reuse_forbidden")
    if manifest.get("side_effects") != []:
        errors.append("authorization_side_effects_must_be_empty")

    preparation, _ = _verify_reference(
        manifest.get("preparation_manifest"),
        "preparation_manifest",
        errors,
        json_required=True,
    )
    binding, _ = _verify_reference(
        manifest.get("input_binding"), "input_binding", errors, json_required=True
    )
    source, _ = _verify_reference(
        manifest.get("source_input"), "source_input", errors, json_required=True
    )
    _verify_reference(manifest.get("prompt"), "prompt", errors, json_required=False)
    replacement_contract, _ = _verify_reference(
        manifest.get("replacement_contract"),
        "replacement_contract",
        errors,
        json_required=True,
    )
    base_contract, _ = _verify_reference(
        manifest.get("base_contract"), "base_contract", errors, json_required=True
    )
    m2_validation, _ = _verify_reference(
        manifest.get("m2_validation"), "m2_validation", errors, json_required=True
    )
    eligibility, _ = _verify_reference(
        manifest.get("eligibility"), "eligibility", errors, json_required=True
    )
    erratum, _ = _verify_reference(
        manifest.get("supersession_policy"),
        "supersession_policy",
        errors,
        json_required=True,
    )

    if isinstance(preparation, dict):
        if (
            preparation.get("based_on_head") != "c5ca408beedf2c3f20160fb1d06293336eacd725"
            or preparation.get("historical_evidence_head") != EVIDENCE_HEAD
            or preparation.get("revision") != REVISION
            or preparation.get("case_id") != CASE_ID
            or preparation.get("new_fresh_run_authorized") is not False
            or preparation.get("reserved_task_id") is not None
        ):
            errors.append("preparation_manifest_state_drift")
        for auth_key, prep_key in (
            ("input_binding", "input_binding"),
            ("prompt", "prompt"),
            ("replacement_contract", "contract"),
        ):
            if not _same_fields(
                manifest.get(auth_key), preparation.get(prep_key), ("path", "raw_sha256")
            ):
                errors.append(f"{auth_key}_preparation_binding_mismatch")
        if manifest.get("future_paths") != preparation.get("future_paths"):
            errors.append("future_paths_preparation_mismatch")
        if manifest.get("counters") != preparation.get("counters"):
            errors.append("counters_preparation_mismatch")

    if isinstance(binding, dict):
        if not _same_fields(
            manifest.get("source_input"),
            binding.get("source_input"),
            ("path", "git_blob_oid", "raw_sha256", "canonical_sha256"),
        ):
            errors.append("source_input_binding_mismatch")
        for key in ("m2_validation", "eligibility"):
            if not _same_fields(
                manifest.get(key), binding.get(key), ("path", "raw_sha256", "required_status")
            ):
                errors.append(f"{key}_binding_mismatch")
        if manifest.get("route_condition_authority") != binding.get(
            "route_condition_authority"
        ):
            errors.append("route_condition_authority_binding_mismatch")
        failed = binding.get("historical_failed_task", {})
        if (
            failed.get("task_id") != HISTORICAL_TASK_ID
            or failed.get("result_root") != HISTORICAL_RESULT_ROOT
            or failed.get("retry_forbidden") is not True
        ):
            errors.append("historical_failed_task_binding_drift")

    authority = manifest.get("route_condition_authority")
    if isinstance(source, dict) and isinstance(authority, dict):
        route = source.get("route_output")
        if not isinstance(route, dict):
            errors.append("route_output_missing")
        else:
            derived = {
                "stop_conditions": route.get("stop_conditions"),
                "pivot_conditions": route.get("pivot_conditions"),
            }
            if authority.get("condition_fields") != CONDITION_FIELDS:
                errors.append("route_condition_authority_fields_invalid")
            if authority.get("canonical_sha256") != _canonical_sha256(derived):
                errors.append("route_condition_authority_sha256_mismatch")
            if authority.get("stop_condition_count") != len(derived["stop_conditions"] or []):
                errors.append("route_stop_condition_count_mismatch")
            if authority.get("pivot_condition_count") != len(derived["pivot_conditions"] or []):
                errors.append("route_pivot_condition_count_mismatch")
    else:
        errors.append("route_condition_authority_invalid")

    base_ref = manifest.get("base_contract")
    if isinstance(replacement_contract, dict):
        embedded = replacement_contract.get("x-base-contract-binding")
        if not isinstance(base_ref, dict) or not isinstance(embedded, dict):
            errors.append("base_contract_binding_invalid")
        else:
            for field in ("path", "git_blob_oid", "raw_sha256", "canonical_sha256"):
                if base_ref.get(field) != embedded.get(field):
                    errors.append(f"base_contract_{field}_mismatch")
        if replacement_contract.get("x-authority-inheritance", {}).get(
            "condition_fields"
        ) != CONDITION_FIELDS:
            errors.append("replacement_contract_authority_fields_invalid")
        expected_ref = "../forward-inputs-r5/m3-model-output-contract.schema.json"
        refs = replacement_contract.get("allOf")
        if not isinstance(refs, list) or refs != [{"$ref": expected_ref}]:
            errors.append("replacement_contract_base_ref_invalid")
    if base_contract is None:
        errors.append("base_contract_unavailable")

    if manifest.get("m2_validation", {}).get("required_status") != "valid":
        errors.append("m2_validation_required_status_invalid")
    if not isinstance(m2_validation, dict) or m2_validation.get("status") != "valid":
        errors.append("m2_validation_status_invalid")
    if manifest.get("eligibility", {}).get("required_status") != "eligible":
        errors.append("eligibility_required_status_invalid")
    if not isinstance(eligibility, dict) or eligibility.get("status") != "eligible":
        errors.append("eligibility_status_invalid")

    policy_ref = manifest.get("supersession_policy")
    if isinstance(erratum, dict) and isinstance(policy_ref, dict):
        policy = erratum.get("supersession_policy", {})
        for field in (
            "policy",
            "same_task_retry_forbidden",
            "same_output_path_retry_forbidden",
            "cross_revision_aggregate_requires_hash_bound_cross_validation",
        ):
            if policy_ref.get(field) != policy.get(field):
                errors.append(f"supersession_policy_{field}_mismatch")
        if (
            erratum.get("evidence_head") != EVIDENCE_HEAD
            or policy.get("replacement_case") != CASE_ID
            or policy.get("replacement_revision") != REVISION
            or policy.get("replacement_result_root")
            != "evals/m3/results/forward-r5.1-f02"
            or policy.get("new_fresh_run_authorized") is not False
        ):
            errors.append("supersession_policy_state_drift")

    historical = manifest.get("historical_failed_task")
    if not isinstance(historical, dict) or (
        historical.get("task_id") != HISTORICAL_TASK_ID
        or historical.get("result_root") != HISTORICAL_RESULT_ROOT
        or historical.get("retry_count") != 0
        or historical.get("retry_forbidden") is not True
    ):
        errors.append("historical_failed_task_state_drift")

    counters = _check_counters(manifest.get("counters"), errors)
    artifact_count = _check_result_root(manifest, errors)
    errors.extend(validate_future_paths(CASE_ID, manifest.get("future_paths"), RESULT_ROOT))

    if isinstance(preparation, dict):
        preparation_result = audit_preparation(REPO_ROOT / EXPECTED_PATHS["preparation_manifest"])
        if preparation_result.get("status") != "ready_for_fresh_authorization":
            errors.append("preparation_audit_not_ready")
    if not _r5_evidence_tree_clean():
        errors.append("immutable_r5_evidence_changed")

    return {
        "status": "ready_for_fresh_authorization" if not errors else "invalid",
        "case_id": manifest.get("case_id"),
        "revision": manifest.get("revision"),
        "preparation_baseline_head": manifest.get("preparation_baseline_head"),
        "historical_evidence_head": manifest.get("historical_evidence_head"),
        "new_fresh_run_authorized": manifest.get("new_fresh_run_authorized"),
        "reserved_task_id": manifest.get("reserved_task_id"),
        "counters": counters,
        "result_artifact_count": artifact_count,
        "historical_f02_retry_count": historical.get("retry_count")
        if isinstance(historical, dict)
        else None,
        "side_effects": [],
        "errors": sorted(set(errors)),
        "evidence_gaps": [],
        "does_not_prove": [
            "Authorization readiness does not authorize or launch a fresh task.",
            "No final is consumed, no F02 result is accepted, and no cross-revision aggregate is created.",
            "M3 remains in progress and M4 remains not started.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) > 1:
        return 2
    path = (
        Path(arguments[0])
        if arguments
        else REPO_ROOT
        / "evals"
        / "m3"
        / "forward-inputs-r5.1-f02"
        / "authorization-manifest.json"
    )
    result = audit_authorization(path)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0 if result["status"] == "ready_for_fresh_authorization" else 1


if __name__ == "__main__":
    raise SystemExit(main())
