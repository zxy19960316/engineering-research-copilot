from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


_ACCEPTED_TEST_SOURCE_HEAD = "4e9fa25b6b7cbbc7bc529cdac87f12e710ead348"
_ACCEPTED_TEST_SOURCE_PATH = "tests/test_m4_2_authorization_preparation.py"
_ACCEPTED_TEST_SOURCE_BLOB = "4ec193688a491f966045154b4beec6717e409674"
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

GATE_A_STATIC_EXECUTION_PATHS = frozenset(
    {
        "evals/m4/execution/m4.2/launch-claim.schema.json",
        "evals/m4/execution/m4.2/dispatch-receipt.schema.json",
        "evals/m4/execution/m4.2/create-thread-response-attestation.schema.json",
        "evals/m4/execution/m4.2/execution-terminal.schema.json",
    }
)


def _present_forbidden(root: Path = REPO_ROOT) -> list[str]:
    """Permit only exact Gate A static schemas, never runtime evidence."""

    found: set[str] = set()
    for relative in FORBIDDEN_EXACT:
        if (root / relative).exists():
            found.add(relative)
    for relative in FORBIDDEN_PREFIXES:
        path = root / relative
        if not path.exists():
            continue
        if path.is_file() or path.is_symlink():
            found.add(relative)
            continue
        for item in path.rglob("*"):
            if not (item.is_file() or item.is_symlink()):
                continue
            item_relative = item.relative_to(root).as_posix()
            if item_relative not in GATE_A_STATIC_EXECUTION_PATHS:
                found.add(item_relative)
    return sorted(found)


class M42GateAStaticPreparationCompatibilityTests(unittest.TestCase):
    def test_exact_gate_a_static_schemas_are_not_runtime_evidence(self) -> None:
        self.assertEqual(_present_forbidden(), [])

    def test_runtime_siblings_remain_forbidden(self) -> None:
        runtime = "evals/m4/execution/m4.2/launch-claim.json"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative in GATE_A_STATIC_EXECUTION_PATHS:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("{}\n", encoding="utf-8")
            self.assertEqual(_present_forbidden(root), [])
            runtime_path = root / runtime
            runtime_path.write_text("{}\n", encoding="utf-8")
            self.assertIn(runtime, _present_forbidden(root))


if _TEST_SHIM_ORIGINAL_NAME == "__main__":
    unittest.main()
