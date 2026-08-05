from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "skills" / "engineering-research-copilot" / "scripts"
TESTS_DIR = REPO_ROOT / "tests"
sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(TESTS_DIR))

from test_validate_m2_direction_bundle import (  # noqa: E402
    _confirm_bundle,
    _route_output,
    canonical_sha256,
    make_valid_m2_bundle,
)
from test_validate_m1_bundle import make_structurally_valid_production_bundle  # noqa: E402
from validate_m3_method_bundle import validate_m3_bundle  # noqa: E402


def _selected_direction(source_m2_bundle: dict) -> dict:
    selected_id = source_m2_bundle["direction_decision"]["selected_direction_id"]
    return next(
        direction
        for direction in source_m2_bundle["direction_portfolio"]["directions"]
        if direction["direction_id"] == selected_id
    )


def _refresh_m3_hashes(bundle: dict) -> None:
    source = bundle["source_m2_bundle"]
    direction = _selected_direction(source)
    bundle["source_m2_bundle_hash"] = canonical_sha256(source)
    bundle["selected_direction_id"] = direction["direction_id"]
    bundle["selected_direction_hash"] = canonical_sha256(direction)


def _reconfirm_after_m1_change(bundle: dict) -> None:
    source = bundle["source_m2_bundle"]
    source["direction_portfolio"]["source_m1_bundle_hash"] = canonical_sha256(
        source["source_m1_bundle"]
    )
    _confirm_bundle(source)
    source["route_output"] = None
    _refresh_m3_hashes(bundle)


def _complete_method_card(direction: dict) -> dict:
    return {
        "schema_version": "m3.1",
        "card_id": "card:data-ml-hybrid:1",
        "method_family": "data_ml_hybrid",
        "applicability": {
            "supported_claim_types": [
                claim["claim_type"] for claim in direction["core_claims"]
            ],
            "required_inputs": ["Frozen fixture input"],
            "incompatible_conditions": ["Unresolved data provenance"],
        },
        "assumptions": ["Fixture observations are independent by trajectory"],
        "minimum_resources": [
            {
                "resource": "CPU time",
                "required_value": 1,
                "unit": "hours",
                "source_constraint_id": "R-CPU-HOURS",
            }
        ],
        "inherited_constraints": copy.deepcopy(direction["resource_limits"]),
        "baselines": ["Frozen fixture baseline"],
        "controls": ["Frozen fixture control"],
        "procedure_outline": ["Compare one bounded fixture prediction"],
        "primary_metrics": [
            metric["metric_id"]
            for claim in direction["core_claims"]
            for metric in claim["required_decision_metrics"]
        ],
        "uncertainty_handling": ["Report calibration error by fixture split"],
        "validation_checks": ["Check trajectory-level split isolation"],
        "failure_modes": ["Trajectory leakage inflates predictive performance"],
        "stop_conditions": [
            {
                "criterion_type": "stop",
                "metric_id": "M-PRED",
                "operator": "<",
                "value": 0.6,
                "unit": "ratio",
            }
        ],
        "pivot_conditions": [
            {
                "criterion_type": "pivot",
                "metric_id": "M-UQ",
                "operator": ">",
                "value": 0.2,
                "unit": "ratio",
            }
        ],
        "safety_boundaries": ["No operational or safety conclusion"],
        "source_ledger": [
            {
                "source_id": "source:fixture:P04",
                "candidate_id": "fixture:P04",
                "basis_level": "abstract",
                "supports": ["Offline method-card structure"],
                "does_not_support": ["Real method performance"],
                "limitations": ["Synthetic abstract-level fixture only"],
            }
        ],
    }


def _make_route_compatible(source: dict) -> None:
    direction = source["direction_portfolio"]["directions"][0]
    direction["minimum_decisive_test"]["claim_coverage"][0][
        "required_precondition_ids"
    ] = ["data-preflight"]
    _confirm_bundle(source)
    route = _route_output(source)
    metric_rows = [
        metric
        for claim in direction["core_claims"]
        for metric in claim["required_decision_metrics"]
    ]
    route["stop_conditions"] = [
        {
            "criterion_type": "stop",
            "metric_id": metric["metric_id"],
            "operator": "<",
            "value": 0.5,
            "unit": metric["unit"],
        }
        for metric in metric_rows
    ]
    route["pivot_conditions"] = [
        {
            "criterion_type": "pivot",
            "metric_id": metric["metric_id"],
            "operator": "<",
            "value": 0.6,
            "unit": metric["unit"],
        }
        for metric in metric_rows
    ]
    source["route_output"] = route


