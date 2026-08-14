from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
PREPARATION_HEAD = "c56c3c1ab384f65e51a70e9582672c6320d19121"
AUTHORIZATION_HEAD = "e3542201f96218f340a09f77458661822c98d876"
AUTHORIZATION_BRANCH = (
    "codex/m4-cross-engineering-forward-evaluation-one-shot-authorization"
)
CLAIM_RELATIVE = Path("evals/m4/execution/m4.0/launch-claim.json")
FAILURE_RELATIVE = Path("evals/m4/execution/m4.0/pre-dispatch-failure.json")
AUTHORIZATION_RELATIVE = Path(
    "evals/m4/authorization/execution-authorization.json"
)
CONTROL_RELATIVE = Path("evals/m4/authorization/execution-control.json")
PREPARATION_RELATIVE = Path("evals/m4/preparation-manifest.json")
RESULTS_BASE_RELATIVE = Path("evals/m4/results/m4.0")
RESULTS_MANIFEST_RELATIVE = Path("evals/m4/results-manifest.json")

CLAIM_KEYS = {
    "schema_version",
    "milestone",
    "revision",
    "status",
    "claim_id",
    "claimed_at_utc",
    "claim_count",
    "authorization_token",
    "authorization_token_status_after_claim",
    "claim_consumes_entire_matrix_authorization",
    "authorization_head",
    "authorization_branch",
    "coordinator_execution_head",
    "coordinator_execution_branch",
    "project",
    "configured_defaults",
    "frozen_bindings",
    "batch_ids",
    "task_ids",
    "limits",
    "prelaunch_counters",
}
FAILURE_KEYS = {
    "schema_version",
    "milestone",
    "revision",
    "status",
    "recorded_at_utc",
    "launch_claim",
    "failed_stage",
    "failure_class",
    "batch_id",
    "task_id",
    "raw_failure",
    "environment",
    "counters",
    "evidence_state",
    "unlaunched_batch_ids",
    "permissions_still_closed",
}
ZERO_COUNTERS = {
    "create_thread_calls": 0,
    "created_contexts": 0,
    "dispatched_tasks": 0,
    "finalizations": 0,
    "results_observed": 0,
    "retries": 0,
    "repairs": 0,
    "followup_messages": 0,
    "judge_contexts": 0,
    "unauthorized_side_effects": 0,
}
EXPECTED_RAW_FAILURE = {
    "exception_type": "System.Management.Automation.RuntimeException",
    "fully_qualified_error_id": "MethodNotFound",
    "message": (
        "Method invocation failed because [System.Convert] does not contain a "
        "method named 'ToHexString'."
    ),
    "failing_expression": "[Convert]::ToHexString($sha.ComputeHash($Bytes))",
}
FROZEN_M3_PATHS = ("skills/engineering-research-copilot", "evals/m3")
FROZEN_PREPARATION_PATHS = (
    "evals/m4/cases",
    "evals/m4/variants",
    "evals/m4/schemas",
    "evals/m4/preparation-manifest.json",
    "evals/m4/task-protocol.md",
    "evals/m4/judge-rubric.json",
)


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _add(errors: list[str], code: str) -> None:
    if code not in errors:
        errors.append(code)


def _load(path: Path, label: str, errors: list[str]) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
    except OSError:
        _add(errors, f"{label}_missing")
        return {}, b""
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError):
        _add(errors, f"{label}_invalid_json")
        return {}, raw
    if not isinstance(value, dict):
        _add(errors, f"{label}_invalid_shape")
        return {}, raw
    return value, raw


