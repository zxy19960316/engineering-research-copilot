from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from evals.m4.audit_m4_1_preparation import audit_preparation
from evals.m4.build_m4_1_preparation import (
    CLAIM_SHA256,
    FAILURE_SHA256,
    TERMINAL_CI_RUN_ID,
    TERMINAL_HEAD,
    build_preparation,
    request_binding_sha256,
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
HELPER_PATH = M4_ROOT / "execution" / "prepare_m4_1_request_bundles.ps1"

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
            new_task_ids,
            ["M4.1-" + task_id.removeprefix("M4-") for task_id in old_task_ids],
        )
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
        self.assertEqual(
            [batch["batch_id"] for batch in batches],
            [
                "M4.1-BATCH-" + batch["batch_id"].removeprefix("M4-BATCH-")
                for batch in self.base["matrix"]["batches"]
            ],
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

        first = tasks[0]
        framed = "\n".join(
            (
                "m4.1-request-binding-v1",
                first["task_id"],
                first["source_task_id"],
                first["blind_id"],
                first["case_sha256"],
                first["user_input_sha256"],
                first["task_protocol_sha256"],
                first["variant_instruction_sha256"] or "NONE",
                first["rubric_sha256"],
                first["execution_constraints_sha256"],
            )
        ) + "\n"
        self.assertEqual(
            first["request_binding_sha256"],
            hashlib.sha256(framed.encode("utf-8")).hexdigest(),
        )
        self.assertEqual(
            first["request_binding_sha256"], request_binding_sha256(first)
        )

    def test_powershell_helper_is_hash_bound_and_uses_legacy_compatible_apis(self) -> None:
        source_bytes = HELPER_PATH.read_bytes()
        source = source_bytes.decode("utf-8")
        helper = self.manifest["execution_helper"]
        self.assertEqual(helper["raw_sha256"], hashlib.sha256(source_bytes).hexdigest())
        self.assertIn("[System.Security.Cryptography.SHA256]::Create()", source)
        self.assertIn("[System.BitConverter]::ToString", source)
        self.assertNotIn("[Convert]::ToHexString", source)
        self.assertNotIn("SHA256]::HashData", source)
        for write_api in ("Set-Content", "Out-File", "New-Item", "WriteAllBytes"):
            self.assertNotIn(write_api, source)

    def test_powershell_helper_self_test_all_and_single_task_are_read_only(self) -> None:
        engine = shutil.which("powershell.exe") or shutil.which("pwsh")
        if engine is None:
            self.skipTest("PowerShell is unavailable")

        before = {
            "claim": CLAIM_PATH.read_bytes(),
            "failure": FAILURE_PATH.read_bytes(),
            "manifest": MANIFEST_PATH.read_bytes(),
        }

        def run(*arguments: str) -> dict:
            completed = subprocess.run(
                [
                    engine,
                    "-NoLogo",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(HELPER_PATH),
                    *arguments,
                ],
                cwd=REPO_ROOT,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8-sig",
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            value = json.loads(completed.stdout.strip())
            self.assertIsInstance(value, dict)
            self.assertEqual(value["mismatches"], [])
            self.assertEqual(value["side_effects"], [])
            return value

        self_test = run("-SelfTest")
        self.assertEqual(self_test["status"], "SELF_TEST_PASSED")
        self.assertEqual(self_test["checked_task_count"], 0)

        checked = run("-CheckAll")
        self.assertEqual(checked["status"], "VERIFIED")
        self.assertEqual(checked["checked_task_count"], 60)

        single = run("-TaskId", self.manifest["tasks"][0]["task_id"])
        self.assertEqual(single["status"], "VERIFIED")
        self.assertEqual(single["checked_task_count"], 1)
        self.assertEqual(
            {
                "claim": CLAIM_PATH.read_bytes(),
                "failure": FAILURE_PATH.read_bytes(),
                "manifest": MANIFEST_PATH.read_bytes(),
            },
            before,
        )

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

    def _audit_mutation(self, mutate) -> dict[str, object]:
        value = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        mutate(value)
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            changed = Path(temp_dir) / "preparation-manifest.json"
            changed.write_text(
                json.dumps(value, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            return audit_preparation(
                REPO_ROOT, manifest_path=changed, verify_git=False
            )

    def test_rejects_reused_task_id(self) -> None:
        result = self._audit_mutation(
            lambda value: value["tasks"][0].__setitem__(
                "task_id", value["tasks"][0]["source_task_id"]
            )
        )
        self.assertEqual(result["status"], "INVALID")
        self.assertIn("task_id_reused", result["errors"])

    def test_rejects_task_order_drift(self) -> None:
        result = self._audit_mutation(lambda value: value["tasks"].reverse())
        self.assertEqual(result["status"], "INVALID")
        self.assertIn("task_order_changed", result["errors"])

    def test_rejects_request_binding_drift(self) -> None:
        result = self._audit_mutation(
            lambda value: value["tasks"][0].__setitem__(
                "request_binding_sha256", "0" * 64
            )
        )
        self.assertEqual(result["status"], "INVALID")
        self.assertIn("request_binding_mismatch", result["errors"])

    def test_rejects_nonzero_execution_counter(self) -> None:
        result = self._audit_mutation(
            lambda value: value["counters"].__setitem__("created_contexts", 1)
        )
        self.assertEqual(result["status"], "INVALID")
        self.assertIn("execution_counter_nonzero", result["errors"])

    def test_rejects_even_empty_results_revision_root(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            results_root = Path(temp_dir) / "m4.1"
            results_root.mkdir()
            result = audit_preparation(
                REPO_ROOT, results_base=results_root, verify_git=False
            )
        self.assertEqual(result["status"], "INVALID")
        self.assertIn("result_root_present", result["errors"])
        self.assertEqual(result["existing_result_root_count"], 1)


if __name__ == "__main__":
    unittest.main()
