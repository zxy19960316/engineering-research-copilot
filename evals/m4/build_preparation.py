from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


M4_ROOT = Path("evals/m4")
CASES_ROOT = M4_ROOT / "cases"
SCHEMAS_ROOT = M4_ROOT / "schemas"
VARIANTS_ROOT = M4_ROOT / "variants"
MANIFEST_PATH = M4_ROOT / "preparation-manifest.json"
BASELINE_COMMIT = "eb0f2ebc3d0c0a02802ee1cc395c1e705f8ade42"
CLOSURE_DELIVERY_HEAD = "716c11b9154a1ff3b866b7f64d39b1c6a9039e54"
M3_TAG = "m3.1.1-closed"
ARM_IDS = ("N", "F", "A1", "A2", "A3")
DOMAIN_ORDER = (
    "nuclear_engineering",
    "mechanical_engineering",
    "electrical_engineering",
    "automation_control",
    "computer_data",
    "multiphysics",
)
DOMAIN_BATCH_IDS = {
    "nuclear_engineering": "M4-BATCH-NUC",
    "mechanical_engineering": "M4-BATCH-MEC",
    "electrical_engineering": "M4-BATCH-ELE",
    "automation_control": "M4-BATCH-AUT",
    "computer_data": "M4-BATCH-COM",
    "multiphysics": "M4-BATCH-MPH",
}
COUNTER_NAMES = (
    "authorized_tasks",
    "created_contexts",
    "dispatched_tasks",
    "finalizations",
    "results_observed",
    "judge_scores",
    "retries",
    "repairs",
    "unauthorized_side_effects",
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _canonical_sha256(value: object) -> str:
    data = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return _sha256(data)


def _load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _git(repo_root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or f"git {' '.join(args)} failed")
    return completed.stdout.strip()


def _artifact(repo_root: Path, relative_path: str, role: str) -> dict[str, object]:
    data = (repo_root / relative_path).read_bytes()
    return {"sha256": _sha256(data), "bytes": len(data), "role": role}


def _collect_artifacts(repo_root: Path, variant_manifest: dict[str, Any]) -> dict[str, object]:
    artifacts: dict[str, object] = {}
    for path in sorted((repo_root / CASES_ROOT).glob("*.json")):
        relative = path.relative_to(repo_root).as_posix()
        artifacts[relative] = _artifact(repo_root, relative, "case_input")
    fixed = {
        (M4_ROOT / "task-protocol.md").as_posix(): "common_task_protocol",
        (M4_ROOT / "judge-rubric.json").as_posix(): "judge_rubric",
        (VARIANTS_ROOT / "variant-manifest.json").as_posix(): "variant_manifest",
    }
    for relative, role in fixed.items():
        artifacts[relative] = _artifact(repo_root, relative, role)
    for path in sorted((repo_root / SCHEMAS_ROOT).glob("*.json")):
        relative = path.relative_to(repo_root).as_posix()
        artifacts[relative] = _artifact(repo_root, relative, "schema")
    for arm_id in ("F", "A1", "A2", "A3"):
        relative = variant_manifest["arms"][arm_id]["instruction_path"]
        artifacts[relative] = _artifact(repo_root, relative, "variant_instructions")
    return dict(sorted(artifacts.items()))


def _execution_constraints() -> dict[str, object]:
    return {
        "exact_model_id": None,
        "model_binding_status": "UNBOUND_UNTIL_SEPARATE_AUTHORIZATION",
        "same_model_across_arms": True,
        "tool_profile_id": "M4-READONLY-RESEARCH-V1",
        "allowed_tool_capabilities": [
            "scholarly_discovery_readonly",
            "citation_metadata_verification_readonly",
            "web_search_readonly",
        ],
        "forbidden_actions": [
            "write_user_files",
            "start_services",
            "download_models",
            "upload_research_materials",
            "execute_experiment_or_simulation",
            "train_or_deploy_models",
            "control_physical_systems",
        ],
        "search_query_budget": 12,
        "input_context_token_ceiling": 32000,
        "output_token_ceiling": 8000,
        "wall_clock_minutes": 20,
        "same_user_input_across_arms": True,
        "same_scoring_contract_across_arms": True,
        "one_independent_context_per_task": True,
        "one_independent_finalization_per_task": True,
        "cross_task_result_visibility": False,
        "same_task_retry_count": 0,
    }


def build_preparation(repo_root: Path, *, write: bool = True) -> dict[str, object]:
    case_paths = sorted((repo_root / CASES_ROOT).glob("*.json"))
    cases = [_load_object(path) for path in case_paths]
    cases.sort(key=lambda value: value["case_id"])
    if len(cases) != 12:
        raise ValueError("exactly twelve M4 cases are required")
    variant_manifest = _load_object(repo_root / VARIANTS_ROOT / "variant-manifest.json")
    if list(variant_manifest["arms"]) != list(ARM_IDS):
        raise ValueError("variant arm order or set is invalid")

    artifacts = _collect_artifacts(repo_root, variant_manifest)
    protocol_path = (M4_ROOT / "task-protocol.md").as_posix()
    rubric_path = (M4_ROOT / "judge-rubric.json").as_posix()
    protocol_hash = artifacts[protocol_path]["sha256"]
    rubric_hash = artifacts[rubric_path]["sha256"]
    execution_constraints = _execution_constraints()
    execution_constraints_hash = _canonical_sha256(execution_constraints)

    preliminary: list[dict[str, object]] = []
    for case in cases:
        case_path = next(path for path in case_paths if _load_object(path)["case_id"] == case["case_id"])
        relative_case_path = case_path.relative_to(repo_root).as_posix()
        case_bytes = case_path.read_bytes()
        user_input_hash = _sha256(case["user_input"].encode("utf-8"))
        for arm_id in ARM_IDS:
            arm = variant_manifest["arms"][arm_id]
            task_id = f"{case['case_id']}-{arm_id}"
            preliminary.append(
                {
                    "task_id": task_id,
                    "case_id": case["case_id"],
                    "domain": case["domain"],
                    "case_type": case["case_type"],
                    "arm_id": arm_id,
                    "batch_id": DOMAIN_BATCH_IDS[case["domain"]],
                    "case_path": relative_case_path,
                    "case_sha256": _sha256(case_bytes),
                    "user_input_sha256": user_input_hash,
                    "task_protocol_sha256": protocol_hash,
                    "variant_instruction_path": arm["instruction_path"],
                    "variant_instruction_sha256": arm["instruction_sha256"],
                    "rubric_sha256": rubric_hash,
                    "execution_constraints_sha256": execution_constraints_hash,
                    "result_root": f"evals/m4/results/m4.0/{task_id}",
                    "result_root_must_be_absent": True,
                }
            )

    ordered = sorted(
        preliminary,
        key=lambda task: _sha256(f"m4.0-order-v1:{task['task_id']}".encode("utf-8")),
    )
    blind_mapping: dict[str, str] = {}
    tasks: list[dict[str, object]] = []
    for index, task in enumerate(ordered, start=1):
        blind_id = f"M4-J{index:03d}"
        blind_mapping[task["task_id"]] = blind_id
        tasks.append({**task, "blind_id": blind_id})

    batches = []
    for domain in DOMAIN_ORDER:
        domain_tasks = [task["task_id"] for task in tasks if task["domain"] == domain]
        case_ids = sorted({task["case_id"] for task in tasks if task["domain"] == domain})
        batches.append(
            {
                "batch_id": DOMAIN_BATCH_IDS[domain],
                "domain": domain,
                "case_ids": case_ids,
                "task_ids": domain_tasks,
                "planned_task_count": len(domain_tasks),
                "stop_on_infrastructure_or_protocol_failure": True,
                "later_batches_mutable_after_observation": False,
            }
        )

    manifest: dict[str, object] = {
        "schema_version": "m4-preparation-manifest-v1",
        "milestone": "M4",
        "revision": "M4.0",
        "status": "PREPARATION_ONLY",
        "baseline": {
            "main_integration_commit": BASELINE_COMMIT,
            "main_integration_ci": {
                "status": "PASSED",
                "run_id": 31235319084,
            },
            "closure_delivery_head": CLOSURE_DELIVERY_HEAD,
            "closure_delivery_ci": {
                "status": "PASSED",
                "run_id": 31233977467,
            },
            "m3_tag": M3_TAG,
            "m3_tag_object_oid": _git(repo_root, "rev-parse", M3_TAG),
            "m3_tag_target_commit": _git(repo_root, "rev-parse", f"{M3_TAG}^{{}}"),
            "m3_evidence_tree_git_oid": _git(
                repo_root, "rev-parse", f"{BASELINE_COMMIT}:evals/m3"
            ),
            "skill_tree_git_oid": _git(
                repo_root,
                "rev-parse",
                f"{BASELINE_COMMIT}:skills/engineering-research-copilot",
            ),
        },
        "authority": {
            "fresh_execution_authorized": False,
            "fresh_tasks_authorized": False,
            "result_writes_authorized": False,
            "retry_authorized": False,
            "repair_authorized": False,
            "authorization_artifact": None,
            "model_binding_status": "UNBOUND_UNTIL_SEPARATE_AUTHORIZATION",
        },
        "matrix": {
            "domains": list(DOMAIN_ORDER),
            "case_count": len(cases),
            "ordinary_case_count": sum(case["case_type"] == "ordinary" for case in cases),
            "adversarial_case_count": sum(
                case["case_type"] == "adversarial" for case in cases
            ),
            "arms": list(ARM_IDS),
            "arm_count": len(ARM_IDS),
            "planned_task_count": len(tasks),
            "tasks_per_domain_batch": 10,
            "batches": batches,
        },
        "execution_constraints": execution_constraints,
        "randomization": {
            "frozen": True,
            "algorithm": "sha256_lexicographic_v1",
            "seed": "m4.0-order-v1",
            "task_order": [task["task_id"] for task in tasks],
            "blind_mapping": blind_mapping,
            "judge_mapping_access_authorized": False,
        },
        "artifacts": artifacts,
        "tasks": tasks,
        "counters": {name: 0 for name in COUNTER_NAMES},
    }
    if write:
        target = repo_root / MANIFEST_PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(_json_bytes(manifest))
    return manifest


def check_preparation(repo_root: Path) -> dict[str, object]:
    expected = build_preparation(repo_root, write=False)
    path = repo_root / MANIFEST_PATH
    mismatches: list[str] = []
    if not path.is_file():
        mismatches.append("preparation_manifest_missing")
    elif path.read_bytes() != _json_bytes(expected):
        mismatches.append("preparation_manifest_bytes_mismatch")
    return {
        "status": "valid" if not mismatches else "invalid",
        "mismatches": mismatches,
        "case_count": expected["matrix"]["case_count"],
        "arm_count": expected["matrix"]["arm_count"],
        "planned_task_count": expected["matrix"]["planned_task_count"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    if args.check:
        result = check_preparation(repo_root)
    else:
        manifest = build_preparation(repo_root, write=True)
        result = {
            "status": "generated",
            "case_count": manifest["matrix"]["case_count"],
            "arm_count": manifest["matrix"]["arm_count"],
            "planned_task_count": manifest["matrix"]["planned_task_count"],
        }
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return 0 if result["status"] in {"generated", "valid"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
