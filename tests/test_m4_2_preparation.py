from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from evals.m4.build_m4_2_preparation import (
    CLAIM_SHA256,
    FAILURE_EVIDENCE_SHA256,
    SOURCE_PREPARATION_SHA256,
    TERMINAL_CLOSURE_CI_RUN_ID,
    TERMINAL_CLOSURE_HEAD,
    TERMINAL_EVIDENCE_HEAD,
    TERMINAL_SHA256,
    build_preparation,
    request_binding_sha256,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
M4_ROOT = REPO_ROOT / "evals" / "m4"
BASE_PATH = M4_ROOT / "preparation-manifest.json"
SOURCE_PATH = M4_ROOT / "revisions" / "m4.1" / "preparation-manifest.json"
REVISION_ROOT = M4_ROOT / "revisions" / "m4.2"
MANIFEST_PATH = REVISION_ROOT / "preparation-manifest.json"
SCHEMA_PATH = REVISION_ROOT / "preparation-manifest.schema.json"
CLAIM_PATH = M4_ROOT / "execution" / "m4.1" / "launch-claim.json"
TERMINAL_PATH = M4_ROOT / "execution" / "m4.1" / "execution-terminal.json"
HELPER_PATH = M4_ROOT / "execution" / "prepare_m4_2_request_bundles.ps1"

MANIFEST_KEYS = {
    "schema_version",
    "milestone",
    "revision",
    "status",
    "predecessor",
    "source_preparation",
    "authority",
    "lifecycle_requirements",
    "matrix",
    "randomization",
    "execution_helper",
    "tasks",
    "counters",
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
TERMINAL_COUNTER_NAMES = {
    "tasks",
    "threads",
    "attempts",
    "finalizations",
    "results",
    "retries",
    "repairs",
    "followups",
    "judge_calls",
    "aggregation_calls",
    "side_effects",
}
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


def load_object(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"expected JSON object: {path}")
    return value


class M42PreparationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.base = load_object(BASE_PATH)
        cls.source = load_object(SOURCE_PATH)
        cls.manifest = load_object(MANIFEST_PATH)
        cls.claim = load_object(CLAIM_PATH)
        cls.terminal = load_object(TERMINAL_PATH)

    def test_exact_successor_identity_and_lineage_projection(self) -> None:
        manifest = self.manifest
        self.assertEqual(set(manifest), MANIFEST_KEYS)
        self.assertEqual(manifest["schema_version"], "m4.2-successor-preparation-v1")
        self.assertEqual(manifest["milestone"], "M4")
        self.assertEqual(manifest["revision"], "M4.2")
        self.assertEqual(manifest["status"], "PREPARATION_ONLY")

        tasks = manifest["tasks"]
        source_tasks = self.source["tasks"]
        root_task_ids = [task["task_id"] for task in self.base["tasks"]]
        source_task_ids = [task["task_id"] for task in source_tasks]
        task_ids = [task["task_id"] for task in tasks]
        self.assertEqual(len(tasks), 60)
        self.assertEqual(
            [task["source_task_id"] for task in tasks], source_task_ids
        )
        self.assertEqual(
            [task["root_task_id"] for task in tasks],
            [task["source_task_id"] for task in source_tasks],
        )
        self.assertEqual(
            task_ids,
            [
                "M4.2-" + task_id.removeprefix("M4.1-")
                for task_id in source_task_ids
            ],
        )
        self.assertEqual(len(task_ids), len(set(task_ids)))
        self.assertTrue(set(task_ids).isdisjoint(source_task_ids))
        self.assertTrue(set(task_ids).isdisjoint(root_task_ids))
        self.assertEqual(
            [task["blind_id"] for task in tasks],
            [f"M4-J{index:03d}" for index in range(121, 181)],
        )
        self.assertEqual(
            [task["source_blind_id"] for task in tasks],
            [task["blind_id"] for task in source_tasks],
        )
        self.assertEqual(
            [task["root_blind_id"] for task in tasks],
            [task["source_blind_id"] for task in source_tasks],
        )
        all_blind_ids = [task["blind_id"] for task in self.base["tasks"]]
        all_blind_ids += [task["blind_id"] for task in source_tasks]
        self.assertTrue(
            {task["blind_id"] for task in tasks}.isdisjoint(all_blind_ids)
        )

        batches = manifest["matrix"]["batches"]
        source_batches = self.source["matrix"]["batches"]
        self.assertEqual(len(batches), 6)
        self.assertEqual(
            [batch["source_batch_id"] for batch in batches],
            [batch["batch_id"] for batch in source_batches],
        )
        self.assertEqual(
            [batch["root_batch_id"] for batch in batches],
            [batch["source_batch_id"] for batch in source_batches],
        )
        self.assertEqual(
            [batch["batch_id"] for batch in batches],
            [
                "M4.2-BATCH-" + batch["batch_id"].removeprefix("M4.1-BATCH-")
                for batch in source_batches
            ],
        )

    def test_predecessor_terminal_evidence_and_authority_are_closed(self) -> None:
        predecessor = self.manifest["predecessor"]
        self.assertEqual(predecessor["terminal_closure_head"], TERMINAL_CLOSURE_HEAD)
        self.assertEqual(
            predecessor["terminal_closure_ci_run_id"], TERMINAL_CLOSURE_CI_RUN_ID
        )
        self.assertEqual(predecessor["terminal_closure_ci_conclusion"], "success")
        self.assertEqual(predecessor["terminal_evidence_head"], TERMINAL_EVIDENCE_HEAD)
        self.assertEqual(predecessor["launch_claim"]["sha256"], CLAIM_SHA256)
        self.assertEqual(predecessor["launch_claim"]["byte_length"], 24078)
        self.assertEqual(
            predecessor["execution_terminal"]["sha256"], TERMINAL_SHA256
        )
        self.assertEqual(predecessor["execution_terminal"]["byte_length"], 3707)
        self.assertEqual(
            predecessor["failure_evidence"]["raw_evidence_sha256"],
            FAILURE_EVIDENCE_SHA256,
        )
        self.assertEqual(
            predecessor["failure_evidence"]["observed_protocol_error"],
            "authorization_already_claimed",
        )
        self.assertEqual(predecessor["authorization_token_status"], "CONSUMED")
        self.assertEqual(predecessor["claim_count"], 1)
        self.assertEqual(
            predecessor["terminal_state"],
            "STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE",
        )
        self.assertEqual(predecessor["failed_stage"], "post_claim_dual_confirmation")
        self.assertTrue(predecessor["successor_revision_required"])
        self.assertEqual(set(predecessor["counts"]), TERMINAL_COUNTER_NAMES)
        self.assertEqual(set(predecessor["counts"].values()), {0})
        self.assertEqual(predecessor["counts"], self.terminal["counts"])
        self.assertEqual(predecessor["later_gates"], self.terminal["later_gates"])

        source = self.manifest["source_preparation"]
        self.assertEqual(source["raw_sha256"], SOURCE_PREPARATION_SHA256)
        self.assertEqual(source["byte_length"], 85962)
        self.assertEqual(source["task_count"], 60)
        self.assertEqual(self.manifest["authority"], EXPECTED_AUTHORITY)
        self.assertEqual(
            self.manifest["lifecycle_requirements"], EXPECTED_LIFECYCLE
        )
        self.assertEqual(set(self.manifest["counters"]), COUNTER_NAMES)
        self.assertEqual(set(self.manifest["counters"].values()), {0})

    def test_inherited_inputs_order_request_bindings_and_future_paths(self) -> None:
        inherited_keys = (
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
        tasks = self.manifest["tasks"]
        for task, source in zip(tasks, self.source["tasks"], strict=True):
            self.assertEqual(
                {key: task[key] for key in inherited_keys},
                {key: source[key] for key in inherited_keys},
            )
            self.assertEqual(task["request_binding_sha256"], request_binding_sha256(task))
            self.assertEqual(
                task["result_root"], f"evals/m4/results/m4.2/{task['task_id']}"
            )
            self.assertTrue(task["result_root_must_be_absent"])
            self.assertFalse((REPO_ROOT / task["result_root"]).exists())

        source_order = self.source["randomization"]["task_order"]
        source_to_successor = {
            task["source_task_id"]: task["task_id"] for task in tasks
        }
        self.assertEqual(
            self.manifest["randomization"]["task_order"],
            [source_to_successor[task_id] for task_id in source_order],
        )
        request_hashes = [task["request_binding_sha256"] for task in tasks]
        self.assertEqual(len(request_hashes), len(set(request_hashes)))
        self.assertFalse((M4_ROOT / "authorization" / "m4.2").exists())
        self.assertFalse((M4_ROOT / "execution" / "m4.2").exists())
        self.assertFalse((M4_ROOT / "results" / "m4.1").exists())
        self.assertFalse((M4_ROOT / "results" / "m4.2").exists())
        self.assertFalse((M4_ROOT / "results-manifest.json").exists())

    def test_request_binding_frame_is_exact(self) -> None:
        first = self.manifest["tasks"][0]
        framed = "\n".join(
            (
                "m4.2-request-binding-v1",
                first["task_id"],
                first["source_task_id"],
                first["root_task_id"],
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

    def test_helper_source_is_read_only_and_powershell_5_1_compatible(self) -> None:
        source = HELPER_PATH.read_text(encoding="utf-8")
        self.assertIn("[System.Security.Cryptography.SHA256]::Create()", source)
        self.assertIn("[System.BitConverter]::ToString", source)
        self.assertIn(".Replace('-', '').ToLowerInvariant()", source)
        self.assertNotIn("[Convert]::ToHexString", source)
        self.assertNotIn("SHA256]::HashData", source)
        for forbidden in (
            "Set-Content",
            "Out-File",
            "New-Item",
            "Remove-Item",
            "Invoke-WebRequest",
            "Start-Process",
        ):
            self.assertNotIn(forbidden, source)

    def test_helper_executes_read_only_on_windows_powershell(self) -> None:
        executable = Path("C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe")
        if not executable.exists():
            self.skipTest("Windows PowerShell 5.1 is unavailable")

        before = {
            "claim": CLAIM_PATH.read_bytes(),
            "terminal": TERMINAL_PATH.read_bytes(),
            "source": SOURCE_PATH.read_bytes(),
            "manifest": MANIFEST_PATH.read_bytes(),
        }

        def run(*arguments: str) -> dict:
            completed = subprocess.run(
                [
                    str(executable),
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
                encoding="utf-8",
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            lines = [line for line in completed.stdout.splitlines() if line.strip()]
            self.assertEqual(len(lines), 1, completed.stdout)
            return json.loads(lines[0])

        self.assertEqual(run("-SelfTest")["status"], "SELF_TEST_PASSED")
        self.assertEqual(run("-CheckAll")["checked_task_count"], 60)
        self.assertEqual(
            run("-TaskId", self.manifest["tasks"][0]["task_id"])[
                "checked_task_count"
            ],
            1,
        )
        self.assertEqual(
            {
                "claim": CLAIM_PATH.read_bytes(),
                "terminal": TERMINAL_PATH.read_bytes(),
                "source": SOURCE_PATH.read_bytes(),
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
        self.assertEqual(
            schema["properties"]["schema_version"]["const"],
            "m4.2-successor-preparation-v1",
        )
        for definition in (
            "evidence_binding",
            "terminal_counts",
            "later_gates",
            "batch",
            "task",
            "counters",
        ):
            self.assertFalse(schema["$defs"][definition]["additionalProperties"])
        self.assertEqual(build_preparation(REPO_ROOT, write=False), self.manifest)


class M42PreparationAuditTests(unittest.TestCase):
    @staticmethod
    def _audit(**kwargs) -> dict[str, object]:
        from evals.m4.audit_m4_2_preparation import audit_preparation

        return audit_preparation(REPO_ROOT, **kwargs)

    def _audit_mutation(self, mutate) -> dict[str, object]:
        value = load_object(MANIFEST_PATH)
        mutate(value)
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            changed = Path(temp_dir) / "preparation-manifest.json"
            changed.write_text(
                json.dumps(value, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            return self._audit(manifest_path=changed, verify_git=False)

    def test_repository_audit_is_read_only_repeatable_and_not_authorized(self) -> None:
        before_status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=REPO_ROOT,
            check=True,
            stdout=subprocess.PIPE,
        ).stdout
        before = {
            "claim": CLAIM_PATH.read_bytes(),
            "terminal": TERMINAL_PATH.read_bytes(),
            "source": SOURCE_PATH.read_bytes(),
            "manifest": MANIFEST_PATH.read_bytes(),
        }
        first = self._audit()
        second = self._audit()
        self.assertEqual(first, second)
        self.assertEqual(first["status"], "M4_2_PREPARED_NOT_AUTHORIZED")
        self.assertEqual(first["errors"], [])
        self.assertEqual(first["planned_task_count"], 60)
        self.assertEqual(first["reused_task_id_count"], 0)
        self.assertEqual(first["batch_count"], 6)
        self.assertEqual(first["request_binding_count"], 60)
        self.assertFalse(first["fresh_execution_authorized"])
        self.assertEqual(first["forbidden_path_count"], 0)
        self.assertEqual(
            first["m4_1_terminal_status"],
            "M4_1_STOPPED_PROTOCOL_FAILURE_PRESERVED",
        )
        self.assertEqual(first["side_effects"], [])
        self.assertEqual(
            {
                "claim": CLAIM_PATH.read_bytes(),
                "terminal": TERMINAL_PATH.read_bytes(),
                "source": SOURCE_PATH.read_bytes(),
                "manifest": MANIFEST_PATH.read_bytes(),
            },
            before,
        )
        after_status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=REPO_ROOT,
            check=True,
            stdout=subprocess.PIPE,
        ).stdout
        self.assertEqual(after_status, before_status)

    def test_rejects_predecessor_evidence_and_lifecycle_drift(self) -> None:
        mutations = (
            (
                lambda value: value["predecessor"]["launch_claim"].__setitem__(
                    "sha256", "0" * 64
                ),
                "predecessor_claim_binding_invalid",
            ),
            (
                lambda value: value["predecessor"]["execution_terminal"].__setitem__(
                    "sha256", "0" * 64
                ),
                "predecessor_terminal_binding_invalid",
            ),
            (
                lambda value: value["lifecycle_requirements"].__setitem__(
                    "post_claim_claim_absence_checks_authorized", True
                ),
                "lifecycle_requirements_invalid",
            ),
        )
        for mutate, error in mutations:
            with self.subTest(error=error):
                result = self._audit_mutation(mutate)
                self.assertEqual(result["status"], "INVALID")
                self.assertIn(error, result["errors"])

    def test_rejects_identity_lineage_order_and_request_drift(self) -> None:
        mutations = (
            (
                lambda value: value["tasks"][0].__setitem__(
                    "task_id", value["tasks"][0]["source_task_id"]
                ),
                "task_id_reused",
            ),
            (
                lambda value: value["tasks"][0].__setitem__(
                    "source_task_id", value["tasks"][1]["source_task_id"]
                ),
                "source_task_lineage_invalid",
            ),
            (
                lambda value: value["tasks"][0].__setitem__(
                    "root_task_id", value["tasks"][1]["root_task_id"]
                ),
                "root_task_lineage_invalid",
            ),
            (
                lambda value: value["tasks"][0].__setitem__(
                    "blind_id", value["tasks"][0]["source_blind_id"]
                ),
                "blind_id_reused",
            ),
            (lambda value: value["tasks"].reverse(), "task_order_changed"),
            (
                lambda value: value["tasks"][0].__setitem__(
                    "request_binding_sha256", "0" * 64
                ),
                "request_binding_mismatch",
            ),
        )
        for mutate, error in mutations:
            with self.subTest(error=error):
                result = self._audit_mutation(mutate)
                self.assertEqual(result["status"], "INVALID")
                self.assertIn(error, result["errors"])

    def test_rejects_authority_counter_and_authorization_artifact(self) -> None:
        mutations = (
            (
                lambda value: value["authority"].__setitem__(
                    "fresh_execution_authorized", True
                ),
                "preparation_authority_invalid",
            ),
            (
                lambda value: value["authority"].__setitem__(
                    "authorization_artifact", "evals/m4/authorization/m4.2/x.json"
                ),
                "preparation_authority_invalid",
            ),
            (
                lambda value: value["counters"].__setitem__(
                    "created_contexts", 1
                ),
                "execution_counter_nonzero",
            ),
        )
        for mutate, error in mutations:
            with self.subTest(error=error):
                result = self._audit_mutation(mutate)
                self.assertEqual(result["status"], "INVALID")
                self.assertIn(error, result["errors"])

    def test_rejects_every_forbidden_future_path(self) -> None:
        keys = (
            "m4_1_results",
            "m4_2_authorization",
            "m4_2_execution",
            "m4_2_results",
            "results_manifest",
        )
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            for key in keys:
                with self.subTest(key=key):
                    path = root / key
                    if key == "results_manifest":
                        path.write_text("{}\n", encoding="utf-8", newline="\n")
                    else:
                        path.mkdir()
                    result = self._audit(
                        forbidden_path_overrides={key: path}, verify_git=False
                    )
                    self.assertEqual(result["status"], "INVALID")
                    self.assertIn(f"{key}_present", result["errors"])
                    if path.is_file():
                        path.unlink()
                    else:
                        path.rmdir()


if __name__ == "__main__":
    unittest.main()
