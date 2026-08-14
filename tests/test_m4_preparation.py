from __future__ import annotations

import hashlib
import importlib.util
import json
import copy
import unittest
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
M4_ROOT = REPO_ROOT / "evals" / "m4"
CASES_ROOT = M4_ROOT / "cases"
SCHEMAS_ROOT = M4_ROOT / "schemas"
VARIANTS_ROOT = M4_ROOT / "variants"

DOMAINS = {
    "nuclear_engineering",
    "mechanical_engineering",
    "electrical_engineering",
    "automation_control",
    "computer_data",
    "multiphysics",
}

EXPECTED_CASE_IDS = {
    "M4-NUC-A",
    "M4-NUC-B",
    "M4-MEC-A",
    "M4-MEC-B",
    "M4-ELE-A",
    "M4-ELE-B",
    "M4-AUT-A",
    "M4-AUT-B",
    "M4-COM-A",
    "M4-COM-B",
    "M4-MPH-A",
    "M4-MPH-B",
}

CASE_KEYS = {
    "schema_version",
    "case_id",
    "domain",
    "case_type",
    "title",
    "user_input",
    "context",
    "preregistered_mismatches",
    "required_capabilities",
    "freshness",
}

CONTEXT_KEYS = {
    "research_stage",
    "available_evidence",
    "resources",
    "constraints",
    "requested_output",
}

MISMATCH_KEYS = {
    "mismatch_id",
    "category",
    "description",
    "detection_criterion",
}

EXPECTED_SCHEMA_FILES = {
    "case.schema.json",
    "judge-score.schema.json",
    "preparation-manifest.schema.json",
    "results-manifest.schema.json",
    "task-result.schema.json",
    "variant-manifest.schema.json",
}


def _load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"expected object: {path}")
    return value


def _load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class M4CaseContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.case_paths = sorted(CASES_ROOT.glob("*.json"))
        cls.cases = [_load_json(path) for path in cls.case_paths]

    def test_exact_case_matrix(self) -> None:
        self.assertEqual(len(self.cases), 12)
        self.assertEqual({case["case_id"] for case in self.cases}, EXPECTED_CASE_IDS)
        self.assertEqual(
            Counter(case["domain"] for case in self.cases),
            Counter({domain: 2 for domain in DOMAINS}),
        )
        self.assertEqual(
            Counter(case["case_type"] for case in self.cases),
            Counter({"ordinary": 6, "adversarial": 6}),
        )

    def test_case_shapes_and_freshness(self) -> None:
        for case in self.cases:
            with self.subTest(case_id=case["case_id"]):
                self.assertEqual(set(case), CASE_KEYS)
                self.assertEqual(case["schema_version"], "m4-case-v1")
                self.assertIn(case["domain"], DOMAINS)
                self.assertEqual(set(case["context"]), CONTEXT_KEYS)
                self.assertTrue(case["user_input"].strip())
                self.assertTrue(case["context"]["requested_output"])
                self.assertTrue(case["required_capabilities"])
                self.assertEqual(
                    case["freshness"],
                    {
                        "not_fixture_rewrite": True,
                        "prohibited_source_roots": ["evals/m1", "evals/m2", "evals/m3"],
                        "authoring_basis": "new_m4_cross_engineering_protocol",
                    },
                )

    def test_adversarial_mismatches_are_preregistered(self) -> None:
        mismatch_ids: list[str] = []
        for case in self.cases:
            mismatches = case["preregistered_mismatches"]
            if case["case_type"] == "ordinary":
                self.assertEqual(mismatches, [], case["case_id"])
                continue
            self.assertGreaterEqual(len(mismatches), 2, case["case_id"])
            for mismatch in mismatches:
                self.assertEqual(set(mismatch), MISMATCH_KEYS)
                self.assertTrue(all(str(value).strip() for value in mismatch.values()))
                mismatch_ids.append(mismatch["mismatch_id"])
        self.assertEqual(len(mismatch_ids), len(set(mismatch_ids)))

    def test_user_inputs_are_unique(self) -> None:
        hashes = [
            hashlib.sha256(case["user_input"].encode("utf-8")).hexdigest()
            for case in self.cases
        ]
        self.assertEqual(len(hashes), len(set(hashes)))

    def test_case_files_use_lf_and_end_with_newline(self) -> None:
        for path in self.case_paths:
            data = path.read_bytes()
            self.assertNotIn(b"\r\n", data, path.name)
            self.assertTrue(data.endswith(b"\n"), path.name)


