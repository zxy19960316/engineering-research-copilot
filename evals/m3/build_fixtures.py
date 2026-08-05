#!/usr/bin/env python3
"""Build deterministic offline-only M3.1 adversarial fixtures and manifest."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


M3_DIR = Path(__file__).resolve().parent
REPO_ROOT = M3_DIR.parents[1]
_TEST_SPEC = importlib.util.spec_from_file_location(
    "m3_fixture_builders",
    REPO_ROOT / "tests" / "test_validate_m3_method_bundle.py",
)
if _TEST_SPEC is None or _TEST_SPEC.loader is None:
    raise RuntimeError("Unable to load M3 fixture builders")
_TEST_MODULE = importlib.util.module_from_spec(_TEST_SPEC)
_TEST_SPEC.loader.exec_module(_TEST_MODULE)
_nuclear_overlay = _TEST_MODULE._nuclear_overlay
_refresh_m3_hashes = _TEST_MODULE._refresh_m3_hashes
_refresh_m3_hashes_for_nonconfirmed = (
    _TEST_MODULE._refresh_m3_hashes_for_nonconfirmed
)
make_valid_m3_bundle = _TEST_MODULE.make_valid_m3_bundle


EXPECTED_RESULTS: dict[str, dict[str, object]] = {
    "valid-bounded": {
        "status": "valid",
        "errors": [],
        "evidence_gaps": [],
    },
    "valid-route-specific": {
        "status": "valid",
        "errors": [],
        "evidence_gaps": [],
    },
    "missing-assumptions": {
        "status": "invalid",
        "errors": ["invalid_method_card", "missing_method_card_assumptions"],
        "evidence_gaps": [],
    },
    "missing-baseline": {
        "status": "invalid",
        "errors": ["invalid_method_card", "missing_method_card_baselines"],
        "evidence_gaps": [],
    },
    "missing-failure-mode": {
        "status": "invalid",
        "errors": ["invalid_method_card", "missing_method_card_failure_modes"],
        "evidence_gaps": [],
    },
    "missing-uncertainty-handling": {
        "status": "invalid",
        "errors": [
            "invalid_method_card",
            "missing_method_card_uncertainty_handling",
        ],
        "evidence_gaps": [],
    },
    "nonnumeric-stop-condition": {
        "status": "invalid",
        "errors": [
            "invalid_method_card_stop_condition",
            "method_card_stop_condition_not_authoritative",
        ],
        "evidence_gaps": [],
    },
    "unbound-stop-condition": {
        "status": "invalid",
        "errors": ["method_card_stop_condition_not_authoritative"],
        "evidence_gaps": [],
    },
    "unbound-pivot-condition": {
        "status": "invalid",
        "errors": ["method_card_pivot_condition_not_authoritative"],
        "evidence_gaps": [],
    },
    "source-missing-does-not-support": {
        "status": "invalid",
        "errors": [
            "invalid_source_ledger",
            "missing_source_ledger_does_not_support",
        ],
        "evidence_gaps": [],
    },
    "unconfirmed-direction": {
        "status": "invalid",
        "errors": ["direction_not_user_confirmed"],
        "evidence_gaps": [],
    },
    "nonempty-approved-constraint-changes": {
        "status": "invalid",
        "errors": ["unsupported_approved_constraint_change_provenance"],
        "evidence_gaps": [],
    },
    "resource-expansion": {
        "status": "invalid",
        "errors": ["minimum_resource_exceeds_ceiling"],
        "evidence_gaps": [],
    },
    "route-precondition-mismatch": {
        "status": "invalid",
        "errors": ["route_precondition_traceability_mismatch"],
        "evidence_gaps": [],
    },
    "route-condition-mismatch": {
        "status": "invalid",
        "errors": [
            "method_card_stop_condition_not_authoritative",
            "route_condition_traceability_mismatch",
        ],
        "evidence_gaps": [],
    },
    "nuclear-transfer-overclaim": {
        "status": "invalid",
        "errors": ["nuclear_overlay_transfer_status_not_hypothesis"],
        "evidence_gaps": [],
    },
}


def _write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(
            payload,
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


def build_cases() -> dict[str, dict]:
    cases = {
        "valid-bounded": make_valid_m3_bundle(),
        "valid-route-specific": make_valid_m3_bundle("route_specific"),
    }

    for name, field in (
        ("missing-assumptions", "assumptions"),
        ("missing-baseline", "baselines"),
        ("missing-failure-mode", "failure_modes"),
        ("missing-uncertainty-handling", "uncertainty_handling"),
    ):
        changed = make_valid_m3_bundle()
        del changed["method_cards"][0][field]
        cases[name] = changed

    nonnumeric_stop = make_valid_m3_bundle()
    nonnumeric_stop["method_cards"][0]["stop_conditions"][0]["value"] = (
        "not-numeric"
    )
    cases["nonnumeric-stop-condition"] = nonnumeric_stop

    unbound_stop = make_valid_m3_bundle()
    unbound_stop["method_cards"][0]["stop_conditions"][0]["value"] = 0.61
    cases["unbound-stop-condition"] = unbound_stop

    unbound_pivot = make_valid_m3_bundle()
    unbound_pivot["method_cards"][0]["pivot_conditions"][0]["value"] = 0.21
    cases["unbound-pivot-condition"] = unbound_pivot

    missing_non_support = make_valid_m3_bundle()
    del missing_non_support["method_cards"][0]["source_ledger"][0][
        "does_not_support"
    ]
    cases["source-missing-does-not-support"] = missing_non_support

    unconfirmed = make_valid_m3_bundle()
    unconfirmed["source_m2_bundle"]["direction_decision"] = {
        "selected_direction_id": None,
        "status": "waiting_for_user_confirmation",
        "permitted_next_actions": ["confirm", "modify", "reject"],
        "confirmation_event": None,
    }
    _refresh_m3_hashes_for_nonconfirmed(unconfirmed)
    cases["unconfirmed-direction"] = unconfirmed

    unsupported_change = make_valid_m3_bundle("route_specific")
    unsupported_change["source_m2_bundle"]["route_output"][
        "approved_constraint_changes"
    ] = [
        {
            "constraint_id": "R-D1-VRAM",
            "previous_value": 24,
            "approved_value": 48,
            "unit": "GiB",
            "approval_message_id": "message:unverifiable-change",
            "approval_message_sha256": "0" * 64,
        }
    ]
    _refresh_m3_hashes(unsupported_change)
    cases["nonempty-approved-constraint-changes"] = unsupported_change

    resource_expansion = make_valid_m3_bundle()
    resource_expansion["method_cards"][0]["minimum_resources"][0][
        "required_value"
    ] = 3
    cases["resource-expansion"] = resource_expansion

    precondition_mismatch = make_valid_m3_bundle("route_specific")
    precondition_mismatch["source_m2_bundle"]["route_output"][
        "route_traceability"
    ][0]["source_precondition_ids"] = []
    _refresh_m3_hashes(precondition_mismatch)
    cases["route-precondition-mismatch"] = precondition_mismatch

    condition_mismatch = make_valid_m3_bundle("route_specific")
    condition_mismatch["source_m2_bundle"]["route_output"]["stop_conditions"] = [
        {
            "criterion_type": "stop",
            "metric_id": "M-COST",
            "operator": ">",
            "value": 2,
            "unit": "hours",
        }
    ]
    _refresh_m3_hashes(condition_mismatch)
    cases["route-condition-mismatch"] = condition_mismatch

    transfer_overclaim = make_valid_m3_bundle()
    overlay = copy.deepcopy(_nuclear_overlay())
    overlay["transfer_status"] = "validated"
    transfer_overclaim["domain_overlays"] = [overlay]
    cases["nuclear-transfer-overclaim"] = transfer_overclaim

    if set(cases) != set(EXPECTED_RESULTS):
        raise ValueError("fixture_case_manifest_mismatch")
    return cases


def build_manifest(cases: dict[str, dict]) -> dict:
    return {
        "schema_version": "m3.1-adversarial-cases",
        "evidence_class": "offline_contract_fixture",
        "cases": [
            {
                "case_id": name,
                "fixture": f"{name}.json",
                "expected_status": EXPECTED_RESULTS[name]["status"],
                "expected_errors": EXPECTED_RESULTS[name]["errors"],
                "expected_evidence_gaps": EXPECTED_RESULTS[name]["evidence_gaps"],
            }
            for name in cases
        ],
    }


def main() -> int:
    fixture_dir = M3_DIR / "fixtures"
    fixture_dir.mkdir(parents=True, exist_ok=True)
    cases = build_cases()
    expected_names = {f"{name}.json" for name in cases}
    for old_path in fixture_dir.glob("*.json"):
        if old_path.name not in expected_names:
            old_path.unlink()
    for name, payload in cases.items():
        _write_json(fixture_dir / f"{name}.json", payload)
    _write_json(M3_DIR / "adversarial-cases.json", build_manifest(cases))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
