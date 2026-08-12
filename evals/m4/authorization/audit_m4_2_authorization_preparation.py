#!/usr/bin/env python3
"""Admit exact Gate A static protocol paths while preserving accepted lifecycle code."""

from __future__ import annotations

import subprocess
from pathlib import Path


_ACCEPTED_LIFECYCLE_SOURCE_HEAD = "4e9fa25b6b7cbbc7bc529cdac87f12e710ead348"
_ACCEPTED_LIFECYCLE_SOURCE_PATH = "evals/m4/authorization/audit_m4_2_authorization_preparation.py"
_ACCEPTED_LIFECYCLE_SOURCE_BLOB = "8421d433778e86209218fe0272ec97a6d71f1f9e"
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
ALLOWED_CHANGE_PATHS = frozenset(
    set(ALLOWED_CHANGE_PATHS) | set(GATE_A_STATIC_PATHS)
)
_ACCEPTED_DISCOVER_FORBIDDEN_PATHS = discover_forbidden_paths


def discover_forbidden_paths(
    repo_root: Path,
    present_paths: set[str] | None = None,
) -> list[str]:
    """Permit only exact Gate A static files; runtime evidence stays forbidden."""

    found = set(
        _ACCEPTED_DISCOVER_FORBIDDEN_PATHS(
            repo_root,
            present_paths,
        )
    )
    return sorted(found - set(GATE_A_STATIC_PATHS))


if _LIFECYCLE_SHIM_ORIGINAL_NAME == "__main__":
    raise SystemExit(main())
