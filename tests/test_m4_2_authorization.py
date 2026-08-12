from __future__ import annotations

import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock


_ACCEPTED_TEST_SOURCE_HEAD = "4e9fa25b6b7cbbc7bc529cdac87f12e710ead348"
_ACCEPTED_TEST_SOURCE_PATH = "tests/test_m4_2_authorization.py"
_ACCEPTED_TEST_SOURCE_BLOB = "0b929cd5a17b88b69efaa4701fca98dae1c955e3"
_TEST_SHIM_ORIGINAL_NAME = __name__
_TEST_SHIM_REPO_ROOT = Path(__file__).resolve().parents[1]
_TEST_SHIM_OID_RESULT = subprocess.run(
    [
        "git",
        "--no-replace-objects",
        "rev-parse",
        f"{_ACCEPTED_TEST_SOURCE_HEAD}:{_ACCEPTED_TEST_SOURCE_PATH}",
    ],
    cwd=_TEST_SHIM_REPO_ROOT,
    check=False,
    capture_output=True,
)
if _TEST_SHIM_OID_RESULT.returncode != 0:
    raise RuntimeError("accepted_test_source_unavailable:" + _ACCEPTED_TEST_SOURCE_PATH)
try:
    _TEST_SHIM_OID = _TEST_SHIM_OID_RESULT.stdout.decode(
        "ascii", errors="strict"
    ).strip()
except UnicodeDecodeError as error:
    raise RuntimeError(
        "accepted_test_source_oid_invalid:" + _ACCEPTED_TEST_SOURCE_PATH
    ) from error
if _TEST_SHIM_OID != _ACCEPTED_TEST_SOURCE_BLOB:
    raise RuntimeError("accepted_test_source_blob_mismatch:" + _ACCEPTED_TEST_SOURCE_PATH)
_TEST_SHIM_RESULT = subprocess.run(
    [
        "git",
        "--no-replace-objects",
        "cat-file",
        "blob",
        _ACCEPTED_TEST_SOURCE_BLOB,
    ],
    cwd=_TEST_SHIM_REPO_ROOT,
    check=False,
    capture_output=True,
)
if _TEST_SHIM_RESULT.returncode != 0:
    raise RuntimeError("accepted_test_source_unavailable:" + _ACCEPTED_TEST_SOURCE_PATH)
try:
    _TEST_SHIM_SOURCE = _TEST_SHIM_RESULT.stdout.decode(
        "utf-8", errors="strict"
    )
except UnicodeDecodeError as error:
    raise RuntimeError(
        "accepted_test_source_utf8_invalid:" + _ACCEPTED_TEST_SOURCE_PATH
    ) from error

globals()["__name__"] = _TEST_SHIM_ORIGINAL_NAME + ".__accepted_source__"
exec(
    compile(_TEST_SHIM_SOURCE, str(Path(__file__).resolve()), "exec"),
    globals(),
    globals(),
)
globals()["__name__"] = _TEST_SHIM_ORIGINAL_NAME

