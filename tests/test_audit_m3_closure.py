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

import audit_m3_closure as audit  # noqa: E402


CANDIDATE_HEAD = "a" * 40
CANDIDATE_RUN = 31_200_000_001


class AuditM3ClosureTests(unittest.TestCase):
    def _write_json(self, path: Path, value: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
            newline="\n",
        )

    def _artifact_ref(self, path: str) -> dict:
        return {
            "path": path,
            "source_head": CANDIDATE_HEAD,
            "git_blob_oid": "b" * 40,
            "byte_length": 2,
            "raw_sha256": "c" * 64,
            "json_status": "valid",
            "canonical_sha256": "d" * 64,
        }

    def _aggregate_result(self) -> dict:
        return {
            "status": "accepted",
            "selected_cases": [],
            "selected_counters": {},
            "historical_counters": {},
            "excluded_attempts": [],
            "historical_diffs": [],
            "errors": [],
            "evidence_gaps": [],
            "side_effects": [],
            "m3_status": "IN_PROGRESS",
            "m4_status": "NOT_STARTED",
        }

    def _closure(self) -> dict:
        return {
            "schema_version": "m3.1-cross-revision-closure-v1",
            "milestone": "M3",
            "status": "CLOSED",
            "result_root": audit.RESULT_ROOT,
            "result_root_allowlist": audit.RESULT_ROOT_ALLOWLIST,
            "aggregate_status": "accepted",
            "aggregate_candidate": {
                "head_sha": CANDIDATE_HEAD,
                "workflow": audit.WORKFLOW_PATH,
                "run_id": CANDIDATE_RUN,
            },
            "aggregate_candidate_ci": {
                "head_sha": CANDIDATE_HEAD,
                "workflow": audit.WORKFLOW_PATH,
                "run_id": CANDIDATE_RUN,
                "status": "completed",
                "conclusion": "success",
                "jobs": {"validate": "success", "ubuntu": "success", "windows": "success"},
            },
            "artifacts": {
                name: self._artifact_ref(path) for name, path in audit.ARTIFACT_PATHS.items()
            },
            "required_gates": {name: True for name in audit.REQUIRED_GATE_KEYS},
            "historical_diffs": {name: [] for name in audit.HISTORICAL_DIFF_KEYS},
            "worktree": {"before_closure_edits": "clean", "unexpected_artifacts": []},
            "m4_status": "NOT_STARTED",
            "scope_limits": {
                "fresh_execution_authorized": False,
                "retry_authorized": False,
                "same_task_retry_authorized": False,
                "repair_authorized": False,
                "m4_started": False,
                "m4_execution_authorized": False,
                "empirical_claim": False,
            },
            "side_effects": [],
            "does_not_prove": audit.DOES_NOT_PROVE,
        }

    def _fixture(self, root: Path, closure: dict) -> tuple[Path, dict[str, dict]]:
        result_root = root / audit.RESULT_ROOT
        result_root.mkdir(parents=True)
        aggregate_manifest = {"schema_version": "synthetic-aggregate-v1"}
        aggregate_result = self._aggregate_result()
        final_validation = {"schema_version": "synthetic-final-validation-v1", "status": "passed", "errors": []}
        values = {
            audit.ARTIFACT_PATHS["aggregate_manifest"]: aggregate_manifest,
            audit.ARTIFACT_PATHS["aggregate_audit"]: aggregate_result,
            audit.ARTIFACT_PATHS["final_validation"]: final_validation,
        }
        self._write_json(root / audit.ARTIFACT_PATHS["aggregate_manifest"], aggregate_manifest)
        self._write_json(root / audit.ARTIFACT_PATHS["aggregate_audit"], aggregate_result)
        self._write_json(root / audit.ARTIFACT_PATHS["final_validation"], final_validation)
        self._write_json(result_root / "supersession-manifest.json", {"fixture": True})
        closure_path = root / audit.CLOSURE_MANIFEST
        self._write_json(closure_path, closure)
        return closure_path, values

    def _audit(
        self,
        closure: dict,
        *,
        aggregate_result: dict | None = None,
        value_mutator=None,
        root_mutator=None,
    ) -> dict:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            closure_path, values = self._fixture(root, closure)
            if value_mutator is not None:
                value_mutator(values)
            if root_mutator is not None:
                root_mutator(root / audit.RESULT_ROOT)

            def load_object(path: Path) -> dict:
                return json.loads(path.read_text(encoding="utf-8"))

            def git_json(repo_root: Path, head: str, path: str) -> dict | None:
                del repo_root, head
                value = values.get(path)
                return copy.deepcopy(value) if value is not None else None

            with (
                mock.patch.object(audit, "_load_strict_object", side_effect=load_object),
                mock.patch.object(audit, "_validate_artifact_reference", return_value=[]),
                mock.patch.object(audit, "_git_json", side_effect=git_json),
                mock.patch.object(
                    audit,
                    "_run_aggregate_audit",
                    return_value=aggregate_result or self._aggregate_result(),
                ),
            ):
                return audit.audit_closure(closure_path, repo_root=root)

    def _mutate(self, mutator, **kwargs) -> dict:
        closure = copy.deepcopy(self._closure())
        mutator(closure)
        return self._audit(closure, **kwargs)

    def test_synthetic_valid_closure_is_closed(self):
        result = self._audit(self._closure())

        self.assertEqual(result["status"], "closed")
        self.assertEqual(result["milestone"], "M3")
        self.assertEqual(result["aggregate_status"], "accepted")
        self.assertEqual(result["m4_status"], "NOT_STARTED")
        self.assertEqual(result["errors"], [])
        self.assertEqual(
            set(result),
            {
                "status",
                "milestone",
                "aggregate_status",
                "required_gates",
                "historical_diffs",
                "worktree",
                "m4_status",
                "errors",
                "side_effects",
                "does_not_prove",
            },
        )

    def test_closure_uses_strict_json_loading(self):
        for raw in (b'{"a":1,"a":2}', b"\xef\xbb\xbf{}", b'{"a":NaN}'):
            with self.subTest(raw=raw), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir)
                path = root / audit.CLOSURE_MANIFEST
                path.parent.mkdir(parents=True)
                path.write_bytes(raw)
                result = audit.audit_closure(path, repo_root=root)

            self.assertEqual(result["status"], "invalid")
            self.assertIn("closure_manifest_invalid", result["errors"])

    def test_closure_rejects_non_green_candidate_ci(self):
        result = self._mutate(
            lambda value: value["aggregate_candidate_ci"].__setitem__("conclusion", "failure")
        )

        self.assertIn("aggregate_candidate_ci_not_green", result["errors"])

    def test_closure_rejects_m4_start_or_execution_authority(self):
        for field in ("m4_started", "m4_execution_authorized"):
            with self.subTest(field=field):
                result = self._mutate(
                    lambda value, field=field: value["scope_limits"].__setitem__(field, True)
                )
                self.assertIn("m4_must_remain_not_started", result["errors"])

    def test_missing_bound_artifact_reference_is_rejected(self):
        for name in audit.ARTIFACT_PATHS:
            with self.subTest(name=name):
                result = self._mutate(lambda value, name=name: value["artifacts"].pop(name))
                self.assertIn("closure_artifact_reference_set_invalid", result["errors"])
                self.assertIn(f"closure_artifact_reference_missing:{name}", result["errors"])

    def test_candidate_head_or_run_mismatch_is_rejected(self):
        mutations = (
            (
                "aggregate_candidate_head_mismatch",
                lambda value: value["aggregate_candidate_ci"].__setitem__("head_sha", "e" * 40),
            ),
            (
                "aggregate_candidate_run_mismatch",
                lambda value: value["aggregate_candidate_ci"].__setitem__("run_id", CANDIDATE_RUN + 1),
            ),
        )
        for code, mutator in mutations:
            with self.subTest(code=code):
                self.assertIn(code, self._mutate(mutator)["errors"])

    def test_aggregate_must_be_declared_and_recomputed_as_accepted(self):
        declared = self._mutate(lambda value: value.__setitem__("aggregate_status", "invalid"))
        recomputed = self._audit(
            self._closure(),
            aggregate_result={**self._aggregate_result(), "status": "invalid", "errors": ["tamper"]},
        )

        self.assertIn("aggregate_not_accepted", declared["errors"])
        self.assertIn("aggregate_not_accepted", recomputed["errors"])

    def test_any_required_gate_false_is_rejected(self):
        gate = "aggregate_candidate_ci_green"
        result = self._mutate(lambda value: value["required_gates"].__setitem__(gate, False))

        self.assertIn("required_gate_not_passed", result["errors"])

    def test_nonempty_historical_diff_is_rejected(self):
        result = self._mutate(
            lambda value: value["historical_diffs"].__setitem__("forward_r5", ["changed"])
        )

        self.assertIn("historical_diff_nonempty", result["errors"])

    def test_dirty_or_changed_closure_result_allowlist_is_rejected(self):
        declared = self._mutate(
            lambda value: value["result_root_allowlist"].append("unexpected.json")
        )
        actual = self._audit(
            self._closure(),
            root_mutator=lambda root: (root / "unexpected.json").write_bytes(b"{}\n"),
        )

        self.assertIn("closure_result_root_allowlist_invalid", declared["errors"])
        self.assertIn("closure_result_root_dirty", actual["errors"])

    def test_extra_top_level_field_is_rejected(self):
        result = self._mutate(lambda value: value.__setitem__("extra", True))

        self.assertIn("closure_shape_invalid", result["errors"])

    def test_fresh_retry_or_repair_authority_is_rejected(self):
        expected = {
            "fresh_execution_authorized": "fresh_execution_authority_forbidden",
            "retry_authorized": "retry_authority_forbidden",
            "same_task_retry_authorized": "retry_authority_forbidden",
            "repair_authorized": "repair_authority_forbidden",
        }
        for field, code in expected.items():
            with self.subTest(field=field):
                result = self._mutate(
                    lambda value, field=field: value["scope_limits"].__setitem__(field, True)
                )
                self.assertIn(code, result["errors"])

    def test_wrong_milestone_or_status_is_rejected(self):
        milestone = self._mutate(lambda value: value.__setitem__("milestone", "M4"))
        status = self._mutate(lambda value: value.__setitem__("status", "IN_PROGRESS"))

        self.assertIn("closure_milestone_invalid", milestone["errors"])
        self.assertIn("closure_status_invalid", status["errors"])

    def test_candidate_receipts_must_match_recomputation_and_pass_validation(self):
        aggregate = self._audit(
            self._closure(),
            value_mutator=lambda values: values[audit.ARTIFACT_PATHS["aggregate_audit"]].__setitem__(
                "status", "invalid"
            ),
        )
        final_validation = self._audit(
            self._closure(),
            value_mutator=lambda values: values[audit.ARTIFACT_PATHS["final_validation"]].__setitem__(
                "status", "failed"
            ),
        )

        self.assertIn("aggregate_audit_receipt_mismatch", aggregate["errors"])
        self.assertIn("final_validation_not_passed", final_validation["errors"])

    def test_candidate_aggregate_blob_must_equal_recomputed_input(self):
        result = self._audit(
            self._closure(),
            value_mutator=lambda values: values[audit.ARTIFACT_PATHS["aggregate_manifest"]].__setitem__(
                "tampered", True
            ),
        )

        self.assertIn("aggregate_manifest_candidate_mismatch", result["errors"])


if __name__ == "__main__":
    unittest.main()
