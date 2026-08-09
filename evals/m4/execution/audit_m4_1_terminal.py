#!/usr/bin/env python3
"""Read-only audit of the immutable stopped M4.1 execution terminal."""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from evals.m4.execution import audit_m4_1 as protocol  # noqa: E402


STATUS = "M4_1_STOPPED_PROTOCOL_FAILURE_PRESERVED"
EVIDENCE_BASELINE = "80b54697c3e27a5dad0a24d5318ce26c8fe46141"
CLAIM_ID = "32e0df57-a8d2-5c19-9ffc-da69997686e8"
CLAIM_SHA256 = "c16a2e53aa2e9215e2325464d547356afdb73897bfc7d29605e0105b9987b3c6"
CLAIM_BYTE_LENGTH = 24078
TERMINAL_SHA256 = "7305d71ba94cd209f5bb0cb2c977db3bb157d95b907f8f59df9133c192f4d66e"
TERMINAL_BYTE_LENGTH = 3707
FAILURE_EVIDENCE_SHA256 = (
    "61a18842ac13637f9ba71a5dac6547d1fcbd4355127f97ea213e0ea44941f9c5"
)
FAILED_STAGE = "post_claim_dual_confirmation"
FAILED_BATCH = "M4.1-BATCH-NUC"
FAILED_TASK_ID = "M4.1-NUC-A-F"
RECORDED_AT_UTC = "2026-08-08T14:28:37Z"
PLATFORM_OBSERVATIONS_RELATIVE = Path(
    "evals/m4/execution/m4.1/platform-observations"
)
ZERO_COUNTERS = {
    "tasks": 0,
    "threads": 0,
    "finalizations": 0,
    "attempts": 0,
    "retries": 0,
    "repairs": 0,
    "followups": 0,
    "results": 0,
    "judge_calls": 0,
    "aggregation_calls": 0,
    "side_effects": 0,
}
EXPECTED_LATER_GATES = {
    "judge": "NOT_RUN",
    "unblinding_and_aggregation": "NOT_RUN",
    "threshold_decision": "NOT_RUN",
    "m4_closure": "NOT_RUN",
    "m5": "NOT_STARTED",
}


def _add(errors: list[str], code: str) -> None:
    if code not in errors:
        errors.append(code)


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _load_object(
    path: Path, label: str, errors: list[str]
) -> tuple[dict[str, Any], bytes]:
    if not path.is_file():
        _add(errors, f"{label}_missing" if not path.exists() else f"{label}_not_file")
        return {}, b""
    try:
        raw = path.read_bytes()
    except OSError:
        _add(errors, f"{label}_unavailable")
        return {}, b""
    try:
        return protocol.parse_json_object(raw), raw
    except (UnicodeError, ValueError, json.JSONDecodeError):
        _add(errors, f"{label}_invalid_json")
        return {}, raw


def _git(repo_root: Path, *arguments: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *arguments],
        cwd=repo_root,
        capture_output=True,
        check=False,
    )


def _verify_git_preservation(
    repo_root: Path,
    *,
    claim_path: Path,
    terminal_path: Path,
    claim_raw: bytes,
    terminal_raw: bytes,
    errors: list[str],
) -> None:
    expected_paths = {
        protocol.CLAIM_RELATIVE: claim_path,
        protocol.TERMINAL_RELATIVE: terminal_path,
    }
    for relative, actual in expected_paths.items():
        if actual.resolve() != (repo_root / relative).resolve():
            _add(errors, f"git_verification_custom_path:{relative.as_posix()}")
            return

    if _git(repo_root, "cat-file", "-e", f"{EVIDENCE_BASELINE}^{{commit}}").returncode:
        _add(errors, "evidence_baseline_unavailable")
        return
    if _git(
        repo_root, "merge-base", "--is-ancestor", EVIDENCE_BASELINE, "HEAD"
    ).returncode:
        _add(errors, "evidence_baseline_not_ancestor")

    raw_by_path = {
        protocol.CLAIM_RELATIVE: claim_raw,
        protocol.TERMINAL_RELATIVE: terminal_raw,
    }
    for relative, current_raw in raw_by_path.items():
        relative_text = relative.as_posix()
        if _git(
            repo_root,
            "diff",
            "--raw",
            "--exit-code",
            EVIDENCE_BASELINE,
            "HEAD",
            "--",
            relative_text,
        ).returncode:
            _add(errors, f"evidence_git_diff:{relative_text}")
        baseline_blob = _git(
            repo_root, "show", f"{EVIDENCE_BASELINE}:{relative_text}"
        )
        if baseline_blob.returncode:
            _add(errors, f"evidence_baseline_blob_unavailable:{relative_text}")
        elif baseline_blob.stdout != current_raw:
            _add(errors, f"evidence_worktree_bytes_changed:{relative_text}")


