#!/usr/bin/env python3
"""Build the single M4.1 launch claim; default execution is check-only."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any


EXECUTION_ROOT = Path(__file__).resolve().parent
REPO_ROOT = EXECUTION_ROOT.parents[2]
AUTHORIZATION_ROOT = REPO_ROOT / "evals" / "m4" / "authorization"
if str(EXECUTION_ROOT) not in sys.path:
    sys.path.insert(0, str(EXECUTION_ROOT))
if str(AUTHORIZATION_ROOT) not in sys.path:
    sys.path.insert(0, str(AUTHORIZATION_ROOT))

import audit_m4_1 as protocol  # noqa: E402
import audit_m4_1_authorization as authorization_audit  # noqa: E402


AUTHORIZATION_HEAD = protocol.AUTHORIZATION_HEAD
AUTHORIZATION_BRANCH = protocol.AUTHORIZATION_BRANCH
AUTHORIZATION_CI_RUN_ID = protocol.AUTHORIZATION_CI_RUN_ID
AUTHORIZATION_TOKEN = protocol.AUTHORIZATION_TOKEN
PROTOCOL_HEAD = "bb1b8a5e4bab46d625c637d564d8132dc69a21ab"
PROTOCOL_BRANCH = protocol.EXECUTION_BRANCH
PROTOCOL_CI_RUN_ID = 31255966197
PROTOCOL_JOBS = (
    ("validate", 93099235968),
    ("historical-audit-cross-platform (ubuntu-latest)", 93099235987),
    ("historical-audit-cross-platform (windows-latest)", 93099235994),
)
REQUEST_AGGREGATE = "bccd78e80c338818929b825ca6624639529ba73d2817f22e63676b8aaeced500"
REVIEW_PATH = EXECUTION_ROOT / "m4.1" / "gate-iv-b-review.json"
PLATFORM_OBSERVATIONS_RELATIVE = Path(
    "evals/m4/execution/m4.1/platform-observations"
)
DOES_NOT_AUTHORIZE = (
    "launch_claim_creation",
    "fresh_task_dispatch",
    "judge_execution",
    "blind_mapping_access",
    "unblinding",
    "aggregation",
    "threshold_decision",
    "m4_closure",
    "m5",
)
REVIEW_KEYS = {
    "schema_version",
    "milestone",
    "revision",
    "gate",
    "reviewed_at_utc",
    "decision",
    "findings",
    "authorization",
    "protocol",
    "branch_immutability",
    "request_binding_aggregate",
    "writer_contract",
    "exit_conditions",
    "does_not_authorize",
}
_CHECK_TIMESTAMP = "2000-01-01T00:00:00Z"
_CLAIM_NAMESPACE = uuid.UUID("18300bd0-130c-4f37-8330-045933dbb46f")


def _add(errors: list[str], code: str) -> None:
    if code not in errors:
        errors.append(code)


def _valid_timestamp(value: object) -> bool:
    return isinstance(value, str) and protocol._valid_timestamp(value)


def _load_review(path: Path = REVIEW_PATH) -> tuple[dict[str, Any], bytes, list[str]]:
    errors: list[str] = []
    try:
        raw = path.read_bytes()
        value = protocol.parse_json_object(raw)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError):
        return {}, b"", ["gate_iv_b_review_unavailable_or_invalid"]
    if raw != protocol.canonical_bytes(value) + b"\n":
        _add(errors, "gate_iv_b_review_not_canonical")
    return value, raw, errors


def validate_review(value: object) -> list[str]:
    if not isinstance(value, dict):
        return ["gate_iv_b_review_object_required"]
    errors: list[str] = []
    if set(value) != REVIEW_KEYS:
        _add(errors, "gate_iv_b_review_fields_invalid")
    expected_scalars = {
        "schema_version": "m4.1-gate-iv-b-launch-readiness-review-v1",
        "milestone": "M4",
        "revision": "M4.1",
        "gate": "IV-B",
        "decision": "PASSED",
        "findings": [],
        "does_not_authorize": list(DOES_NOT_AUTHORIZE),
    }
    for field, expected in expected_scalars.items():
        if value.get(field) != expected:
            _add(errors, f"gate_iv_b_review_field_invalid:{field}")
    if not _valid_timestamp(value.get("reviewed_at_utc")):
        _add(errors, "gate_iv_b_review_timestamp_invalid")
    expected_authorization = {
        "branch": AUTHORIZATION_BRANCH,
        "ci_conclusion": "success",
        "ci_run_id": AUTHORIZATION_CI_RUN_ID,
        "claim_count": 0,
        "head": AUTHORIZATION_HEAD,
        "token": AUTHORIZATION_TOKEN,
        "token_status": "UNCONSUMED",
    }
    if value.get("authorization") != expected_authorization:
        _add(errors, "gate_iv_b_authorization_binding_invalid")
    expected_protocol = {
        "branch": PROTOCOL_BRANCH,
        "ci_conclusion": "success",
        "ci_run_id": PROTOCOL_CI_RUN_ID,
        "head": PROTOCOL_HEAD,
        "jobs": [
            {"conclusion": "success", "job_id": job_id, "name": name}
            for name, job_id in PROTOCOL_JOBS
        ],
        "review": "PASSED",
    }
    if value.get("protocol") != expected_protocol:
        _add(errors, "gate_iv_b_protocol_binding_invalid")
    immutability = value.get("branch_immutability")
    expected_immutability = {
        "active_repository_rulesets": 0,
        "authorization_branch_protected": False,
        "baseline_commit_object": AUTHORIZATION_HEAD,
        "create_thread_starting_branch": AUTHORIZATION_BRANCH,
        "expected_resolved_checkout_sha": AUTHORIZATION_HEAD,
        "failure_policy": "fail_closed_before_dispatch_or_stop_after_claim",
        "frozen_authorization_paths_source_head": AUTHORIZATION_HEAD,
        "mechanism": "immutable-start-equivalent-v1",
        "pre_consume_remote_ref_recheck_required": True,
        "remote_ref": f"refs/heads/{AUTHORIZATION_BRANCH}",
        "remote_ref_head": AUTHORIZATION_HEAD,
        "resolved_checkout_sha_policy": "require_exact_if_exposed",
    }
    if not isinstance(immutability, dict):
        _add(errors, "gate_iv_b_immutability_invalid")
    else:
        checked_at = immutability.get("remote_ref_checked_at_utc")
        without_time = dict(immutability)
        without_time.pop("remote_ref_checked_at_utc", None)
        if without_time != expected_immutability or not _valid_timestamp(checked_at):
            _add(errors, "gate_iv_b_immutability_invalid")
    if value.get("request_binding_aggregate") != {
        "algorithm": "sha256-canonical-json-task-request-bindings-v1",
        "ordered_pair_count": 60,
        "sha256": REQUEST_AGGREGATE,
    }:
        _add(errors, "gate_iv_b_request_aggregate_invalid")
    if value.get("writer_contract") != {
        "aggregate": False,
        "canonical_response_hash": "REQUIRED",
        "check_deterministic": True,
        "claim_exclusive": True,
        "consume_mode": "--consume",
        "coordinator_exception": "STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE",
        "default_mode": "--check",
        "delete": False,
        "judge": False,
        "model_field": "OMITTED",
        "overwrite": False,
        "raw_create_thread_response": "PRESERVE_EXACT_BYTES",
        "raw_final_exclusive": True,
        "receipt_exclusive": True,
        "resolved_checkout_sha": "REQUIRE_EXACT_IF_EXPOSED",
        "results_manifest": False,
        "rollback": False,
        "target_directory_exclusive": True,
        "terminal_exclusive": True,
        "thinking_field": "OMITTED",
        "write_primitive": "os.open(O_CREAT|O_EXCL)",
    }:
        _add(errors, "gate_iv_b_writer_contract_invalid")
    if value.get("exit_conditions") != {
        "authorization_audit": "READY_UNCONSUMED",
        "authorization_immutability": "IMMUTABLE_START_EQUIVALENT_ESTABLISHED",
        "execution_audit": "READY_UNCLAIMED",
        "launch_claim": "ABSENT",
        "protocol_exact_head_ci": "PASSED",
        "protocol_head_run_binding": "EXACT",
        "protocol_review": "PASSED",
        "result_root": "ABSENT",
        "writer_check": "DETERMINISTIC",
    }:
        _add(errors, "gate_iv_b_exit_conditions_invalid")
    return sorted(errors)


def _git(repo_root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _protocol_errors(repo_root: Path) -> list[str]:
    return sorted(protocol._protocol_git_errors(repo_root, PROTOCOL_HEAD))


def _target_paths(
    repo_root: Path,
    *,
    claim_path: Path | None = None,
    terminal_path: Path | None = None,
    results_base: Path | None = None,
    results_manifest_path: Path | None = None,
    observations_base: Path | None = None,
) -> dict[str, Path]:
    return {
        "claim": claim_path or (repo_root / protocol.CLAIM_RELATIVE),
        "terminal": terminal_path or (repo_root / protocol.TERMINAL_RELATIVE),
        "result_root": results_base or (repo_root / protocol.RESULTS_BASE_RELATIVE),
        "results_manifest": results_manifest_path
        or (repo_root / protocol.RESULTS_MANIFEST_RELATIVE),
        "platform_observations": observations_base
        or (repo_root / PLATFORM_OBSERVATIONS_RELATIVE),
    }


def build_claim(
    repo_root: Path = REPO_ROOT,
    *,
    claimed_at_utc: str,
) -> dict[str, Any]:
    if not _valid_timestamp(claimed_at_utc):
        raise ValueError("claimed_at_utc_invalid")
    control = protocol.parse_json_object(protocol.CONTROL_PATH.read_bytes())
    tasks = protocol.ordered_tasks(control)
    if protocol.request_binding_aggregate(tasks) != REQUEST_AGGREGATE:
        raise ValueError("request_binding_aggregate_mismatch")
    seed = f"{AUTHORIZATION_TOKEN}|{PROTOCOL_HEAD}|M4.1"
    task_claims: list[dict[str, Any]] = []
    for task in tasks:
        task_id = str(task["task_id"])
        task_claims.append(
            {
                "task_id": task_id,
                "batch_id": task["batch_id"],
                "request_binding_sha256": task["request_binding_sha256"],
                "result_root": task["result_root"],
                "context_id": str(
                    uuid.uuid5(_CLAIM_NAMESPACE, f"{seed}|{task_id}|context")
                ),
                "finalization_id": str(
                    uuid.uuid5(_CLAIM_NAMESPACE, f"{seed}|{task_id}|finalization")
                ),
            }
        )
    value: dict[str, Any] = {
        "schema_version": "m4.1-launch-claim-v1",
        "milestone": "M4",
        "revision": "M4.1",
        "status": "CLAIMED",
        "claim_id": str(uuid.uuid5(_CLAIM_NAMESPACE, f"{seed}|claim")),
        "claimed_at_utc": claimed_at_utc,
        "claim_count": 1,
        "creation_semantics": {
            "mechanism": "python_os_open_O_CREAT_O_EXCL",
            "target_path": protocol.CLAIM_RELATIVE.as_posix(),
            "target_preexisted": False,
            "overwrite_allowed": False,
        },
        "authorization": {
            "head": AUTHORIZATION_HEAD,
            "branch": AUTHORIZATION_BRANCH,
            "ci_run_id": AUTHORIZATION_CI_RUN_ID,
            "ci_conclusion": "success",
            "token": AUTHORIZATION_TOKEN,
            "token_status_before_claim": "UNCONSUMED",
            "token_status_after_claim": "CONSUMED",
            "claim_consumes_entire_authorization": True,
        },
        "execution_protocol": {
            "head": PROTOCOL_HEAD,
            "branch": PROTOCOL_BRANCH,
            "ci_run_id": PROTOCOL_CI_RUN_ID,
            "ci_conclusion": "success",
        },
        "project": {
            "project_id": protocol.PROJECT_ID,
            "is_git_repository": True,
            "environment": "worktree",
            "starting_branch": AUTHORIZATION_BRANCH,
            "starting_head": AUTHORIZATION_HEAD,
        },
        "configured_defaults": {
            "exact_model_id": protocol.MODEL_ID,
            "reasoning_effort": protocol.REASONING_EFFORT,
            "configured_default_check": "MATCHED",
            "create_thread_model_field": "OMITTED",
            "create_thread_thinking_field": "OMITTED",
        },
        "frozen_bindings": protocol._expected_frozen_bindings(),
        "request_binding_aggregate": {
            "algorithm": "sha256-canonical-json-task-request-bindings-v1",
            "ordered_pair_count": 60,
            "sha256": REQUEST_AGGREGATE,
        },
        "batch_order": list(protocol.BATCH_ORDER),
        "batches": protocol._expected_batches(control),
        "task_ids": [str(task["task_id"]) for task in tasks],
        "task_claims": task_claims,
        "limits": dict(protocol.CLAIM_LIMITS),
        "does_not_authorize": list(protocol.DOES_NOT_AUTHORIZE),
    }
    validation_errors: list[str] = []
    protocol._validate_claim(value, control, tasks, validation_errors)
    if validation_errors:
        raise ValueError("claim_build_invalid:" + ",".join(sorted(validation_errors)))
    return value


def exclusive_create_bytes(path: Path, raw: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = -1
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def exclusive_create_json(path: Path, value: dict[str, Any]) -> None:
    exclusive_create_bytes(path, protocol.canonical_bytes(value) + b"\n")


def check_claim_readiness(
    repo_root: Path = REPO_ROOT,
    *,
    review_path: Path = REVIEW_PATH,
    claim_path: Path | None = None,
    terminal_path: Path | None = None,
    results_base: Path | None = None,
    results_manifest_path: Path | None = None,
    observations_base: Path | None = None,
    verify_git: bool = True,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    targets = _target_paths(
        repo_root,
        claim_path=claim_path,
        terminal_path=terminal_path,
        results_base=results_base,
        results_manifest_path=results_manifest_path,
        observations_base=observations_base,
    )
    errors: list[str] = []
    review, _, load_errors = _load_review(review_path)
    errors.extend(load_errors)
    errors.extend(validate_review(review))
    for label, path in targets.items():
        if path.exists():
            _add(errors, f"target_present:{label}")
    if verify_git:
        errors.extend(_protocol_errors(repo_root))
    try:
        authorization = authorization_audit.audit_authorization(
            repo_root,
            launch_claim_path=targets["claim"],
            results_parent=targets["result_root"].parent,
            configured_model=protocol.MODEL_ID,
            configured_reasoning_effort=protocol.REASONING_EFFORT,
            verify_git=verify_git,
        )
    except (OSError, RuntimeError, TypeError, ValueError):
        authorization = {"status": "INVALID", "errors": ["audit_exception"]}
    if authorization.get("status") != "READY_UNCONSUMED":
        for code in authorization.get("errors", ["authorization_audit_failed"]):
            _add(errors, f"authorization_audit:{code}")
    try:
        execution = protocol.audit_execution(
            repo_root,
            claim_path=targets["claim"],
            results_base=targets["result_root"],
            terminal_path=targets["terminal"],
            results_manifest_path=targets["results_manifest"],
            verify_git=verify_git,
        )
    except (OSError, RuntimeError, TypeError, ValueError):
        execution = {"status": "INVALID", "errors": ["audit_exception"]}
    if execution.get("status") != "READY_UNCLAIMED":
        for code in execution.get("errors", ["execution_audit_failed"]):
            _add(errors, f"execution_audit:{code}")
    try:
        template = build_claim(repo_root, claimed_at_utc=_CHECK_TIMESTAMP)
        template_sha256 = protocol.canonical_sha256(template)
    except (KeyError, OSError, TypeError, UnicodeError, ValueError):
        template_sha256 = None
        _add(errors, "claim_template_build_failed")
    return {
        "status": "READY_TO_CONSUME" if not errors else "INVALID",
        "mode": "CHECK_ONLY",
        "errors": sorted(set(errors)),
        "token": "UNCONSUMED",
        "claim": "ABSENT" if not targets["claim"].exists() else "PRESENT",
        "result_root": (
            "ABSENT" if not targets["result_root"].exists() else "PRESENT"
        ),
        "terminal": "ABSENT" if not targets["terminal"].exists() else "PRESENT",
        "platform_observations": (
            "ABSENT"
            if not targets["platform_observations"].exists()
            else "PRESENT"
        ),
        "task_count": 60,
        "batch_count": 6,
        "request_binding_aggregate_sha256": REQUEST_AGGREGATE,
        "protocol_head": PROTOCOL_HEAD,
        "protocol_ci_run_id": PROTOCOL_CI_RUN_ID,
        "claim_template_canonical_sha256": template_sha256,
        "network_calls": 0,
        "writes": 0,
    }


def _ls_remote(repo_root: Path, branch: str) -> str | None:
    result = _git(repo_root, "ls-remote", "--heads", "origin", branch)
    if result.returncode != 0:
        return None
    rows = [line.split() for line in result.stdout.splitlines() if line.strip()]
    if len(rows) != 1 or len(rows[0]) != 2:
        return None
    return rows[0][0]


def _live_remote_errors(repo_root: Path) -> list[str]:
    errors: list[str] = []
    if _ls_remote(repo_root, AUTHORIZATION_BRANCH) != AUTHORIZATION_HEAD:
        _add(errors, "live_authorization_remote_ref_mismatch")
    if _ls_remote(repo_root, PROTOCOL_BRANCH) != PROTOCOL_HEAD:
        _add(errors, "live_protocol_remote_ref_mismatch")
    return errors


def _run_view(repo_root: Path, run_id: int) -> dict[str, Any] | None:
    result = subprocess.run(
        [
            "gh",
            "run",
            "view",
            str(run_id),
            "--repo",
            "zxy19960316/engineering-research-copilot",
            "--json",
            "databaseId,headSha,headBranch,status,conclusion,jobs",
        ],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        return None
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def _live_ci_errors(repo_root: Path) -> list[str]:
    errors: list[str] = []
    authorization = _run_view(repo_root, AUTHORIZATION_CI_RUN_ID)
    if not isinstance(authorization, dict) or (
        authorization.get("databaseId") != AUTHORIZATION_CI_RUN_ID
        or authorization.get("headSha") != AUTHORIZATION_HEAD
        or authorization.get("headBranch") != AUTHORIZATION_BRANCH
        or authorization.get("status") != "completed"
        or authorization.get("conclusion") != "success"
    ):
        _add(errors, "live_authorization_ci_attestation_invalid")
    execution = _run_view(repo_root, PROTOCOL_CI_RUN_ID)
    if not isinstance(execution, dict) or (
        execution.get("databaseId") != PROTOCOL_CI_RUN_ID
        or execution.get("headSha") != PROTOCOL_HEAD
        or execution.get("headBranch") != PROTOCOL_BRANCH
        or execution.get("status") != "completed"
        or execution.get("conclusion") != "success"
    ):
        _add(errors, "live_protocol_ci_attestation_invalid")
    else:
        actual_jobs = {
            (item.get("name"), item.get("databaseId"), item.get("conclusion"))
            for item in execution.get("jobs", [])
            if isinstance(item, dict)
        }
        expected_jobs = {(name, job_id, "success") for name, job_id in PROTOCOL_JOBS}
        if actual_jobs != expected_jobs:
            _add(errors, "live_protocol_ci_jobs_invalid")
    return errors


def consume_claim(
    repo_root: Path = REPO_ROOT,
    *,
    claimed_at_utc: str,
    review_path: Path = REVIEW_PATH,
    claim_path: Path | None = None,
    terminal_path: Path | None = None,
    results_base: Path | None = None,
    results_manifest_path: Path | None = None,
    observations_base: Path | None = None,
    verify_git: bool = True,
    verify_live: bool = True,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    targets = _target_paths(
        repo_root,
        claim_path=claim_path,
        terminal_path=terminal_path,
        results_base=results_base,
        results_manifest_path=results_manifest_path,
        observations_base=observations_base,
    )
    if targets["claim"].exists():
        return {
            "status": "ALREADY_CLAIMED",
            "errors": ["launch_claim_already_exists"],
            "token": "CONSUMED_OR_UNKNOWN",
            "claim": "PRESENT",
            "writes": 0,
        }
    readiness = check_claim_readiness(
        repo_root,
        review_path=review_path,
        claim_path=targets["claim"],
        terminal_path=targets["terminal"],
        results_base=targets["result_root"],
        results_manifest_path=targets["results_manifest"],
        observations_base=targets["platform_observations"],
        verify_git=verify_git,
    )
    errors = list(readiness.get("errors", []))
    if readiness.get("status") != "READY_TO_CONSUME":
        _add(errors, "claim_readiness_not_ready")
    if verify_live:
        errors.extend(_live_remote_errors(repo_root))
        errors.extend(_live_ci_errors(repo_root))
    if errors:
        return {
            "status": "INVALID",
            "errors": sorted(set(errors)),
            "token": "UNCONSUMED",
            "claim": "ABSENT",
            "writes": 0,
        }
    value = build_claim(repo_root, claimed_at_utc=claimed_at_utc)
    try:
        exclusive_create_json(targets["claim"], value)
    except FileExistsError:
        return {
            "status": "ALREADY_CLAIMED",
            "errors": ["launch_claim_already_exists"],
            "token": "CONSUMED_OR_UNKNOWN",
            "claim": "PRESENT",
            "writes": 0,
        }
    except OSError:
        return {
            "status": "INVALID",
            "errors": ["launch_claim_exclusive_create_failed"],
            "token": "UNCONSUMED",
            "claim": "ABSENT",
            "writes": 0,
        }
    execution = protocol.audit_execution(
        repo_root,
        claim_path=targets["claim"],
        results_base=targets["result_root"],
        terminal_path=targets["terminal"],
        results_manifest_path=targets["results_manifest"],
        verify_git=verify_git,
    )
    consumed_authorization = authorization_audit.audit_authorization(
        repo_root,
        launch_claim_path=targets["claim"],
        results_parent=targets["result_root"].parent,
        configured_model=protocol.MODEL_ID,
        configured_reasoning_effort=protocol.REASONING_EFFORT,
        verify_git=verify_git,
    )
    confirmed = (
        execution.get("status") == "CLAIMED_IN_PROGRESS"
        and execution.get("tasks") == 0
        and execution.get("finalizations") == 0
        and "authorization_already_claimed"
        in consumed_authorization.get("errors", [])
    )
    if not confirmed:
        try:
            import record_m4_1_execution_evidence as recorder

            first_task_id = str(value["task_ids"][0])
            stopped = recorder.record_terminal(
                repo_root,
                state="STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE",
                recorded_at_utc=claimed_at_utc,
                failed_task_id=first_task_id,
                failed_stage="post_claim_dual_confirmation",
                failure_class="PROTOCOL_FAILURE",
                failure_evidence_raw=protocol.canonical_bytes(
                    {
                        "code": "post_claim_dual_confirmation_failed",
                        "authorization_errors": consumed_authorization.get(
                            "errors", []
                        ),
                        "execution_status": execution.get("status"),
                        "execution_errors": execution.get("errors", []),
                    }
                ),
                attempt_included=False,
                claim_path=targets["claim"],
                results_base=targets["result_root"],
                terminal_path=targets["terminal"],
                results_manifest_path=targets["results_manifest"],
                observations_base=targets["platform_observations"],
                verify_git=verify_git,
            )
        except (ImportError, KeyError, OSError, TypeError, ValueError):
            stopped = {"status": "INVALID", "errors": ["stop_terminal_failed"]}
        return {
            "status": stopped.get("status", "INVALID"),
            "errors": sorted(
                set(
                    ["post_claim_dual_confirmation_failed"]
                    + list(stopped.get("errors", []))
                )
            ),
            "token": "CONSUMED",
            "claim": "PRESENT",
            "terminal": (
                "PRESENT" if targets["terminal"].is_file() else "ABSENT"
            ),
            "writes": 2 if targets["terminal"].is_file() else 1,
        }
    return {
        "status": "CLAIMED_IN_PROGRESS",
        "errors": [],
        "token": "CONSUMED",
        "claim": "PRESENT",
        "claim_id": value["claim_id"],
        "claim_raw_sha256": protocol.sha256(targets["claim"].read_bytes()),
        "authorization_auditor": "authorization_already_claimed",
        "execution_auditor": "CLAIMED_IN_PROGRESS",
        "tasks": 0,
        "finalizations": 0,
        "writes": 1,
    }


def _now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--consume", action="store_true")
    parser.add_argument("--claimed-at-utc")
    arguments = parser.parse_args(argv)
    if arguments.consume:
        result = consume_claim(
            REPO_ROOT,
            claimed_at_utc=arguments.claimed_at_utc or _now_utc(),
        )
    else:
        result = check_claim_readiness(REPO_ROOT)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0 if result["status"] in {"READY_TO_CONSUME", "CLAIMED_IN_PROGRESS"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
