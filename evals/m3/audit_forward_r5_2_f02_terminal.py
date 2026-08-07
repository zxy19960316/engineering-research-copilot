#!/usr/bin/env python3
"""Independent terminal audit for the one-shot r5.2-f02 result."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

from r5_2_f02_execution_contract import (
    AUTHORIZATION_PATH,
    CASE_ID,
    CONTROL_PATH,
    FUTURE_PATHS,
    LAUNCH_ATTEMPT_NAME,
    LAUNCH_RECEIPT_NAME,
    RESULT_ROOT,
    REVISION,
    expected_model_visible_messages_sha256,
    expected_request_envelope_sha256,
    parse_json_object,
    sha256,
    validate_launch_attempt,
    validate_launch_receipt,
)
from r5_2_f02_protocol import validate_raw_observation


REPO_ROOT = Path(__file__).resolve().parents[2]
R5_HEAD = "1b696bce53ee0a11163bfe4f91a9a49ab3af6f49"
R5_1_HEAD = "fb5eec44bbf86446cf12bda2bddc76fcb07a7e69"
R5_PATH = "evals/m3/results/forward-r5"
R5_1_PATH = "evals/m3/results/forward-r5.1-f02"


def _add(errors: list[str], code: str) -> None:
    if code not in errors:
        errors.append(code)


def _load(path: Path, code: str, errors: list[str]) -> tuple[dict[str, Any] | None, bytes | None]:
    try:
        raw = path.read_bytes()
        return parse_json_object(raw), raw
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        _add(errors, f"{code}_invalid")
        return None, None


def _historical_tree_clean(head: str, relative: str) -> bool:
    try:
        diff = subprocess.run(
            ["git", "diff", "--quiet", head, "--", relative],
            cwd=REPO_ROOT,
            capture_output=True,
            check=False,
        )
        status = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all", "--", relative],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
    except OSError:
        return False
    return diff.returncode == 0 and status.returncode == 0 and not status.stdout.strip()


def _path(root: Path, key: str) -> Path:
    return root / FUTURE_PATHS[key]


def audit_terminal(
    result_root: Path = RESULT_ROOT,
    *,
    compose_once: Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]] | None = None,
    validate_once: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Audit one terminal state without writing or retrying anything."""

    errors: list[str] = []
    terminal, _ = _load(_path(result_root, "terminal_manifest_json"), "terminal_manifest", errors)
    if terminal is None:
        return {
            "status": "invalid",
            "revision": REVISION,
            "case_id": CASE_ID,
            "accepted": False,
            "counters": {},
            "raw_output_bytes": None,
            "raw_output_sha256": None,
            "unexpected_artifacts": [],
            "side_effects": [],
            "errors": sorted(errors),
        }

    actual_names = sorted(path.name for path in result_root.iterdir())
    allowlist = terminal.get("result_root_allowlist")
    unexpected = []
    if not isinstance(allowlist, list) or allowlist != sorted(set(allowlist)):
        _add(errors, "terminal_result_root_allowlist_invalid")
        allowed = set()
    else:
        allowed = set(allowlist)
        unexpected = sorted(name for name in actual_names if name not in allowed)
        missing = sorted(name for name in allowed if name not in actual_names)
        if missing:
            _add(errors, "terminal_declared_artifact_missing")
    if unexpected or terminal.get("unexpected_artifacts") != []:
        _add(errors, "unexpected_result_artifacts")
    if terminal.get("side_effects") != []:
        _add(errors, "terminal_side_effects_nonempty")

    try:
        raw = _path(result_root, "raw_model_final").read_bytes()
    except OSError:
        raw = b""
        _add(errors, "raw_model_final_unavailable")
    observation, _ = _load(
        _path(result_root, "raw_response_observation_json"),
        "raw_response_observation",
        errors,
    )
    if observation is not None:
        errors.extend(validate_raw_observation(observation, raw_bytes=raw))

    attempt, _ = _load(result_root / LAUNCH_ATTEMPT_NAME, "launch_attempt", errors)
    launch, _ = _load(result_root / LAUNCH_RECEIPT_NAME, "launch_receipt", errors)
    if attempt is not None:
        try:
            errors.extend(
                validate_launch_attempt(
                    attempt,
                    authorization_raw=AUTHORIZATION_PATH.read_bytes(),
                    control_raw=CONTROL_PATH.read_bytes(),
                )
            )
        except OSError:
            _add(errors, "launch_authorization_binding_unavailable")
    if attempt is not None and launch is not None:
        errors.extend(validate_launch_receipt(launch, attempt=attempt))

    task_id = terminal.get("task_id")
    if not isinstance(task_id, str) or not task_id:
        _add(errors, "terminal_task_id_invalid")
    for value, code in (
        (launch, "launch_receipt"),
        (observation, "raw_response_observation"),
    ):
        if isinstance(value, dict):
            field = "fresh_task_id" if value is launch else "task_id"
            if value.get(field) != task_id:
                _add(errors, f"terminal_task_binding_mismatch:{code}")
    if isinstance(observation, dict):
        if observation.get("model_id") != terminal.get("model_id"):
            _add(errors, "terminal_model_binding_mismatch")
        if observation.get("finalization_id") != terminal.get("finalization_id"):
            _add(errors, "terminal_finalization_binding_mismatch")
        if observation.get("request_envelope_sha256") != expected_request_envelope_sha256():
            _add(errors, "request_envelope_sha256_mismatch")
        if observation.get("model_visible_messages_sha256") != expected_model_visible_messages_sha256():
            _add(errors, "model_visible_messages_sha256_mismatch")

    raw_record = terminal.get("raw_output")
    if not isinstance(raw_record, dict):
        _add(errors, "terminal_raw_output_record_invalid")
    else:
        if raw_record.get("path") != FUTURE_PATHS["raw_model_final"]:
            _add(errors, "terminal_raw_output_path_invalid")
        if raw_record.get("byte_length") != len(raw):
            _add(errors, "terminal_raw_output_byte_length_mismatch")
        if raw_record.get("raw_sha256") != sha256(raw):
            _add(errors, "terminal_raw_output_sha256_mismatch")

    context, _ = _load(_path(result_root, "context_finalization_json"), "context", errors)
    transaction, transaction_raw = _load(
        _path(result_root, "case_transaction_json"), "transaction", errors
    )
    composer, _ = _load(
        _path(result_root, "composer_invocation_receipt_json"),
        "composer_receipt",
        errors,
    )
    counters = terminal.get("counters")
    if not isinstance(counters, dict) or set(counters) != {
        "tasks",
        "finalizations",
        "composer",
        "validator",
        "retry",
    }:
        _add(errors, "terminal_counters_invalid")
        counters = {}
    for value, code in ((context, "context"), (transaction, "transaction")):
        if isinstance(value, dict) and value.get("counters") != counters:
            _add(errors, f"terminal_counter_binding_mismatch:{code}")
    if counters.get("tasks") != 1:
        _add(errors, "terminal_task_count_invalid")
    if counters.get("finalizations") != 1:
        _add(errors, "terminal_finalization_count_invalid")
    if counters.get("composer") != 1:
        _add(errors, "terminal_composer_count_invalid")
    if counters.get("validator") not in {0, 1}:
        _add(errors, "terminal_validator_count_invalid")
    if counters.get("retry") != 0:
        _add(errors, "terminal_retry_count_invalid")
    if terminal.get("retry_allowed") is not False or terminal.get("same_task_retry_forbidden") is not True:
        _add(errors, "terminal_retry_policy_invalid")

    accepted = terminal.get("accepted") is True
    expected_status = "accepted" if accepted else "terminal_not_accepted"
    if terminal.get("status") != expected_status:
        _add(errors, "terminal_status_acceptance_mismatch")
    expected_state = "completed" if accepted else "processing_failed"
    if not isinstance(transaction, dict) or transaction.get("state") != expected_state:
        _add(errors, "transaction_state_invalid")
    if isinstance(transaction, dict):
        if transaction.get("accepted") is not accepted:
            _add(errors, "transaction_acceptance_mismatch")
        if transaction.get("retry_count") != 0 or transaction.get("retry_forbidden") is not True:
            _add(errors, "transaction_retry_policy_invalid")
        if transaction.get("unexpected_artifacts") != [] or transaction.get("side_effects") != []:
            _add(errors, "transaction_unexpected_effects")
    transaction_reference = terminal.get("transaction")
    if not isinstance(transaction_reference, dict):
        _add(errors, "terminal_transaction_reference_invalid")
    elif transaction_raw is not None:
        if transaction_reference.get("raw_sha256") != sha256(transaction_raw):
            _add(errors, "terminal_transaction_sha256_mismatch")
        if transaction_reference.get("state") != expected_state:
            _add(errors, "terminal_transaction_state_mismatch")

    composer_status = composer.get("status") if isinstance(composer, dict) else None
    terminal_composer = terminal.get("composer")
    if not isinstance(terminal_composer, dict) or terminal_composer.get("status") != composer_status:
        _add(errors, "terminal_composer_status_mismatch")
    if isinstance(composer, dict) and composer.get("invocation_count") != 1:
        _add(errors, "composer_receipt_count_invalid")

    if counters.get("validator") == 1:
        validation, _ = _load(_path(result_root, "validation_json"), "validation", errors)
        validator, _ = _load(_path(result_root, "validator_receipt_json"), "validator_receipt", errors)
        if not isinstance(validator, dict) or validator.get("invocation_count") != 1:
            _add(errors, "validator_receipt_count_invalid")
        validation_accepted = isinstance(validation, dict) and validation.get("accepted") is True
        if validation_accepted is not accepted:
            _add(errors, "validation_acceptance_mismatch")
        terminal_validator = terminal.get("validator")
        expected_validator_status = "accepted" if accepted else "rejected"
        if not isinstance(terminal_validator, dict) or terminal_validator.get("status") != expected_validator_status:
            _add(errors, "terminal_validator_status_mismatch")
        if validate_once is not None:
            bundle, _ = _load(_path(result_root, "composed_bundle_json"), "bundle", errors)
            if bundle is not None:
                replay = validate_once(bundle)
                replay_accepted = (
                    isinstance(replay, dict)
                    and replay.get("status") == "valid"
                    and replay.get("errors") == []
                    and replay.get("evidence_gaps") == []
                )
                if replay_accepted is not accepted:
                    _add(errors, "validator_replay_acceptance_mismatch")
    else:
        terminal_validator = terminal.get("validator")
        if not isinstance(terminal_validator, dict) or terminal_validator.get("status") != "not_invoked":
            _add(errors, "terminal_validator_status_mismatch")

    if compose_once is not None and composer_status == "success":
        payload, _ = _load(_path(result_root, "payload_json"), "payload", errors)
        bundle, _ = _load(_path(result_root, "composed_bundle_json"), "bundle", errors)
        if payload is not None and bundle is not None:
            from consume_forward_r5_2_f02_once import _source_input

            try:
                replay_bundle = compose_once(_source_input(), payload)
            except Exception:
                _add(errors, "composer_replay_failed")
            else:
                if replay_bundle != bundle:
                    _add(errors, "composer_replay_mismatch")

    if not _historical_tree_clean(R5_HEAD, R5_PATH):
        _add(errors, "immutable_forward_r5_changed")
    if not _historical_tree_clean(R5_1_HEAD, R5_1_PATH):
        _add(errors, "immutable_forward_r5_1_f02_changed")

    return {
        "status": expected_status if not errors else "invalid",
        "revision": REVISION,
        "case_id": CASE_ID,
        "accepted": accepted if not errors else False,
        "task_id": task_id,
        "counters": counters,
        "raw_output_bytes": len(raw),
        "raw_output_sha256": sha256(raw),
        "unexpected_artifacts": unexpected,
        "side_effects": [],
        "errors": sorted(set(errors)),
        "gate_4": "NOT_STARTED",
    }


def _production_compose(source: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    script_root = REPO_ROOT / "skills" / "engineering-research-copilot" / "scripts"
    if str(script_root) not in sys.path:
        sys.path.insert(0, str(script_root))
    from compose_m3_bundle import compose_bundle

    return compose_bundle(source, payload)


def _production_validate(bundle: dict[str, Any]) -> dict[str, Any]:
    script_root = REPO_ROOT / "skills" / "engineering-research-copilot" / "scripts"
    if str(script_root) not in sys.path:
        sys.path.insert(0, str(script_root))
    from validate_m3_method_bundle import validate_m3_bundle

    return validate_m3_bundle(bundle)


def main() -> int:
    result = audit_terminal(
        RESULT_ROOT,
        compose_once=_production_compose,
        validate_once=_production_validate,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0 if result["status"] in {"accepted", "terminal_not_accepted"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
