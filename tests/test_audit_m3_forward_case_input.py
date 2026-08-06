from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "evals" / "m3"))
sys.path.insert(0, str(REPO_ROOT / "tests"))

from audit_forward_case_input import audit_case  # noqa: E402
from test_validate_m2_direction_bundle import canonical_sha256  # noqa: E402
from test_validate_m3_method_bundle import (  # noqa: E402
    _make_production_m3_bundle,
    _make_route_compatible,
)


VALIDATOR = "skills/engineering-research-copilot/scripts/validate_m2_direction_bundle.py"


def _receipt(bundle: dict, case_id: str) -> dict:
    return {
        "case_id": case_id,
        "status": "valid",
        "errors": [],
        "evidence_gaps": [],
        "invocation_count": 1,
        "validator": VALIDATOR,
        "input_canonical_sha256": canonical_sha256(bundle),
        "source_m1_acceptance_status": "complete",
        "constructed_by_context": f"construct:{case_id}",
        "reviewed_by_context": f"review:{case_id}",
    }


def _bounded_source() -> dict:
    return copy.deepcopy(_make_production_m3_bundle()["source_m2_bundle"])


def _route_source() -> dict:
    source = _bounded_source()
    _make_route_compatible(source)
    return source


def _selected(bundle: dict) -> dict:
    selected_id = bundle["direction_decision"]["selected_direction_id"]
    return next(
        direction
        for direction in bundle["direction_portfolio"]["directions"]
        if direction["direction_id"] == selected_id
    )


