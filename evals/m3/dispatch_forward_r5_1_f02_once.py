#!/usr/bin/env python3
"""One-shot r5.1-f02 dispatcher with separate read-only preflight."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable

from audit_forward_r5_1_f02_execution_authorization import (
    AUTHORIZATION,
    REPO_ROOT,
    RESULT_ROOT,
    audit_execution_authorization,
)
from consume_forward_r5_once import consume_case_once
from r5_1_f02_execution_contract import (
    CASE_ID,
    EXECUTION_PATHS,
    HISTORICAL_TASK_ID,
    REVISION,
    build_launch_receipt,
    parse_json_object,
    validate_execution_authorization_shape,
    validate_launch_receipt,
    write_new_json,
)


def _invalid(errors: list[str]) -> dict[str, Any]:
    return {
        "status": "invalid",
        "case_id": CASE_ID,
        "revision": REVISION,
        "callback_invocations": 0,
        "task_id": None,
        "errors": sorted(set(errors)),
        "side_effects": [],
    }


def preflight_execution(path: str | Path) -> dict[str, Any]:
    """Audit execution readiness without calling a callback or writing a file."""

    audit = audit_execution_authorization(path)
    if audit.get("status") != "ready_for_one_shot_fresh_execution":
        return _invalid(audit.get("errors", ["execution_authorization_invalid"]))
    return {
        "status": "ready_for_one_shot_fresh_execution",
        "case_id": CASE_ID,
        "revision": REVISION,
        "callback_invocations": 0,
        "task_id": None,
        "authorization_token": audit.get("authorization_token"),
        "errors": [],
        "side_effects": [],
    }


def _load_authorization(path: Path) -> tuple[dict[str, Any], bytes] | None:
    try:
        raw = path.read_bytes()
        value = parse_json_object(raw)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        return None
    if validate_execution_authorization_shape(value):
        return None
    return value, raw


def _terminal_launch_failure(
    authorization: dict[str, Any],
    authorization_raw: bytes,
    receipt_path: Path,
    error: str,
    side_effects: list[str],
) -> dict[str, Any]:
    receipt = build_launch_receipt(
        authorization,
        task_id=None,
        status="launch_failed",
        errors=[error],
        authorization_raw=authorization_raw,
    )
    errors = [error]
    try:
        write_new_json(receipt_path, receipt)
        side_effects.append("launch_receipt_created")
    except FileExistsError:
        errors.append("launch_receipt_overwrite_forbidden")
    except OSError:
        errors.append("launch_receipt_write_failed")
    return {
        "status": "launch_failed",
        "case_id": CASE_ID,
        "revision": REVISION,
        "callback_invocations": 1,
        "task_id": None,
        "errors": sorted(set(errors)),
        "side_effects": side_effects,
    }


def dispatch_authorized_once(
    path: str | Path,
    launch_fresh_context: Callable[[], str],
) -> dict[str, Any]:
    """Consume the authorization once and invoke the injected launcher at most once."""

    preflight = preflight_execution(path)
    if preflight["status"] != "ready_for_one_shot_fresh_execution":
        return preflight
    loaded = _load_authorization(Path(path))
    if loaded is None:
        return _invalid(["execution_authorization_invalid"])
    authorization, authorization_raw = loaded
    if not RESULT_ROOT.is_dir() or RESULT_ROOT.is_symlink():
        return _invalid(["result_root_invalid"])

    claim_path = RESULT_ROOT / EXECUTION_PATHS["launch_attempt_json"]
    receipt_path = RESULT_ROOT / EXECUTION_PATHS["launch_receipt_json"]
    if claim_path.exists() or receipt_path.exists():
        return {
            "status": "already_consumed",
            "case_id": CASE_ID,
            "revision": REVISION,
            "callback_invocations": 0,
            "task_id": None,
            "errors": ["authorization_already_consumed"],
            "side_effects": [],
        }
    claim = {
        "schema_version": "m3.1-forward-r5.1-f02-launch-attempt-v1",
        "case_id": CASE_ID,
        "revision": REVISION,
        "authorization_token": authorization["authorization_token"],
        "attempt_count": 1,
        "max_fresh_tasks": 1,
        "no_retry": True,
    }
    try:
        write_new_json(claim_path, claim)
    except FileExistsError:
        return {
            "status": "already_consumed",
            "case_id": CASE_ID,
            "revision": REVISION,
            "callback_invocations": 0,
            "task_id": None,
            "errors": ["authorization_already_consumed"],
            "side_effects": [],
        }
    except OSError:
        return _invalid(["launch_attempt_claim_write_failed"])
    side_effects = ["launch_attempt_claim_created"]

    try:
        task_id = launch_fresh_context()
    except Exception:
        return _terminal_launch_failure(
            authorization,
            authorization_raw,
            receipt_path,
            "fresh_context_launch_failed",
            side_effects,
        )
    if not isinstance(task_id, str) or not task_id:
        return _terminal_launch_failure(
            authorization,
            authorization_raw,
            receipt_path,
            "fresh_task_id_invalid",
            side_effects,
        )
    if task_id == HISTORICAL_TASK_ID:
        return _terminal_launch_failure(
            authorization,
            authorization_raw,
            receipt_path,
            "historical_task_id_reuse_forbidden",
            side_effects,
        )

    receipt = build_launch_receipt(
        authorization,
        task_id=task_id,
        status="launched",
        errors=[],
        authorization_raw=authorization_raw,
    )
    try:
        write_new_json(receipt_path, receipt)
        side_effects.append("launch_receipt_created")
    except FileExistsError:
        return {
            "status": "launch_receipt_failed",
            "case_id": CASE_ID,
            "revision": REVISION,
            "callback_invocations": 1,
            "task_id": task_id,
            "errors": ["launch_receipt_overwrite_forbidden"],
            "side_effects": side_effects,
        }
    except OSError:
        return {
            "status": "launch_receipt_failed",
            "case_id": CASE_ID,
            "revision": REVISION,
            "callback_invocations": 1,
            "task_id": task_id,
            "errors": ["launch_receipt_write_failed"],
            "side_effects": side_effects,
        }
    return {
        "status": "launched",
        "case_id": CASE_ID,
        "revision": REVISION,
        "callback_invocations": 1,
        "task_id": task_id,
        "errors": [],
        "side_effects": side_effects,
    }


def finalize_authorized_once(
    path: str | Path,
    task_id: str,
    final_raw: bytes,
    *,
    compose_once: Callable[[Path, Path], dict[str, Any]] | None,
    validate_once: Callable[[Path], dict[str, Any]],
) -> dict[str, Any]:
    """Preserve one bound final verbatim, then reuse the r5 consumer exactly once."""

    loaded = _load_authorization(Path(path))
    if loaded is None:
        return {"status": "blocked", "errors": ["execution_authorization_invalid"], "record": None}
    authorization, authorization_raw = loaded
    receipt_path = RESULT_ROOT / EXECUTION_PATHS["launch_receipt_json"]
    try:
        receipt = parse_json_object(receipt_path.read_bytes())
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        return {"status": "blocked", "errors": ["launch_receipt_invalid"], "record": None}
    receipt_errors = validate_launch_receipt(
        receipt,
        authorization,
        authorization_raw=authorization_raw,
    )
    if receipt_errors:
        return {"status": "blocked", "errors": receipt_errors, "record": None}
    if receipt.get("launch_status") != "launched" or receipt.get("fresh_task_id") != task_id:
        return {"status": "blocked", "errors": ["authorized_task_binding_mismatch"], "record": None}
    source = authorization.get("bindings", {}).get("source_input", {}).get("path")
    if not isinstance(source, str):
        return {"status": "blocked", "errors": ["source_input_binding_missing"], "record": None}
    plan = {
        "case_id": CASE_ID,
        "task_id": task_id,
        "future_paths": authorization["future_paths"],
        "result_root": RESULT_ROOT,
        "source_input_path": REPO_ROOT / source,
    }
    return consume_case_once(
        plan,
        final_raw,
        compose_once=compose_once,
        validate_once=validate_once,
    )


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) > 1:
        return 2
    path = Path(arguments[0]) if arguments else AUTHORIZATION
    result = preflight_execution(path)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0 if result["status"] == "ready_for_one_shot_fresh_execution" else 1


if __name__ == "__main__":
    raise SystemExit(main())
