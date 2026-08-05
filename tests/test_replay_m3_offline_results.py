from __future__ import annotations

import copy
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
M3_EVAL_DIR = REPO_ROOT / "evals" / "m3"
_REPLAY_SPEC = importlib.util.spec_from_file_location(
    "m3_replay_offline_results",
    M3_EVAL_DIR / "replay_offline_results.py",
)
if _REPLAY_SPEC is None or _REPLAY_SPEC.loader is None:
    raise RuntimeError("Unable to load the M3 replay module")
_REPLAY_MODULE = importlib.util.module_from_spec(_REPLAY_SPEC)
_REPLAY_SPEC.loader.exec_module(_REPLAY_MODULE)
evaluate = _REPLAY_MODULE.evaluate


class M3OfflineResultsReplayTests(unittest.TestCase):
    def _copy_replay_tree(self, temp_root: Path) -> tuple[Path, dict]:
        fixture_dir = temp_root / "fixtures"
        fixture_dir.mkdir()
        manifest = json.loads(
            (M3_EVAL_DIR / "adversarial-cases.json").read_text(encoding="utf-8")
        )
        for case in manifest["cases"]:
            case.setdefault("case_id", Path(case["fixture"]).stem)
            source = M3_EVAL_DIR / "fixtures" / case["fixture"]
            (fixture_dir / case["fixture"]).write_bytes(source.read_bytes())
        manifest_path = temp_root / "adversarial-cases.json"
        self._write_json(manifest_path, manifest)
        return manifest_path, manifest

    @staticmethod
    def _write_json(path: Path, payload: object) -> None:
        path.write_text(
            json.dumps(
                payload,
                sort_keys=True,
                indent=2,
                ensure_ascii=False,
                allow_nan=False,
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )

    def _assert_contract_rejected(self, manifest_path: Path) -> None:
        with self.assertRaisesRegex(ValueError, r"^invalid_replay_contract$"):
            evaluate(manifest_path)

    def _run_main(self, temp_root: Path, arguments: list[str]) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            mock.patch.object(_REPLAY_MODULE, "M3_DIR", temp_root),
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            exit_code = _REPLAY_MODULE.main(arguments)
        return exit_code, stdout.getvalue(), stderr.getvalue()

    def test_replay_matches_every_declared_fixture_and_frozen_record(self):
        manifest = M3_EVAL_DIR / "adversarial-cases.json"
        actual = evaluate(manifest)
        frozen = json.loads(
            (M3_EVAL_DIR / "offline-results.json").read_text(encoding="utf-8")
        )
        self.assertTrue(actual["all_matched"])
        self.assertEqual(actual, frozen)

    def test_replay_exposes_exact_expectation_mismatch(self):
        manifest = json.loads(
            (M3_EVAL_DIR / "adversarial-cases.json").read_text(encoding="utf-8")
        )
        changed = copy.deepcopy(manifest)
        changed["cases"][0]["expected_errors"] = ["invented_error"]
        with tempfile.TemporaryDirectory(dir=M3_EVAL_DIR) as directory:
            temp_root = Path(directory)
            temp_manifest = temp_root / "adversarial-cases.json"
            temp_fixture_dir = temp_root / "fixtures"
            temp_fixture_dir.mkdir()
            temp_manifest.write_text(
                json.dumps(changed),
                encoding="utf-8",
                newline="\n",
            )
            for case in changed["cases"]:
                source = M3_EVAL_DIR / "fixtures" / case["fixture"]
                (temp_fixture_dir / case["fixture"]).write_bytes(source.read_bytes())
            result = evaluate(temp_manifest)
        self.assertFalse(result["all_matched"])
        self.assertFalse(result["cases"][0]["matched"])

    def test_manifest_requires_at_least_one_case(self):
        with tempfile.TemporaryDirectory(dir=M3_EVAL_DIR) as directory:
            manifest_path, manifest = self._copy_replay_tree(Path(directory))
            manifest["cases"] = []
            self._write_json(manifest_path, manifest)
            self._assert_contract_rejected(manifest_path)

    def test_case_ids_and_fixture_declarations_must_be_unique(self):
        for duplicate_field in ("case_id", "fixture"):
            with self.subTest(duplicate_field=duplicate_field):
                with tempfile.TemporaryDirectory(dir=M3_EVAL_DIR) as directory:
                    manifest_path, manifest = self._copy_replay_tree(Path(directory))
                    manifest["cases"][1][duplicate_field] = manifest["cases"][0][
                        duplicate_field
                    ]
                    self._write_json(manifest_path, manifest)
                    self._assert_contract_rejected(manifest_path)

    def test_fixture_names_are_basename_only_json_files(self):
        with tempfile.TemporaryDirectory(dir=M3_EVAL_DIR) as directory:
            temp_root = Path(directory)
            manifest_path, original = self._copy_replay_tree(temp_root)
            invalid_names = (
                str((temp_root / "fixtures" / "valid-bounded.json").resolve()),
                "../adversarial-cases.json",
                "nested/valid-bounded.json",
                "valid-bounded.txt",
                "",
            )
            for fixture_name in invalid_names:
                with self.subTest(fixture_name=fixture_name):
                    manifest = copy.deepcopy(original)
                    manifest["cases"][0]["fixture"] = fixture_name
                    self._write_json(manifest_path, manifest)
                    self._assert_contract_rejected(manifest_path)

    def test_declared_fixture_set_must_match_directory_exactly(self):
        with tempfile.TemporaryDirectory(dir=M3_EVAL_DIR) as directory:
            temp_root = Path(directory)
            manifest_path, manifest = self._copy_replay_tree(temp_root)
            orphan = temp_root / "fixtures" / "orphan.json"
            orphan.write_text("{}\n", encoding="utf-8", newline="\n")
            self._assert_contract_rejected(manifest_path)
            orphan.unlink()
            (temp_root / "fixtures" / manifest["cases"][0]["fixture"]).unlink()
            self._assert_contract_rejected(manifest_path)

    def test_linked_fixture_root_is_rejected_before_external_fixture_read(self):
        with tempfile.TemporaryDirectory(dir=M3_EVAL_DIR) as directory:
            temp_root = Path(directory)
            manifest_root = temp_root / "manifest"
            manifest_root.mkdir()
            manifest_path, _ = self._copy_replay_tree(manifest_root)
            fixture_entry = manifest_root / "fixtures"
            external_fixture_dir = temp_root / "external-fixtures"
            fixture_entry.rename(external_fixture_dir)
            try:
                os.symlink(
                    external_fixture_dir,
                    fixture_entry,
                    target_is_directory=True,
                )
            except OSError as error:
                if os.name == "nt":
                    self.skipTest(f"directory symlink unavailable: {error.winerror}")
                raise

            loaded_paths: list[Path] = []
            real_load_json = _REPLAY_MODULE._load_json

            def tracked_load_json(path: Path) -> object:
                loaded_paths.append(path)
                return real_load_json(path)

            try:
                with mock.patch.object(
                    _REPLAY_MODULE,
                    "_load_json",
                    side_effect=tracked_load_json,
                ):
                    self._assert_contract_rejected(manifest_path)
                self.assertEqual(
                    [path.resolve() for path in loaded_paths],
                    [manifest_path.resolve()],
                )

                loaded_paths.clear()
                with mock.patch.object(
                    _REPLAY_MODULE,
                    "_load_json",
                    side_effect=tracked_load_json,
                ):
                    exit_code, stdout, stderr = self._run_main(manifest_root, [])
                self.assertEqual(exit_code, 1)
                self.assertEqual(stderr, "")
                self.assertEqual(
                    json.loads(stdout),
                    {"error": "invalid_replay_contract", "status": "invalid"},
                )
                self.assertEqual(
                    [path.resolve() for path in loaded_paths],
                    [manifest_path.resolve()],
                )
            finally:
                fixture_entry.unlink(missing_ok=True)

    def test_windows_reparse_attribute_marks_fixture_root_as_linked(self):
        reparse_metadata = mock.Mock(
            st_mode=0o040000,
            st_file_attributes=0x400,
        )
        with mock.patch.object(
            _REPLAY_MODULE.os,
            "lstat",
            return_value=reparse_metadata,
        ):
            self.assertTrue(
                _REPLAY_MODULE._fixture_root_is_linked(Path("fixtures"))
            )

    def test_manifest_and_case_objects_are_closed_and_typed(self):
        mutations = {
            "unknown_manifest_field": lambda manifest: manifest.update(
                {"unexpected": True}
            ),
            "missing_manifest_schema": lambda manifest: manifest.pop("schema_version"),
            "missing_manifest_evidence_class": lambda manifest: manifest.pop(
                "evidence_class"
            ),
            "missing_manifest_cases": lambda manifest: manifest.pop("cases"),
            "wrong_manifest_schema_type": lambda manifest: manifest.update(
                {"schema_version": 31}
            ),
            "wrong_manifest_evidence_class_type": lambda manifest: manifest.update(
                {"evidence_class": []}
            ),
            "wrong_cases_type": lambda manifest: manifest.update({"cases": {}}),
            "unknown_case_field": lambda manifest: manifest["cases"][0].update(
                {"unexpected": True}
            ),
            "missing_case_id": lambda manifest: manifest["cases"][0].pop("case_id"),
            "missing_case_fixture": lambda manifest: manifest["cases"][0].pop(
                "fixture"
            ),
            "missing_case_status": lambda manifest: manifest["cases"][0].pop(
                "expected_status"
            ),
            "missing_case_errors": lambda manifest: manifest["cases"][0].pop(
                "expected_errors"
            ),
            "missing_case_gaps": lambda manifest: manifest["cases"][0].pop(
                "expected_evidence_gaps"
            ),
            "wrong_case_id_type": lambda manifest: manifest["cases"][0].update(
                {"case_id": 1}
            ),
            "empty_case_id": lambda manifest: manifest["cases"][0].update(
                {"case_id": ""}
            ),
            "wrong_fixture_type": lambda manifest: manifest["cases"][0].update(
                {"fixture": 1}
            ),
            "wrong_status_value": lambda manifest: manifest["cases"][0].update(
                {"expected_status": "unknown"}
            ),
            "wrong_status_type": lambda manifest: manifest["cases"][0].update(
                {"expected_status": []}
            ),
            "wrong_errors_type": lambda manifest: manifest["cases"][0].update(
                {"expected_errors": "invalid_method_card"}
            ),
            "wrong_error_item_type": lambda manifest: manifest["cases"][0].update(
                {"expected_errors": [1]}
            ),
            "wrong_gaps_type": lambda manifest: manifest["cases"][0].update(
                {"expected_evidence_gaps": {}}
            ),
            "wrong_gap_item_type": lambda manifest: manifest["cases"][0].update(
                {"expected_evidence_gaps": [None]}
            ),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                with tempfile.TemporaryDirectory(dir=M3_EVAL_DIR) as directory:
                    manifest_path, manifest = self._copy_replay_tree(Path(directory))
                    mutate(manifest)
                    self._write_json(manifest_path, manifest)
                    self._assert_contract_rejected(manifest_path)

    def test_duplicate_json_keys_are_rejected_in_manifest_and_fixture(self):
        with tempfile.TemporaryDirectory(dir=M3_EVAL_DIR) as directory:
            temp_root = Path(directory)
            manifest_path, manifest = self._copy_replay_tree(temp_root)
            manifest_text = manifest_path.read_text(encoding="utf-8")
            duplicate = '  "schema_version": "m3.1-adversarial-cases"\n'
            manifest_path.write_text(
                manifest_text.replace(
                    duplicate,
                    duplicate.rstrip("\n") + ",\n" + duplicate,
                    1,
                ),
                encoding="utf-8",
                newline="\n",
            )
            self._assert_contract_rejected(manifest_path)

            self._write_json(manifest_path, manifest)
            fixture_path = temp_root / "fixtures" / manifest["cases"][0]["fixture"]
            fixture_text = fixture_path.read_text(encoding="utf-8")
            duplicate = '  "schema_version": "m3.1",\n'
            fixture_path.write_text(
                fixture_text.replace(duplicate, duplicate + duplicate, 1),
                encoding="utf-8",
                newline="\n",
            )
            self._assert_contract_rejected(manifest_path)

    def test_nonfinite_json_constants_are_rejected_in_manifest_and_fixture(self):
        for constant in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(location="manifest", constant=constant):
                with tempfile.TemporaryDirectory(dir=M3_EVAL_DIR) as directory:
                    manifest_path, _ = self._copy_replay_tree(Path(directory))
                    text = manifest_path.read_text(encoding="utf-8")
                    manifest_path.write_text(
                        text.replace(
                            '"schema_version": "m3.1-adversarial-cases"',
                            f'"schema_version": {constant}',
                            1,
                        ),
                        encoding="utf-8",
                        newline="\n",
                    )
                    self._assert_contract_rejected(manifest_path)
            with self.subTest(location="fixture", constant=constant):
                with tempfile.TemporaryDirectory(dir=M3_EVAL_DIR) as directory:
                    temp_root = Path(directory)
                    manifest_path, manifest = self._copy_replay_tree(temp_root)
                    fixture_path = (
                        temp_root / "fixtures" / manifest["cases"][0]["fixture"]
                    )
                    text = fixture_path.read_text(encoding="utf-8")
                    fixture_path.write_text(
                        text.replace("{\n", f'{{\n  "nonfinite": {constant},\n', 1),
                        encoding="utf-8",
                        newline="\n",
                    )
                    self._assert_contract_rejected(manifest_path)

    def test_record_refuses_mismatch_and_invalid_contract_without_overwrite(self):
        for failure_kind in ("mismatch", "invalid_contract"):
            with self.subTest(failure_kind=failure_kind):
                with tempfile.TemporaryDirectory(dir=M3_EVAL_DIR) as directory:
                    temp_root = Path(directory)
                    manifest_path, manifest = self._copy_replay_tree(temp_root)
                    if failure_kind == "mismatch":
                        manifest["cases"][0]["expected_errors"] = ["invented_error"]
                    else:
                        manifest["cases"] = []
                    self._write_json(manifest_path, manifest)
                    frozen_path = temp_root / "offline-results.json"
                    sentinel = b"preserve-existing-frozen-record\n"
                    frozen_path.write_bytes(sentinel)
                    before_sha256 = hashlib.sha256(sentinel).hexdigest()
                    exit_code, stdout, stderr = self._run_main(temp_root, ["--record"])
                    self.assertEqual(exit_code, 1)
                    self.assertEqual(stderr, "")
                    expected_output = (
                        {
                            "all_matched": False,
                            "case_count": 16,
                            "matched_frozen_record": False,
                            "status": "invalid",
                        }
                        if failure_kind == "mismatch"
                        else {
                            "error": "invalid_replay_contract",
                            "status": "invalid",
                        }
                    )
                    self.assertEqual(json.loads(stdout), expected_output)
                    self.assertEqual(frozen_path.read_bytes(), sentinel)
                    self.assertEqual(
                        hashlib.sha256(frozen_path.read_bytes()).hexdigest(),
                        before_sha256,
                    )

    def test_successful_record_is_atomic_canonical_and_leaves_no_temp_file(self):
        with tempfile.TemporaryDirectory(dir=M3_EVAL_DIR) as directory:
            temp_root = Path(directory)
            manifest_path, _ = self._copy_replay_tree(temp_root)
            frozen_path = temp_root / "offline-results.json"
            frozen_path.write_bytes(b"old-frozen-record\n")
            replace_calls: list[tuple[Path, Path]] = []
            real_replace = os.replace

            def tracked_replace(source: str | Path, target: str | Path) -> None:
                replace_calls.append((Path(source), Path(target)))
                real_replace(source, target)

            with mock.patch.object(
                _REPLAY_MODULE.os,
                "replace",
                side_effect=tracked_replace,
            ):
                exit_code, stdout, stderr = self._run_main(temp_root, ["--record"])
            self.assertEqual(exit_code, 0)
            self.assertEqual(stderr, "")
            self.assertEqual(json.loads(stdout)["status"], "valid")
            self.assertEqual(len(replace_calls), 1)
            temp_path, target_path = replace_calls[0]
            self.assertEqual(temp_path.parent, temp_root)
            self.assertEqual(target_path, frozen_path)
            expected = (
                json.dumps(
                    evaluate(manifest_path),
                    sort_keys=True,
                    indent=2,
                    ensure_ascii=False,
                    allow_nan=False,
                )
                + "\n"
            ).encode("utf-8")
            self.assertEqual(frozen_path.read_bytes(), expected)
            self.assertFalse(temp_path.exists())

    def test_failed_atomic_replace_preserves_record_and_cleans_temp_file(self):
        with tempfile.TemporaryDirectory(dir=M3_EVAL_DIR) as directory:
            temp_root = Path(directory)
            self._copy_replay_tree(temp_root)
            frozen_path = temp_root / "offline-results.json"
            sentinel = b"preserve-on-replace-failure\n"
            frozen_path.write_bytes(sentinel)
            with mock.patch.object(
                _REPLAY_MODULE.os,
                "replace",
                side_effect=OSError("simulated replace failure"),
            ):
                exit_code, stdout, stderr = self._run_main(temp_root, ["--record"])
            self.assertEqual(exit_code, 1)
            self.assertEqual(stderr, "")
            self.assertEqual(
                json.loads(stdout),
                {"error": "record_write_failed", "status": "invalid"},
            )
            self.assertEqual(frozen_path.read_bytes(), sentinel)
            self.assertEqual(
                sorted(path.name for path in temp_root.iterdir()),
                ["adversarial-cases.json", "fixtures", "offline-results.json"],
            )

    def test_fixture_builder_is_byte_deterministic(self):
        manifest = M3_EVAL_DIR / "adversarial-cases.json"
        fixture_dir = M3_EVAL_DIR / "fixtures"
        paths = [manifest, *sorted(fixture_dir.glob("*.json"))]
        before = {
            path.relative_to(M3_EVAL_DIR).as_posix(): path.read_bytes()
            for path in paths
        }
        completed = subprocess.run(
            [sys.executable, "-X", "utf8", str(M3_EVAL_DIR / "build_fixtures.py")],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        after_paths = [manifest, *sorted(fixture_dir.glob("*.json"))]
        after = {
            path.relative_to(M3_EVAL_DIR).as_posix(): path.read_bytes()
            for path in after_paths
        }
        self.assertEqual(after, before)
        self.assertEqual(len(after) - 1, 16)


if __name__ == "__main__":
    unittest.main()
