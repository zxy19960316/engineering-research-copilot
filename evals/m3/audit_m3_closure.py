#!/usr/bin/env python3
"""Read-only audit for the M3 cross-revision closure record."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
RESULT_ROOT = "evals/m3/results/forward-r5.2-aggregate"
CLOSURE_MANIFEST = f"{RESULT_ROOT}/m3-closure-manifest.json"
WORKFLOW_PATH = ".github/workflows/m1-validation.yml"

ARTIFACT_PATHS = {
    "aggregate_manifest": f"{RESULT_ROOT}/aggregate-manifest.json",
    "aggregate_audit": f"{RESULT_ROOT}/aggregate-audit.json",
    "final_validation": f"{RESULT_ROOT}/m3-final-validation.json",
}
RESULT_ROOT_ALLOWLIST = sorted(
    {
        "aggregate-audit.json",
        "aggregate-manifest.json",
        "m3-closure-manifest.json",
        "m3-final-validation.json",
        "supersession-manifest.json",
    }
)
REQUIRED_GATE_KEYS = {
    "gate_0_terminal_evidence_complete",
    "gate_1_root_cause_complete",
    "gate_2_protocol_preparation_complete",
    "gate_3_f02_accepted",
    "gate_4_cross_revision_aggregate_accepted",
    "aggregate_audit_passed",
    "final_validation_passed",
    "aggregate_candidate_ci_green",
    "historical_evidence_immutable",
}
HISTORICAL_DIFF_KEYS = {
    "forward_r5",
    "forward_r5_1_f02",
    "forward_r5_2_f02",
}
SCOPE_LIMIT_KEYS = {
    "fresh_execution_authorized",
    "retry_authorized",
    "same_task_retry_authorized",
    "repair_authorized",
    "m4_started",
    "m4_execution_authorized",
    "empirical_claim",
}
DOES_NOT_PROVE = [
    "M3 closure is structural acceptance evidence, not an empirical or safety claim.",
    "M3 closure does not authorize M4 or another fresh execution.",
]
TOP_LEVEL_KEYS = {
    "schema_version",
    "milestone",
    "status",
    "result_root",
    "result_root_allowlist",
    "aggregate_status",
    "aggregate_candidate",
    "aggregate_candidate_ci",
    "artifacts",
    "required_gates",
    "historical_diffs",
    "worktree",
    "m4_status",
    "scope_limits",
    "side_effects",
    "does_not_prove",
}


def _add(errors: list[str], code: str) -> None:
    if code not in errors:
        errors.append(code)


def _load_strict_object(path: Path) -> dict[str, Any]:
    from m3_cross_revision_contract import load_strict_object

    return load_strict_object(path)


def _parse_strict_object(raw: bytes) -> dict[str, Any]:
    from m3_cross_revision_contract import parse_strict_object

    return parse_strict_object(raw)


def _validate_artifact_reference(
    ref: object,
    *,
    repo_root: Path,
    expected_head: str,
) -> list[str]:
    from m3_cross_revision_contract import validate_artifact_ref

    return validate_artifact_ref(
        ref,
        repo_root=repo_root,
        expected_head=expected_head,
        allowed_prefixes=(f"{RESULT_ROOT}/",),
        json_required=True,
    )


def _run_aggregate_audit(path: Path, *, repo_root: Path) -> dict[str, Any]:
    from audit_forward_r5_2_aggregate import audit_aggregate

    return audit_aggregate(path, repo_root=repo_root)


def _git_json(repo_root: Path, head: str, path: str) -> dict[str, Any] | None:
    try:
        process = subprocess.run(
            ["git", "show", f"{head}:{path}"],
            cwd=repo_root,
            capture_output=True,
            check=False,
        )
    except OSError:
        return None
    if process.returncode != 0:
        return None
    try:
        return _parse_strict_object(process.stdout)
    except (UnicodeError, json.JSONDecodeError, ValueError):
        return None


def _exact_keys(value: object, expected: set[str]) -> bool:
    return isinstance(value, dict) and set(value) == expected


def _valid_sha(value: object) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}", value) is not None


def _valid_run_id(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _empty_result(errors: list[str]) -> dict[str, Any]:
    return {
        "status": "invalid",
        "milestone": None,
        "aggregate_status": "invalid",
        "required_gates": {},
        "historical_diffs": {},
        "worktree": {},
        "m4_status": None,
        "errors": sorted(set(errors)),
        "side_effects": [],
        "does_not_prove": DOES_NOT_PROVE,
    }


def _validate_candidate_binding(closure: dict[str, Any], errors: list[str]) -> str | None:
    candidate = closure.get("aggregate_candidate")
    ci = closure.get("aggregate_candidate_ci")
    candidate_keys = {"head_sha", "workflow", "run_id"}
    ci_keys = {"head_sha", "workflow", "run_id", "status", "conclusion", "jobs"}
    if not _exact_keys(candidate, candidate_keys):
        _add(errors, "aggregate_candidate_shape_invalid")
        candidate = {}
    if not _exact_keys(ci, ci_keys):
        _add(errors, "aggregate_candidate_ci_shape_invalid")
        ci = {}

    head = candidate.get("head_sha")
    if not _valid_sha(head):
        _add(errors, "aggregate_candidate_head_invalid")
        head = None
    if candidate.get("workflow") != WORKFLOW_PATH:
        _add(errors, "aggregate_candidate_workflow_invalid")
    if not _valid_run_id(candidate.get("run_id")):
        _add(errors, "aggregate_candidate_run_invalid")

    if ci.get("head_sha") != candidate.get("head_sha"):
        _add(errors, "aggregate_candidate_head_mismatch")
    if ci.get("workflow") != candidate.get("workflow"):
        _add(errors, "aggregate_candidate_workflow_mismatch")
    if ci.get("run_id") != candidate.get("run_id"):
        _add(errors, "aggregate_candidate_run_mismatch")

    jobs = ci.get("jobs")
    jobs_green = _exact_keys(jobs, {"validate", "ubuntu", "windows"}) and all(
        jobs.get(name) == "success" for name in ("validate", "ubuntu", "windows")
    )
    if ci.get("status") != "completed" or ci.get("conclusion") != "success" or not jobs_green:
        _add(errors, "aggregate_candidate_ci_not_green")
    return head


def _validate_artifacts(
    closure: dict[str, Any],
    *,
    repo_root: Path,
    candidate_head: str | None,
    errors: list[str],
) -> dict[str, dict[str, Any]]:
    artifacts = closure.get("artifacts")
    if not _exact_keys(artifacts, set(ARTIFACT_PATHS)):
        _add(errors, "closure_artifact_reference_set_invalid")
        artifacts = artifacts if isinstance(artifacts, dict) else {}

    loaded: dict[str, dict[str, Any]] = {}
    for name, expected_path in ARTIFACT_PATHS.items():
        ref = artifacts.get(name)
        if not isinstance(ref, dict):
            _add(errors, f"closure_artifact_reference_missing:{name}")
            continue
        if ref.get("path") != expected_path:
            _add(errors, f"closure_artifact_path_invalid:{name}")
        if candidate_head is None:
            continue
        if ref.get("source_head") != candidate_head:
            _add(errors, "aggregate_candidate_head_mismatch")
        try:
            ref_errors = _validate_artifact_reference(
                ref,
                repo_root=repo_root,
                expected_head=candidate_head,
            )
        except (OSError, UnicodeError, ValueError):
            ref_errors = ["validation_failed"]
        for code in ref_errors:
            _add(errors, f"closure_artifact_invalid:{name}:{code}")
        value = _git_json(repo_root, candidate_head, expected_path)
        if value is None:
            _add(errors, f"candidate_artifact_unavailable:{name}")
        else:
            loaded[name] = value
    return loaded


def _validate_required_gates(closure: dict[str, Any], errors: list[str]) -> dict[str, Any]:
    gates = closure.get("required_gates")
    if not _exact_keys(gates, REQUIRED_GATE_KEYS):
        _add(errors, "required_gate_set_invalid")
        return gates if isinstance(gates, dict) else {}
    if any(gates.get(name) is not True for name in REQUIRED_GATE_KEYS):
        _add(errors, "required_gate_not_passed")
    return gates


def _validate_historical_diffs(closure: dict[str, Any], errors: list[str]) -> dict[str, Any]:
    diffs = closure.get("historical_diffs")
    if not _exact_keys(diffs, HISTORICAL_DIFF_KEYS):
        _add(errors, "historical_diff_set_invalid")
        return diffs if isinstance(diffs, dict) else {}
    if any(diffs.get(name) != [] for name in HISTORICAL_DIFF_KEYS):
        _add(errors, "historical_diff_nonempty")
    return diffs


def _validate_scope(closure: dict[str, Any], errors: list[str]) -> None:
    scope = closure.get("scope_limits")
    if not _exact_keys(scope, SCOPE_LIMIT_KEYS):
        _add(errors, "closure_scope_shape_invalid")
        scope = scope if isinstance(scope, dict) else {}
    if scope.get("fresh_execution_authorized") is not False:
        _add(errors, "fresh_execution_authority_forbidden")
    if scope.get("retry_authorized") is not False or scope.get("same_task_retry_authorized") is not False:
        _add(errors, "retry_authority_forbidden")
    if scope.get("repair_authorized") is not False:
        _add(errors, "repair_authority_forbidden")
    if scope.get("m4_started") is not False or scope.get("m4_execution_authorized") is not False:
        _add(errors, "m4_must_remain_not_started")
    if scope.get("empirical_claim") is not False:
        _add(errors, "empirical_claim_forbidden")


def _validate_result_root(
    closure: dict[str, Any], *, repo_root: Path, errors: list[str]
) -> dict[str, Any]:
    if closure.get("result_root") != RESULT_ROOT:
        _add(errors, "closure_result_root_invalid")
    if closure.get("result_root_allowlist") != RESULT_ROOT_ALLOWLIST:
        _add(errors, "closure_result_root_allowlist_invalid")

    root = repo_root / RESULT_ROOT
    try:
        actual = sorted(item.name for item in root.iterdir())
    except OSError:
        actual = []
        _add(errors, "closure_result_root_unavailable")
    if actual != RESULT_ROOT_ALLOWLIST:
        _add(errors, "closure_result_root_dirty")

    worktree = closure.get("worktree")
    if not _exact_keys(worktree, {"before_closure_edits", "unexpected_artifacts"}):
        _add(errors, "closure_worktree_shape_invalid")
        worktree = worktree if isinstance(worktree, dict) else {}
    if worktree.get("before_closure_edits") != "clean":
        _add(errors, "worktree_not_clean_before_closure")
    if worktree.get("unexpected_artifacts") != []:
        _add(errors, "closure_unexpected_artifacts")
    return worktree


def audit_closure(
    path: str | Path,
    *,
    repo_root: Path = REPO_ROOT,
) -> dict[str, Any]:
    """Audit a closure manifest without writing, retrying, or executing a task."""

    errors: list[str] = []
    manifest_path = Path(path)
    expected_path = (repo_root / CLOSURE_MANIFEST).resolve()
    try:
        if manifest_path.resolve() != expected_path:
            _add(errors, "closure_manifest_path_invalid")
        closure = _load_strict_object(manifest_path)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        _add(errors, "closure_manifest_invalid")
        return _empty_result(errors)

    if set(closure) != TOP_LEVEL_KEYS:
        _add(errors, "closure_shape_invalid")
    if closure.get("schema_version") != "m3.1-cross-revision-closure-v1":
        _add(errors, "closure_schema_version_invalid")
    if closure.get("milestone") != "M3":
        _add(errors, "closure_milestone_invalid")
    if closure.get("status") != "CLOSED":
        _add(errors, "closure_status_invalid")
    if closure.get("aggregate_status") != "accepted":
        _add(errors, "aggregate_not_accepted")
    if closure.get("m4_status") != "NOT_STARTED":
        _add(errors, "m4_must_remain_not_started")
    if closure.get("side_effects") != []:
        _add(errors, "closure_side_effects_nonempty")
    if closure.get("does_not_prove") != DOES_NOT_PROVE:
        _add(errors, "closure_claim_limit_invalid")

    candidate_head = _validate_candidate_binding(closure, errors)
    loaded = _validate_artifacts(
        closure,
        repo_root=repo_root,
        candidate_head=candidate_head,
        errors=errors,
    )
    required_gates = _validate_required_gates(closure, errors)
    historical_diffs = _validate_historical_diffs(closure, errors)
    worktree = _validate_result_root(closure, repo_root=repo_root, errors=errors)
    _validate_scope(closure, errors)

    aggregate_manifest_path = repo_root / ARTIFACT_PATHS["aggregate_manifest"]
    aggregate_manifest = loaded.get("aggregate_manifest")
    if aggregate_manifest is not None:
        try:
            current_aggregate = _load_strict_object(aggregate_manifest_path)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
            _add(errors, "aggregate_manifest_unavailable")
        else:
            if current_aggregate != aggregate_manifest:
                _add(errors, "aggregate_manifest_candidate_mismatch")

    try:
        aggregate = _run_aggregate_audit(aggregate_manifest_path, repo_root=repo_root)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        aggregate = {"status": "invalid", "errors": ["aggregate_audit_failed"]}
    if aggregate.get("status") != "accepted" or aggregate.get("errors") != []:
        _add(errors, "aggregate_not_accepted")
    aggregate_receipt = loaded.get("aggregate_audit")
    if aggregate_receipt is not None and aggregate_receipt != aggregate:
        _add(errors, "aggregate_audit_receipt_mismatch")

    final_validation = loaded.get("final_validation")
    if final_validation is not None and (
        final_validation.get("status") != "passed" or final_validation.get("errors") != []
    ):
        _add(errors, "final_validation_not_passed")

    status = "closed" if not errors else "invalid"
    return {
        "status": status,
        "milestone": closure.get("milestone"),
        "aggregate_status": aggregate.get("status"),
        "required_gates": required_gates,
        "historical_diffs": historical_diffs,
        "worktree": worktree,
        "m4_status": closure.get("m4_status"),
        "errors": sorted(set(errors)),
        "side_effects": closure.get("side_effects") if isinstance(closure.get("side_effects"), list) else [],
        "does_not_prove": DOES_NOT_PROVE,
    }


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) > 1:
        return 2
    path = Path(arguments[0]) if arguments else REPO_ROOT / CLOSURE_MANIFEST
    result = audit_closure(path)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0 if result["status"] == "closed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
