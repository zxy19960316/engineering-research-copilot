from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Any


M4_ROOT = Path("evals/m4")
BASE_MANIFEST_PATH = M4_ROOT / "preparation-manifest.json"
MANIFEST_PATH = M4_ROOT / "revisions/m4.1/preparation-manifest.json"
HELPER_PATH = M4_ROOT / "execution/prepare_m4_1_request_bundles.ps1"
CLAIM_PATH = M4_ROOT / "execution/m4.0/launch-claim.json"
FAILURE_PATH = M4_ROOT / "execution/m4.0/pre-dispatch-failure.json"

TERMINAL_HEAD = "f48ab8d7e835e9a57e65b75458faa786d696316d"
TERMINAL_CI_RUN_ID = 31246286753
BASE_PREPARATION_HEAD = "c56c3c1ab384f65e51a70e9582672c6320d19121"
BASE_PREPARATION_SHA256 = (
    "1838412c690c2000544999e955e399b4429289a698aa9467129f43fb0cd1bb76"
)
BASE_PREPARATION_BLOB = "196d19be1483b58f2f6f8bb67d76d9a3f8020d98"
CLAIM_SHA256 = "5690177383c44a30e808533ebdfe0b504c6da2abf8e61a1d0303d4c439c3ecec"
CLAIM_BLOB = "cfbcba7a28162ba489f3ed34effcf30ebebc499c"
FAILURE_SHA256 = "8ef9487ce617aeafefc6d665a981581ffc046b541cf426f22d434be689f007ff"
FAILURE_BLOB = "1a6bc8268adbfab7850daefac5f897c5e03f32aa"

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
INHERITED_TASK_KEYS = (
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


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


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


def _require_bytes_sha256(path: Path, expected: str, error: str) -> bytes:
    data = path.read_bytes()
    if _sha256(data) != expected:
        raise ValueError(error)
    return data


def successor_task_id(source_task_id: str) -> str:
    if not source_task_id.startswith("M4-") or source_task_id.startswith("M4-BATCH-"):
        raise ValueError("source_task_id_invalid")
    return "M4.1-" + source_task_id.removeprefix("M4-")


def successor_batch_id(source_batch_id: str) -> str:
    if not source_batch_id.startswith("M4-BATCH-"):
        raise ValueError("source_batch_id_invalid")
    return "M4.1-BATCH-" + source_batch_id.removeprefix("M4-BATCH-")


def request_binding_sha256(task: Mapping[str, object]) -> str:
    fields = (
        "m4.1-request-binding-v1",
        str(task["task_id"]),
        str(task["source_task_id"]),
        str(task["blind_id"]),
        str(task["case_sha256"]),
        str(task["user_input_sha256"]),
        str(task["task_protocol_sha256"]),
        str(task["variant_instruction_sha256"] or "NONE"),
        str(task["rubric_sha256"]),
        str(task["execution_constraints_sha256"]),
    )
    return _sha256(("\n".join(fields) + "\n").encode("utf-8"))


def build_preparation(repo_root: Path, *, write: bool = True) -> dict[str, object]:
    base_path = repo_root / BASE_MANIFEST_PATH
    base_bytes = _require_bytes_sha256(
        base_path, BASE_PREPARATION_SHA256, "base_preparation_raw_sha256_mismatch"
    )
    if (
        _git(repo_root, "rev-parse", f"{BASE_PREPARATION_HEAD}:{BASE_MANIFEST_PATH.as_posix()}")
        != BASE_PREPARATION_BLOB
    ):
        raise ValueError("base_preparation_git_blob_mismatch")

    _require_bytes_sha256(
        repo_root / CLAIM_PATH, CLAIM_SHA256, "m4_0_launch_claim_sha256_mismatch"
    )
    _require_bytes_sha256(
        repo_root / FAILURE_PATH,
        FAILURE_SHA256,
        "m4_0_pre_dispatch_failure_sha256_mismatch",
    )
    if (
        _git(repo_root, "rev-parse", f"{TERMINAL_HEAD}:{CLAIM_PATH.as_posix()}")
        != CLAIM_BLOB
    ):
        raise ValueError("m4_0_launch_claim_git_blob_mismatch")
    if (
        _git(repo_root, "rev-parse", f"{TERMINAL_HEAD}:{FAILURE_PATH.as_posix()}")
        != FAILURE_BLOB
    ):
        raise ValueError("m4_0_pre_dispatch_failure_git_blob_mismatch")

    helper_bytes = (repo_root / HELPER_PATH).read_bytes()
    base = json.loads(base_bytes.decode("utf-8"))
    if not isinstance(base, dict):
        raise ValueError("base_preparation_not_object")
    source_tasks = base.get("tasks")
    if not isinstance(source_tasks, list) or len(source_tasks) != 60:
        raise ValueError("base_task_count_invalid")

    tasks: list[dict[str, object]] = []
    task_id_map: dict[str, str] = {}
    for index, source in enumerate(source_tasks, start=61):
        if not isinstance(source, dict):
            raise ValueError("base_task_invalid")
        source_task_id = str(source["task_id"])
        task_id = successor_task_id(source_task_id)
        source_batch_id = str(source["batch_id"])
        task: dict[str, object] = {
            "task_id": task_id,
            "source_task_id": source_task_id,
            "blind_id": f"M4-J{index:03d}",
            "source_blind_id": source["blind_id"],
        }
        task.update({key: source[key] for key in INHERITED_TASK_KEYS})
        task.update(
            {
                "batch_id": successor_batch_id(source_batch_id),
                "source_batch_id": source_batch_id,
                "result_root": f"evals/m4/results/m4.1/{task_id}",
                "result_root_must_be_absent": True,
            }
        )
        task["request_binding_sha256"] = request_binding_sha256(task)
        tasks.append(task)
        task_id_map[source_task_id] = task_id

    source_ids = [str(task["task_id"]) for task in source_tasks]
    if len(task_id_map) != 60:
        raise ValueError("base_task_id_duplicate")

    source_batches = base.get("matrix", {}).get("batches")
    if not isinstance(source_batches, list) or len(source_batches) != 6:
        raise ValueError("base_batch_count_invalid")
    batches: list[dict[str, object]] = []
    for source_batch in source_batches:
        if not isinstance(source_batch, dict):
            raise ValueError("base_batch_invalid")
        source_batch_id = str(source_batch["batch_id"])
        source_batch_task_ids = [str(value) for value in source_batch["task_ids"]]
        batches.append(
            {
                "batch_id": successor_batch_id(source_batch_id),
                "source_batch_id": source_batch_id,
                "domain": source_batch["domain"],
                "task_ids": [task_id_map[value] for value in source_batch_task_ids],
                "source_task_ids": source_batch_task_ids,
                "planned_task_count": 10,
                "stop_on_infrastructure_or_protocol_failure": True,
                "later_batches_mutable_after_observation": False,
            }
        )

    task_order = [task_id_map[value] for value in base["randomization"]["task_order"]]
    blind_mapping = {str(task["task_id"]): str(task["blind_id"]) for task in tasks}
    manifest: dict[str, object] = {
        "schema_version": "m4.1-successor-preparation-v1",
        "milestone": "M4",
        "revision": "M4.1",
        "status": "PREPARATION_ONLY",
        "predecessor": {
            "terminal_head": TERMINAL_HEAD,
            "terminal_ci_run_id": TERMINAL_CI_RUN_ID,
            "terminal_ci_conclusion": "success",
            "launch_claim": {
                "path": CLAIM_PATH.as_posix(),
                "sha256": CLAIM_SHA256,
                "git_blob_oid": CLAIM_BLOB,
            },
            "pre_dispatch_failure": {
                "path": FAILURE_PATH.as_posix(),
                "sha256": FAILURE_SHA256,
                "git_blob_oid": FAILURE_BLOB,
            },
            "m4_0_authorization_token_status": "CONSUMED",
            "m4_0_task_ids_consumed": 60,
            "m4_0_observed_contexts": 0,
        },
        "base_preparation": {
            "path": BASE_MANIFEST_PATH.as_posix(),
            "head": BASE_PREPARATION_HEAD,
            "raw_sha256": BASE_PREPARATION_SHA256,
            "git_blob_oid": BASE_PREPARATION_BLOB,
            "task_count": 60,
            "source_order_sha256": _sha256(
                ("\n".join(source_ids) + "\n").encode("utf-8")
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
            "case_count": 12,
            "arm_count": 5,
            "planned_task_count": 60,
            "batch_count": 6,
            "batches": batches,
        },
        "randomization": {
            "frozen": True,
            "policy": "INHERITED_M4_0_RELATIVE_ORDER_WITH_DISJOINT_IDENTITIES",
            "source_seed": base["randomization"]["seed"],
            "task_order": task_order,
            "blind_mapping": blind_mapping,
            "judge_mapping_access_authorized": False,
        },
        "execution_helper": {
            "path": HELPER_PATH.as_posix(),
            "raw_sha256": _sha256(helper_bytes),
            "minimum_windows_powershell_version": "5.1",
            "hash_algorithm": "SHA-256",
            "hex_encoding": "BitConverter.ToString.Replace.ToLowerInvariant",
            "prohibited_apis": ["Convert.ToHexString", "SHA256.HashData"],
            "modes": ["SelfTest", "CheckAll", "TaskId"],
            "request_binding_count": 60,
        },
        "tasks": tasks,
        "counters": {name: 0 for name in COUNTER_NAMES},
    }

    if write:
        output_path = repo_root / MANIFEST_PATH
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(_json_bytes(manifest))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the frozen M4.1 preparation")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    manifest = build_preparation(repo_root, write=not args.check)
    expected = _json_bytes(manifest)
    output_path = repo_root / MANIFEST_PATH
    mismatches: list[str] = []
    if args.check:
        if not output_path.is_file():
            mismatches.append("preparation_manifest_missing")
        elif output_path.read_bytes() != expected:
            mismatches.append("preparation_manifest_regeneration_mismatch")
    result = {
        "status": "prepared" if not mismatches else "invalid",
        "revision": "M4.1",
        "planned_task_count": len(manifest["tasks"]),
        "batch_count": len(manifest["matrix"]["batches"]),
        "request_binding_count": len(manifest["tasks"]),
        "mismatches": mismatches,
        "fresh_execution_authorized": False,
        "side_effects": [],
    }
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return 0 if not mismatches else 1


if __name__ == "__main__":
    raise SystemExit(main())
