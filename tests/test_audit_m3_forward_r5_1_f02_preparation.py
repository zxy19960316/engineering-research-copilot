from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "evals" / "m3"))

import audit_forward_r5_1_f02_preparation as audit  # noqa: E402


MANIFEST = (
    REPO_ROOT
    / "evals"
    / "m3"
    / "forward-inputs-r5.1-f02"
    / "manifest.json"
)


class AuditM3ForwardR51F02PreparationTests(unittest.TestCase):
    def _write_manifest(self, root: Path, mutate) -> Path:
        value = json.loads(MANIFEST.read_text(encoding="utf-8"))
        mutate(value)
        path = root / "manifest.json"
        path.write_text(
            json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
        return path

    def test_accepts_frozen_one_case_preparation_without_side_effects(self):
        before = {path.name: path.read_bytes() for path in audit.RESULT_ROOT.iterdir()}
        with (
            mock.patch.object(audit, "_check_result_root", return_value=0),
            mock.patch.object(audit, "validate_future_paths", return_value=[]),
        ):
            result = audit.audit_preparation(MANIFEST)
        after = {path.name: path.read_bytes() for path in audit.RESULT_ROOT.iterdir()}

        self.assertEqual(result["status"], "ready_for_fresh_authorization")
        self.assertEqual(result["case_id"], "m3-f02")
        self.assertEqual(result["revision"], "r5.1-f02")
        self.assertFalse(result["new_fresh_run_authorized"])
        self.assertEqual(result["result_artifact_count"], 0)
        self.assertTrue(all(value == 0 for value in result["counters"].values()))
        self.assertEqual(result["errors"], [])
        self.assertEqual(before, after)

    def test_rejects_authorization_or_counter_drift(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            path = self._write_manifest(
                Path(temp_dir),
                lambda value: (
                    value.__setitem__("new_fresh_run_authorized", True),
                    value["counters"].__setitem__("tasks_launched", 1),
                ),
            )
            result = audit.audit_preparation(path)

        self.assertEqual(result["status"], "invalid")
        self.assertIn("fresh_run_authorization_must_be_false", result["errors"])
        self.assertIn("manifest_counter_nonzero:tasks_launched", result["errors"])

    def test_rejects_input_binding_hash_drift(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            path = self._write_manifest(
                Path(temp_dir),
                lambda value: value["input_binding"].__setitem__("raw_sha256", "0" * 64),
            )
            result = audit.audit_preparation(path)

        self.assertEqual(result["status"], "invalid")
        self.assertIn("input_binding_sha256_mismatch", result["errors"])

    def test_rejects_historical_task_or_result_root_reuse(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            path = self._write_manifest(
                Path(temp_dir),
                lambda value: (
                    value.__setitem__(
                        "result_root", "evals/m3/results/forward-r5"
                    ),
                    value.__setitem__(
                        "reserved_task_id", "019fd687-5575-7143-8cf3-1ab3069611f5"
                    ),
                ),
            )
            result = audit.audit_preparation(path)

        self.assertEqual(result["status"], "invalid")
        self.assertIn("result_root_not_canonical", result["errors"])
        self.assertIn("historical_task_id_reuse_forbidden", result["errors"])

    def test_rejects_result_artifacts_but_allows_only_gitkeep(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            result_root = root / "forward-r5.1-f02"
            result_root.mkdir()
            (result_root / ".gitkeep").write_bytes(b"")
            (result_root / "m3-f02.model-final.json").write_text(
                "{}\n", encoding="utf-8", newline="\n"
            )

            def mutate(value: dict) -> None:
                value["result_root"] = result_root.relative_to(REPO_ROOT).as_posix()

            path = self._write_manifest(root, mutate)
            with mock.patch.object(audit, "RESULT_ROOT", result_root):
                result = audit.audit_preparation(path)

        self.assertEqual(result["status"], "invalid")
        self.assertEqual(result["result_artifact_count"], 1)
        self.assertIn("result_root_not_empty", result["errors"])

    def test_rejects_immutable_r5_evidence_tree_drift(self):
        with mock.patch.object(audit, "_r5_evidence_tree_clean", return_value=False):
            result = audit.audit_preparation(MANIFEST)

        self.assertEqual(result["status"], "invalid")
        self.assertIn("immutable_r5_evidence_changed", result["errors"])


if __name__ == "__main__":
    unittest.main()
