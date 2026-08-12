#!/usr/bin/env python3
"""Admit exact Gate A static protocol paths while preserving accepted builder code."""

from __future__ import annotations

import subprocess
from pathlib import Path


_ACCEPTED_LIFECYCLE_SOURCE_HEAD = "4e9fa25b6b7cbbc7bc529cdac87f12e710ead348"
_ACCEPTED_LIFECYCLE_SOURCE_PATH = "evals/m4/authorization/build_m4_2_authorization.py"
_ACCEPTED_LIFECYCLE_SOURCE_BLOB = "d1db55abee500181bb4861a83fa909cb875b3830"
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

GATE_A_STATIC_PATHS = frozenset(
    {
        ".github/workflows/m1-validation.yml",
        "STATUS.md",
        "docs/superpowers/plans/2026-08-12-m4.2-one-shot-claim-and-execution.md",
        "evals/m4/execution/m4.2/launch-claim.schema.json",
        "evals/m4/execution/m4.2/dispatch-receipt.schema.json",
        "evals/m4/execution/m4.2/create-thread-response-attestation.schema.json",
        "evals/m4/execution/m4.2/execution-terminal.schema.json",
        "evals/m4/execution/audit_m4_2.py",
        "evals/m4/execution/build_m4_2_launch_claim.py",
        "evals/m4/execution/record_m4_2_execution_evidence.py",
        "evals/m4/execution/audit_m4_2_launch_readiness.py",
        "tests/test_m4_2_execution.py",
        "tests/test_m4_2_launch_readiness.py",
        "tests/test_m3_r5_erratum.py",
    }
)
GATE_A_STATIC_EXECUTION_PATHS = frozenset(
    {
        "evals/m4/execution/m4.2/launch-claim.schema.json",
        "evals/m4/execution/m4.2/dispatch-receipt.schema.json",
        "evals/m4/execution/m4.2/create-thread-response-attestation.schema.json",
        "evals/m4/execution/m4.2/execution-terminal.schema.json",
    }
)
ALLOWED_CHANGE_PATHS = frozenset(
    set(ALLOWED_CHANGE_PATHS) | set(GATE_A_STATIC_PATHS)
)


def _forbidden_prelaunch_paths() -> list[str]:
    """Reject runtime evidence while permitting only exact Gate A static schemas."""

    found: set[str] = set()
    for relative in (
        TOKEN_RELATIVE,
        ACCEPTANCE_CLAIM_RELATIVE,
        LAUNCH_CLAIM_RELATIVE,
        RESULTS_MANIFEST_RELATIVE,
    ):
        path = REPO_ROOT / relative
        if path.exists() or path.is_symlink():
            found.add(relative)

    execution_root_relative = "evals/m4/execution/m4.2"
    execution_root = REPO_ROOT / execution_root_relative
    if execution_root.exists() or execution_root.is_symlink():
        if execution_root.is_file() or execution_root.is_symlink():
            found.add(execution_root_relative)
        else:
            for item in execution_root.rglob("*"):
                if item.is_file() or item.is_symlink():
                    relative = item.relative_to(REPO_ROOT).as_posix()
                    if relative not in GATE_A_STATIC_EXECUTION_PATHS:
                        found.add(relative)

    for relative in ("evals/m4/results/m4.2", "evals/m5"):
        path = REPO_ROOT / relative
        if path.exists() or path.is_symlink():
            found.add(relative)
    return sorted(found)


if _LIFECYCLE_SHIM_ORIGINAL_NAME == "__main__":
    raise SystemExit(main())
