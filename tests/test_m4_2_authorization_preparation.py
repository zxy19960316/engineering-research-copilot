from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path
from types import ModuleType
from typing import Any, Iterator


REPO_ROOT = Path(__file__).resolve().parents[1]
AUTHORIZATION_ROOT = REPO_ROOT / "evals" / "m4" / "authorization"
M42_ROOT = AUTHORIZATION_ROOT / "m4.2"
AUDITOR_PATH = AUTHORIZATION_ROOT / "audit_m4_2_authorization_preparation.py"
ARTIFACT_PATH = M42_ROOT / "authorization-preparation.json"
PREPARATION_SCHEMA_PATH = M42_ROOT / "authorization-preparation.schema.json"
AUTHORIZATION_SCHEMA_PATH = M42_ROOT / "execution-authorization.schema.json"
CONTROL_SCHEMA_PATH = M42_ROOT / "execution-control.schema.json"
PROOF_PATH = M42_ROOT / "gate-iv-b-protocol-proof.json"
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "m1-validation.yml"
STATUS_PATH = REPO_ROOT / "STATUS.md"

BASELINE_HEAD = "ad67a79f39685937466d3a49d30c6a5117e2810c"
BASELINE_TREE = "7f5d7c2e15616e4e52f45c0366f8b347211e8849"
B3_HEAD = "249e28d07d5e52cd9cec9b7e110f6159e6046222"
B3_TREE = "dacb6e5048a54c3f242add441dd1a36255f80dc4"
PROOF_BLOB = "d3fe975431f2e4584a52ee5305b169f5b5d29268"
PROOF_SHA256 = "9d160de6893fbb6bd01158524a3a48931496b6d4cae1fdc4c9f0e736921068e0"
PROOF_BYTE_LENGTH = 33204
BRANCH = (
    "codex/m4-cross-engineering-forward-evaluation-"
    "m4.2-authorization-preparation"
)
BASE_BRANCH = (
    "codex/m4-cross-engineering-forward-evaluation-"
    "m4.2-gate-iv-b-protocol-proof"
)

FORBIDDEN_EXACT = (
    "evals/m4/authorization/m4.2/authorization-token.json",
    "evals/m4/authorization/m4.2/acceptance-claim.json",
    "evals/m4/results-manifest.json",
)
SUCCESSOR_PAIR = (
    "evals/m4/authorization/m4.2/execution-authorization.json",
    "evals/m4/authorization/m4.2/execution-control.json",
)
FORBIDDEN_PREFIXES = (
    "evals/m4/execution/m4.2",
    "evals/m4/results/m4.1",
    "evals/m4/results/m4.2",
    "evals/m5",
)
ROOT_KEYS = {
    "schema_version",
    "milestone",
    "revision",
    "preparation_kind",
    "baseline",
    "gate_iv_b_evidence",
    "schema_bindings",
    "matrix_projection",
    "request_binding_projection",
    "authorization_projection",
    "control_projection",
    "policy_proofs",
    "negative_authority",
    "delivery",
    "findings",
    "auditor_side_effects",
    "decision",
    "status",
}
ZERO_MARKERS = {"FAIL:": 0, "FAILED (": 0, "Traceback": 0, "##[error]": 0}
PROVISIONAL_DECISION = "PENDING_M4_2_AUTHORIZATION_PREPARATION_EXACT_HEAD_CI"
PROVISIONAL_STATUS = (
    "M4_2_AUTHORIZATION_PREPARATION_LOCAL_PASSED_NOT_AUTHORIZED"
)
FINAL_DECISION = "APPROVE_M4_2_SEPARATE_AUTHORIZATION_WORK_PACKAGE_ONLY"
FINAL_STATUS = "M4_2_AUTHORIZATION_PREPARATION_PASSED_NOT_AUTHORIZED"
IMPLEMENTED = all(
    path.is_file()
    for path in (
        AUDITOR_PATH,
        ARTIFACT_PATH,
        PREPARATION_SCHEMA_PATH,
        AUTHORIZATION_SCHEMA_PATH,
        CONTROL_SCHEMA_PATH,
    )
)


