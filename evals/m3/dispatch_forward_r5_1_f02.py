#!/usr/bin/env python3
"""Narrow r5.1-f02 readiness dispatcher that cannot launch a fresh run."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Callable

from audit_forward_r5_1_f02_authorization import (
    CASE_ID,
    REPO_ROOT,
    REVISION,
    audit_authorization,
)


def preflight_dispatch(
    manifest_path: str | Path,
    callback: Callable[[], Any],
    *,
    case_id: str = CASE_ID,
    revision: str = REVISION,
) -> dict[str, Any]:
    """Return readiness without invoking ``callback`` or writing any artifact.

    A future execution revision must add and validate a separately authorized
    receipt before it can expose a callback path. Readiness alone is never
    treated as execution authority.
    """

    del callback
    if case_id != CASE_ID or revision != REVISION:
        return {
            "status": "invalid",
            "case_id": case_id,
            "revision": revision,
            "callback_invocations": 0,
            "reason": "replacement_identity_invalid",
            "errors": ["replacement_identity_invalid"],
            "side_effects": [],
        }

    audit = audit_authorization(manifest_path)
    if audit.get("status") != "ready_for_fresh_authorization":
        return {
            "status": "invalid",
            "case_id": CASE_ID,
            "revision": REVISION,
            "callback_invocations": 0,
            "reason": "authorization_preflight_invalid",
            "errors": audit.get("errors", ["authorization_preflight_invalid"]),
            "side_effects": [],
        }

    return {
        "status": "ready_for_fresh_authorization",
        "case_id": CASE_ID,
        "revision": REVISION,
        "callback_invocations": 0,
        "reason": "fresh_run_not_authorized",
        "errors": [],
        "side_effects": [],
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
    result = preflight_dispatch(path, lambda: None)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0 if result["status"] == "ready_for_fresh_authorization" else 1


if __name__ == "__main__":
    raise SystemExit(main())
