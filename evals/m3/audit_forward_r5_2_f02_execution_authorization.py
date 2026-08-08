#!/usr/bin/env python3
"""Read-only audit of the r5.2-f02 one-shot execution authorization."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from r5_2_f02_execution_contract import (
    AUTHORIZATION_PATH,
    CASE_ID,
    CONTROL_PATH,
    GATE_2_CI_RUN_ID,
    GATE_2_HEAD,
    INPUT_BINDING_SHA256,
    LAUNCH_SCHEMA_PATH,
    PROMPT_SHA256,
    RESULT_ROOT,
    REVISION,
    ZERO_COUNTERS,
    sha256,
    validate_execution_control,
)
from r5_2_f02_protocol import (
    parse_strict_json_object,
    validate_authorization_receipt,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
R5_HEAD = "1b696bce53ee0a11163bfe4f91a9a49ab3af6f49"
R5_1_HEAD = "fb5eec44bbf86446cf12bda2bddc76fcb07a7e69"
R5_PATH = "evals/m3/results/forward-r5"
R5_1_PATH = "evals/m3/results/forward-r5.1-f02"
GATE_2_FROZEN_PATHS = (
    "evals/m3/forward-inputs-r5.2-f02/manifest.json",
    "evals/m3/forward-inputs-r5.2-f02/m3-f02.prompt.txt",
    "evals/m3/forward-inputs-r5.2-f02/m3-f02.input-binding.json",
    "evals/m3/forward-inputs-r5.2-f02/m3-model-output-contract.schema.json",
    "evals/m3/forward-inputs-r5.2-f02/m3-f02.authorization-receipt.schema.json",
    "evals/m3/forward-inputs-r5.2-f02/m3-f02.raw-response-observation.schema.json",
    "evals/m3/forward-inputs-r5.2-f02/m3-f02.output-mode.json",
    "evals/m3/forward-inputs-r5.2-f02/protocol-regression-cases.json",
    "evals/m3/r5_2_f02_protocol.py",
    "evals/m3/audit_forward_r5_2_f02_preparation.py",
    "evals/m3/dispatch_forward_r5_2_f02.py",
    "evals/m3/results/forward-r5.2-f02/.gitkeep",
)


def _add(errors: list[str], code: str) -> None:
    if code not in errors:
        errors.append(code)


def _load_strict(path: Path, code: str, errors: list[str]) -> tuple[dict[str, Any] | None, bytes | None]:
    try:
        raw = path.read_bytes()
    except OSError:
        _add(errors, f"{code}_unavailable")
        return None, None
    parsed = parse_strict_json_object(raw)
    if not parsed.ok or parsed.value is None:
        _add(errors, f"{code}_invalid_json")
        return None, raw
    return parsed.value, raw


def _git_blob(head: str, relative: str) -> bytes | None:
    try:
        result = subprocess.run(
            ["git", "show", f"{head}:{relative}"],
            cwd=REPO_ROOT,
            capture_output=True,
            check=False,
        )
    except OSError:
        return None
    return result.stdout if result.returncode == 0 else None


def _gate_2_snapshot_errors() -> list[str]:
    errors: list[str] = []
    try:
        ancestor = subprocess.run(
            ["git", "merge-base", "--is-ancestor", GATE_2_HEAD, "HEAD"],
            cwd=REPO_ROOT,
            capture_output=True,
            check=False,
        )
    except OSError:
        ancestor = None
    if ancestor is None or ancestor.returncode != 0:
        _add(errors, "gate_2_head_not_ancestor")
    for relative in GATE_2_FROZEN_PATHS:
        frozen = _git_blob(GATE_2_HEAD, relative)
        if frozen is None:
            _add(errors, f"gate_2_frozen_blob_unavailable:{relative}")
            continue
        current = _git_blob("HEAD", relative)
        if current is None:
            _add(errors, f"gate_2_current_blob_unavailable:{relative}")
            continue
        if current != frozen:
            _add(errors, f"gate_2_frozen_blob_changed:{relative}")
    return sorted(errors)


def _historical_tree_clean(head: str, relative: str) -> bool:
    try:
        diff = subprocess.run(
            ["git", "diff", "--quiet", head, "--", relative],
            cwd=REPO_ROOT,
            capture_output=True,
            check=False,
        )
        status = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all", "--", relative],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
    except OSError:
        return False
    return diff.returncode == 0 and status.returncode == 0 and not status.stdout.strip()


def _check_result_root(result_root: Path, errors: list[str]) -> int:
    if not result_root.is_dir() or result_root.is_symlink():
        _add(errors, "result_root_invalid")
        return 0
    entries = list(result_root.iterdir())
    marker = result_root / ".gitkeep"
    try:
        marker_valid = marker.is_file() and not marker.is_symlink() and marker.read_bytes() == b""
    except OSError:
        marker_valid = False
    if not marker_valid:
        _add(errors, "result_root_marker_invalid")
    artifacts = [path for path in entries if path.name != ".gitkeep"]
    if artifacts:
        _add(errors, "result_root_not_logically_empty")
    return len(artifacts)


def _check_launch_schema(errors: list[str]) -> None:
    value, _ = _load_strict(LAUNCH_SCHEMA_PATH, "launch_schema", errors)
    if value is None:
        return
    if value.get("$id") != "urn:engineering-research-copilot:m3:r5.2-f02:launch-records":
        _add(errors, "launch_schema_id_invalid")
    if value.get("x-max-fresh-tasks") != 1:
        _add(errors, "launch_schema_task_limit_invalid")
    if value.get("x-retry-allowed") is not False:
        _add(errors, "launch_schema_retry_policy_invalid")


def audit_execution_authorization(
    path: str | Path,
    *,
    control_path: str | Path = CONTROL_PATH,
    result_root: Path = RESULT_ROOT,
) -> dict[str, Any]:
    """Audit the unconsumed authorization without writing or launching."""

    errors: list[str] = []
    authorization, authorization_raw = _load_strict(
        Path(path), "authorization_receipt", errors
    )
    control, control_raw = _load_strict(
        Path(control_path), "execution_control", errors
    )
    if authorization is not None:
        errors.extend(
            validate_authorization_receipt(
                authorization,
                expected_prompt_sha256=PROMPT_SHA256,
                expected_input_binding_sha256=INPUT_BINDING_SHA256,
            )
        )
    if control is not None:
        errors.extend(validate_execution_control(control))
    if authorization_raw is not None and control is not None:
        reference = control.get("authorization_receipt")
        if not isinstance(reference, dict) or reference.get("raw_sha256") != sha256(
            authorization_raw
        ):
            _add(errors, "authorization_receipt_control_hash_mismatch")

    errors.extend(_gate_2_snapshot_errors())
    _check_launch_schema(errors)
    artifact_count = _check_result_root(result_root, errors)
    if not _historical_tree_clean(R5_HEAD, R5_PATH):
        _add(errors, "immutable_forward_r5_changed")
    if not _historical_tree_clean(R5_1_HEAD, R5_1_PATH):
        _add(errors, "immutable_forward_r5_1_f02_changed")

    counters = (
        control.get("prelaunch_counters")
        if isinstance(control, dict)
        else dict(ZERO_COUNTERS)
    )
    if not isinstance(counters, dict):
        counters = {}
    return {
        "status": "ready_for_one_shot_fresh_execution" if not errors else "invalid",
        "revision": REVISION,
        "case_id": CASE_ID,
        "readiness_head": GATE_2_HEAD,
        "readiness_ci_run_id": GATE_2_CI_RUN_ID,
        "authorization_raw_sha256": sha256(authorization_raw)
        if authorization_raw is not None
        else None,
        "execution_control_raw_sha256": sha256(control_raw)
        if control_raw is not None
        else None,
        "selected_output_mode": "strict_text_json_fail_closed",
        "structured_output_request_config": None,
        "logical_result_artifact_count": artifact_count,
        "counters": counters,
        "callback_invocations": 0,
        "side_effects": [],
        "errors": sorted(set(errors)),
        "does_not_prove": [
            "No fresh task has been created or finalized.",
            "No raw response, composer, validator, transaction, or acceptance exists.",
            "Cross-revision aggregation, M3 closure, Gate 4, and M4 remain unauthorized.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) > 1:
        return 2
    authorization = Path(arguments[0]) if arguments else AUTHORIZATION_PATH
    result = audit_execution_authorization(authorization)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0 if result["status"] == "ready_for_one_shot_fresh_execution" else 1


if __name__ == "__main__":
    raise SystemExit(main())
