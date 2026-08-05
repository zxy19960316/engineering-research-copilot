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
        "feasibility_and_governance": [],
        "m1_citation_integrity": ["fixture:P01", "fixture:P04", "fixture:P09"],
    }
    return [
        {
            "gate_id": gate_id,
            "status": "pass",
            "evidence_candidate_ids": candidate_ids,
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
                "evidence": "Offline fixture score evidence",
                "confidence": "medium",
                "unknowns": ["Real direction merit was not evaluated"],
                "change_triggers": ["Target-domain decisive evidence"],
            }
            for dimension, weight in DIMENSION_WEIGHTS.items()
        ],
        "weighted_total": float(score * 20),
    }


def _decisive_test() -> dict:
    return {
        "hypothesis": "The candidate method beats the fixture baseline on the primary metric",
        "inputs": ["Frozen fixture input"],
        "baseline": "Frozen fixture baseline",
        "steps": ["Compare one bounded candidate against the baseline"],
        "primary_metric": "fixture_score",
        "success_threshold": _threshold("fixture_score", ">=", 0.8, "ratio"),
        "stop_condition": _threshold("fixture_cost", ">", 10.0, "fixture_units"),
        "pivot_condition": _threshold("fixture_score", "<", 0.6, "ratio"),
        "expected_time": "One offline fixture pass",
        "required_resources": ["Offline fixture data"],
    }


def _direction(
    direction_id: str,
    position: str,
    title: str,
    tier: str,
    score: int,
    axis_changes: list[dict],
) -> dict:
    return {
        "direction_id": direction_id,
        "position": position,
        "title": title,
        "evidence_tier": tier,
        "axis_changes": axis_changes,
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
        "minimum_decisive_test": _decisive_test(),
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
            "schema_version": "m2.1",
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


def _route_output() -> dict:
    return {
        "selected_direction_id": "D1",
        "hypothesis": "Confirmed fixture hypothesis",
        "baselines": ["Fixture baseline"],
        "controls": ["Fixture control"],
        "sequence": ["Run the bounded fixture sequence"],
        "inputs": ["Fixture input"],
        "outputs": ["Fixture output"],
        "controlled_variables": ["Fixture controlled variable"],
        "confounders": ["Fixture confounder"],
        "primary_metrics": ["Fixture primary metric"],
        "secondary_metrics": ["Fixture secondary metric"],
        "minimum_meaningful_improvement": "At least 0.1 fixture ratio",
        "uncertainty_checks": ["Fixture uncertainty check"],
        "sensitivity_checks": ["Fixture sensitivity check"],
        "validity_checks": ["Fixture validity check"],
        "go_conditions": ["Fixture success threshold passes"],
        "stop_conditions": ["Fixture stop threshold passes"],
        "pivot_conditions": ["Fixture pivot threshold passes"],
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
        test["success_threshold"] = "meaningful improvement"
        test["stop_condition"]["value"] = None
        errors = validate_bundle(bundle)["errors"]
        self.assertIn("invalid_success_threshold", errors)
        self.assertIn("invalid_stop_condition", errors)

    def test_high_risk_ideas_are_speculative_unranked_and_limited(self):
        bundle = make_valid_m2_bundle()
        idea = {
            "direction_id": "H1",
            "title": "Fixture high-risk idea",
            "evidence_tier": "transfer-supported",
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
        bundle["route_output"] = _route_output()
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
                bundle["direction_decision"] = {
                    "selected_direction_id": None,
                    "status": status,
                    "permitted_next_actions": actions,
                }
                self.assertEqual(validate_bundle(bundle)["status"], "valid")

    def test_selected_direction_before_confirmation_is_rejected(self):
        bundle = make_valid_m2_bundle()
        bundle["direction_decision"]["selected_direction_id"] = "D1"
        self.assertIn(
            "selected_direction_before_confirmation", validate_bundle(bundle)["errors"]
        )

    def test_confirmed_direction_can_open_gate_before_route_is_generated(self):
        bundle = make_valid_m2_bundle()
        bundle["direction_decision"] = {
            "selected_direction_id": "D1",
            "status": "user_confirmed",
            "permitted_next_actions": ["modify", "reject", "generate_route"],
        }
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
        bundle["direction_decision"] = {
            "selected_direction_id": "D1",
            "status": "user_confirmed",
            "permitted_next_actions": ["modify", "reject", "generate_route"],
        }
        bundle["route_output"] = _route_output()
        self.assertEqual(validate_bundle(bundle)["status"], "valid")

        bundle["direction_decision"]["selected_direction_id"] = "H1"
        self.assertIn("selected_direction_not_formal", validate_bundle(bundle)["errors"])

    def test_route_envelope_is_closed_and_complete(self):
        bundle = make_valid_m2_bundle()
        bundle["direction_decision"] = {
            "selected_direction_id": "D1",
            "status": "user_confirmed",
            "permitted_next_actions": ["modify", "reject", "generate_route"],
        }
        route = _route_output()
        route["model_download"] = "download now"
        route["controls"] = []
        bundle["route_output"] = route
        errors = validate_bundle(bundle)["errors"]
        self.assertIn("unknown_route_output_fields", errors)
        self.assertIn("empty_route_output_controls", errors)

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
