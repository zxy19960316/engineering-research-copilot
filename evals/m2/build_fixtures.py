#!/usr/bin/env python3
"""Build deterministic offline-only M2.1.1 adversarial fixtures and manifest."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path


M2_DIR = Path(__file__).resolve().parent
REPO_ROOT = M2_DIR.parents[1]
sys.path.insert(0, str(REPO_ROOT))

from tests.test_validate_m2_direction_bundle import (  # noqa: E402
    _confirm_bundle,
    _refresh_hash,
    _route_output,
    _set_nonconfirmed_decision,
    make_valid_m2_bundle,
)
from validate_m2_direction_bundle import canonical_sha256  # noqa: E402


def _frozen_waiting_bundle() -> dict:
    bundle = make_valid_m2_bundle()
    source_path = REPO_ROOT / "evals" / "m1" / "fixtures" / "valid-complete.json"
    bundle["source_m1_bundle"] = json.loads(source_path.read_text(encoding="utf-8"))
    _refresh_hash(bundle)
    bundle["proves"] = ["M2.1.1 offline structural contract behavior"]
    bundle["does_not_prove"] = [
        "Real citation existence or metadata accuracy",
        "Host-system user identity",
        "Real direction merit or target-domain transfer success",
        "Execution of any experiment, simulation, training, download, deployment, or route",
    ]
    return bundle


def _confirmed_route_bundle() -> dict:
    bundle = _frozen_waiting_bundle()
    _confirm_bundle(bundle)
    bundle["route_output"] = _route_output(bundle)
    return bundle


def _mark_preprint(candidate: dict) -> None:
    candidate["verification_status"] = "verified_preprint"
    candidate["verified_record"]["verification"]["status"] = "verified_preprint"


def build_cases() -> dict[str, dict]:
    cases: dict[str, dict] = {
        "valid-waiting": _frozen_waiting_bundle(),
        "valid-confirmed": _confirmed_route_bundle(),
    }

    hard_gate = copy.deepcopy(cases["valid-waiting"])
    main = hard_gate["direction_portfolio"]["directions"][0]
    main["hard_gates"][0]["status"] = "fail"
    main["hard_gates"][0]["blockers"] = ["No target problem evidence"]
    main["scorecard"]["weighted_total"] = 100.0
    cases["hard-gate-score-override"] = hard_gate

    speculative = copy.deepcopy(cases["valid-waiting"])
    speculative["direction_portfolio"]["directions"][0]["evidence_tier"] = "speculative"
    cases["speculative-formal-main"] = speculative

    language = copy.deepcopy(cases["valid-waiting"])
    language["direction_portfolio"]["directions"][0]["claim_language"] = (
        "Established and ready to deploy"
    )
    cases["tier-language-mismatch"] = language

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
    _refresh_hash(blocked)
    cases["blocked-m1-citation"] = blocked

    missing = copy.deepcopy(cases["valid-waiting"])
    missing["direction_portfolio"]["directions"][0]["supporting_candidate_ids"] = [
        "fixture:UNKNOWN"
    ]
    cases["missing-supporting-id"] = missing

    route_before = _confirmed_route_bundle()
    _set_nonconfirmed_decision(route_before, "waiting_for_user_confirmation")
    cases["route-before-confirmation"] = route_before

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
        "claim_coverage"
    ][0]["decision_criteria"] = "meaningful improvement"
    cases["vague-decisive-test"] = decisive

    incomplete = copy.deepcopy(cases["valid-waiting"])
    incomplete["source_m1_bundle"]["terminal_state"] = "WAITING_FOR_EVIDENCE_DECISION"
    incomplete["source_m1_bundle"]["outcome"] = "evidence_incomplete"
    _refresh_hash(incomplete)
    cases["m1-evidence-incomplete-upgrade"] = incomplete

    missing_event = copy.deepcopy(cases["valid-waiting"])
    missing_event["direction_decision"] = {
        "selected_direction_id": "D1",
        "status": "user_confirmed",
        "permitted_next_actions": ["modify", "reject", "generate_route"],
        "confirmation_event": None,
    }
    cases["confirmation-missing-event"] = missing_event

    non_user = copy.deepcopy(cases["valid-confirmed"])
    non_user["direction_decision"]["confirmation_event"]["actor_role"] = "assistant"
    cases["confirmation-non-user"] = non_user

    mismatch = copy.deepcopy(cases["valid-confirmed"])
    mismatch["direction_decision"]["confirmation_event"]["selected_direction_id"] = "D2"
    cases["confirmation-direction-mismatch"] = mismatch

    stale_confirmation = copy.deepcopy(cases["valid-confirmed"])
    stale_confirmation["direction_decision"]["confirmation_event"][
        "previous_bundle_hash"
    ] = "0" * 64
    cases["confirmation-stale-bundle"] = stale_confirmation

    implicit_message = copy.deepcopy(cases["valid-confirmed"])
    event = implicit_message["direction_decision"]["confirmation_event"]
    event["source_message_excerpt"] = "I confirm the recommended option."
    event["source_message_sha256"] = hashlib.sha256(
        event["source_message_excerpt"].encode("utf-8")
    ).hexdigest()
    cases["confirmation-message-without-id"] = implicit_message

    high_risk = copy.deepcopy(cases["valid-waiting"])
    _confirm_bundle(high_risk, "H1")
    cases["confirmation-high-risk-id"] = high_risk

    for name, field in (
        ("route-wrong-direction-hash", "source_direction_hash"),
        ("route-wrong-confirmation-hash", "confirmation_event_hash"),
        ("route-wrong-bundle-hash", "source_bundle_hash"),
    ):
        changed = copy.deepcopy(cases["valid-confirmed"])
        changed["route_output"][field] = "0" * 64
        cases[name] = changed

    d2_route = copy.deepcopy(cases["valid-confirmed"])
    d2_route["route_output"]["source_direction_hash"] = canonical_sha256(
        d2_route["direction_portfolio"]["directions"][1]
    )
    cases["route-d2-relabelled"] = d2_route

    missing_trace = copy.deepcopy(cases["valid-confirmed"])
    missing_trace["route_output"]["route_traceability"] = missing_trace["route_output"][
        "route_traceability"
    ][:1]
    cases["route-missing-claim-trace"] = missing_trace

    resource_expansion = copy.deepcopy(cases["valid-confirmed"])
    resource_expansion["route_output"]["inherited_constraints"][0]["value"] = 20
    cases["route-resource-expansion"] = resource_expansion

    oversized = copy.deepcopy(cases["valid-waiting"])
    oversized["direction_portfolio"]["directions"][0]["minimum_decisive_test"]["steps"][0][
        "action"
    ] = "x" * 1000
    cases["decisive-test-oversized-step"] = oversized

    too_many = copy.deepcopy(cases["valid-waiting"])
    steps = too_many["direction_portfolio"]["directions"][0]["minimum_decisive_test"]["steps"]
    steps.extend(copy.deepcopy(steps[0]) for _ in range(3))
    cases["decisive-test-too-many-steps"] = too_many

    nested = copy.deepcopy(cases["valid-waiting"])
    nested["direction_portfolio"]["directions"][0]["minimum_decisive_test"]["steps"][0][
        "bounded_output"
    ] = {"route_output": {"sequence": []}}
    cases["decisive-test-nested-route"] = nested

    preprint_main = copy.deepcopy(cases["valid-waiting"])
    for candidate in preprint_main["source_m1_bundle"]["round2"]["candidate_pool"]:
        if candidate["candidate_id"] in {"fixture:P01", "fixture:P04"}:
            _mark_preprint(candidate)
    _refresh_hash(preprint_main)
    cases["preprint-only-main"] = preprint_main

    preprint_safety = copy.deepcopy(cases["valid-waiting"])
    main = preprint_safety["direction_portfolio"]["directions"][0]
    safety = next(
        gate for gate in main["hard_gates"] if gate["gate_id"] == "safety_ethics_compliance"
    )
    safety["evidence_candidate_ids"] = ["fixture:P01"]
    _mark_preprint(preprint_safety["source_m1_bundle"]["round2"]["candidate_pool"][0])
    _refresh_hash(preprint_safety)
    cases["preprint-only-safety"] = preprint_safety

    missing_coverage = copy.deepcopy(cases["valid-waiting"])
    missing_coverage["direction_portfolio"]["directions"][0]["minimum_decisive_test"][
        "claim_coverage"
    ] = missing_coverage["direction_portfolio"]["directions"][0][
        "minimum_decisive_test"
    ]["claim_coverage"][:1]
    cases["claim-missing-coverage"] = missing_coverage

    wrong_uq = copy.deepcopy(cases["valid-waiting"])
    wrong_uq["direction_portfolio"]["directions"][0]["core_claims"][1][
        "required_decision_metrics"
    ][0]["metric_role"] = "predictive_performance"
    cases["uq-wrong-metric-role"] = wrong_uq

    unresolved = copy.deepcopy(cases["valid-waiting"])
    unresolved["direction_portfolio"]["directions"][0]["minimum_decisive_test"][
        "required_preconditions"
    ][0]["status"] = "unresolved"
    cases["unresolved-data-precondition"] = unresolved

    axis = copy.deepcopy(cases["valid-waiting"])
    axis["direction_portfolio"]["directions"][1]["axis_profile"] = copy.deepcopy(
        axis["direction_portfolio"]["directions"][0]["axis_profile"]
    )
    cases["axis-profile-mismatch"] = axis

    duplicate_score = copy.deepcopy(cases["valid-waiting"])
    for item in duplicate_score["direction_portfolio"]["directions"][0]["scorecard"][
        "dimensions"
    ]:
        item["evidence"] = "Same evidence"
        item["unknowns"] = ["Same unknown"]
        item["change_triggers"] = ["Same trigger"]
    cases["scorecard-duplicate-rationale"] = duplicate_score
    return cases


EXPECTED_ERRORS = {
    "valid-waiting": ("valid", []),
    "valid-confirmed": ("valid", []),
    "hard-gate-score-override": (
        "invalid",
        [
            "failed_hard_gate_has_scorecard",
            "failed_hard_gate_ranked",
            "incomplete_portfolio_marked_provisional",
        ],
    ),
    "speculative-formal-main": ("invalid", ["invalid_tier_for_formal_position"]),
    "tier-language-mismatch": ("invalid", ["evidence_tier_language_mismatch"]),
    "blocked-m1-citation": ("invalid", ["blocked_m1_candidate"]),
    "missing-supporting-id": ("invalid", ["unknown_m1_candidate_id"]),
    "route-before-confirmation": ("invalid", ["route_output_before_user_confirmation"]),
    "renamed-duplicate-direction": ("invalid", ["adjacent_requires_one_axis_change"]),
    "missing-anti-transfer-factors": ("invalid", ["missing_anti_transfer_factors"]),
    "vague-decisive-test": ("invalid", ["invalid_claim_decision_criteria"]),
    "m1-evidence-incomplete-upgrade": ("invalid", ["source_m1_not_complete"]),
    "confirmation-missing-event": ("invalid", ["confirmed_without_confirmation_event"]),
    "confirmation-non-user": ("invalid", ["confirmation_actor_not_user"]),
    "confirmation-direction-mismatch": ("invalid", ["confirmation_direction_mismatch"]),
    "confirmation-stale-bundle": (
        "invalid",
        ["confirmation_previous_bundle_hash_mismatch"],
    ),
    "confirmation-message-without-id": (
        "invalid",
        ["confirmation_message_missing_explicit_direction_id"],
    ),
    "confirmation-high-risk-id": ("invalid", ["selected_direction_not_formal"]),
    "route-wrong-direction-hash": ("invalid", ["route_source_direction_hash_mismatch"]),
    "route-wrong-confirmation-hash": (
        "invalid",
        ["route_confirmation_event_hash_mismatch"],
    ),
    "route-wrong-bundle-hash": ("invalid", ["route_source_bundle_hash_mismatch"]),
    "route-d2-relabelled": ("invalid", ["route_source_direction_hash_mismatch"]),
    "route-missing-claim-trace": ("invalid", ["route_missing_claim_traceability"]),
    "route-resource-expansion": ("invalid", ["route_inherited_constraints_mismatch"]),
    "decisive-test-oversized-step": ("invalid", ["decisive_test_step_too_large"]),
    "decisive-test-too-many-steps": ("invalid", ["invalid_decisive_test_step_count"]),
    "decisive-test-nested-route": ("invalid", ["invalid_decisive_test_step"]),
    "preprint-only-main": (
        "invalid",
        ["provisional_main_requires_non_preprint_support"],
    ),
    "preprint-only-safety": (
        "invalid",
        ["safety_gate_requires_non_preprint_support"],
    ),
    "claim-missing-coverage": ("invalid", ["core_claim_without_test_coverage"]),
    "uq-wrong-metric-role": (
        "invalid",
        ["uncertainty_claim_requires_uncertainty_metric"],
    ),
    "unresolved-data-precondition": (
        "invalid",
        ["unresolved_blocking_precondition_passed_gate"],
    ),
    "axis-profile-mismatch": ("invalid", ["axis_changes_do_not_match_profiles"]),
    "scorecard-duplicate-rationale": (
        "invalid",
        ["duplicate_score_dimension_rationale"],
    ),
}


def build_manifest(cases: dict[str, dict]) -> dict:
    if set(cases) != set(EXPECTED_ERRORS):
        raise ValueError("fixture_case_manifest_mismatch")
    return {
        "schema_version": "m2.1.1-adversarial-cases",
        "evidence_class": "offline_contract_fixture",
        "cases": [
            {
                "fixture": f"{name}.json",
                "expected_status": EXPECTED_ERRORS[name][0],
                "expected_errors": EXPECTED_ERRORS[name][1],
            }
            for name in cases
        ],
    }


def main() -> int:
    fixture_dir = M2_DIR / "fixtures"
    fixture_dir.mkdir(parents=True, exist_ok=True)
    cases = build_cases()
    expected_names = {f"{name}.json" for name in cases}
    for old_path in fixture_dir.glob("*.json"):
        if old_path.name not in expected_names:
            old_path.unlink()
    for name, payload in cases.items():
        (fixture_dir / f"{name}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
            encoding="utf-8",
        )
    (M2_DIR / "adversarial-cases.json").write_text(
        json.dumps(build_manifest(cases), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
