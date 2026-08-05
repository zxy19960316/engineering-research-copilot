#!/usr/bin/env python3
"""Build deterministic real-evidence M2.1.1 Case A revision and Case F route artifacts."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any


M2_DIR = Path(__file__).resolve().parent
RESULTS_DIR = M2_DIR / "results"
LEGACY_CASE_A = RESULTS_DIR / "2026-08-05-case-a.bundle.json"

CASE_A_BUNDLE = RESULTS_DIR / "2026-08-05-case-a.m2.1.1.bundle.json"
CASE_A_REPORT = RESULTS_DIR / "2026-08-05-case-a.m2.1.1.md"
CASE_F_PRE = RESULTS_DIR / "2026-08-05-case-f.pre-confirmation.bundle.json"
CASE_F_CONFIRMED = RESULTS_DIR / "2026-08-05-case-f.confirmed.bundle.json"
CASE_F_ROUTE = RESULTS_DIR / "2026-08-05-case-f.route.bundle.json"
CASE_F_REPORT = RESULTS_DIR / "2026-08-05-case-f.md"

WEIGHTS = {
    "engineering_value": 15,
    "gap_and_evidence_quality": 15,
    "data_and_resource_fit": 20,
    "validation_and_falsifiability": 15,
    "method_maturity": 10,
    "time_to_decisive_signal": 10,
    "interdisciplinary_interface_quality": 10,
    "safety_ethics_compliance": 5,
}

AXIS_PROFILES = {
    "D1": {
        "problem": "early SB-LOCA break-extent estimation",
        "method": "physics-constrained uncertainty-aware temporal regression",
        "data": "SB-LOCA-focused NPPAD transient windows",
    },
    "D2": {
        "problem": "early SB-LOCA break-extent estimation",
        "method": "forecast-assisted deterministic temporal regression",
        "data": "SB-LOCA-focused NPPAD transient windows",
    },
    "D3": {
        "problem": "early SB-LOCA break-extent estimation",
        "method": "Bayesian spatio-temporal open-set classification",
        "data": "mixed-accident NPPAD windows with held-out accident families",
    },
}

DIRECTION_SPECS = {
    "D1": {
        "position": "provisional_main",
        "title": "Physics-constrained uncertainty-aware temporal SB-LOCA break-extent diagnosis",
        "tier": "transfer-supported",
        "supporting": ["P7", "P20", "P21", "P25"],
        "counter": ["P22"],
        "source_success": ["P20", "P21"],
        "scores": [5, 4, 4, 5, 4, 4, 5, 5],
        "claims": [
            {
                "claim_id": "C-D1-PRED",
                "claim": "On a frozen leakage-free public SB-LOCA split, the bounded candidate reduces held-out break-extent MAE versus the matched temporal baseline.",
                "claim_type": "predictive_performance",
                "evidence_candidate_ids": ["P7", "P20", "P25"],
                "metric_id": "M-D1-MAE",
                "metric": "Relative held-out break-extent MAE reduction versus baseline",
                "metric_role": "predictive_performance",
                "unit": "percent",
                "criterion": (">=", 5.0),
            },
            {
                "claim_id": "C-D1-UQ",
                "claim": "On the same held-out split, the candidate's predictive intervals meet a preregistered calibration-error ceiling.",
                "claim_type": "uncertainty_quality",
                "evidence_candidate_ids": ["P21", "P22"],
                "metric_id": "M-D1-ECE",
                "metric": "Held-out expected calibration error",
                "metric_role": "uncertainty_quality",
                "unit": "fraction",
                "criterion": ("<=", 0.05),
            },
            {
                "claim_id": "C-D1-DATA",
                "claim": "The frozen public data yield at least 30 eligible held-out SB-LOCA trajectories after manifest and leakage preflight.",
                "claim_type": "data_availability",
                "evidence_candidate_ids": ["P7"],
                "metric_id": "M-D1-N",
                "metric": "Eligible leakage-free held-out SB-LOCA trajectories",
                "metric_role": "data_availability",
                "unit": "count",
                "criterion": (">=", 30),
            },
        ],
    },
    "D2": {
        "position": "adjacent_alternative",
        "title": "Forecast-assisted temporal SB-LOCA break-extent diagnosis",
        "tier": "transfer-supported",
        "supporting": ["P7", "P22", "P25"],
        "counter": ["P17"],
        "source_success": ["P22", "P25"],
        "scores": [5, 4, 4, 5, 4, 5, 4, 5],
        "claims": [
            {
                "claim_id": "C-D2-PRED",
                "claim": "On a frozen leakage-free public SB-LOCA split, forecast assistance reduces held-out break-extent MAE versus the matched autoregressive baseline.",
                "claim_type": "predictive_performance",
                "evidence_candidate_ids": ["P7", "P25"],
                "metric_id": "M-D2-MAE",
                "metric": "Relative held-out break-extent MAE reduction versus baseline",
                "metric_role": "predictive_performance",
                "unit": "percent",
                "criterion": (">=", 5.0),
            },
            {
                "claim_id": "C-D2-UQ",
                "claim": "Residual-based prediction intervals for the forecast-assisted candidate meet the preregistered empirical coverage floor.",
                "claim_type": "uncertainty_quality",
                "evidence_candidate_ids": ["P22", "P25"],
                "metric_id": "M-D2-COV",
                "metric": "Held-out 90-percent prediction-interval empirical coverage",
                "metric_role": "uncertainty_quality",
                "unit": "fraction",
                "criterion": (">=", 0.85),
            },
        ],
    },
    "D3": {
        "position": "transfer_exploration",
        "title": "Open-set Bayesian SB-LOCA triage across mixed accident scenarios",
        "tier": "transfer-supported",
        "supporting": ["P7", "P21", "P23", "P25"],
        "counter": ["P22"],
        "source_success": ["P21", "P23"],
        "scores": [4, 4, 3, 4, 3, 3, 5, 5],
        "claims": [
            {
                "claim_id": "C-D3-PRED",
                "claim": "On known held-out scenarios, the bounded candidate retains the preregistered SB-LOCA recall floor.",
                "claim_type": "predictive_performance",
                "evidence_candidate_ids": ["P7", "P25"],
                "metric_id": "M-D3-RECALL",
                "metric": "Held-out SB-LOCA recall",
                "metric_role": "predictive_performance",
                "unit": "fraction",
                "criterion": (">=", 0.90),
            },
            {
                "claim_id": "C-D3-UQ",
                "claim": "On known and unknown held-out scenarios, predictive uncertainty meets the preregistered calibration-error ceiling.",
                "claim_type": "uncertainty_quality",
                "evidence_candidate_ids": ["P21", "P22"],
                "metric_id": "M-D3-ECE",
                "metric": "Held-out known-unknown expected calibration error",
                "metric_role": "uncertainty_quality",
                "unit": "fraction",
                "criterion": ("<=", 0.08),
            },
            {
                "claim_id": "C-D3-OOD",
                "claim": "For completely held-out accident families, the candidate meets the preregistered unknown-detection AUROC floor.",
                "claim_type": "open_set_detection",
                "evidence_candidate_ids": ["P23"],
                "metric_id": "M-D3-AUROC",
                "metric": "Unknown-accident detection AUROC",
                "metric_role": "open_set_detection",
                "unit": "area",
                "criterion": (">=", 0.85),
            },
        ],
    },
}


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def threshold(metric: str, operator: str, value: float, unit: str) -> dict:
    return {"metric": metric, "operator": operator, "value": value, "unit": unit}


def resource_limits(direction_id: str) -> list[dict]:
    return [
        {
            "constraint_id": f"R-{direction_id}-GPU-COUNT",
            "resource": "GPU devices",
            "operator": "<=",
            "value": 1,
            "unit": "count",
        },
        {
            "constraint_id": f"R-{direction_id}-VRAM",
            "resource": "Peak GPU memory",
            "operator": "<=",
            "value": 24,
            "unit": "GiB",
        },
        {
            "constraint_id": f"R-{direction_id}-WALL",
            "resource": "Elapsed route duration",
            "operator": "<=",
            "value": 14,
            "unit": "calendar_days",
        },
        {
            "constraint_id": f"R-{direction_id}-FITS",
            "resource": "Total bounded model fits",
            "operator": "<=",
            "value": 2,
            "unit": "fits",
        },
    ]


def preconditions(direction_id: str) -> list[dict]:
    return [
        {
            "precondition_id": f"P-{direction_id}-MANIFEST",
            "description": "Before any model fitting, verify a frozen manifest with labels, trajectory IDs, sample counts, channel units, sampling rate, and prediction horizon.",
            "gate_id": "data_availability",
            "status": "bounded_testable",
            "evidence_candidate_ids": ["P7"],
            "blocking_if_unresolved": True,
            "preflight_check": "Read only the manifest and count eligible labeled trajectories before any training or fitting.",
            "stop_condition": threshold("eligible_labeled_trajectories", "<", 30, "count"),
        },
        {
            "precondition_id": f"P-{direction_id}-SPLIT",
            "description": "Before any model fitting, verify trajectory- and scenario-level separation across train, validation, and held-out partitions.",
            "gate_id": "data_availability",
            "status": "bounded_testable",
            "evidence_candidate_ids": ["P7"],
            "blocking_if_unresolved": True,
            "preflight_check": "Compare trajectory and scenario identifiers across partitions; fitting remains blocked unless overlap is zero.",
            "stop_condition": threshold("cross_partition_identifier_overlap", ">", 0, "count"),
        },
    ]


def core_claims(direction_id: str) -> list[dict]:
    claims = []
    for item in DIRECTION_SPECS[direction_id]["claims"]:
        claims.append(
            {
                "claim_id": item["claim_id"],
                "claim": item["claim"],
                "claim_type": item["claim_type"],
                "evidence_candidate_ids": item["evidence_candidate_ids"],
                "required_decision_metrics": [
                    {
                        "metric_id": item["metric_id"],
                        "metric": item["metric"],
                        "metric_role": item["metric_role"],
                        "unit": item["unit"],
                    }
                ],
            }
        )
    return claims


def decisive_test(direction_id: str, claims: list[dict]) -> dict:
    conditions = {
        item["claim_id"]: (item["criterion"], item["unit"])
        for item in DIRECTION_SPECS[direction_id]["claims"]
    }
    required = preconditions(direction_id)
    precondition_ids = [item["precondition_id"] for item in required]
    coverage = []
    for claim in claims:
        metric = claim["required_decision_metrics"][0]
        criterion, unit = conditions[claim["claim_id"]]
        coverage.append(
            {
                "claim_id": claim["claim_id"],
                "metric_ids": [metric["metric_id"]],
                "decision_criteria": [
                    {
                        "criterion_type": "success",
                        "metric_id": metric["metric_id"],
                        "operator": criterion[0],
                        "value": criterion[1],
                        "unit": unit,
                    }
                ],
                "required_precondition_ids": precondition_ids,
            }
        )
    return {
        "scope": "minimum_decisive_test",
        "hypothesis": DIRECTION_SPECS[direction_id]["claims"][0]["claim"],
        "inputs": [
            "One frozen public NPPAD/PCTRAN-PWR3LP manifest and trajectory-level split",
            "One matched baseline and one bounded candidate configuration",
        ],
        "baseline": "One matched temporal baseline evaluated on the identical frozen split and resource ceiling.",
        "steps": [
            {
                "step_id": "S1",
                "action": "Before any fitting, run the manifest and split preflight checks; stop if either numeric condition fires.",
                "bounded_output": "One read-only preflight record with counts, sampling metadata, horizon, labels, units, and overlap.",
            },
            {
                "step_id": "S2",
                "action": "Only after both preflights pass, fit one baseline and one candidate within the four numeric resource ceilings.",
                "bounded_output": "At most two fit records with measured peak memory and elapsed time.",
            },
            {
                "step_id": "S3",
                "action": "Evaluate the preregistered claim metrics once on the frozen held-out partition.",
                "bounded_output": "One closed metric table and one success, stop, or pivot disposition; no deployment claim.",
            },
        ],
        "primary_metric_id": claims[0]["required_decision_metrics"][0]["metric_id"],
        "claim_coverage": coverage,
        "required_preconditions": required,
        "expected_time": "At most 14 calendar days after all preflight checks pass.",
        "required_resources": [
            "At most one GPU and 24 GiB peak GPU memory",
            "At most two bounded model fits",
            "Public data already available locally; no download is authorized",
        ],
    }


def hard_gates(direction_id: str) -> list[dict]:
    precondition_ids = [f"P-{direction_id}-MANIFEST", f"P-{direction_id}-SPLIT"]
    evidence = {
        "target_problem_evidence": ["P7", "P25"],
        "data_availability": ["P7"],
        "falsifiability": ["P20", "P21"],
        "resource_feasibility": ["P20", "P21"],
        "time_feasibility": ["P7"],
        "safety_ethics_compliance": ["P22"],
        "m1_citation_integrity": sorted(
            set(DIRECTION_SPECS[direction_id]["supporting"] + DIRECTION_SPECS[direction_id]["counter"])
        ),
    }
    rationales = {
        "target_problem_evidence": "P7 and P25 directly anchor the simulated PWR accident data and break-extent problem; they do not prove the proposed transfer.",
        "data_availability": "P7 supports public simulated data, while the manifest and leakage properties remain bounded preflight checks required before any fitting.",
        "falsifiability": "Every closed core claim has a role-matched metric and a finite numeric criterion in the minimum decisive test.",
        "resource_feasibility": "The decision test is capped at one GPU, 24 GiB peak memory, two fits, and 14 calendar days; actual consumption remains unmeasured.",
        "time_feasibility": "The bounded comparison has three closed steps and cannot begin fitting until both preflight checks pass.",
        "safety_ethics_compliance": "Only public simulated data are in scope; no plant control, operational safety conclusion, service, or deployment is authorized.",
        "m1_citation_integrity": "All cited IDs resolve to recommendation-eligible records in the unchanged accepted M1.2 candidate ledger, with basis limits preserved.",
    }
    return [
        {
            "gate_id": gate_id,
            "status": "pass",
            "evidence_candidate_ids": evidence[gate_id],
            "required_precondition_ids": precondition_ids if gate_id == "data_availability" else [],
            "rationale": rationales[gate_id],
            "blockers": [],
        }
        for gate_id in (
            "target_problem_evidence",
            "data_availability",
            "falsifiability",
            "resource_feasibility",
            "time_feasibility",
            "safety_ethics_compliance",
            "m1_citation_integrity",
        )
    ]


def transfer_case(direction_id: str) -> dict:
    compatibility = {
        "D1": {
            "concepts": ["Map temporal break-extent estimation to physics-derived features plus predictive uncertainty as a testable transfer hypothesis."],
            "units": ["Retain simulator channel units and physical definitions when scaling signals and residual features."],
            "scales": ["Freeze transient-window duration, sampling interval, horizon, and break-extent scale before comparison."],
            "boundary_conditions": ["Limit evidence to public simulated PWR scenarios; exclude operational-plant use."],
            "assumptions": ["The preflight confirms enough labeled, non-overlapping SB-LOCA trajectories for the bounded split."],
        },
        "D2": {
            "concepts": ["Transfer multi-step forecast assistance to bounded SB-LOCA break-extent regression with separately assessed interval coverage."],
            "units": ["Keep forecast targets, break extent, and interval widths in declared physical or normalized units."],
            "scales": ["Fix lookback, forecast horizon, sampling rate, and accident-onset alignment before fitting."],
            "boundary_conditions": ["Limit evidence to the frozen public simulation split and do not infer plant reliability."],
            "assumptions": ["The preflight confirms the forecast horizon and labels are consistent across trajectories."],
        },
        "D3": {
            "concepts": ["Transfer Bayesian uncertainty and open-set scoring to mixed simulated accident families as a testable triage hypothesis."],
            "units": ["Apply unit-aware scaling consistently across known and completely held-out accident families."],
            "scales": ["Freeze window length, onset alignment, family prevalence, sampling rate, and decision horizon."],
            "boundary_conditions": ["Restrict the exploration to public simulated scenarios and exclude operational safety use."],
            "assumptions": ["The preflight can withhold complete accident families without trajectory or scenario leakage."],
        },
    }[direction_id]
    anti_transfer = {
        "D1": ["No selected source establishes the exact combined method on SB-LOCA.", "Simulator-to-plant and reactor-design shift can invalidate apparent error and calibration gains."],
        "D2": ["P25 does not establish the proposed interval-calibration behavior on the selected public split.", "Forecast error can compound across horizons and conceal poor rare-event coverage."],
        "D3": ["P21 and P23 do not establish the combined method on SB-LOCA.", "Unknown-family benchmarks can be inflated by trajectory leakage or unrealistically separated scenarios."],
    }[direction_id]
    return {
        "target_problem_evidence": ["P7", "P25"],
        "source_success_evidence": DIRECTION_SPECS[direction_id]["source_success"],
        "transfer_compatibility": compatibility,
        "anti_transfer_factors": anti_transfer,
    }


def scorecard(direction_id: str) -> dict:
    scores = DIRECTION_SPECS[direction_id]["scores"]
    evidence_ids = sorted(
        set(DIRECTION_SPECS[direction_id]["supporting"] + DIRECTION_SPECS[direction_id]["counter"])
    )
    basis = {
        "engineering_value": "Direct-problem records anchor early simulated PWR diagnosis value, while the transfer remains untested.",
        "gap_and_evidence_quality": "The ledger combines full-text data evidence with abstract- and metadata-level method evidence, so exact-method support is incomplete.",
        "data_and_resource_fit": "P7 supports a public simulated dataset, but manifest eligibility, leakage, memory, and runtime still require bounded checks.",
        "validation_and_falsifiability": "Closed claim metrics and numeric thresholds provide a decisive comparison without treating the outcome as deployment evidence.",
        "method_maturity": "Component methods have eligible literature support, while their exact combination and target-domain behavior remain a hypothesis.",
        "time_to_decisive_signal": "One baseline, one candidate, one frozen split, and a 14-day ceiling bound the time to a decision signal.",
        "interdisciplinary_interface_quality": "The direction explicitly connects nuclear transient semantics, physical units, temporal modeling, and uncertainty limits.",
        "safety_ethics_compliance": "The scope is public simulated data and research-only analysis with no plant actuation or operational safety claim.",
    }
    dimensions = []
    for (dimension, weight), score in zip(WEIGHTS.items(), scores, strict=True):
        dimensions.append(
            {
                "dimension": dimension,
                "weight": weight,
                "score": score,
                "evidence_candidate_ids": evidence_ids,
                "evidence": f"{direction_id}: {basis[dimension]}",
                "confidence": "medium",
                "unknowns": [f"{direction_id} {dimension}: the preregistered bounded test has not been executed."],
                "change_triggers": [f"Re-score {direction_id} {dimension} only if its named preflight or metric evidence changes."],
            }
        )
    total = sum(item["score"] * item["weight"] / 5 for item in dimensions)
    return {"dimensions": dimensions, "weighted_total": total}


def axis_changes(direction_id: str) -> list[dict]:
    baseline = AXIS_PROFILES["D1"]
    profile = AXIS_PROFILES[direction_id]
    return [
        {"axis": axis, "from": baseline[axis], "to": profile[axis]}
        for axis in ("problem", "method", "data")
        if baseline[axis] != profile[axis]
    ]


def direction(direction_id: str) -> dict:
    spec = DIRECTION_SPECS[direction_id]
    claims = core_claims(direction_id)
    return {
        "direction_id": direction_id,
        "position": spec["position"],
        "title": spec["title"],
        "evidence_tier": spec["tier"],
        "claim_language": "Recommended for priority validation",
        "axis_profile": AXIS_PROFILES[direction_id],
        "axis_changes": axis_changes(direction_id),
        "core_claims": claims,
        "resource_limits": resource_limits(direction_id),
        "hard_gates": hard_gates(direction_id),
        "transfer_case": transfer_case(direction_id),
        "scorecard": scorecard(direction_id),
        "minimum_decisive_test": decisive_test(direction_id, claims),
        "supporting_candidate_ids": spec["supporting"],
        "counter_candidate_ids": spec["counter"],
        "unknowns": [
            "No M2 route or model fit has been executed.",
            "The exact transfer, resource use, and target-domain performance remain unverified until the bounded test runs under separate authorization.",
        ],
        "confidence": "medium",
        "recommendation_status": "provisional",
    }


def waiting_bundle() -> dict:
    legacy = json.loads(LEGACY_CASE_A.read_text(encoding="utf-8"))
    source = legacy["source_m1_bundle"]
    return {
        "source_m1_bundle": source,
        "direction_portfolio": {
            "schema_version": "m2.1.1",
            "source_m1_terminal_state": "M1_COMPLETE",
            "source_m1_bundle_hash": canonical_sha256(source),
            "brief_version": source["round2"]["research_brief"]["brief_version"],
            "branch_id": source["round2"]["research_brief"]["branch_id"],
            "directions": [direction("D1"), direction("D2"), direction("D3")],
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
    }


def confirmed_bundle(preconfirmation: dict) -> dict:
    bundle = copy.deepcopy(preconfirmation)
    pre_hash = canonical_sha256(preconfirmation)
    excerpt = (
        "I explicitly select formal direction D1 from pre-confirmation bundle "
        f"SHA-256 {pre_hash} and request its bounded research route."
    )
    bundle["direction_decision"] = {
        "selected_direction_id": "D1",
        "status": "user_confirmed",
        "permitted_next_actions": ["modify", "reject", "generate_route"],
        "confirmation_event": {
            "actor_role": "user",
            "selected_direction_id": "D1",
            "source_message_id": "forward-eval:2026-08-05:case-f:confirm-d1",
            "source_message_excerpt": excerpt,
            "source_message_sha256": text_sha256(excerpt),
            "previous_bundle_hash": pre_hash,
        },
    }
    return bundle


def route_output(confirmed: dict) -> dict:
    selected = confirmed["direction_portfolio"]["directions"][0]
    event = confirmed["direction_decision"]["confirmation_event"]
    coverage = selected["minimum_decisive_test"]["claim_coverage"]
    metrics = [
        metric
        for claim in selected["core_claims"]
        for metric in claim["required_decision_metrics"]
    ]
    go_conditions = [item["decision_criteria"][0] for item in coverage]
    stop_conditions = [
        {
            "criterion_type": "stop",
            "metric_id": "R-D1-VRAM",
            "operator": ">",
            "value": 24,
            "unit": "GiB",
        },
        {
            "criterion_type": "stop",
            "metric_id": "P-D1-SPLIT",
            "operator": ">",
            "value": 0,
            "unit": "count",
        },
    ]
    pivot_conditions = [
        {
            "criterion_type": "pivot",
            "metric_id": "M-D1-MAE",
            "operator": "<",
            "value": 2.0,
            "unit": "percent",
        },
        {
            "criterion_type": "pivot",
            "metric_id": "M-D1-ECE",
            "operator": ">",
            "value": 0.10,
            "unit": "fraction",
        },
    ]
    trace_by_claim = {
        item["claim_id"]: item["required_precondition_ids"] for item in coverage
    }
    confirmed_without_route = copy.deepcopy(confirmed)
    confirmed_without_route["route_output"] = None
    return {
        "selected_direction_id": "D1",
        "source_direction_hash": canonical_sha256(selected),
        "confirmation_event_hash": canonical_sha256(event),
        "source_bundle_hash": canonical_sha256(confirmed_without_route),
        "hypothesis": selected["minimum_decisive_test"]["hypothesis"],
        "baselines": [selected["minimum_decisive_test"]["baseline"]],
        "controls": ["Identical frozen split, temporal backbone, seed, fit count, horizon, and resource ceiling for baseline and candidate."],
        "sequence": [
            "Read-only manifest preflight before any fitting; stop below 30 eligible labeled trajectories.",
            "Read-only split preflight before any fitting; stop above zero cross-partition identifier overlap.",
            "Only after both preflights pass, fit exactly one baseline and one D1 candidate within the inherited ceilings.",
            "Evaluate the three bound D1 metrics once on the frozen held-out partition and record Go, Stop, or Pivot.",
        ],
        "inputs": ["The exact frozen manifest and split bound by P-D1-MANIFEST and P-D1-SPLIT.", "The exact baseline and D1 candidate configurations bound by the selected direction."],
        "outputs": ["Preflight record, two bounded fit records, one metric table, and one closed decision disposition."],
        "controlled_variables": ["Split, seed, backbone, sampling rate, horizon, fit count, and resource ceilings."],
        "confounders": ["Trajectory leakage, scenario leakage, simulator shift, class imbalance, horizon mismatch, and calibration-set reuse."],
        "primary_metrics": [metric["metric_id"] for metric in metrics],
        "secondary_metrics": ["R-D1-VRAM", "R-D1-WALL", "P-D1-SPLIT"],
        "minimum_meaningful_improvement": "M-D1-MAE must be at least 5.0 percent while M-D1-ECE is at most 0.05 and M-D1-N is at least 30 trajectories.",
        "uncertainty_checks": ["Report M-D1-ECE on the untouched held-out split and compare interval coverage across break-extent strata."],
        "sensitivity_checks": ["Recompute bound metrics across fixed onset-window and horizon strata without adding fits."],
        "validity_checks": ["Verify manifest completeness, zero identifier overlap, identical controls, numeric resource logs, and no operational extrapolation."],
        "go_conditions": go_conditions,
        "stop_conditions": stop_conditions,
        "pivot_conditions": pivot_conditions,
        "route_traceability": [
            {
                "claim_id": claim["claim_id"],
                "route_metric_ids": [metric["metric_id"] for metric in claim["required_decision_metrics"]],
                "source_precondition_ids": trace_by_claim[claim["claim_id"]],
                "route_condition_types": ["go", "stop", "pivot"],
            }
            for claim in selected["core_claims"]
        ],
        "source_test_mapping": [
            {
                "claim_id": claim["claim_id"],
                "minimum_test_metric_ids": [metric["metric_id"] for metric in claim["required_decision_metrics"]],
                "route_metric_ids": [metric["metric_id"] for metric in claim["required_decision_metrics"]],
            }
            for claim in selected["core_claims"]
        ],
        "inherited_constraints": copy.deepcopy(selected["resource_limits"]),
        "approved_constraint_changes": [],
        "evidence_chain": {
            "design": ["D1 hypothesis, claims, metrics, preconditions, thresholds, controls, and ceilings are copied or hash-bound from the selected direction."],
            "data": ["P-D1-MANIFEST and P-D1-SPLIT must pass before fitting; their exact numeric stop conditions remain active."],
            "analysis": ["Compute only the bound D1 predictive, uncertainty, and data metrics plus inherited resource logs."],
            "result": ["Record raw metric values and compare them mechanically with Go, Stop, and Pivot criteria."],
            "claim": ["Support is limited to the three closed D1 claims; no transfer success, deployment, or operational safety claim is permitted."],
        },
    }


def report_case_a(bundle: dict) -> str:
    directions = bundle["direction_portfolio"]["directions"]
    return f"""# Case A M2.1.1 corrected forward evaluation