def _git(*arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return completed.stdout.strip()


def _load_auditor() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "m4_2_authorization_preparation_auditor", AUDITOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("authorization_preparation_auditor_unloadable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{path.name}_must_be_object")
    return value


def _object_nodes(value: object) -> Iterator[dict[str, Any]]:
    if isinstance(value, dict):
        if value.get("type") == "object":
            yield value
        for child in value.values():
            yield from _object_nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from _object_nodes(child)


def _present_forbidden(root: Path = REPO_ROOT) -> list[str]:
    found: set[str] = set()
    for relative in FORBIDDEN_EXACT:
        if (root / relative).exists():
            found.add(relative)
    for relative in FORBIDDEN_PREFIXES:
        path = root / relative
        if path.exists():
            if path.is_file() or path.is_symlink():
                found.add(relative)
            else:
                found.update(
                    item.relative_to(root).as_posix()
                    for item in path.rglob("*")
                    if item.is_file() or item.is_symlink()
                )
    return sorted(found)


class M42AuthorizationPreparationRedFirstTests(unittest.TestCase):
    def test_exact_successor_baseline_and_gate_iv_b_blob_are_available(self) -> None:
        self.assertEqual(_git("rev-parse", f"{BASELINE_HEAD}^{{tree}}"), BASELINE_TREE)
        self.assertEqual(_git("rev-parse", f"{B3_HEAD}^{{tree}}"), B3_TREE)
        self.assertEqual(
            _git("rev-parse", f"{BASELINE_HEAD}:{PROOF_PATH.relative_to(REPO_ROOT).as_posix()}"),
            PROOF_BLOB,
        )
        self.assertEqual(
            subprocess.run(
                ["git", "merge-base", "--is-ancestor", BASELINE_HEAD, "HEAD"],
                cwd=REPO_ROOT,
                check=False,
            ).returncode,
            0,
        )

    def test_claim_execution_and_result_paths_are_absent(self) -> None:
        self.assertEqual(_present_forbidden(), [])
        present = [(REPO_ROOT / relative).is_file() for relative in SUCCESSOR_PAIR]
        self.assertIn(present, ([False, False], [True, True]))

    def test_preparation_files_exist(self) -> None:
        missing = [
            path.relative_to(REPO_ROOT).as_posix()
            for path in (
                AUDITOR_PATH,
                ARTIFACT_PATH,
                PREPARATION_SCHEMA_PATH,
                AUTHORIZATION_SCHEMA_PATH,
                CONTROL_SCHEMA_PATH,
            )
            if not path.is_file()
        ]
        self.assertEqual(missing, [])


@unittest.skipUnless(IMPLEMENTED, "AP1 red: authorization preparation absent")
class M42AuthorizationPreparationContractTests(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.auditor = _load_auditor()
        cls.artifact = _load_json(ARTIFACT_PATH)

    def _audit(
        self,
        artifact: dict[str, Any],
        *,
        verify_git: bool = False,
        present_paths: set[str] | None = None,
    ) -> dict[str, Any]:
        return self.auditor.audit_authorization_preparation(
            REPO_ROOT,
            artifact_data=artifact,
            verify_git=verify_git,
            present_paths=present_paths,
        )

    def _assert_blocked(self, artifact: dict[str, Any], error: str) -> None:
        result = self._audit(artifact)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn(error, result["errors"])

    def test_all_three_schemas_are_recursively_closed(self) -> None:
        for path in (
            PREPARATION_SCHEMA_PATH,
            AUTHORIZATION_SCHEMA_PATH,
            CONTROL_SCHEMA_PATH,
        ):
            schema = _load_json(path)
            nodes = list(_object_nodes(schema))
            self.assertGreater(len(nodes), 3, path.name)
            for index, node in enumerate(nodes):
                with self.subTest(schema=path.name, object_index=index):
                    self.assertIs(node.get("additionalProperties"), False)
                    self.assertEqual(
                        set(node.get("required", [])), set(node.get("properties", {}))
                    )

    def test_future_schemas_freeze_atomic_single_use_and_visibility(self) -> None:
        authorization = _load_json(AUTHORIZATION_SCHEMA_PATH)
        control = _load_json(CONTROL_SCHEMA_PATH)
        serialized = json.dumps(
            {"authorization": authorization, "control": control}, sort_keys=True
        )
        for required in (
            '"authorized_task_count": {"const": 60}',
            '"partial_authority_allowed": {"const": false}',
            '"second_claim_allowed": {"const": false}',
            '"claim_consumes_entire_matrix_authorization": {"const": true}',
            '"successor_revision_required_after_failure": {"const": true}',
            '"cross_task_result_visibility": {"const": false}',
        ):
            with self.subTest(required=required):
                self.assertIn(required, serialized)

    def test_artifact_is_preparation_only_without_token_or_authorized_state(self) -> None:
        self.assertEqual(set(self.artifact), ROOT_KEYS)
        self.assertEqual(
            self.artifact["preparation_kind"],
            "AUTHORIZATION_SCHEMA_AND_PROJECTION_ONLY",
        )
        raw = ARTIFACT_PATH.read_bytes()
        self.assertNotIn(b"AUTHORIZED_UNCONSUMED", raw)
        self.assertNotIn(b"sha256:", raw)
        self.assertEqual(self.artifact["findings"], [])
        self.assertEqual(self.artifact["auditor_side_effects"], [])
        delivery = self.artifact["delivery"]
        if delivery["status"] == "PENDING_EXACT_HEAD_CI":
            self.assertEqual(self.artifact["decision"], PROVISIONAL_DECISION)
            self.assertEqual(self.artifact["status"], PROVISIONAL_STATUS)
        else:
            self.assertEqual(delivery["status"], "VERIFIED_TRUE_GREEN")
            self.assertEqual(self.artifact["decision"], FINAL_DECISION)
            self.assertEqual(self.artifact["status"], FINAL_STATUS)

    def test_repository_preparation_audit_passes_and_recomputes_everything(self) -> None:
        result = self._audit(copy.deepcopy(self.artifact), verify_git=True)
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["findings"], [])
        self.assertEqual(result["auditor_side_effects"], [])
        self.assertEqual(result["case_count"], 12)
        self.assertEqual(result["arm_count"], 5)
        self.assertEqual(result["planned_task_count"], 60)
        self.assertEqual(result["batch_count"], 6)
        self.assertEqual(result["request_binding_count"], 60)
        self.assertEqual(result["forbidden_path_count"], 0)
        for counter in self.auditor.COUNTER_NAMES:
            self.assertEqual(result[counter], 0, counter)
        self.assertEqual(result["authorization_token_status"], "NOT_ISSUED")
        self.assertEqual(result["authorization_artifact"], "ABSENT")
        self.assertEqual(result["execution_control"], "ABSENT")
        self.assertEqual(result["launch_claim"], "ABSENT")
        self.assertEqual(result["result_root"], "ABSENT")

    def test_successor_authorization_change_set_is_explicit_and_pair_gated(self) -> None:
        required = {
            "docs/superpowers/plans/2026-08-10-m4.2-one-shot-authorization.md",
            "evals/m4/authorization/build_m4_2_authorization.py",
            "evals/m4/authorization/audit_m4_2_authorization.py",
            "tests/test_m4_2_authorization.py",
            *SUCCESSOR_PAIR,
        }
        self.assertTrue(required <= self.auditor.ALLOWED_CHANGE_PATHS)
        pair_present = all((REPO_ROOT / relative).is_file() for relative in SUCCESSOR_PAIR)
        self.assertEqual(
            self.auditor.valid_successor_authorization_pair(REPO_ROOT), pair_present
        )

    def test_candidate_projections_are_pure_non_instances(self) -> None:
        authorization = self.auditor.candidate_authorization_projection(REPO_ROOT)
        control = self.auditor.candidate_control_projection(REPO_ROOT)
        self.assertIs(authorization["projection_only"], True)
        self.assertIs(control["projection_only"], True)
        self.assertIsNone(authorization["authorization_token"])
        self.assertEqual(authorization["authorization_token_status"], "NOT_ISSUED")
        self.assertIs(authorization["fresh_execution_authorized"], False)
        self.assertIs(authorization["claim_authorized"], False)
        self.assertIs(control["execution_ready"], False)
        self.assertIs(control["claim_ready"], False)
        self.assertEqual(authorization["future_whole_matrix_task_count"], 60)
        self.assertEqual(control["future_controlled_task_count"], 60)
        self.assertEqual(control["visible_result_task_ids"], [])
        self.assertIs(control["cross_task_result_visibility"], False)
        self.assertFalse(
            self.auditor.projection_is_future_authorization_instance(authorization)
        )
        self.assertFalse(self.auditor.projection_is_future_control_instance(control))

    def test_gate_iv_b_b3_and_b4_delivery_are_exact(self) -> None:
        evidence = self.artifact["gate_iv_b_evidence"]
        self.assertEqual(evidence["b3"]["head"], B3_HEAD)
        self.assertEqual(evidence["b4"]["head"], BASELINE_HEAD)
        self.assertEqual(evidence["b4"]["proof_artifact"]["git_blob_oid"], PROOF_BLOB)
        self.assertEqual(evidence["b4"]["proof_artifact"]["raw_sha256"], PROOF_SHA256)
        self.assertEqual(
            evidence["b4"]["proof_artifact"]["byte_length"], PROOF_BYTE_LENGTH
        )
        expected_runs = {
            "b3": {"push": 31370941146, "pull_request": 31370945548},
            "b4": {"push": 31371973449, "pull_request": 31371976651},
        }
        for stage, events in expected_runs.items():
            for event, run_id in events.items():
                with self.subTest(stage=stage, event=event):
                    run = evidence[stage][event]
                    self.assertEqual(run["run_id"], run_id)
                    self.assertEqual(run["event"], event)
                    self.assertEqual(run["job_count"], 11)
                    self.assertEqual(len(run["jobs"]), 11)
                    self.assertTrue(
                        all(job["conclusion"] == "success" for job in run["jobs"])
                    )
                    self.assertEqual(run["raw_log"]["markers"], ZERO_MARKERS)

    def test_strict_loader_rejects_duplicate_keys_bom_and_nonfinite(self) -> None:
        for raw, expected in (
            (b'{"x":1,"x":2}', "sample_duplicate_key"),
            (b"\xef\xbb\xbf{}", "sample_bom_forbidden"),
            (b'{"x":NaN}', "sample_invalid_json"),
        ):
            errors: list[str] = []
            self.assertEqual(self.auditor.load_json_bytes(raw, "sample", errors), {})
            self.assertIn(expected, errors)

    def test_workflow_runs_preparation_and_request_verification_both_platforms(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        self.assertIn("m4-2-authorization-preparation:", workflow)
        job = workflow.split("m4-2-authorization-preparation:", 1)[1]
        self.assertIn("M4.2 authorization preparation (NOT AUTHORIZED)", job)
        self.assertIn("ubuntu-latest", job)
        self.assertIn("windows-latest", job)
        self.assertIn("tests.test_m4_2_authorization_preparation", job)
        self.assertIn("audit_m4_2_authorization_preparation.py", job)
        self.assertIn("audit_m4_2_gate_iv_b_protocol_proof.py", job)
        self.assertIn("audit_results.py --expect-not-run", job)
        self.assertIn("prepare_m4_2_request_bundles.ps1 -CheckAll", job)
        self.assertIn("git status", job)
        self.assertNotIn("continue-on-error", job)

    def test_auditor_is_offline_read_only_and_no_authorization_writer_exists(self) -> None:
        source = AUDITOR_PATH.read_text(encoding="utf-8")
        for forbidden in (
            "import urllib",
            "from urllib",
            "import requests",
            "from requests",
            "import socket",
            "http.client",
            ".write_text(",
            ".write_bytes(",
            "create_thread",
            "send_message_to_thread",
            "build_m4_1_authorization",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)
        self.assertTrue((AUTHORIZATION_ROOT / "build_m4_2_authorization.py").is_file())
        self.assertTrue((AUTHORIZATION_ROOT / "audit_m4_2_authorization.py").is_file())

    def test_cli_is_byte_repeatable_and_read_only(self) -> None:
        before = subprocess.run(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
        ).stdout
        first = subprocess.run(
            [sys.executable, "-X", "utf8", str(AUDITOR_PATH)],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
        )
        second = subprocess.run(
            [sys.executable, "-X", "utf8", str(AUDITOR_PATH)],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
        )
        after = subprocess.run(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
        ).stdout
        self.assertEqual(first.returncode, 0, first.stderr.decode("utf-8", "replace"))
        self.assertEqual(second.returncode, 0, second.stderr.decode("utf-8", "replace"))
        self.assertEqual(first.stdout, second.stdout)
        self.assertEqual(before, after)
        self.assertEqual(json.loads(first.stdout)["errors"], [])

    def test_final_status_is_written_only_after_verified_candidate_delivery(self) -> None:
        delivery = self.artifact["delivery"]
        status = STATUS_PATH.read_text(encoding="utf-8")
        if delivery["status"] == "VERIFIED_TRUE_GREEN":
            self.assertIn(FINAL_STATUS, status)
            self.assertIn(FINAL_DECISION, status)
            self.assertIn("authorization artifact=ABSENT", status)
            self.assertIn("authorization token=NOT_ISSUED", status)
        else:
            self.assertNotIn(FINAL_STATUS, status)


@unittest.skipUnless(IMPLEMENTED, "AP1 red: authorization preparation absent")
class M42AuthorizationPreparationMutationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.auditor = _load_auditor()
        cls.artifact = _load_json(ARTIFACT_PATH)

    def _assert_blocked(self, artifact: dict[str, Any], error: str) -> None:
        result = self.auditor.audit_authorization_preparation(
            REPO_ROOT, artifact_data=artifact, verify_git=False
        )
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn(error, result["errors"])

    def test_rejects_unknown_root_key(self) -> None:
        artifact = copy.deepcopy(self.artifact)
        artifact["unexpected"] = True
        self._assert_blocked(artifact, "artifact_root_keys_mismatch")

    def test_rejects_baseline_proof_or_delivery_drift(self) -> None:
        mutations = (
            (("baseline", "required_ancestor_head"), "0" * 40, "baseline_mismatch"),
            (
                ("gate_iv_b_evidence", "b4", "proof_artifact", "git_blob_oid"),
                "0" * 40,
                "gate_iv_b_evidence_mismatch",
            ),
            (
                ("gate_iv_b_evidence", "b3", "push", "job_count"),
                10,
                "gate_iv_b_evidence_mismatch",
            ),
        )
        for path, value, error in mutations:
            artifact = copy.deepcopy(self.artifact)
            target: dict[str, Any] = artifact
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = value
            with self.subTest(path=path):
                self._assert_blocked(artifact, error)

    def test_rejects_matrix_request_projection_or_policy_drift(self) -> None:
        mutations = (
            ("matrix_projection", "planned_task_count", 59, "matrix_projection_mismatch"),
            ("request_binding_projection", "matched", 59, "request_binding_projection_mismatch"),
            ("policy_proofs", "partial_authority_allowed", True, "policy_proofs_mismatch"),
        )
        for section, key, value, error in mutations:
            artifact = copy.deepcopy(self.artifact)
            artifact[section][key] = value
            with self.subTest(section=section, key=key):
                self._assert_blocked(artifact, error)

    def test_rejects_projection_that_issues_token_or_authority(self) -> None:
        artifact = copy.deepcopy(self.artifact)
        artifact["authorization_projection"]["authorization_token"] = "sha256:" + "0" * 64
        artifact["authorization_projection"]["fresh_execution_authorized"] = True
        self._assert_blocked(artifact, "authorization_projection_mismatch")

    def test_rejects_nonzero_counter_or_forbidden_path(self) -> None:
        artifact = copy.deepcopy(self.artifact)
        artifact["negative_authority"]["created_contexts"] = 1
        self._assert_blocked(artifact, "negative_authority_mismatch")
        result = self.auditor.audit_authorization_preparation(
            REPO_ROOT,
            artifact_data=self.artifact,
            verify_git=False,
            present_paths={FORBIDDEN_EXACT[0]},
        )
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("forbidden_future_path_present", result["errors"])

    def test_rejects_execution_authorizing_decision_or_findings(self) -> None:
        artifact = copy.deepcopy(self.artifact)
        artifact["decision"] = "AUTHORIZE_M4_2_EXECUTION"
        self._assert_blocked(artifact, "decision_attempts_execution_authorization")
        artifact = copy.deepcopy(self.artifact)
        artifact["findings"] = [{"code": "unexpected"}]
        self._assert_blocked(artifact, "findings_present")

    def test_rejects_final_state_without_valid_candidate_delivery(self) -> None:
        artifact = copy.deepcopy(self.artifact)
        artifact["delivery"] = self.auditor.provisional_delivery()
        artifact["decision"] = FINAL_DECISION
        artifact["status"] = FINAL_STATUS
        self._assert_blocked(artifact, "decision_status_state_mismatch")


if __name__ == "__main__":
    unittest.main()
