from __future__ import annotations

import copy
import hashlib
import json
import math
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

from test_validate_m1_bundle import make_complete_fixture_bundle  # noqa: E402
from validate_m2_direction_bundle import (  # noqa: E402
    canonical_sha256,
    validate_bundle,
)


DIMENSION_WEIGHTS = {
    "engineering_value": 15,
    "gap_and_evidence_quality": 15,
    "data_and_resource_fit": 20,
    "validation_and_falsifiability": 15,
    "method_maturity": 10,
    "time_to_decisive_signal": 10,
    "interdisciplinary_interface_quality": 10,
    "safety_ethics_compliance": 5,
}


def _threshold(metric: str, operator: str, value: float, unit: str) -> dict:
    return {
        "metric": metric,
        "operator": operator,
        "value": value,
        "unit": unit,
    }


def _hard_gates() -> list[dict]:
    evidence = {
        "target_problem_evidence": ["fixture:P01"],
        "data_availability": [],
        "falsifiability": [],
        "resource_feasibility": [],
        "time_feasibility": [],
        "safety_ethics_compliance": [],
        "m1_citation_integrity": ["fixture:P01", "fixture:P04", "fixture:P09"],
    }
    return [
        {
            "gate_id": gate_id,
            "status": "pass",
            "evidence_candidate_ids": candidate_ids,
            "required_precondition_ids": (
                ["data-preflight"] if gate_id == "data_availability" else []
            ),
            "rationale": f"Offline fixture rationale for {gate_id}",
            "blockers": [],
        }
        for gate_id, candidate_ids in evidence.items()
    ]


def _scorecard(score: int) -> dict:
    return {
        "dimensions": [
            {
                "dimension": dimension,
                "weight": weight,
                "score": score,
                "evidence_candidate_ids": ["fixture:P01"],
                "evidence": f"Offline fixture evidence specific to {dimension}",
                "confidence": "medium",
                "unknowns": [f"Real {dimension} merit was not evaluated"],
                "change_triggers": [f"Target-domain {dimension} evidence"],
            }
            for dimension, weight in DIMENSION_WEIGHTS.items()
        ],
        "weighted_total": float(score * 20),
    }


def _decisive_test(claims: list[dict]) -> dict:
    metrics = {
        metric["metric_id"]: metric
        for claim in claims
        for metric in claim["required_decision_metrics"]
    }
    return {
        "scope": "minimum_decisive_test",
        "hypothesis": "The candidate method beats the fixture baseline on the primary metric",
        "inputs": ["Frozen fixture input"],
        "baseline": "Frozen fixture baseline",
        "steps": [
            {
                "step_id": "S1",
                "action": "Run one bounded fixture comparison",
                "bounded_output": "One frozen prediction and uncertainty table",
            },
            {
                "step_id": "S2",
                "action": "Evaluate only preregistered decision metrics",
                "bounded_output": "One pass, stop, or pivot decision",
            },
        ],
        "primary_metric_id": next(iter(metrics)),
        "claim_coverage": [
            {
                "claim_id": claim["claim_id"],
                "metric_ids": [
                    metric["metric_id"] for metric in claim["required_decision_metrics"]
                ],
                "decision_criteria": [
                    {
                        "criterion_type": "success",
                        "metric_id": metric["metric_id"],
                        "operator": ">=",
                        "value": 0.8,
                        "unit": metric["unit"],
                    }
                    for metric in claim["required_decision_metrics"]
                ],
                "required_precondition_ids": (
                    ["data-preflight"]
                    if claim["claim_type"] == "data_availability"
                    else []
                ),
            }
            for claim in claims
        ],
        "required_preconditions": [
            {
                "precondition_id": "data-preflight",
                "description": "Fixture data are split without trajectory leakage",
                "gate_id": "data_availability",
                "status": "verified",
                "evidence_candidate_ids": ["fixture:P01"],
                "blocking_if_unresolved": True,
                "preflight_check": "Check split, count, labels, sampling rate, and horizon",
                "stop_condition": _threshold("eligible_trajectories", "<", 10, "count"),
            }
        ],
        "expected_time": "One offline fixture pass",
        "required_resources": ["Offline fixture data"],
    }


