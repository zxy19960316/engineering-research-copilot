#!/usr/bin/env python3
"""Invoke the M3 forward-outcome validator once and capture exact evidence."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = REPO_ROOT / "evals" / "m3" / "validate_m3_forward_outcome.py"
RUNNER_FAILURE_EXIT = 2
REQUIRED_OUTPUT_FIELDS = {
    "case_id",
    "status",
    "outcome_kind",
    "errors",
    "evidence_gaps",
    "method_bundle_validation",
}


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _artifact_diagnostic(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
    except OSError:
        return {
            "byte_status": "missing_or_unreadable",
            "utf8_status": "not_checked",
            "json_status": "not_checked",
        }
    diagnostic: dict[str, Any] = {
        "byte_status": "read",
        "byte_length": len(raw),
        "raw_sha256": _sha256(raw),
    }
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        diagnostic.update(
            {
                "utf8_status": "invalid",
                "utf8_error": {"byte_start": exc.start, "byte_end": exc.end},
                "json_status": "not_checked",
            }
        )
        return diagnostic
    diagnostic["utf8_status"] = "valid"
    try:
        json.loads(text, parse_constant=lambda _: _reject_nonfinite())
    except json.JSONDecodeError as exc:
        diagnostic.update(
            {
                "json_status": "syntax_error",
                "json_error": {
                    "line": exc.lineno,
                    "column": exc.colno,
                    "position": exc.pos,
                },
            }
        )
    except ValueError:
        diagnostic["json_status"] = "non_finite_number"
    else:
        diagnostic["json_status"] = "valid"
    return diagnostic


def _reject_nonfinite() -> None:
    raise ValueError("non-finite number")


def _write_new(path: Path, receipt: dict[str, Any]) -> bool:
    try:
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(
                json.dumps(
                    receipt,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                    allow_nan=False,
                )
            )
            stream.write("\n")
    except (FileExistsError, OSError):
        return False
    return True


def _base_receipt(
    case_id: str,
    command: list[str],
    source_path: Path,
    outcome_path: Path,
) -> dict[str, Any]:
    try:
        validator_raw = VALIDATOR_PATH.read_bytes()
        validator_sha256: str | None = _sha256(validator_raw)
    except OSError:
        validator_sha256 = None
    return {
        "schema_version": "m3.1-forward-outcome-receipt-r3",
        "case_id": case_id,
        "validator": "evals/m3/validate_m3_forward_outcome.py",
        "validator_script_sha256": validator_sha256,
        "validator_argv": command,
        "validator_invocation_count": 1,
        "source_m2_artifact": _artifact_diagnostic(source_path),
        "outcome_artifact": _artifact_diagnostic(outcome_path),
    }


def _fail(
    receipt_path: Path,
    receipt: dict[str, Any],
    reason: str,
    exit_code: int | None,
    stdout: bytes | None,
) -> int:
    receipt["runner_failure"] = reason
    receipt["validator_exit_code"] = exit_code
    receipt["validator_stdout_sha256"] = (
        _sha256(stdout) if stdout is not None else None
    )
    if not _write_new(receipt_path, receipt):
        return RUNNER_FAILURE_EXIT
    return RUNNER_FAILURE_EXIT


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) != 4:
        return RUNNER_FAILURE_EXIT
    case_id, source_name, outcome_name, receipt_name = arguments
    source_path = Path(source_name)
    outcome_path = Path(outcome_name)
    receipt_path = Path(receipt_name)
    if receipt_path.exists():
        return RUNNER_FAILURE_EXIT

    command = [
        sys.executable,
        "-X",
        "utf8",
        str(VALIDATOR_PATH),
        case_id,
        str(source_path),
        str(outcome_path),
    ]
    receipt = _base_receipt(case_id, command, source_path, outcome_path)
    try:
        completed = subprocess.run(command, capture_output=True)
    except OSError:
        return _fail(
            receipt_path,
            receipt,
            "validator_invocation_error",
            None,
            None,
        )

    stdout = completed.stdout
    stderr = completed.stderr
    receipt["validator_exit_code"] = completed.returncode
    receipt["validator_stdout_sha256"] = _sha256(stdout)
    receipt["validator_stderr_nonempty"] = bool(stderr)
    if stderr:
        return _fail(
            receipt_path,
            receipt,
            "validator_stderr_nonempty",
            completed.returncode,
            stdout,
        )
    try:
        stdout_text = stdout.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return _fail(
            receipt_path,
            receipt,
            "validator_stdout_invalid_utf8",
            completed.returncode,
            stdout,
        )
    lines = stdout_text.splitlines()
    if len(lines) != 1 or not lines[0]:
        return _fail(
            receipt_path,
            receipt,
            "validator_stdout_not_single_line_json",
            completed.returncode,
            stdout,
        )
    try:
        validator_output = json.loads(lines[0])
    except json.JSONDecodeError:
        return _fail(
            receipt_path,
            receipt,
            "validator_stdout_invalid_json",
            completed.returncode,
            stdout,
        )
    if (
        not isinstance(validator_output, dict)
        or set(validator_output) != REQUIRED_OUTPUT_FIELDS
        or validator_output.get("status")
        not in {"accepted", "accepted_expected_block", "invalid"}
        or not isinstance(validator_output.get("errors"), list)
        or not isinstance(validator_output.get("evidence_gaps"), list)
    ):
        return _fail(
            receipt_path,
            receipt,
            "validator_stdout_invalid_receipt",
            completed.returncode,
            stdout,
        )
    expected_exit = (
        0
        if validator_output["status"] in {"accepted", "accepted_expected_block"}
        else 1
    )
    if completed.returncode != expected_exit:
        return _fail(
            receipt_path,
            receipt,
            "validator_exit_status_mismatch",
            completed.returncode,
            stdout,
        )
    receipt["validator_output"] = validator_output
    if not _write_new(receipt_path, receipt):
        return RUNNER_FAILURE_EXIT
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