Status: awaiting the preserved one-shot validator record at `2026-08-05-case-a.m2.1.1.validation.json`.

This revision preserves the complete embedded M1.2 source bundle from the original Case A and replaces only the M2 envelope required by the breaking m2.1.1 contract. The original Case A-E files remain historical evidence and are not edited.

## Decision state

- Portfolio: `provisional`
- Decision: `waiting_for_user_confirmation`
- Selected direction: `null`
- Route output: `null`
- Source M1 canonical SHA-256: `{bundle['direction_portfolio']['source_m1_bundle_hash']}`

## Formal directions

| ID | Position | Derived axis changes | Core claims | Weighted score |
|---|---|---:|---:|---:|
{chr(10).join(f"| {item['direction_id']} | {item['position']} | {len(item['axis_changes'])} | {len(item['core_claims'])} | {item['scorecard']['weighted_total']:.1f} |" for item in directions)}

Every direction includes role-matched prediction and uncertainty criteria, two structured data preconditions that must run before any fitting, four finite resource ceilings, and dimension-specific evidence, unknowns, and change triggers. This is a forward contract evaluation only. It does not execute training, simulation, downloads, services, deployment, or large-resource work, and it does not establish empirical transfer success or operational nuclear safety.
"""


def report_case_f(pre: dict, confirmed: dict, routed: dict) -> str:
    event = confirmed["direction_decision"]["confirmation_event"]
    route = routed["route_output"]
    return f"""# Case F confirmation and route-gate forward evaluation

