#!/usr/bin/env python3
"""Admit one exact successor plan while preserving accepted lifecycle code."""

from __future__ import annotations

import subprocess
from pathlib import Path

_ACCEPTED_LIFECYCLE_SOURCE_HEAD = "4e9fa25b6b7cbbc7bc529cdac87f12e710ead348"
_ACCEPTED_LIFECYCLE_SOURCE_PATH = "evals/m4/authorization/audit_m4_2_gate_iv_b_protocol_proof.py"
_ACCEPTED_LIFECYCLE_SOURCE_BLOB = "a2b5f180b30f97f1c398a6089e57adaa495c11a5"
_SUCCESSOR_CLAIM_EXECUTION_PLAN_PATH = "docs/superpowers/plans/2026-08-12-m4.2-one-shot-claim-and-execution.md"
_LIFECYCLE_SHIM_ORIGINAL_NAME = __name__
_LIFECYCLE_SHIM_REPO_ROOT = Path(__file__).resolve().parents[3]
_LIFECYCLE_SHIM_OID_RESULT = subprocess.run(
    [
        "git",
        "--no-replace-objects",
        "rev-parse",
        f"{_ACCEPTED_LIFECYCLE_SOURCE_HEAD}:{_ACCEPTED_LIFECYCLE_SOURCE_PATH}",
    ],
    cwd=_LIFECYCLE_SHIM_REPO_ROOT,
    check=False,
    capture_output=True,
)
if _LIFECYCLE_SHIM_OID_RESULT.returncode != 0:
    raise RuntimeError(
        "accepted_lifecycle_source_unavailable:"
        + _ACCEPTED_LIFECYCLE_SOURCE_PATH
    )
try:
    _LIFECYCLE_SHIM_OID = _LIFECYCLE_SHIM_OID_RESULT.stdout.decode(
        "ascii", errors="strict"
    ).strip()
except UnicodeDecodeError as error:
    raise RuntimeError(
        "accepted_lifecycle_source_oid_invalid:"
        + _ACCEPTED_LIFECYCLE_SOURCE_PATH
    ) from error
if _LIFECYCLE_SHIM_OID != _ACCEPTED_LIFECYCLE_SOURCE_BLOB:
    raise RuntimeError(
        "accepted_lifecycle_source_blob_mismatch:"
        + _ACCEPTED_LIFECYCLE_SOURCE_PATH
    )
_LIFECYCLE_SHIM_RESULT = subprocess.run(
    [
        "git",
        "--no-replace-objects",
        "cat-file",
        "blob",
        _ACCEPTED_LIFECYCLE_SOURCE_BLOB,
    ],
    cwd=_LIFECYCLE_SHIM_REPO_ROOT,
    check=False,
    capture_output=True,
)
if _LIFECYCLE_SHIM_RESULT.returncode != 0:
    raise RuntimeError(
        "accepted_lifecycle_source_unavailable:"
        + _ACCEPTED_LIFECYCLE_SOURCE_PATH
    )
try:
    _LIFECYCLE_SHIM_SOURCE = _LIFECYCLE_SHIM_RESULT.stdout.decode(
        "utf-8", errors="strict"
    )
except UnicodeDecodeError as error:
    raise RuntimeError(
        "accepted_lifecycle_source_utf8_invalid:"
        + _ACCEPTED_LIFECYCLE_SOURCE_PATH
    ) from error

globals()["__name__"] = _LIFECYCLE_SHIM_ORIGINAL_NAME + ".__accepted_source__"
exec(
    compile(
        _LIFECYCLE_SHIM_SOURCE,
        str(Path(__file__).resolve()),
        "exec",
    ),
    globals(),
    globals(),
)
globals()["__name__"] = _LIFECYCLE_SHIM_ORIGINAL_NAME

SUCCESSOR_CLAIM_EXECUTION_PLAN_RELATIVE = _SUCCESSOR_CLAIM_EXECUTION_PLAN_PATH
ALLOWED_CHANGE_PATHS = frozenset(
    set(ALLOWED_CHANGE_PATHS) | {SUCCESSOR_CLAIM_EXECUTION_PLAN_RELATIVE}
)

if _LIFECYCLE_SHIM_ORIGINAL_NAME == "__main__":
    raise SystemExit(main())