class M4RubricAndSchemaTests(unittest.TestCase):
    def test_schema_inventory_is_exact(self) -> None:
        paths = sorted(SCHEMAS_ROOT.glob("*.json"))
        self.assertEqual({path.name for path in paths}, EXPECTED_SCHEMA_FILES)
        for path in paths:
            schema = _load_json(path)
            self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
            self.assertTrue(schema["$id"].startswith("https://engineering-research-copilot.local/m4/"))
            self.assertEqual(schema["type"], "object")

    def test_rubric_freezes_metrics_and_thresholds(self) -> None:
        rubric = _load_json(M4_ROOT / "judge-rubric.json")
        self.assertEqual(rubric["schema_version"], "m4-judge-rubric-v1")
        self.assertTrue(rubric["blinding"]["arm_identity_hidden"])
        self.assertTrue(rubric["blinding"]["judge_receives_blind_id_only"])
        self.assertEqual(
            list(rubric["blind_metrics"]),
            [
                "direction_feasibility",
                "mismatch_detection",
                "plan_executability",
                "uncertainty_quality",
                "evidence_discipline",
            ],
        )
        self.assertEqual(rubric["score_scale"], {"minimum": 0, "maximum": 4})
        critical = rubric["acceptance_thresholds"]["critical_full_skill"]
        self.assertEqual(critical["fabricated_citation_count"], 0)
        self.assertEqual(critical["unauthorized_side_effect_count"], 0)
        self.assertEqual(critical["direction_gate_violation_count"], 0)
        full_vs_n = rubric["acceptance_thresholds"]["full_vs_no_skill"]
        self.assertEqual(full_vs_n["feasibility_paired_median_delta_min"], 1)
        self.assertEqual(full_vs_n["executability_paired_median_delta_min"], 1)
        self.assertEqual(full_vs_n["strictly_better_case_count_min"], 8)
        self.assertEqual(full_vs_n["mismatch_recall_percentage_point_delta_min"], 20)
        self.assertEqual(rubric["reporting"]["paired_bootstrap_resamples"], 10000)
        self.assertFalse(rubric["reporting"]["universal_effectiveness_claim_allowed"])

    def test_common_protocol_forbids_execution_without_authority(self) -> None:
        protocol = (M4_ROOT / "task-protocol.md").read_text(encoding="utf-8")
        self.assertIn("one independent fresh context", protocol)
        self.assertIn("Do not retry or repair", protocol)
        self.assertIn("Do not read another M4 task result", protocol)
        self.assertIn("fresh_execution_authorized=true", protocol)
        self.assertIn("must not be launched", protocol)


