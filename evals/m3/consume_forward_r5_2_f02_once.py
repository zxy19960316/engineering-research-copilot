#!/usr/bin/env python3
"""Raw-first, fail-closed consumption of one authorized r5.2-f02 final."""

from __future__ import annotations

import base64
import json
import sys
from pathlib import Path
from typing import Any, Callable

from r5_2_f02_execution_contract import (
    AUTHORIZATION_PATH,
    CASE_ID,
    CONTROL_PATH,
    FUTURE_PATHS,
    INPUT_BINDING_PATH,
    LAUNCH_ATTEMPT_NAME,
    LAUNCH_RECEIPT_NAME,
    RESULT_ROOT,
    REVISION,
    canonical_bytes,
    expected_model_visible_messages_sha256,
    expected_request_envelope_sha256,
    parse_json_object,
    sha256,
    validate_launch_attempt,
    validate_launch_receipt,
    write_new_bytes,
    write_new_json,
)
from r5_2_f02_protocol import (
    parse_strict_json_object,
    validate_raw_observation,
)


SCRIPT_ROOT = Path(__file__).resolve().parents[2] / "skills" / "engineering-research-copilot" / "scripts"
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))


COUNTERS_START = {
    "tasks": 1,
    "finalizations": 1,
    "composer": 0,
    "validator": 0,
    "retry": 0,
}


def _path(root: Path, key: str) -> Path:
    return root / FUTURE_PATHS[key]