Status: awaiting the preserved one-shot validator record at `2026-08-05-case-f.validation.json`.

Case F begins from the exact corrected Case A M2.1.1 waiting bundle, records an explicit D1 selection, then creates a route envelope without executing it.

## Hash bindings

- Pre-confirmation bundle canonical SHA-256: `{canonical_sha256(pre)}`
- Confirmation excerpt: `{event['source_message_excerpt']}`
- Confirmation message SHA-256: `{event['source_message_sha256']}`
- Selected D1 direction SHA-256: `{route['source_direction_hash']}`
- Confirmation event canonical SHA-256: `{route['confirmation_event_hash']}`
- Confirmed bundle canonical SHA-256: `{route['source_bundle_hash']}`

The route copies D1's three closed claims, three metric IDs, two data-preflight dependencies, and four numeric resource ceilings through `route_traceability`, `source_test_mapping`, and `inherited_constraints`. `approved_constraint_changes` is empty. No training, simulation, download, service, deployment, or large-resource action was executed.
"""


def main() -> int:
    pre = waiting_bundle()
    confirmed = confirmed_bundle(pre)
    routed = copy.deepcopy(confirmed)
    routed["route_output"] = route_output(confirmed)

    write_json(CASE_A_BUNDLE, pre)
    write_json(CASE_F_PRE, pre)
    write_json(CASE_F_CONFIRMED, confirmed)
    write_json(CASE_F_ROUTE, routed)
    CASE_A_REPORT.write_text(report_case_a(pre), encoding="utf-8")
    CASE_F_REPORT.write_text(report_case_f(pre, confirmed, routed), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