def _claims(position: str) -> list[dict]:
    claims = [
        {
            "claim_id": "C-PRED",
            "claim": "The direction can improve bounded predictive performance",
            "claim_type": "predictive_performance",
            "evidence_candidate_ids": ["fixture:P01", "fixture:P04"],
            "required_decision_metrics": [
                {
                    "metric_id": "M-PRED",
                    "metric": "Fixture predictive score",
                    "metric_role": "predictive_performance",
                    "unit": "ratio",
                }
            ],
        }
    ]
    if position == "provisional_main":
        claims.append(
            {
                "claim_id": "C-UQ",
                "claim": "The direction can produce calibrated uncertainty",
                "claim_type": "uncertainty_quality",
                "evidence_candidate_ids": ["fixture:P04"],
                "required_decision_metrics": [
                    {
                        "metric_id": "M-UQ",
                        "metric": "Fixture calibration error",
                        "metric_role": "uncertainty_quality",
                        "unit": "ratio",
                    }
                ],
            }
        )
    if position == "transfer_exploration":
        claims.append(
            {
                "claim_id": "C-OOD",
                "claim": "The direction can distinguish an open-set fixture",
                "claim_type": "open_set_detection",
                "evidence_candidate_ids": ["fixture:P04"],
                "required_decision_metrics": [
                    {
                        "metric_id": "M-OOD",
                        "metric": "Fixture open-set detection rate",
                        "metric_role": "open_set_detection",
                        "unit": "ratio",
                    }
                ],
            }
        )
    return claims


def _axis_profile(position: str) -> dict:
    profiles = {
        "provisional_main": {
            "problem": "fixture problem A",
            "method": "fixture method A",
            "data": "fixture data A",
        },
        "adjacent_alternative": {
            "problem": "fixture problem A",
            "method": "fixture method B",
            "data": "fixture data A",
        },
        "transfer_exploration": {
            "problem": "fixture problem A",
            "method": "fixture method C",
            "data": "fixture data B",
        },
    }
    return profiles[position]


def _direction(
    direction_id: str,
    position: str,
    title: str,
    tier: str,
    score: int,
    axis_changes: list[dict],
) -> dict:
    claims = _claims(position)
    return {
        "direction_id": direction_id,
        "position": position,
        "title": title,
        "evidence_tier": tier,
        "claim_language": {
            "established-in-target": "Direct evidence supports applicability",
            "transfer-supported": "Recommended for priority validation",
            "mechanism-plausible": "Divergent exploration suggestion",
        }[tier],
        "axis_profile": _axis_profile(position),
        "axis_changes": axis_changes,
        "core_claims": claims,
        "resource_limits": [
            {
                "constraint_id": "R-CPU-HOURS",
                "resource": "CPU time",
                "operator": "<=",
                "value": 2,
                "unit": "hours",
            }
        ],
        "hard_gates": _hard_gates(),
        "transfer_case": {
            "target_problem_evidence": ["fixture:P01"],
            "source_success_evidence": ["fixture:P04"],
            "transfer_compatibility": {
                "concepts": ["fixture concept mapping"],
                "units": ["fixture unit mapping"],
                "scales": ["fixture scale mapping"],
                "boundary_conditions": ["fixture boundary mapping"],
                "assumptions": ["fixture assumption mapping"],
            },
            "anti_transfer_factors": ["Fixture domain shift"],
        },
        "scorecard": _scorecard(score),
        "minimum_decisive_test": _decisive_test(claims),
        "supporting_candidate_ids": ["fixture:P01", "fixture:P04"],
        "counter_candidate_ids": ["fixture:P09"],
        "unknowns": ["Real-world transfer remains untested"],
        "confidence": "medium" if tier == "transfer-supported" else "low",
        "recommendation_status": "provisional",
    }


def make_valid_m2_bundle() -> dict:
    source = make_complete_fixture_bundle()
    directions = [
        _direction(
            "D1",
            "provisional_main",
            "Fixture main direction",
            "transfer-supported",
            4,
            [],
        ),
        _direction(
            "D2",
            "adjacent_alternative",
            "Fixture adjacent direction",
            "established-in-target",
            3,
            [
                {
                    "axis": "method",
                    "from": "fixture method A",
                    "to": "fixture method B",
                }
            ],
        ),
        _direction(
            "D3",
            "transfer_exploration",
            "Fixture transfer direction",
            "mechanism-plausible",
            2,
            [
                {
                    "axis": "method",
                    "from": "fixture method A",
                    "to": "fixture method C",
                },
                {
                    "axis": "data",
                    "from": "fixture data A",
                    "to": "fixture data B",
                },
            ],
        ),
    ]
    return {
        "source_m1_bundle": source,
        "direction_portfolio": {
            "schema_version": "m2.1.1",
            "source_m1_terminal_state": "M1_COMPLETE",
            "source_m1_bundle_hash": canonical_sha256(source),
            "brief_version": 2,
            "branch_id": "branch-a",
            "directions": directions,
            "high_risk_ideas": [],
            "portfolio_status": "provisional",
        },
        "direction_decision": {
            "selected_direction_id": None,
            "status": "waiting_for_user_confirmation",
            "permitted_next_actions": ["confirm", "modify", "reject"],
            "confirmation_event": None,
        },
        "route_output": None,
        "fixture_mode": True,
        "evidence_class": "offline_contract_fixture",
        "proves": ["M2 structural contract behavior"],
        "does_not_prove": ["Real direction merit or citation accuracy"],
    }


def _refresh_hash(bundle: dict) -> None:
    bundle["direction_portfolio"]["source_m1_bundle_hash"] = canonical_sha256(
        bundle["source_m1_bundle"]
    )