def _git(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def _changed_paths(base: str, paths: tuple[str, ...]) -> list[str]:
    result = _git("diff", "--name-only", base, "HEAD", "--", *paths)
    if result.returncode != 0:
        return ["git_diff_failed"]
    return sorted(line for line in result.stdout.splitlines() if line)


def _validate_claim(
    claim: dict[str, Any],
    authorization: dict[str, Any],
    control: dict[str, Any],
    errors: list[str],
) -> None:
    if set(claim) != CLAIM_KEYS:
        _add(errors, "claim_shape_invalid")
    expected_scalar = {
        "schema_version": "m4-launch-claim-v1",
        "milestone": "M4",
        "revision": "M4.0",
        "status": "CLAIMED",
        "claim_count": 1,
        "authorization_token_status_after_claim": "CONSUMED",
        "claim_consumes_entire_matrix_authorization": True,
        "authorization_head": AUTHORIZATION_HEAD,
        "authorization_branch": AUTHORIZATION_BRANCH,
    }
    for key, expected in expected_scalar.items():
        if claim.get(key) != expected:
            _add(errors, f"claim_{key}_invalid")
    token = authorization.get("authorization_token")
    if not isinstance(token, str) or claim.get("authorization_token") != token:
        _add(errors, "claim_authorization_token_invalid")

    authority = authorization.get("authority")
    expected_tasks = (
        authority.get("authorized_task_ids", []) if isinstance(authority, dict) else []
    )
    expected_batches = control.get("batch_order", [])
    if claim.get("task_ids") != expected_tasks or len(expected_tasks) != 60:
        _add(errors, "claim_task_roster_invalid")
    if claim.get("batch_ids") != expected_batches or len(expected_batches) != 6:
        _add(errors, "claim_batch_roster_invalid")

    defaults = claim.get("configured_defaults")
    expected_defaults = {
        "exact_model_id": "gpt-5.6-sol",
        "reasoning_effort": "max",
        "configured_default_check": "MATCHED",
        "create_thread_model_field": "OMITTED",
        "create_thread_thinking_field": "OMITTED",
    }
    if defaults != expected_defaults:
        _add(errors, "claim_configured_defaults_invalid")
    expected_limits = {
        "task_count": 60,
        "batch_count": 6,
        "attempts_per_task_id": 1,
        "retries": 0,
        "repairs": 0,
        "followup_messages": 0,
        "judge_contexts": 0,
    }
    if claim.get("limits") != expected_limits:
        _add(errors, "claim_limits_invalid")


def _validate_failure(
    failure: dict[str, Any],
    claim: dict[str, Any],
    claim_raw: bytes,
    errors: list[str],
) -> None:
    if set(failure) != FAILURE_KEYS:
        _add(errors, "failure_shape_invalid")
    expected_scalar = {
        "schema_version": "m4-pre-dispatch-failure-v1",
        "milestone": "M4",
        "revision": "M4.0",
        "status": "PRE_DISPATCH_FAILED",
        "failed_stage": "frozen_request_bundle_hash_verification",
        "failure_class": "coordinator_infrastructure_or_protocol_failure",
        "batch_id": "M4-BATCH-NUC",
        "task_id": None,
    }
    for key, expected in expected_scalar.items():
        if failure.get(key) != expected:
            _add(errors, f"failure_{key}_invalid")
    claim_binding = failure.get("launch_claim")
    if not isinstance(claim_binding, dict):
        _add(errors, "failure_claim_binding_invalid")
    else:
        if claim_binding.get("claim_id") != claim.get("claim_id"):
            _add(errors, "failure_claim_id_invalid")
        if claim_binding.get("claim_sha256") != _sha256(claim_raw):
            _add(errors, "failure_claim_hash_invalid")
        if claim_binding.get("authorization_token") != claim.get(
            "authorization_token"
        ):
            _add(errors, "failure_claim_token_invalid")
        if claim_binding.get("authorization_consumed") is not True:
            _add(errors, "failure_claim_consumption_invalid")
        if claim_binding.get("claim_count") != 1:
            _add(errors, "failure_claim_count_invalid")
    if failure.get("raw_failure") != EXPECTED_RAW_FAILURE:
        _add(errors, "raw_failure_invalid")
    if failure.get("counters") != ZERO_COUNTERS:
        _add(errors, "execution_counters_nonzero")
    evidence_state = failure.get("evidence_state")
    expected_evidence_state = {
        "result_root_count": 0,
        "fresh_task_result_state": "NOT_RUN",
        "raw_failure_preserved": True,
        "current_batch_stopped": True,
        "later_batches_stopped": True,
        "same_revision_resume_authorized": False,
        "successor_revision_required": True,
    }
    if evidence_state != expected_evidence_state:
        _add(errors, "failure_evidence_state_invalid")
    if failure.get("unlaunched_batch_ids") != claim.get("batch_ids"):
        _add(errors, "failure_unlaunched_batches_invalid")


def audit_execution(
    repo_root: Path = REPO_ROOT,
    *,
    claim_path: Path | None = None,
    failure_path: Path | None = None,
    results_base: Path | None = None,
    verify_git: bool = True,
) -> dict[str, object]:
    repo_root = repo_root.resolve()
    errors: list[str] = []
    claim_path = claim_path or (repo_root / CLAIM_RELATIVE)
    failure_path = failure_path or (repo_root / FAILURE_RELATIVE)
    results_base = results_base or (repo_root / RESULTS_BASE_RELATIVE)

    claim, claim_raw = _load(claim_path, "launch_claim", errors)
    failure, failure_raw = _load(failure_path, "pre_dispatch_failure", errors)
    authorization, authorization_raw = _load(
        repo_root / AUTHORIZATION_RELATIVE, "execution_authorization", errors
    )
    control, control_raw = _load(
        repo_root / CONTROL_RELATIVE, "execution_control", errors
    )
    preparation_path = repo_root / PREPARATION_RELATIVE
    try:
        preparation_raw = preparation_path.read_bytes()
    except OSError:
        preparation_raw = b""
        _add(errors, "preparation_manifest_missing")

    _validate_claim(claim, authorization, control, errors)
    _validate_failure(failure, claim, claim_raw, errors)

    frozen = claim.get("frozen_bindings")
    expected_frozen = {
        "authorization_sha256": _sha256(authorization_raw),
        "execution_control_sha256": _sha256(control_raw),
        "preparation_manifest_sha256": _sha256(preparation_raw),
    }
    if frozen != expected_frozen:
        _add(errors, "claim_frozen_bindings_invalid")

    existing_result_roots: list[str] = []
    if results_base.exists():
        existing_result_roots = sorted(
            path.name for path in results_base.iterdir() if path.is_dir()
        )
    if existing_result_roots:
        _add(errors, "result_root_present")
    results_manifest_present = (repo_root / RESULTS_MANIFEST_RELATIVE).exists()
    if results_manifest_present:
        _add(errors, "results_manifest_present")

    m3_changed_paths: list[str] = []
    preparation_changed_paths: list[str] = []
    if verify_git:
        ancestry = _git("merge-base", "--is-ancestor", PREPARATION_HEAD, "HEAD")
        if ancestry.returncode != 0:
            _add(errors, "preparation_head_not_ancestor")
        authorization_commit = _git(
            "cat-file", "-e", f"{AUTHORIZATION_HEAD}^{{commit}}"
        )
        if authorization_commit.returncode != 0:
            _add(errors, "authorization_head_unavailable")
        else:
            authorization_ancestry = _git(
                "merge-base", "--is-ancestor", AUTHORIZATION_HEAD, "HEAD"
            )
            if authorization_ancestry.returncode != 0:
                _add(errors, "authorization_head_not_ancestor")
        m3_changed_paths = _changed_paths(PREPARATION_HEAD, FROZEN_M3_PATHS)
        preparation_changed_paths = _changed_paths(
            PREPARATION_HEAD, FROZEN_PREPARATION_PATHS
        )
        if m3_changed_paths:
            _add(errors, "m3_or_skill_changed")
        if preparation_changed_paths:
            _add(errors, "m4_preparation_changed")

    evidence_state = failure.get("evidence_state")
    return {
        "status": "PRE_DISPATCH_FAILED_PRESERVED" if not errors else "INVALID",
        "errors": sorted(errors),
        "claim_id": claim.get("claim_id"),
        "claim_sha256": _sha256(claim_raw),
        "failure_sha256": _sha256(failure_raw),
        "authorization_token_status": claim.get(
            "authorization_token_status_after_claim"
        ),
        "failed_stage": failure.get("failed_stage"),
        "failed_batch_id": failure.get("batch_id"),
        "failed_task_id": failure.get("task_id"),
        "execution_counters": failure.get("counters", {}),
        "existing_result_root_count": len(existing_result_roots),
        "results_manifest_present": results_manifest_present,
        "fresh_result_state": evidence_state.get("fresh_task_result_state")
        if isinstance(evidence_state, dict)
        else None,
        "same_revision_resume_authorized": evidence_state.get(
            "same_revision_resume_authorized"
        )
        if isinstance(evidence_state, dict)
        else None,
        "successor_revision_required": evidence_state.get(
            "successor_revision_required"
        )
        if isinstance(evidence_state, dict)
        else None,
        "m3_changed_paths": m3_changed_paths,
        "preparation_changed_paths": preparation_changed_paths,
        "side_effects": [],
    }


def main() -> int:
    result = audit_execution()
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return 0 if result["status"] == "PRE_DISPATCH_FAILED_PRESERVED" else 1


if __name__ == "__main__":
    sys.exit(main())
