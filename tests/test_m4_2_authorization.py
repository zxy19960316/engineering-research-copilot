from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
AUTHORIZATION_ROOT = REPO_ROOT / "evals" / "m4" / "authorization"
M42_ROOT = AUTHORIZATION_ROOT / "m4.2"
BUILDER_PATH = AUTHORIZATION_ROOT / "build_m4_2_authorization.py"
AUDITOR_PATH = AUTHORIZATION_ROOT / "audit_m4_2_authorization.py"
AUTHORIZATION_PATH = M42_ROOT / "execution-authorization.json"
CONTROL_PATH = M42_ROOT / "execution-control.json"
AUTHORIZATION_SCHEMA_PATH = M42_ROOT / "execution-authorization.schema.json"
CONTROL_SCHEMA_PATH = M42_ROOT / "execution-control.schema.json"
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "m1-validation.yml"
BASELINE_HEAD = "4efa75c542172a95c6c72c8c1450fea77a8e2ff1"
BASELINE_TREE = "f7394004d9d5f0a9be22a62dca1d67bb5f2af52d"
BRANCH = "codex/m4-cross-engineering-forward-evaluation-m4.2-one-shot-authorization"

FORBIDDEN_EXACT = (
    "evals/m4/authorization/m4.2/authorization-token.json",
    "evals/m4/authorization/m4.2/acceptance-claim.json",
    "evals/m4/results-manifest.json",
)
FORBIDDEN_PREFIXES = (
    "evals/m4/execution/m4.2",
    "evals/m4/results/m4.2",
    "evals/m5",
)