def _validate_claim(claim: dict[str, Any], errors: list[str]) -> None:
    if claim.get("claim_id") != CLAIM_ID:
        _add(errors, "claim_id_invalid")
    if claim.get("claim_count") != 1:
        _add(errors, "claim_count_invalid")
    if claim.get("claimed_at_utc") != RECORDED_AT_UTC:
        _add(errors, "claim_timestamp_invalid")
    if claim.get("status") != "CLAIMED":
        _add(errors, "claim_status_invalid")
    authorization = claim.get("authorization")
    if not isinstance(authorization, dict):
        _add(errors, "claim_authorization_invalid")
        return
    if authorization.get("token_status_after_claim") != "CONSUMED":
        _add(errors, "claim_token_not_consumed")
    if authorization.get("claim_consumes_entire_authorization") is not True:
        _add(errors, "claim_does_not_consume_entire_authorization")


def _decode_failure_evidence(
    terminal: dict[str, Any], errors: list[str]
) -> dict[str, Any]:
    evidence = terminal.get("failure_evidence")
    if not isinstance(evidence, dict):
        _add(errors, "failure_evidence_invalid")
        return {}
    if evidence.get("failure_class") != "PROTOCOL_FAILURE":
        _add(errors, "failure_class_invalid")
    if evidence.get("raw_evidence_sha256") != FAILURE_EVIDENCE_SHA256:
        _add(errors, "failure_evidence_sha256_invalid")
    raw_evidence = evidence.get("raw_evidence")
    if not isinstance(raw_evidence, str) or not raw_evidence.startswith("base64:"):
        _add(errors, "failure_evidence_encoding_invalid")
        return {}
    if _sha256(raw_evidence.encode("utf-8")) != evidence.get(
        "raw_evidence_sha256"
    ):
        _add(errors, "failure_evidence_hash_mismatch")
    try:
        encoded = raw_evidence.removeprefix("base64:").encode("ascii")
        decoded = base64.b64decode(encoded, validate=True)
    except (UnicodeEncodeError, binascii.Error, ValueError):
        _add(errors, "failure_evidence_base64_invalid")
        return {}
    try:
        payload = protocol.parse_json_object(decoded)
    except (UnicodeError, ValueError, json.JSONDecodeError):
        _add(errors, "failure_evidence_payload_invalid_json")
        return {}
    if payload.get("code") != "post_claim_dual_confirmation_failed":
        _add(errors, "failure_evidence_code_invalid")
    if payload.get("execution_status") != "INVALID":
        _add(errors, "failure_evidence_execution_status_invalid")
    authorization_errors = payload.get("authorization_errors")
    if not isinstance(authorization_errors, list) or any(
        not isinstance(item, str) for item in authorization_errors
    ):
        _add(errors, "failure_evidence_authorization_errors_invalid")
    else:
        if "authorization_already_claimed" not in authorization_errors:
            _add(errors, "authorization_already_claimed_missing")
        if "preparation_audit_failed:launch_claim_present" not in authorization_errors:
            _add(errors, "post_claim_presence_error_missing")
    execution_errors = payload.get("execution_errors")
    if not isinstance(execution_errors, list) or any(
        not isinstance(item, str) for item in execution_errors
    ):
        _add(errors, "failure_evidence_execution_errors_invalid")
    return payload


