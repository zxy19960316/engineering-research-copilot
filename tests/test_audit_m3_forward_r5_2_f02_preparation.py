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

import audit_forward_r5_2_f02_preparation as audit  # noqa: E402


MANIFEST = (
    REPO_ROOT
    / "evals"
    / "m3"
    / "forward-inputs-r5.2-f02"
    / "manifest.json"
)


def _raw_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class AuditM3ForwardR52F02PreparationTests(unittest.TestCase):
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

    def _bind_artifact(
        self, manifest: dict, key: str, path: Path, *, canonical: bool = False
    ) -> None:
        reference = manifest["artifacts"][key]
        reference["path"] = path.relative_to(REPO_ROOT).as_posix()
        reference["raw_sha256"] = _raw_sha256(path)
        if canonical:
            value = json.loads(path.read_text(encoding="utf-8"))
            reference["canonical_sha256"] = audit.canonical_sha256(value)

    def test_accepts_frozen_preparation_without_writes_or_execution(self):
        before = {
            path.name: path.read_bytes() for path in audit.RESULT_ROOT.iterdir()
        }

        result = audit.audit_preparation(MANIFEST)

        after = {path.name: path.read_bytes() for path in audit.RESULT_ROOT.iterdir()}
        self.assertEqual(result["status"], "gate_2_preparation_valid")
        self.assertEqual(result["revision"], "r5.2-f02")
        self.assertFalse(result["new_fresh_run_authorized"])
        self.assertEqual(result["fresh_execution"], "NOT_RUN")
        self.assertEqual(result["logical_result_artifact_count"], 0)
        self.assertTrue(all(value == 0 for value in result["counters"].values()))
        self.assertEqual(result["prompt_lint_errors"], [])
        self.assertEqual(result["errors"], [])
        self.assertEqual(before, after)

    def test_rejects_authorization_task_identity_or_counter_drift(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            path = self._write_manifest(
                Path(temp_dir),
                lambda value: (
                    value.__setitem__("new_fresh_run_authorized", True),
                    value.__setitem__("reserved_task_id", "already-created"),
                    value["counters"].__setitem__("tasks", 1),
                ),
            )
            result = audit.audit_preparation(path)

        self.assertEqual(result["status"], "invalid")
        self.assertIn("fresh_run_authorization_must_be_false", result["errors"])
        self.assertIn("reserved_task_id_must_be_null", result["errors"])
        self.assertIn("manifest_counter_nonzero:tasks", result["errors"])

    def test_rejects_bound_artifact_hash_drift(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            path = self._write_manifest(
                Path(temp_dir),
                lambda value: value["artifacts"]["input_binding"].__setitem__(
                    "raw_sha256", "0" * 64
                ),
            )
            result = audit.audit_preparation(path)

        self.assertEqual(result["status"], "invalid")
        self.assertIn("input_binding_raw_sha256_mismatch", result["errors"])

    def test_rejects_prompt_contradiction_even_when_new_hash_is_bound(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            prompt = root / "prompt.txt"
            prompt.write_text(
                "This is the authorized r5.2-f02 execution.\n"
                "Execute the frozen task now.\n"
                "This is a future task.\n",
                encoding="utf-8",
                newline="\n",
            )

            def mutate(value: dict) -> None:
                self._bind_artifact(value, "prompt", prompt)

            path = self._write_manifest(root, mutate)
            result = audit.audit_preparation(path)

        self.assertEqual(result["status"], "invalid")
        self.assertIn(
            "prompt_lint:forbidden_prompt_phrase:future task", result["errors"]
        )

    def test_rejects_unexpected_result_artifact(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            result_root = root / "forward-r5.2-f02"
            result_root.mkdir()
            (result_root / ".gitkeep").write_bytes(b"")
            (result_root / "m3-f02.payload.json").write_bytes(b"{}\n")

            def mutate(value: dict) -> None:
                value["result_root"] = result_root.relative_to(REPO_ROOT).as_posix()

            path = self._write_manifest(root, mutate)
            with mock.patch.object(audit, "RESULT_ROOT", result_root):
                result = audit.audit_preparation(path)

        self.assertEqual(result["status"], "invalid")
        self.assertEqual(result["logical_result_artifact_count"], 1)
        self.assertIn("result_root_not_logically_empty", result["errors"])

    def test_rejects_gate_3_authorization_instance_during_gate_2(self):
        with mock.patch.object(
            audit, "_authorization_instance_absent", return_value=False
        ):
            result = audit.audit_preparation(MANIFEST)

        self.assertEqual(result["status"], "invalid")
        self.assertIn("execution_authorization_instance_present", result["errors"])

    def test_rejects_structured_output_surface_or_mode_drift(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            source = json.loads(
                (
                    REPO_ROOT
                    / "evals"
                    / "m3"
                    / "forward-inputs-r5.2-f02"
                    / "m3-f02.output-mode.json"
                ).read_text(encoding="utf-8")
            )
            source["decision"]["selected_mode"] = "native_structured_output"
            mode = root / "output-mode.json"
            mode.write_text(
                json.dumps(source, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
                newline="\n",
            )

            def mutate(value: dict) -> None:
                self._bind_artifact(value, "output_mode", mode, canonical=True)

            path = self._write_manifest(root, mutate)
            result = audit.audit_preparation(path)

        self.assertEqual(result["status"], "invalid")
        self.assertIn("output_mode_decision_invalid", result["errors"])

    def test_rejects_historical_r5_or_r5_1_tree_drift(self):
        with mock.patch.object(
            audit,
            "_historical_tree_clean",
            side_effect=[False, False],
        ):
            result = audit.audit_preparation(MANIFEST)

        self.assertEqual(result["status"], "invalid")
        self.assertIn("immutable_forward_r5_changed", result["errors"])
        self.assertIn("immutable_forward_r5_1_f02_changed", result["errors"])

    def test_rejects_regression_matrix_identity_drift(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            source = json.loads(
                (
                    REPO_ROOT
                    / "evals"
                    / "m3"
                    / "forward-inputs-r5.2-f02"
                    / "protocol-regression-cases.json"
                ).read_text(encoding="utf-8")
            )
            source["cases"].pop()
            cases = root / "cases.json"
            cases.write_text(
                json.dumps(source, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
                newline="\n",
            )

            def mutate(value: dict) -> None:
                self._bind_artifact(
                    value, "protocol_regression_cases", cases, canonical=True
                )

            path = self._write_manifest(root, mutate)
            result = audit.audit_preparation(path)

        self.assertEqual(result["status"], "invalid")
        self.assertIn("protocol_regression_case_set_invalid", result["errors"])


if __name__ == "__main__":
    unittest.main()