def _set_nonconfirmed_decision(bundle: dict, status: str) -> None:
    actions = {
        "direction_evidence_incomplete": ["modify", "reject"],
        "waiting_for_user_confirmation": ["confirm", "modify", "reject"],
        "modification_requested": ["modify", "reject"],
        "rejected": ["modify"],
    }
    bundle["direction_decision"] = {
        "selected_direction_id": None,
        "status": status,
        "permitted_next_actions": actions[status],
        "confirmation_event": None,
    }


def _preconfirmation_hash(bundle: dict) -> str:
    prior = copy.deepcopy(bundle)
    _set_nonconfirmed_decision(prior, "waiting_for_user_confirmation")
    prior["route_output"] = None
    return canonical_sha256(prior)


def _confirm_bundle(bundle: dict, direction_id: str = "D1") -> None:
    excerpt = f"I explicitly confirm formal direction {direction_id}."
    event = {
        "actor_role": "user",
        "selected_direction_id": direction_id,
        "source_message_id": f"message:confirm-{direction_id.lower()}",
        "source_message_excerpt": excerpt,
        "source_message_sha256": hashlib.sha256(excerpt.encode("utf-8")).hexdigest(),
        "previous_bundle_hash": _preconfirmation_hash(bundle),
    }
    bundle["direction_decision"] = {
        "selected_direction_id": direction_id,
        "status": "user_confirmed",
        "permitted_next_actions": ["modify", "reject", "generate_route"],
        "confirmation_event": event,
    }


def _confirmed_bundle_hash(bundle: dict) -> str:
    confirmed = copy.deepcopy(bundle)
    confirmed["route_output"] = None
    return canonical_sha256(confirmed)


def _route_output(bundle: dict) -> dict:
    direction = bundle["direction_portfolio"]["directions"][0]
    event = bundle["direction_decision"]["confirmation_event"]
    all_metric_ids = [
        metric["metric_id"]
        for claim in direction["core_claims"]
        for metric in claim["required_decision_metrics"]
    ]
    coverage = direction["minimum_decisive_test"]["claim_coverage"]
    return {
        "selected_direction_id": "D1",
        "source_direction_hash": canonical_sha256(direction),
        "confirmation_event_hash": canonical_sha256(event),
        "source_bundle_hash": _confirmed_bundle_hash(bundle),
        "hypothesis": "Confirmed fixture hypothesis",
        "baselines": ["Fixture baseline"],
        "controls": ["Fixture control"],
        "sequence": ["Run the bounded fixture sequence"],
        "inputs": ["Fixture input"],
        "outputs": ["Fixture output"],
        "controlled_variables": ["Fixture controlled variable"],
        "confounders": ["Fixture confounder"],
        "primary_metrics": all_metric_ids,
        "secondary_metrics": ["M-COST"],
        "minimum_meaningful_improvement": "At least 0.1 fixture ratio",
        "uncertainty_checks": ["Fixture uncertainty check"],
        "sensitivity_checks": ["Fixture sensitivity check"],
        "validity_checks": ["Fixture validity check"],
        "go_conditions": [item["decision_criteria"][0] for item in coverage],
        "stop_conditions": [
            {
                "criterion_type": "stop",
                "metric_id": "M-COST",
                "operator": ">",
                "value": 2,
                "unit": "hours",
            }
        ],
        "pivot_conditions": [
            {
                "criterion_type": "pivot",
                "metric_id": all_metric_ids[0],
                "operator": "<",
                "value": 0.6,
                "unit": "ratio",
            }
        ],
        "route_traceability": [
            {
                "claim_id": claim["claim_id"],
                "route_metric_ids": [
                    metric["metric_id"] for metric in claim["required_decision_metrics"]
                ],
                "source_precondition_ids": next(
                    item["required_precondition_ids"]
                    for item in coverage
                    if item["claim_id"] == claim["claim_id"]
                ),
                "route_condition_types": ["go", "stop", "pivot"],
            }
            for claim in direction["core_claims"]
        ],
        "source_test_mapping": [
            {
                "claim_id": claim["claim_id"],
                "minimum_test_metric_ids": [
                    metric["metric_id"] for metric in claim["required_decision_metrics"]
                ],
                "route_metric_ids": [
                    metric["metric_id"] for metric in claim["required_decision_metrics"]
                ],
            }
            for claim in direction["core_claims"]
        ],
        "inherited_constraints": copy.deepcopy(direction["resource_limits"]),
        "approved_constraint_changes": [],
        "evidence_chain": {
            "design": ["Fixture design evidence"],
            "data": ["Fixture data evidence"],
            "analysis": ["Fixture analysis evidence"],
            "result": ["Fixture result evidence"],
            "claim": ["Fixture claim boundary"],
        },
    }


