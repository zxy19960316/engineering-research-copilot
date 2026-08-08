from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
TERMINAL_HEAD = "f48ab8d7e835e9a57e65b75458faa786d696316d"
M4_0_AUTHORIZATION_HEAD = "e3542201f96218f340a09f77458661822c98d876"
CLAIM_SHA256 = "5690177383c44a30e808533ebdfe0b504c6da2abf8e61a1d0303d4c439c3ecec"
FAILURE_SHA256 = "8ef9487ce617aeafefc6d665a981581ffc046b541cf426f22d434be689f007ff"
CLAIM_BLOB_OID = "cfbcba7a28162ba489f3ed34effcf30ebebc499c"
FAILURE_BLOB_OID = "1a6bc8268adbfab7850daefac5f897c5e03f32aa"

M4_ROOT = Path("evals/m4")
BASE_MANIFEST_RELATIVE = M4_ROOT / "preparation-manifest.json"
MANIFEST_RELATIVE = M4_ROOT / "revisions/m4.1/preparation-manifest.json"
HELPER_RELATIVE = M4_ROOT / "execution/prepare_m4_1_request_bundles.ps1"
M4_0_CLAIM_RELATIVE = M4_ROOT / "execution/m4.0/launch-claim.json"
M4_0_FAILURE_RELATIVE = M4_ROOT / "execution/m4.0/pre-dispatch-failure.json"
M4_1_CLAIM_RELATIVE = M4_ROOT / "execution/m4.1/launch-claim.json"
RESULTS_MANIFEST_RELATIVE = M4_ROOT / "results-manifest.json"

FROZEN_M3_AND_SKILL_PATHS = (
    "evals/m3",
    "skills/engineering-research-copilot",
)
FROZEN_BASE_PREPARATION_PATHS = (
    "evals/m4/cases",
    "evals/m4/variants",
    "evals/m4/schemas",
    "evals/m4/preparation-manifest.json",
    "evals/m4/task-protocol.md",
    "evals/m4/judge-rubric.json",
)
FROZEN_ROOT_AUTHORIZATION_PATHS = (
    "evals/m4/authorization/gate-iv-review.json",
    "evals/m4/authorization/execution-authorization.json",
    "evals/m4/authorization/execution-control.json",
)
FROZEN_M4_0_EVIDENCE_PATHS = (
    "evals/m4/execution/m4.0/launch-claim.json",
    "evals/m4/execution/m4.0/pre-dispatch-failure.json",
)

TOP_LEVEL_KEYS = {
    "schema_version",
    "milestone",
    "revision",
    "status",
    "predecessor",
    "base_preparation",
    "authority",
    "matrix",
    "randomization",
    "execution_helper",
    "tasks",
    "counters",
}
TASK_KEYS = {
    "task_id",
    "source_task_id",
    "blind_id",
    "source_blind_id",
    "case_id",
    "domain",
    "case_type",
    "arm_id",
    "batch_id",
    "source_batch_id",
    "case_path",
    "case_sha256",
    "user_input_sha256",
    "task_protocol_sha256",
    "variant_instruction_path",
    "variant_instruction_sha256",
    "rubric_sha256",
    "execution_constraints_sha256",
    "result_root",
    "result_root_must_be_absent",
    "request_binding_sha256",
}
COUNTER_NAMES = {
    "authorized_tasks",
    "created_contexts",
    "dispatched_tasks",
    "finalizations",
    "results_observed",
    "judge_scores",
    "retries",
    "repairs",
    "unauthorized_side_effects",
}
INHERITED_TASK_FIELDS = (
    "case_id",
    "domain",
    "case_type",
    "arm_id",
    "case_path",
    "case_sha256",
    "user_input_sha256",
    "task_protocol_sha256",
    "variant_instruction_path",
    "variant_instruction_sha256",
    "rubric_sha256",
    "execution_constraints_sha256",
)
EXPECTED_AUTHORITY = {
    "fresh_execution_authorized": False,
    "fresh_tasks_authorized": False,
    "result_writes_authorized": False,
    "retry_authorized": False,
    "repair_authorized": False,
    "authorization_artifact": None,
    "model_binding_status": "UNBOUND_UNTIL_SEPARATE_AUTHORIZATION",
}