class AuditM3ForwardCaseInputTests(unittest.TestCase):
    def assertConflict(self, result: dict, code: str) -> None:  # noqa: N802
        self.assertEqual(result["status"], "contract_conflict")
        self.assertIn(code, result["errors"])

    def test_f01_accepts_route_free_data_ml_with_numeric_authority(self):
        bundle = _bounded_source()

        result = audit_case("m3-f01", bundle, _receipt(bundle, "m3-f01"))

        self.assertEqual(result, {
            "case_id": "m3-f01",
            "status": "eligible",
            "coaching_mode": "bounded",
            "errors": [],
            "evidence_gaps": [],
            "required_model_boundaries": [],
        })

    def test_bounded_with_route_present_conflicts_before_prompt(self):
        bundle = _route_source()

        result = audit_case("m3-f01", bundle, _receipt(bundle, "m3-f01"))

        self.assertConflict(result, "bounded_coaching_requires_route_absent")

    def test_f01_rejects_unresolved_blocking_precondition(self):
        bundle = _bounded_source()
        direction = _selected(bundle)
        direction["minimum_decisive_test"]["required_preconditions"][0][
            "status"
        ] = "unresolved"

        result = audit_case("m3-f01", bundle, _receipt(bundle, "m3-f01"))

        self.assertConflict(result, "blocking_precondition_unresolved")

    def test_f02_accepts_exact_route_traceability(self):
        bundle = _route_source()

        result = audit_case("m3-f02", bundle, _receipt(bundle, "m3-f02"))

        self.assertEqual(result["status"], "eligible")
        self.assertEqual(result["coaching_mode"], "route_specific")

    def test_route_specific_without_route_conflicts_before_prompt(self):
        bundle = _bounded_source()

        result = audit_case("m3-f02", bundle, _receipt(bundle, "m3-f02"))

        self.assertConflict(result, "route_specific_requires_route")

    def test_f02_rederives_preconditions_and_condition_types(self):
        bundle = _route_source()
        route = bundle["route_output"]
        route["route_traceability"][0]["source_precondition_ids"] = []
        route["route_traceability"][1]["route_condition_types"] = ["go", "stop"]

        result = audit_case("m3-f02", bundle, _receipt(bundle, "m3-f02"))

        self.assertConflict(result, "route_precondition_traceability_mismatch")
        self.assertIn("route_condition_traceability_mismatch", result["errors"])

    def test_f02_rejects_condition_metric_outside_selected_metrics(self):
        bundle = _route_source()
        bundle["route_output"]["stop_conditions"][0]["metric_id"] = "M-COST"

        result = audit_case("m3-f02", bundle, _receipt(bundle, "m3-f02"))

        self.assertConflict(result, "route_condition_metric_not_selected")

    def test_f03_accepts_nonempty_change_with_type_strict_original_limits(self):
        bundle = json.loads(
            (
                REPO_ROOT
                / "evals"
                / "m3"
                / "forward-inputs-r2"
                / "m3-f03-approved-change.bundle.json"
            ).read_text(encoding="utf-8")
        )

        result = audit_case("m3-f03", bundle, _receipt(bundle, "m3-f03"))

        self.assertEqual(result["status"], "eligible")
        self.assertIsNone(result["coaching_mode"])

    def test_f03_rejects_empty_change_and_numeric_type_drift(self):
        bundle = json.loads(
            (
                REPO_ROOT
                / "evals"
                / "m3"
                / "forward-inputs-r2"
                / "m3-f03-approved-change.bundle.json"
            ).read_text(encoding="utf-8")
        )
        bundle["route_output"]["approved_constraint_changes"] = []
        result = audit_case("m3-f03", bundle, _receipt(bundle, "m3-f03"))
        self.assertConflict(result, "approved_constraint_changes_required")

        bundle = json.loads(
            (
                REPO_ROOT
                / "evals"
                / "m3"
                / "forward-inputs-r2"
                / "m3-f03-approved-change.bundle.json"
            ).read_text(encoding="utf-8")
        )
        bundle["route_output"]["inherited_constraints"][0]["value"] = float(
            bundle["route_output"]["inherited_constraints"][0]["value"]
        )
        result = audit_case("m3-f03", bundle, _receipt(bundle, "m3-f03"))
        self.assertConflict(result, "original_resource_limits_not_type_strict_equal")

    def test_f04_requires_independent_measurement_calibration_and_uq_lineage(self):
        bundle = _bounded_source()
        result = audit_case("m3-f04", bundle, _receipt(bundle, "m3-f04"))
        self.assertConflict(result, "experiment_measurement_uq_family_not_derivable")

        direction = _selected(bundle)
        direction["title"] = (
            "Non-nuclear controlled physical measurement calibration and uncertainty"
        )
        direction["minimum_decisive_test"]["scope"] = (
            "measurement calibration repeatability reproducibility uncertainty budget"
        )
        direction["minimum_decisive_test"]["inputs"].append(
            "Measurand units and calibration trace"
        )
        direction["minimum_decisive_test"]["required_preconditions"][0][
            "description"
        ] = (
            "Verify metric unit, calibration trace, repeatability, reproducibility, "
            "and measurement uncertainty before the bounded test."
        )
        result = audit_case("m3-f04", bundle, _receipt(bundle, "m3-f04"))
        self.assertEqual(result["status"], "eligible")
        self.assertEqual(result["coaching_mode"], "bounded")

    def test_f04_not_run_receipt_remains_not_run(self):
        receipt = {
            "case_id": "m3-f04",
            "status": "NOT_RUN",
            "errors": [],
            "evidence_gaps": ["no independently accepted complete non-nuclear M1/M2 input"],
            "invocation_count": 0,
            "validator": VALIDATOR,
        }

        result = audit_case("m3-f04", None, receipt)

        self.assertEqual(result["status"], "not_run")
        self.assertEqual(result["errors"], [])
        self.assertTrue(result["evidence_gaps"])

    def test_f05_accepts_current_route_compatible_nuclear_lineage(self):
        bundle = json.loads(
            (
                REPO_ROOT
                / "evals"
                / "m3"
                / "forward-inputs-r2"
                / "m3-f02-route-compatible.bundle.json"
            ).read_text(encoding="utf-8")
        )

        result = audit_case("m3-f05", bundle, _receipt(bundle, "m3-f05"))

        self.assertEqual(result["status"], "eligible")
        self.assertEqual(result["coaching_mode"], "route_specific")
        self.assertEqual(
            result["required_model_boundaries"],
            [
                "non_preprint_safety_support_is_claim_limited",
                "specialist_review_required",
                "no_operational_or_safety_credit",
                "transfer_status_hypothesis",
            ],
        )

    def test_f05_rejects_bounded_route_free_input_and_preprint_only_safety(self):
        bundle = json.loads(
            (
                REPO_ROOT
                / "evals"
                / "m3"
                / "forward-inputs-r2"
                / "m3-f05-nuclear-ml.bundle.json"
            ).read_text(encoding="utf-8")
        )
        result = audit_case("m3-f05", bundle, _receipt(bundle, "m3-f05"))
        self.assertConflict(result, "route_specific_requires_route")

        bundle = json.loads(
            (
                REPO_ROOT
                / "evals"
                / "m3"
                / "forward-inputs-r2"
                / "m3-f02-route-compatible.bundle.json"
            ).read_text(encoding="utf-8")
        )
        for round_name in ("round1", "round2"):
            for candidate in bundle["source_m1_bundle"][round_name]["candidate_pool"]:
                if "safety" in json.dumps(candidate, ensure_ascii=False).lower():
                    candidate["verification_status"] = "verified_preprint"
        result = audit_case("m3-f05", bundle, _receipt(bundle, "m3-f05"))
        self.assertConflict(result, "non_preprint_safety_source_missing")

    def test_invalid_or_nonindependent_m2_receipt_conflicts(self):
        bundle = _bounded_source()
        receipt = _receipt(bundle, "m3-f01")
        receipt["invocation_count"] = 2
        receipt["reviewed_by_context"] = receipt["constructed_by_context"]

        result = audit_case("m3-f01", bundle, receipt)

        self.assertConflict(result, "m2_validation_receipt_not_one_shot")
        self.assertIn("construction_and_review_context_must_differ", result["errors"])


if __name__ == "__main__":
    unittest.main()
