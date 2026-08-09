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
NESTED_REQUIRED = {
    "predecessor": {
        "terminal_closure_head",
        "terminal_closure_ci_run_id",
        "terminal_closure_ci_conclusion",
        "terminal_evidence_head",
        "launch_claim",
        "execution_terminal",
        "failure_evidence",
        "authorization_token_status",
        "claim_count",
        "terminal_state",
        "failed_stage",
        "successor_revision_required",
        "counts",
        "later_gates",
    },
    "source_preparation": {
        "path",
        "head",
        "ci_run_id",
        "ci_conclusion",
        "byte_length",
        "raw_sha256",
        "git_blob_oid",
        "task_count",
        "source_order_sha256",
    },
    "authority": set(EXPECTED_AUTHORITY),
    "lifecycle_requirements": set(EXPECTED_LIFECYCLE),
    "matrix": {"case_count", "arm_count", "planned_task_count", "batch_count", "batches"},
    "randomization": {
        "frozen",
        "policy",
        "source_seed",
        "task_order",
        "blind_mapping",
        "judge_mapping_access_authorized",
    },
    "execution_helper": {
        "path",
        "raw_sha256",
        "read_only",
        "minimum_windows_powershell_version",
        "request_binding_count",
    },
}
DEFINITION_REQUIRED = {
    "evidence_binding": {"path", "byte_length", "sha256", "git_blob_oid"},
    "terminal_counts": TERMINAL_COUNTER_NAMES,
    "later_gates": {
        "judge",
        "m4_closure",
        "m5",
        "threshold_decision",
        "unblinding_and_aggregation",
    },
    "batch": {
        "batch_id",
        "source_batch_id",
        "root_batch_id",
        "domain",
        "task_ids",
        "source_task_ids",
        "root_task_ids",
        "planned_task_count",
        "stop_on_infrastructure_or_protocol_failure",
        "later_batches_mutable_after_observation",
    },
    "task": {
        "task_id",
        "source_task_id",
        "root_task_id",
        "blind_id",
        "source_blind_id",
        "root_blind_id",
        "case_id",
        "domain",
        "case_type",
        "arm_id",
        "batch_id",
        "source_batch_id",
        "root_batch_id",
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
    },
    "counters": COUNTER_NAMES,
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
            "Add-Content",
            "Clear-Content",
            "Out-File",
            "Export-Csv",
            "Export-Clixml",
            "New-Item",
            "Remove-Item",
            "Move-Item",
            "Copy-Item",
            "Rename-Item",
            "Set-Item",
            "Invoke-WebRequest",
            "Invoke-RestMethod",
            "Start-BitsTransfer",
            "Start-Process",
            "Invoke-Expression",
            "System.Net",
            "WebClient",
            "HttpClient",
            "WriteAll",
            "OpenWrite",
            "FileStream",
            "Directory]::Create",
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
        before_status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=REPO_ROOT,
            check=True,
            stdout=subprocess.PIPE,
        ).stdout
        forbidden_paths = (
            M4_ROOT / "authorization" / "m4.2",
            M4_ROOT / "execution" / "m4.2",
            M4_ROOT / "results" / "m4.1",
            M4_ROOT / "results" / "m4.2",
            M4_ROOT / "results-manifest.json",
        )
        self.assertTrue(all(not path.exists() for path in forbidden_paths))

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
            value = json.loads(lines[0])
            self.assertEqual(value["side_effects"], [])
            return value

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
        self.assertTrue(all(not path.exists() for path in forbidden_paths))
        after_status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=REPO_ROOT,
            check=True,
            stdout=subprocess.PIPE,
        ).stdout
        self.assertEqual(after_status, before_status)

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
        for name, required in NESTED_REQUIRED.items():
            with self.subTest(object=name):
                contract = schema["properties"][name]
                self.assertFalse(contract["additionalProperties"])
                self.assertEqual(set(contract["required"]), required)
                self.assertEqual(set(contract["properties"]), required)
        predecessor = schema["properties"]["predecessor"]["properties"]
        failure = predecessor["failure_evidence"]
        self.assertFalse(failure["additionalProperties"])
        self.assertEqual(
            set(failure["required"]),
            {"raw_evidence_sha256", "observed_protocol_error"},
        )
        self.assertEqual(set(failure["properties"]), set(failure["required"]))
        for definition, required in DEFINITION_REQUIRED.items():
            with self.subTest(definition=definition):
                contract = schema["$defs"][definition]
                self.assertFalse(contract["additionalProperties"])
                self.assertEqual(set(contract["required"]), required)
                self.assertEqual(set(contract["properties"]), required)
        anchored_patterns = (
            schema["properties"]["randomization"]["properties"]["task_order"]
            ["items"]["pattern"],
            schema["properties"]["randomization"]["properties"]["blind_mapping"]
            ["propertyNames"]["pattern"],
            schema["$defs"]["batch"]["properties"]["batch_id"]["pattern"],
            schema["$defs"]["task"]["properties"]["task_id"]["pattern"],
            schema["$defs"]["task"]["properties"]["result_root"]["pattern"],
        )
        self.assertTrue(all(pattern.endswith("$") for pattern in anchored_patterns))
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
                lambda value: value["predecessor"].__setitem__(
                    "unexpected", "forbidden"
                ),
                "predecessor_shape_invalid",
            ),
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
                lambda value: value["predecessor"]["failure_evidence"].__setitem__(
                    "raw_evidence_sha256", "0" * 64
                ),
                "predecessor_failure_evidence_invalid",
            ),
            (
                lambda value: value["source_preparation"].__setitem__(
                    "raw_sha256", "0" * 64
                ),
                "source_preparation_binding_invalid",
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
            (
                lambda value: value["matrix"]["batches"][0].__setitem__(
                    "batch_id",
                    value["matrix"]["batches"][0]["source_batch_id"],
                ),
                "batch_id_reused",
            ),
            (
                lambda value: value["matrix"]["batches"][0].__setitem__(
                    "source_batch_id",
                    value["matrix"]["batches"][1]["source_batch_id"],
                ),
                "source_batch_lineage_invalid",
            ),
            (
                lambda value: value["matrix"]["batches"][0].__setitem__(
                    "root_batch_id",
                    value["matrix"]["batches"][1]["root_batch_id"],
                ),
                "root_batch_lineage_invalid",
            ),
        )
        for mutate, error in mutations:
            with self.subTest(error=error):
                result = self._audit_mutation(mutate)
                self.assertEqual(result["status"], "INVALID")
                self.assertIn(error, result["errors"])

    def test_rejects_authority_counter_and_authorization_artifact(self) -> None:
        mutations = []
        for key in (
            "fresh_execution_authorized",
            "fresh_tasks_authorized",
            "result_writes_authorized",
            "retry_authorized",
            "repair_authorized",
        ):
            mutations.append(
                (
                    lambda value, key=key: value["authority"].__setitem__(key, True),
                    "preparation_authority_invalid",
                )
            )
        mutations.extend(
            (
                (
                    lambda value: value["authority"].__setitem__(
                        "authorization_artifact",
                        "evals/m4/authorization/m4.2/execution-authorization.json",
                    ),
                    "preparation_authority_invalid",
                ),
                (
                    lambda value: value["authority"].__setitem__(
                        "model_binding_status", "BOUND"
                    ),
                    "preparation_authority_invalid",
                ),
            )
        )
        for key in sorted(COUNTER_NAMES):
            mutations.append(
                (
                    lambda value, key=key: value["counters"].__setitem__(key, 1),
                    "execution_counter_nonzero",
                )
            )
        for mutate, error in mutations:
            with self.subTest(error=error):
                result = self._audit_mutation(mutate)
                self.assertEqual(result["status"], "INVALID")
                self.assertIn(error, result["errors"])

    def test_rejects_bool_int_type_confusion(self) -> None:
        mutations = (
            (
                lambda value: value["authority"].__setitem__("retry_authorized", 0),
                "preparation_authority_invalid",
            ),
            (
                lambda value: value["lifecycle_requirements"].__setitem__(
                    "claim_aware_post_claim_confirmation_required", 1
                ),
                "lifecycle_requirements_invalid",
            ),
            (
                lambda value: value["counters"].__setitem__(
                    "authorized_tasks", False
                ),
                "execution_counter_type_invalid",
            ),
            (
                lambda value: value["predecessor"].__setitem__("claim_count", True),
                "predecessor_invalid",
            ),
            (
                lambda value: value["predecessor"]["counts"].__setitem__(
                    "tasks", False
                ),
                "predecessor_counts_invalid",
            ),
            (
                lambda value: value["predecessor"]["later_gates"].__setitem__(
                    "judge", 0
                ),
                "predecessor_later_gates_invalid",
            ),
            (
                lambda value: value["randomization"].__setitem__("frozen", 1),
                "randomization_invalid",
            ),
            (
                lambda value: value["execution_helper"].__setitem__(
                    "read_only", 1
                ),
                "execution_helper_binding_invalid",
            ),
        )
        for mutate, error in mutations:
            with self.subTest(error=error):
                result = self._audit_mutation(mutate)
                self.assertEqual(result["status"], "INVALID")
                self.assertIn(error, result["errors"])

    def test_git_freeze_detects_hidden_index_and_unexpected_repo_drift(self) -> None:
        import os
        import stat

        from evals.m4.audit_m4_2_preparation import (
            _changed_paths,
            _unexpected_repo_changes,
            _worktree_changed_paths,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)

            def git(*arguments: str) -> subprocess.CompletedProcess[bytes]:
                return subprocess.run(
                    ["git", "-c", "core.autocrlf=false", *arguments],
                    cwd=repo,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )

            git("init", "--quiet")
            frozen_relative = Path("evals/m4/frozen.txt")
            frozen = repo / frozen_relative
            f04_relative = Path("evals/f04-upstream/frozen.txt")
            f04 = repo / f04_relative
            frozen.parent.mkdir(parents=True, exist_ok=True)
            f04.parent.mkdir(parents=True, exist_ok=True)
            (repo / ".gitattributes").write_text(
                "/evals/f04-upstream/** text eol=lf\n"
                "/evals/m4/** text eol=lf\n",
                encoding="utf-8",
                newline="\n",
            )
            frozen.write_text("baseline\n", encoding="utf-8", newline="\n")
            f04.write_text("baseline\n", encoding="utf-8", newline="\n")
            git(
                "add",
                "--",
                ".gitattributes",
                frozen_relative.as_posix(),
                f04_relative.as_posix(),
            )
            git(
                "-c",
                "user.name=M4.2 Audit Test",
                "-c",
                "user.email=m4.2-audit@example.invalid",
                "commit",
                "--quiet",
                "-m",
                "baseline",
            )
            baseline = git("rev-parse", "HEAD").stdout.decode("ascii").strip()

            frozen.write_text("staged drift\n", encoding="utf-8", newline="\n")
            git("add", "--", frozen_relative.as_posix())
            frozen.write_text("baseline\n", encoding="utf-8", newline="\n")
            errors: list[str] = []
            changed = _changed_paths(
                repo, baseline, (frozen_relative.as_posix(),), "frozen", errors
            )
            self.assertEqual(changed, [frozen_relative.as_posix()])
            self.assertIn("frozen_changed", errors)

            (repo / "pyproject.toml").write_text(
                "[project]\n", encoding="utf-8", newline="\n"
            )
            errors = []
            unexpected = _unexpected_repo_changes(repo, baseline, errors)
            self.assertIn("pyproject.toml", unexpected)
            self.assertIn("unexpected_repository_change", errors)

            (repo / "pyproject.toml").unlink()
            git("read-tree", baseline)
            f04.write_bytes(b"baseline\r\n")
            errors = []
            raw_unexpected = _unexpected_repo_changes(repo, baseline, errors)
            self.assertIn(f04_relative.as_posix(), raw_unexpected)
            self.assertIn("unexpected_repository_change", errors)
            f04.write_bytes(b"baseline\n")

            (repo / ".git/info/attributes").write_text(
                "/evals/m4/** -text eol=crlf filter=evil\n",
                encoding="utf-8",
                newline="\n",
            )
            frozen.write_bytes(b"baseline\r\n")
            errors = []
            self.assertEqual(
                _changed_paths(
                    repo,
                    baseline,
                    (frozen_relative.as_posix(),),
                    "frozen",
                    errors,
                ),
                [],
            )
            raw_changed = _worktree_changed_paths(
                repo,
                baseline,
                (frozen_relative.as_posix(),),
                "frozen_raw",
                errors,
            )
            self.assertEqual(raw_changed, [frozen_relative.as_posix()])
            self.assertIn("frozen_raw_changed", errors)

            original_oid = git(
                "rev-parse", f"{baseline}:{frozen_relative.as_posix()}"
            ).stdout.decode("ascii").strip()
            replacement_bytes = b"replacement baseline\n"
            replacement_oid = subprocess.run(
                ["git", "hash-object", "-w", "--stdin"],
                cwd=repo,
                check=True,
                input=replacement_bytes,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            ).stdout.decode("ascii").strip()
            git("replace", original_oid, replacement_oid)
            frozen.write_bytes(replacement_bytes)
            errors = []
            replacement_changed = _worktree_changed_paths(
                repo,
                baseline,
                (frozen_relative.as_posix(),),
                "replacement",
                errors,
            )
            self.assertEqual(replacement_changed, [frozen_relative.as_posix()])
            self.assertIn("replacement_changed", errors)

            if os.name != "nt":
                git("replace", "-d", original_oid)
                frozen.write_bytes(b"baseline\n")
                os.chmod(frozen, frozen.stat().st_mode | stat.S_IXUSR)
                errors = []
                mode_changed = _worktree_changed_paths(
                    repo,
                    baseline,
                    (frozen_relative.as_posix(),),
                    "mode",
                    errors,
                )
                self.assertEqual(mode_changed, [frozen_relative.as_posix()])
                self.assertIn("mode_changed", errors)

    def test_rejects_raw_bound_input_eol_drift(self) -> None:
        from evals.m4.audit_m4_2_preparation import _validate_bound_input_bytes

        with tempfile.TemporaryDirectory() as temp_dir:
            repo = Path(temp_dir)
            case_relative = Path("evals/m4/cases/probe.json")
            protocol_relative = Path("evals/m4/task-protocol.md")
            variant_relative = Path("evals/m4/variants/A1/instructions.md")
            rubric_relative = Path("evals/m4/judge-rubric.json")
            for relative in (
                case_relative,
                protocol_relative,
                variant_relative,
                rubric_relative,
            ):
                (repo / relative).parent.mkdir(parents=True, exist_ok=True)

            lf_case = b'{\n  "user_input": "probe"\n}\n'
            lf_protocol = b"protocol\n"
            lf_variant = b"variant\n"
            lf_rubric = b'{"rubric":true}\n'
            (repo / case_relative).write_bytes(lf_case.replace(b"\n", b"\r\n"))
            (repo / protocol_relative).write_bytes(
                lf_protocol.replace(b"\n", b"\r\n")
            )
            (repo / variant_relative).write_bytes(lf_variant.replace(b"\n", b"\r\n"))
            (repo / rubric_relative).write_bytes(lf_rubric.replace(b"\n", b"\r\n"))
            task = {
                "case_path": case_relative.as_posix(),
                "case_sha256": hashlib.sha256(lf_case).hexdigest(),
                "user_input_sha256": hashlib.sha256(b"probe").hexdigest(),
                "task_protocol_sha256": hashlib.sha256(lf_protocol).hexdigest(),
                "variant_instruction_path": variant_relative.as_posix(),
                "variant_instruction_sha256": hashlib.sha256(lf_variant).hexdigest(),
                "rubric_sha256": hashlib.sha256(lf_rubric).hexdigest(),
            }
            errors: list[str] = []
            _validate_bound_input_bytes(repo, [task], errors)
            self.assertIn("case_raw_sha256_mismatch", errors)
            self.assertIn("task_protocol_raw_sha256_mismatch", errors)
            self.assertIn("variant_instruction_raw_sha256_mismatch", errors)
            self.assertIn("rubric_raw_sha256_mismatch", errors)
            self.assertNotIn("user_input_sha256_mismatch", errors)

    def test_module_loading_is_bytecode_free_and_dangling_paths_are_present(self) -> None:
        import sys

        from evals.m4.audit_m4_2_preparation import _load_module, _path_present

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            dependency_name = "m4_2_read_only_dependency"
            (root / f"{dependency_name}.py").write_text(
                "VALUE = 7\n", encoding="utf-8", newline="\n"
            )
            module_path = root / "probe.py"
            module_path.write_text(
                f"import {dependency_name}\nVALUE = {dependency_name}.VALUE\n",
                encoding="utf-8",
                newline="\n",
            )
            sys.path.insert(0, str(root))
            try:
                module = _load_module(module_path, "m4_2_read_only_probe")
            finally:
                sys.path.remove(str(root))
                sys.modules.pop(dependency_name, None)
            self.assertEqual(module.VALUE, 7)
            self.assertFalse((root / "__pycache__").exists())

        class DanglingPath:
            @staticmethod
            def exists() -> bool:
                return False

            @staticmethod
            def is_symlink() -> bool:
                return True

        self.assertTrue(_path_present(DanglingPath()))

        class DanglingJunction:
            @staticmethod
            def exists() -> bool:
                return False

            @staticmethod
            def is_symlink() -> bool:
                return False

            @staticmethod
            def is_junction() -> bool:
                return True

        self.assertTrue(_path_present(DanglingJunction()))

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
