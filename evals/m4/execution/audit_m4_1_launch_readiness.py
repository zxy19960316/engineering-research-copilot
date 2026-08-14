#!/usr/bin/env python3
"""Read-only M4.1 Gate IV-B launch-readiness audit."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


EXECUTION_ROOT = Path(__file__).resolve().parent
REPO_ROOT = EXECUTION_ROOT.parents[2]
if str(EXECUTION_ROOT) not in sys.path:
    sys.path.insert(0, str(EXECUTION_ROOT))

import audit_m4_1 as protocol  # noqa: E402
import build_m4_1_launch_claim as claim  # noqa: E402
import record_m4_1_execution_evidence as recorder  # noqa: E402


REVIEW_PATH = claim.REVIEW_PATH
REVIEW_KEYS = claim.REVIEW_KEYS
AUTHORIZATION_HEAD = claim.AUTHORIZATION_HEAD
PROTOCOL_HEAD = claim.PROTOCOL_HEAD
REQUEST_AGGREGATE = claim.REQUEST_AGGREGATE
DOES_NOT_AUTHORIZE = claim.DOES_NOT_AUTHORIZE


def _add(errors: list[str], code: str) -> None:
    if code not in errors:
        errors.append(code)


def audit_launch_readiness(
    repo_root: Path = REPO_ROOT,
    *,
    review_path: Path = REVIEW_PATH,
    verify_git: bool = True,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    errors: list[str] = []
    try:
        review_raw = review_path.read_bytes()
        review = protocol.parse_json_object(review_raw)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError):
        review_raw = b""
        review = {}
        _add(errors, "gate_iv_b_review_unavailable_or_invalid")
    if review_raw and review_raw != protocol.canonical_bytes(review) + b"\n":
        _add(errors, "gate_iv_b_review_not_canonical")
    for code in claim.validate_review(review):
        _add(errors, code)
    if verify_git:
        for code in claim._protocol_errors(repo_root):
            _add(errors, code)

    claim_first = claim.check_claim_readiness(
        repo_root,
        review_path=review_path,
        verify_git=verify_git,
    )
    if claim_first.get("status") != "READY_TO_CONSUME":
        for code in claim_first.get("errors", ["claim_writer_check_failed"]):
            _add(errors, f"claim_writer:{code}")

    recorder_first = recorder.check_recorder(repo_root, verify_git=verify_git)
    if recorder_first.get("status") != "READY_UNCLAIMED":
        for code in recorder_first.get("errors", ["evidence_writer_check_failed"]):
            _add(errors, f"evidence_writer:{code}")

    real_targets = {
        "launch_claim": repo_root / protocol.CLAIM_RELATIVE,
        "execution_terminal": repo_root / protocol.TERMINAL_RELATIVE,
        "result_root": repo_root / protocol.RESULTS_BASE_RELATIVE,
        "results_manifest": repo_root / protocol.RESULTS_MANIFEST_RELATIVE,
        "platform_observations": repo_root / recorder.PLATFORM_OBSERVATIONS_RELATIVE,
    }
    for label, path in real_targets.items():
        if path.exists():
            _add(errors, f"gate_iv_b_target_present:{label}")

    try:
        template_first = claim.build_claim(
            repo_root, claimed_at_utc="2000-01-01T00:00:00Z"
        )
        template_second = claim.build_claim(
            repo_root, claimed_at_utc="2000-01-01T00:00:00Z"
        )
        writers_deterministic = protocol.canonical_bytes(
            template_first
        ) == protocol.canonical_bytes(template_second)
    except (KeyError, OSError, TypeError, UnicodeError, ValueError):
        writers_deterministic = False
    if not writers_deterministic:
        _add(errors, "claim_writer_check_nondeterministic")

    authorization_status = (
        "READY_UNCONSUMED"
        if claim_first.get("status") == "READY_TO_CONSUME"
        else "INVALID"
    )
    execution_status = str(recorder_first.get("status"))
    return {
        "status": "READY_FOR_ATOMIC_CLAIM" if not errors else "INVALID",
        "errors": sorted(errors),
        "protocol_review": review.get("protocol", {}).get("review")
        if isinstance(review.get("protocol"), dict)
        else None,
        "authorization_immutability": (
            review.get("exit_conditions", {}).get("authorization_immutability")
            if isinstance(review.get("exit_conditions"), dict)
            else None
        ),
        "authorization_audit": authorization_status,
        "execution_audit": execution_status,
        "writer_check": (
            "DETERMINISTIC"
            if writers_deterministic
            else "NONDETERMINISTIC"
        ),
        "token": "UNCONSUMED",
        "launch_claim": (
            "ABSENT" if not real_targets["launch_claim"].exists() else "PRESENT"
        ),
        "result_root": (
            "ABSENT" if not real_targets["result_root"].exists() else "PRESENT"
        ),
        "terminal": (
            "ABSENT"
            if not real_targets["execution_terminal"].exists()
            else "PRESENT"
        ),
        "platform_observations": (
            "ABSENT"
            if not real_targets["platform_observations"].exists()
            else "PRESENT"
        ),
        "protocol_head": PROTOCOL_HEAD,
        "protocol_ci_run_id": claim.PROTOCOL_CI_RUN_ID,
        "request_binding_aggregate_sha256": REQUEST_AGGREGATE,
        "tasks": 0,
        "finalizations": 0,
        "network_calls": 0,
        "writes": 0,
        "later_gates_authorized": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args(argv)
    del arguments
    result = audit_launch_readiness(REPO_ROOT)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0 if result["status"] == "READY_FOR_ATOMIC_CLAIM" else 1


if __name__ == "__main__":
    raise SystemExit(main())
