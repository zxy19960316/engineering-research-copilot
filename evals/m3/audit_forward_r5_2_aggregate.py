#!/usr/bin/env python3
"""Read-only audit of the M3 r5 plus r5.2-f02 cross-revision aggregate."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
M3_ROOT = REPO_ROOT / "evals" / "m3"
if str(M3_ROOT) not in sys.path:
    sys.path.insert(0, str(M3_ROOT))

from audit_forward_r5_1_f02_terminal import (  # noqa: E402
    audit_terminal as audit_r5_1_terminal,
)
from audit_forward_r5_2_f02_terminal import (  # noqa: E402
    _production_compose,
    _production_validate,
    audit_terminal as audit_r5_2_terminal,
)
from audit_forward_r5_acceptance import audit_acceptance_manifest  # noqa: E402
from m3_cross_revision_contract import (  # noqa: E402
    GATE3_HEAD,
    HISTORICAL_COUNTERS,
    R5_1_HEAD,
    R5_2_ARTIFACT_HEAD,
    R5_HEAD,
    SELECTED_COUNTERS,
    SELECTED_REVISIONS,
    canonical_sha256,
    load_strict_object,
    parse_strict_object,
    validate_artifact_ref,
)


AGGREGATE_ROOT_RELATIVE = "evals/m3/results/forward-r5.2-aggregate"
AGGREGATE_ROOT = REPO_ROOT / AGGREGATE_ROOT_RELATIVE
SUPERSESSION_RELATIVE = f"{AGGREGATE_ROOT_RELATIVE}/supersession-manifest.json"
AGGREGATE_RELATIVE = f"{AGGREGATE_ROOT_RELATIVE}/aggregate-manifest.json"
SUPERSESSION_MANIFEST = REPO_ROOT / SUPERSESSION_RELATIVE
AGGREGATE_MANIFEST = REPO_ROOT / AGGREGATE_RELATIVE

SUPERSESSION_SCHEMA = "m3.1-cross-revision-supersession-v1"
AGGREGATE_SCHEMA = "m3.1-cross-revision-aggregate-v1"
REVISION = "r5+r5.2-f02"
AUTHORIZATION_SHA256 = "98d85c7301a2a8e65c95c7bcfa3fd256d55c60584f26113e0ae8be6464a4153e"
GATE3_RUN_ID = 31192712555
SUPERSESSION_DOES_NOT_PROVE = [
    "Supersession relabels or repairs a failed historical F02 attempt.",
    "A fresh task or retry is authorized.",
    "M3 is closed or M4 has started.",
    "Any experiment, simulation, training, deployment, or safety claim.",
]
AGGREGATE_DOES_NOT_PROVE = [
    "A failed historical F02 attempt was repaired, retried, or relabeled.",
    "M3 closure has completed or M4 has started.",
    "Any experiment, simulation, training, deployment, or safety claim.",
]

ATTEMPT_KEYS = {
    "attempt_id",
    "case_id",
    "revision",
    "task_id",
    "finalization_id",
    "terminal_status",
    "accepted",
    "selected",
    "composer",
    "validator",
    "retry",
    "evidence",
}
EXPECTED_ATTEMPTS = [
    {
        "attempt_id": "r5:m3-f01",
        "case_id": "m3-f01",
        "revision": "r5",
        "task_id": "019fd687-4252-73d1-9220-9f8bf88354a6",
        "finalization_id": "019fd687-47c9-7f02-bc56-1c0716ed73a6",
        "terminal_status": "processed_accepted",
        "accepted": True,
        "selected": True,
        "composer": 1,
        "validator": 1,
        "retry": 0,
    },
    {
        "attempt_id": "r5:m3-f02",
        "case_id": "m3-f02",
        "revision": "r5",
        "task_id": "019fd687-5575-7143-8cf3-1ab3069611f5",
        "finalization_id": "019fd687-6645-70e0-82d0-003a43147447",
        "terminal_status": "processing_failed",
        "accepted": False,
        "selected": False,
        "composer": 1,
        "validator": 0,
        "retry": 0,
    },
    {
        "attempt_id": "r5:m3-f03",
        "case_id": "m3-f03",
        "revision": "r5",
        "task_id": "019fd687-66db-7a50-98dd-1b4e23b65798",
        "finalization_id": "019fd687-6ec4-76b2-83b4-9ceeb7d31329",
        "terminal_status": "processed_accepted",
        "accepted": True,
        "selected": True,
        "composer": 0,
        "validator": 1,
        "retry": 0,
    },
    {
        "attempt_id": "r5:m3-f04",
        "case_id": "m3-f04",
        "revision": "r5",
        "task_id": "019fd687-7f89-7881-b7e3-17fbb9f7b79d",
        "finalization_id": "019fd687-86a2-7940-85c2-e89d8bd492da",
        "terminal_status": "processed_accepted",
        "accepted": True,
        "selected": True,
        "composer": 1,
        "validator": 1,
        "retry": 0,
    },
    {
        "attempt_id": "r5:m3-f05",
        "case_id": "m3-f05",
        "revision": "r5",
        "task_id": "019fd687-a0c1-7473-bc24-8e15f05a6ab9",
        "finalization_id": "019fd687-a9c8-7e30-9fab-50164156a3a7",
        "terminal_status": "processed_accepted",
        "accepted": True,
        "selected": True,
        "composer": 1,
        "validator": 1,
        "retry": 0,
    },
    {
        "attempt_id": "r5.1-f02:m3-f02",
        "case_id": "m3-f02",
        "revision": "r5.1-f02",
        "task_id": "019fdb7c-1728-7a92-b6cf-b0eb631a18b8",
        "finalization_id": "019fdb7c-201e-7a72-bbed-853b45fbfae9",
        "terminal_status": "terminal_not_accepted",
        "accepted": False,
        "selected": False,
        "composer": 1,
        "validator": 0,
        "retry": 0,
    },
    {
        "attempt_id": "r5.2-f02:m3-f02",
        "case_id": "m3-f02",
        "revision": "r5.2-f02",
        "task_id": "019fdcb5-14e4-7462-be4f-379b72171a4d",
        "finalization_id": "019fdcb5-1932-7182-a682-ea8bbd4703ab",
        "terminal_status": "accepted",
        "accepted": True,
        "selected": True,
        "composer": 1,
        "validator": 1,
        "retry": 0,
    },
]
EXPECTED_BY_ID = {item["attempt_id"]: item for item in EXPECTED_ATTEMPTS}
SELECTED_IDS = [
    "r5:m3-f01",
    "r5.2-f02:m3-f02",
    "r5:m3-f03",
    "r5:m3-f04",
    "r5:m3-f05",
]
EXCLUDED_IDS = ["r5:m3-f02", "r5.1-f02:m3-f02"]
F02_LINEAGE = ["r5:m3-f02", "r5.1-f02:m3-f02", "r5.2-f02:m3-f02"]

SUPERSESSION_KEYS = {
    "schema_version",
    "revision",
    "authorization",
    "gate_3_baseline",
    "supersession_scope",
    "selected_mapping",
    "f02_lineage",
    "attempts",
    "historical_counters",
    "side_effects",
    "does_not_prove",
}
AGGREGATE_KEYS = {
    "schema_version",
    "revision",
    "result_root",
    "result_root_allowlist",
    "status",
    "supersession_manifest",
    "selected_cases",
    "selected_counters",
    "historical_counters",
    "excluded_attempts",
    "historical_diffs",
    "gate_state",
    "scope_limits",
    "unexpected_artifacts",
    "side_effects",
    "does_not_prove",
}


def _add(errors: list[str], code: str) -> None:
    if code not in errors:
        errors.append(code)


def _closed(value: object, keys: set[str], code: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        _add(errors, f"{code}_object_required")
        return {}
    if set(value) != keys:
        _add(errors, f"{code}_keys_invalid")
    return value


def _safe_repo_file(repo_root: Path, raw_path: object, exact: str) -> Path | None:
    if raw_path != exact or not isinstance(raw_path, str) or "\\" in raw_path:
        return None
    candidate = PurePosixPath(raw_path)
    if candidate.is_absolute() or ".." in candidate.parts:
        return None
    resolved = (repo_root / Path(*candidate.parts)).resolve()
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError:
        return None
    return resolved


def _git_json(repo_root: Path, head: str, path: str) -> dict[str, Any] | None:
    try:
        completed = subprocess.run(
            ["git", "show", f"{head}:{path}"],
            cwd=repo_root,
            capture_output=True,
            check=False,
        )
    except OSError:
        return None
    if completed.returncode != 0:
        return None
    try:
        return parse_strict_object(completed.stdout)
    except ValueError:
        return None


def _evidence_parameters(revision: str) -> tuple[str, tuple[str, ...]]:
    if revision == "r5":
        return R5_HEAD, ("evals/m3/results/forward-r5",)
    if revision == "r5.1-f02":
        return R5_1_HEAD, ("evals/m3/results/forward-r5.1-f02",)
    return R5_2_ARTIFACT_HEAD, ("evals/m3/results/forward-r5.2-f02",)


def _validate_attempts(
    raw: object,
    *,
    repo_root: Path,
    errors: list[str],
    code: str,
    expected_ids: list[str],
) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        _add(errors, f"{code}_list_required")
        return []
    rows: list[dict[str, Any]] = []
    ids: list[Any] = []
    for item in raw:
        row = _closed(item, ATTEMPT_KEYS, f"{code}_entry", errors)
        if not row:
            continue
        attempt_id = row.get("attempt_id")
        ids.append(attempt_id)
        expected = EXPECTED_BY_ID.get(attempt_id) if isinstance(attempt_id, str) else None
        if expected is None:
            _add(errors, "attempt_id_invalid")
        else:
            for key, value in expected.items():
                if row.get(key) != value:
                    _add(errors, f"attempt_identity_invalid:{attempt_id}:{key}")
            head, prefixes = _evidence_parameters(expected["revision"])
            for artifact_error in validate_artifact_ref(
                row.get("evidence"),
                repo_root=repo_root,
                expected_head=head,
                allowed_prefixes=prefixes,
                json_required=True,
            ):
                _add(errors, f"attempt_evidence_invalid:{attempt_id}:{artifact_error}")
        rows.append(row)
    if len(ids) != len(set(str(item) for item in ids)):
        _add(errors, "attempt_id_duplicate")
    if ids != expected_ids:
        _add(errors, f"{code}_set_invalid")
    return rows


def _derive_counters(rows: list[dict[str, Any]]) -> dict[str, int]:
    def integer(item: dict[str, Any], key: str) -> int:
        value = item.get(key)
        return value if isinstance(value, int) and not isinstance(value, bool) else 0

    return {
        "tasks": len(rows),
        "finalizations": len(rows),
        "composer": sum(integer(item, "composer") for item in rows),
        "validator": sum(integer(item, "validator") for item in rows),
        "accepted": sum(item.get("accepted") is True for item in rows),
        "failed": sum(item.get("accepted") is False for item in rows),
        "retry": sum(integer(item, "retry") for item in rows),
    }


def _validate_supersession(
    value: dict[str, Any], *, repo_root: Path, errors: list[str]
) -> list[dict[str, Any]]:
    _closed(value, SUPERSESSION_KEYS, "supersession", errors)
    if value.get("schema_version") != SUPERSESSION_SCHEMA:
        _add(errors, "supersession_schema_invalid")
    if value.get("revision") != REVISION:
        _add(errors, "supersession_revision_invalid")
    authorization = _closed(
        value.get("authorization"),
        {
            "message_sha256",
            "message_utf8_bytes",
            "authorized_scope",
            "fresh_execution_authorized",
            "retry_authorized",
            "repair_authorized",
            "m4_authorized",
        },
        "supersession_authorization",
        errors,
    )
    expected_authorization = {
        "message_sha256": AUTHORIZATION_SHA256,
        "message_utf8_bytes": 188,
        "authorized_scope": ["gate_4", "cross_revision_aggregate", "m3_closure"],
        "fresh_execution_authorized": False,
        "retry_authorized": False,
        "repair_authorized": False,
        "m4_authorized": False,
    }
    if authorization != expected_authorization:
        _add(errors, "supersession_authorization_invalid")
    baseline = _closed(
        value.get("gate_3_baseline"),
        {"head", "branch", "ci_run_id", "conclusion"},
        "gate_3_baseline",
        errors,
    )
    if baseline != {
        "head": GATE3_HEAD,
        "branch": "codex/m3.1.1-r5.2-f02-one-shot-fresh-execution",
        "ci_run_id": GATE3_RUN_ID,
        "conclusion": "success",
    }:
        _add(errors, "gate_3_baseline_invalid")
    scope = _closed(
        value.get("supersession_scope"),
        {"selection_only", "relabels_history", "deletes_history", "repairs_history", "retries_history"},
        "supersession_scope",
        errors,
    )
    if scope != {
        "selection_only": True,
        "relabels_history": False,
        "deletes_history": False,
        "repairs_history": False,
        "retries_history": False,
    }:
        _add(errors, "supersession_scope_invalid")
    if value.get("selected_mapping") != SELECTED_REVISIONS:
        _add(errors, "selected_revision_mapping_invalid")
    if value.get("f02_lineage") != F02_LINEAGE:
        _add(errors, "f02_lineage_invalid")
    attempts = _validate_attempts(
        value.get("attempts"),
        repo_root=repo_root,
        errors=errors,
        code="historical_attempt",
        expected_ids=[item["attempt_id"] for item in EXPECTED_ATTEMPTS],
    )
    task_ids = [item.get("task_id") for item in attempts]
    finalization_ids = [item.get("finalization_id") for item in attempts]
    if not all(isinstance(item, str) and item for item in task_ids):
        _add(errors, "task_id_invalid")
    elif len(task_ids) != len(set(task_ids)):
        _add(errors, "task_id_duplicate")
    if not all(isinstance(item, str) and item for item in finalization_ids):
        _add(errors, "finalization_id_invalid")
    elif len(finalization_ids) != len(set(finalization_ids)):
        _add(errors, "finalization_id_duplicate")
    if value.get("historical_counters") != HISTORICAL_COUNTERS:
        _add(errors, "historical_counters_invalid")
    if attempts and _derive_counters(attempts) != HISTORICAL_COUNTERS:
        _add(errors, "historical_counter_derivation_mismatch")
    if value.get("side_effects") != []:
        _add(errors, "supersession_side_effects_nonempty")
    if value.get("does_not_prove") != SUPERSESSION_DOES_NOT_PROVE:
        _add(errors, "supersession_claim_limits_invalid")
    return attempts


def _validate_supersession_binding(
    aggregate: dict[str, Any], *, repo_root: Path, errors: list[str]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    binding = _closed(
        aggregate.get("supersession_manifest"),
        {"path", "raw_sha256", "canonical_sha256"},
        "supersession_binding",
        errors,
    )
    path = _safe_repo_file(repo_root, binding.get("path"), SUPERSESSION_RELATIVE)
    if path is None:
        _add(errors, "supersession_path_invalid")
        return {}, []
    try:
        raw = path.read_bytes()
        supersession = parse_strict_object(raw)
    except (OSError, ValueError):
        _add(errors, "supersession_manifest_invalid")
        return {}, []
    if binding.get("raw_sha256") != hashlib.sha256(raw).hexdigest():
        _add(errors, "supersession_raw_sha256_mismatch")
    if binding.get("canonical_sha256") != canonical_sha256(supersession):
        _add(errors, "supersession_canonical_sha256_mismatch")
    attempts = _validate_supersession(supersession, repo_root=repo_root, errors=errors)
    return supersession, attempts


def _historical_diff(
    repo_root: Path, head: str, path: str
) -> str:
    try:
        completed = subprocess.run(
            ["git", "diff", "--quiet", head, "HEAD", "--", path],
            cwd=repo_root,
            capture_output=True,
            check=False,
        )
    except OSError:
        return "unavailable"
    return "empty" if completed.returncode == 0 else "nonempty"


def _validate_f03(repo_root: Path, errors: list[str]) -> None:
    outcome = _git_json(
        repo_root, R5_HEAD, "evals/m3/results/forward-r5/m3-f03.outcome.json"
    )
    validation = _git_json(
        repo_root, R5_HEAD, "evals/m3/results/forward-r5/m3-f03.validation.json"
    )
    if not isinstance(outcome, dict):
        _add(errors, "f03_outcome_unavailable")
    else:
        if outcome.get("terminal_code") != "unsupported_approved_constraint_change_provenance":
            _add(errors, "f03_terminal_code_invalid")
        if outcome.get("applied_constraint_changes") != []:
            _add(errors, "f03_constraint_changes_nonempty")
        if outcome.get("outcome_kind") != "blocked":
            _add(errors, "f03_outcome_kind_invalid")
    if not isinstance(validation, dict) or validation != {
        "accepted": True,
        "case_id": "m3-f03",
        "errors": [],
        "evidence_gaps": [],
        "method_bundle_validation": "not_applicable_expected_block",
        "outcome_kind": "blocked",
        "status": "accepted_expected_block",
    }:
        _add(errors, "f03_validation_invalid")


def _validate_source_audits(repo_root: Path, errors: list[str]) -> None:
    r5 = audit_acceptance_manifest(
        repo_root / "evals/m3/results/forward-r5/acceptance-manifest-consumed.json"
    )
    if r5.get("status") != "blocked_not_accepted" or r5.get("errors") != [
        "acceptance_requirements_unmet"
    ]:
        _add(errors, "r5_source_audit_invalid")
    r5_cases = {
        item.get("case_id"): item for item in r5.get("cases", []) if isinstance(item, dict)
    }
    for case_id in ("m3-f01", "m3-f03", "m3-f04", "m3-f05"):
        item = r5_cases.get(case_id, {})
        if item.get("record_state") != "processed_accepted" or item.get("errors") != []:
            _add(errors, f"r5_selected_case_invalid:{case_id}")
    if (
        r5_cases.get("m3-f02", {}).get("record_state") != "processing_failed"
        or r5_cases.get("m3-f02", {}).get("errors") != []
    ):
        _add(errors, "r5_failed_f02_history_invalid")

    r5_1 = audit_r5_1_terminal(
        repo_root / "evals/m3/results/forward-r5.1-f02/terminal-manifest.json",
        artifact_root=repo_root,
        git_root=repo_root,
    )
    if (
        r5_1.get("status") != "terminal_not_accepted"
        or r5_1.get("accepted") is not False
        or r5_1.get("errors") != []
        or r5_1.get("fresh_task_id") != EXPECTED_BY_ID["r5.1-f02:m3-f02"]["task_id"]
    ):
        _add(errors, "r5_1_source_audit_invalid")

    root_cause = _git_json(
        repo_root,
        GATE3_HEAD,
        "evals/m3/results/diagnostics-r5.2-f02/root-cause-report.json",
    )
    if (
        not isinstance(root_cause, dict)
        or root_cause.get("task_id") != EXPECTED_BY_ID["r5.1-f02:m3-f02"]["task_id"]
        or root_cause.get("consumed_turn_id")
        != EXPECTED_BY_ID["r5.1-f02:m3-f02"]["finalization_id"]
    ):
        _add(errors, "r5_1_finalization_identity_invalid")

    r5_2 = audit_r5_2_terminal(
        repo_root / "evals/m3/results/forward-r5.2-f02",
        compose_once=_production_compose,
        validate_once=_production_validate,
    )
    if (
        r5_2.get("status") != "accepted"
        or r5_2.get("accepted") is not True
        or r5_2.get("errors") != []
        or r5_2.get("task_id") != EXPECTED_BY_ID["r5.2-f02:m3-f02"]["task_id"]
        or r5_2.get("counters")
        != {"tasks": 1, "finalizations": 1, "composer": 1, "validator": 1, "retry": 0}
    ):
        _add(errors, "r5_2_source_audit_invalid")

    r5_2_terminal = _git_json(
        repo_root,
        R5_2_ARTIFACT_HEAD,
        "evals/m3/results/forward-r5.2-f02/terminal-manifest.json",
    )
    if (
        not isinstance(r5_2_terminal, dict)
        or r5_2_terminal.get("finalization_id")
        != EXPECTED_BY_ID["r5.2-f02:m3-f02"]["finalization_id"]
    ):
        _add(errors, "r5_2_finalization_identity_invalid")
    _validate_f03(repo_root, errors)


def _empty_result(errors: list[str]) -> dict[str, Any]:
    return {
        "status": "invalid",
        "selected_cases": [],
        "selected_counters": {},
        "historical_counters": {},
        "excluded_attempts": [],
        "historical_diffs": [],
        "errors": sorted(set(errors)),
        "evidence_gaps": [],
        "side_effects": [],
        "m3_status": "IN_PROGRESS",
        "m4_status": "NOT_STARTED",
    }


def audit_aggregate(
    path: str | Path = AGGREGATE_MANIFEST, *, repo_root: Path = REPO_ROOT
) -> dict[str, Any]:
    """Audit a closed aggregate without writing, repairing, retrying, or executing."""

    errors: list[str] = []
    try:
        manifest = load_strict_object(Path(path))
    except ValueError:
        return _empty_result(["aggregate_manifest_invalid"])
    _closed(manifest, AGGREGATE_KEYS, "aggregate", errors)
    if manifest.get("schema_version") != AGGREGATE_SCHEMA:
        _add(errors, "aggregate_schema_invalid")
    if manifest.get("revision") != REVISION:
        _add(errors, "aggregate_revision_invalid")
    if manifest.get("result_root") != AGGREGATE_ROOT_RELATIVE:
        _add(errors, "result_root_not_exact")
    allowed_names = [
        "aggregate-audit.json",
        "aggregate-manifest.json",
        "m3-closure-manifest.json",
        "m3-final-validation.json",
        "supersession-manifest.json",
    ]
    if manifest.get("result_root_allowlist") != allowed_names:
        _add(errors, "result_root_allowlist_invalid")
    try:
        actual_names = sorted(item.name for item in (repo_root / AGGREGATE_ROOT_RELATIVE).iterdir())
    except OSError:
        actual_names = []
        _add(errors, "result_root_unavailable")
    unexpected_names = sorted(set(actual_names) - set(allowed_names))
    if unexpected_names:
        _add(errors, "unexpected_result_artifacts")
    if not {"aggregate-manifest.json", "supersession-manifest.json"}.issubset(actual_names):
        _add(errors, "required_aggregate_manifests_missing")
    if manifest.get("status") != "accepted":
        _add(errors, "aggregate_declared_status_invalid")

    _, historical_attempts = _validate_supersession_binding(
        manifest, repo_root=repo_root, errors=errors
    )
    selected = _validate_attempts(
        manifest.get("selected_cases"),
        repo_root=repo_root,
        errors=errors,
        code="selected_case",
        expected_ids=SELECTED_IDS,
    )
    excluded = _validate_attempts(
        manifest.get("excluded_attempts"),
        repo_root=repo_root,
        errors=errors,
        code="excluded_attempt",
        expected_ids=EXCLUDED_IDS,
    )
    selected_mapping: dict[str, Any] = {}
    for item in selected:
        case_id = item.get("case_id")
        if isinstance(case_id, str):
            selected_mapping[case_id] = item.get("revision")
        else:
            _add(errors, "selected_case_id_invalid")
    if selected_mapping != SELECTED_REVISIONS:
        _add(errors, "selected_revision_mapping_invalid")
    if manifest.get("selected_counters") != SELECTED_COUNTERS:
        _add(errors, "selected_counters_invalid")
    if selected and _derive_counters(selected) != SELECTED_COUNTERS:
        _add(errors, "selected_counter_derivation_mismatch")
    if manifest.get("historical_counters") != HISTORICAL_COUNTERS:
        _add(errors, "historical_counters_invalid")
    if historical_attempts and _derive_counters(historical_attempts) != HISTORICAL_COUNTERS:
        _add(errors, "historical_counter_derivation_mismatch")
    if historical_attempts:
        historical_by_id = {
            item["attempt_id"]: item
            for item in historical_attempts
            if isinstance(item.get("attempt_id"), str)
        }
        for row in [*selected, *excluded]:
            attempt_id = row.get("attempt_id")
            bound = historical_by_id.get(attempt_id) if isinstance(attempt_id, str) else None
            if row != bound:
                _add(errors, f"aggregate_attempt_binding_mismatch:{attempt_id}")

    expected_diffs = [
        {
            "revision": "r5",
            "path": "evals/m3/results/forward-r5",
            "source_head": R5_HEAD,
            "status": "empty",
        },
        {
            "revision": "r5.1-f02",
            "path": "evals/m3/results/forward-r5.1-f02",
            "source_head": R5_1_HEAD,
            "status": "empty",
        },
        {
            "revision": "r5.2-f02",
            "path": "evals/m3/results/forward-r5.2-f02",
            "source_head": R5_2_ARTIFACT_HEAD,
            "status": "empty",
        },
    ]
    if manifest.get("historical_diffs") != expected_diffs:
        _add(errors, "historical_diff_declarations_invalid")
    actual_diffs: list[dict[str, Any]] = []
    for item in expected_diffs:
        status = _historical_diff(repo_root, item["source_head"], item["path"])
        actual = {**item, "status": status}
        actual_diffs.append(actual)
        if status != "empty":
            _add(errors, f"historical_diff_nonempty:{item['revision']}")

    gate_state = _closed(
        manifest.get("gate_state"),
        {"gate_4", "m3_closure", "m3", "m4"},
        "gate_state",
        errors,
    )
    if gate_state != {
        "gate_4": "COMPLETE",
        "m3_closure": "NOT_RUN",
        "m3": "IN_PROGRESS",
        "m4": "NOT_STARTED",
    }:
        _add(errors, "gate_state_invalid")
    scope_limits = _closed(
        manifest.get("scope_limits"),
        {
            "fresh_execution_authorized",
            "retry_authorized",
            "repair_authorized",
            "m4_authorized",
            "no_empirical_claim",
        },
        "scope_limits",
        errors,
    )
    if scope_limits != {
        "fresh_execution_authorized": False,
        "retry_authorized": False,
        "repair_authorized": False,
        "m4_authorized": False,
        "no_empirical_claim": True,
    }:
        _add(errors, "scope_limits_invalid")
    if manifest.get("unexpected_artifacts") != unexpected_names or unexpected_names:
        _add(errors, "unexpected_artifacts_nonempty")
    if manifest.get("side_effects") != []:
        _add(errors, "side_effects_nonempty")
    if manifest.get("does_not_prove") != AGGREGATE_DOES_NOT_PROVE:
        _add(errors, "claim_limits_invalid")

    f03 = next((item for item in selected if item.get("case_id") == "m3-f03"), {})
    if f03.get("composer") != 0:
        _add(errors, "f03_composer_must_be_zero")
    if f03.get("validator") != 1 or f03.get("terminal_status") != "processed_accepted":
        _add(errors, "f03_expected_block_counters_invalid")

    if not errors:
        _validate_source_audits(repo_root, errors)
    status = "accepted" if not errors else "invalid"
    return {
        "status": status,
        "selected_cases": selected,
        "selected_counters": manifest.get("selected_counters", {}),
        "historical_counters": manifest.get("historical_counters", {}),
        "excluded_attempts": excluded,
        "historical_diffs": actual_diffs,
        "errors": sorted(set(errors)),
        "evidence_gaps": [],
        "side_effects": [],
        "m3_status": gate_state.get("m3", "IN_PROGRESS"),
        "m4_status": gate_state.get("m4", "NOT_STARTED"),
    }


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) > 1:
        return 2
    path = Path(arguments[0]) if arguments else AGGREGATE_MANIFEST
    result = audit_aggregate(path)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0 if result["status"] == "accepted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
