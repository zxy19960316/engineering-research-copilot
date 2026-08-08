#!/usr/bin/env python3
"""Gate 2 r5.2-f02 readiness preflight with no execution path."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable

from audit_forward_r5_2_f02_preparation import (
    CASE_ID,
    INPUT_ROOT,
    REVISION,
    audit_preparation,
)


ZERO_COUNTERS = {
    "tasks": 0,
    "finalizations": 0,
    "composer": 0,
    "validator": 0,
    "retry": 0,
}


def _invalid(reason: str, errors: list[str]) -> dict[str, Any]:
    return {
        "status": "invalid",
        "case_id": CASE_ID,
        "revision": REVISION,
        "new_fresh_run_authorized": False,
        "fresh_execution": "NOT_RUN",
        "reason": reason,
        "callback_invocations": 0,
        "counters": dict(ZERO_COUNTERS),
        "errors": errors,
        "side_effects": [],
    }


def preflight_dispatch(
    manifest_path: str | Path,
    callback: Callable[[], Any],
    *,
    authorization_receipt: object | None = None,
    case_id: str = CASE_ID,
    revision: str = REVISION,
) -> dict[str, Any]:
    """Return Gate 2 readiness without exposing a launch callback.

    A Gate 3 implementation must separately validate a newly created receipt,
    recheck execution-surface capabilities, bind a new task ID, and add an
    exclusive one-shot launch path. This preparation dispatcher deliberately
    discards its injected callback and cannot consume an authorization receipt.
    """

    del callback
    if case_id != CASE_ID or revision != REVISION:
        return _invalid("replacement_identity_invalid", ["replacement_identity_invalid"])
    if authorization_receipt is not None:
        return _invalid(
            "gate_3_receipt_forbidden_in_gate_2",
            ["gate_3_receipt_forbidden_in_gate_2"],
        )

    audit = audit_preparation(manifest_path)
    if audit.get("status") != "gate_2_preparation_valid":
        return _invalid(
            "gate_2_preparation_invalid",
            list(audit.get("errors", ["gate_2_preparation_invalid"])),
        )

    return {
        "status": "gate_2_preparation_ready",
        "case_id": CASE_ID,
        "revision": REVISION,
        "new_fresh_run_authorized": False,
        "fresh_execution": "NOT_RUN",
        "reason": "fresh_run_not_authorized",
        "callback_invocations": 0,
        "counters": dict(ZERO_COUNTERS),
        "errors": [],
        "side_effects": [],
        "does_not_prove": [
            "Readiness is not an execution authorization receipt.",
            "No task, model output, finalization, composition, validation, or acceptance exists.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) > 1:
        return 2
    manifest = (
        Path(arguments[0]) if arguments else INPUT_ROOT / "manifest.json"
    )
    result = preflight_dispatch(manifest, lambda: None)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0 if result["status"] == "gate_2_preparation_ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