class ValidateM2DirectionBundleTests(unittest.TestCase):
    def test_valid_waiting_portfolio_returns_valid(self):
        result = validate_bundle(make_valid_m2_bundle())
        self.assertEqual(result, {"status": "valid", "errors": [], "evidence_gaps": []})

    def test_source_hash_must_match_verbatim_m1_bundle(self):
        bundle = make_valid_m2_bundle()
        bundle["direction_portfolio"]["source_m1_bundle_hash"] = "0" * 64
        self.assertIn("source_m1_bundle_hash_mismatch", validate_bundle(bundle)["errors"])

    def test_m1_incomplete_cannot_be_upgraded_to_direction_ready(self):
        bundle = make_valid_m2_bundle()
        bundle["source_m1_bundle"]["terminal_state"] = "WAITING_FOR_EVIDENCE_DECISION"
        bundle["source_m1_bundle"]["outcome"] = "evidence_incomplete"
        _refresh_hash(bundle)
        errors = validate_bundle(bundle)["errors"]
        self.assertIn("source_m1_not_complete", errors)

    def test_portfolio_must_copy_round_two_brief_and_branch(self):
        bundle = make_valid_m2_bundle()
        bundle["direction_portfolio"]["brief_version"] = 3
        bundle["direction_portfolio"]["branch_id"] = "branch-invented"
        errors = validate_bundle(bundle)["errors"]
        self.assertIn("m1_brief_version_mismatch", errors)
        self.assertIn("m1_branch_id_mismatch", errors)

    def test_unknown_supporting_id_is_rejected(self):
        bundle = make_valid_m2_bundle()
        bundle["direction_portfolio"]["directions"][0]["supporting_candidate_ids"] = [
            "fixture:UNKNOWN"
        ]
        self.assertIn("unknown_m1_candidate_id", validate_bundle(bundle)["errors"])

    def test_blocked_m1_candidate_cannot_support_direction(self):
        bundle = make_valid_m2_bundle()
        candidate = bundle["source_m1_bundle"]["round2"]["candidate_pool"][14]
        candidate["verification_status"] = "conflicted"
        candidate["recommendation_eligible"] = False
        candidate["verified_record"]["verification"]["status"] = "conflicted"
        candidate["verified_record"]["verification"]["recommendation_eligible"] = False
        candidate["verified_record"]["verification"]["blocking_reasons"] = [
            "Fixture conflict"
        ]
        bundle["direction_portfolio"]["directions"][0]["supporting_candidate_ids"] = [
            "fixture:P15"
        ]
        _refresh_hash(bundle)
        self.assertIn("blocked_m1_candidate", validate_bundle(bundle)["errors"])

    def test_hard_gate_failure_cannot_keep_score_or_ranking(self):
        bundle = make_valid_m2_bundle()
        direction = bundle["direction_portfolio"]["directions"][0]
        direction["hard_gates"][0]["status"] = "fail"
        direction["hard_gates"][0]["blockers"] = ["No target evidence"]
        direction["scorecard"]["weighted_total"] = 100.0
        errors = validate_bundle(bundle)["errors"]
        self.assertIn("failed_hard_gate_has_scorecard", errors)
        self.assertIn("failed_hard_gate_ranked", errors)
        self.assertIn("incomplete_portfolio_marked_provisional", errors)

    def test_honest_hard_gate_failure_returns_evidence_incomplete(self):
        bundle = make_valid_m2_bundle()
        direction = bundle["direction_portfolio"]["directions"][0]
        direction["hard_gates"][0]["status"] = "fail"
        direction["hard_gates"][0]["blockers"] = ["No target evidence"]
        direction["scorecard"] = None
        direction["recommendation_status"] = "excluded"
        bundle["direction_portfolio"]["portfolio_status"] = "evidence_incomplete"
        bundle["direction_decision"] = {
            "selected_direction_id": None,
            "status": "direction_evidence_incomplete",
            "permitted_next_actions": ["modify", "reject"],
            "confirmation_event": None,
        }
        result = validate_bundle(bundle)
        self.assertEqual(result["status"], "evidence_incomplete")
        self.assertEqual(result["errors"], [])
        self.assertIn("target_problem_evidence", result["evidence_gaps"])

    def test_speculative_direction_cannot_be_formal_main(self):
        bundle = make_valid_m2_bundle()
        bundle["direction_portfolio"]["directions"][0]["evidence_tier"] = "speculative"
        self.assertIn("invalid_tier_for_formal_position", validate_bundle(bundle)["errors"])

    def test_mechanism_plausible_cannot_be_formal_main(self):
        bundle = make_valid_m2_bundle()
        bundle["direction_portfolio"]["directions"][0][
            "evidence_tier"
        ] = "mechanism-plausible"
        self.assertIn("invalid_tier_for_formal_position", validate_bundle(bundle)["errors"])

    def test_transfer_supported_main_confidence_cannot_be_high(self):
        bundle = make_valid_m2_bundle()
        bundle["direction_portfolio"]["directions"][0]["confidence"] = "high"
        self.assertIn("transfer_supported_confidence_too_high", validate_bundle(bundle)["errors"])

    def test_evidence_tier_is_bound_to_exact_allowed_language(self):
        bundle = make_valid_m2_bundle()
        bundle["direction_portfolio"]["directions"][0][
            "claim_language"
        ] = "Established and ready to deploy"
        self.assertIn(
            "evidence_tier_language_mismatch", validate_bundle(bundle)["errors"]
        )

    def test_formal_positions_and_ids_are_unique_and_closed(self):
        bundle = make_valid_m2_bundle()
        bundle["direction_portfolio"]["directions"][1]["direction_id"] = "D1"
        bundle["direction_portfolio"]["directions"][1]["position"] = "provisional_main"
        errors = validate_bundle(bundle)["errors"]
        self.assertIn("duplicate_direction_id", errors)
        self.assertIn("invalid_formal_positions", errors)

    def test_adjacent_and_transfer_directions_change_meaningful_axes(self):
        bundle = make_valid_m2_bundle()
        bundle["direction_portfolio"]["directions"][1]["axis_changes"] = []
        bundle["direction_portfolio"]["directions"][2]["axis_changes"] = [
            {
                "axis": "method",
                "from": "fixture method A",
                "to": "fixture method A",
            }
        ]
        errors = validate_bundle(bundle)["errors"]
        self.assertIn("adjacent_requires_one_axis_change", errors)
        self.assertIn("transfer_requires_two_axis_changes", errors)
        self.assertIn("axis_change_has_no_change", errors)

    def test_transfer_case_requires_anti_transfer_and_all_boundaries(self):
        bundle = make_valid_m2_bundle()
        transfer = bundle["direction_portfolio"]["directions"][0]["transfer_case"]
        transfer["anti_transfer_factors"] = []
        transfer["transfer_compatibility"]["units"] = []
        errors = validate_bundle(bundle)["errors"]
        self.assertIn("missing_anti_transfer_factors", errors)
        self.assertIn("missing_transfer_compatibility_units", errors)

    def test_scorecard_weights_scores_and_total_are_recomputed(self):
        bundle = make_valid_m2_bundle()
        dimension = bundle["direction_portfolio"]["directions"][0]["scorecard"][
            "dimensions"
        ][0]
        dimension["score"] = 6
        dimension["weight"] = 14
        bundle["direction_portfolio"]["directions"][0]["scorecard"][
            "weighted_total"
        ] = math.nan
        errors = validate_bundle(bundle)["errors"]
        self.assertIn("score_out_of_range", errors)
        self.assertIn("scorecard_weights_do_not_total_100", errors)
        self.assertIn("invalid_weighted_total", errors)

    def test_decisive_test_requires_numeric_falsifiable_thresholds(self):
        bundle = make_valid_m2_bundle()
        test = bundle["direction_portfolio"]["directions"][0][
            "minimum_decisive_test"
        ]
        test["claim_coverage"][0]["decision_criteria"] = "meaningful improvement"
        test["required_preconditions"][0]["stop_condition"]["value"] = None
        errors = validate_bundle(bundle)["errors"]
        self.assertIn("invalid_claim_decision_criteria", errors)
        self.assertIn("invalid_precondition_stop_condition", errors)

    def test_high_risk_ideas_are_speculative_unranked_and_limited(self):
        bundle = make_valid_m2_bundle()
        idea = {
            "direction_id": "H1",
            "title": "Fixture high-risk idea",
            "evidence_tier": "transfer-supported",
            "claim_language": "Recommended for priority validation",
            "supporting_candidate_ids": ["fixture:P01"],
            "unknowns": ["Everything important"],
            "recommendation_status": "provisional",
        }
        bundle["direction_portfolio"]["high_risk_ideas"] = [
            copy.deepcopy(idea),
            copy.deepcopy(idea),
            copy.deepcopy(idea),
        ]
        errors = validate_bundle(bundle)["errors"]
        self.assertIn("too_many_high_risk_ideas", errors)
        self.assertIn("invalid_high_risk_idea", errors)

    def test_waiting_decision_blocks_route_output(self):
        bundle = make_valid_m2_bundle()
        _confirm_bundle(bundle)
        route = _route_output(bundle)
        _set_nonconfirmed_decision(bundle, "waiting_for_user_confirmation")
        bundle["route_output"] = route
        self.assertIn("route_output_before_user_confirmation", validate_bundle(bundle)["errors"])

    def test_nonconfirmed_transition_table_keeps_route_closed(self):
        cases = {
            "waiting_for_user_confirmation": ["confirm", "modify", "reject"],
            "modification_requested": ["modify", "reject"],
            "rejected": ["modify"],
        }
        for status, actions in cases.items():
            with self.subTest(status=status):
                bundle = make_valid_m2_bundle()
                _set_nonconfirmed_decision(bundle, status)
                self.assertEqual(bundle["direction_decision"]["permitted_next_actions"], actions)
                self.assertEqual(validate_bundle(bundle)["status"], "valid")

    def test_selected_direction_before_confirmation_is_rejected(self):
        bundle = make_valid_m2_bundle()
        bundle["direction_decision"]["selected_direction_id"] = "D1"
        self.assertIn(
            "selected_direction_before_confirmation", validate_bundle(bundle)["errors"]
        )

    def test_confirmed_direction_can_open_gate_before_route_is_generated(self):
        bundle = make_valid_m2_bundle()
        _confirm_bundle(bundle)
        self.assertIsNone(bundle["route_output"])
        self.assertEqual(validate_bundle(bundle)["status"], "valid")

    def test_preconfirmation_prohibited_route_keys_are_rejected_at_any_depth(self):
        for location in ("root", "direction"):
            with self.subTest(location=location):
                bundle = make_valid_m2_bundle()
                if location == "root":
                    bundle["training_plan"] = {"epochs": 100}
                else:
                    bundle["direction_portfolio"]["directions"][0][
                        "service_deployment"
                    ] = ["start service"]
                self.assertIn(
                    "prohibited_route_content_before_user_confirmation",
                    validate_bundle(bundle)["errors"],
                )

    def test_only_explicit_confirmed_formal_id_opens_route_gate(self):
        bundle = make_valid_m2_bundle()
        _confirm_bundle(bundle)
        bundle["route_output"] = _route_output(bundle)
        self.assertEqual(validate_bundle(bundle)["status"], "valid")

        bundle["direction_decision"]["selected_direction_id"] = "H1"
        self.assertIn("selected_direction_not_formal", validate_bundle(bundle)["errors"])

    def test_route_envelope_is_closed_and_complete(self):
        bundle = make_valid_m2_bundle()
        _confirm_bundle(bundle)
        route = _route_output(bundle)
        route["model_download"] = "download now"
        route["controls"] = []
        bundle["route_output"] = route
        errors = validate_bundle(bundle)["errors"]
        self.assertIn("unknown_route_output_fields", errors)
        self.assertIn("empty_route_output_controls", errors)

    def test_user_confirmed_requires_a_complete_confirmation_event(self):
        bundle = make_valid_m2_bundle()
        bundle["direction_decision"] = {
            "selected_direction_id": "D1",
            "status": "user_confirmed",
            "permitted_next_actions": ["modify", "reject", "generate_route"],
            "confirmation_event": None,
        }
        self.assertIn(
            "confirmed_without_confirmation_event", validate_bundle(bundle)["errors"]
        )

    def test_confirmation_event_actor_must_be_user(self):
        bundle = make_valid_m2_bundle()
        _confirm_bundle(bundle)
        bundle["direction_decision"]["confirmation_event"]["actor_role"] = "assistant"
        self.assertIn("confirmation_actor_not_user", validate_bundle(bundle)["errors"])

    def test_confirmation_event_direction_must_match_decision(self):
        bundle = make_valid_m2_bundle()
        _confirm_bundle(bundle)
        bundle["direction_decision"]["confirmation_event"]["selected_direction_id"] = "D2"
        self.assertIn("confirmation_direction_mismatch", validate_bundle(bundle)["errors"])

    def test_confirmation_event_must_bind_exact_preconfirmation_bundle(self):
        bundle = make_valid_m2_bundle()
        _confirm_bundle(bundle)
        bundle["direction_decision"]["confirmation_event"]["previous_bundle_hash"] = "0" * 64
        self.assertIn("confirmation_previous_bundle_hash_mismatch", validate_bundle(bundle)["errors"])

    def test_confirmation_source_message_must_explicitly_name_formal_id(self):
        bundle = make_valid_m2_bundle()
        _confirm_bundle(bundle)
        event = bundle["direction_decision"]["confirmation_event"]
        event["source_message_excerpt"] = "I confirm the recommended option."
        event["source_message_sha256"] = hashlib.sha256(
            event["source_message_excerpt"].encode("utf-8")
        ).hexdigest()
        self.assertIn(
            "confirmation_message_missing_explicit_direction_id",
            validate_bundle(bundle)["errors"],
        )

    def test_confirmation_source_message_hash_must_match_excerpt(self):
        bundle = make_valid_m2_bundle()
        _confirm_bundle(bundle)
        bundle["direction_decision"]["confirmation_event"]["source_message_sha256"] = "0" * 64
        self.assertIn("confirmation_message_hash_mismatch", validate_bundle(bundle)["errors"])

    def test_nonconfirmed_state_cannot_carry_confirmation_event(self):
        bundle = make_valid_m2_bundle()
        _confirm_bundle(bundle)
        event = bundle["direction_decision"]["confirmation_event"]
        _set_nonconfirmed_decision(bundle, "waiting_for_user_confirmation")
        bundle["direction_decision"]["confirmation_event"] = event
        self.assertIn("confirmation_event_before_confirmation", validate_bundle(bundle)["errors"])

    def test_confirmation_rejects_high_risk_or_unknown_id(self):
        for direction_id in ("H1", "D99"):
            with self.subTest(direction_id=direction_id):
                bundle = make_valid_m2_bundle()
                _confirm_bundle(bundle, direction_id)
                self.assertIn("selected_direction_not_formal", validate_bundle(bundle)["errors"])

    def test_route_binds_direction_event_and_confirmed_bundle_hashes(self):
        bundle = make_valid_m2_bundle()
        _confirm_bundle(bundle)
        route = _route_output(bundle)
        bundle["route_output"] = route
        for field, error in (
            ("source_direction_hash", "route_source_direction_hash_mismatch"),
            ("confirmation_event_hash", "route_confirmation_event_hash_mismatch"),
            ("source_bundle_hash", "route_source_bundle_hash_mismatch"),
        ):
            with self.subTest(field=field):
                changed = copy.deepcopy(bundle)
                changed["route_output"][field] = "0" * 64
                self.assertIn(error, validate_bundle(changed)["errors"])

    def test_d2_route_cannot_be_relabelled_as_d1(self):
        bundle = make_valid_m2_bundle()
        _confirm_bundle(bundle)
        route = _route_output(bundle)
        route["source_direction_hash"] = canonical_sha256(
            bundle["direction_portfolio"]["directions"][1]
        )
        bundle["route_output"] = route
        self.assertIn("route_source_direction_hash_mismatch", validate_bundle(bundle)["errors"])

    def test_route_must_cover_every_core_claim_and_inherit_resource_limits(self):
        bundle = make_valid_m2_bundle()
        _confirm_bundle(bundle)
        route = _route_output(bundle)
        route["route_traceability"] = route["route_traceability"][:1]
        route["inherited_constraints"][0]["value"] = 20
        bundle["route_output"] = route
        errors = validate_bundle(bundle)["errors"]
        self.assertIn("route_missing_claim_traceability", errors)
        self.assertIn("route_inherited_constraints_mismatch", errors)

    def test_route_cannot_bind_stale_confirmed_bundle(self):
        bundle = make_valid_m2_bundle()
        _confirm_bundle(bundle)
        bundle["route_output"] = _route_output(bundle)
        bundle["direction_portfolio"]["directions"][0]["unknowns"].append(
            "A new unresolved limitation"
        )
        self.assertIn("route_source_bundle_hash_mismatch", validate_bundle(bundle)["errors"])

    def test_minimum_decisive_test_rejects_full_route_shapes_and_size(self):
        bundle = make_valid_m2_bundle()
        test = bundle["direction_portfolio"]["directions"][0]["minimum_decisive_test"]
        test["steps"][0]["action"] = "x" * 1000
        test["steps"][1]["bounded_output"] = {"route_output": {"sequence": []}}
        test["steps"].extend(copy.deepcopy(test["steps"][0]) for _ in range(3))
        errors = validate_bundle(bundle)["errors"]
        self.assertIn("decisive_test_step_too_large", errors)
        self.assertIn("invalid_decisive_test_step", errors)
        self.assertIn("invalid_decisive_test_step_count", errors)

    def test_every_core_claim_requires_numeric_metric_coverage(self):
        bundle = make_valid_m2_bundle()
        test = bundle["direction_portfolio"]["directions"][0]["minimum_decisive_test"]
        test["claim_coverage"] = test["claim_coverage"][:1]
        self.assertIn("core_claim_without_test_coverage", validate_bundle(bundle)["errors"])

    def test_uq_and_ood_claims_require_semantically_typed_metrics(self):
        bundle = make_valid_m2_bundle()
        main_uq = bundle["direction_portfolio"]["directions"][0]["core_claims"][1]
        main_uq["required_decision_metrics"][0]["metric_role"] = "predictive_performance"
        transfer_ood = bundle["direction_portfolio"]["directions"][2]["core_claims"][1]
        transfer_ood["required_decision_metrics"][0]["metric_role"] = "predictive_performance"
        errors = validate_bundle(bundle)["errors"]
        self.assertIn("uncertainty_claim_requires_uncertainty_metric", errors)
        self.assertIn("open_set_claim_requires_open_set_metric", errors)

    def test_main_direction_cannot_be_supported_only_by_preprints(self):
        bundle = make_valid_m2_bundle()
        for candidate in bundle["source_m1_bundle"]["round2"]["candidate_pool"]:
            if candidate["candidate_id"] in {"fixture:P01", "fixture:P04"}:
                candidate["verification_status"] = "verified_preprint"
                candidate["verified_record"]["verification"]["status"] = "verified_preprint"
        _refresh_hash(bundle)
        self.assertIn(
            "provisional_main_requires_non_preprint_support",
            validate_bundle(bundle)["errors"],
        )

    def test_safety_gate_cannot_be_supported_only_by_preprints(self):
        bundle = make_valid_m2_bundle()
        main = bundle["direction_portfolio"]["directions"][0]
        safety = next(gate for gate in main["hard_gates"] if gate["gate_id"] == "safety_ethics_compliance")
        safety["evidence_candidate_ids"] = ["fixture:P01"]
        candidate = bundle["source_m1_bundle"]["round2"]["candidate_pool"][0]
        candidate["verification_status"] = "verified_preprint"
        candidate["verified_record"]["verification"]["status"] = "verified_preprint"
        _refresh_hash(bundle)
        self.assertIn(
            "safety_gate_requires_non_preprint_support",
            validate_bundle(bundle)["errors"],
        )

    def test_unresolved_material_precondition_cannot_pass_hard_gate(self):
        bundle = make_valid_m2_bundle()
        precondition = bundle["direction_portfolio"]["directions"][0][
            "minimum_decisive_test"
        ]["required_preconditions"][0]
        precondition["status"] = "unresolved"
        self.assertIn(
            "unresolved_blocking_precondition_passed_gate",
            validate_bundle(bundle)["errors"],
        )

    def test_axis_changes_are_derived_from_common_main_profile(self):
        bundle = make_valid_m2_bundle()
        adjacent = bundle["direction_portfolio"]["directions"][1]
        adjacent["axis_profile"] = copy.deepcopy(
            bundle["direction_portfolio"]["directions"][0]["axis_profile"]
        )
        adjacent["axis_changes"][0]["from"] = "invented baseline"
        errors = validate_bundle(bundle)["errors"]
        self.assertIn("adjacent_requires_one_axis_change", errors)
        self.assertIn("axis_changes_do_not_match_profiles", errors)

    def test_duplicate_scorecard_rationales_are_rejected(self):
        bundle = make_valid_m2_bundle()
        dimensions = bundle["direction_portfolio"]["directions"][0]["scorecard"]["dimensions"]
        for item in dimensions:
            item["evidence"] = "Same evidence"
            item["unknowns"] = ["Same unknown"]
            item["change_triggers"] = ["Same trigger"]
        self.assertIn("duplicate_score_dimension_rationale", validate_bundle(bundle)["errors"])

    def test_malformed_shapes_fail_closed_without_exception(self):
        malformed = [None, [], "bundle", {"source_m1_bundle": []}]
        for payload in malformed:
            with self.subTest(payload=payload):
                result = validate_bundle(payload)
                self.assertEqual(result["status"], "invalid")
                self.assertEqual(set(result), {"status", "errors", "evidence_gaps"})


