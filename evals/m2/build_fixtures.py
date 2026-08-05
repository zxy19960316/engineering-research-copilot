#!/usr/bin/env python3
"""Build deterministic offline-only M2 adversarial fixture bundles."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "skills" / "engineering-research-copilot" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from validate_m2_direction_bundle import canonical_sha256  # noqa: E402


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
    return {"metric": metric, "operator": operator, "value": value, "unit": unit}


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
            "rationale": f"Offline contract rationale for {gate_id}",
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
                "evidence": "Offline contract score evidence",
                "confidence": "medium",
                "unknowns": ["Real direction merit was not evaluated"],
                "change_triggers": ["Target-domain decisive evidence"],
            }
            for dimension, weight in DIMENSION_WEIGHTS.items()
        ],
        "weighted_total": float(score * 20),
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
        "minimum_decisive_test": {
            "hypothesis": "The candidate method beats the fixture baseline",
            "inputs": ["Frozen fixture input"],
            "baseline": "Frozen fixture baseline",
            "steps": ["Compare one bounded candidate against the baseline"],
            "primary_metric": "fixture_score",
            "success_threshold": _threshold("fixture_score", ">=", 0.8, "ratio"),
            "stop_condition": _threshold("fixture_cost", ">", 10.0, "fixture_units"),
            "pivot_condition": _threshold("fixture_score", "<", 0.6, "ratio"),
            "expected_time": "One offline fixture pass",
            "required_resources": ["Offline fixture data"],
        },
        "supporting_candidate_ids": ["fixture:P01", "fixture:P04"],
        "counter_candidate_ids": ["fixture:P09"],
        "unknowns": ["Real-world transfer remains untested"],
        "confidence": "medium" if tier == "transfer-supported" else "low",
        "recommendation_status": "provisional",
    }


def _route_output() -> dict:
    return {
        "selected_direction_id": "D1",
        "hypothesis": "Confirmed offline fixture hypothesis",
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


def valid_waiting_bundle() -> dict:
    source_path = REPO_ROOT / "evals" / "m1" / "fixtures" / "valid-complete.json"
    source = json.loads(source_path.read_text(encoding="utf-8"))
    return {
        "source_m1_bundle": source,
        "direction_portfolio": {
            "schema_version": "m2.1",
            "source_m1_terminal_state": "M1_COMPLETE",
            "source_m1_bundle_hash": canonical_sha256(source),
            "brief_version": 2,
            "branch_id": "branch-a",
            "directions": [
                _direction(
                    "D1",
                    "provisional_main",
                    "Offline fixture main direction",
                    "transfer-supported",
                    4,
                    [],
                ),
                _direction(
                    "D2",
                    "adjacent_alternative",
                    "Offline fixture adjacent direction",
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
                    "Offline fixture transfer direction",
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
            ],
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
        "proves": ["M2 structural contract and gate behavior"],
        "does_not_prove": [
            "Real citation accuracy",
            "Real direction merit",
            "Target-domain transfer success",
            "Executed route feasibility",
        ],
    }


def build_cases() -> dict[str, dict]:
    cases: dict[str, dict] = {"valid-waiting": valid_waiting_bundle()}

    confirmed = copy.deepcopy(cases["valid-waiting"])
    confirmed["direction_decision"] = {
        "selected_direction_id": "D1",
        "status": "user_confirmed",
        "permitted_next_actions": ["modify", "reject", "generate_route"],
    }
    confirmed["route_output"] = _route_output()
    cases["valid-confirmed"] = confirmed

    hard_gate = copy.deepcopy(cases["valid-waiting"])
    main = hard_gate["direction_portfolio"]["directions"][0]
    main["hard_gates"][0]["status"] = "fail"
    main["hard_gates"][0]["blockers"] = ["No target problem evidence"]
    main["scorecard"]["weighted_total"] = 100.0
    cases["hard-gate-score-override"] = hard_gate

    speculative = copy.deepcopy(cases["valid-waiting"])
    speculative["direction_portfolio"]["directions"][0]["evidence_tier"] = "speculative"
    cases["speculative-formal-main"] = speculative

    blocked = copy.deepcopy(cases["valid-waiting"])
    candidate = blocked["source_m1_bundle"]["round2"]["candidate_pool"][14]
    candidate["verification_status"] = "conflicted"
    candidate["recommendation_eligible"] = False
    candidate["verified_record"]["verification"]["status"] = "conflicted"
    candidate["verified_record"]["verification"]["recommendation_eligible"] = False
    candidate["verified_record"]["verification"]["blocking_reasons"] = ["Fixture conflict"]
    blocked["direction_portfolio"]["directions"][0]["supporting_candidate_ids"] = [
        "fixture:P15"
    ]
    blocked["direction_portfolio"]["source_m1_bundle_hash"] = canonical_sha256(
        blocked["source_m1_bundle"]
    )
    cases["blocked-m1-citation"] = blocked

    missing = copy.deepcopy(cases["valid-waiting"])
    missing["direction_portfolio"]["directions"][0]["supporting_candidate_ids"] = [
        "fixture:UNKNOWN"
    ]
    cases["missing-supporting-id"] = missing

    route = copy.deepcopy(cases["valid-waiting"])
    route["route_output"] = _route_output()
    cases["route-before-confirmation"] = route

    renamed = copy.deepcopy(cases["valid-waiting"])
    renamed["direction_portfolio"]["directions"][1]["axis_changes"] = []
    cases["renamed-duplicate-direction"] = renamed

    anti_transfer = copy.deepcopy(cases["valid-waiting"])
    anti_transfer["direction_portfolio"]["directions"][0]["transfer_case"][
        "anti_transfer_factors"
    ] = []
    cases["missing-anti-transfer-factors"] = anti_transfer

    decisive = copy.deepcopy(cases["valid-waiting"])
    decisive["direction_portfolio"]["directions"][0]["minimum_decisive_test"][
        "success_threshold"
    ] = "meaningful improvement"
    cases["vague-decisive-test"] = decisive

    incomplete = copy.deepcopy(cases["valid-waiting"])
    incomplete["source_m1_bundle"]["terminal_state"] = "WAITING_FOR_EVIDENCE_DECISION"
    incomplete["source_m1_bundle"]["outcome"] = "evidence_incomplete"
    incomplete["direction_portfolio"]["source_m1_bundle_hash"] = canonical_sha256(
        incomplete["source_m1_bundle"]
    )
    cases["m1-evidence-incomplete-upgrade"] = incomplete
    return cases


def main() -> int:
    fixture_dir = Path(__file__).resolve().parent / "fixtures"
    fixture_dir.mkdir(parents=True, exist_ok=True)
    for name, payload in build_cases().items():
        path = fixture_dir / f"{name}.json"
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
