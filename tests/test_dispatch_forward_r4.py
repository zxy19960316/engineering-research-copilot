from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "evals" / "m3"))

from dispatch_forward_r4 import dispatch_case, preflight_case  # noqa: E402


SOURCE = REPO_ROOT / "evals" / "m3" / "forward-inputs-r2" / "m3-f03-approved-change.bundle.json"


class DispatchForwardR4Tests(unittest.TestCase):
    def _sha256(self, path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def _write_manifest(self, root: Path, *, prompt_path: str | None = None) -> Path:
        prompt = root / "prompt.txt"
        prompt.write_text("closed prompt\n", encoding="utf-8", newline="\n")
        contract = root / "contract.json"
        contract.write_text('{"type":"object"}\n', encoding="utf-8", newline="\n")
        prompt_relative = prompt_path or prompt.relative_to(REPO_ROOT).as_posix()
        manifest = {
            "schema_version": "m3.1-forward-acceptance-r4-v1",
            "status": "ready_for_authorized_fresh_contexts",
            "prompts_frozen": True,
            "fresh_contexts_consumed": 0,
            "cases": [
                {
                    "case_id": "m3-f03",
                    "input_path": "evals/m3/forward-inputs-r2/m3-f03-approved-change.bundle.json",
                    "input_raw_sha256": self._sha256(SOURCE),
                    "prompt_path": prompt_relative,
                    "prompt_raw_sha256": self._sha256(prompt),
                    "contract_path": contract.relative_to(REPO_ROOT).as_posix(),
                    "contract_raw_sha256": self._sha256(contract),
                    "eligibility_status": "eligible",
                }
            ],
        }
        manifest_path = root / "manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        return manifest_path

    def _result_root(self, root: Path) -> Path:
        result_root = root / "forward-r4-results"
        result_root.mkdir()
        return result_root

    def test_f03_source_is_derived_from_manifest_not_cli_alias(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            manifest_path = self._write_manifest(root)
            result_root = self._result_root(root)

            with mock.patch("dispatch_forward_r4.R4_RESULT_ROOT", result_root):
                callback = mock.Mock(return_value={"accepted": False})
                result = dispatch_case(manifest_path, "m3-f03", callback)

            callback.assert_called_once()
            plan = callback.call_args.args[0]
            self.assertEqual(
                plan["source_input_path"],
                SOURCE.resolve(),
            )
            self.assertEqual(
                plan["source_input_relative_path"],
                "evals/m3/forward-inputs-r2/m3-f03-approved-change.bundle.json",
            )
            self.assertTrue(result["fresh_context_consumed"])

    def test_missing_source_blocks_without_consuming_or_mutating_manifest(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            manifest_path = self._write_manifest(root)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["cases"][0]["input_path"] = "tests/does-not-exist-r4-source.json"
            manifest_before = manifest_path.read_bytes()
            manifest_path.write_text(
                json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n",
                encoding="utf-8",
                newline="\n",
            )
            manifest_before = manifest_path.read_bytes()

            callback = mock.Mock()
            result = dispatch_case(manifest_path, "m3-f03", callback)

            callback.assert_not_called()
            self.assertFalse(result["fresh_context_consumed"])
            self.assertIn("source_input_missing", result["errors"])
            self.assertEqual(manifest_path.read_bytes(), manifest_before)

    def test_source_hash_mismatch_blocks_without_consuming(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            manifest_path = self._write_manifest(root)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["cases"][0]["input_raw_sha256"] = "0" * 64
            manifest_path.write_text(
                json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n",
                encoding="utf-8",
                newline="\n",
            )

            callback = mock.Mock()
            result = preflight_case(manifest_path, "m3-f03")

            callback.assert_not_called()
            self.assertEqual(result["status"], "blocked")
            self.assertFalse(result["fresh_context_consumed"])
            self.assertIn("source_input_raw_sha256_mismatch", result["errors"])

    def test_existing_output_blocks_without_consuming_or_writing_receipt(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            manifest_path = self._write_manifest(root)
            result_root = self._result_root(root)
            output_path = result_root / "m3-f03.outcome.json"
            output_path.write_text("sentinel\n", encoding="utf-8", newline="\n")
            manifest_before = manifest_path.read_bytes()

            with mock.patch("dispatch_forward_r4.R4_RESULT_ROOT", result_root):
                callback = mock.Mock()
                result = dispatch_case(manifest_path, "m3-f03", callback)

            callback.assert_not_called()
            self.assertFalse(result["fresh_context_consumed"])
            self.assertIn("future_output_exists", result["errors"])
            self.assertEqual(output_path.read_text(encoding="utf-8"), "sentinel\n")
            self.assertEqual(manifest_path.read_bytes(), manifest_before)

    def test_existing_receipt_blocks_without_consuming(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            manifest_path = self._write_manifest(root)
            result_root = self._result_root(root)
            receipt_path = result_root / "m3-f03.validator-receipt.json"
            receipt_path.write_text("sentinel\n", encoding="utf-8", newline="\n")

            with mock.patch("dispatch_forward_r4.R4_RESULT_ROOT", result_root):
                callback = mock.Mock()
                result = dispatch_case(manifest_path, "m3-f03", callback)

            callback.assert_not_called()
            self.assertFalse(result["fresh_context_consumed"])
            self.assertIn("future_receipt_exists", result["errors"])

    def test_prompt_missing_or_hash_mismatch_blocks_without_consuming(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            manifest_path = self._write_manifest(root)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["cases"][0]["prompt_raw_sha256"] = "f" * 64
            manifest_path.write_text(
                json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n",
                encoding="utf-8",
                newline="\n",
            )

            callback = mock.Mock()
            result = preflight_case(manifest_path, "m3-f03")

            callback.assert_not_called()
            self.assertFalse(result["fresh_context_consumed"])
            self.assertIn("prompt_raw_sha256_mismatch", result["errors"])

    def test_manifest_has_no_caller_source_argument_in_dispatch_api(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            manifest_path = self._write_manifest(root)
            with self.assertRaises(TypeError):
                dispatch_case(manifest_path, "m3-f03", mock.Mock(), SOURCE)


if __name__ == "__main__":
    unittest.main()
