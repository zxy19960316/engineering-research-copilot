from __future__ import annotations

import json
import unittest
from pathlib import Path

from evals.m4.audit_m4_1_preparation import audit_preparation
from evals.m4.build_m4_1_preparation import (
    CLAIM_SHA256,
    FAILURE_SHA256,
    TERMINAL_CI_RUN_ID,
    TERMINAL_HEAD,
    build_preparation,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
M4_ROOT = REPO_ROOT / "evals" / "m4"
BASE_PATH = M4_ROOT / "preparation-manifest.json"
REVISION_ROOT = M4_ROOT / "revisions" / "m4.1"
MANIFEST_PATH = REVISION_ROOT / "preparation-manifest.json"
SCHEMA_PATH = REVISION_ROOT / "preparation-manifest.schema.json"
CLAIM_PATH = M4_ROOT / "execution" / "m4.0" / "launch-claim.json"
FAILURE_PATH = M4_ROOT / "execution" / "m4.0" / "pre-dispatch-failure.json"
M4_1_CLAIM_PATH = M4_ROOT / "execution" / "m4.1" / "launch-claim.json"

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
MANIFEST_KEYS = {
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


def load_object(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"expected JSON object: {path}")
    return value


class M41PreparationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.base = load_object(BASE_PATH)
        cls.manifest = load_object(MANIFEST_PATH)

    def test_exact_successor_identity_projection(self) -> None:
        manifest = self.manifest
        self.assertEqual(set(manifest), MANIFEST_KEYS)
        self.assertEqual(manifest["schema_version"], "m4.1-successor-preparation-v1")
        self.assertEqual(manifest["milestone"], "M4")
        self.assertEqual(manifest["revision"], "M4.1")
        self.assertEqual(manifest["status"], "PREPARATION_ONLY")

        tasks = manifest["tasks"]
        old_task_ids = [task["task_id"] for task in self.base["tasks"]]
        new_task_ids = [task["task_id"] for task in tasks]
        self.assertEqual(len(tasks), 60)
        self.assertEqual(
            [task["source_task_id"] for task in tasks], old_task_ids
        )
        self.assertEqual(len(new_task_ids), len(set(new_task_ids)))
        self.assertTrue(set(new_task_ids).isdisjoint(old_task_ids))
        self.assertEqual(
            [task["blind_id"] for task in tasks],
            [f"M4-J{index:03d}" for index in range(61, 121)],
        )
        self.assertTrue(
            {task["blind_id"] for task in tasks}.isdisjoint(
                task["blind_id"] for task in self.base["tasks"]
            )
        )

        batches = manifest["matrix"]["batches"]
        self.assertEqual(len(batches), 6)
        self.assertEqual(
            [batch["source_batch_id"] for batch in batches],
            [batch["batch_id"] for batch in self.base["matrix"]["batches"]],
        )
        self.assertTrue(
            {batch["batch_id"] for batch in batches}.isdisjoint(
                batch["batch_id"] for batch in self.base["matrix"]["batches"]
            )
        )

    def test_predecessor_evidence_and_authority_are_closed(self) -> None:
        predecessor = self.manifest["predecessor"]
        self.assertEqual(predecessor["terminal_head"], TERMINAL_HEAD)
        self.assertEqual(predecessor["terminal_ci_run_id"], TERMINAL_CI_RUN_ID)
        self.assertEqual(predecessor["terminal_ci_conclusion"], "success")
        self.assertEqual(predecessor["launch_claim"]["sha256"], CLAIM_SHA256)
        self.assertEqual(
            predecessor["pre_dispatch_failure"]["sha256"], FAILURE_SHA256
        )
        self.assertEqual(predecessor["m4_0_authorization_token_status"], "CONSUMED")
        self.assertEqual(predecessor["m4_0_task_ids_consumed"], 60)
        self.assertEqual(predecessor["m4_0_observed_contexts"], 0)

        self.assertEqual(
            self.manifest["authority"],
            {
                "fresh_execution_authorized": False,
                "fresh_tasks_authorized": False,
                "result_writes_authorized": False,
                "retry_authorized": False,
                "repair_authorized": False,
                "authorization_artifact": None,
                "model_binding_status": "UNBOUND_UNTIL_SEPARATE_AUTHORIZATION",
            },
        )
        self.assertEqual(set(self.manifest["counters"]), COUNTER_NAMES)
        self.assertEqual(set(self.manifest["counters"].values()), {0})

    def test_request_bindings_and_future_paths_are_frozen_empty(self) -> None:
        tasks = self.manifest["tasks"]
        request_hashes = [task["request_binding_sha256"] for task in tasks]
        result_roots = [task["result_root"] for task in tasks]
        self.assertEqual(len(request_hashes), len(set(request_hashes)))
        self.assertTrue(all(len(value) == 64 for value in request_hashes))
        self.assertEqual(len(result_roots), len(set(result_roots)))
        self.assertTrue(
            all(root.startswith("evals/m4/results/m4.1/") for root in result_roots)
        )
        self.assertTrue(
            all(not (REPO_ROOT / root).exists() for root in result_roots)
        )
        self.assertFalse(M4_1_CLAIM_PATH.exists())
        self.assertFalse((M4_ROOT / "results-manifest.json").exists())

    def test_schema_is_closed_and_manifest_regenerates_exactly(self) -> None:
        schema = load_object(SCHEMA_PATH)
        self.assertEqual(schema["type"], "object")
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(set(schema["required"]), MANIFEST_KEYS)
        self.assertEqual(set(schema["properties"]), MANIFEST_KEYS)
        self.assertEqual(build_preparation(REPO_ROOT, write=False), self.manifest)

    def test_repository_audit_is_read_only_and_not_authorized(self) -> None:
        before = {
            "claim": CLAIM_PATH.read_bytes(),
            "failure": FAILURE_PATH.read_bytes(),
            "manifest": MANIFEST_PATH.read_bytes(),
        }
        result = audit_preparation(REPO_ROOT)
        self.assertEqual(result["status"], "PREPARED_NOT_AUTHORIZED")
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["planned_task_count"], 60)
        self.assertEqual(result["reused_task_id_count"], 0)
        self.assertEqual(result["existing_result_root_count"], 0)
        self.assertFalse(result["launch_claim_present"])
        self.assertFalse(result["fresh_execution_authorized"])
        self.assertEqual(result["side_effects"], [])
        self.assertEqual(
            {
                "claim": CLAIM_PATH.read_bytes(),
                "failure": FAILURE_PATH.read_bytes(),
                "manifest": MANIFEST_PATH.read_bytes(),
            },
            before,
        )


if __name__ == "__main__":
    unittest.main()
