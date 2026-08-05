#!/usr/bin/env python3
"""Run the M3 validator once and persist one closed validation receipt."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = (
    REPO_ROOT
    / "skills"
    / "engineering-research-copilot"
    / "scripts"
    / "validate_m3_method_bundle.py"
)
REQUIRED_VALIDATOR_FIELDS = {"status", "errors", "evidence_gaps"}
RUNNER_FAILURE_EXIT = 2


def _write_new_json(path: Path, payload: dict[str, Any]) -> bool:
    """Create one UTF-8/no-BOM JSON line without overwriting an artifact."""

    try:
        with path.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(
                json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
            )
            handle.write("\n")
    except (FileExistsError, OSError):
        return False
    return True


def _runner_failure(reason: str, returncode: int | None = None) -> dict[str, Any]:
    receipt: dict[str, Any] = {"runner_failure": reason}
    if returncode is not None:
        receipt["validator_returncode"] = returncode
    return receipt


def _save_failure(validation_path: Path, reason: str, returncode: int | None = None) -> int:
    if not _write_new_json(validation_path, _runner_failure(reason, returncode)):
        return RUNNER_FAILURE_EXIT
    return RUNNER_FAILURE_EXIT


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) != 2:
        return RUNNER_FAILURE_EXIT

    output_path = Path(arguments[0])
    validation_path = Path(arguments[1])
    if validation_path.exists():
        return RUNNER_FAILURE_EXIT

    command = [
        sys.executable,
        "-X",
        "utf8",
        str(VALIDATOR_PATH),
        str(output_path),
    ]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="strict",
        )
    except (OSError, UnicodeError):
        return _save_failure(validation_path, "validator_invocation_error")

    if completed.stderr:
        return _save_failure(
            validation_path,
            "validator_stderr_nonempty",
            completed.returncode,
        )

    lines = completed.stdout.splitlines()
    if len(lines) != 1 or not lines[0].strip():
        return _save_failure(
            validation_path,
            "validator_stdout_not_single_line_json",
            completed.returncode,
        )

    try:
        payload = json.loads(lines[0])
    except json.JSONDecodeError:
        return _save_failure(
            validation_path,
            "validator_stdout_invalid_json",
            completed.returncode,
        )

    if (
        not isinstance(payload, dict)
        or not REQUIRED_VALIDATOR_FIELDS.issubset(payload)
        or not isinstance(payload.get("status"), str)
        or not isinstance(payload.get("errors"), list)
        or not isinstance(payload.get("evidence_gaps"), list)
    ):
        return _save_failure(
            validation_path,
            "validator_stdout_invalid_receipt",
            completed.returncode,
        )

    if not _write_new_json(validation_path, payload):
        return RUNNER_FAILURE_EXIT
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