class ValidateM2DirectionBundleCliTests(unittest.TestCase):
    def test_cli_emits_one_json_line_and_closed_exit_codes(self):
        script = SCRIPTS_DIR / "validate_m2_direction_bundle.py"
        valid = make_valid_m2_bundle()
        invalid = make_valid_m2_bundle()
        invalid["direction_portfolio"]["schema_version"] = "m2.0"
        incomplete = make_valid_m2_bundle()
        direction = incomplete["direction_portfolio"]["directions"][0]
        direction["hard_gates"][0]["status"] = "fail"
        direction["hard_gates"][0]["blockers"] = ["No target evidence"]
        direction["scorecard"] = None
        direction["recommendation_status"] = "excluded"
        incomplete["direction_portfolio"]["portfolio_status"] = "evidence_incomplete"
        incomplete["direction_decision"] = {
            "selected_direction_id": None,
            "status": "direction_evidence_incomplete",
            "permitted_next_actions": ["modify", "reject"],
            "confirmation_event": None,
        }
        with tempfile.TemporaryDirectory() as directory:
            completed = []
            for name, payload in (
                ("valid", valid),
                ("invalid", invalid),
                ("incomplete", incomplete),
            ):
                path = Path(directory) / f"{name}.json"
                path.write_text(json.dumps(payload, allow_nan=False), encoding="utf-8")
                completed.append(
                    subprocess.run(
                        [sys.executable, str(script), str(path)],
                        check=False,
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                    )
                )
        self.assertEqual([item.returncode for item in completed], [0, 1, 2])
        for item in completed:
            self.assertEqual(item.stderr, "")
            self.assertEqual(len(item.stdout.strip().splitlines()), 1)
            self.assertEqual(
                set(json.loads(item.stdout)),
                {"status", "errors", "evidence_gaps"},
            )


class CanonicalHashTests(unittest.TestCase):
    def test_hash_is_key_order_independent_and_rejects_nonfinite_numbers(self):
        self.assertEqual(canonical_sha256({"b": 1, "a": 2}), canonical_sha256({"a": 2, "b": 1}))
        with self.assertRaises(ValueError):
            canonical_sha256({"value": math.nan})


if __name__ == "__main__":
    unittest.main()
