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

import dispatch_forward_r5 as dispatcher  # noqa: E402
from r5_dispatch_contract import (  # noqa: E402
    CASE_IDS,
    COUNTER_KEYS,
    R5_SCHEMA_VERSION,
    canonical_future_paths,
)


SOURCE = REPO_ROOT / "evals" / "m3" / "forward-inputs-r2" / "m3-f03-approved-change.bundle.json"


class DispatchForwardR5Tests(unittest.TestCase):
    def _sha256(self, path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def _write_json(self, path: Path, value: object) -> None:
        path.write_text(
            json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
            newline="\n",
        )

    def _manifest(self, root: Path) -> tuple[Path, Path]:
        result_root = root / "forward-r5"
        result_root.mkdir()
        prompt = root / "prompt.txt"
        prompt.write_text("frozen prompt\n", encoding="utf-8", newline="\n")
        contract = root / "contract.json"
        self._write_json(contract, {"type": "object", "additionalProperties": False})
        validation = root / "m2-validation.json"
        self._write_json(validation, {"status": "valid", "errors": [], "evidence_gaps": []})
        eligibility = root / "eligibility.json"
        self._write_json(eligibility, {"status": "eligible", "errors": [], "evidence_gaps": []})
        cases = []
        for case_id in CASE_IDS:
            cases.append(
                {
                    "case_id": case_id,
                    "input_path": "evals/m3/forward-inputs-r2/m3-f03-approved-change.bundle.json",
                    "input_raw_sha256": self._sha256(SOURCE),
                    "prompt_path": prompt.relative_to(REPO_ROOT).as_posix(),
                    "prompt_raw_sha256": self._sha256(prompt),
                    "contract_path": contract.relative_to(REPO_ROOT).as_posix(),
                    "contract_raw_sha256": self._sha256(contract),
                    "m2_validation_path": validation.relative_to(REPO_ROOT).as_posix(),
                    "m2_validation_raw_sha256": self._sha256(validation),
                    "eligibility_path": eligibility.relative_to(REPO_ROOT).as_posix(),
                    "eligibility_raw_sha256": self._sha256(eligibility),
                    "eligibility_status": "eligible",
                    "future_paths": canonical_future_paths(case_id, result_root),
                }
            )
        manifest = {
            "schema_version": R5_SCHEMA_VERSION,
            "status": "ready_for_authorized_fresh_contexts",
            "prompts_frozen": True,
            "result_root": result_root.relative_to(REPO_ROOT).as_posix(),
            "counters": {key: 0 for key in COUNTER_KEYS},
            "cases": cases,
        }
        manifest_path = root / "acceptance-manifest.json"
        self._write_json(manifest_path, manifest)
        return manifest_path, result_root

    def test_missing_validator_receipt_blocks_before_callback_or_side_effects(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            manifest_path, result_root = self._manifest(root)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            f01 = manifest["cases"][0]
            f01["future_paths"].pop("validator_receipt_json")
            before_manifest = manifest_path.read_bytes()
            self._write_json(manifest_path, manifest)
            before_manifest = manifest_path.read_bytes()
            callback = mock.Mock()

            with mock.patch.object(dispatcher, "R5_RESULT_ROOT", result_root):
                result = dispatcher.dispatch_batch(manifest_path, callback)

            callback.assert_not_called()
            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["callback_invocations"], 0)
            self.assertIn("future_path_keys_missing:validator_receipt_json", result["errors"])
            self.assertEqual(manifest_path.read_bytes(), before_manifest)
            self.assertEqual(list(result_root.iterdir()), [])

    def test_invalid_later_case_blocks_all_five_consumptions(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            manifest_path, result_root = self._manifest(root)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["cases"][-1]["future_paths"]["validator_receipt_json"] = "../escape.json"
            self._write_json(manifest_path, manifest)
            callback = mock.Mock()
            with (
                mock.patch.object(dispatcher, "R5_RESULT_ROOT", result_root),
                mock.patch.object(
                    dispatcher,
                    "_preflight_case",
                    wraps=dispatcher._preflight_case,
                ) as preflight_mock,
            ):
                result = dispatcher.dispatch_batch(manifest_path, callback)

            self.assertEqual(preflight_mock.call_count, 5)
            callback.assert_not_called()
            self.assertEqual(result["callback_invocations"], 0)
            self.assertIn("future_path_unsafe:validator_receipt_json", result["errors"])

    def test_batch_dry_preflight_runs_all_cases_before_consumption(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            manifest_path, result_root = self._manifest(root)
            callback = mock.Mock()

            with (
                mock.patch.object(dispatcher, "R5_RESULT_ROOT", result_root),
                mock.patch.object(
                    dispatcher,
                    "_preflight_case",
                    wraps=dispatcher._preflight_case,
                ) as preflight_mock,
            ):
                result = dispatcher.preflight_batch(manifest_path)

            self.assertEqual(result["status"], "ready")
            self.assertEqual(preflight_mock.call_count, 5)
            self.assertEqual(len(result["plans"]), 5)

    def test_f03_resolves_exact_frozen_r2_input_path(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            manifest_path, result_root = self._manifest(root)

            with mock.patch.object(dispatcher, "R5_RESULT_ROOT", result_root):
                result = dispatcher.preflight_case(manifest_path, "m3-f03")

            self.assertEqual(result["status"], "ready")
            self.assertEqual(
                result["plan"]["source_input_relative_path"],
                "evals/m3/forward-inputs-r2/m3-f03-approved-change.bundle.json",
            )
            self.assertEqual(result["plan"]["source_input_path"], SOURCE.resolve())

    def test_future_paths_are_unique_and_below_r5_root(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            manifest_path, result_root = self._manifest(root)

            with mock.patch.object(dispatcher, "R5_RESULT_ROOT", result_root):
                result = dispatcher.preflight_batch(manifest_path)

            self.assertEqual(result["status"], "ready")
            all_paths = []
            for plan in result["plans"]:
                for raw in plan["future_paths"].values():
                    if raw is None:
                        continue
                    candidate = (result_root / raw).resolve()
                    candidate.relative_to(result_root.resolve())
                    all_paths.append(candidate)
            self.assertEqual(len(all_paths), len(set(all_paths)))

    def test_existing_output_or_receipt_blocks_without_overwrite(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            manifest_path, result_root = self._manifest(root)
            output = result_root / "m3-f03.outcome.json"
            receipt = result_root / "m3-f03.validator-receipt.json"
            output.write_text("output sentinel\n", encoding="utf-8", newline="\n")
            receipt.write_text("receipt sentinel\n", encoding="utf-8", newline="\n")
            callback = mock.Mock()

            with mock.patch.object(dispatcher, "R5_RESULT_ROOT", result_root):
                result = dispatcher.dispatch_batch(manifest_path, callback)

            callback.assert_not_called()
            self.assertIn("future_path_exists:outcome_json", result["errors"])
            self.assertIn("future_path_exists:validator_receipt_json", result["errors"])
            self.assertEqual(output.read_text(encoding="utf-8"), "output sentinel\n")
            self.assertEqual(receipt.read_text(encoding="utf-8"), "receipt sentinel\n")

    def test_callback_cannot_be_invoked_twice_for_one_case(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            manifest_path, result_root = self._manifest(root)
            calls: list[str] = []

            def callback(plan: dict) -> None:
                calls.append(plan["case_id"])

            with mock.patch.object(dispatcher, "R5_RESULT_ROOT", result_root):
                result = dispatcher.dispatch_batch(manifest_path, callback)

            self.assertEqual(result["status"], "dispatched")
            self.assertEqual(calls, list(CASE_IDS))
            self.assertEqual(len(calls), len(set(calls)))
            self.assertEqual(result["callback_invocations"], 5)

    def test_manifest_has_no_caller_source_or_receipt_arguments(self):
        with self.assertRaises(TypeError):
            dispatcher.dispatch_batch(Path("manifest.json"), mock.Mock(), SOURCE)


if __name__ == "__main__":
    unittest.main()
