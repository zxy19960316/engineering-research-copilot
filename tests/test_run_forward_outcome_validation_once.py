from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER = REPO_ROOT / "evals" / "m3" / "run_forward_outcome_validation_once.py"
sys.path.insert(0, str(REPO_ROOT / "evals" / "m3"))
sys.path.insert(0, str(REPO_ROOT / "tests"))

from run_forward_outcome_validation_once import (  # noqa: E402
    VALIDATOR_PATH,
    main,
)
from test_validate_m3_method_bundle import make_valid_m3_bundle  # noqa: E402


ACCEPTED = {
    "case_id": "m3-f01",
    "status": "accepted",
    "outcome_kind": "bundle",
    "errors": [],
    "evidence_gaps": [],
    "method_bundle_validation": {
        "status": "valid",
        "errors": [],
        "evidence_gaps": [],
    },
}


class RunForwardOutcomeValidationOnceTests(unittest.TestCase):
    def _write_json(self, path: Path, value: object) -> None:
        path.write_text(
            json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n",
            encoding="utf-8",
            newline="\n",
        )

    def _inputs(self, root: Path) -> tuple[Path, Path, Path]:
        bundle = make_valid_m3_bundle()
        source_path = root / "source-m2.json"
        outcome_path = root / "outcome.json"
        receipt_path = root / "receipt.json"
        self._write_json(source_path, bundle["source_m2_bundle"])
        self._write_json(
            outcome_path,
            {"outcome_kind": "bundle", "bundle": bundle},
        )
        return source_path, outcome_path, receipt_path

    def test_records_exact_invocation_script_hash_stdout_hash_and_exit(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_path, outcome_path, receipt_path = self._inputs(root)
            stdout = (
                json.dumps(ACCEPTED, ensure_ascii=False, separators=(",", ":"))
                + "\n"
            ).encode("utf-8")
            completed = subprocess.CompletedProcess([], 0, stdout=stdout, stderr=b"")

            with mock.patch(
                "run_forward_outcome_validation_once.subprocess.run",
                return_value=completed,
            ) as run_mock:
                exit_code = main(
                    ["m3-f01", str(source_path), str(outcome_path), str(receipt_path)]
                )

            self.assertEqual(exit_code, 0)
            expected_command = [
                sys.executable,
                "-X",
                "utf8",
                str(VALIDATOR_PATH),
                "m3-f01",
                str(source_path),
                str(outcome_path),
            ]
            run_mock.assert_called_once_with(expected_command, capture_output=True)
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(receipt["validator_invocation_count"], 1)
            self.assertEqual(receipt["validator_argv"], expected_command)
            self.assertEqual(receipt["validator_exit_code"], 0)
            self.assertEqual(receipt["validator_stdout_sha256"], hashlib.sha256(stdout).hexdigest())
            self.assertEqual(
                receipt["validator_script_sha256"],
                hashlib.sha256(VALIDATOR_PATH.read_bytes()).hexdigest(),
            )
            self.assertEqual(receipt["validator_output"], ACCEPTED)

    def test_real_valid_bundle_receipt_is_utf8_no_bom_single_object(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_path, outcome_path, receipt_path = self._inputs(root)

            completed = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(RUNNER),
                    "m3-f01",
                    str(source_path),
                    str(outcome_path),
                    str(receipt_path),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            raw = receipt_path.read_bytes()
            self.assertFalse(raw.startswith(b"\xef\xbb\xbf"))
            self.assertEqual(raw.count(b"\n"), 1)
            self.assertEqual(json.loads(raw.decode("utf-8"))["validator_output"], ACCEPTED)

    def test_json_syntax_error_records_line_column_position_without_repair(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_path, outcome_path, receipt_path = self._inputs(root)
            raw = b'{"outcome_kind":"bundle","bundle" {}}\n'
            outcome_path.write_bytes(raw)

            completed = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(RUNNER),
                    "m3-f01",
                    str(source_path),
                    str(outcome_path),
                    str(receipt_path),
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

            self.assertEqual(completed.returncode, 1)
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            diagnostic = receipt["outcome_artifact"]
            self.assertEqual(diagnostic["raw_sha256"], hashlib.sha256(raw).hexdigest())
            self.assertEqual(diagnostic["utf8_status"], "valid")
            self.assertEqual(diagnostic["json_status"], "syntax_error")
            self.assertEqual(
                set(diagnostic["json_error"]), {"line", "column", "position"}
            )
            self.assertEqual(outcome_path.read_bytes(), raw)
            self.assertEqual(receipt["validator_invocation_count"], 1)

    def test_invalid_utf8_is_distinct_from_json_syntax(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_path, outcome_path, receipt_path = self._inputs(root)
            outcome_path.write_bytes(b"{\xff}\n")

            subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(RUNNER),
                    "m3-f01",
                    str(source_path),
                    str(outcome_path),
                    str(receipt_path),
                ],
                check=False,
            )

            diagnostic = json.loads(receipt_path.read_text(encoding="utf-8"))[
                "outcome_artifact"
            ]
            self.assertEqual(diagnostic["utf8_status"], "invalid")
            self.assertEqual(diagnostic["json_status"], "not_checked")
            self.assertNotIn("json_error", diagnostic)

    def test_fenced_json_is_not_stripped_or_extracted(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_path, outcome_path, receipt_path = self._inputs(root)
            raw = b'```json\n{"outcome_kind":"bundle"}\n```\n'
            outcome_path.write_bytes(raw)

            subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    str(RUNNER),
                    "m3-f01",
                    str(source_path),
                    str(outcome_path),
                    str(receipt_path),
                ],
                check=False,
            )

            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(receipt["outcome_artifact"]["json_status"], "syntax_error")
            self.assertEqual(outcome_path.read_bytes(), raw)

    def test_nonempty_stderr_and_bad_stdout_fail_closed_without_retry(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_path, outcome_path, receipt_path = self._inputs(root)
            completed = subprocess.CompletedProcess([], 1, stdout=b"not-json\n", stderr=b"secret")

            with mock.patch(
                "run_forward_outcome_validation_once.subprocess.run",
                return_value=completed,
            ) as run_mock:
                exit_code = main(
                    ["m3-f01", str(source_path), str(outcome_path), str(receipt_path)]
                )

            self.assertEqual(exit_code, 2)
            run_mock.assert_called_once()
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            self.assertEqual(receipt["runner_failure"], "validator_stderr_nonempty")
            self.assertNotIn("secret", json.dumps(receipt))
            self.assertEqual(receipt["validator_invocation_count"], 1)

    def test_existing_receipt_and_wrong_argument_count_never_invoke_validator(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_path, outcome_path, receipt_path = self._inputs(root)
            receipt_path.write_text("sentinel\n", encoding="utf-8")

            with mock.patch("run_forward_outcome_validation_once.subprocess.run") as run_mock:
                self.assertEqual(
                    main(["m3-f01", str(source_path), str(outcome_path), str(receipt_path)]),
                    2,
                )
                self.assertEqual(main(["m3-f01"]), 2)

            run_mock.assert_not_called()
            self.assertEqual(receipt_path.read_text(encoding="utf-8"), "sentinel\n")


if __name__ == "__main__":
    unittest.main()