def _validate_terminal(
    terminal: dict[str, Any], *, claim: dict[str, Any], claim_raw: bytes, errors: list[str]
) -> None:
    if terminal.get("terminal_state") != "STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE":
        _add(errors, "terminal_state_invalid")
    if terminal.get("recorded_at_utc") != RECORDED_AT_UTC:
        _add(errors, "terminal_timestamp_invalid")
    if terminal.get("failed_stage") != FAILED_STAGE:
        _add(errors, "failed_stage_invalid")
    if terminal.get("failed_batch") != FAILED_BATCH:
        _add(errors, "failed_batch_invalid")
    if terminal.get("failed_task_id") != FAILED_TASK_ID:
        _add(errors, "failed_task_id_invalid")
    if terminal.get("last_completed_batch") is not None:
        _add(errors, "last_completed_batch_invalid")
    if terminal.get("successor_revision_required") is not True:
        _add(errors, "successor_revision_not_required")
    if terminal.get("launch_claim") != {
        "claim_id": claim.get("claim_id"),
        "path": protocol.CLAIM_RELATIVE.as_posix(),
        "raw_sha256": _sha256(claim_raw),
    }:
        _add(errors, "terminal_claim_binding_invalid")
    if terminal.get("later_gates") != EXPECTED_LATER_GATES:
        _add(errors, "later_gates_invalid")

    counts = terminal.get("counts")
    if not isinstance(counts, dict):
        _add(errors, "terminal_counts_invalid")
    else:
        for counter, expected in ZERO_COUNTERS.items():
            if counts.get(counter) != expected:
                _add(errors, f"nonzero_counter:{counter}")
    for field in ("attempted_task_ids", "dispatch_receipts", "raw_finals"):
        if terminal.get(field) != []:
            _add(errors, f"terminal_activity_present:{field}")
    if terminal.get("later_batches_not_started") != list(protocol.BATCH_ORDER[1:]):
        _add(errors, "later_batches_not_closed")
    _decode_failure_evidence(terminal, errors)


def _validate_absence(
    *,
    results_base: Path,
    results_manifest_path: Path,
    platform_observations_path: Path,
    errors: list[str],
) -> None:
    if results_base.exists():
        _add(errors, "result_root_present")
        if results_base.is_dir():
            if any(results_base.rglob("dispatch-receipt.json")):
                _add(errors, "dispatch_receipt_present")
            if any(results_base.rglob("raw-final.txt")):
                _add(errors, "raw_final_present")
    if results_manifest_path.exists():
        _add(errors, "results_manifest_present")
    if platform_observations_path.exists():
        _add(errors, "platform_observations_present")


