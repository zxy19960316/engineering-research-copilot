#!/usr/bin/env python3
"""Audit the frozen r5.1-f02 replacement preparation without consuming it."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from r5_dispatch_contract import COUNTER_KEYS, validate_future_paths


REPO_ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_HEAD = "1b696bce53ee0a11163bfe4f91a9a49ab3af6f49"
SCHEMA_VERSION = "m3.1-forward-replacement-r5.1-f02-v1"
REVISION = "r5.1-f02"
CASE_ID = "m3-f02"
RESULT_ROOT = REPO_ROOT / "evals" / "m3" / "results" / "forward-r5.1-f02"
R5_RESULT_RELATIVE = "evals/m3/results/forward-r5"
HISTORICAL_TASK_ID = "019fd687-5575-7143-8cf3-1ab3069611f5"
CONDITION_FIELDS = ["criterion_type", "metric_id", "operator", "value", "unit"]


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


def _load_json(path: Path, code: str, errors: list[str]) -> dict[str, Any] | None:
    try:
        raw = path.read_bytes()
        if raw.startswith(b"\xef\xbb\xbf"):
            raise ValueError("utf8_bom_forbidden")
        value = json.loads(raw.decode("utf-8", errors="strict"))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        errors.append(f"{code}_invalid_json")
        return None
    if not isinstance(value, dict):
        errors.append(f"{code}_object_required")
        return None
    return value


def _safe_file(relative: object, code: str, errors: list[str]) -> Path | None:
    if not isinstance(relative, str) or not relative:
        errors.append(f"{code}_path_invalid")
        return None
    candidate = (REPO_ROOT / relative).resolve()
    try:
        candidate.relative_to(REPO_ROOT.resolve())
    except ValueError:
        errors.append(f"{code}_outside_repository")
        return None
    if not candidate.is_file() or candidate.is_symlink():
        errors.append(f"{code}_missing")
        return None
    return candidate


def _bound_json(
    reference: object,
    code: str,
    errors: list[str],
) -> tuple[Path | None, dict[str, Any] | None]:
    if not isinstance(reference, dict):
        errors.append(f"{code}_reference_invalid")
        return None, None
    path = _safe_file(reference.get("path"), code, errors)
    if path is None:
        return None, None
    try:
        raw = path.read_bytes()
    except OSError:
        errors.append(f"{code}_unreadable")
        return None, None
    if reference.get("raw_sha256") != _sha256(raw):
        errors.append(f"{code}_sha256_mismatch")
    return path, _load_json(path, code, errors)


def _bound_file(reference: object, code: str, errors: list[str]) -> Path | None:
    if not isinstance(reference, dict):
        errors.append(f"{code}_reference_invalid")
        return None
    path = _safe_file(reference.get("path"), code, errors)
    if path is None:
        return None
    try:
        raw = path.read_bytes()
    except OSError:
        errors.append(f"{code}_unreadable")
        return None
    if reference.get("raw_sha256") != _sha256(raw):
        errors.append(f"{code}_sha256_mismatch")
    return path


def _git_blob(relative: object, errors: list[str]) -> tuple[str, bytes] | None:
    if not isinstance(relative, str) or not relative.startswith("evals/"):
        errors.append("historical_blob_path_invalid")
        return None
    try:
        head = subprocess.run(
            ["git", "cat-file", "-e", f"{EVIDENCE_HEAD}^{{commit}}"],
            cwd=REPO_ROOT,
            capture_output=True,
            check=False,
        )
        if head.returncode != 0:
            errors.append("historical_evidence_head_unavailable")
            return None
        raw = subprocess.run(
            ["git", "show", f"{EVIDENCE_HEAD}:{relative}"],
            cwd=REPO_ROOT,
            capture_output=True,
            check=False,
        )
        oid = subprocess.run(
            ["git", "rev-parse", f"{EVIDENCE_HEAD}:{relative}"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
    except OSError:
        errors.append("historical_evidence_head_unavailable")
        return None
    if raw.returncode != 0 or oid.returncode != 0:
        errors.append(f"historical_blob_missing:{relative}")
        return None
    return oid.stdout.strip(), raw.stdout


def _verify_historical_identity(reference: object, errors: list[str]) -> None:
    if (
        not isinstance(reference, list)
        or len(reference) != 3
        or not all(isinstance(item, str) and item for item in reference)
    ):
        errors.append("historical_identity_invalid")
        return
    relative, expected_oid, expected_sha256 = reference
    actual = _git_blob(relative, errors)
    if actual is None:
        return
    oid, raw = actual
    if oid != expected_oid:
        errors.append(f"historical_blob_oid_mismatch:{relative}")
    if _sha256(raw) != expected_sha256:
        errors.append(f"historical_blob_sha256_mismatch:{relative}")


def _r5_evidence_tree_clean() -> bool:
    try:
        result = subprocess.run(
            ["git", "diff", "--quiet", EVIDENCE_HEAD, "--", R5_RESULT_RELATIVE],
            cwd=REPO_ROOT,
            check=False,
        )
    except OSError:
        return False
    return result.returncode == 0


def _check_zero_counters(value: object, errors: list[str]) -> dict[str, int]:
    counters = value if isinstance(value, dict) else {}
    if set(counters) != set(COUNTER_KEYS):
        errors.append("manifest_counter_keys_invalid")
    result: dict[str, int] = {}
    for key in COUNTER_KEYS:
        raw = counters.get(key)
        result[key] = raw if isinstance(raw, int) and not isinstance(raw, bool) else -1
        if raw != 0:
            errors.append(f"manifest_counter_nonzero:{key}")
    return result


def _check_result_root(manifest: dict[str, Any], errors: list[str]) -> int:
    try:
        declared = (REPO_ROOT / manifest.get("result_root", "")).resolve()
    except (AttributeError, TypeError, ValueError):
        declared = None
    if declared != RESULT_ROOT.resolve():
        errors.append("result_root_not_canonical")
    if not RESULT_ROOT.is_dir() or RESULT_ROOT.is_symlink():
        errors.append("result_root_missing")
        return 0
    entries = list(RESULT_ROOT.iterdir())
    marker = RESULT_ROOT / ".gitkeep"
    if not marker.is_file() or marker.is_symlink() or marker.read_bytes() != b"":
        errors.append("result_root_marker_invalid")
    artifacts = [path for path in entries if path.name != ".gitkeep"]
    if artifacts:
        errors.append("result_root_not_empty")
    return len(artifacts)


def _check_input_binding(value: dict[str, Any], errors: list[str]) -> None:
    if value.get("schema_version") != "m3.1-forward-r5.1-f02-input-binding-v1":
        errors.append("input_binding_schema_invalid")
    if value.get("revision") != REVISION or value.get("case_id") != CASE_ID:
        errors.append("input_binding_identity_invalid")
    if value.get("historical_evidence_head") != EVIDENCE_HEAD:
        errors.append("input_binding_evidence_head_drift")

    source_ref = value.get("source_input")
    if not isinstance(source_ref, dict):
        errors.append("source_input_binding_invalid")
        return
    source_path = _safe_file(source_ref.get("path"), "source_input", errors)
    if source_path is None:
        return
    source = _load_json(source_path, "source_input", errors)
    if source is None:
        return
    raw = source_path.read_bytes()
    if source_ref.get("raw_sha256") != _sha256(raw):
        errors.append("source_input_raw_sha256_mismatch")
    if source_ref.get("canonical_sha256") != _canonical_sha256(source):
        errors.append("source_input_canonical_sha256_mismatch")
    historical = _git_blob(source_ref.get("path"), errors)
    if historical is not None and source_ref.get("git_blob_oid") != historical[0]:
        errors.append("source_input_git_blob_oid_mismatch")

    route = source.get("route_output")
    authority_ref = value.get("route_condition_authority")
    if not isinstance(route, dict) or not isinstance(authority_ref, dict):
        errors.append("route_condition_authority_invalid")
    else:
        authority = {
            "stop_conditions": route.get("stop_conditions"),
            "pivot_conditions": route.get("pivot_conditions"),
        }
        if authority_ref.get("source_pointer") != "route_output":
            errors.append("route_condition_authority_pointer_invalid")
        if authority_ref.get("condition_fields") != CONDITION_FIELDS:
            errors.append("route_condition_authority_fields_invalid")
        if authority_ref.get("stop_condition_count") != len(authority["stop_conditions"] or []):
            errors.append("route_stop_condition_count_mismatch")
        if authority_ref.get("pivot_condition_count") != len(authority["pivot_conditions"] or []):
            errors.append("route_pivot_condition_count_mismatch")
        if authority_ref.get("canonical_sha256") != _canonical_sha256(authority):
            errors.append("route_condition_authority_sha256_mismatch")

    for key, required_status in (("m2_validation", "valid"), ("eligibility", "eligible")):
        _, receipt = _bound_json(value.get(key), key, errors)
        reference = value.get(key)
        if isinstance(reference, dict) and reference.get("required_status") != required_status:
            errors.append(f"{key}_required_status_invalid")
        if receipt is not None and receipt.get("status") != required_status:
            errors.append(f"{key}_status_invalid")

    failed = value.get("historical_failed_task")
    if not isinstance(failed, dict):
        errors.append("historical_failed_task_invalid")
    else:
        if failed.get("task_id") != HISTORICAL_TASK_ID:
            errors.append("historical_failed_task_id_drift")
        if failed.get("result_root") != R5_RESULT_RELATIVE:
            errors.append("historical_failed_result_root_drift")
        if failed.get("retry_forbidden") is not True:
            errors.append("historical_retry_must_be_forbidden")
        transaction = _git_blob(failed.get("transaction_path"), errors)
        if transaction is not None:
            if failed.get("transaction_git_blob_oid") != transaction[0]:
                errors.append("historical_transaction_oid_mismatch")
            try:
                transaction_value = json.loads(transaction[1])
            except (UnicodeError, json.JSONDecodeError):
                transaction_value = {}
            if transaction_value.get("task_id") != HISTORICAL_TASK_ID:
                errors.append("historical_transaction_task_id_drift")


def audit_preparation(manifest_path: str | Path) -> dict[str, Any]:
    errors: list[str] = []
    manifest = _load_json(Path(manifest_path), "manifest", errors)
    if manifest is None:
        return {
            "status": "invalid",
            "case_id": CASE_ID,
            "revision": REVISION,
            "new_fresh_run_authorized": False,
            "result_artifact_count": 0,
            "counters": {key: 0 for key in COUNTER_KEYS},
            "errors": sorted(set(errors)),
            "evidence_gaps": [],
        }

    if manifest.get("schema_version") != SCHEMA_VERSION:
        errors.append("manifest_schema_invalid")
    if manifest.get("status") != "prepared_awaiting_fresh_authorization":
        errors.append("manifest_status_invalid")
    if manifest.get("revision") != REVISION or manifest.get("case_id") != CASE_ID:
        errors.append("manifest_identity_invalid")
    if manifest.get("m3_status") != "IN_PROGRESS" or manifest.get("m4_status") != "NOT_STARTED":
        errors.append("milestone_status_drift")
    if manifest.get("historical_evidence_head") != EVIDENCE_HEAD:
        errors.append("manifest_evidence_head_drift")
    if manifest.get("preparation_authorized") is not True:
        errors.append("preparation_authorization_missing")
    if manifest.get("new_fresh_run_authorized") is not False:
        errors.append("fresh_run_authorization_must_be_false")
    if manifest.get("historical_failed_task_id") != HISTORICAL_TASK_ID:
        errors.append("historical_failed_task_id_drift")
    if manifest.get("reserved_task_id") is not None:
        errors.append("reserved_task_id_forbidden_before_authorization")
        if manifest.get("reserved_task_id") == HISTORICAL_TASK_ID:
            errors.append("historical_task_id_reuse_forbidden")

    counters = _check_zero_counters(manifest.get("counters"), errors)
    artifact_count = _check_result_root(manifest, errors)
    errors.extend(validate_future_paths(CASE_ID, manifest.get("future_paths"), RESULT_ROOT))

    _, binding = _bound_json(manifest.get("input_binding"), "input_binding", errors)
    if binding is not None:
        _check_input_binding(binding, errors)
    _bound_file(manifest.get("prompt"), "prompt", errors)
    _, contract = _bound_json(manifest.get("contract"), "contract", errors)
    if not isinstance(contract, dict) or contract.get("x-authority-inheritance", {}).get("condition_fields") != CONDITION_FIELDS:
        errors.append("contract_authority_binding_invalid")

    _, policy = _bound_json(manifest.get("supersession_policy"), "supersession_policy", errors)
    policy_ref = manifest.get("supersession_policy")
    expected_reused: dict[str, Any] = {}
    if isinstance(policy, dict):
        if policy.get("evidence_head") != EVIDENCE_HEAD:
            errors.append("supersession_policy_evidence_head_drift")
        frozen = policy.get("supersession_policy", {})
        if (
            frozen.get("policy") != "replace_f02_only"
            or frozen.get("replacement_case") != CASE_ID
            or frozen.get("replacement_revision") != REVISION
            or frozen.get("replacement_result_root")
            != "evals/m3/results/forward-r5.1-f02"
            or frozen.get("new_fresh_run_authorized") is not False
        ):
            errors.append("supersession_policy_drift")
        expected_reused = policy.get("accepted_fresh_cases", {})
    if isinstance(policy_ref, dict):
        for key in (
            "same_task_retry_forbidden",
            "same_output_path_retry_forbidden",
            "cross_revision_aggregate_requires_hash_bound_cross_validation",
        ):
            if policy_ref.get(key) is not True:
                errors.append(f"supersession_{key}_missing")

    reused = manifest.get("reused_accepted_cases")
    if not isinstance(reused, list) or [item.get("case_id") for item in reused if isinstance(item, dict)] != [
        "m3-f01",
        "m3-f03",
        "m3-f04",
        "m3-f05",
    ]:
        errors.append("reused_accepted_cases_invalid")
    else:
        for item in reused:
            case_id = item["case_id"]
            expected = expected_reused.get(case_id)
            actual = {key: value for key, value in item.items() if key != "case_id"}
            if actual != expected:
                errors.append(f"reused_case_identity_drift:{case_id}")
            for reference in actual.values():
                _verify_historical_identity(reference, errors)

    if not _r5_evidence_tree_clean():
        errors.append("immutable_r5_evidence_changed")

    return {
        "status": "ready_for_fresh_authorization" if not errors else "invalid",
        "case_id": manifest.get("case_id"),
        "revision": manifest.get("revision"),
        "new_fresh_run_authorized": manifest.get("new_fresh_run_authorized"),
        "result_artifact_count": artifact_count,
        "counters": counters,
        "reused_accepted_case_ids": [
            item.get("case_id") for item in reused if isinstance(item, dict)
        ] if isinstance(reused, list) else [],
        "errors": sorted(set(errors)),
        "evidence_gaps": [],
        "does_not_prove": [
            "Preparation readiness is not authorization to launch the fresh F02 task.",
            "No historical F02 retry, cross-revision acceptance, M3 closure, or M4 work is established.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) > 1:
        return 2
    path = (
        Path(arguments[0])
        if arguments
        else REPO_ROOT / "evals" / "m3" / "forward-inputs-r5.1-f02" / "manifest.json"
    )
    result = audit_preparation(path)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0 if result["status"] == "ready_for_fresh_authorization" else 1


if __name__ == "__main__":
    raise SystemExit(main())