def _load_launch(result_root: Path, task_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    authorization_raw = AUTHORIZATION_PATH.read_bytes()
    control_raw = CONTROL_PATH.read_bytes()
    attempt = parse_json_object((result_root / LAUNCH_ATTEMPT_NAME).read_bytes())
    attempt_errors = validate_launch_attempt(
        attempt,
        authorization_raw=authorization_raw,
        control_raw=control_raw,
    )
    if attempt_errors:
        raise ValueError("launch_attempt_invalid")
    launch = parse_json_object((result_root / LAUNCH_RECEIPT_NAME).read_bytes())
    launch_errors = validate_launch_receipt(launch, attempt=attempt, task_id=task_id)
    if launch_errors:
        raise ValueError("launch_receipt_invalid")
    return attempt, launch


def _source_input() -> dict[str, Any]:
    binding = parse_json_object(INPUT_BINDING_PATH.read_bytes())
    reference = binding.get("source_input")
    if not isinstance(reference, dict) or not isinstance(reference.get("path"), str):
        raise ValueError("source_input_binding_invalid")
    source_path = Path(__file__).resolve().parents[2] / reference["path"]
    source = parse_json_object(source_path.read_bytes())
    if sha256(source_path.read_bytes()) != reference.get("raw_sha256"):
        raise ValueError("source_input_hash_mismatch")
    return source


def _safe_failure_code(error: Exception) -> str:
    code = getattr(error, "code", None)
    allowed = {
        "invalid_source_m2_bundle",
        "payload_contract_invalid",
        "invalid_composed_m3_bundle",
        "source_input_binding_invalid",
        "source_input_hash_mismatch",
    }
    return code if isinstance(code, str) and code in allowed else "composer_invocation_failed"


def _write_terminal(
    result_root: Path,
    *,
    launch: dict[str, Any],
    observation: dict[str, Any],
    final_raw: bytes,
    counters: dict[str, int],
    accepted: bool,
    failure_stage: str | None,
    failure_code: str | None,
    parser_record: dict[str, Any],
    composer_status: str,
    validator_status: str,
) -> dict[str, Any]:
    state = "completed" if accepted else "processing_failed"
    context = {
        "schema_version": "m3.1-r5.2-f02-context-v1",
        "revision": REVISION,
        "case_id": CASE_ID,
        "task_id": launch["fresh_task_id"],
        "model_id": launch["model_id"],
        "finalization_id": observation["finalization_id"],
        "state": state,
        "accepted": accepted,
        "counters": dict(counters),
        "raw_output_bytes": len(final_raw),
        "raw_output_sha256": sha256(final_raw),
        "request_envelope_sha256": observation["request_envelope_sha256"],
        "model_visible_messages_sha256": observation[
            "model_visible_messages_sha256"
        ],
        "failure_stage": failure_stage,
        "failure_code": failure_code,
    }
    context_path = _path(result_root, "context_finalization_json")
    write_new_json(context_path, context)
    transaction = {
        "schema_version": "m3.1-r5.2-f02-transaction-v1",
        "revision": REVISION,
        "case_id": CASE_ID,
        "task_id": launch["fresh_task_id"],
        "state": state,
        "accepted": accepted,
        "counters": dict(counters),
        "retry_count": 0,
        "retry_forbidden": True,
        "failure_stage": failure_stage,
        "failure_code": failure_code,
        "unexpected_artifacts": [],
        "side_effects": [],
    }
    transaction_path = _path(result_root, "case_transaction_json")
    write_new_json(transaction_path, transaction)
    actual_names = sorted(path.name for path in result_root.iterdir())
    terminal_name = FUTURE_PATHS["terminal_manifest_json"]
    allowlist = sorted(set(actual_names + [terminal_name]))
    terminal = {
        "schema_version": "m3.1-r5.2-f02-terminal-manifest-v1",
        "revision": REVISION,
        "case_id": CASE_ID,
        "status": "accepted" if accepted else "terminal_not_accepted",
        "accepted": accepted,
        "task_id": launch["fresh_task_id"],
        "model_id": launch["model_id"],
        "finalization_id": observation["finalization_id"],
        "counters": dict(counters),
        "raw_output": {
            "path": FUTURE_PATHS["raw_model_final"],
            "byte_length": len(final_raw),
            "raw_sha256": sha256(final_raw),
        },
        "parser": parser_record,
        "composer": {
            "status": composer_status,
            "invocation_count": counters["composer"],
        },
        "validator": {
            "status": validator_status,
            "invocation_count": counters["validator"],
        },
        "transaction": {
            "path": FUTURE_PATHS["case_transaction_json"],
            "state": state,
            "raw_sha256": sha256(transaction_path.read_bytes()),
        },
        "result_root_allowlist": allowlist,
        "unexpected_artifacts": [],
        "side_effects": [],
        "retry_allowed": False,
        "same_task_retry_forbidden": True,
        "historical_evidence": {
            "forward_r5": {
                "head": "1b696bce53ee0a11163bfe4f91a9a49ab3af6f49",
                "required_diff": "empty",
            },
            "forward_r5_1_f02": {
                "head": "fb5eec44bbf86446cf12bda2bddc76fcb07a7e69",
                "required_diff": "empty",
            },
        },
        "gate_state": {
            "gate_3": "COMPLETE" if accepted else "TERMINAL_NOT_ACCEPTED",
            "gate_4": "NOT_STARTED",
            "m3_closure": "NOT_RUN",
            "m4": "NOT_STARTED",
        },
        "does_not_prove": [
            "No cross-revision aggregate or M3 closure has run.",
            "No experiment, simulation, training, deployment, or safety validation has run.",
            "Gate 4 and M4 remain not started.",
        ],
    }
    write_new_json(_path(result_root, "terminal_manifest_json"), terminal)
    return {
        "status": terminal["status"],
        "accepted": accepted,
        "counters": dict(counters),
        "failure_stage": failure_stage,
        "failure_code": failure_code,
    }


def consume_final_once(
    authorization_path: str | Path,
    *,
    task_id: str,
    final_raw: bytes,
    observation: dict[str, Any],
    result_root: Path = RESULT_ROOT,
    compose_once: Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]],
    validate_once: Callable[[dict[str, Any]], dict[str, Any]],
) -> dict[str, Any]:
    """Preserve and consume one final; every terminal outcome forbids retry."""

    del authorization_path
    if not isinstance(final_raw, bytes):
        return {"status": "blocked", "accepted": False, "errors": ["final_bytes_required"]}
    final_path = _path(result_root, "raw_model_final")
    terminal_path = _path(result_root, "terminal_manifest_json")
    if final_path.exists() or terminal_path.exists():
        return {
            "status": "already_consumed",
            "accepted": False,
            "errors": ["second_finalization_forbidden"],
        }
    try:
        _, launch = _load_launch(result_root, task_id)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        return {"status": "blocked", "accepted": False, "errors": ["launch_binding_invalid"]}

    observation_errors = validate_raw_observation(observation, raw_bytes=final_raw)
    expected_observation = {
        "task_id": task_id,
        "model_id": launch.get("model_id"),
        "task_created_at": launch.get("task_created_at"),
        "request_envelope_sha256": expected_request_envelope_sha256(),
        "model_visible_messages_sha256": expected_model_visible_messages_sha256(),
    }
    for field, required in expected_observation.items():
        if observation.get(field) != required:
            observation_errors.append(f"raw_observation_launch_binding_mismatch:{field}")
    if observation_errors:
        return {
            "status": "blocked",
            "accepted": False,
            "errors": sorted(set(observation_errors)),
        }

    try:
        write_new_bytes(final_path, final_raw)
        write_new_json(_path(result_root, "raw_response_observation_json"), observation)
    except FileExistsError:
        return {
            "status": "already_consumed",
            "accepted": False,
            "errors": ["second_finalization_forbidden"],
        }
    except OSError:
        return {"status": "blocked", "accepted": False, "errors": ["raw_capture_failed"]}

    counters = dict(COUNTERS_START)
    counters["composer"] = 1
    parsed = parse_strict_json_object(final_raw)
    parser_record = {
        "status": "valid" if parsed.ok else "invalid",
        "classification": parsed.classification,
        "failure_code": parsed.failure_code,
        "json_error": parsed.json_error,
    }
    composer_receipt_path = _path(result_root, "composer_invocation_receipt_json")
    if not parsed.ok or parsed.value is None:
        write_new_json(
            composer_receipt_path,
            {
                "schema_version": "m3.1-r5.2-f02-composer-receipt-v1",
                "revision": REVISION,
                "case_id": CASE_ID,
                "invocation_count": 1,
                "status": "failed",
                "failure_code": parsed.failure_code,
                "classification": parsed.classification,
                "raw_output_sha256": sha256(final_raw),
            },
        )
        return _write_terminal(
            result_root,
            launch=launch,
            observation=observation,
            final_raw=final_raw,
            counters=counters,
            accepted=False,
            failure_stage="parser",
            failure_code=parsed.failure_code,
            parser_record=parser_record,
            composer_status="failed",
            validator_status="not_invoked",
        )

    payload_path = _path(result_root, "payload_json")
    write_new_bytes(payload_path, final_raw)
    try:
        source = _source_input()
        bundle = compose_once(source, parsed.value)
        if not isinstance(bundle, dict):
            raise TypeError("composer_result_object_required")
        bundle_path = _path(result_root, "composed_bundle_json")
        write_new_json(bundle_path, bundle)
        write_new_json(
            composer_receipt_path,
            {
                "schema_version": "m3.1-r5.2-f02-composer-receipt-v1",
                "revision": REVISION,
                "case_id": CASE_ID,
                "invocation_count": 1,
                "status": "success",
                "failure_code": None,
                "payload_raw_sha256": sha256(final_raw),
                "bundle_raw_sha256": sha256(bundle_path.read_bytes()),
            },
        )
    except Exception as error:
        failure_code = _safe_failure_code(error)
        detail = getattr(error, "detail", None)
        safe_detail = detail if isinstance(detail, dict) else {}
        write_new_json(
            composer_receipt_path,
            {
                "schema_version": "m3.1-r5.2-f02-composer-receipt-v1",
                "revision": REVISION,
                "case_id": CASE_ID,
                "invocation_count": 1,
                "status": "failed",
                "failure_code": failure_code,
                "contract_errors": safe_detail.get("contract_errors", []),
                "validator_errors": safe_detail.get("validator_errors", []),
                "evidence_gaps": safe_detail.get("validator_evidence_gaps", []),
                "raw_output_sha256": sha256(final_raw),
            },
        )
        return _write_terminal(
            result_root,
            launch=launch,
            observation=observation,
            final_raw=final_raw,
            counters=counters,
            accepted=False,
            failure_stage="composer",
            failure_code=failure_code,
            parser_record=parser_record,
            composer_status="failed",
            validator_status="not_invoked",
        )

    counters["validator"] = 1
    try:
        validation = validate_once(bundle)
        if not isinstance(validation, dict):
            raise TypeError("validator_result_object_required")
    except Exception:
        validation = {
            "status": "invalid",
            "errors": ["validator_invocation_failed"],
            "evidence_gaps": [],
        }
    accepted = (
        validation.get("status") == "valid"
        and validation.get("errors") == []
        and validation.get("evidence_gaps") == []
    )
    validation_record = {**validation, "accepted": accepted}
    validation_path = _path(result_root, "validation_json")
    write_new_json(validation_path, validation_record)
    write_new_json(
        _path(result_root, "validator_receipt_json"),
        {
            "schema_version": "m3.1-r5.2-f02-validator-receipt-v1",
            "revision": REVISION,
            "case_id": CASE_ID,
            "invocation_count": 1,
            "status": "accepted" if accepted else "rejected",
            "accepted": accepted,
            "validation_raw_sha256": sha256(validation_path.read_bytes()),
        },
    )
    return _write_terminal(
        result_root,
        launch=launch,
        observation=observation,
        final_raw=final_raw,
        counters=counters,
        accepted=accepted,
        failure_stage=None if accepted else "validator",
        failure_code=None if accepted else "validator_rejected",
        parser_record=parser_record,
        composer_status="success",
        validator_status="accepted" if accepted else "rejected",
    )


def _production_compose(source: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    from compose_m3_bundle import compose_bundle

    return compose_bundle(source, payload)


def _production_validate(bundle: dict[str, Any]) -> dict[str, Any]:
    from validate_m3_method_bundle import validate_m3_bundle

    return validate_m3_bundle(bundle)


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) != 1:
        return 2
    envelope_path = Path(arguments[0])
    try:
        envelope = parse_json_object(envelope_path.read_bytes())
        task_id = envelope["task_id"]
        final_raw = base64.b64decode(envelope["final_raw_base64"], validate=True)
        observation = envelope["observation"]
        if not isinstance(task_id, str) or not isinstance(observation, dict):
            raise ValueError("capture_envelope_invalid")
    except (KeyError, OSError, UnicodeError, json.JSONDecodeError, ValueError, TypeError):
        return 2
    result = consume_final_once(
        AUTHORIZATION_PATH,
        task_id=task_id,
        final_raw=final_raw,
        observation=observation,
        compose_once=_production_compose,
        validate_once=_production_validate,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0 if result["status"] in {"accepted", "terminal_not_accepted"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