def _git(*arguments: str) -> str:
    return subprocess.run(
        ["git", "--no-replace-objects", *arguments],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout.strip()


def _load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"module_unavailable:{name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


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


IMPLEMENTED = BUILDER_PATH.is_file() and AUDITOR_PATH.is_file()


class M42AuthorizationRedFirstTests(unittest.TestCase):
    def test_exact_preparation_closure_baseline_is_available(self) -> None:
        self.assertEqual(_git("rev-parse", f"{BASELINE_HEAD}^{{tree}}"), BASELINE_TREE)
        self.assertEqual(
            subprocess.run(
                ["git", "--no-replace-objects", "merge-base", "--is-ancestor", BASELINE_HEAD, "HEAD"],
                cwd=REPO_ROOT,
                check=False,
            ).returncode,
            0,
        )

    def test_instances_are_both_absent_or_both_present(self) -> None:
        self.assertEqual(AUTHORIZATION_PATH.exists(), CONTROL_PATH.exists())

    def test_claim_execution_results_and_m5_are_absent(self) -> None:
        self.assertEqual(_present_forbidden(), [])

    def test_candidate_implementation_files_exist(self) -> None:
        missing = [
            path.relative_to(REPO_ROOT).as_posix()
            for path in (BUILDER_PATH, AUDITOR_PATH)
            if not path.is_file()
        ]
        self.assertEqual(missing, [])


@unittest.skipUnless(IMPLEMENTED, "red-first: M4.2 authorization implementation absent")
class M42AuthorizationContractTests(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.build = _load_module("test_build_m4_2_authorization", BUILDER_PATH)
        cls.audit = _load_module("test_audit_m4_2_authorization", AUDITOR_PATH)
        cls.artifacts = cls.build.build_artifacts()
        cls.authorization_raw = cls.artifacts[AUTHORIZATION_PATH]
        cls.control_raw = cls.artifacts[CONTROL_PATH]
        cls.authorization = cls.audit.load_json_bytes(
            cls.authorization_raw, "authorization", []
        )
        cls.control = cls.audit.load_json_bytes(cls.control_raw, "control", [])

    def _audit_pair(
        self,
        authorization: dict[str, object],
        control: dict[str, object],
        *,
        present_paths: set[str] | None = None,
    ) -> dict[str, object]:
        return self.audit.audit_authorization(
            REPO_ROOT,
            authorization_data=authorization,
            control_data=control,
            verify_git=False,
            present_paths=present_paths,
        )

    def _assert_mutation_blocked(
        self,
        mutate,
        *,
        target: str = "authorization",
    ) -> None:
        authorization = copy.deepcopy(self.authorization)
        control = copy.deepcopy(self.control)
        selected = authorization if target == "authorization" else control
        before = _canonical(selected)
        mutate(selected)
        after = _canonical(selected)
        self.assertNotEqual(before, after, "mutation must change canonical bytes")
        result = self._audit_pair(authorization, control)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertTrue(result["errors"])

    def test_build_artifacts_is_pure_exact_and_byte_stable(self) -> None:
        before = subprocess.run(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
        ).stdout
        first = self.build.build_artifacts()
        second = self.build.build_artifacts()
        after = subprocess.run(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
        ).stdout
        self.assertEqual(set(first), {AUTHORIZATION_PATH, CONTROL_PATH})
        self.assertEqual(first, second)
        self.assertEqual(before, after)

    def test_built_instances_match_frozen_schemas(self) -> None:
        for instance, schema_path in (
            (self.authorization, AUTHORIZATION_SCHEMA_PATH),
            (self.control, CONTROL_SCHEMA_PATH),
        ):
            schema = self.audit.load_json_bytes(schema_path.read_bytes(), "schema", [])
            self.assertEqual(self.audit.schema_errors(instance, schema), [])

    def test_authorization_exact_unconsumed_shape(self) -> None:
        authorization = self.authorization
        self.assertEqual(authorization["status"], "AUTHORIZED_UNCONSUMED")
        self.assertEqual(authorization["model_binding"]["exact_model_id"], "gpt-5.6-sol")
        self.assertEqual(authorization["model_binding"]["reasoning_effort"], "max")
        self.assertEqual(authorization["execution_surface"]["starting_branch"], BRANCH)
        self.assertEqual(authorization["authority"]["authorized_task_count"], 60)
        self.assertEqual(authorization["authority"]["authorized_batch_count"], 6)
        self.assertEqual(authorization["authority"]["fresh_contexts_authorized"], 60)
        self.assertEqual(
            authorization["authority"]["independent_finalizations_authorized"], 60
        )
        self.assertTrue(authorization["authority"]["whole_matrix_required"])
        self.assertFalse(authorization["authority"]["partial_authority_allowed"])
        self.assertEqual(authorization["prelaunch_counters"], self.build.ZERO_COUNTERS)
        self.assertEqual(authorization["consumption"]["claim_count"], 0)
        self.assertEqual(
            authorization["consumption"]["authorization_token_status"], "UNCONSUMED"
        )
        self.assertEqual(
            authorization["authorization_token"],
            self.build.authorization_token(authorization),
        )
        historical_errors: list[str] = []
        self.assertNotIn(
            authorization["authorization_token"],
            self.audit._historical_tokens(REPO_ROOT, historical_errors),
        )
        self.assertEqual(historical_errors, [])

    def test_frozen_source_binding_mutations_are_rejected(self) -> None:
        with self.subTest(binding="baseline_head"):
            with mock.patch.object(self.build, "BASELINE_HEAD", "0" * 40):
                with self.assertRaisesRegex(ValueError, "baseline_head_unavailable"):
                    self.build.build_artifacts()
        with self.subTest(binding="baseline_tree"):
            with mock.patch.object(self.build, "BASELINE_TREE", "0" * 40):
                with self.assertRaisesRegex(ValueError, "baseline_tree_mismatch"):
                    self.build.build_artifacts()

        snapshot_mutations = (
            (self.build.PREPARATION_RELATIVE, 0, "preparation_blob"),
            (self.build.PREPARATION_RELATIVE, 1, "preparation_raw_sha256"),
            (self.build.PROOF_RELATIVE, 0, "proof_blob"),
            (self.build.PROOF_RELATIVE, 1, "proof_raw_sha256"),
            (self.build.AUTHORIZATION_SCHEMA_RELATIVE, 1, "authorization_schema_raw_sha256"),
            (self.build.CONTROL_SCHEMA_RELATIVE, 1, "control_schema_raw_sha256"),
            (self.build.HELPER_RELATIVE, 1, "helper_raw_sha256"),
        )
        for relative, field, label in snapshot_mutations:
            with self.subTest(binding=label):
                original = self.build.SNAPSHOTS[relative]
                mutated = list(original)
                mutated[field] = "0" * len(str(mutated[field]))
                self.assertNotEqual(tuple(mutated), original)
                with mock.patch.dict(
                    self.build.SNAPSHOTS,
                    {relative: tuple(mutated)},
                ):
                    with self.assertRaises(ValueError):
                        self.build.build_artifacts()

    def test_control_cross_links_roster_batches_and_result_roots(self) -> None:
        control = self.control
        self.assertEqual(control["status"], "READY_UNCONSUMED")
        self.assertEqual(
            control["authorization"]["raw_sha256"],
            hashlib.sha256(self.authorization_raw).hexdigest(),
        )
        self.assertEqual(
            control["authorization"]["authorization_token"],
            self.authorization["authorization_token"],
        )
        self.assertEqual(len(control["tasks"]), 60)
        self.assertEqual(len(control["batches"]), 6)
        self.assertEqual(len(set(task["task_id"] for task in control["tasks"])), 60)
        self.assertEqual(len(set(task["blind_id"] for task in control["tasks"])), 60)
        batch_tasks = [task_id for batch in control["batches"] for task_id in batch["task_ids"]]
        self.assertEqual(sorted(batch_tasks), sorted(task["task_id"] for task in control["tasks"]))
        for task in control["tasks"]:
            self.assertTrue(task["result_root"].startswith("evals/m4/results/m4.2/M4.2-"))
            self.assertTrue(task["result_root_must_be_absent"])
            self.assertEqual(task["forbidden_context_roots"], ["evals/m4/results", "evals/m4/execution"])
            self.assertEqual(task["attempt_limit"], 1)
            self.assertTrue(task["independent_finalization_required"])
            self.assertFalse(task["cross_task_result_visibility"])

    def test_candidate_or_issued_repository_state_is_valid_and_read_only(self) -> None:
        before = subprocess.run(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
        ).stdout
        first = self.audit.audit_authorization(REPO_ROOT)
        second = self.audit.audit_authorization(REPO_ROOT)
        after = subprocess.run(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
        ).stdout
        expected = (
            "M4_2_AUTHORIZED_UNCONSUMED_NOT_CLAIMED_NOT_EXECUTED"
            if AUTHORIZATION_PATH.exists()
            else "M4_2_ONE_SHOT_AUTHORIZATION_CANDIDATE_READY_NOT_ISSUED"
        )
        self.assertEqual(first["status"], expected)
        self.assertEqual(first, second)
        self.assertEqual(first["errors"], [])
        self.assertEqual(before, after)

    def test_strict_json_loader_rejects_noncanonical_hazards(self) -> None:
        cases = (
            (b"\xef\xbb\xbf{}", "utf8_bom_forbidden"),
            (b'{"a":1,"a":2}', "duplicate_key"),
            (b'{"a":NaN}', "non_finite_number"),
            (b'[]', "object_root_required"),
            (b'\xff', "utf8_invalid"),
        )
        for raw, code in cases:
            errors: list[str] = []
            self.audit.load_json_bytes(raw, "sample", errors)
            self.assertTrue(any(code in error for error in errors), (code, errors))

    def test_authorization_mutations_are_rejected(self) -> None:
        mutations = (
            lambda value: value.__setitem__("status", "READY_UNCONSUMED"),
            lambda value: value["authorization_preparation"].__setitem__("accepted_candidate_head", "0" * 40),
            lambda value: value["authorization_preparation"].__setitem__("git_blob_oid", "0" * 40),
            lambda value: value["authorization_preparation"].__setitem__("raw_sha256", "0" * 64),
            lambda value: value["gate_iv_b_proof"].__setitem__("closure_head", "0" * 40),
            lambda value: value["gate_iv_b_proof"].__setitem__("git_blob_oid", "0" * 40),
            lambda value: value["gate_iv_b_proof"].__setitem__("raw_sha256", "0" * 64),
            lambda value: value["model_binding"].__setitem__("exact_model_id", "other"),
            lambda value: value["model_binding"].__setitem__("reasoning_effort", "high"),
            lambda value: value["execution_surface"].__setitem__("project_id", "other"),
            lambda value: value["execution_surface"].__setitem__("starting_branch", "main"),
            lambda value: value["authority"]["authorized_task_ids"].__setitem__(0, "M4.2-UNKNOWN"),
            lambda value: value["authority"]["authorized_task_ids"].__setitem__(1, value["authority"]["authorized_task_ids"][0]),
            lambda value: value["authority"]["authorized_task_ids"].__setitem__(slice(0, 2), list(reversed(value["authority"]["authorized_task_ids"][:2]))),
            lambda value: value["authority"]["authorized_task_ids"].pop(),
            lambda value: value["authority"]["authorized_batch_ids"].__setitem__(1, value["authority"]["authorized_batch_ids"][0]),
            lambda value: value["authority"].__setitem__("authorized_task_count", True),
            lambda value: value["authority"].__setitem__("partial_authority_allowed", True),
            lambda value: value["authority"].__setitem__("retry_authorized", True),
            lambda value: value["authority"].__setitem__("repair_authorized", True),
            lambda value: value["authority"].__setitem__("followup_message_authorized", True),
            lambda value: value["authority"].__setitem__("cross_task_result_visibility", True),
            lambda value: value["authority"].__setitem__("judge_execution_authorized", True),
            lambda value: value["authority"].__setitem__("blind_mapping_access_authorized", True),
            lambda value: value["authority"].__setitem__("aggregation_authorized", True),
            lambda value: value["authority"].__setitem__("threshold_claim_authorized", True),
            lambda value: value["authority"].__setitem__("closure_authorized", True),
            lambda value: value["consumption"].__setitem__("claim_count", 1),
            lambda value: value["consumption"].__setitem__("authorization_token_status", "CONSUMED"),
            lambda value: value["consumption"].__setitem__("second_claim_allowed", True),
            lambda value: value.__setitem__("authorization_token", value["authorization_token"][:-1] + ("0" if value["authorization_token"][-1] != "0" else "1")),
            lambda value: value.__setitem__("authorization_token", "sha256:" + "0" * 64),
            lambda value: value.__setitem__("unknown", None),
        )
        for index, mutation in enumerate(mutations):
            with self.subTest(index=index):
                self._assert_mutation_blocked(mutation)
        for counter in self.build.COUNTER_NAMES:
            with self.subTest(counter=counter):
                self._assert_mutation_blocked(
                    lambda value, counter=counter: value["prelaunch_counters"].__setitem__(counter, 1)
                )

    def test_control_mutations_are_rejected(self) -> None:
        mutations = (
            lambda value: value.__setitem__("status", "INVALID"),
            lambda value: value["authorization"].__setitem__("raw_sha256", "0" * 64),
            lambda value: value["authorization"].__setitem__("authorization_token", "sha256:" + "0" * 64),
            lambda value: value["preparation"].__setitem__("git_blob_oid", "0" * 40),
            lambda value: value["preparation"].__setitem__("raw_sha256", "0" * 64),
            lambda value: value["execution_helper"].__setitem__("git_blob_oid", "0" * 40),
            lambda value: value["execution_helper"].__setitem__("raw_sha256", "0" * 64),
            lambda value: value["tasks"].__setitem__(1, copy.deepcopy(value["tasks"][0])),
            lambda value: value["tasks"].pop(),
            lambda value: value["tasks"][0].__setitem__("task_id", "M4.2-UNKNOWN"),
            lambda value: value["tasks"][0].__setitem__("blind_id", value["tasks"][1]["blind_id"]),
            lambda value: value["tasks"][0].__setitem__("batch_id", value["tasks"][2]["batch_id"]),
            lambda value: value["tasks"][0].__setitem__("request_binding_sha256", "0" * 64),
            lambda value: value["tasks"][0].__setitem__("result_root", "../escape"),
            lambda value: value["tasks"][0].__setitem__("result_root", "/absolute/escape"),
            lambda value: value["tasks"][0].__setitem__("attempt_limit", True),
            lambda value: value["tasks"][0].__setitem__("cross_task_result_visibility", True),
            lambda value: value["batches"][0]["task_ids"].__setitem__(0, value["batches"][1]["task_ids"][0]),
            lambda value: value["launch_claim"].__setitem__("claim_count_before_execution", 1),
            lambda value: value["execution_constraints"].__setitem__("partial_authority_allowed", True),
            lambda value: value["execution_constraints"].__setitem__("second_claim_allowed", True),
            lambda value: value["permissions"].__setitem__("retry", True),
            lambda value: value["permissions"].__setitem__("repair", True),
            lambda value: value["permissions"].__setitem__("followup_message", True),
            lambda value: value["permissions"].__setitem__("cross_task_result_read", True),
            lambda value: value["permissions"].__setitem__("judge_execution", True),
            lambda value: value["permissions"].__setitem__("blind_mapping_access", True),
            lambda value: value["permissions"].__setitem__("aggregation", True),
            lambda value: value["permissions"].__setitem__("threshold_claim", True),
            lambda value: value["permissions"].__setitem__("m4_closure", True),
            lambda value: value.__setitem__("unknown", None),
        )
        for index, mutation in enumerate(mutations):
            with self.subTest(index=index):
                self._assert_mutation_blocked(mutation, target="control")
        for counter in self.build.COUNTER_NAMES:
            with self.subTest(counter=counter):
                self._assert_mutation_blocked(
                    lambda value, counter=counter: value["prelaunch_counters"].__setitem__(counter, 1),
                    target="control",
                )

    def test_forbidden_lifecycle_paths_are_rejected(self) -> None:
        paths = (
            "evals/m4/authorization/m4.2/authorization-token.json",
            "evals/m4/authorization/m4.2/acceptance-claim.json",
            "evals/m4/execution/m4.2/launch-claim.json",
            "evals/m4/execution/m4.2/dispatch.json",
            "evals/m4/results/m4.2/M4.2-NUC-A-F/final.json",
            "evals/m4/results-manifest.json",
            "evals/m5/state.json",
        )
        for path in paths:
            with self.subTest(path=path):
                result = self._audit_pair(
                    copy.deepcopy(self.authorization),
                    copy.deepcopy(self.control),
                    present_paths={path},
                )
                self.assertEqual(result["status"], "BLOCKED")
                self.assertIn(path, result["forbidden_paths"])

    def test_authorization_pair_symlink_escape_is_rejected(self) -> None:
        original_exists = Path.exists
        original_is_symlink = Path.is_symlink
        original_read_bytes = Path.read_bytes
        targets = {AUTHORIZATION_PATH, CONTROL_PATH}

        def mocked_exists(path: Path) -> bool:
            return True if path in targets else original_exists(path)

        def mocked_is_symlink(path: Path) -> bool:
            return True if path in targets else original_is_symlink(path)

        def mocked_read_bytes(path: Path) -> bytes:
            if path == AUTHORIZATION_PATH:
                return self.authorization_raw
            if path == CONTROL_PATH:
                return self.control_raw
            return original_read_bytes(path)

        with mock.patch.object(Path, "exists", mocked_exists), mock.patch.object(
            Path, "is_symlink", mocked_is_symlink
        ), mock.patch.object(Path, "read_bytes", mocked_read_bytes):
            result = self.audit.audit_authorization(REPO_ROOT, verify_git=False)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("authorization_pair_symlink_forbidden", result["errors"])

    def test_atomic_pair_publication_rolls_back_partial_failure_and_is_write_once(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            authorization = root / "execution-authorization.json"
            control = root / "execution-control.json"
            self.build._publish_pair(
                {authorization: b"authorization\n", control: b"control\n"}
            )
            self.assertEqual(authorization.read_bytes(), b"authorization\n")
            self.assertEqual(control.read_bytes(), b"control\n")
            with self.assertRaisesRegex(ValueError, "already_issued"):
                self.build._publish_pair(
                    {authorization: b"authorization\n", control: b"control\n"}
                )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            authorization = root / "execution-authorization.json"
            control = root / "execution-control.json"
            real_replace = self.build.os.replace
            calls = 0

            def fail_second(source: str | Path, target: str | Path) -> None:
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("simulated second publish failure")
                real_replace(source, target)

            with mock.patch.object(self.build.os, "replace", side_effect=fail_second):
                with self.assertRaisesRegex(OSError, "simulated second publish failure"):
                    self.build._publish_pair(
                        {authorization: b"authorization\n", control: b"control\n"}
                    )
            self.assertFalse(authorization.exists())
            self.assertFalse(control.exists())
            self.assertEqual(list(root.iterdir()), [])

    def test_cli_dry_run_truncates_token_and_writes_nothing(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-X", "utf8", str(BUILDER_PATH), "--dry-run"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        result = json.loads(completed.stdout)
        self.assertEqual(result["status"], "candidate_valid")
        self.assertNotIn(self.authorization["authorization_token"], completed.stdout)
        self.assertLess(len(result["token_fingerprint"]), len(self.authorization["authorization_token"]))
        if not AUTHORIZATION_PATH.exists():
            self.assertFalse(CONTROL_PATH.exists())

    def test_builder_and_auditor_sources_do_not_launch_or_use_network(self) -> None:
        for path in (BUILDER_PATH, AUDITOR_PATH):
            source = path.read_text(encoding="utf-8")
            self.assertNotIn("create_thread(", source)
            self.assertNotIn("urlopen(", source)
            self.assertNotIn("requests.", source)
            self.assertNotIn("socket.", source)
        self.assertNotIn("import build_m4_2_authorization", AUDITOR_PATH.read_text(encoding="utf-8"))

    def test_workflow_adds_two_cross_platform_lifecycle_jobs(self) -> None:
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        self.assertIn("m4-2-one-shot-authorization:", workflow)
        job = workflow.split("m4-2-one-shot-authorization:", 1)[1].split(
            "historical-audit-cross-platform:", 1
        )[0]
        self.assertIn("M4.2 one-shot authorization lifecycle (${{ matrix.os }})", job)
        self.assertIn("          - ubuntu-latest", job)
        self.assertIn("          - windows-latest", job)
        self.assertIn("tests.test_m4_2_authorization", job)
        self.assertIn("build_m4_2_authorization.py --dry-run", job)
        self.assertIn("build_m4_2_authorization.py --check", job)
        self.assertGreaterEqual(job.count("audit_m4_2_authorization.py"), 5)
        self.assertIn("audit_results.py --expect-not-run", job)
        self.assertIn("prepare_m4_2_request_bundles.ps1 -CheckAll", job)
        self.assertIn("expected_windows_powershell_5_1", job)
        self.assertNotIn("continue-on-error", job)


if __name__ == "__main__":
    unittest.main()
