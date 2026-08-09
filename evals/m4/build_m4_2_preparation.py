from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Any


M4_ROOT = Path("evals/m4")
SOURCE_MANIFEST_PATH = M4_ROOT / "revisions/m4.1/preparation-manifest.json"
MANIFEST_PATH = M4_ROOT / "revisions/m4.2/preparation-manifest.json"
HELPER_PATH = M4_ROOT / "execution/prepare_m4_2_request_bundles.ps1"
CLAIM_PATH = M4_ROOT / "execution/m4.1/launch-claim.json"
TERMINAL_PATH = M4_ROOT / "execution/m4.1/execution-terminal.json"

TERMINAL_CLOSURE_HEAD = "e6ae2be7695ce1d2613dcd39e379ff458c1b60fe"
TERMINAL_CLOSURE_CI_RUN_ID = 31301984766
TERMINAL_EVIDENCE_HEAD = "80b54697c3e27a5dad0a24d5318ce26c8fe46141"
SOURCE_PREPARATION_HEAD = "fedc5cdeebd7a2943afeb6767d39841305c55444"
SOURCE_PREPARATION_CI_RUN_ID = 31248424046

CLAIM_SHA256 = "c16a2e53aa2e9215e2325464d547356afdb73897bfc7d29605e0105b9987b3c6"
CLAIM_BYTE_LENGTH = 24078
CLAIM_BLOB = "794058739b96598955216b3960b95b0feea1208f"
TERMINAL_SHA256 = "7305d71ba94cd209f5bb0cb2c977db3bb157d95b907f8f59df9133c192f4d66e"
TERMINAL_BYTE_LENGTH = 3707
TERMINAL_BLOB = "76c7dc1ef88d587741d364536c86e389c296ad5c"
FAILURE_EVIDENCE_SHA256 = (
    "61a18842ac13637f9ba71a5dac6547d1fcbd4355127f97ea213e0ea44941f9c5"
)
SOURCE_PREPARATION_SHA256 = (
    "d66ad9d513d8e64307f9a1553242d9b7d840ea5432d084b06d86707c1b4c2b61"
)
SOURCE_PREPARATION_BYTE_LENGTH = 85962
SOURCE_PREPARATION_BLOB = "42a10d36e4d64ab98aa724114b904001107f557d"

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
EXPECTED_AUTHORITY = {
    "fresh_execution_authorized": False,
    "fresh_tasks_authorized": False,
    "result_writes_authorized": False,
    "retry_authorized": False,
    "repair_authorized": False,
    "authorization_artifact": None,
    "model_binding_status": "UNBOUND_UNTIL_SEPARATE_AUTHORIZATION",
}
EXPECTED_LIFECYCLE = {
    "claim_aware_post_claim_confirmation_required": True,
    "post_claim_claim_absence_checks_authorized": False,
    "canonical_claim_path_integration_test_required": True,
    "same_revision_continuation_authorized": False,
}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _load_object(raw: bytes, label: str) -> dict[str, Any]:
    value = json.loads(raw.decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{label}_not_object")
    return value


def _git(repo_root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=repo_root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    if completed.returncode != 0:
        raise RuntimeError(
            completed.stderr.strip() or f"git {' '.join(arguments)} failed"
        )
    return completed.stdout.strip()


def _require_raw(path: Path, expected_length: int, expected_sha256: str, label: str) -> bytes:
    raw = path.read_bytes()
    if len(raw) != expected_length:
        raise ValueError(f"{label}_byte_length_mismatch")
    if _sha256(raw) != expected_sha256:
        raise ValueError(f"{label}_sha256_mismatch")
    return raw


def _require_blob(
    repo_root: Path, head: str, relative_path: Path, expected_blob: str, label: str
) -> None:
    actual = _git(repo_root, "rev-parse", f"{head}:{relative_path.as_posix()}")
    if actual != expected_blob:
        raise ValueError(f"{label}_git_blob_mismatch")


def successor_task_id(source_task_id: str) -> str:
    if not source_task_id.startswith("M4.1-") or source_task_id.startswith(
        "M4.1-BATCH-"
    ):
        raise ValueError("source_task_id_invalid")
    return "M4.2-" + source_task_id.removeprefix("M4.1-")


def successor_batch_id(source_batch_id: str) -> str:
    if not source_batch_id.startswith("M4.1-BATCH-"):
        raise ValueError("source_batch_id_invalid")
    return "M4.2-BATCH-" + source_batch_id.removeprefix("M4.1-BATCH-")


def request_binding_sha256(task: Mapping[str, object]) -> str:
    fields = (
        "m4.2-request-binding-v1",
        str(task["task_id"]),
        str(task["source_task_id"]),
        str(task["root_task_id"]),
        str(task["blind_id"]),
        str(task["case_sha256"]),
        str(task["user_input_sha256"]),
        str(task["task_protocol_sha256"]),
        str(task["variant_instruction_sha256"] or "NONE"),
        str(task["rubric_sha256"]),
        str(task["execution_constraints_sha256"]),
    )
    return _sha256(("\n".join(fields) + "\n").encode("utf-8"))


def _validate_terminal(terminal: dict[str, Any]) -> None:
    if terminal.get("terminal_state") != "STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE":
        raise ValueError("m4_1_terminal_state_invalid")
    if terminal.get("failed_stage") != "post_claim_dual_confirmation":
        raise ValueError("m4_1_failed_stage_invalid")
    if terminal.get("successor_revision_required") is not True:
        raise ValueError("m4_1_successor_revision_not_required")
    counts = terminal.get("counts")
    if not isinstance(counts, dict) or any(value != 0 for value in counts.values()):
        raise ValueError("m4_1_terminal_counts_nonzero")
    failure = terminal.get("failure_evidence")
    if not isinstance(failure, dict):
        raise ValueError("m4_1_failure_evidence_invalid")
    if failure.get("raw_evidence_sha256") != FAILURE_EVIDENCE_SHA256:
        raise ValueError("m4_1_failure_evidence_sha256_mismatch")
    raw_evidence = failure.get("raw_evidence")
    if not isinstance(raw_evidence, str) or not raw_evidence.startswith("base64:"):
        raise ValueError("m4_1_failure_evidence_encoding_invalid")
    if _sha256(raw_evidence.encode("utf-8")) != FAILURE_EVIDENCE_SHA256:
        raise ValueError("m4_1_failure_evidence_raw_sha256_mismatch")
    try:
        decoded = base64.b64decode(raw_evidence[7:].encode("ascii"), validate=True)
    except (UnicodeEncodeError, binascii.Error) as exc:
        raise ValueError("m4_1_failure_evidence_decode_failed") from exc
    payload = _load_object(decoded, "m4_1_failure_evidence")
    authorization_errors = payload.get("authorization_errors")
    if not isinstance(authorization_errors, list) or (
        "authorization_already_claimed" not in authorization_errors
    ):
        raise ValueError("m4_1_observed_protocol_error_missing")


def build_preparation(
    repo_root: Path | None = None, *, write: bool = True
) -> dict[str, object]:
    repo_root = repo_root or Path(__file__).resolve().parents[2]
    source_raw = _require_raw(
        repo_root / SOURCE_MANIFEST_PATH,
        SOURCE_PREPARATION_BYTE_LENGTH,
        SOURCE_PREPARATION_SHA256,
        "source_preparation",
    )
    claim_raw = _require_raw(
        repo_root / CLAIM_PATH, CLAIM_BYTE_LENGTH, CLAIM_SHA256, "m4_1_launch_claim"
    )
    terminal_raw = _require_raw(
        repo_root / TERMINAL_PATH,
        TERMINAL_BYTE_LENGTH,
        TERMINAL_SHA256,
        "m4_1_execution_terminal",
    )
    _require_blob(
        repo_root,
        SOURCE_PREPARATION_HEAD,
        SOURCE_MANIFEST_PATH,
        SOURCE_PREPARATION_BLOB,
        "source_preparation",
    )
    for head in (TERMINAL_EVIDENCE_HEAD, TERMINAL_CLOSURE_HEAD):
        _require_blob(repo_root, head, CLAIM_PATH, CLAIM_BLOB, "m4_1_launch_claim")
        _require_blob(
            repo_root, head, TERMINAL_PATH, TERMINAL_BLOB, "m4_1_execution_terminal"
        )

    source = _load_object(source_raw, "source_preparation")
    _load_object(claim_raw, "m4_1_launch_claim")
    terminal = _load_object(terminal_raw, "m4_1_execution_terminal")
    _validate_terminal(terminal)
    helper_bytes = (repo_root / HELPER_PATH).read_bytes()

    source_tasks = source.get("tasks")
    if not isinstance(source_tasks, list) or len(source_tasks) != 60:
        raise ValueError("source_task_count_invalid")
    tasks: list[dict[str, object]] = []
    task_id_map: dict[str, str] = {}
    root_task_id_map: dict[str, str] = {}
    for index, source_task in enumerate(source_tasks, start=121):
        if not isinstance(source_task, dict):
            raise ValueError("source_task_invalid")
        source_task_id = str(source_task["task_id"])
        root_task_id = str(source_task["source_task_id"])
        source_batch_id = str(source_task["batch_id"])
        root_batch_id = str(source_task["source_batch_id"])
        task_id = successor_task_id(source_task_id)
        task: dict[str, object] = {
            "task_id": task_id,
            "source_task_id": source_task_id,
            "root_task_id": root_task_id,
            "blind_id": f"M4-J{index:03d}",
            "source_blind_id": source_task["blind_id"],
            "root_blind_id": source_task["source_blind_id"],
        }
        task.update({key: source_task[key] for key in INHERITED_TASK_KEYS})
        task.update(
            {
                "batch_id": successor_batch_id(source_batch_id),
                "source_batch_id": source_batch_id,
                "root_batch_id": root_batch_id,
                "result_root": f"evals/m4/results/m4.2/{task_id}",
                "result_root_must_be_absent": True,
            }
        )
        task["request_binding_sha256"] = request_binding_sha256(task)
        tasks.append(task)
        task_id_map[source_task_id] = task_id
        root_task_id_map[source_task_id] = root_task_id
    if len(task_id_map) != 60:
        raise ValueError("source_task_id_duplicate")

    source_batches = source.get("matrix", {}).get("batches")
    if not isinstance(source_batches, list) or len(source_batches) != 6:
        raise ValueError("source_batch_count_invalid")
    batches: list[dict[str, object]] = []
    for source_batch in source_batches:
        if not isinstance(source_batch, dict):
            raise ValueError("source_batch_invalid")
        source_batch_id = str(source_batch["batch_id"])
        source_task_ids = [str(value) for value in source_batch["task_ids"]]
        root_task_ids = [str(value) for value in source_batch["source_task_ids"]]
        if [root_task_id_map[value] for value in source_task_ids] != root_task_ids:
            raise ValueError("source_batch_root_lineage_invalid")
        batches.append(
            {
                "batch_id": successor_batch_id(source_batch_id),
                "source_batch_id": source_batch_id,
                "root_batch_id": source_batch["source_batch_id"],
                "domain": source_batch["domain"],
                "task_ids": [task_id_map[value] for value in source_task_ids],
                "source_task_ids": source_task_ids,
                "root_task_ids": root_task_ids,
                "planned_task_count": 10,
                "stop_on_infrastructure_or_protocol_failure": True,
                "later_batches_mutable_after_observation": False,
            }
        )

    source_ids = [str(task["task_id"]) for task in source_tasks]
    source_order = source.get("randomization", {}).get("task_order")
    if not isinstance(source_order, list) or len(source_order) != 60:
        raise ValueError("source_task_order_invalid")
    task_order = [task_id_map[str(value)] for value in source_order]
    blind_mapping = {str(task["task_id"]): str(task["blind_id"]) for task in tasks}
    manifest: dict[str, object] = {
        "schema_version": "m4.2-successor-preparation-v1",
        "milestone": "M4",
        "revision": "M4.2",
        "status": "PREPARATION_ONLY",
        "predecessor": {
            "terminal_closure_head": TERMINAL_CLOSURE_HEAD,
            "terminal_closure_ci_run_id": TERMINAL_CLOSURE_CI_RUN_ID,
            "terminal_closure_ci_conclusion": "success",
            "terminal_evidence_head": TERMINAL_EVIDENCE_HEAD,
            "launch_claim": {
                "path": CLAIM_PATH.as_posix(),
                "byte_length": CLAIM_BYTE_LENGTH,
                "sha256": CLAIM_SHA256,
                "git_blob_oid": CLAIM_BLOB,
            },
            "execution_terminal": {
                "path": TERMINAL_PATH.as_posix(),
                "byte_length": TERMINAL_BYTE_LENGTH,
                "sha256": TERMINAL_SHA256,
                "git_blob_oid": TERMINAL_BLOB,
            },
            "failure_evidence": {
                "raw_evidence_sha256": FAILURE_EVIDENCE_SHA256,
                "observed_protocol_error": "authorization_already_claimed",
            },
            "authorization_token_status": "CONSUMED",
            "claim_count": 1,
            "terminal_state": terminal["terminal_state"],
            "failed_stage": terminal["failed_stage"],
            "successor_revision_required": terminal["successor_revision_required"],
            "counts": terminal["counts"],
            "later_gates": terminal["later_gates"],
        },
        "source_preparation": {
            "path": SOURCE_MANIFEST_PATH.as_posix(),
            "head": SOURCE_PREPARATION_HEAD,
            "ci_run_id": SOURCE_PREPARATION_CI_RUN_ID,
            "ci_conclusion": "success",
            "byte_length": SOURCE_PREPARATION_BYTE_LENGTH,
            "raw_sha256": SOURCE_PREPARATION_SHA256,
            "git_blob_oid": SOURCE_PREPARATION_BLOB,
            "task_count": 60,
            "source_order_sha256": _sha256(
                ("\n".join(source_ids) + "\n").encode("utf-8")
            ),
        },
        "authority": dict(EXPECTED_AUTHORITY),
        "lifecycle_requirements": dict(EXPECTED_LIFECYCLE),
        "matrix": {
            "case_count": 12,
            "arm_count": 5,
            "planned_task_count": 60,
            "batch_count": 6,
            "batches": batches,
        },
        "randomization": {
            "frozen": True,
            "policy": "INHERITED_M4_1_RELATIVE_ORDER_WITH_DISJOINT_IDENTITIES",
            "source_seed": source["randomization"]["source_seed"],
            "task_order": task_order,
            "blind_mapping": blind_mapping,
            "judge_mapping_access_authorized": False,
        },
        "execution_helper": {
            "path": HELPER_PATH.as_posix(),
            "raw_sha256": _sha256(helper_bytes),
            "read_only": True,
            "minimum_windows_powershell_version": "5.1",
            "request_binding_count": 60,
        },
        "tasks": tasks,
        "counters": {name: 0 for name in COUNTER_NAMES},
    }
    if write:
        target = repo_root / MANIFEST_PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(_json_bytes(manifest))
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the frozen M4.2 preparation")
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    manifest = build_preparation(repo_root, write=False)
    expected = _json_bytes(manifest)
    target = repo_root / MANIFEST_PATH
    if arguments.check:
        if not target.exists() or target.read_bytes() != expected:
            raise SystemExit("m4_2_preparation_manifest_mismatch")
        status = "verified"
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(expected)
        status = "prepared"
    print(
        json.dumps(
            {
                "status": status,
                "revision": "M4.2",
                "planned_task_count": len(manifest["tasks"]),
                "batch_count": len(manifest["matrix"]["batches"]),
                "request_binding_count": manifest["execution_helper"][
                    "request_binding_count"
                ],
                "fresh_execution_authorized": False,
                "side_effects": [],
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