def _counter(terminal: dict[str, Any], name: str) -> int:
    counts = terminal.get("counts")
    value = counts.get(name) if isinstance(counts, dict) else None
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def audit_terminal(
    repo_root: Path = REPO_ROOT,
    *,
    claim_path: Path | None = None,
    terminal_path: Path | None = None,
    results_base: Path | None = None,
    results_manifest_path: Path | None = None,
    platform_observations_path: Path | None = None,
    verify_git: bool = True,
) -> dict[str, object]:
    """Return one deterministic terminal-preservation result without writing."""

    repo_root = repo_root.resolve()
    claim_path = claim_path or (repo_root / protocol.CLAIM_RELATIVE)
    terminal_path = terminal_path or (repo_root / protocol.TERMINAL_RELATIVE)
    results_base = results_base or (repo_root / protocol.RESULTS_BASE_RELATIVE)
    results_manifest_path = results_manifest_path or (
        repo_root / protocol.RESULTS_MANIFEST_RELATIVE
    )
    platform_observations_path = platform_observations_path or (
        repo_root / PLATFORM_OBSERVATIONS_RELATIVE
    )
    errors: list[str] = []

    claim, claim_raw = _load_object(claim_path, "launch_claim", errors)
    terminal, terminal_raw = _load_object(terminal_path, "execution_terminal", errors)
    claim_hash = _sha256(claim_raw) if claim_raw else None
    terminal_hash = _sha256(terminal_raw) if terminal_raw else None
    if len(claim_raw) != CLAIM_BYTE_LENGTH:
        _add(errors, "claim_byte_length_mismatch")
    if claim_hash != CLAIM_SHA256:
        _add(errors, "claim_sha256_mismatch")
    if len(terminal_raw) != TERMINAL_BYTE_LENGTH:
        _add(errors, "terminal_byte_length_mismatch")
    if terminal_hash != TERMINAL_SHA256:
        _add(errors, "terminal_sha256_mismatch")

    _validate_claim(claim, errors)
    _validate_terminal(terminal, claim=claim, claim_raw=claim_raw, errors=errors)
    _validate_absence(
        results_base=results_base,
        results_manifest_path=results_manifest_path,
        platform_observations_path=platform_observations_path,
        errors=errors,
    )

    try:
        protocol_result = protocol.audit_execution(
            repo_root,
            claim_path=claim_path,
            results_base=results_base,
            terminal_path=terminal_path,
            results_manifest_path=results_manifest_path,
            verify_git=False,
        )
    except (OSError, RuntimeError, TypeError, ValueError):
        protocol_result = {}
        _add(errors, "protocol_audit_exception")
    for code in protocol_result.get("errors", []):
        _add(errors, f"protocol:{code}")
    if protocol_result.get("status") != "STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE":
        _add(errors, "protocol_status_invalid")
    if protocol_result.get("token") != "CONSUMED":
        _add(errors, "protocol_token_not_consumed")
    for counter in ZERO_COUNTERS:
        if protocol_result.get(counter) != 0:
            _add(errors, f"protocol_nonzero_counter:{counter}")
    if protocol_result.get("launch_claim_present") is not True:
        _add(errors, "protocol_claim_not_present")
    if protocol_result.get("terminal_present") is not True:
        _add(errors, "protocol_terminal_not_present")
    if protocol_result.get("result_root_count") != 0:
        _add(errors, "protocol_result_root_present")
    if protocol_result.get("successor_revision_required") is not True:
        _add(errors, "protocol_successor_revision_not_required")

    if verify_git:
        _verify_git_preservation(
            repo_root,
            claim_path=claim_path,
            terminal_path=terminal_path,
            claim_raw=claim_raw,
            terminal_raw=terminal_raw,
            errors=errors,
        )

    return {
        "aggregation_calls": _counter(terminal, "aggregation_calls"),
        "attempts": _counter(terminal, "attempts"),
        "claim_count": claim.get("claim_count"),
        "claim_id": claim.get("claim_id"),
        "claim_sha256": claim_hash,
        "errors": sorted(errors),
        "failed_stage": terminal.get("failed_stage"),
        "finalizations": _counter(terminal, "finalizations"),
        "followups": _counter(terminal, "followups"),
        "judge_calls": _counter(terminal, "judge_calls"),
        "repairs": _counter(terminal, "repairs"),
        "result_root_count": 1 if results_base.exists() else 0,
        "results": _counter(terminal, "results"),
        "retries": _counter(terminal, "retries"),
        "side_effects": _counter(terminal, "side_effects"),
        "status": STATUS if not errors else "INVALID",
        "successor_revision_required": terminal.get("successor_revision_required")
        is True,
        "tasks": _counter(terminal, "tasks"),
        "terminal_sha256": terminal_hash,
        "threads": _counter(terminal, "threads"),
        "token": "CONSUMED"
        if isinstance(claim.get("authorization"), dict)
        and claim["authorization"].get("token_status_after_claim") == "CONSUMED"
        else "INVALID",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Audit the immutable stopped M4.1 terminal evidence."
    )
    parser.parse_args(argv)
    result = audit_terminal()
    print(json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=True))
    return 0 if result["status"] == STATUS and result["errors"] == [] else 1


if __name__ == "__main__":
    raise SystemExit(main())
