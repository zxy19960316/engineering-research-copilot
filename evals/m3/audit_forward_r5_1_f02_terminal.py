#!/usr/bin/env python3
"""Read-only audit of the consumed r5.1-f02 terminal failure evidence."""

from __future__ import annotations

import json
import subprocess
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

from r5_1_f02_execution_contract import (
    validate_execution_authorization_shape,
    validate_launch_receipt,
)
from r5_1_f02_terminal_contract import (
    ALLOWED_RESULT_FILES,
    ARTIFACT_SPECS,
    AUTHORIZATION_TOKEN,
    CASE_ID,
    COUNTERS,
    EXECUTION_AUTHORIZATION_HEAD,
    EXECUTION_EVIDENCE_HEAD,
    FORBIDDEN_RESULT_FILES,
    FRESH_TASK_ID,
    HISTORICAL_EVIDENCE_HEAD,
    HISTORICAL_RESULT_ROOT,
    HISTORICAL_TASK_ID,
    REQUIRED_RESULT_FILES,
    RESULT_ROOT,
    REVISION,
    TERMINAL_MANIFEST_PATH,
    canonical_sha256,
    parse_json_object,
    sha256,
    validate_terminal_manifest_shape,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
RESULT_ROOT_RELATIVE = Path(RESULT_ROOT)
TERMINAL_MANIFEST_RELATIVE = Path(TERMINAL_MANIFEST_PATH)
TERMINAL_MANIFEST = REPO_ROOT / TERMINAL_MANIFEST_RELATIVE


def _add(errors: list[str], code: str) -> None:
    if code not in errors:
        errors.append(code)


def _load_manifest(path: Path, errors: list[str]) -> dict[str, Any] | None:
    try:
        return parse_json_object(path.read_bytes())
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        _add(errors, "terminal_manifest_invalid_json")
        return None


@lru_cache(maxsize=None)
def _git_blob(git_root: Path, head: str, path: str) -> tuple[str, bytes] | None:
    try:
        commit = subprocess.run(
            ["git", "cat-file", "-e", f"{head}^{{commit}}"],
            cwd=git_root,
            capture_output=True,
            check=False,
        )
        raw = subprocess.run(
            ["git", "show", f"{head}:{path}"],
            cwd=git_root,
            capture_output=True,
            check=False,
        )
        oid = subprocess.run(
            ["git", "rev-parse", f"{head}:{path}"],
            cwd=git_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
    except OSError:
        return None
    if commit.returncode != 0 or raw.returncode != 0 or oid.returncode != 0:
        return None
    return oid.stdout.strip(), raw.stdout


def _git_filtered_oid(git_root: Path, path: str, raw: bytes) -> str | None:
    """Hash worktree bytes with the repository's clean-filter rules."""

    try:
        result = subprocess.run(
            ["git", "hash-object", "--stdin", f"--path={path}"],
            cwd=git_root,
            input=raw,
            capture_output=True,
            check=False,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    try:
        return result.stdout.decode("ascii", errors="strict").strip()
    except UnicodeError:
        return None


def _verify_artifact(
    key: str,
    manifest: dict[str, Any],
    *,
    artifact_root: Path,
    git_root: Path,
    errors: list[str],
) -> tuple[bytes | None, dict[str, Any] | None]:
    identity = manifest.get("artifacts", {}).get(key)
    if not isinstance(identity, dict):
        _add(errors, f"artifact_identity_invalid:{key}")
        return None, None
    head, relative, kind = ARTIFACT_SPECS[key]
    blob = _git_blob(git_root, head, relative)
    if blob is None:
        _add(errors, f"artifact_git_blob_unavailable:{key}")
        return None, None
    oid, blob_raw = blob
    expected = {
        "path": relative,
        "source_head": head,
        "git_blob_oid": oid,
        "byte_length": len(blob_raw),
        "raw_sha256": sha256(blob_raw),
        "utf8_status": "valid",
        "json_status": {
            "json": "valid",
            "malformed_json": "invalid_expected",
            "text": "not_applicable",
        }[kind],
    }
    parsed_blob: dict[str, Any] | None = None
    try:
        blob_text = blob_raw.decode("utf-8", errors="strict")
        if kind == "json":
            parsed_blob = parse_json_object(blob_raw)
            expected["canonical_sha256"] = canonical_sha256(parsed_blob)
        elif kind == "malformed_json":
            try:
                json.loads(blob_text)
            except json.JSONDecodeError:
                pass
            else:
                _add(errors, f"artifact_blob_expected_malformed:{key}")
    except (UnicodeError, json.JSONDecodeError, ValueError):
        _add(errors, f"artifact_git_blob_content_invalid:{key}")
    for field, required in expected.items():
        if identity.get(field) != required:
            _add(errors, f"artifact_manifest_{field}_mismatch:{key}")

    worktree_path = artifact_root / relative
    if not worktree_path.exists() or not worktree_path.is_file() or worktree_path.is_symlink():
        _add(errors, f"missing_required_artifact:{key}")
        return None, None
    try:
        worktree_raw = worktree_path.read_bytes()
    except OSError:
        _add(errors, f"artifact_unreadable:{key}")
        return None, None
    if worktree_raw != blob_raw and _git_filtered_oid(
        git_root, relative, worktree_raw
    ) != oid:
        _add(errors, f"artifact_worktree_drift:{key}")

    parsed_worktree: dict[str, Any] | None = None
    try:
        worktree_text = worktree_raw.decode("utf-8", errors="strict")
    except UnicodeError:
        _add(errors, f"artifact_utf8_invalid:{key}")
        return worktree_raw, None
    if kind == "json":
        try:
            parsed_worktree = parse_json_object(worktree_raw)
        except (UnicodeError, json.JSONDecodeError, ValueError):
            _add(errors, f"artifact_json_invalid:{key}")
    elif kind == "malformed_json":
        try:
            json.loads(worktree_text)
        except json.JSONDecodeError:
            pass
        else:
            code = (
                "terminal_payload_failure_not_reproducible"
                if key == "payload"
                else "terminal_model_final_failure_not_reproducible"
            )
            _add(errors, code)
    return worktree_raw, parsed_worktree


def _default_historical_check(git_root: Path) -> bool:
    try:
        result = subprocess.run(
            [
                "git",
                "diff",
                "--exit-code",
                HISTORICAL_EVIDENCE_HEAD,
                "--",
                HISTORICAL_RESULT_ROOT,
            ],
            cwd=git_root,
            capture_output=True,
            check=False,
        )
    except OSError:
        return False
    return result.returncode == 0 and not result.stdout and not result.stderr


def _verify_result_root(artifact_root: Path, errors: list[str]) -> None:
    root = artifact_root / RESULT_ROOT_RELATIVE
    if not root.is_dir() or root.is_symlink():
        _add(errors, "terminal_result_root_invalid")
        return
    names = {path.name for path in root.iterdir()}
    for name in sorted(REQUIRED_RESULT_FILES - names):
        _add(errors, f"missing_result_artifact:{name}")
    for name in sorted(names):
        if name in FORBIDDEN_RESULT_FILES:
            _add(errors, f"forbidden_result_artifact:{name}")
        elif name not in ALLOWED_RESULT_FILES:
            _add(errors, f"unexpected_result_artifact:{name}")


def _expect(value: Any, required: Any, errors: list[str], code: str) -> None:
    if isinstance(required, int) and not isinstance(required, bool):
        if isinstance(value, bool) or value != required:
            _add(errors, code)
    elif value != required:
        _add(errors, code)


def audit_terminal(
    path: str | Path,
    *,
    artifact_root: Path = REPO_ROOT,
    git_root: Path = REPO_ROOT,
    historical_check: Callable[[], bool] | None = None,
) -> dict[str, Any]:
    """Verify the terminal failure without writing, repairing, or re-running it."""

    errors: list[str] = []
    manifest = _load_manifest(Path(path), errors)
    if manifest is None:
        manifest = {}
    errors.extend(validate_terminal_manifest_shape(manifest))
    _verify_result_root(artifact_root, errors)

    raw: dict[str, bytes | None] = {}
    values: dict[str, dict[str, Any] | None] = {}
    artifacts = manifest.get("artifacts")
    if isinstance(artifacts, dict):
        for key in ARTIFACT_SPECS:
            raw[key], values[key] = _verify_artifact(
                key,
                manifest,
                artifact_root=artifact_root,
                git_root=git_root,
                errors=errors,
            )

    authorization = values.get("execution_authorization")
    authorization_raw = raw.get("execution_authorization")
    if isinstance(authorization, dict):
        for code in validate_execution_authorization_shape(authorization):
            _add(errors, f"execution_authorization_invalid:{code}")
        if authorization.get("authorization_token") != AUTHORIZATION_TOKEN:
            _add(errors, "authorization_token_mismatch")
    else:
        _add(errors, "execution_authorization_unavailable")

    launch_attempt = values.get("launch_attempt") or {}
    for field, required in {
        "case_id": CASE_ID,
        "revision": REVISION,
        "authorization_token": AUTHORIZATION_TOKEN,
        "attempt_count": 1,
        "max_fresh_tasks": 1,
        "no_retry": True,
    }.items():
        _expect(
            launch_attempt.get(field),
            required,
            errors,
            f"launch_attempt_field_invalid:{field}",
        )

    launch = values.get("launch_receipt") or {}
    if isinstance(authorization, dict):
        for code in validate_launch_receipt(
            launch,
            authorization,
            authorization_raw=authorization_raw,
        ):
            _add(errors, f"launch_receipt_invalid:{code}")
    if launch.get("fresh_task_id") != FRESH_TASK_ID:
        _add(errors, "task_id_mismatch")
    if launch.get("fresh_task_id") == HISTORICAL_TASK_ID:
        _add(errors, "historical_task_id_reuse_forbidden")
    _expect(launch.get("launch_count"), 1, errors, "launch_count_invalid")

    model_raw = raw.get("model_final")
    payload_raw = raw.get("payload")
    if model_raw is not None and payload_raw is not None and model_raw != payload_raw:
        _add(errors, "model_final_payload_bytes_mismatch")

    composer = values.get("composer_receipt") or {}
    _expect(composer.get("status"), "failed", errors, "composer_status_invalid")
    _expect(
        composer.get("composer_invocation_count"),
        1,
        errors,
        "composer_invocation_count_invalid",
    )
    _expect(
        composer.get("failure_stage"),
        "composition",
        errors,
        "composer_failure_stage_invalid",
    )
    _expect(
        composer.get("failure_code"),
        "payload_invalid_json",
        errors,
        "composer_failure_code_invalid",
    )
    _expect(composer.get("retry_count"), 0, errors, "retry_count_invalid")
    if model_raw is not None and composer.get("model_final_sha256") != sha256(model_raw):
        _add(errors, "composer_model_final_hash_mismatch")
    if payload_raw is not None and composer.get("payload_sha256") != sha256(payload_raw):
        _add(errors, "composer_payload_hash_mismatch")
    source_raw = raw.get("source_input")
    if source_raw is not None and composer.get("source_sha256") != sha256(source_raw):
        _add(errors, "composer_source_hash_mismatch")

    context = values.get("context") or {}
    transaction = values.get("transaction") or {}
    for value in (context, transaction):
        if value.get("task_id") != FRESH_TASK_ID:
            _add(errors, "task_id_mismatch")
        _expect(value.get("state"), "processing_failed", errors, "transaction_state_invalid")
        _expect(value.get("accepted"), False, errors, "transaction_accepted_invalid")
        _expect(
            value.get("task_finalizations_observed"),
            1,
            errors,
            "finalization_count_invalid",
        )
        _expect(
            value.get("dispatcher_cases_preflighted"),
            1,
            errors,
            "dispatcher_preflight_count_invalid",
        )
        _expect(
            value.get("composer_invocations"),
            1,
            errors,
            "composer_invocation_count_invalid",
        )
        _expect(
            value.get("validator_invocations"),
            0,
            errors,
            "validator_invocation_count_invalid",
        )
        if value.get("transaction_failures") != ["composer_invocation_failed"]:
            _add(errors, "transaction_failure_inconsistent")
    _expect(transaction.get("tasks_launched"), 1, errors, "tasks_launched_invalid")
    _expect(
        transaction.get("dispatcher_cases_processed"),
        0,
        errors,
        "dispatcher_processed_count_invalid",
    )
    _expect(
        context.get("dispatcher_cases_processed"),
        0,
        errors,
        "dispatcher_processed_count_invalid",
    )
    if model_raw is not None:
        _expect(
            context.get("final_raw_sha256"),
            sha256(model_raw),
            errors,
            "context_final_hash_mismatch",
        )
        _expect(
            context.get("final_byte_length"),
            len(model_raw),
            errors,
            "context_final_length_mismatch",
        )

    validation_raw = raw.get("execution_validation")
    if validation_raw is not None:
        validation_text = validation_raw.decode("utf-8", errors="strict")
        required_lines = {
            "- Fresh task ID: `019fdb7c-1728-7a92-b6cf-b0eb631a18b8`",
            "- Callback invocation count: `1`",
            "- Finalization count: `1`",
            "- Accepted: `false`",
            "- Transaction state: `processing_failed`",
            "- Failure code: `payload_invalid_json`",
            "NO RETRY PERMITTED",
        }
        for line in sorted(required_lines):
            if line not in validation_text:
                _add(errors, "execution_validation_fact_missing")

    historical_ok = (
        historical_check()
        if historical_check is not None
        else _default_historical_check(git_root)
    )
    if not historical_ok:
        _add(errors, "historical_r5_changed")

    counters = manifest.get("counters") if isinstance(manifest, dict) else None
    if counters != COUNTERS:
        _add(errors, "terminal_counters_invalid")
    failure = manifest.get("failure") if isinstance(manifest, dict) else None
    if failure != {
        "failure_stage": "composition",
        "failure_code": "payload_invalid_json",
        "transaction_failure": "composer_invocation_failed",
    }:
        _add(errors, "terminal_failure_invalid")

    errors = sorted(set(errors))
    return {
        "status": "terminal_not_accepted" if not errors else "invalid",
        "case_id": manifest.get("case_id"),
        "revision": manifest.get("revision"),
        "accepted": manifest.get("accepted"),
        "transaction_state": transaction.get("state"),
        "failure_stage": composer.get("failure_stage"),
        "failure_code": composer.get("failure_code"),
        "fresh_task_id": manifest.get("fresh_task_id"),
        "tasks_launched": transaction.get("tasks_launched"),
        "task_finalizations_observed": transaction.get(
            "task_finalizations_observed"
        ),
        "composer_invocations": transaction.get("composer_invocations"),
        "validator_invocations": transaction.get("validator_invocations"),
        "retry_count": composer.get("retry_count"),
        "historical_f02_retry_count": COUNTERS["historical_f02_retry_count"],
        "historical_r5_unchanged": historical_ok,
        "execution_authorization_head": EXECUTION_AUTHORIZATION_HEAD,
        "execution_evidence_head": EXECUTION_EVIDENCE_HEAD,
        "errors": errors,
        "evidence_gaps": [],
        "side_effects": [],
        "later_gates": "NOT_RUN",
        "does_not_prove": [
            "F02 acceptance.",
            "A retry or repair of F02.",
            "Authorization for another r5.1-f02 task.",
            "Cross-revision aggregate acceptance.",
            "M3 closure or M4 start.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) > 1:
        return 2
    path = Path(arguments[0]) if arguments else TERMINAL_MANIFEST
    result = audit_terminal(path)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0 if result["status"] == "terminal_not_accepted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
