#!/usr/bin/env python3
"""Assert the exact historical-prerequisite and current r5 blocked states."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from audit_forward_inputs import audit_manifest
from audit_forward_r5_acceptance import audit_acceptance_manifest


REPO_ROOT = Path(__file__).resolve().parents[2]
R2_INPUT_MANIFEST = REPO_ROOT / "evals" / "m3" / "forward-inputs-r2" / "manifest.json"
R5_CONSUMED_MANIFEST = (
    REPO_ROOT / "evals" / "m3" / "results" / "forward-r5" / "acceptance-manifest-consumed.json"
)


def audit_expected_state() -> dict[str, Any]:
    errors: list[str] = []
    prerequisite = audit_manifest(R2_INPUT_MANIFEST)
    acceptance = audit_acceptance_manifest(R5_CONSUMED_MANIFEST)

    prerequisite_cases = {
        item.get("case_id"): item
        for item in prerequisite.get("cases", [])
        if isinstance(item, dict)
    }
    if prerequisite.get("status") != "evidence_incomplete":
        errors.append("historical_prerequisite_status_drift")
    if prerequisite.get("errors") != []:
        errors.append("historical_prerequisite_errors_present")
    if prerequisite.get("evidence_gaps") != [
        "no independently accepted complete non-nuclear M1/M2 input"
    ]:
        errors.append("historical_prerequisite_gap_drift")
    for case_id in ("m3-f01", "m3-f02", "m3-f03", "m3-f05"):
        if prerequisite_cases.get(case_id, {}).get("status") != "valid":
            errors.append(f"historical_prerequisite_case_drift:{case_id}")
    if prerequisite_cases.get("m3-f04", {}).get("status") != "evidence_incomplete":
        errors.append("historical_prerequisite_case_drift:m3-f04")

    expected_counters = {
        "tasks_launched": 5,
        "task_finalizations_observed": 5,
        "dispatcher_cases_preflighted": 5,
        "dispatcher_cases_processed": 4,
        "composer_invocations": 4,
        "validator_invocations": 4,
        "accepted_cases": 4,
        "transaction_failures": 1,
    }
    if acceptance.get("status") != "blocked_not_accepted":
        errors.append("r5_acceptance_status_drift")
    if acceptance.get("errors") != ["acceptance_requirements_unmet"]:
        errors.append("r5_acceptance_error_drift")
    if acceptance.get("counters") != expected_counters:
        errors.append("r5_acceptance_counter_drift")
    if acceptance.get("m3_status") != "IN_PROGRESS":
        errors.append("r5_m3_status_drift")
    if acceptance.get("later_gates") != "NOT_RUN":
        errors.append("r5_later_gate_drift")

    return {
        "status": "valid" if not errors else "invalid",
        "errors": sorted(set(errors)),
        "historical_prerequisite_status": prerequisite.get("status"),
        "r5_acceptance_status": acceptance.get("status"),
        "r5_counters": acceptance.get("counters"),
        "m3_status": acceptance.get("m3_status"),
        "later_gates": acceptance.get("later_gates"),
        "does_not_prove": [
            "A valid state assertion does not relabel the historical F04 gap or failed r5 F02 as accepted.",
            "This is structural CI evidence, not M3 closure or fresh acceptance."
        ],
    }


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if arguments:
        return 2
    result = audit_expected_state()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0 if result["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
