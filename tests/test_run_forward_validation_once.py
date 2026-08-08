from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER = REPO_ROOT / "evals" / "m3" / "run_forward_validation_once.py"
sys.path.insert(0, str(REPO_ROOT / "evals" / "m3"))
sys.path.insert(0, str(REPO_ROOT / "tests"))

from test_validate_m3_method_bundle import make_valid_m3_bundle  # noqa: E402
from run_forward_validation_once import VALIDATOR_PATH, main  # noqa: E402


VALID_RESULT = {"status": "valid", "errors": [], "evidence_gaps": []}


class RunForwardValidationOnceTests(unittest.TestCase):
    def _write_json(self, path: Path, payload: object) -> None:
        path.write_text(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )

    def _run(self, output_path: Path, validation_path: Path, *extra: str):
        return subprocess.run(
            [
                sys.executable,
                "-X",
                "utf8",
                str(RUNNER),
                str(output_path),
                str(validation_path),
                *extra,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def test_valid_bundle_writes_one_line_validator_json_and_returns_zero(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output_path = root / "bundle.json"
            validation_path = root / "validation.json"
            self._write_json(output_path, make_valid_m3_bundle())

            completed = self._run(output_path, validation_path)

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(completed.stderr, "")
            raw = validation_path.read_bytes()
            self.assertFalse(raw.startswith(b"\xef\xbb\xbf"))
            self.assertEqual(raw.count(b"\n"), 1)
            self.assertEqual(json.loads(raw.decode("utf-8")), VALID_RESULT)

    def test_invalid_bundle_preserves_exact_validator_json_and_returns_one(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output_path = root / "bundle.json"
            validation_path = root / "validation.json"
            self._write_json(output_path, {})

            completed = self._run(output_path, validation_path)

            self.assertEqual(completed.returncode, 1)
            self.assertEqual(
                json.loads(validation_path.read_text(encoding="utf-8")),
                {
                    "status": "invalid",
                    "errors": ["invalid_m3_bundle"],
                    "evidence_gaps": [],
                },
            )

    def test_existing_validation_file_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output_path = root / "bundle.json"
            validation_path = root / "validation.json"
            self._write_json(output_path, make_valid_m3_bundle())
            validation_path.write_text("sentinel\n", encoding="utf-8")

            completed = self._run(output_path, validation_path)

            self.assertNotEqual(completed.returncode, 0)
            self.assertEqual(validation_path.read_text(encoding="utf-8"), "sentinel\n")

    def test_runner_rejects_extra_arguments(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            completed = self._run(root / "bundle.json", root / "validation.json", "extra")

            self.assertNotEqual(completed.returncode, 0)

    def test_validator_command_has_one_output_path_and_fixed_validator(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output_path = root / "bundle.json"
            validation_path = root / "validation.json"
            self._write_json(output_path, make_valid_m3_bundle())
            completed_process = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout=json.dumps(VALID_RESULT, separators=(",", ":")) + "\n",
                stderr="",
            )

            with mock.patch(
                "run_forward_validation_once.subprocess.run",
                return_value=completed_process,
            ) as run_mock:
                self.assertEqual(main([str(output_path), str(validation_path)]), 0)

            run_mock.assert_called_once_with(
                [sys.executable, "-X", "utf8", str(VALIDATOR_PATH), str(output_path)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="strict",
            )

    def test_nonempty_stderr_writes_closed_runner_failure_without_retry(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output_path = root / "bundle.json"
            validation_path = root / "validation.json"
            self._write_json(output_path, make_valid_m3_bundle())
            completed_process = subprocess.CompletedProcess(
                args=[],
                returncode=1,
                stdout=json.dumps(VALID_RESULT, separators=(",", ":")) + "\n",
                stderr="unexpected diagnostic",
            )

            with mock.patch(
                "run_forward_validation_once.subprocess.run",
                return_value=completed_process,
            ) as run_mock:
                exit_code = main([str(output_path), str(validation_path)])

            self.assertNotEqual(exit_code, 0)
            run_mock.assert_called_once()
            receipt = json.loads(validation_path.read_text(encoding="utf-8"))
            self.assertEqual(receipt["runner_failure"], "validator_stderr_nonempty")
            self.assertNotIn("unexpected diagnostic", json.dumps(receipt))

    def test_multiline_stdout_writes_closed_runner_failure_without_retry(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output_path = root / "bundle.json"
            validation_path = root / "validation.json"
            self._write_json(output_path, make_valid_m3_bundle())
            completed_process = subprocess.CompletedProcess(
                args=[],
                returncode=0,
                stdout='{"status":"valid"}\n{"errors":[],"evidence_gaps":[]}\n',
                stderr="",
            )

            with mock.patch(
                "run_forward_validation_once.subprocess.run",
                return_value=completed_process,
            ) as run_mock:
                exit_code = main([str(output_path), str(validation_path)])

            self.assertNotEqual(exit_code, 0)
            run_mock.assert_called_once()
            self.assertEqual(
                json.loads(validation_path.read_text(encoding="utf-8"))["runner_failure"],
                "validator_stdout_not_single_line_json",
            )


if __name__ == "__main__":
    unittest.main()
