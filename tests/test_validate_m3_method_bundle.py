from __future__ import annotations

import copy
import json
import math
import os
import subprocess
import sys
import tempfile
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


BASIS_LEVEL_MAP = {
    "metadata_level": "metadata",
    "abstract_level": "abstract",
    "fulltext_level": "full_text",
}
REQUIRED_NONEMPTY_CARD_LISTS = (
    "assumptions",
    "minimum_resources",
    "inherited_constraints",
    "baselines",
    "controls",
    "procedure_outline",
    "primary_metrics",
    "uncertainty_handling",
    "validation_checks",
    "failure_modes",
    "stop_conditions",
    "pivot_conditions",
    "safety_boundaries",
    "source_ledger",
)
METHOD_FAMILIES = (
    "experiment_measurement_uq",
    "modeling_simulation_vvuq",
    "control_optimization_identification",
    "signal_diagnostics",
    "data_ml_hybrid",
    "reliability_safety_risk",
)
NONFINITE_OR_BOOLEAN_VALUES = (True, math.nan, math.inf, -math.inf)
VALID_RESULT = {"status": "valid", "errors": [], "evidence_gaps": []}


def _assert_valid(test_case: unittest.TestCase, bundle: dict) -> None:
    test_case.assertEqual(validate_m3_bundle(bundle), VALID_RESULT)


def _candidate_by_id(source_m1_bundle: dict, round_name: str, candidate_id: str) -> dict:
    matches = [
        candidate
        for candidate in source_m1_bundle[round_name]["candidate_pool"]
        if candidate["candidate_id"] == candidate_id
    ]
    if len(matches) != 1:
        raise AssertionError(
            f"expected exactly one {candidate_id} in {round_name}, found {len(matches)}"
        )
    return matches[0]


def _m3_basis_level(candidate: dict) -> str:
    return BASIS_LEVEL_MAP[candidate["basis_level"]]


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


def _add_bounded_condition_authority(source_m2_bundle: dict) -> None:
    direction = source_m2_bundle["direction_portfolio"]["directions"][0]
    coverage_by_claim = {
        coverage["claim_id"]: coverage
        for coverage in direction["minimum_decisive_test"]["claim_coverage"]
    }
    coverage_by_claim["C-PRED"]["decision_criteria"].append(
        {
            "criterion_type": "stop",
            "metric_id": "M-PRED",
            "operator": "<",
            "value": 0.6,
            "unit": "ratio",
        }
    )
    coverage_by_claim["C-UQ"]["decision_criteria"].append(
        {
            "criterion_type": "pivot",
            "metric_id": "M-UQ",
            "operator": ">",
            "value": 0.2,
            "unit": "ratio",
        }
    )


def _complete_method_card(direction: dict, source_m1_bundle: dict) -> dict:
    source_candidate = _candidate_by_id(
        source_m1_bundle,
        "round2",
        direction["supporting_candidate_ids"][1],
    )
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
                "source_id": f"source:{source_candidate['candidate_id']}",
                "candidate_id": source_candidate["candidate_id"],
                "basis_level": _m3_basis_level(source_candidate),
                "support_types": ["method"],
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
    _add_bounded_condition_authority(source)
    if coaching_mode == "route_specific":
        _make_route_compatible(source)
    else:
        _confirm_bundle(source)
    direction = _selected_direction(source)
    card = _complete_method_card(direction, source["source_m1_bundle"])
    if coaching_mode == "route_specific":
        card["stop_conditions"] = copy.deepcopy(
            source["route_output"]["stop_conditions"]
        )
        card["pivot_conditions"] = copy.deepcopy(
            source["route_output"]["pivot_conditions"]
        )
    return {
        "schema_version": "m3.1",
        "source_m2_bundle": source,
        "source_m2_bundle_hash": canonical_sha256(source),
        "selected_direction_id": direction["direction_id"],
        "selected_direction_hash": canonical_sha256(direction),
        "coaching_mode": coaching_mode,
        "method_cards": [card],
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
    _add_bounded_condition_authority(source)
    source["direction_portfolio"]["source_m1_bundle_hash"] = canonical_sha256(
        source["source_m1_bundle"]
    )
    _confirm_bundle(source)
    direction = _selected_direction(source)
    card = _complete_method_card(direction, source["source_m1_bundle"])
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
                "value": 0.6,
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
                "support_types": ["safety"],
                "supports": ["Safety-related method checks"],
                "does_not_support": ["Operational nuclear safety"],
                "limitations": ["Synthetic abstract-level fixture only"],
            }
        ],
    }