def _add(errors: list[str], code: str) -> None:
    if code not in errors:
        errors.append(code)


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _load_object(
    path: Path, label: str, errors: list[str]
) -> tuple[dict[str, Any], bytes]:
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


def _load_module(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot_load_{name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _git(repo_root: Path, *arguments: str) -> tuple[int, str]:
    try:
        completed = subprocess.run(
            ["git", *arguments],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    except OSError:
        return 127, ""
    return completed.returncode, completed.stdout.strip()


def _commit_is_available_and_ancestor(
    repo_root: Path, commit: str, label: str, errors: list[str]
) -> bool:
    returncode, _ = _git(repo_root, "cat-file", "-e", f"{commit}^{{commit}}")
    if returncode != 0:
        _add(errors, f"{label}_unavailable")
        return False
    returncode, _ = _git(
        repo_root, "merge-base", "--is-ancestor", commit, "HEAD"
    )
    if returncode != 0:
        _add(errors, f"{label}_not_ancestor")
        return False
    return True


def _changed_paths(
    repo_root: Path,
    baseline: str,
    paths: tuple[str, ...],
    label: str,
    errors: list[str],
) -> list[str]:
    changed: set[str] = set()
    returncode, output = _git(
        repo_root, "diff", "--name-only", baseline, "HEAD", "--", *paths
    )
    if returncode != 0:
        _add(errors, f"{label}_git_diff_failed")
    else:
        changed.update(line for line in output.splitlines() if line)
    returncode, output = _git(
        repo_root,
        "status",
        "--porcelain",
        "--untracked-files=all",
        "--",
        *paths,
    )
    if returncode != 0:
        _add(errors, f"{label}_git_status_failed")
    else:
        changed.update(line[3:] for line in output.splitlines() if len(line) > 3)
    if changed:
        _add(errors, f"{label}_changed")
    return sorted(changed)


def _validate_m4_0_evidence(
    repo_root: Path,
    claim_raw: bytes,
    failure_raw: bytes,
    errors: list[str],
) -> None:
    if _sha256(claim_raw) != CLAIM_SHA256:
        _add(errors, "m4_0_claim_raw_sha256_mismatch")
    if _sha256(failure_raw) != FAILURE_SHA256:
        _add(errors, "m4_0_failure_raw_sha256_mismatch")
    for relative_path, expected_blob, label in (
        (M4_0_CLAIM_RELATIVE, CLAIM_BLOB_OID, "m4_0_claim"),
        (M4_0_FAILURE_RELATIVE, FAILURE_BLOB_OID, "m4_0_failure"),
    ):
        git_path = relative_path.as_posix()
        returncode, blob = _git(repo_root, "rev-parse", f"HEAD:{git_path}")
        if returncode != 0 or blob != expected_blob:
            _add(errors, f"{label}_head_blob_mismatch")
        returncode, blob = _git(
            repo_root, "rev-parse", f"{TERMINAL_HEAD}:{git_path}"
        )
        if returncode != 0 or blob != expected_blob:
            _add(errors, f"{label}_terminal_blob_mismatch")


def _validate_identity_projection(
    manifest: dict[str, Any],
    base: dict[str, Any],
    builder: ModuleType | None,
    errors: list[str],
) -> tuple[list[dict[str, Any]], int]:
    tasks_value = manifest.get("tasks")
    tasks = tasks_value if isinstance(tasks_value, list) else []
    base_tasks_value = base.get("tasks")
    base_tasks = base_tasks_value if isinstance(base_tasks_value, list) else []
    if len(tasks) != 60:
        _add(errors, "planned_task_count_invalid")
    if len(base_tasks) != 60:
        _add(errors, "base_task_count_invalid")
    if any(not isinstance(task, dict) or set(task) != TASK_KEYS for task in tasks):
        _add(errors, "task_shape_invalid")

    old_task_ids = [
        task.get("task_id") for task in base_tasks if isinstance(task, dict)
    ]
    new_task_ids = [task.get("task_id") for task in tasks if isinstance(task, dict)]
    source_task_ids = [
        task.get("source_task_id") for task in tasks if isinstance(task, dict)
    ]
    reused_task_ids = set(new_task_ids).intersection(old_task_ids)
    if len(new_task_ids) != len(set(new_task_ids)):
        _add(errors, "task_id_not_unique")
    if reused_task_ids:
        _add(errors, "task_id_reused")
    if source_task_ids != old_task_ids:
        _add(errors, "task_order_changed")

    expected_blind_ids = [f"M4-J{index:03d}" for index in range(61, 121)]
    blind_ids = [task.get("blind_id") for task in tasks if isinstance(task, dict)]
    if blind_ids != expected_blind_ids or len(blind_ids) != len(set(blind_ids)):
        _add(errors, "blind_id_projection_invalid")
    old_blind_ids = [
        task.get("blind_id") for task in base_tasks if isinstance(task, dict)
    ]
    if set(blind_ids).intersection(old_blind_ids):
        _add(errors, "blind_id_reused")

    projection_invalid = False
    for source, task in zip(base_tasks, tasks):
        if not isinstance(source, dict) or not isinstance(task, dict):
            projection_invalid = True
            continue
        if task.get("source_task_id") != source.get("task_id"):
            projection_invalid = True
        if task.get("source_blind_id") != source.get("blind_id"):
            projection_invalid = True
        if task.get("source_batch_id") != source.get("batch_id"):
            projection_invalid = True
        if any(task.get(field) != source.get(field) for field in INHERITED_TASK_FIELDS):
            projection_invalid = True
        if builder is not None:
            try:
                expected_task_id = builder.successor_task_id(str(source["task_id"]))
                expected_batch_id = builder.successor_batch_id(str(source["batch_id"]))
            except (AttributeError, KeyError, TypeError, ValueError):
                projection_invalid = True
            else:
                if task.get("task_id") != expected_task_id:
                    projection_invalid = True
                if task.get("batch_id") != expected_batch_id:
                    projection_invalid = True
    if projection_invalid:
        _add(errors, "task_identity_projection_invalid")

    randomization = manifest.get("randomization")
    if not isinstance(randomization, dict):
        _add(errors, "randomization_invalid")
    else:
        if randomization.get("task_order") != new_task_ids:
            _add(errors, "task_order_changed")
        if randomization.get("blind_mapping") != dict(zip(new_task_ids, blind_ids)):
            _add(errors, "blind_mapping_invalid")
        if randomization.get("frozen") is not True:
            _add(errors, "randomization_not_frozen")
        if randomization.get("judge_mapping_access_authorized") is not False:
            _add(errors, "judge_mapping_access_authorized")

    return [task for task in tasks if isinstance(task, dict)], len(reused_task_ids)


def _validate_batches(
    manifest: dict[str, Any], base: dict[str, Any], errors: list[str]
) -> None:
    matrix = manifest.get("matrix")
    base_matrix = base.get("matrix")
    if not isinstance(matrix, dict) or not isinstance(base_matrix, dict):
        _add(errors, "matrix_invalid")
        return
    batches = matrix.get("batches")
    base_batches = base_matrix.get("batches")
    if not isinstance(batches, list) or len(batches) != 6:
        _add(errors, "batch_count_invalid")
        return
    if not isinstance(base_batches, list) or len(base_batches) != 6:
        _add(errors, "base_batch_count_invalid")
        return
    if (
        matrix.get("case_count") != 12
        or matrix.get("arm_count") != 5
        or matrix.get("planned_task_count") != 60
        or matrix.get("batch_count") != 6
    ):
        _add(errors, "matrix_cardinality_invalid")
    old_batch_ids = [
        batch.get("batch_id") for batch in base_batches if isinstance(batch, dict)
    ]
    new_batch_ids = [
        batch.get("batch_id") for batch in batches if isinstance(batch, dict)
    ]
    source_batch_ids = [
        batch.get("source_batch_id") for batch in batches if isinstance(batch, dict)
    ]
    if len(new_batch_ids) != len(set(new_batch_ids)) or set(new_batch_ids).intersection(
        old_batch_ids
    ):
        _add(errors, "batch_id_projection_invalid")
    if source_batch_ids != old_batch_ids:
        _add(errors, "batch_order_changed")
    for source, batch in zip(base_batches, batches):
        if not isinstance(source, dict) or not isinstance(batch, dict):
            _add(errors, "batch_projection_invalid")
            continue
        if batch.get("source_task_ids") != source.get("task_ids"):
            _add(errors, "batch_projection_invalid")
        if batch.get("planned_task_count") != 10:
            _add(errors, "batch_task_count_invalid")


def _validate_request_bindings(
    tasks: list[dict[str, Any]], builder: ModuleType | None, errors: list[str]
) -> None:
    hashes: list[Any] = []
    for task in tasks:
        actual = task.get("request_binding_sha256")
        hashes.append(actual)
        if builder is None:
            continue
        try:
            expected = builder.request_binding_sha256(task)
        except (AttributeError, KeyError, TypeError, ValueError):
            _add(errors, "request_binding_regeneration_failed")
            continue
        if actual != expected:
            _add(errors, "request_binding_mismatch")
    if len(hashes) != 60 or len(set(hashes)) != len(hashes):
        _add(errors, "request_binding_set_invalid")
    if any(not isinstance(value, str) or len(value) != 64 for value in hashes):
        _add(errors, "request_binding_set_invalid")


def _validate_helper(
    repo_root: Path, manifest: dict[str, Any], errors: list[str]
) -> None:
    helper = manifest.get("execution_helper")
    if not isinstance(helper, dict):
        _add(errors, "execution_helper_invalid")
        return
    path = helper.get("path")
    if path != HELPER_RELATIVE.as_posix():
        _add(errors, "execution_helper_path_invalid")
        return
    try:
        raw = (repo_root / HELPER_RELATIVE).read_bytes()
    except OSError:
        _add(errors, "execution_helper_missing")
        return
    if helper.get("raw_sha256") != _sha256(raw):
        _add(errors, "execution_helper_hash_mismatch")
    source = raw.decode("utf-8", errors="replace")
    if "[Convert]::ToHexString" in source or "SHA256]::HashData" in source:
        _add(errors, "execution_helper_incompatible_api")
    if helper.get("request_binding_count") != 60:
        _add(errors, "execution_helper_request_count_invalid")


def audit_preparation(
    repo_root: Path = REPO_ROOT,
    *,
    manifest_path: Path | None = None,
    results_base: Path | None = None,
    launch_claim_path: Path | None = None,
    verify_git: bool = True,
) -> dict[str, object]:
    repo_root = repo_root.resolve()
    manifest_path = manifest_path or (repo_root / MANIFEST_RELATIVE)
    launch_claim_path = launch_claim_path or (repo_root / M4_1_CLAIM_RELATIVE)
    errors: list[str] = []

    manifest, _ = _load_object(manifest_path, "m4_1_manifest", errors)
    base, base_raw = _load_object(
        repo_root / BASE_MANIFEST_RELATIVE, "base_preparation_manifest", errors
    )
    _, claim_raw = _load_object(
        repo_root / M4_0_CLAIM_RELATIVE, "m4_0_claim", errors
    )
    _, failure_raw = _load_object(
        repo_root / M4_0_FAILURE_RELATIVE, "m4_0_failure", errors
    )

    try:
        builder = _load_module(
            repo_root / "evals/m4/build_m4_1_preparation.py",
            "m4_1_preparation_builder_for_audit",
        )
        expected_manifest = builder.build_preparation(repo_root, write=False)
    except (
        AttributeError,
        OSError,
        TypeError,
        UnicodeError,
        json.JSONDecodeError,
        RuntimeError,
        ValueError,
    ):
        builder = None
        expected_manifest = None
        _add(errors, "preparation_regeneration_failed")

    if set(manifest) != TOP_LEVEL_KEYS:
        _add(errors, "preparation_shape_invalid")
    if manifest.get("schema_version") != "m4.1-successor-preparation-v1":
        _add(errors, "preparation_schema_version_invalid")
    if (
        manifest.get("milestone") != "M4"
        or manifest.get("revision") != "M4.1"
        or manifest.get("status") != "PREPARATION_ONLY"
    ):
        _add(errors, "preparation_identity_invalid")
    if expected_manifest is not None and manifest != expected_manifest:
        _add(errors, "preparation_manifest_regeneration_mismatch")

    predecessor = manifest.get("predecessor")
    if not isinstance(predecessor, dict):
        _add(errors, "predecessor_invalid")
    else:
        expected_predecessor = {
            "terminal_head": TERMINAL_HEAD,
            "terminal_ci_run_id": 31246286753,
            "terminal_ci_conclusion": "success",
            "m4_0_authorization_token_status": "CONSUMED",
            "m4_0_task_ids_consumed": 60,
            "m4_0_observed_contexts": 0,
        }
        for key, value in expected_predecessor.items():
            if predecessor.get(key) != value:
                _add(errors, "predecessor_invalid")
        claim_binding = predecessor.get("launch_claim")
        failure_binding = predecessor.get("pre_dispatch_failure")
        expected_claim_binding = {
            "path": M4_0_CLAIM_RELATIVE.as_posix(),
            "sha256": CLAIM_SHA256,
            "git_blob_oid": CLAIM_BLOB_OID,
        }
        expected_failure_binding = {
            "path": M4_0_FAILURE_RELATIVE.as_posix(),
            "sha256": FAILURE_SHA256,
            "git_blob_oid": FAILURE_BLOB_OID,
        }
        if claim_binding != expected_claim_binding:
            _add(errors, "predecessor_claim_binding_invalid")
        if failure_binding != expected_failure_binding:
            _add(errors, "predecessor_failure_binding_invalid")

    if manifest.get("authority") != EXPECTED_AUTHORITY:
        _add(errors, "preparation_authority_invalid")
    authority = manifest.get("authority")
    fresh_execution_authorized = (
        authority.get("fresh_execution_authorized")
        if isinstance(authority, dict)
        else None
    )
    if fresh_execution_authorized is not False:
        _add(errors, "fresh_execution_authorized")

    counters = manifest.get("counters")
    if not isinstance(counters, dict) or set(counters) != COUNTER_NAMES:
        _add(errors, "execution_counters_invalid")
        counters = counters if isinstance(counters, dict) else {}
    if any(value != 0 for value in counters.values()):
        _add(errors, "execution_counter_nonzero")

    tasks, reused_task_id_count = _validate_identity_projection(
        manifest, base, builder, errors
    )
    _validate_batches(manifest, base, errors)
    _validate_request_bindings(tasks, builder, errors)
    _validate_helper(repo_root, manifest, errors)

    base_binding = manifest.get("base_preparation")
    if not isinstance(base_binding, dict):
        _add(errors, "base_preparation_binding_invalid")
    else:
        if base_binding.get("raw_sha256") != _sha256(base_raw):
            _add(errors, "base_preparation_hash_mismatch")

    existing_result_roots: list[str] = []
    base_tasks = base.get("tasks") if isinstance(base.get("tasks"), list) else []
    for task in base_tasks:
        if not isinstance(task, dict):
            continue
        relative = task.get("result_root")
        if isinstance(relative, str) and (repo_root / relative).exists():
            existing_result_roots.append(str(task.get("task_id")))
    for task in tasks:
        if task.get("result_root_must_be_absent") is not True:
            _add(errors, "result_root_absence_gate_missing")
        relative = task.get("result_root")
        relative_path = Path(relative) if isinstance(relative, str) else Path()
        safe_relative = (
            isinstance(relative, str)
            and not relative_path.is_absolute()
            and ".." not in relative_path.parts
            and relative.startswith("evals/m4/results/m4.1/")
        )
        if not safe_relative:
            _add(errors, "result_root_invalid")
            continue
        if results_base is None:
            path = repo_root / relative_path
        else:
            path = results_base / str(task.get("task_id", ""))
        if path.exists():
            existing_result_roots.append(str(task.get("task_id")))
    if existing_result_roots:
        _add(errors, "result_root_present")
    results_manifest_present = (repo_root / RESULTS_MANIFEST_RELATIVE).exists()
    if results_manifest_present:
        _add(errors, "results_manifest_present")
    launch_claim_present = launch_claim_path.exists()
    if launch_claim_present:
        _add(errors, "launch_claim_present")

    m4_0_status: object = None
    try:
        m4_0_module = _load_module(
            repo_root / "evals/m4/execution/audit_m4_0.py",
            "m4_0_terminal_audit_for_m4_1",
        )
        m4_0_audit = m4_0_module.audit_execution(
            repo_root, verify_git=verify_git
        )
        m4_0_status = m4_0_audit.get("status")
        if m4_0_status != "PRE_DISPATCH_FAILED_PRESERVED":
            _add(errors, "m4_0_terminal_audit_failed")
    except (OSError, RuntimeError, ValueError):
        _add(errors, "m4_0_terminal_audit_failed")

    m3_changed_paths: list[str] = []
    base_preparation_changed_paths: list[str] = []
    root_authorization_changed_paths: list[str] = []
    m4_0_evidence_changed_paths: list[str] = []
    if verify_git:
        terminal_available = _commit_is_available_and_ancestor(
            repo_root, TERMINAL_HEAD, "terminal_head", errors
        )
        _commit_is_available_and_ancestor(
            repo_root, M4_0_AUTHORIZATION_HEAD, "m4_0_authorization_head", errors
        )
        if terminal_available:
            _validate_m4_0_evidence(
                repo_root, claim_raw, failure_raw, errors
            )
            m3_changed_paths = _changed_paths(
                repo_root,
                TERMINAL_HEAD,
                FROZEN_M3_AND_SKILL_PATHS,
                "m3_or_skill",
                errors,
            )
            base_preparation_changed_paths = _changed_paths(
                repo_root,
                TERMINAL_HEAD,
                FROZEN_BASE_PREPARATION_PATHS,
                "base_preparation",
                errors,
            )
            root_authorization_changed_paths = _changed_paths(
                repo_root,
                TERMINAL_HEAD,
                FROZEN_ROOT_AUTHORIZATION_PATHS,
                "root_authorization",
                errors,
            )
            m4_0_evidence_changed_paths = _changed_paths(
                repo_root,
                TERMINAL_HEAD,
                FROZEN_M4_0_EVIDENCE_PATHS,
                "m4_0_evidence",
                errors,
            )
    else:
        if _sha256(claim_raw) != CLAIM_SHA256:
            _add(errors, "m4_0_claim_raw_sha256_mismatch")
        if _sha256(failure_raw) != FAILURE_SHA256:
            _add(errors, "m4_0_failure_raw_sha256_mismatch")

    return {
        "status": "PREPARED_NOT_AUTHORIZED" if not errors else "INVALID",
        "errors": sorted(errors),
        "m4_0_status": m4_0_status,
        "terminal_head": TERMINAL_HEAD,
        "planned_task_count": len(tasks),
        "reused_task_id_count": reused_task_id_count,
        "batch_count": len(manifest.get("matrix", {}).get("batches", []))
        if isinstance(manifest.get("matrix"), dict)
        and isinstance(manifest.get("matrix", {}).get("batches"), list)
        else 0,
        "request_binding_count": len(
            {
                task.get("request_binding_sha256")
                for task in tasks
                if isinstance(task.get("request_binding_sha256"), str)
            }
        ),
        "fresh_execution_authorized": fresh_execution_authorized,
        "execution_counters": counters,
        "existing_result_root_count": len(set(existing_result_roots)),
        "results_manifest_present": results_manifest_present,
        "launch_claim_present": launch_claim_present,
        "m3_changed_paths": m3_changed_paths,
        "base_preparation_changed_paths": base_preparation_changed_paths,
        "root_authorization_changed_paths": root_authorization_changed_paths,
        "m4_0_evidence_changed_paths": m4_0_evidence_changed_paths,
        "side_effects": [],
    }


def main() -> int:
    result = audit_preparation()
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return 0 if result["status"] == "PREPARED_NOT_AUTHORIZED" else 1


if __name__ == "__main__":
    sys.exit(main())
