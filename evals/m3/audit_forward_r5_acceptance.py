#!/usr/bin/env python3
"""Cross-validate immutable r5 task records and every linked artifact."""

from __future__ import annotations

import hashlib
import json
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
M3_SCRIPT_ROOT = REPO_ROOT / "skills" / "engineering-research-copilot" / "scripts"
sys.path.insert(0, str(M3_SCRIPT_ROOT))

from validate_m3_method_bundle import validate_m3_bundle  # noqa: E402

from r5_dispatch_contract import (  # noqa: E402
    CASE_IDS,
    COMPOSER_CASE_IDS,
    COUNTER_KEYS,
    R5_SCHEMA_VERSION,
    derive_counters,
    validate_case_record,
    validate_case_records,
    validate_future_path_sets,
)
from validate_m3_forward_outcome import validate_forward_outcome  # noqa: E402


R5_RESULT_ROOT = REPO_ROOT / "evals" / "m3" / "results" / "forward-r5"
R5_EVIDENCE_HEAD = "1b696bce53ee0a11163bfe4f91a9a49ab3af6f49"
R4_MANIFEST_RELATIVE = "evals/m3/results/forward-r4/acceptance-manifest.json"
PROCESSED_STATES = {"processed_accepted", "processed_invalid"}
RECORD_CONTEXT_KEYS = {
    "case_id",
    "task_id",
    "state",
    "task_finalizations_observed",
    "dispatcher_cases_preflighted",
    "dispatcher_cases_processed",
    "composer_invocations",
    "validator_invocations",
    "accepted",
    "transaction_failures",
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


def _canonical_sha256(value: Any) -> str | None:
    try:
        return _sha256(_canonical_bytes(value))
    except (TypeError, ValueError):
        return None


def _json_equal(left: Any, right: Any) -> bool:
    try:
        return _canonical_bytes(left) == _canonical_bytes(right)
    except (TypeError, ValueError):
        return False


def _safe_file(raw_path: Any, code: str, errors: list[str]) -> Path | None:
    if not isinstance(raw_path, str) or not raw_path:
        errors.append(f"{code}_missing")
        return None
    candidate = Path(raw_path)
    resolved = (candidate if candidate.is_absolute() else REPO_ROOT / candidate).resolve()
    try:
        resolved.relative_to(REPO_ROOT.resolve())
    except ValueError:
        errors.append(f"{code}_outside_repository")
        return None
    if not resolved.exists():
        errors.append(f"{code}_missing")
        return None
    current = resolved
    while True:
        try:
            attributes = getattr(current.stat(), "st_file_attributes", 0)
        except OSError:
            errors.append(f"{code}_unreadable")
            return None
        if current.is_symlink() or attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            errors.append(f"{code}_reparse_point_forbidden")
            return None
        if current == REPO_ROOT.resolve():
            break
        if current.parent == current:
            errors.append(f"{code}_outside_repository")
            return None
        current = current.parent
    if not resolved.is_file():
        errors.append(f"{code}_not_file")
        return None
    return resolved


def _evidence_blob(path: Path) -> bytes | None:
    try:
        relative = path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
        if not relative.startswith("evals/"):
            return None
        completed = subprocess.run(
            ["git", "show", f"{R5_EVIDENCE_HEAD}:{relative}"],
            cwd=REPO_ROOT,
            capture_output=True,
            check=False,
        )
    except (OSError, ValueError):
        return None
    return completed.stdout if completed.returncode == 0 else None


def _parse_json(raw: bytes) -> Any:
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ValueError("utf8_bom_forbidden")
    return json.loads(raw.decode("utf-8", errors="strict"))


def _read_artifact(
    path: Path,
    code: str,
    errors: list[str],
    *,
    json_required: bool,
) -> dict[str, Any] | None:
    try:
        worktree_raw = path.read_bytes()
    except OSError:
        errors.append(f"{code}_unreadable")
        return None
    identity_raw = _evidence_blob(path) or worktree_raw
    value: Any = None
    if json_required:
        try:
            value = _parse_json(worktree_raw)
            identity_value = _parse_json(identity_raw)
        except (UnicodeError, json.JSONDecodeError, ValueError):
            errors.append(f"{code}_invalid_json")
            return None
        if not isinstance(value, dict) or not isinstance(identity_value, dict):
            errors.append(f"{code}_object_required")
            return None
        if not _json_equal(value, identity_value):
            errors.append(f"{code}_worktree_content_mismatch")
    else:
        normalized = worktree_raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        identity_normalized = identity_raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        if normalized != identity_normalized:
            errors.append(f"{code}_worktree_content_mismatch")
        value = worktree_raw
    return {
        "value": value,
        "sha256": _sha256(identity_raw),
        "byte_length": len(identity_raw),
        "canonical_sha256": _canonical_sha256(value) if json_required else None,
    }


def _declared_hash(
    artifact: dict[str, Any] | None,
    expected: Any,
    code: str,
    errors: list[str],
) -> None:
    if artifact is None:
        return
    if not isinstance(expected, str) or len(expected) != 64 or artifact["sha256"] != expected:
        errors.append(f"{code}_sha256_mismatch")


def _path_for(result_root: Path, future_paths: dict[str, Any], key: str) -> Path | None:
    raw = future_paths.get(key)
    if not isinstance(raw, str):
        return None
    return (result_root / raw).resolve()


def _read_future(
    case_id: str,
    key: str,
    future_paths: dict[str, Any],
    result_root: Path,
    errors: list[str],
) -> dict[str, Any] | None:
    path = _path_for(result_root, future_paths, key)
    if path is None or not path.is_file():
        errors.append(f"artifact_missing:{case_id}:{key}")
        return None
    return _read_artifact(path, f"artifact_invalid:{case_id}:{key}", errors, json_required=True)


def _required_keys(record: dict[str, Any]) -> set[str]:
    required: set[str] = set()
    if record["task_finalizations_observed"] == 1:
        required.add("model_final_json")
    if record["state"] in {"processing_failed", *PROCESSED_STATES}:
        required.update({"context_finalization_json", "case_transaction_json"})
    if record["state"] in PROCESSED_STATES:
        required.update({"outcome_json", "validation_json", "validator_receipt_json"})
        if record["case_id"] in COMPOSER_CASE_IDS:
            required.update(
                {"payload_json", "composed_bundle_json", "composer_invocation_receipt_json"}
            )
    elif record["state"] == "processing_failed":
        if record["composer_invocations"] == 1:
            required.add("composer_invocation_receipt_json")
        if record["validator_invocations"] == 1:
            required.add("validator_receipt_json")
    return required


def _audit_historical_r4(value: object, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append("historical_r4_reference_invalid")
        return {"status": "invalid", "count_as_r5": False}
    if value.get("path") != R4_MANIFEST_RELATIVE:
        errors.append("historical_r4_path_invalid")
    if value.get("count_as_r5") is not False:
        errors.append("historical_r4_counting_forbidden")
    path = _safe_file(value.get("path"), "historical_r4_manifest", errors)
    if path is not None:
        artifact = _read_artifact(path, "historical_r4_manifest", errors, json_required=True)
        _declared_hash(artifact, value.get("raw_sha256"), "historical_r4_manifest", errors)
        historical = artifact["value"] if artifact is not None else None
        if not isinstance(historical, dict) or historical.get("status") != "blocked_not_accepted":
            errors.append("historical_r4_not_blocked")
    return {
        "path": value.get("path"),
        "raw_sha256": value.get("raw_sha256"),
        "status": value.get("status"),
        "count_as_r5": value.get("count_as_r5"),
    }


def _cross_case(
    item: dict[str, Any],
    result_root: Path,
    run: dict[str, Any],
) -> dict[str, Any]:
    case_id = item.get("case_id")
    errors: list[str] = []
    record = item.get("record")
    record_errors = validate_case_record(record)
    errors.extend(record_errors)
    if not isinstance(record, dict):
        return {"case_id": case_id, "record_state": "invalid", "errors": sorted(set(errors))}
    future_paths = item.get("future_paths")
    if not isinstance(future_paths, dict):
        errors.append(f"future_paths_invalid:{case_id}")
        future_paths = {}

    task_ids = run.get("task_ids") if isinstance(run.get("task_ids"), dict) else {}
    finalization_ids = (
        run.get("finalization_turn_ids")
        if isinstance(run.get("finalization_turn_ids"), dict)
        else {}
    )
    if not (
        record.get("task_id")
        == item.get("fresh_context_thread_id")
        == task_ids.get(case_id)
    ):
        errors.append(f"task_id_binding_mismatch:{case_id}")
    if item.get("finalization_turn_id") != finalization_ids.get(case_id):
        errors.append(f"finalization_id_binding_mismatch:{case_id}")

    source_path = _safe_file(item.get("input_path"), f"source:{case_id}", errors)
    source = (
        _read_artifact(source_path, f"source:{case_id}", errors, json_required=True)
        if source_path is not None
        else None
    )
    _declared_hash(source, item.get("input_raw_sha256"), f"source:{case_id}", errors)
    if source is not None and source["canonical_sha256"] != item.get("input_canonical_sha256"):
        errors.append(f"source_canonical_sha256_mismatch:{case_id}")

    prompt_path = _safe_file(item.get("prompt_path"), f"prompt:{case_id}", errors)
    prompt = (
        _read_artifact(prompt_path, f"prompt:{case_id}", errors, json_required=False)
        if prompt_path is not None
        else None
    )
    _declared_hash(prompt, item.get("prompt_raw_sha256"), f"prompt:{case_id}", errors)

    contract_path = _safe_file(item.get("contract_path"), f"contract:{case_id}", errors)
    contract = (
        _read_artifact(contract_path, f"contract:{case_id}", errors, json_required=True)
        if contract_path is not None
        else None
    )
    _declared_hash(contract, item.get("contract_raw_sha256"), f"contract:{case_id}", errors)

    required = _required_keys(record)
    artifacts: dict[str, dict[str, Any] | None] = {}
    for key in sorted(required):
        artifacts[key] = _read_future(case_id, key, future_paths, result_root, errors)
    declared_artifact_hashes = item.get("artifact_sha256")
    if isinstance(declared_artifact_hashes, dict):
        for key, expected in declared_artifact_hashes.items():
            artifact = artifacts.get(key)
            if artifact is not None and artifact["sha256"] != expected:
                errors.append(f"artifact_sha256_mismatch:{case_id}:{key}")

    model = artifacts.get("model_final_json")
    context = artifacts.get("context_finalization_json")
    transaction = artifacts.get("case_transaction_json")
    if transaction is not None and not _json_equal(transaction["value"], record):
        errors.append(f"transaction_record_mismatch:{case_id}")
    if context is not None:
        context_value = context["value"]
        for key in RECORD_CONTEXT_KEYS:
            if not _json_equal(context_value.get(key), record.get(key)):
                errors.append(f"context_record_mismatch:{case_id}:{key}")
        if model is not None:
            if context_value.get("final_raw_sha256") != model["sha256"]:
                errors.append(f"model_final_sha256_mismatch:{case_id}")
            if context_value.get("final_byte_length") != model["byte_length"]:
                errors.append(f"model_final_byte_length_mismatch:{case_id}")

    composer_receipt = artifacts.get("composer_invocation_receipt_json")
    if composer_receipt is not None:
        receipt = composer_receipt["value"]
        if receipt.get("case_id") != case_id:
            errors.append(f"composer_receipt_case_mismatch:{case_id}")
        if receipt.get("composer_invocation_count") != record.get("composer_invocations"):
            errors.append(f"composer_count_mismatch:{case_id}")
        expected_status = "invoked" if record.get("state") in PROCESSED_STATES else "failed"
        if receipt.get("status") != expected_status:
            errors.append(f"composer_receipt_status_mismatch:{case_id}")

    validator_receipt = artifacts.get("validator_receipt_json")
    if validator_receipt is not None:
        receipt = validator_receipt["value"]
        if receipt.get("case_id") != case_id:
            errors.append(f"validator_receipt_case_mismatch:{case_id}")
        if receipt.get("validator_invocation_count") != record.get("validator_invocations"):
            errors.append(f"validator_count_mismatch:{case_id}")
        expected_status = "invoked" if record.get("state") in PROCESSED_STATES else "failed"
        if receipt.get("status") != expected_status:
            errors.append(f"validator_receipt_status_mismatch:{case_id}")

    bundle = artifacts.get("composed_bundle_json")
    payload = artifacts.get("payload_json")
    if record.get("state") in PROCESSED_STATES and case_id in COMPOSER_CASE_IDS:
        if model is not None and payload is not None and not _json_equal(model["value"], payload["value"]):
            errors.append(f"payload_model_final_mismatch:{case_id}")
        if bundle is not None and source is not None:
            bundle_value = bundle["value"]
            if not _json_equal(bundle_value.get("source_m2_bundle"), source["value"]):
                errors.append(f"composed_source_mismatch:{case_id}")
            if bundle_value.get("source_m2_bundle_hash") != source["canonical_sha256"]:
                errors.append(f"composed_source_hash_mismatch:{case_id}")
            if model is not None:
                for key in ("coaching_mode", "method_cards", "domain_overlays"):
                    if not _json_equal(bundle_value.get(key), model["value"].get(key)):
                        errors.append(f"composed_payload_mismatch:{case_id}:{key}")

    validation = artifacts.get("validation_json")
    outcome = artifacts.get("outcome_json")
    if record.get("state") in PROCESSED_STATES and validation is not None:
        validation_value = validation["value"]
        if case_id == "m3-f03":
            replayed_outcome = validate_forward_outcome(
                case_id,
                source["value"] if source is not None else None,
                outcome["value"] if outcome is not None else None,
            )
            expected_validation = {
                **replayed_outcome,
                "accepted": replayed_outcome.get("status") == "accepted_expected_block",
            }
            if model is not None and outcome is not None and not _json_equal(
                model["value"], outcome["value"]
            ):
                errors.append(f"outcome_model_final_mismatch:{case_id}")
        else:
            validated = validate_m3_bundle(bundle["value"] if bundle is not None else None)
            expected_validation = {
                **validated,
                "accepted": validated.get("status") == "valid",
            }
            if outcome is not None:
                outcome_value = outcome["value"]
                if outcome_value.get("case_id") != case_id:
                    errors.append(f"outcome_case_mismatch:{case_id}")
                if outcome_value.get("accepted") != record.get("accepted"):
                    errors.append(f"outcome_accepted_mismatch:{case_id}")
                if outcome_value.get("validation_status") != validation_value.get("status"):
                    errors.append(f"outcome_validation_status_mismatch:{case_id}")
        if not _json_equal(validation_value, expected_validation):
            errors.append(f"validation_replay_mismatch:{case_id}")
        if validation_value.get("accepted") != record.get("accepted"):
            errors.append(f"validation_accepted_mismatch:{case_id}")
        if context is not None and context["value"].get("validation_status") != validation_value.get(
            "status"
        ):
            errors.append(f"context_validation_status_mismatch:{case_id}")

    return {
        "case_id": case_id,
        "record_state": record.get("state"),
        "task_id": record.get("task_id"),
        "finalization_id": item.get("finalization_turn_id"),
        "source_sha256": source.get("sha256") if source is not None else None,
        "prompt_sha256": prompt.get("sha256") if prompt is not None else None,
        "contract_sha256": contract.get("sha256") if contract is not None else None,
        "model_final_sha256": model.get("sha256") if model is not None else None,
        "composed_bundle_sha256": bundle.get("sha256") if bundle is not None else None,
        "errors": sorted(set(errors)),
    }


def audit_acceptance_manifest(manifest_path: str | Path) -> dict[str, Any]:
    errors: list[str] = []
    manifest_file = Path(manifest_path)
    try:
        manifest = _parse_json(manifest_file.read_bytes())
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        manifest = None
    if not isinstance(manifest, dict):
        return {
            "status": "invalid",
            "cases": [],
            "counters": {key: 0 for key in COUNTER_KEYS},
            "errors": ["invalid_manifest_json"],
            "evidence_gaps": [],
            "m3_status": "IN_PROGRESS",
            "later_gates": "NOT_RUN",
        }
    if manifest.get("schema_version") != R5_SCHEMA_VERSION:
        errors.append("manifest_schema_version_invalid")
    if "fresh_contexts_consumed" in manifest:
        errors.append("legacy_fresh_context_counter_forbidden")

    expected_root = R5_RESULT_ROOT.resolve()
    declared = manifest.get("result_root")
    try:
        declared_root = (REPO_ROOT / declared).resolve()
    except (AttributeError, TypeError):
        declared_root = None
    if declared_root != expected_root:
        errors.append("result_root_not_exact")
    if not expected_root.is_dir():
        errors.append("future_result_root_missing")

    raw_cases = manifest.get("cases")
    if not isinstance(raw_cases, list) or len(raw_cases) != len(CASE_IDS):
        errors.append("manifest_cases_invalid")
        raw_cases = []
    case_by_id: dict[str, dict[str, Any]] = {}
    for item in raw_cases:
        if not isinstance(item, dict):
            errors.append("case_entry_object_required")
            continue
        case_id = item.get("case_id")
        if case_id in case_by_id:
            errors.append(f"case_id_duplicate:{case_id}")
        case_by_id[case_id] = item
    if set(case_by_id) != set(CASE_IDS):
        errors.append("manifest_case_ids_invalid")

    records = [case_by_id.get(case_id, {}).get("record") for case_id in CASE_IDS]
    path_maps = {
        case_id: case_by_id.get(case_id, {}).get("future_paths") for case_id in CASE_IDS
    }
    errors.extend(validate_case_records(records))
    errors.extend(validate_future_path_sets(path_maps, expected_root, check_existing=False))
    run = manifest.get("run") if isinstance(manifest.get("run"), dict) else {}
    top_contract = manifest.get("contract")
    if not isinstance(top_contract, dict):
        errors.append("manifest_contract_invalid")
        top_contract = {}
    else:
        top_contract_path = _safe_file(
            top_contract.get("path"), "manifest_contract", errors
        )
        top_contract_artifact = (
            _read_artifact(
                top_contract_path,
                "manifest_contract",
                errors,
                json_required=True,
            )
            if top_contract_path is not None
            else None
        )
        _declared_hash(
            top_contract_artifact,
            top_contract.get("raw_sha256"),
            "manifest_contract",
            errors,
        )
    for case_id in CASE_IDS:
        item = case_by_id.get(case_id)
        if item is not None and (
            item.get("contract_path") != top_contract.get("path")
            or item.get("contract_raw_sha256") != top_contract.get("raw_sha256")
        ):
            errors.append(f"case_contract_binding_mismatch:{case_id}")
    case_results = [
        _cross_case(case_by_id[case_id], expected_root, run)
        for case_id in CASE_IDS
        if case_id in case_by_id
    ]
    for result in case_results:
        errors.extend(result["errors"])

    try:
        derived = derive_counters(records)
    except ValueError:
        derived = {key: 0 for key in COUNTER_KEYS}
    counters = manifest.get("counters")
    if not isinstance(counters, dict) or set(counters) != set(COUNTER_KEYS):
        errors.append("manifest_counter_keys_invalid")
        counters = {key: 0 for key in COUNTER_KEYS}
    else:
        for key in COUNTER_KEYS:
            if counters.get(key) != derived.get(key):
                errors.append(f"aggregate_counter_mismatch:{key}")

    historical_r4 = _audit_historical_r4(manifest.get("historical_r4"), errors)
    structural_errors = sorted(set(errors))
    if structural_errors:
        status = "invalid"
    else:
        acceptance_conditions = {
            "task_finalizations_observed": derived["task_finalizations_observed"] == 5,
            "dispatcher_cases_processed": derived["dispatcher_cases_processed"] == 5,
            "composer_invocations": derived["composer_invocations"] == 4,
            "validator_invocations": derived["validator_invocations"] == 5,
            "accepted_cases": derived["accepted_cases"] == 5,
            "transaction_failures": derived["transaction_failures"] == 0,
            "processed_accepted_states": all(
                isinstance(record, dict) and record.get("state") == "processed_accepted"
                for record in records
            ),
        }
        if all(acceptance_conditions.values()):
            status = "accepted"
        else:
            status = "blocked_not_accepted"
            structural_errors.append("acceptance_requirements_unmet")
    return {
        "status": status,
        "m3_status": "IN_PROGRESS",
        "later_gates": "NOT_RUN",
        "cases": case_results,
        "counters": derived,
        "historical_r4": historical_r4,
        "errors": sorted(set(structural_errors)),
        "evidence_gaps": [],
    }


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) != 1:
        return 2
    result = audit_acceptance_manifest(arguments[0])
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0 if result["status"] == "accepted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
