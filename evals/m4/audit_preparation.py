from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path
from typing import Any


M4_ROOT = Path("evals/m4")
MANIFEST_PATH = M4_ROOT / "preparation-manifest.json"
BASELINE_COMMIT = "eb0f2ebc3d0c0a02802ee1cc395c1e705f8ade42"
ARM_IDS = {"N", "F", "A1", "A2", "A3"}
DOMAIN_IDS = {
    "nuclear_engineering",
    "mechanical_engineering",
    "electrical_engineering",
    "automation_control",
    "computer_data",
    "multiphysics",
}
TOP_LEVEL_KEYS = {
    "schema_version",
    "milestone",
    "revision",
    "status",
    "baseline",
    "authority",
    "matrix",
    "execution_constraints",
    "randomization",
    "artifacts",
    "tasks",
    "counters",
}
TASK_KEYS = {
    "task_id",
    "case_id",
    "domain",
    "case_type",
    "arm_id",
    "batch_id",
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
    "blind_id",
}


def _load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("JSON root must be an object")
    return value


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _add(errors: list[str], code: str) -> None:
    if code not in errors:
        errors.append(code)


def _git(repo_root: Path, *args: str, allowed: tuple[int, ...] = (0,)) -> tuple[int, str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    if completed.returncode not in allowed:
        raise RuntimeError(completed.stderr.strip() or f"git {' '.join(args)} failed")
    return completed.returncode, completed.stdout.strip()


def _load_builder():
    path = Path(__file__).with_name("build_preparation.py")
    spec = importlib.util.spec_from_file_location("m4_build_preparation_for_audit", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load preparation builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def audit_manifest(
    manifest: dict[str, Any],
    repo_root: Path,
    *,
    verify_git: bool = True,
    expected_manifest: dict[str, Any] | None = None,
) -> dict[str, object]:
    errors: list[str] = []
    if set(manifest) != TOP_LEVEL_KEYS:
        _add(errors, "preparation_shape_invalid")
    if manifest.get("schema_version") != "m4-preparation-manifest-v1":
        _add(errors, "preparation_schema_version_invalid")
    if manifest.get("milestone") != "M4" or manifest.get("revision") != "M4.0":
        _add(errors, "preparation_revision_invalid")
    if manifest.get("status") != "PREPARATION_ONLY":
        _add(errors, "preparation_status_invalid")

    authority = manifest.get("authority")
    if not isinstance(authority, dict):
        authority = {}
        _add(errors, "authority_shape_invalid")
    for key in (
        "fresh_execution_authorized",
        "fresh_tasks_authorized",
        "result_writes_authorized",
        "retry_authorized",
        "repair_authorized",
    ):
        if authority.get(key) is not False:
            _add(
                errors,
                "fresh_execution_authority_forbidden"
                if key == "fresh_execution_authorized"
                else f"{key}_forbidden",
            )
    if authority.get("authorization_artifact") is not None:
        _add(errors, "authorization_artifact_must_be_absent")
    if authority.get("model_binding_status") != "UNBOUND_UNTIL_SEPARATE_AUTHORIZATION":
        _add(errors, "model_must_remain_unbound")

    matrix = manifest.get("matrix")
    if not isinstance(matrix, dict):
        matrix = {}
        _add(errors, "matrix_shape_invalid")
    if matrix.get("case_count") != 12:
        _add(errors, "case_count_invalid")
    if matrix.get("arm_count") != 5 or set(matrix.get("arms", [])) != ARM_IDS:
        _add(errors, "arm_set_invalid")
    if matrix.get("planned_task_count") != 60:
        _add(errors, "planned_task_count_invalid")
    if set(matrix.get("domains", [])) != DOMAIN_IDS:
        _add(errors, "domain_set_invalid")
    batches = matrix.get("batches")
    if not isinstance(batches, list) or len(batches) != 6:
        _add(errors, "batch_set_invalid")
    elif any(batch.get("planned_task_count") != 10 for batch in batches):
        _add(errors, "batch_task_count_invalid")

    constraints = manifest.get("execution_constraints")
    if not isinstance(constraints, dict):
        constraints = {}
        _add(errors, "execution_constraints_invalid")
    if constraints.get("exact_model_id") is not None:
        _add(errors, "exact_model_bound_without_authority")
    if constraints.get("same_model_across_arms") is not True:
        _add(errors, "same_model_constraint_missing")
    if constraints.get("same_user_input_across_arms") is not True:
        _add(errors, "same_user_input_constraint_missing")
    if constraints.get("same_scoring_contract_across_arms") is not True:
        _add(errors, "same_scoring_constraint_missing")
    if constraints.get("cross_task_result_visibility") is not False:
        _add(errors, "cross_task_visibility_forbidden")
    if constraints.get("same_task_retry_count") != 0:
        _add(errors, "retry_count_nonzero")

    counters = manifest.get("counters")
    if not isinstance(counters, dict) or not counters:
        _add(errors, "execution_counters_invalid")
        counters = {}
    if any(value != 0 for value in counters.values()):
        _add(errors, "execution_counter_nonzero")

    tasks = manifest.get("tasks")
    if not isinstance(tasks, list):
        tasks = []
        _add(errors, "tasks_shape_invalid")
    if len(tasks) != 60:
        _add(errors, "task_count_invalid")
    task_ids = [task.get("task_id") for task in tasks if isinstance(task, dict)]
    blind_ids = [task.get("blind_id") for task in tasks if isinstance(task, dict)]
    if len(set(task_ids)) != len(task_ids):
        _add(errors, "task_id_reused")
    if len(set(blind_ids)) != len(blind_ids):
        _add(errors, "blind_id_reused")
    if any(not isinstance(task, dict) or set(task) != TASK_KEYS for task in tasks):
        _add(errors, "task_shape_invalid")
    if {task.get("arm_id") for task in tasks if isinstance(task, dict)} != ARM_IDS:
        _add(errors, "task_arm_set_invalid")
    per_case: dict[str, list[dict[str, Any]]] = {}
    for task in tasks:
        if not isinstance(task, dict):
            continue
        per_case.setdefault(task.get("case_id", ""), []).append(task)
    if len(per_case) != 12 or any(len(case_tasks) != 5 for case_tasks in per_case.values()):
        _add(errors, "case_arm_matrix_invalid")
    for case_tasks in per_case.values():
        if {task.get("arm_id") for task in case_tasks} != ARM_IDS:
            _add(errors, "case_arm_matrix_invalid")
        for field in (
            "case_sha256",
            "user_input_sha256",
            "task_protocol_sha256",
            "rubric_sha256",
            "execution_constraints_sha256",
        ):
            if len({task.get(field) for task in case_tasks}) != 1:
                _add(errors, "cross_arm_input_hash_mismatch")

    randomization = manifest.get("randomization")
    if not isinstance(randomization, dict):
        randomization = {}
        _add(errors, "randomization_shape_invalid")
    if randomization.get("frozen") is not True:
        _add(errors, "randomization_not_frozen")
    if randomization.get("algorithm") != "sha256_lexicographic_v1":
        _add(errors, "randomization_algorithm_invalid")
    if randomization.get("task_order") != task_ids:
        _add(errors, "randomization_order_invalid")
    expected_order = sorted(
        task_ids,
        key=lambda task_id: _sha256(f"m4.0-order-v1:{task_id}".encode("utf-8")),
    )
    if task_ids != expected_order:
        _add(errors, "randomization_order_invalid")
    mapping = randomization.get("blind_mapping")
    if not isinstance(mapping, dict) or mapping != dict(zip(task_ids, blind_ids)):
        _add(errors, "blind_mapping_invalid")
    if randomization.get("judge_mapping_access_authorized") is not False:
        _add(errors, "judge_mapping_access_forbidden")

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict) or not artifacts:
        artifacts = {}
        _add(errors, "artifact_manifest_invalid")
    for relative_path, record in artifacts.items():
        path = repo_root / relative_path
        if not path.is_file():
            _add(errors, "artifact_missing")
            continue
        data = path.read_bytes()
        if not isinstance(record, dict) or record.get("sha256") != _sha256(data):
            _add(errors, "artifact_hash_mismatch")
        elif record.get("bytes") != len(data):
            _add(errors, "artifact_size_mismatch")

    existing_result_roots: list[str] = []
    for task in tasks:
        if not isinstance(task, dict):
            continue
        if task.get("result_root_must_be_absent") is not True:
            _add(errors, "result_root_absence_gate_missing")
        result_root = repo_root / str(task.get("result_root", ""))
        if result_root.exists():
            existing_result_roots.append(str(task.get("result_root")))
    if existing_result_roots:
        _add(errors, "result_root_not_empty")
    if (repo_root / M4_ROOT / "results-manifest.json").exists():
        _add(errors, "previous_result_manifest_accessible")

    m3_changed_paths: list[str] = []
    if verify_git:
        _, diff_output = _git(
            repo_root,
            "diff",
            "--name-only",
            BASELINE_COMMIT,
            "--",
            "evals/m3",
            "skills/engineering-research-copilot",
        )
        m3_changed_paths.extend(line for line in diff_output.splitlines() if line)
        _, status_output = _git(
            repo_root,
            "status",
            "--porcelain",
            "--untracked-files=all",
            "--",
            "evals/m3",
            "skills/engineering-research-copilot",
        )
        m3_changed_paths.extend(line for line in status_output.splitlines() if line)
        m3_changed_paths = sorted(set(m3_changed_paths))
        if m3_changed_paths:
            _add(errors, "m3_evidence_or_skill_changed")
        baseline = manifest.get("baseline", {})
        _, m3_tree = _git(repo_root, "rev-parse", f"{BASELINE_COMMIT}:evals/m3")
        _, skill_tree = _git(
            repo_root,
            "rev-parse",
            f"{BASELINE_COMMIT}:skills/engineering-research-copilot",
        )
        if baseline.get("m3_evidence_tree_git_oid") != m3_tree:
            _add(errors, "m3_tree_binding_invalid")
        if baseline.get("skill_tree_git_oid") != skill_tree:
            _add(errors, "skill_tree_binding_invalid")
        grep_rc, grep_output = _git(
            repo_root,
            "grep",
            "-n",
            "M4-",
            BASELINE_COMMIT,
            "--",
            "evals/m1",
            "evals/m2",
            "evals/m3",
            allowed=(0, 1),
        )
        if grep_rc == 0 and grep_output:
            _add(errors, "historical_m4_task_id_reused")

    if expected_manifest is not None and manifest != expected_manifest:
        _add(errors, "preparation_manifest_frozen_mismatch")

    return {
        "status": "prepared" if not errors else "invalid",
        "errors": errors,
        "case_count": matrix.get("case_count", 0),
        "arm_count": matrix.get("arm_count", 0),
        "planned_task_count": len(tasks),
        "fresh_execution_authorized": authority.get("fresh_execution_authorized"),
        "execution_counters": counters,
        "existing_result_root_count": len(existing_result_roots),
        "m3_changed_paths": m3_changed_paths,
    }


def audit_preparation(repo_root: Path) -> dict[str, object]:
    path = repo_root / MANIFEST_PATH
    if not path.is_file():
        return {
            "status": "invalid",
            "errors": ["preparation_manifest_missing"],
            "case_count": 0,
            "arm_count": 0,
            "planned_task_count": 0,
            "fresh_execution_authorized": None,
            "execution_counters": {},
            "existing_result_root_count": 0,
            "m3_changed_paths": [],
        }
    try:
        manifest = _load_object(path)
        expected = _load_builder().build_preparation(repo_root, write=False)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError, RuntimeError):
        return {
            "status": "invalid",
            "errors": ["preparation_manifest_or_binding_invalid"],
            "case_count": 0,
            "arm_count": 0,
            "planned_task_count": 0,
            "fresh_execution_authorized": None,
            "execution_counters": {},
            "existing_result_root_count": 0,
            "m3_changed_paths": [],
        }
    return audit_manifest(
        manifest,
        repo_root,
        verify_git=True,
        expected_manifest=expected,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    result = audit_preparation(repo_root)
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return 0 if result["status"] == "prepared" else 1


if __name__ == "__main__":
    raise SystemExit(main())
