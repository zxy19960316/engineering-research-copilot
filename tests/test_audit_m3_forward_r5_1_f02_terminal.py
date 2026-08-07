from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "evals" / "m3"))

import audit_forward_r5_1_f02_terminal as audit  # noqa: E402


class AuditM3ForwardR51F02TerminalTests(unittest.TestCase):
    def _manifest(self) -> dict:
        return json.loads(audit.TERMINAL_MANIFEST.read_text(encoding="utf-8"))

    def _write_json(self, path: Path, value: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            + "\n",
            encoding="utf-8",
            newline="\n",
        )

    def _copy_terminal_tree(self, root: Path) -> Path:
        manifest = self._manifest()
        for binding in manifest["artifacts"].values():
            relative = Path(binding["path"])
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO_ROOT / relative, target)
        marker = REPO_ROOT / audit.RESULT_ROOT_RELATIVE / ".gitkeep"
        if marker.exists():
            target = root / audit.RESULT_ROOT_RELATIVE / marker.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(marker, target)
        manifest_path = root / audit.TERMINAL_MANIFEST_RELATIVE
        self._write_json(manifest_path, manifest)
        return manifest_path

    def _mutate_bound_json(self, root: Path, key: str, mutate) -> None:
        manifest = json.loads(
            (root / audit.TERMINAL_MANIFEST_RELATIVE).read_text(encoding="utf-8")
        )
        path = root / manifest["artifacts"][key]["path"]
        value = json.loads(path.read_text(encoding="utf-8"))
        mutate(value)
        self._write_json(path, value)

    def _audit_copy(self, mutate=None, *, historical_check=None) -> dict:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            manifest_path = self._copy_terminal_tree(root)
            if mutate is not None:
                mutate(root)
            return audit.audit_terminal(
                manifest_path,
                artifact_root=root,
                git_root=REPO_ROOT,
                historical_check=historical_check,
            )

    def test_current_terminal_failure_is_valid(self):
        result = audit.audit_terminal(audit.TERMINAL_MANIFEST)
        self.assertEqual(result["status"], "terminal_not_accepted")
        self.assertEqual(result["case_id"], "m3-f02")
        self.assertEqual(result["revision"], "r5.1-f02")
        self.assertIs(result["accepted"], False)
        self.assertEqual(result["transaction_state"], "processing_failed")
        self.assertEqual(result["failure_stage"], "composition")
        self.assertEqual(result["failure_code"], "payload_invalid_json")
        self.assertEqual(result["tasks_launched"], 1)
        self.assertEqual(result["task_finalizations_observed"], 1)
        self.assertEqual(result["composer_invocations"], 1)
        self.assertEqual(result["validator_invocations"], 0)
        self.assertEqual(result["retry_count"], 0)
        self.assertEqual(result["historical_f02_retry_count"], 0)
        self.assertIs(result["historical_r5_unchanged"], True)
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["evidence_gaps"], [])
        self.assertEqual(result["side_effects"], [])
        self.assertEqual(result["later_gates"], "NOT_RUN")

    def test_manifest_accepted_true_is_invalid(self):
        def mutate(root: Path) -> None:
            path = root / audit.TERMINAL_MANIFEST_RELATIVE
            value = json.loads(path.read_text(encoding="utf-8"))
            value["accepted"] = True
            self._write_json(path, value)

        result = self._audit_copy(mutate)
        self.assertIn("terminal_manifest_field_invalid:accepted", result["errors"])

    def test_transaction_accepted_true_is_invalid(self):
        result = self._audit_copy(
            lambda root: self._mutate_bound_json(
                root, "transaction", lambda value: value.__setitem__("accepted", True)
            )
        )
        self.assertIn("transaction_accepted_invalid", result["errors"])

    def test_processing_state_drift_is_invalid(self):
        result = self._audit_copy(
            lambda root: self._mutate_bound_json(
                root,
                "transaction",
                lambda value: value.__setitem__("state", "processed_accepted"),
            )
        )
        self.assertIn("transaction_state_invalid", result["errors"])

    def test_failure_stage_drift_is_invalid(self):
        result = self._audit_copy(
            lambda root: self._mutate_bound_json(
                root,
                "composer_receipt",
                lambda value: value.__setitem__("failure_stage", "validation"),
            )
        )
        self.assertIn("composer_failure_stage_invalid", result["errors"])

    def test_failure_code_drift_is_invalid(self):
        result = self._audit_copy(
            lambda root: self._mutate_bound_json(
                root,
                "composer_receipt",
                lambda value: value.__setitem__("failure_code", "different_failure"),
            )
        )
        self.assertIn("composer_failure_code_invalid", result["errors"])

    def test_payload_made_parseable_is_invalid(self):
        def mutate(root: Path) -> None:
            manifest = self._manifest()
            path = root / manifest["artifacts"]["payload"]["path"]
            path.write_bytes(b"{}\n")

        result = self._audit_copy(mutate)
        self.assertIn("terminal_payload_failure_not_reproducible", result["errors"])

    def test_payload_manifest_raw_hash_drift_is_invalid(self):
        def mutate(root: Path) -> None:
            path = root / audit.TERMINAL_MANIFEST_RELATIVE
            value = json.loads(path.read_text(encoding="utf-8"))
            value["artifacts"]["payload"]["raw_sha256"] = "0" * 64
            self._write_json(path, value)

        result = self._audit_copy(mutate)
        self.assertIn("artifact_manifest_raw_sha256_mismatch:payload", result["errors"])

    def test_model_final_payload_bytes_mismatch_is_invalid(self):
        def mutate(root: Path) -> None:
            manifest = self._manifest()
            path = root / manifest["artifacts"]["payload"]["path"]
            path.write_bytes(b"not-json-but-different")

        result = self._audit_copy(mutate)
        self.assertIn("model_final_payload_bytes_mismatch", result["errors"])

    def test_composer_receipt_count_drift_is_invalid(self):
        result = self._audit_copy(
            lambda root: self._mutate_bound_json(
                root,
                "composer_receipt",
                lambda value: value.__setitem__("composer_invocation_count", 2),
            )
        )
        self.assertIn("composer_invocation_count_invalid", result["errors"])

    def test_transaction_composer_count_drift_is_invalid(self):
        result = self._audit_copy(
            lambda root: self._mutate_bound_json(
                root,
                "transaction",
                lambda value: value.__setitem__("composer_invocations", 2),
            )
        )
        self.assertIn("composer_invocation_count_invalid", result["errors"])

    def test_validator_count_drift_is_invalid(self):
        result = self._audit_copy(
            lambda root: self._mutate_bound_json(
                root,
                "transaction",
                lambda value: value.__setitem__("validator_invocations", 1),
            )
        )
        self.assertIn("validator_invocation_count_invalid", result["errors"])

    def test_retry_count_drift_is_invalid(self):
        result = self._audit_copy(
            lambda root: self._mutate_bound_json(
                root,
                "composer_receipt",
                lambda value: value.__setitem__("retry_count", 1),
            )
        )
        self.assertIn("retry_count_invalid", result["errors"])

    def test_second_task_evidence_is_invalid(self):
        def mutate(root: Path) -> None:
            path = root / audit.RESULT_ROOT_RELATIVE / "m3-f02.second-task.json"
            path.write_text("{}\n", encoding="utf-8", newline="\n")

        result = self._audit_copy(mutate)
        self.assertIn(
            "unexpected_result_artifact:m3-f02.second-task.json", result["errors"]
        )

    def test_second_finalization_evidence_is_invalid(self):
        def mutate(root: Path) -> None:
            path = root / audit.RESULT_ROOT_RELATIVE / "m3-f02.second-final.json"
            path.write_text("{}\n", encoding="utf-8", newline="\n")

        result = self._audit_copy(mutate)
        self.assertIn(
            "unexpected_result_artifact:m3-f02.second-final.json", result["errors"]
        )

    def test_unexpected_bundle_is_invalid(self):
        def mutate(root: Path) -> None:
            path = root / audit.RESULT_ROOT_RELATIVE / "m3-f02.bundle.json"
            path.write_text("{}\n", encoding="utf-8", newline="\n")

        result = self._audit_copy(mutate)
        self.assertIn("forbidden_result_artifact:m3-f02.bundle.json", result["errors"])

    def test_unexpected_validation_receipt_is_invalid(self):
        def mutate(root: Path) -> None:
            path = root / audit.RESULT_ROOT_RELATIVE / "m3-f02.validation.json"
            path.write_text("{}\n", encoding="utf-8", newline="\n")

        result = self._audit_copy(mutate)
        self.assertIn(
            "forbidden_result_artifact:m3-f02.validation.json", result["errors"]
        )

    def test_task_id_mismatch_is_invalid(self):
        for key in ("launch_receipt", "context", "transaction"):
            with self.subTest(key=key):
                field = "fresh_task_id" if key == "launch_receipt" else "task_id"
                result = self._audit_copy(
                    lambda root, key=key, field=field: self._mutate_bound_json(
                        root,
                        key,
                        lambda value, field=field: value.__setitem__(field, "different-task"),
                    )
                )
                self.assertIn("task_id_mismatch", result["errors"])

    def test_historical_task_id_reuse_is_invalid(self):
        result = self._audit_copy(
            lambda root: self._mutate_bound_json(
                root,
                "launch_receipt",
                lambda value: value.__setitem__(
                    "fresh_task_id", audit.HISTORICAL_TASK_ID
                ),
            )
        )
        self.assertIn("historical_task_id_reuse_forbidden", result["errors"])

    def test_historical_forward_r5_drift_is_invalid(self):
        result = self._audit_copy(historical_check=lambda: False)
        self.assertIn("historical_r5_changed", result["errors"])

    def test_execution_authorization_drift_is_invalid(self):
        result = self._audit_copy(
            lambda root: self._mutate_bound_json(
                root,
                "execution_authorization",
                lambda value: value.__setitem__("status", "drift"),
            )
        )
        self.assertIn(
            "artifact_worktree_drift:execution_authorization", result["errors"]
        )

    def test_prompt_drift_is_invalid(self):
        def mutate(root: Path) -> None:
            manifest = self._manifest()
            path = root / manifest["artifacts"]["prompt"]["path"]
            path.write_bytes(path.read_bytes() + b"drift")

        result = self._audit_copy(mutate)
        self.assertIn("artifact_worktree_drift:prompt", result["errors"])

    def test_source_input_drift_is_invalid(self):
        result = self._audit_copy(
            lambda root: self._mutate_bound_json(
                root,
                "source_input",
                lambda value: value.__setitem__("schema_version", "drift"),
            )
        )
        self.assertIn("artifact_worktree_drift:source_input", result["errors"])

    def test_missing_composer_receipt_is_invalid(self):
        def mutate(root: Path) -> None:
            manifest = self._manifest()
            (root / manifest["artifacts"]["composer_receipt"]["path"]).unlink()

        result = self._audit_copy(mutate)
        self.assertIn("missing_required_artifact:composer_receipt", result["errors"])

    def test_missing_transaction_is_invalid(self):
        def mutate(root: Path) -> None:
            manifest = self._manifest()
            (root / manifest["artifacts"]["transaction"]["path"]).unlink()

        result = self._audit_copy(mutate)
        self.assertIn("missing_required_artifact:transaction", result["errors"])

    def test_transaction_failure_inconsistent_with_composer_is_invalid(self):
        result = self._audit_copy(
            lambda root: self._mutate_bound_json(
                root,
                "transaction",
                lambda value: value.__setitem__("transaction_failures", ["different"]),
            )
        )
        self.assertIn("transaction_failure_inconsistent", result["errors"])

    def test_manifest_retry_permission_drift_is_invalid(self):
        def mutate(root: Path) -> None:
            path = root / audit.TERMINAL_MANIFEST_RELATIVE
            value = json.loads(path.read_text(encoding="utf-8"))
            value["retry_allowed"] = True
            self._write_json(path, value)

        result = self._audit_copy(mutate)
        self.assertIn("terminal_manifest_field_invalid:retry_allowed", result["errors"])

    def test_auditor_has_zero_side_effects(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            root = Path(temp_dir)
            manifest_path = self._copy_terminal_tree(root)
            before = {
                path.relative_to(root).as_posix(): path.read_bytes()
                for path in root.rglob("*")
                if path.is_file()
            }
            result = audit.audit_terminal(
                manifest_path, artifact_root=root, git_root=REPO_ROOT
            )
            after = {
                path.relative_to(root).as_posix(): path.read_bytes()
                for path in root.rglob("*")
                if path.is_file()
            }
        self.assertEqual(after, before)
        self.assertEqual(result["side_effects"], [])

    def test_repeated_auditor_invocation_is_identical(self):
        first = audit.audit_terminal(audit.TERMINAL_MANIFEST)
        second = audit.audit_terminal(audit.TERMINAL_MANIFEST)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