def make_valid_m3_bundle(coaching_mode: str = "bounded") -> dict:
    source = make_valid_m2_bundle()
    if coaching_mode == "route_specific":
        _make_route_compatible(source)
    else:
        _confirm_bundle(source)
    direction = _selected_direction(source)
    return {
        "schema_version": "m3.1",
        "source_m2_bundle": source,
        "source_m2_bundle_hash": canonical_sha256(source),
        "selected_direction_id": direction["direction_id"],
        "selected_direction_hash": canonical_sha256(direction),
        "coaching_mode": coaching_mode,
        "method_cards": [_complete_method_card(direction)],
        "domain_overlays": [],
    }


def _make_production_m3_bundle() -> dict:
    source = json.loads(
        json.dumps(make_valid_m2_bundle()).replace("fixture:P", "contract:P")
    )
    source["source_m1_bundle"] = make_structurally_valid_production_bundle()
    source["fixture_mode"] = False
    del source["evidence_class"]
    del source["proves"]
    del source["does_not_prove"]
    source["direction_portfolio"]["source_m1_bundle_hash"] = canonical_sha256(
        source["source_m1_bundle"]
    )
    _confirm_bundle(source)
    direction = _selected_direction(source)
    card = _complete_method_card(direction)
    card["source_ledger"][0]["source_id"] = "source:contract:P04"
    card["source_ledger"][0]["candidate_id"] = "contract:P04"
    return {
        "schema_version": "m3.1",
        "source_m2_bundle": source,
        "source_m2_bundle_hash": canonical_sha256(source),
        "selected_direction_id": direction["direction_id"],
        "selected_direction_hash": canonical_sha256(direction),
        "coaching_mode": "bounded",
        "method_cards": [card],
        "domain_overlays": [],
    }


def _nuclear_overlay(candidate_id: str = "fixture:P04") -> dict:
    return {
        "schema_version": "m3.1",
        "overlay_id": "domain:nuclear-ml:1",
        "domain": "nuclear_engineering_ml",
        "base_card_ids": ["card:data-ml-hybrid:1"],
        "additional_assumptions": ["Simulator-to-plant transfer is unverified"],
        "additional_failure_modes": ["Domain shift hides unsafe sensor behavior"],
        "additional_validation_checks": ["Check conservation residuals"],
        "additional_stop_conditions": [
            {
                "criterion_type": "stop",
                "metric_id": "M-PRED",
                "operator": "<",
                "value": 0.7,
                "unit": "ratio",
            }
        ],
        "specialist_review_boundaries": ["Independent nuclear specialist review"],
        "transfer_status": "hypothesis",
        "source_ledger": [
            {
                "source_id": f"source:{candidate_id}",
                "candidate_id": candidate_id,
                "basis_level": "abstract",
                "supports": ["Safety-related method checks"],
                "does_not_support": ["Operational nuclear safety"],
                "limitations": ["Synthetic abstract-level fixture only"],
            }
        ],
    }


