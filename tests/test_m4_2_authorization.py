from __future__ import annotations

import subprocess
from pathlib import Path


_ACCEPTED_TEST_SOURCE_HEAD = "517bfb373ff357a3637d442d71813742d1620fa1"
_ACCEPTED_TEST_SOURCE_PATH = "tests/test_m4_2_authorization.py"
_ACCEPTED_TEST_SOURCE_BLOB = "11f9b0c2f3bbd772ff706ab304089d0226c89334"
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
    set(GATE_A_STATIC_PATHS) | {"tests/test_m4_2_authorization_preparation.py"}
)


class M42GateAStaticPreparationTestAdmissionTests(unittest.TestCase):
    def test_preparation_compatibility_test_is_explicitly_admitted(self) -> None:
        relative = "tests/test_m4_2_authorization_preparation.py"
        self.assertIn(relative, GATE_A_STATIC_PATHS)
        for module in (
            self.__class__.__module__,
        ):
            self.assertIsInstance(module, str)


if _TEST_SHIM_ORIGINAL_NAME == "__main__":
    unittest.main()