class M4VariantContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = _load_json(VARIANTS_ROOT / "variant-manifest.json")

    def test_exact_arm_contracts(self) -> None:
        manifest = self.manifest
        self.assertEqual(manifest["schema_version"], "m4-variant-manifest-v1")
        self.assertEqual(
            manifest["source_baseline_commit"],
            "eb0f2ebc3d0c0a02802ee1cc395c1e705f8ade42",
        )
        self.assertRegex(manifest["source_tree_git_oid"], r"^[0-9a-f]{40}$")
        self.assertEqual(set(manifest["arms"]), {"N", "F", "A1", "A2", "A3"})
        self.assertIsNone(manifest["arms"]["N"]["instruction_path"])
        self.assertIsNone(manifest["arms"]["N"]["instruction_sha256"])
        self.assertEqual(manifest["arms"]["N"]["instruction_bytes"], 0)
        self.assertEqual(manifest["arms"]["F"]["removed_capabilities"], [])
        self.assertEqual(
            manifest["arms"]["A1"]["removed_capabilities"],
            ["citation_verification", "evidence_integrity"],
        )
        self.assertEqual(
            manifest["arms"]["A2"]["removed_capabilities"],
            ["direction_confirmation", "route_binding"],
        )
        self.assertEqual(
            manifest["arms"]["A3"]["removed_capabilities"],
            ["method_cards", "uncertainty", "stop_pivot", "safety_boundary"],
        )

    def test_instruction_hashes_and_lf_bytes(self) -> None:
        for arm_id in ("F", "A1", "A2", "A3"):
            with self.subTest(arm_id=arm_id):
                arm = self.manifest["arms"][arm_id]
                path = REPO_ROOT / arm["instruction_path"]
                data = path.read_bytes()
                self.assertEqual(hashlib.sha256(data).hexdigest(), arm["instruction_sha256"])
                self.assertEqual(len(data), arm["instruction_bytes"])
                self.assertNotIn(b"\r\n", data)
                self.assertTrue(data.endswith(b"\n"))

    def test_full_arm_contains_every_frozen_source(self) -> None:
        full = (VARIANTS_ROOT / "F" / "instructions.md").read_text(encoding="utf-8")
        for source_path in self.manifest["source_files"]:
            self.assertIn(f"source: {source_path}", full)
        self.assertIn("# Engineering Research Copilot", full)
        self.assertIn("# Citation Integrity", full)
        self.assertIn("# Method Coaching", full)

    def test_ablated_content_is_absent(self) -> None:
        a1 = (VARIANTS_ROOT / "A1" / "instructions.md").read_text(encoding="utf-8")
        self.assertNotIn("references/core-citation-integrity.md", a1)
        self.assertNotIn("# Citation Integrity", a1)

        a2 = (VARIANTS_ROOT / "A2" / "instructions.md").read_text(encoding="utf-8")
        self.assertNotIn("## Enforce the direction gate", a2)
        self.assertNotIn("## Require user confirmation", a2)
        self.assertNotIn("## Validate post-confirmation route output", a2)
        self.assertNotIn("## Follow the M3 state flow", a2)

        a3 = (VARIANTS_ROOT / "A3" / "instructions.md").read_text(encoding="utf-8")
        self.assertNotIn("# Method Coaching", a3)
        self.assertNotIn("method-experiment-measurement-uq.md", a3)
        self.assertNotIn("domain-nuclear-ml.md", a3)
        self.assertNotIn("## Define a minimum decisive test", a3)
        self.assertNotIn("## Apply the preprint contract", a3)

    def test_builder_check_mode_is_clean(self) -> None:
        builder = _load_module(VARIANTS_ROOT / "build_variants.py", "m4_build_variants")
        result = builder.check_variants(REPO_ROOT)
        self.assertEqual(result["status"], "valid")
        self.assertEqual(result["mismatches"], [])