class ValidateM3MethodBundleTests(unittest.TestCase):
    def test_valid_bounded_bundle_without_route_is_valid(self):
        self.assertEqual(
            validate_m3_bundle(make_valid_m3_bundle()),
            {"status": "valid", "errors": [], "evidence_gaps": []},
        )

    def test_valid_route_specific_bundle_is_valid(self):
        self.assertEqual(
            validate_m3_bundle(make_valid_m3_bundle("route_specific")),
            {"status": "valid", "errors": [], "evidence_gaps": []},
        )

    def test_nonempty_approved_constraint_changes_fail_closed(self):
        bundle = make_valid_m3_bundle(coaching_mode="route_specific")
        bundle["source_m2_bundle"]["route_output"]["approved_constraint_changes"] = [{
            "constraint_id": "R-D1-VRAM",
            "previous_value": 24,
            "approved_value": 48,
            "unit": "GiB",
            "approval_message_id": "message:unverifiable-change",
            "approval_message_sha256": "0" * 64,
        }]
        self.assertIn(
            "unsupported_approved_constraint_change_provenance",
            validate_m3_bundle(bundle)["errors"],
        )

    def test_route_preconditions_must_equal_claim_coverage(self):
        bundle = make_valid_m3_bundle(coaching_mode="route_specific")
        bundle["source_m2_bundle"]["route_output"]["route_traceability"][0][
            "source_precondition_ids"
        ] = []
        self.assertIn(
            "route_precondition_traceability_mismatch",
            validate_m3_bundle(bundle)["errors"],
        )

    def test_route_condition_types_are_derived_from_actual_metric_conditions(self):
        bundle = make_valid_m3_bundle(coaching_mode="route_specific")
        bundle["source_m2_bundle"]["route_output"]["stop_conditions"] = [{
            "criterion_type": "stop",
            "metric_id": "M-COST",
            "operator": ">",
            "value": 2,
            "unit": "hours",
        }]
        self.assertIn(
            "route_condition_traceability_mismatch",
            validate_m3_bundle(bundle)["errors"],
        )

    def test_invalid_embedded_m2_is_rejected(self):
        bundle = make_valid_m3_bundle()
        bundle["source_m2_bundle"]["direction_portfolio"]["schema_version"] = "m2.0"
        bundle["source_m2_bundle_hash"] = canonical_sha256(bundle["source_m2_bundle"])
        self.assertIn("invalid_source_m2_bundle", validate_m3_bundle(bundle)["errors"])

    def test_nonconfirmed_direction_is_rejected(self):
        bundle = make_valid_m3_bundle()
        bundle["source_m2_bundle"]["direction_decision"] = {
            "selected_direction_id": None,
            "status": "waiting_for_user_confirmation",
            "permitted_next_actions": ["confirm", "modify", "reject"],
            "confirmation_event": None,
        }
        _refresh_m3_hashes_for_nonconfirmed(bundle)
        self.assertIn("direction_not_user_confirmed", validate_m3_bundle(bundle)["errors"])

    def test_wrong_selected_direction_hash_is_rejected(self):
        bundle = make_valid_m3_bundle()
        bundle["selected_direction_hash"] = "0" * 64
        self.assertIn("selected_direction_hash_mismatch", validate_m3_bundle(bundle)["errors"])

    def test_route_specific_mode_requires_route(self):
        bundle = make_valid_m3_bundle()
        bundle["coaching_mode"] = "route_specific"
        self.assertIn("route_specific_requires_route", validate_m3_bundle(bundle)["errors"])

    def test_missing_assumptions_is_rejected(self):
        bundle = make_valid_m3_bundle()
        del bundle["method_cards"][0]["assumptions"]
        self.assertIn("missing_method_card_assumptions", validate_m3_bundle(bundle)["errors"])

    def test_missing_baselines_is_rejected(self):
        bundle = make_valid_m3_bundle()
        del bundle["method_cards"][0]["baselines"]
        self.assertIn("missing_method_card_baselines", validate_m3_bundle(bundle)["errors"])

    def test_missing_failure_modes_is_rejected(self):
        bundle = make_valid_m3_bundle()
        del bundle["method_cards"][0]["failure_modes"]
        self.assertIn("missing_method_card_failure_modes", validate_m3_bundle(bundle)["errors"])

    def test_missing_uncertainty_handling_is_rejected(self):
        bundle = make_valid_m3_bundle()
        del bundle["method_cards"][0]["uncertainty_handling"]
        self.assertIn(
            "missing_method_card_uncertainty_handling",
            validate_m3_bundle(bundle)["errors"],
        )

    def test_stop_condition_requires_numeric_value(self):
        bundle = make_valid_m3_bundle()
        bundle["method_cards"][0]["stop_conditions"][0]["value"] = "not-numeric"
        self.assertIn("invalid_method_card_stop_condition", validate_m3_bundle(bundle)["errors"])

    def test_source_ledger_requires_does_not_support(self):
        bundle = make_valid_m3_bundle()
        del bundle["method_cards"][0]["source_ledger"][0]["does_not_support"]
        self.assertIn(
            "missing_source_ledger_does_not_support",
            validate_m3_bundle(bundle)["errors"],
        )

    def test_source_ledger_basis_level_must_match_candidate(self):
        bundle = make_valid_m3_bundle()
        bundle["method_cards"][0]["source_ledger"][0]["basis_level"] = "metadata"
        self.assertIn("source_ledger_basis_level_mismatch", validate_m3_bundle(bundle)["errors"])

    def test_ineligible_source_is_rejected(self):
        bundle = _make_production_m3_bundle()
        for round_name in ("round1", "round2"):
            candidate = bundle["source_m2_bundle"]["source_m1_bundle"][round_name][
                "candidate_pool"
            ][14]
            candidate["recommendation_eligible"] = False
            candidate["verified_record"]["verification"][
                "recommendation_eligible"
            ] = False
            candidate["verified_record"]["verification"]["blocking_reasons"] = [
                "Verified evidence is outside the recommendation scope"
            ]
        ledger = bundle["method_cards"][0]["source_ledger"][0]
        ledger["source_id"] = "source:contract:P15"
        ledger["candidate_id"] = "contract:P15"
        _reconfirm_after_m1_change(bundle)
        self.assertIn("source_ledger_ineligible_candidate", validate_m3_bundle(bundle)["errors"])

    def test_minimum_resource_must_bind_inherited_constraint(self):
        bundle = make_valid_m3_bundle()
        bundle["method_cards"][0]["minimum_resources"][0][
            "source_constraint_id"
        ] = "R-UNKNOWN"
        self.assertIn("minimum_resource_unbound", validate_m3_bundle(bundle)["errors"])

    def test_minimum_resource_cannot_expand_resource_ceiling(self):
        bundle = make_valid_m3_bundle()
        bundle["method_cards"][0]["minimum_resources"][0]["required_value"] = 3
        self.assertIn("minimum_resource_exceeds_ceiling", validate_m3_bundle(bundle)["errors"])

    def test_unknown_method_family_is_rejected(self):
        bundle = make_valid_m3_bundle()
        bundle["method_cards"][0]["method_family"] = "quantum_oracle"
        self.assertIn("unknown_method_family", validate_m3_bundle(bundle)["errors"])

    def test_nuclear_overlay_requires_existing_base_cards(self):
        bundle = make_valid_m3_bundle()
        overlay = _nuclear_overlay()
        overlay["base_card_ids"] = []
        bundle["domain_overlays"] = [overlay]
        self.assertIn("nuclear_overlay_missing_base_card", validate_m3_bundle(bundle)["errors"])

    def test_nuclear_overlay_transfer_must_remain_hypothesis(self):
        bundle = make_valid_m3_bundle()
        overlay = _nuclear_overlay()
        overlay["transfer_status"] = "validated"
        bundle["domain_overlays"] = [overlay]
        self.assertIn(
            "nuclear_overlay_transfer_status_not_hypothesis",
            validate_m3_bundle(bundle)["errors"],
        )

    def test_preprint_cannot_be_sole_nuclear_safety_support(self):
        bundle = _make_production_m3_bundle()
        for round_name in ("round1", "round2"):
            candidate = bundle["source_m2_bundle"]["source_m1_bundle"][round_name][
                "candidate_pool"
            ][14]
            candidate["verification_status"] = "verified_preprint"
            candidate["verified_record"]["verification"]["status"] = (
                "verified_preprint"
            )
        _reconfirm_after_m1_change(bundle)
        bundle["domain_overlays"] = [_nuclear_overlay("contract:P15")]
        self.assertIn(
            "nuclear_safety_requires_non_preprint_support",
            validate_m3_bundle(bundle)["errors"],
        )


def _refresh_m3_hashes_for_nonconfirmed(bundle: dict) -> None:
    source = bundle["source_m2_bundle"]
    bundle["source_m2_bundle_hash"] = canonical_sha256(source)
    direction = source["direction_portfolio"]["directions"][0]
    bundle["selected_direction_id"] = direction["direction_id"]
    bundle["selected_direction_hash"] = canonical_sha256(direction)


if __name__ == "__main__":
    unittest.main()
