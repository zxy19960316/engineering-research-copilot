from __future__ import annotations

import subprocess
from pathlib import Path

_ACCEPTED_TEST_SOURCE_HEAD = "4e9fa25b6b7cbbc7bc529cdac87f12e710ead348"
_ACCEPTED_TEST_SOURCE_PATH = "tests/test_m4_2_authorization.py"
_ACCEPTED_TEST_SOURCE_BLOB = "0b929cd5a17b88b69efaa4701fca98dae1c955e3"
_SUCCESSOR_CLAIM_EXECUTION_PLAN_PATH = "docs/superpowers/plans/2026-08-12-m4.2-one-shot-claim-and-execution.md"
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
    _TEST_SHIM_OID = _TEST_SHIM_OID_RESULT.stdout.decode("ascii", errors="strict").strip()
except UnicodeDecodeError as error:
    raise RuntimeError("accepted_test_source_oid_invalid:" + _ACCEPTED_TEST_SOURCE_PATH) from error
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
    _TEST_SHIM_SOURCE = _TEST_SHIM_RESULT.stdout.decode("utf-8", errors="strict")
except UnicodeDecodeError as error:
    raise RuntimeError("accepted_test_source_utf8_invalid:" + _ACCEPTED_TEST_SOURCE_PATH) from error

globals()["__name__"] = _TEST_SHIM_ORIGINAL_NAME + ".__accepted_source__"
exec(
    compile(_TEST_SHIM_SOURCE, str(Path(__file__).resolve()), "exec"),
    globals(),
    globals(),
)
globals()["__name__"] = _TEST_SHIM_ORIGINAL_NAME

SUCCESSOR_CLAIM_EXECUTION_PLAN_RELATIVE = _SUCCESSOR_CLAIM_EXECUTION_PLAN_PATH
PREPARATION_AUDITOR_PATH = AUTHORIZATION_ROOT / "audit_m4_2_authorization_preparation.py"
PROOF_AUDITOR_PATH = AUTHORIZATION_ROOT / "audit_m4_2_gate_iv_b_protocol_proof.py"
AUTHORIZATION_RAW_SHA256 = "dc73c9376bdd78cf7e0d355701c8c3fe6966c34db5a1203544b9d95ab88e719b"
CONTROL_RAW_SHA256 = "c482386a03895fb3820a8fd5b87f52cbd9ae80c5daeb64483dbfd7ea11c62b56"


class M42ClaimExecutionPlanPathCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.builder = _load_module(
            "test_m4_2_plan_path_builder", BUILDER_PATH
        )
        cls.authorization = _load_module(
            "test_m4_2_plan_path_authorization", AUDITOR_PATH
        )
        cls.preparation = _load_module(
            "test_m4_2_plan_path_preparation", PREPARATION_AUDITOR_PATH
        )
        cls.proof = _load_module(
            "test_m4_2_plan_path_proof", PROOF_AUDITOR_PATH
        )

    @property
    def lifecycle_modules(self):
        return (
            self.builder,
            self.authorization,
            self.preparation,
            self.proof,
        )

    def test_exact_successor_plan_path_is_admitted_by_every_lifecycle_gate(self) -> None:
        for module in self.lifecycle_modules:
            with self.subTest(module=module.__name__):
                self.assertEqual(
                    module.SUCCESSOR_CLAIM_EXECUTION_PLAN_RELATIVE,
                    SUCCESSOR_CLAIM_EXECUTION_PLAN_RELATIVE,
                )
                self.assertIn(
                    SUCCESSOR_CLAIM_EXECUTION_PLAN_RELATIVE,
                    module.ALLOWED_CHANGE_PATHS,
                )
        self.builder._assert_baseline()
        authorization = self.authorization.audit_authorization(REPO_ROOT)
        preparation = self.preparation.audit_authorization_preparation(REPO_ROOT)
        proof = self.proof.audit_protocol_proof(REPO_ROOT)
        self.assertEqual(authorization["errors"], [])
        self.assertEqual(preparation["errors"], [])
        self.assertEqual(proof["errors"], [])

    def test_sibling_and_arbitrary_docs_paths_remain_rejected(self) -> None:
        one_character_sibling = SUCCESSOR_CLAIM_EXECUTION_PLAN_RELATIVE.replace(
            "execution.md", "executioo.md"
        )
        arbitrary_docs_path = (
            "docs/superpowers/plans/2026-08-12-unrelated-successor.md"
        )
        self.assertNotEqual(
            one_character_sibling,
            SUCCESSOR_CLAIM_EXECUTION_PLAN_RELATIVE,
        )
        for module in self.lifecycle_modules:
            with self.subTest(module=module.__name__):
                self.assertNotIn(one_character_sibling, module.ALLOWED_CHANGE_PATHS)
                self.assertNotIn(arbitrary_docs_path, module.ALLOWED_CHANGE_PATHS)
                admitted_2026_08_12_plans = {
                    path
                    for path in module.ALLOWED_CHANGE_PATHS
                    if path.startswith("docs/superpowers/plans/2026-08-12-")
                }
                self.assertEqual(
                    admitted_2026_08_12_plans,
                    {SUCCESSOR_CLAIM_EXECUTION_PLAN_RELATIVE},
                )

    def test_issued_pair_remains_byte_exact_unconsumed_and_zero_state(self) -> None:
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
        self.assertEqual(result["actual_counters"], self.authorization.ZERO_COUNTERS)
        self.assertEqual(result["forbidden_path_count"], 0)

    def test_claim_execution_results_and_m5_remain_absent(self) -> None:
        self.assertEqual(_present_forbidden(), [])
        for relative in (
            "evals/m4/execution/m4.2",
            "evals/m4/results/m4.2",
            "evals/m4/results-manifest.json",
            "evals/m5",
        ):
            with self.subTest(relative=relative):
                self.assertFalse((REPO_ROOT / relative).exists())


if _TEST_SHIM_ORIGINAL_NAME == "__main__":
    unittest.main()