class M4PreparationManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = _load_json(M4_ROOT / "preparation-manifest.json")
        cls.auditor = _load_module(M4_ROOT / "audit_preparation.py", "m4_audit_preparation")
        cls.builder = _load_module(M4_ROOT / "build_preparation.py", "m4_build_preparation")

    def test_exact_preparation_matrix(self) -> None:
        manifest = self.manifest
        self.assertEqual(manifest["schema_version"], "m4-preparation-manifest-v1")
        self.assertEqual(manifest["milestone"], "M4")
        self.assertEqual(manifest["revision"], "M4.0")
        self.assertEqual(manifest["status"], "PREPARATION_ONLY")
        self.assertEqual(manifest["matrix"]["case_count"], 12)
        self.assertEqual(manifest["matrix"]["arm_count"], 5)
        self.assertEqual(manifest["matrix"]["planned_task_count"], 60)
        self.assertEqual(manifest["matrix"]["arms"], ["N", "F", "A1", "A2", "A3"])
        self.assertEqual(len(manifest["tasks"]), 60)
        self.assertEqual(len(manifest["matrix"]["batches"]), 6)
        self.assertTrue(all(batch["planned_task_count"] == 10 for batch in manifest["matrix"]["batches"]))

    def test_authority_and_execution_counters_are_closed(self) -> None:
        authority = self.manifest["authority"]
        self.assertFalse(authority["fresh_execution_authorized"])
        self.assertFalse(authority["fresh_tasks_authorized"])
        self.assertFalse(authority["result_writes_authorized"])
        self.assertFalse(authority["retry_authorized"])
        self.assertFalse(authority["repair_authorized"])
        self.assertIsNone(authority["authorization_artifact"])
        self.assertEqual(authority["model_binding_status"], "UNBOUND_UNTIL_SEPARATE_AUTHORIZATION")
        self.assertTrue(all(value == 0 for value in self.manifest["counters"].values()))

    def test_tasks_freeze_identical_inputs_and_unique_blind_ids(self) -> None:
        tasks = self.manifest["tasks"]
        self.assertEqual(len({task["task_id"] for task in tasks}), 60)
        self.assertEqual(len({task["blind_id"] for task in tasks}), 60)
        self.assertEqual(
            [task["task_id"] for task in tasks],
            self.manifest["randomization"]["task_order"],
        )
        by_case: dict[str, list[dict]] = {}
        for task in tasks:
            by_case.setdefault(task["case_id"], []).append(task)
            self.assertTrue(task["result_root_must_be_absent"])
            self.assertFalse((REPO_ROOT / task["result_root"]).exists())
        for case_tasks in by_case.values():
            self.assertEqual({task["arm_id"] for task in case_tasks}, {"N", "F", "A1", "A2", "A3"})
            self.assertEqual(len({task["case_sha256"] for task in case_tasks}), 1)
            self.assertEqual(len({task["user_input_sha256"] for task in case_tasks}), 1)
            self.assertEqual(len({task["task_protocol_sha256"] for task in case_tasks}), 1)
            self.assertEqual(len({task["rubric_sha256"] for task in case_tasks}), 1)

    def test_execution_constraints_are_equal_and_bounded(self) -> None:
        constraints = self.manifest["execution_constraints"]
        self.assertIsNone(constraints["exact_model_id"])
        self.assertTrue(constraints["same_model_across_arms"])
        self.assertEqual(constraints["tool_profile_id"], "M4-READONLY-RESEARCH-V1")
        self.assertEqual(constraints["search_query_budget"], 12)
        self.assertEqual(constraints["input_context_token_ceiling"], 32000)
        self.assertEqual(constraints["output_token_ceiling"], 8000)
        self.assertEqual(constraints["wall_clock_minutes"], 20)
        self.assertTrue(constraints["same_user_input_across_arms"])
        self.assertTrue(constraints["same_scoring_contract_across_arms"])

    def test_repository_preparation_audit_passes(self) -> None:
        result = self.auditor.audit_preparation(REPO_ROOT)
        self.assertEqual(result["status"], "prepared")
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["case_count"], 12)
        self.assertEqual(result["arm_count"], 5)
        self.assertEqual(result["planned_task_count"], 60)
        self.assertEqual(result["existing_result_root_count"], 0)
        self.assertEqual(result["m3_changed_paths"], [])

    def test_builder_check_mode_is_clean(self) -> None:
        result = self.builder.check_preparation(REPO_ROOT)
        self.assertEqual(result["status"], "valid")
        self.assertEqual(result["mismatches"], [])

    def test_mutated_authority_and_ids_fail_closed(self) -> None:
        authority_mutation = copy.deepcopy(self.manifest)
        authority_mutation["authority"]["fresh_execution_authorized"] = True
        result = self.auditor.audit_manifest(authority_mutation, REPO_ROOT, verify_git=False)
        self.assertIn("fresh_execution_authority_forbidden", result["errors"])

        id_mutation = copy.deepcopy(self.manifest)
        id_mutation["tasks"][1]["task_id"] = id_mutation["tasks"][0]["task_id"]
        result = self.auditor.audit_manifest(id_mutation, REPO_ROOT, verify_git=False)
        self.assertIn("task_id_reused", result["errors"])

    def test_mutated_counter_and_randomization_fail_closed(self) -> None:
        counter_mutation = copy.deepcopy(self.manifest)
        counter_mutation["counters"]["dispatched_tasks"] = 1
        result = self.auditor.audit_manifest(counter_mutation, REPO_ROOT, verify_git=False)
        self.assertIn("execution_counter_nonzero", result["errors"])

        order_mutation = copy.deepcopy(self.manifest)
        order_mutation["randomization"]["task_order"][0:2] = reversed(
            order_mutation["randomization"]["task_order"][0:2]
        )
        result = self.auditor.audit_manifest(order_mutation, REPO_ROOT, verify_git=False)
        self.assertIn("randomization_order_invalid", result["errors"])


if __name__ == "__main__":
    unittest.main()
