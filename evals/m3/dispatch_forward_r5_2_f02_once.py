#!/usr/bin/env python3
"""Exclusive one-shot launch operations for authorized r5.2-f02."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from audit_forward_r5_2_f02_execution_authorization import (
    audit_execution_authorization,
)
from r5_2_f02_execution_contract import (
    AUTHORIZATION_PATH,
    CASE_ID,
    CONTROL_PATH,
    LAUNCH_ATTEMPT_NAME,
    LAUNCH_RECEIPT_NAME,
    RESULT_ROOT,
    REVISION,
    build_launch_attempt,
    build_launch_receipt,
    parse_json_object,
    validate_execution_control,
    validate_launch_attempt,
    write_new_json,
)
from r5_2_f02_protocol import validate_authorization_receipt
from r5_2_f02_execution_contract import INPUT_BINDING_SHA256, PROMPT_SHA256


def _result(status: str, *, errors: list[str], side_effects: list[str], task_id: str | None = None) -> dict[str, Any]:
    return {
        "status": status,
        "revision": REVISION,
        "case_id": CASE_ID,
        "task_id": task_id,
        "task_count": 1 if status == "launched" else 0,
        "retry_count": 0,
        "callback_invocations": 0,
        "errors": sorted(set(errors)),
        "side_effects": side_effects,
    }


def preflight_execution(
    path: str | Path,
    *,
    result_root: Path = RESULT_ROOT,
) -> dict[str, Any]:
    return audit_execution_authorization(path, result_root=result_root)


def _load_inputs(path: Path) -> tuple[bytes, dict[str, Any], bytes, dict[str, Any]]:
    authorization_raw = path.read_bytes()
    authorization = parse_json_object(authorization_raw)
    receipt_errors = validate_authorization_receipt(
        authorization,
        expected_prompt_sha256=PROMPT_SHA256,
        expected_input_binding_sha256=INPUT_BINDING_SHA256,
    )
    if receipt_errors:
        raise ValueError("execution_authorization_invalid")
    control_raw = CONTROL_PATH.read_bytes()
    control = parse_json_object(control_raw)
    if validate_execution_control(control):
        raise ValueError("execution_control_invalid")
    reference = control.get("authorization_receipt", {})
    from r5_2_f02_execution_contract import sha256

    if not isinstance(reference, dict) or reference.get("raw_sha256") != sha256(
        authorization_raw
    ):
        raise ValueError("authorization_control_binding_invalid")
    return authorization_raw, authorization, control_raw, control


def claim_launch_once(
    path: str | Path,
    *,
    result_root: Path = RESULT_ROOT,
    observed_at: str,
) -> dict[str, Any]:
    """Consume the single attempt budget before the external task call."""

    attempt_path = result_root / LAUNCH_ATTEMPT_NAME
    receipt_path = result_root / LAUNCH_RECEIPT_NAME
    if attempt_path.exists() or receipt_path.exists():
        return _result(
            "already_consumed",
            errors=["launch_attempt_already_consumed"],
            side_effects=[],
        )
    preflight = preflight_execution(Path(path), result_root=result_root)
    if preflight.get("status") != "ready_for_one_shot_fresh_execution":
        return _result(
            "invalid",
            errors=list(preflight.get("errors", ["execution_authorization_invalid"])),
            side_effects=[],
        )
    try:
        authorization_raw, _, control_raw, _ = _load_inputs(Path(path))
        attempt = build_launch_attempt(
            authorization_raw,
            control_raw,
            observed_at=observed_at,
        )
        write_new_json(attempt_path, attempt)
    except FileExistsError:
        return _result(
            "already_consumed",
            errors=["launch_attempt_already_consumed"],
            side_effects=[],
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        return _result(
            "invalid",
            errors=["launch_attempt_claim_failed"],
            side_effects=[],
        )
    return _result(
        "launch_claimed",
        errors=[],
        side_effects=["launch_attempt_claim_created"],
    )


def record_launch_once(
    path: str | Path,
    *,
    task_id: str,
    model_id: str,
    task_created_at: str,
    result_root: Path = RESULT_ROOT,
) -> dict[str, Any]:
    """Bind the already-created task exactly once to the consumed claim."""

    attempt_path = result_root / LAUNCH_ATTEMPT_NAME
    receipt_path = result_root / LAUNCH_RECEIPT_NAME
    if receipt_path.exists():
        return _result(
            "already_consumed",
            errors=["launch_receipt_already_exists"],
            side_effects=[],
        )
    try:
        authorization_raw, _, control_raw, _ = _load_inputs(Path(path))
        attempt = parse_json_object(attempt_path.read_bytes())
        attempt_errors = validate_launch_attempt(
            attempt,
            authorization_raw=authorization_raw,
            control_raw=control_raw,
        )
        if attempt_errors:
            return _result("invalid", errors=attempt_errors, side_effects=[])
        receipt = build_launch_receipt(
            attempt,
            task_id=task_id,
            model_id=model_id,
            task_created_at=task_created_at,
        )
        write_new_json(receipt_path, receipt)
    except FileExistsError:
        return _result(
            "already_consumed",
            errors=["launch_receipt_already_exists"],
            side_effects=[],
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        code = str(error)
        safe = (
            code
            if code
            in {
                "historical_task_id_reuse_forbidden",
                "fresh_task_id_invalid",
                "model_id_invalid",
                "task_created_at_invalid",
            }
            else "launch_receipt_write_failed"
        )
        return _result("invalid", errors=[safe], side_effects=[])
    return _result(
        "launched",
        task_id=task_id,
        errors=[],
        side_effects=["launch_receipt_created"],
    )


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if not arguments or arguments[0] == "preflight":
        if len(arguments) > 1:
            return 2
        result = preflight_execution(AUTHORIZATION_PATH)
    elif arguments[0] == "claim" and len(arguments) == 2:
        result = claim_launch_once(AUTHORIZATION_PATH, observed_at=arguments[1])
    elif arguments[0] == "record-launch" and len(arguments) == 4:
        result = record_launch_once(
            AUTHORIZATION_PATH,
            task_id=arguments[1],
            model_id=arguments[2],
            task_created_at=arguments[3],
        )
    else:
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0 if result["status"] in {
        "ready_for_one_shot_fresh_execution",
        "launch_claimed",
        "launched",
    } else 1


if __name__ == "__main__":
    raise SystemExit(main())