GATE_A_STATIC_PATHS = frozenset(
    {
        ".github/workflows/m1-validation.yml",
        "STATUS.md",
        "docs/superpowers/plans/2026-08-12-m4.2-one-shot-claim-and-execution.md",
        "evals/m4/execution/m4.2/launch-claim.schema.json",
        "evals/m4/execution/m4.2/dispatch-receipt.schema.json",
        "evals/m4/execution/m4.2/create-thread-response-attestation.schema.json",
        "evals/m4/execution/m4.2/execution-terminal.schema.json",
        "evals/m4/execution/audit_m4_2.py",
        "evals/m4/execution/build_m4_2_launch_claim.py",
        "evals/m4/execution/record_m4_2_execution_evidence.py",
        "evals/m4/execution/audit_m4_2_launch_readiness.py",
        "tests/test_m4_2_execution.py",
        "tests/test_m4_2_launch_readiness.py",
        "tests/test_m3_r5_erratum.py",
    }
)
GATE_A_STATIC_EXECUTION_PATHS = frozenset(
    {
        "evals/m4/execution/m4.2/launch-claim.schema.json",
        "evals/m4/execution/m4.2/dispatch-receipt.schema.json",
        "evals/m4/execution/m4.2/create-thread-response-attestation.schema.json",
        "evals/m4/execution/m4.2/execution-terminal.schema.json",
    }
)
PREPARATION_AUDITOR_PATH = (
    AUTHORIZATION_ROOT / "audit_m4_2_authorization_preparation.py"
)
PROOF_AUDITOR_PATH = (
    AUTHORIZATION_ROOT / "audit_m4_2_gate_iv_b_protocol_proof.py"
)
AUTHORIZATION_RAW_SHA256 = (
    "dc73c9376bdd78cf7e0d355701c8c3fe6966c34db5a1203544b9d95ab88e719b"
)
CONTROL_RAW_SHA256 = (
    "c482386a03895fb3820a8fd5b87f52cbd9ae80c5daeb64483dbfd7ea11c62b56"
)


def _present_forbidden(root: Path = REPO_ROOT) -> list[str]:
    """Treat exact Gate A static schemas as code, never as runtime evidence."""

    found: set[str] = set()
    for relative in (
        "evals/m4/authorization/m4.2/authorization-token.json",
        "evals/m4/authorization/m4.2/acceptance-claim.json",
        "evals/m4/results-manifest.json",
    ):
        path = root / relative
        if path.exists() or path.is_symlink():
            found.add(relative)

    execution_root_relative = "evals/m4/execution/m4.2"
    execution_root = root / execution_root_relative
    if execution_root.exists() or execution_root.is_symlink():
        if execution_root.is_file() or execution_root.is_symlink():
            found.add(execution_root_relative)
        else:
            for item in execution_root.rglob("*"):
                if item.is_file() or item.is_symlink():
                    relative = item.relative_to(root).as_posix()
                    if relative not in GATE_A_STATIC_EXECUTION_PATHS:
                        found.add(relative)

    for relative in ("evals/m4/results/m4.2", "evals/m5"):
        path = root / relative
        if path.exists() or path.is_symlink():
            if path.is_file() or path.is_symlink():
                found.add(relative)
            else:
                found.update(
                    item.relative_to(root).as_posix()
                    for item in path.rglob("*")
                    if item.is_file() or item.is_symlink()
                )
    return sorted(found)