class ValidateM3MethodBundleTests(unittest.TestCase):
    def test_valid_bounded_bundle_without_route_is_valid(self):
        _assert_valid(self, make_valid_m3_bundle())

    def test_valid_route_specific_bundle_is_valid(self):
        _assert_valid(self, make_valid_m3_bundle("route_specific"))

    def test_all_permitted_method_families_are_valid(self):
        for method_family in METHOD_FAMILIES:
            with self.subTest(method_family=method_family):
                bundle = make_valid_m3_bundle()
                bundle["method_cards"][0]["method_family"] = method_family
                _assert_valid(self, bundle)

    def test_valid_nuclear_overlay_is_valid(self):
        bundle = make_valid_m3_bundle()
        bundle["domain_overlays"] = [_nuclear_overlay()]
        _assert_valid(self, bundle)

    def test_bounded_card_conditions_match_decisive_test_authority(self):
        _assert_valid(self, make_valid_m3_bundle())

    def test_route_card_conditions_match_route_authority(self):
        _assert_valid(self, make_valid_m3_bundle("route_specific"))

    def test_overlay_stop_condition_matches_bounded_authority(self):
        bundle = make_valid_m3_bundle()
        bundle["domain_overlays"] = [_nuclear_overlay()]
        _assert_valid(self, bundle)

    def test_bounded_card_rejects_fabricated_stop_value(self):
        bundle = make_valid_m3_bundle()
        bundle["method_cards"][0]["stop_conditions"][0]["value"] = 0.61
        self.assertEqual(
            validate_m3_bundle(bundle),
            {
                "status": "invalid",
                "errors": ["method_card_stop_condition_not_authoritative"],
                "evidence_gaps": [],
            },
        )

    def test_bounded_card_rejects_changed_pivot_unit(self):
        bundle = make_valid_m3_bundle()
        bundle["method_cards"][0]["pivot_conditions"][0]["unit"] = "percent"
        self.assertEqual(
            validate_m3_bundle(bundle),
            {
                "status": "invalid",
                "errors": [
                    "invalid_method_card_pivot_condition",
                    "method_card_pivot_condition_not_authoritative",
                ],
                "evidence_gaps": [],
            },
        )

    def test_route_card_rejects_fabricated_stop_value(self):
        bundle = make_valid_m3_bundle("route_specific")
        bundle["method_cards"][0]["stop_conditions"][0]["value"] = 0.51
        self.assertEqual(
            validate_m3_bundle(bundle),
            {
                "status": "invalid",
                "errors": ["method_card_stop_condition_not_authoritative"],
                "evidence_gaps": [],
            },
        )

    def test_route_card_rejects_changed_pivot_unit(self):
        bundle = make_valid_m3_bundle("route_specific")
        bundle["method_cards"][0]["pivot_conditions"][0]["unit"] = "percent"
        self.assertEqual(
            validate_m3_bundle(bundle),
            {
                "status": "invalid",
                "errors": [
                    "invalid_method_card_pivot_condition",
                    "method_card_pivot_condition_not_authoritative",
                ],
                "evidence_gaps": [],
            },
        )

    def test_overlay_rejects_fabricated_stop_value(self):
        bundle = make_valid_m3_bundle()
        overlay = _nuclear_overlay()
        overlay["additional_stop_conditions"][0]["value"] = 0.61
        bundle["domain_overlays"] = [overlay]
        self.assertEqual(
            validate_m3_bundle(bundle),
            {
                "status": "invalid",
                "errors": ["nuclear_overlay_stop_condition_not_authoritative"],
                "evidence_gaps": [],
            },
        )

    def test_overlay_rejects_changed_stop_unit(self):
        bundle = make_valid_m3_bundle()
        overlay = _nuclear_overlay()
        overlay["additional_stop_conditions"][0]["unit"] = "percent"
        bundle["domain_overlays"] = [overlay]
        self.assertEqual(
            validate_m3_bundle(bundle),
            {
                "status": "invalid",
                "errors": [
                    "invalid_nuclear_overlay_stop_condition",
                    "nuclear_overlay_stop_condition_not_authoritative",
                ],
                "evidence_gaps": [],
            },
        )

    def test_cli_multi_error_order_is_hash_seed_independent(self):
        bundle = make_valid_m3_bundle()
        card = bundle["method_cards"][0]
        for field in (
            "assumptions",
            "baselines",
            "controls",
            "failure_modes",
            "uncertainty_handling",
        ):
            del card[field]
        for field in (
            "supported_claim_types",
            "required_inputs",
            "incompatible_conditions",
        ):
            del card["applicability"][field]
        ledger = card["source_ledger"][0]
        for field in ("supports", "does_not_support", "limitations"):
            del ledger[field]

        outputs = []
        with tempfile.TemporaryDirectory(prefix="m3-hash-seed-") as temp_dir:
            fixture = Path(temp_dir) / "multi-error.json"
            fixture.write_text(
                json.dumps(bundle, ensure_ascii=False),
                encoding="utf-8",
            )
            for seed in ("1", "2", "3", "47", "101"):
                environment = os.environ.copy()
                environment["PYTHONHASHSEED"] = seed
                completed = subprocess.run(
                    [
                        sys.executable,
                        "-X",
                        "utf8",
                        str(SCRIPTS_DIR / "validate_m3_method_bundle.py"),
                        str(fixture),
                    ],
                    cwd=REPO_ROOT,
                    env=environment,
                    check=False,
                    capture_output=True,
                )
                self.assertEqual(completed.returncode, 1)
                self.assertEqual(completed.stderr, b"")
                self.assertEqual(len(completed.stdout.splitlines()), 1)
                outputs.append(completed.stdout)

        self.assertTrue(all(output == outputs[0] for output in outputs[1:]))

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
        _refresh_m3_hashes(bundle)
        self.assertEqual(
            validate_m3_bundle(bundle),
            {
                "status": "invalid",
                "errors": ["unsupported_approved_constraint_change_provenance"],
                "evidence_gaps": [],
            },
        )

    def test_route_preconditions_must_equal_claim_coverage(self):
        bundle = make_valid_m3_bundle(coaching_mode="route_specific")
        bundle["source_m2_bundle"]["route_output"]["route_traceability"][0][
            "source_precondition_ids"
        ] = []
        _refresh_m3_hashes(bundle)
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
        _refresh_m3_hashes(bundle)
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

    def test_bounded_coaching_requires_route_absent(self):
        bundle = make_valid_m3_bundle("route_specific")
        bundle["coaching_mode"] = "bounded"
        self.assertEqual(
            validate_m3_bundle(bundle),
            {
                "status": "invalid",
                "errors": ["bounded_coaching_requires_route_absent"],
                "evidence_gaps": [],
            },
        )

    def test_required_nonempty_card_lists_cannot_be_missing(self):
        for field in REQUIRED_NONEMPTY_CARD_LISTS:
            with self.subTest(field=field):
                bundle = make_valid_m3_bundle()
                del bundle["method_cards"][0][field]
                self.assertIn(
                    f"missing_method_card_{field}",
                    validate_m3_bundle(bundle)["errors"],
                )

    def test_required_nonempty_card_lists_cannot_be_empty(self):
        for field in REQUIRED_NONEMPTY_CARD_LISTS:
            with self.subTest(field=field):
                bundle = make_valid_m3_bundle()
                bundle["method_cards"][0][field] = []
                self.assertIn(
                    f"empty_method_card_{field}",
                    validate_m3_bundle(bundle)["errors"],
                )

    def test_stop_condition_requires_finite_nonboolean_numeric_value(self):
        for value in NONFINITE_OR_BOOLEAN_VALUES + ("not-numeric",):
            with self.subTest(value=value):
                bundle = make_valid_m3_bundle()
                bundle["method_cards"][0]["stop_conditions"][0]["value"] = value
                self.assertIn(
                    "invalid_method_card_stop_condition",
                    validate_m3_bundle(bundle)["errors"],
                )

    def test_pivot_condition_requires_finite_nonboolean_numeric_value(self):
        for value in NONFINITE_OR_BOOLEAN_VALUES:
            with self.subTest(value=value):
                bundle = make_valid_m3_bundle()
                bundle["method_cards"][0]["pivot_conditions"][0]["value"] = value
                self.assertIn(
                    "invalid_method_card_pivot_condition",
                    validate_m3_bundle(bundle)["errors"],
                )

    def test_source_ledger_requires_does_not_support(self):
        bundle = make_valid_m3_bundle()
        del bundle["method_cards"][0]["source_ledger"][0]["does_not_support"]
        self.assertIn(
            "missing_source_ledger_does_not_support",
            validate_m3_bundle(bundle)["errors"],
        )

    def test_source_ledger_required_lists_cannot_be_empty(self):
        for field in ("supports", "does_not_support", "limitations"):
            with self.subTest(field=field):
                bundle = make_valid_m3_bundle()
                bundle["method_cards"][0]["source_ledger"][0][field] = []
                self.assertIn(
                    f"empty_source_ledger_{field}",
                    validate_m3_bundle(bundle)["errors"],
                )

    def test_source_ledger_requires_support_types(self):
        bundle = make_valid_m3_bundle()
        del bundle["method_cards"][0]["source_ledger"][0]["support_types"]
        self.assertIn(
            "missing_source_ledger_support_types",
            validate_m3_bundle(bundle)["errors"],
        )

    def test_source_ledger_support_types_must_be_nonempty(self):
        bundle = make_valid_m3_bundle()
        bundle["method_cards"][0]["source_ledger"][0]["support_types"] = []
        self.assertIn(
            "empty_source_ledger_support_types",
            validate_m3_bundle(bundle)["errors"],
        )

    def test_source_ledger_support_types_are_closed(self):
        bundle = make_valid_m3_bundle()
        bundle["method_cards"][0]["source_ledger"][0]["support_types"] = [
            "method",
            "untyped_claim",
        ]
        self.assertIn(
            "invalid_source_ledger_support_type",
            validate_m3_bundle(bundle)["errors"],
        )

    def test_source_ledger_basis_level_must_match_candidate(self):
        bundle = make_valid_m3_bundle()
        bundle["method_cards"][0]["source_ledger"][0]["basis_level"] = "metadata"
        self.assertIn("source_ledger_basis_level_mismatch", validate_m3_bundle(bundle)["errors"])

    def test_closed_basis_mapping_covers_all_upstream_levels(self):
        self.assertEqual(
            {
                source_level: _m3_basis_level({"basis_level": source_level})
                for source_level in BASIS_LEVEL_MAP
            },
            {
                "metadata_level": "metadata",
                "abstract_level": "abstract",
                "fulltext_level": "full_text",
            },
        )

    def test_all_closed_basis_levels_match_embedded_candidates(self):
        bundle = _make_production_m3_bundle()
        source_m1 = bundle["source_m2_bundle"]["source_m1_bundle"]
        ledger_rows = []
        for candidate_id, source_level in (
            ("contract:P13", "metadata_level"),
            ("contract:P14", "abstract_level"),
            ("contract:P15", "fulltext_level"),
        ):
            for round_name in ("round1", "round2"):
                candidate = _candidate_by_id(source_m1, round_name, candidate_id)
                candidate["basis_level"] = source_level
                candidate["verified_record"]["basis_level"] = source_level
            ledger_rows.append(
                {
                    "source_id": f"source:{candidate_id}",
                    "candidate_id": candidate_id,
                    "basis_level": BASIS_LEVEL_MAP[source_level],
                    "support_types": (
                        ["bibliographic_identity"]
                        if source_level == "metadata_level"
                        else ["method"]
                    ),
                    "supports": ["Offline method-card structure"],
                    "does_not_support": ["Real method performance"],
                    "limitations": ["Synthetic contract record"],
                }
            )
        bundle["method_cards"][0]["source_ledger"] = ledger_rows
        _reconfirm_after_m1_change(bundle)
        self.assertEqual(validate_m3_bundle(bundle)["status"], "valid")

    def test_ineligible_source_is_rejected(self):
        bundle = _make_production_m3_bundle()
        for round_name in ("round1", "round2"):
            candidate = _candidate_by_id(
                bundle["source_m2_bundle"]["source_m1_bundle"],
                round_name,
                "contract:P15",
            )
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

    def test_minimum_resource_requires_finite_nonboolean_numeric_value(self):
        for value in NONFINITE_OR_BOOLEAN_VALUES:
            with self.subTest(value=value):
                bundle = make_valid_m3_bundle()
                bundle["method_cards"][0]["minimum_resources"][0][
                    "required_value"
                ] = value
                self.assertIn(
                    "invalid_minimum_resource_required_value",
                    validate_m3_bundle(bundle)["errors"],
                )

    def test_minimum_resource_unit_must_match_inherited_constraint(self):
        bundle = make_valid_m3_bundle()
        bundle["method_cards"][0]["minimum_resources"][0]["unit"] = "GiB"
        self.assertIn(
            "minimum_resource_unit_mismatch",
            validate_m3_bundle(bundle)["errors"],
        )

    def test_inherited_constraints_must_exactly_copy_selected_direction(self):
        bundle = make_valid_m3_bundle()
        bundle["method_cards"][0]["inherited_constraints"][0]["value"] = 3
        self.assertIn(
            "method_card_inherited_constraints_mismatch",
            validate_m3_bundle(bundle)["errors"],
        )

    def test_inherited_constraints_copy_is_type_strict(self):
        bundle = make_valid_m3_bundle()
        source = bundle["source_m2_bundle"]
        direction = _selected_direction(source)
        direction["resource_limits"][0]["value"] = 1
        _confirm_bundle(source)
        bundle["method_cards"][0]["inherited_constraints"] = copy.deepcopy(
            direction["resource_limits"]
        )
        _refresh_m3_hashes(bundle)
        bundle["method_cards"][0]["inherited_constraints"][0]["value"] = True
        self.assertIn(
            "method_card_inherited_constraints_mismatch",
            validate_m3_bundle(bundle)["errors"],
        )

    def test_duplicate_method_card_id_is_rejected(self):
        bundle = make_valid_m3_bundle()
        bundle["method_cards"].append(copy.deepcopy(bundle["method_cards"][0]))
        self.assertIn(
            "duplicate_method_card_id",
            validate_m3_bundle(bundle)["errors"],
        )

    def test_duplicate_supported_claim_type_is_rejected(self):
        bundle = make_valid_m3_bundle()
        supported = bundle["method_cards"][0]["applicability"][
            "supported_claim_types"
        ]
        supported.append(supported[0])
        self.assertIn(
            "duplicate_method_card_supported_claim_type",
            validate_m3_bundle(bundle)["errors"],
        )

    def test_duplicate_primary_metric_is_rejected(self):
        bundle = make_valid_m3_bundle()
        metrics = bundle["method_cards"][0]["primary_metrics"]
        metrics.append(metrics[0])
        self.assertIn(
            "duplicate_method_card_primary_metric",
            validate_m3_bundle(bundle)["errors"],
        )

    def test_duplicate_source_support_type_is_rejected(self):
        bundle = make_valid_m3_bundle()
        support_types = bundle["method_cards"][0]["source_ledger"][0][
            "support_types"
        ]
        support_types.append(support_types[0])
        self.assertIn(
            "duplicate_source_ledger_support_type",
            validate_m3_bundle(bundle)["errors"],
        )

    def test_duplicate_source_id_within_ledger_is_rejected(self):
        bundle = make_valid_m3_bundle()
        ledger = bundle["method_cards"][0]["source_ledger"]
        ledger.append(copy.deepcopy(ledger[0]))
        self.assertIn(
            "duplicate_source_ledger_source_id",
            validate_m3_bundle(bundle)["errors"],
        )

    def test_duplicate_domain_overlay_id_is_rejected(self):
        bundle = make_valid_m3_bundle()
        overlay = _nuclear_overlay()
        bundle["domain_overlays"] = [overlay, copy.deepcopy(overlay)]
        self.assertIn(
            "duplicate_domain_overlay_id",
            validate_m3_bundle(bundle)["errors"],
        )

    def test_duplicate_nuclear_base_card_id_is_rejected(self):
        bundle = make_valid_m3_bundle()
        overlay = _nuclear_overlay()
        overlay["base_card_ids"].append(overlay["base_card_ids"][0])
        bundle["domain_overlays"] = [overlay]
        self.assertIn(
            "duplicate_nuclear_overlay_base_card_id",
            validate_m3_bundle(bundle)["errors"],
        )

    def test_unknown_method_family_is_rejected(self):
        bundle = make_valid_m3_bundle()
        bundle["method_cards"][0]["method_family"] = "quantum_oracle"
        self.assertIn("unknown_method_family", validate_m3_bundle(bundle)["errors"])

    def test_closed_objects_reject_unknown_fields(self):
        cases = (
            ("top_level", "unknown_m3_bundle_fields"),
            ("method_card", "unknown_method_card_fields"),
            ("source_ledger", "unknown_source_ledger_fields"),
            ("domain_overlay", "unknown_domain_overlay_fields"),
        )
        for level, expected_error in cases:
            with self.subTest(level=level):
                bundle = make_valid_m3_bundle()
                overlay = _nuclear_overlay()
                bundle["domain_overlays"] = [overlay]
                targets = {
                    "top_level": bundle,
                    "method_card": bundle["method_cards"][0],
                    "source_ledger": bundle["method_cards"][0]["source_ledger"][0],
                    "domain_overlay": overlay,
                }
                targets[level]["unexpected_field"] = "must fail closed"
                self.assertIn(
                    expected_error,
                    validate_m3_bundle(bundle)["errors"],
                )

    def test_nested_closed_objects_reject_unknown_fields(self):
        cases = (
            ("applicability", "unknown_applicability_fields"),
            ("minimum_resource", "unknown_minimum_resource_fields"),
            ("criterion", "unknown_criterion_fields"),
        )
        for level, expected_error in cases:
            with self.subTest(level=level):
                bundle = make_valid_m3_bundle()
                card = bundle["method_cards"][0]
                targets = {
                    "applicability": card["applicability"],
                    "minimum_resource": card["minimum_resources"][0],
                    "criterion": card["stop_conditions"][0],
                }
                targets[level]["unexpected_field"] = "must fail closed"
                self.assertIn(
                    expected_error,
                    validate_m3_bundle(bundle)["errors"],
                )

    def test_nuclear_overlay_requires_existing_base_cards(self):
        bundle = make_valid_m3_bundle()
        overlay = _nuclear_overlay()
        overlay["base_card_ids"] = []
        bundle["domain_overlays"] = [overlay]
        self.assertIn("nuclear_overlay_missing_base_card", validate_m3_bundle(bundle)["errors"])

    def test_nuclear_overlay_rejects_unknown_nonempty_base_card(self):
        bundle = make_valid_m3_bundle()
        overlay = _nuclear_overlay()
        overlay["base_card_ids"] = ["card:unknown:1"]
        bundle["domain_overlays"] = [overlay]
        self.assertIn("nuclear_overlay_unknown_base_card", validate_m3_bundle(bundle)["errors"])

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
            candidate = _candidate_by_id(
                bundle["source_m2_bundle"]["source_m1_bundle"],
                round_name,
                "contract:P15",
            )
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

    def test_metadata_basis_cannot_support_result_claim(self):
        bundle = _make_production_m3_bundle()
        for round_name in ("round1", "round2"):
            candidate = _candidate_by_id(
                bundle["source_m2_bundle"]["source_m1_bundle"],
                round_name,
                "contract:P13",
            )
            candidate["basis_level"] = "metadata_level"
            candidate["verified_record"]["basis_level"] = "metadata_level"
        ledger = bundle["method_cards"][0]["source_ledger"][0]
        ledger["source_id"] = "source:contract:P13"
        ledger["candidate_id"] = "contract:P13"
        ledger["basis_level"] = "metadata"
        ledger["support_types"] = ["result"]
        ledger["supports"] = ["Observed endpoint statement"]
        _reconfirm_after_m1_change(bundle)
        self.assertIn(
            "metadata_basis_cannot_support_claim",
            validate_m3_bundle(bundle)["errors"],
        )

    def test_nuclear_safety_support_must_itself_be_non_preprint(self):
        bundle = _make_production_m3_bundle()
        for round_name in ("round1", "round2"):
            candidate = _candidate_by_id(
                bundle["source_m2_bundle"]["source_m1_bundle"],
                round_name,
                "contract:P15",
            )
            candidate["verification_status"] = "verified_preprint"
            candidate["verified_record"]["verification"]["status"] = (
                "verified_preprint"
            )
        _reconfirm_after_m1_change(bundle)
        overlay = _nuclear_overlay("contract:P15")
        overlay["source_ledger"].append(
            {
                "source_id": "source:contract:P14",
                "candidate_id": "contract:P14",
                "basis_level": "abstract",
                "support_types": ["bibliographic_identity"],
                "supports": ["Record identity"],
                "does_not_support": ["Safety-related method checks"],
                "limitations": ["Identity support only"],
            }
        )
        bundle["domain_overlays"] = [overlay]
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
