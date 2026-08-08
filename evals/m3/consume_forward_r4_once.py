#!/usr/bin/env python3
"""Consume one finalized r4 model response through the manifest dispatcher."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from dispatch_forward_r4 import dispatch_case


REPO_ROOT = Path(__file__).resolve().parents[2]
COMPOSER_PATH = (
    REPO_ROOT
    / "skills"
    / "engineering-research-copilot"
    / "scripts"
    / "compose_m3_bundle.py"
)
VALIDATOR_RUNNER_PATH = REPO_ROOT / "evals" / "m3" / "run_forward_validation_once.py"
OUTCOME_VALIDATOR_RUNNER_PATH = (
    REPO_ROOT / "evals" / "m3" / "run_forward_outcome_validation_once.py"
)


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _write_new_bytes(path: Path, raw: bytes) -> None:
    if path.exists():
        raise RuntimeError(f"output_already_exists:{path}")
    descriptor = -1
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = -1
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def _write_new_json(path: Path, value: dict[str, Any]) -> None:
    raw = (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    _write_new_bytes(path, raw)


def _relative(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()


def _command_receipt(command: list[str], completed: subprocess.CompletedProcess[bytes]) -> dict[str, Any]:
    return {
        "argv": command,
        "returncode": completed.returncode,
        "stdout_sha256": _sha256(completed.stdout),
        "stderr_sha256": _sha256(completed.stderr),
        "stdout_nonempty": bool(completed.stdout),
        "stderr_nonempty": bool(completed.stderr),
    }


def _run(command: list[str]) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(command, capture_output=True, check=False)
    except OSError as exc:
        raise RuntimeError(f"invocation_error:{type(exc).__name__}") from exc


def _consume(plan: dict[str, Any], final_raw: bytes) -> dict[str, Any]:
    case_id = str(plan["case_id"])
    paths = plan["future_paths"]
    if case_id == "m3-f03":
        final_path = paths["output_outcome_json"]
        validation_path = paths["output_validation_json"]
        command = [
            sys.executable,
            "-X",
            "utf8",
            str(OUTCOME_VALIDATOR_RUNNER_PATH),
            case_id,
            str(plan["source_input_path"]),
            str(final_path),
            str(validation_path),
        ]
        _write_new_bytes(final_path, final_raw)
        completed = _run(command)
        _write_new_json(
            paths["receipt_validator_receipt_json"],
            {
                "case_id": case_id,
                "final_raw_sha256": _sha256(final_raw),
                "final_byte_length": len(final_raw),
                "validator_invocation_count": 1,
                "validator_runner": _command_receipt(command, completed),
                "validation_path": _relative(validation_path),
            },
        )
        return {
            "final_path": _relative(final_path),
            "final_raw_sha256": _sha256(final_raw),
            "final_byte_length": len(final_raw),
            "composer_invocation_count": 0,
            "validator_invocation_count": 1,
            "validator_runner_returncode": completed.returncode,
        }

    final_path = paths["output_payload_json"]
    bundle_path = paths["output_bundle_json"]
    validation_path = paths["output_validation_json"]
    compose_command = [
        sys.executable,
        "-X",
        "utf8",
        str(COMPOSER_PATH),
        str(plan["source_input_path"]),
        str(final_path),
        str(bundle_path),
    ]
    _write_new_bytes(final_path, final_raw)
    try:
        compose_completed = _run(compose_command)
    except RuntimeError as exc:
        _write_new_json(
            paths["receipt_composer_receipt_json"],
            {
                "case_id": case_id,
                "final_raw_sha256": _sha256(final_raw),
                "final_byte_length": len(final_raw),
                "composer_invocation_count": 1,
                "composer_runner_failure": str(exc),
                "composer_argv": compose_command,
            },
        )
    else:
        _write_new_json(
            paths["receipt_composer_receipt_json"],
            {
                "case_id": case_id,
                "final_raw_sha256": _sha256(final_raw),
                "final_byte_length": len(final_raw),
                "composer_invocation_count": 1,
                "composer_runner": _command_receipt(compose_command, compose_completed),
            },
        )

    validate_command = [
        sys.executable,
        "-X",
        "utf8",
        str(VALIDATOR_RUNNER_PATH),
        str(bundle_path),
        str(validation_path),
    ]
    try:
        validate_completed = _run(validate_command)
    except RuntimeError as exc:
        _write_new_json(
            paths["receipt_validator_receipt_json"],
            {
                "case_id": case_id,
                "validator_invocation_count": 1,
                "validator_runner_failure": str(exc),
                "validator_argv": validate_command,
                "validation_path": _relative(validation_path),
            },
        )
        validator_returncode: int | None = None
    else:
        _write_new_json(
            paths["receipt_validator_receipt_json"],
            {
                "case_id": case_id,
                "validator_invocation_count": 1,
                "validator_runner": _command_receipt(validate_command, validate_completed),
                "validation_path": _relative(validation_path),
            },
        )
        validator_returncode = validate_completed.returncode
    return {
        "final_path": _relative(final_path),
        "final_raw_sha256": _sha256(final_raw),
        "final_byte_length": len(final_raw),
        "composer_invocation_count": 1,
        "validator_invocation_count": 1,
        "validator_runner_returncode": validator_returncode,
    }


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) != 3:
        print(json.dumps({"status": "blocked", "errors": ["expected_manifest_case_and_base64"]}))
        return 2
    manifest_path = Path(arguments[0])
    case_id = arguments[1]
    try:
        final_raw = base64.b64decode(arguments[2], validate=True)
    except (ValueError, TypeError):
        print(json.dumps({"status": "blocked", "errors": ["final_base64_invalid"]}))
        return 2
    try:
        final_raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        print(json.dumps({"status": "blocked", "errors": ["final_utf8_invalid"]}))
        return 2

    callback_result: dict[str, Any] = {}

    def consume(plan: dict[str, Any]) -> None:
        callback_result.update(_consume(plan, final_raw))

    result = dispatch_case(manifest_path, case_id, consume)
    output = {
        "status": result["status"],
        "case_id": case_id,
        "fresh_context_consumed": result.get("fresh_context_consumed", False),
        "errors": result.get("errors", []),
        **callback_result,
    }
    print(json.dumps(output, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0 if result["status"] == "dispatched" else 1


if __name__ == "__main__":
    raise SystemExit(main())