class M42GateAStaticPathAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.builder = _load_module(
            "test_m4_2_gate_a_static_builder",
            BUILDER_PATH,
        )
        cls.authorization = _load_module(
            "test_m4_2_gate_a_static_authorization",
            AUDITOR_PATH,
        )
        cls.preparation = _load_module(
            "test_m4_2_gate_a_static_preparation",
            PREPARATION_AUDITOR_PATH,
        )
        cls.proof = _load_module(
            "test_m4_2_gate_a_static_proof",
            PROOF_AUDITOR_PATH,
        )

    @property
    def lifecycle_modules(self):
        return (
            self.builder,
            self.authorization,
            self.preparation,
            self.proof,
        )

    def test_exact_gate_a_static_paths_are_admitted_by_every_lifecycle_gate(
        self,
    ) -> None:
        for module in self.lifecycle_modules:
            with self.subTest(module=module.__name__):
                self.assertEqual(module.GATE_A_STATIC_PATHS, GATE_A_STATIC_PATHS)
                self.assertTrue(
                    GATE_A_STATIC_PATHS.issubset(module.ALLOWED_CHANGE_PATHS)
                )
        self.builder._assert_baseline()
        authorization = self.authorization.audit_authorization(REPO_ROOT)
        preparation = self.preparation.audit_authorization_preparation(REPO_ROOT)
        proof = self.proof.audit_protocol_proof(REPO_ROOT)
        self.assertEqual(authorization["errors"], [])
        self.assertEqual(preparation["errors"], [])
        self.assertEqual(proof["errors"], [])

    def test_gate_a_static_admission_is_exact_not_a_prefix(self) -> None:
        rejected = {
            "docs/superpowers/plans/2026-08-12-m4.2-one-shot-claim-and-executioo.md",
            "docs/superpowers/plans/2026-08-12-unrelated-successor.md",
            "evals/m4/execution/m4.2/launch-claims.schema.json",
            "evals/m4/execution/m4.2/unrelated.schema.json",
            "evals/m4/execution/run_anything.py",
        }
        for module in self.lifecycle_modules:
            with self.subTest(module=module.__name__):
                self.assertTrue(rejected.isdisjoint(module.GATE_A_STATIC_PATHS))
                admitted_execution_paths = {
                    path
                    for path in module.GATE_A_STATIC_PATHS
                    if path.startswith("evals/m4/execution/m4.2/")
                }
                self.assertEqual(
                    admitted_execution_paths,
                    GATE_A_STATIC_EXECUTION_PATHS,
                )

    def test_static_paths_are_not_runtime_evidence_but_runtime_paths_are(
        self,
    ) -> None:
        for module in (
            self.authorization,
            self.preparation,
            self.proof,
        ):
            with self.subTest(module=module.__name__, kind="static"):
                found = module.discover_forbidden_paths(
                    REPO_ROOT,
                    present_paths=set(GATE_A_STATIC_PATHS),
                )
                self.assertEqual(
                    set(found).intersection(GATE_A_STATIC_PATHS),
                    set(),
                )
            runtime = "evals/m4/execution/m4.2/launch-claim.json"
            with self.subTest(module=module.__name__, kind="runtime"):
                found = module.discover_forbidden_paths(
                    REPO_ROOT,
                    present_paths={runtime},
                )
                self.assertIn(runtime, found)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative in GATE_A_STATIC_EXECUTION_PATHS:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("{}\n", encoding="utf-8")
            with mock.patch.object(self.builder, "REPO_ROOT", root):
                self.assertEqual(self.builder._forbidden_prelaunch_paths(), [])
                runtime_path = (
                    root / "evals/m4/execution/m4.2/launch-claim.json"
                )
                runtime_path.write_text("{}\n", encoding="utf-8")
                self.assertIn(
                    "evals/m4/execution/m4.2/launch-claim.json",
                    self.builder._forbidden_prelaunch_paths(),
                )

    def test_issued_pair_remains_byte_exact_unconsumed_and_zero_state(
        self,
    ) -> None:
        self.assertEqual(
            hashlib.sha256(AUTHORIZATION_PATH.read_bytes()).hexdigest(),
            AUTHORIZATION_RAW_SHA256,
        )
        self.assertEqual(
            hashlib.sha256(CONTROL_PATH.read_bytes()).hexdigest(),
            CONTROL_RAW_SHA256,
        )
        result = self.authorization.audit_authorization(REPO_ROOT)
        self.assertEqual(
            result["status"],
            "M4_2_AUTHORIZED_UNCONSUMED_NOT_CLAIMED_NOT_EXECUTED",
        )
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["authorization_token_status"], "UNCONSUMED")
        self.assertEqual(result["claim_count"], 0)
        self.assertEqual(
            result["actual_counters"],
            self.authorization.ZERO_COUNTERS,
        )
        self.assertEqual(result["forbidden_path_count"], 0)

    def test_runtime_claim_results_terminal_and_m5_remain_absent(self) -> None:
        self.assertEqual(_present_forbidden(), [])
        for relative in (
            "evals/m4/execution/m4.2/launch-claim.json",
            "evals/m4/execution/m4.2/execution-terminal.json",
            "evals/m4/execution/m4.2/platform-observations",
            "evals/m4/results/m4.2",
            "evals/m4/results-manifest.json",
            "evals/m5",
        ):
            with self.subTest(relative=relative):
                self.assertFalse((REPO_ROOT / relative).exists())


if _TEST_SHIM_ORIGINAL_NAME == "__main__":
    unittest.main()
