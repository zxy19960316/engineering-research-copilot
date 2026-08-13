#!/usr/bin/env python3
"""Build or, under separate Gate B authority, exclusively consume M4.2 claim.

The default mode is check-only.  Gate A tests exercise --consume only against
synthetic temporary roots.  No repository claim is created by Gate A.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import audit_m4_2 as protocol


@dataclass(frozen=True)
class GateAAcceptance:
    candidate_head: str
    candidate_tree: str
    push_run_id: int
    pr_run_id: int
    decision: str = "APPROVE_M4_2_ATOMIC_WHOLE_MATRIX_CLAIM_AND_EXECUTION_ONLY"

    def as_json(self) -> dict[str, Any]:
        return {
            "candidate_head": self.candidate_head,
            "candidate_tree": self.candidate_tree,
            "push_run_id": self.push_run_id,
            "push_conclusion": "success",
            "pr_run_id": self.pr_run_id,
            "pr_conclusion": "success",
            "decision": self.decision,
        }


def validate_gate_a_acceptance(value: GateAAcceptance) -> list[str]:
    errors: list[str] = []
    if protocol.OID_RE.fullmatch(value.candidate_head) is None:
        errors.append("gate_a_candidate_head_invalid")
    if protocol.OID_RE.fullmatch(value.candidate_tree) is None:
        errors.append("gate_a_candidate_tree_invalid")
    if not protocol._is_int(value.push_run_id) or value.push_run_id <= 0:
        errors.append("gate_a_push_run_id_invalid")
    if not protocol._is_int(value.pr_run_id) or value.pr_run_id <= 0:
        errors.append("gate_a_pr_run_id_invalid")
    if value.decision != "APPROVE_M4_2_ATOMIC_WHOLE_MATRIX_CLAIM_AND_EXECUTION_ONLY":
        errors.append("gate_a_decision_invalid")
    return errors


def _batch_claims(control: Mapping[str, Any]) -> list[dict[str, Any]]:
    by_id = {
        item["batch_id"]: item
        for item in control.get("batches", [])
        if isinstance(item, dict) and isinstance(item.get("batch_id"), str)
    }
    result: list[dict[str, Any]] = []
    for sequence, batch_id in enumerate(protocol.BATCH_ORDER, start=1):
        source = by_id.get(batch_id)
        if not isinstance(source, dict):
            raise protocol.ContractError("control_batch_missing")
        result.append(
            {
                "batch_id": batch_id,
                "sequence": sequence,
                "planned_task_count": 10,
                "task_ids": list(source["task_ids"]),
            }
        )
    return result


def build_claim(
    repo_root: Path,
    *,
    gate_a: GateAAcceptance,
    claimed_at_utc: str,
    verify_git: bool = True,
    enforce_frozen_hashes: bool = True,
    authorization_path: Path | None = None,
    control_path: Path | None = None,
) -> dict[str, Any]:
    gate_errors = validate_gate_a_acceptance(gate_a)
    if gate_errors:
        raise protocol.ContractError(gate_errors[0])
    if protocol.ISO_UTC_RE.fullmatch(claimed_at_utc) is None:
        raise protocol.ContractError("claimed_at_utc_invalid")
    (
        authorization,
        control,
        authorization_raw,
        control_raw,
        tasks,
        errors,
    ) = protocol.load_frozen_inputs(
        repo_root,
        policy=protocol.FrozenPolicy(
            enforce_raw_hashes=enforce_frozen_hashes,
            verify_git=verify_git,
        ),
        authorization_path=authorization_path,
        control_path=control_path,
    )
    if errors:
        raise protocol.ContractError(errors[0])
    task_claims = protocol._claim_task_expectations(
        tasks,
        protocol.sha256(authorization_raw),
        protocol.sha256(control_raw),
        gate_a.candidate_head,
    )
    token = authorization.get("authorization_token")
    if not isinstance(token, str):
        raise protocol.ContractError("authorization_token_invalid")
    return {
        "schema_version": "m4.2-launch-claim-v1",
        "milestone": protocol.MILESTONE,
        "revision": protocol.REVISION,
        "status": "CLAIMED",
        "claim_id": protocol.deterministic_claim_id(
            protocol.sha256(authorization_raw),
            protocol.sha256(control_raw),
            gate_a.candidate_head,
        ),
        "claimed_at_utc": claimed_at_utc,
        "claim_count": 1,
        "creation_semantics": {
            "mechanism": "python_os_open_O_CREAT_O_EXCL",
            "target_path": protocol.CLAIM_RELATIVE.as_posix(),
            "target_preexisted": False,
            "overwrite_allowed": False,
        },
        "authorization": {
            "closure_head": protocol.AUTHORIZATION_CLOSURE_HEAD,
            "closure_tree": protocol.AUTHORIZATION_CLOSURE_TREE,
            "branch": protocol.AUTHORIZATION_BRANCH,
            "execution_authorization": {
                "path": protocol.AUTHORIZATION_RELATIVE.as_posix(),
                "git_blob_oid": protocol.AUTHORIZATION_BLOB,
                "raw_sha256": protocol.sha256(authorization_raw),
            },
            "execution_control": {
                "path": protocol.CONTROL_RELATIVE.as_posix(),
                "git_blob_oid": protocol.CONTROL_BLOB,
                "raw_sha256": protocol.sha256(control_raw),
            },
            "token_fingerprint": protocol.token_fingerprint(token),
            "token_status_before_claim": "UNCONSUMED",
            "token_status_after_claim": "CONSUMED",
            "claim_consumes_entire_authorization": True,
        },
        "gate_a_acceptance": gate_a.as_json(),
        "project": {
            "project_id": protocol.PROJECT_ID,
            "is_git_repository": True,
            "environment": "worktree",
            "starting_branch": protocol.AUTHORIZATION_BRANCH,
            "starting_head": protocol.AUTHORIZATION_CLOSURE_HEAD,
        },
        "configured_defaults": {
            "exact_model_id": protocol.MODEL_ID,
            "reasoning_effort": protocol.REASONING_EFFORT,
            "configured_default_check": "MATCHED",
            "create_thread_model_field": "OMITTED",
            "create_thread_thinking_field": "OMITTED",
        },
        "request_binding_aggregate": {
            "algorithm": "sha256-canonical-json-task-request-bindings-v1",
            "ordered_pair_count": 60,
            "sha256": protocol.request_binding_aggregate(tasks),
        },
        "batch_order": list(protocol.BATCH_ORDER),
        "batches": _batch_claims(control),
        "task_ids": [str(task["task_id"]) for task in tasks],
        "task_claims": task_claims,
        "limits": dict(protocol.CLAIM_LIMITS),
        "permissions_still_closed": list(protocol.PERMISSIONS_STILL_CLOSED),
    }


def check_claim_readiness(
    repo_root: Path = protocol.REPO_ROOT,
    *,
    claim_path: Path | None = None,
    observations_base: Path | None = None,
    results_base: Path | None = None,
    terminal_path: Path | None = None,
    results_manifest_path: Path | None = None,
    m5_path: Path | None = None,
    verify_git: bool = True,
    enforce_frozen_hashes: bool = True,
    authorization_path: Path | None = None,
    control_path: Path | None = None,
) -> dict[str, Any]:
    state = protocol.audit_execution(
        repo_root,
        claim_path=claim_path,
        observations_base=observations_base,
        results_base=results_base,
        terminal_path=terminal_path,
        results_manifest_path=results_manifest_path,
        m5_path=m5_path,
        verify_git=verify_git,
        enforce_frozen_hashes=enforce_frozen_hashes,
        authorization_path=authorization_path,
        control_path=control_path,
    )
    status = "READY_TO_CONSUME" if state.get("status") == "READY_UNCLAIMED" else "INVALID"
    return {
        "status": status,
        "mode": "CHECK_ONLY",
        "errors": list(state.get("errors", [])),
        "token": state.get("token"),
        "claim": "ABSENT" if not state.get("launch_claim_present") else "PRESENT",
        "tasks": state.get("tasks"),
        "finalizations": state.get("finalizations"),
        "result_root_count": state.get("result_root_count"),
        "writes": 0,
    }


def _git_text(repo_root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "--no-replace-objects", *args],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def verify_remote_heads(repo_root: Path, gate_a: GateAAcceptance) -> list[str]:
    """Gate B live check. Gate A never calls this with a real write."""
    errors: list[str] = []
    authorization_remote = _git_text(
        repo_root,
        "ls-remote",
        "--heads",
        "origin",
        f"refs/heads/{protocol.AUTHORIZATION_BRANCH}",
    )
    if authorization_remote is None or not authorization_remote.startswith(
        protocol.AUTHORIZATION_CLOSURE_HEAD + "\t"
    ):
        errors.append("authorization_remote_head_mismatch")
    candidate_remote = _git_text(
        repo_root,
        "ls-remote",
        "--heads",
        "origin",
        f"refs/heads/{protocol.EXECUTION_BRANCH}",
    )
    if candidate_remote is None or not candidate_remote.startswith(
        gate_a.candidate_head + "\t"
    ):
        errors.append("gate_a_remote_head_mismatch")
    observed_tree = _git_text(
        repo_root, "rev-parse", f"{gate_a.candidate_head}^{{tree}}"
    )
    if observed_tree != gate_a.candidate_tree:
        errors.append("gate_a_candidate_tree_mismatch")
    return errors


def _post_claim_failure_terminal(
    claim: Mapping[str, Any],
    claim_raw: bytes,
    *,
    recorded_at_utc: str,
    diagnostic: str,
) -> dict[str, Any]:
    gate_a = claim.get("gate_a_acceptance")
    if not isinstance(gate_a, dict):
        gate_a = {}
    raw = diagnostic.encode("utf-8")
    return {
        "schema_version": "m4.2-execution-terminal-v1",
        "milestone": protocol.MILESTONE,
        "revision": protocol.REVISION,
        "terminal_state": "STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE",
        "recorded_at_utc": recorded_at_utc,
        "launch_claim": {
            "claim_id": claim.get("claim_id"),
            "path": protocol.CLAIM_RELATIVE.as_posix(),
            "raw_sha256": protocol.sha256(claim_raw),
        },
        "gate_a_acceptance": {
            "candidate_head": gate_a.get("candidate_head"),
            "push_run_id": gate_a.get("push_run_id"),
            "pr_run_id": gate_a.get("pr_run_id"),
        },
        "batch_order": list(protocol.BATCH_ORDER),
        "last_completed_batch": None,
        "failed_batch": None,
        "failed_task_id": None,
        "failed_stage": "post_claim_execution_transition_validation",
        "attempted_task_ids": [],
        "dispatch_receipts": [],
        "create_thread_responses": [],
        "raw_finals": [],
        "counts": {
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
        },
        "failure_evidence": {
            "failure_class": "PROTOCOL_FAILURE",
            "raw_evidence_sha256": protocol.sha256(raw),
            "raw_evidence_byte_length": len(raw),
            "raw_evidence_path": None,
            "diagnostic": diagnostic,
        },
        "later_batches_not_started": list(protocol.BATCH_ORDER),
        "successor_revision_required": True,
        "permissions_still_closed": list(protocol.PERMISSIONS_STILL_CLOSED),
    }


def consume_claim(
    repo_root: Path,
    *,
    gate_a: GateAAcceptance,
    claimed_at_utc: str,
    claim_path: Path | None = None,
    observations_base: Path | None = None,
    results_base: Path | None = None,
    terminal_path: Path | None = None,
    results_manifest_path: Path | None = None,
    m5_path: Path | None = None,
    verify_git: bool = True,
    verify_live: bool = True,
    enforce_frozen_hashes: bool = True,
    authorization_path: Path | None = None,
    control_path: Path | None = None,
) -> dict[str, Any]:
    defaults = protocol.default_paths(repo_root)
    claim_path = claim_path or defaults.claim
    observations_base = observations_base or defaults.observations
    results_base = results_base or defaults.results
    terminal_path = terminal_path or defaults.terminal
    results_manifest_path = results_manifest_path or defaults.results_manifest
    m5_path = m5_path or defaults.m5
    if claim_path.exists():
        return {
            "status": "ALREADY_CLAIMED",
            "errors": ["claim_target_preexists"],
            "writes": 0,
        }
    readiness = check_claim_readiness(
        repo_root,
        claim_path=claim_path,
        observations_base=observations_base,
        results_base=results_base,
        terminal_path=terminal_path,
        results_manifest_path=results_manifest_path,
        m5_path=m5_path,
        verify_git=verify_git,
        enforce_frozen_hashes=enforce_frozen_hashes,
        authorization_path=authorization_path,
        control_path=control_path,
    )
    if readiness["status"] != "READY_TO_CONSUME":
        return readiness
    if verify_live:
        live_errors = verify_remote_heads(repo_root, gate_a)
        if live_errors:
            return {
                "status": "INVALID",
                "errors": live_errors,
                "writes": 0,
            }
    claim = build_claim(
        repo_root,
        gate_a=gate_a,
        claimed_at_utc=claimed_at_utc,
        verify_git=verify_git,
        enforce_frozen_hashes=enforce_frozen_hashes,
        authorization_path=authorization_path,
        control_path=control_path,
    )
    try:
        claim_raw = protocol.exclusive_create_json(claim_path, claim)
    except FileExistsError:
        return {
            "status": "ALREADY_CLAIMED",
            "errors": ["claim_target_preexists"],
            "writes": 0,
        }

    # Critical M4.1 regression guard: after O_EXCL succeeds, confirmation uses
    # only the post-claim execution auditor.  The pre-claim authorization
    # auditor is intentionally not imported or called here.
    post_claim = protocol.audit_execution(
        repo_root,
        claim_path=claim_path,
        observations_base=observations_base,
        results_base=results_base,
        terminal_path=terminal_path,
        results_manifest_path=results_manifest_path,
        m5_path=m5_path,
        verify_git=verify_git,
        enforce_frozen_hashes=enforce_frozen_hashes,
        authorization_path=authorization_path,
        control_path=control_path,
    )
    if post_claim.get("status") == "CLAIMED_IN_PROGRESS" and not post_claim.get("errors"):
        return {
            **post_claim,
            "execution_auditor": "CLAIMED_IN_PROGRESS",
            "preclaim_authorization_auditor_reused": False,
            "writes": 1,
        }
    diagnostic = "post-claim execution auditor rejected the claimed transition"
    terminal = _post_claim_failure_terminal(
        claim,
        claim_raw,
        recorded_at_utc=claimed_at_utc,
        diagnostic=diagnostic,
    )
    try:
        protocol.exclusive_create_json(terminal_path, terminal)
    except FileExistsError:
        pass
    stopped = protocol.audit_execution(
        repo_root,
        claim_path=claim_path,
        observations_base=observations_base,
        results_base=results_base,
        terminal_path=terminal_path,
        results_manifest_path=results_manifest_path,
        m5_path=m5_path,
        verify_git=verify_git,
        enforce_frozen_hashes=enforce_frozen_hashes,
        authorization_path=authorization_path,
        control_path=control_path,
    )
    return {
        **stopped,
        "execution_auditor": post_claim.get("status"),
        "preclaim_authorization_auditor_reused": False,
        "writes": 2,
    }


def _compact(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true")
    group.add_argument("--consume", action="store_true")
    parser.add_argument("--gate-a-head")
    parser.add_argument("--gate-a-tree")
    parser.add_argument("--gate-a-push-run-id", type=int)
    parser.add_argument("--gate-a-pr-run-id", type=int)
    parser.add_argument("--claimed-at-utc")
    args = parser.parse_args(argv)
    if not args.consume:
        result = check_claim_readiness(protocol.REPO_ROOT)
        print(_compact(result))
        return 0 if result["status"] == "READY_TO_CONSUME" else 1
    required = (
        args.gate_a_head,
        args.gate_a_tree,
        args.gate_a_push_run_id,
        args.gate_a_pr_run_id,
        args.claimed_at_utc,
    )
    if any(value is None for value in required):
        parser.error("--consume requires exact Gate A head/tree, push/PR runs, and timestamp")
    gate_a = GateAAcceptance(
        candidate_head=args.gate_a_head,
        candidate_tree=args.gate_a_tree,
        push_run_id=args.gate_a_push_run_id,
        pr_run_id=args.gate_a_pr_run_id,
    )
    result = consume_claim(
        protocol.REPO_ROOT,
        gate_a=gate_a,
        claimed_at_utc=args.claimed_at_utc,
    )
    print(_compact(result))
    return 0 if result.get("status") == "CLAIMED_IN_PROGRESS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
