#!/usr/bin/env python3
"""Prepare immutable M2.1.1 inputs for the M3 forward cases."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SOURCE_BUNDLE = ROOT / "evals" / "m2" / "results" / "2026-08-05-f01-f05-nuclear-ml-confirmed.bundle.json"
VALIDATOR = ROOT / "skills" / "engineering-research-copilot" / "scripts" / "validate_m2_direction_bundle.py"
OUTPUT_ROOT = ROOT / "evals" / "m3" / "forward-inputs-r2"
M1_NUCLEAR = ROOT / "evals" / "m1" / "results" / "2026-08-04-pwr-sb-loca-rerun.bundle.json"
M1_NON_NUCLEAR = ROOT / "evals" / "m1" / "results" / "2026-08-04-bearing-fault-rerun-2.bundle.json"

VALIDATOR_RELATIVE = "skills/engineering-research-copilot/scripts/validate_m2_direction_bundle.py"
BASELINE_COMMIT = "d0f5e9017044ba35d0ac4559591028228f3b22d8"


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def raw_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any, *, compact: bool = False) -> None:
    if compact:
        payload = json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n"
    else:
        payload = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(payload)


def build_route(bundle: dict[str, Any], approved_changes: list[dict[str, Any]]) -> dict[str, Any]:
    decision = bundle["direction_decision"]
    selected_id = decision["selected_direction_id"]
    event = decision["confirmation_event"]
    direction = next(
        item
        for item in bundle["direction_portfolio"]["directions"]
        if item["direction_id"] == selected_id
    )
    minimum_test = direction["minimum_decisive_test"]
    claims = direction["core_claims"]
    claim_metrics = {
        claim["claim_id"]: [
            metric["metric_id"] for metric in claim["required_decision_metrics"]
        ]
        for claim in claims
    }
    all_metrics = [metric_id for metric_ids in claim_metrics.values() for metric_id in metric_ids]
    coverage_by_claim = {
        item["claim_id"]: item for item in minimum_test["claim_coverage"]
    }
    criteria = [
        criterion
        for item in minimum_test["claim_coverage"]
        for criterion in item["decision_criteria"]
    ]
    without_route = copy.deepcopy(bundle)
    without_route["route_output"] = None
    route = {
        "selected_direction_id": selected_id,
        "source_direction_hash": canonical_sha256(direction),
        "confirmation_event_hash": canonical_sha256(event),
        "source_bundle_hash": canonical_sha256(without_route),
        "hypothesis": minimum_test["hypothesis"],
        "baselines": [minimum_test["baseline"]],
        "controls": [
            "Use the identical frozen split, temporal backbone, seed, horizon, and inherited resource ceiling for the baseline and candidate."
        ],
        "sequence": [
            "Read the manifest, labels, sampling rate, horizon, and partition identities before any fit; stop on a failed precondition.",
            "Only after every preflight passes, fit one matched baseline and one bounded candidate within the inherited ceilings.",
            "Score every bound metric once and record a closed Go, Stop, or Pivot disposition without deployment or safety claims.",
        ],
        "inputs": minimum_test["inputs"],
        "outputs": [
            "One read-only preflight record with counts, units, horizon, and overlap.",
            "At most two bounded fit summaries with measured peak memory and elapsed time.",
            "One closed metric table and one disposition.",
        ],
        "controlled_variables": [
            "Frozen split, seed, backbone, sampling rate, horizon, fit count, and resource ceilings."
        ],
        "confounders": [
            "Trajectory leakage, scenario leakage, simulator shift, class imbalance, horizon mismatch, and calibration-set reuse."
        ],
        "primary_metrics": all_metrics,
        "secondary_metrics": [item["constraint_id"] for item in direction["resource_limits"]],
        "minimum_meaningful_improvement": (
            "The candidate must meet every preregistered success criterion while remaining within the inherited resource ceilings."
        ),
        "uncertainty_checks": [
            "Report the uncertainty metric on the untouched held-out split and compare behavior across declared target-domain strata."
        ],
        "sensitivity_checks": [
            "Recompute the bound metrics across fixed onset-window and horizon strata without adding fits."
        ],
        "validity_checks": [
            "Verify manifest completeness, zero identifier overlap, identical controls, numeric resource logs, and no operational extrapolation."
        ],
        "go_conditions": [criterion for criterion in criteria if criterion["criterion_type"] == "success"],
        "stop_conditions": [criterion for criterion in criteria if criterion["criterion_type"] == "stop"],
        "pivot_conditions": [criterion for criterion in criteria if criterion["criterion_type"] == "pivot"],
        "route_traceability": [
            {
                "claim_id": claim["claim_id"],
                "route_metric_ids": claim_metrics[claim["claim_id"]],
                "source_precondition_ids": coverage_by_claim[claim["claim_id"]]["required_precondition_ids"],
                "route_condition_types": ["go", "stop", "pivot"],
            }
            for claim in claims
        ],
        "source_test_mapping": [
            {
                "claim_id": claim["claim_id"],
                "minimum_test_metric_ids": claim_metrics[claim["claim_id"]],
                "route_metric_ids": claim_metrics[claim["claim_id"]],
            }
            for claim in claims
        ],
        "inherited_constraints": copy.deepcopy(direction["resource_limits"]),
        "approved_constraint_changes": approved_changes,
        "evidence_chain": {
            "design": [
                "The selected direction, claims, metrics, preconditions, thresholds, controls, and ceilings are hash-bound from the confirmed M2 card."
            ],
            "data": [
                "The target-domain manifest, split, label, sampling, horizon, and physics-feature preflights remain blocking before any fit."
            ],
            "analysis": [
                "Compute only the selected predictive, uncertainty, and data metrics plus inherited resource logs."
            ],
            "result": [
                "Record raw metric values and compare them mechanically with the bound Go, Stop, and Pivot criteria."
            ],
            "claim": [
                "Support is limited to the selected closed claims; no transfer success, deployment, operational safety, or empirical completion is permitted."
            ],
        },
    }
    return route


def run_validator(case_id: str, bundle_path: Path) -> dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, "-X", "utf8", str(VALIDATOR), str(bundle_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        check=False,
    )
    stdout = completed.stdout.rstrip("\r\n")
    if "\n" in stdout or "\r" in stdout or not stdout:
        raise SystemExit(f"{case_id}: m2_validator_stdout_not_one_line_json")
    result = json.loads(stdout)
    if completed.returncode != 0 or result.get("status") != "valid":
        raise SystemExit(f"{case_id}: m2_validator_not_valid")
    receipt = {
        "case_id": case_id,
        "errors": result["errors"],
        "evidence_gaps": result["evidence_gaps"],
        "input_path": bundle_path.relative_to(ROOT).as_posix(),
        "invocation_count": 1,
        "status": result["status"],
        "validator": VALIDATOR_RELATIVE,
    }
    return receipt


def make_case(
    case_id: str,
    bundle: dict[str, Any],
    filename: str,
    *,
    compact: bool = False,
) -> dict[str, Any]:
    path = OUTPUT_ROOT / filename
    receipt_path = OUTPUT_ROOT / f"{case_id}.validation.json"
    if path.exists() or receipt_path.exists():
        raise SystemExit(f"{case_id}: forward_input_artifact_already_exists")
    write_json(path, bundle, compact=compact)
    receipt = run_validator(case_id, path)
    write_json(receipt_path, receipt)
    return {
        "case_id": case_id,
        "input_path": path.relative_to(ROOT).as_posix(),
        "raw_sha256": raw_sha256(path),
        "canonical_sha256": canonical_sha256(bundle),
        "validation_path": receipt_path.relative_to(ROOT).as_posix(),
        "m2_validation_status": receipt["status"],
        "m2_validation_errors": receipt["errors"],
        "m2_validation_evidence_gaps": receipt["evidence_gaps"],
        "source_m1_artifact": M1_NUCLEAR.relative_to(ROOT).as_posix(),
        "source_m1_raw_sha256": raw_sha256(M1_NUCLEAR),
        "constructed_by_context": f"m2-input-preparation-r2-2026-08-05:{case_id}",
        "reviewed_by_context": f"m2-input-review-r2-2026-08-05:{case_id}",
        "does_not_prove": [
            "M2 structural validity does not prove empirical target-domain performance.",
            "No route step, experiment, simulation, training, download, service, deployment, or resource allocation ran.",
            "No nuclear safety, licensing, plant transfer, or operational conclusion is established.",
        ],
    }


def main() -> int:
    if not SOURCE_BUNDLE.is_file():
        raise SystemExit("missing_confirmed_m2_bundle")
    if not M1_NUCLEAR.is_file() or not M1_NON_NUCLEAR.is_file():
        raise SystemExit("missing_source_m1_artifact")
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    confirmed = json.loads(SOURCE_BUNDLE.read_text(encoding="utf-8"))
    if confirmed["direction_decision"]["selected_direction_id"] != "NEML-F01-D1":
        raise SystemExit("unexpected_selected_direction")
    if confirmed["direction_decision"]["status"] != "user_confirmed":
        raise SystemExit("confirmed_bundle_not_user_confirmed")
    if confirmed.get("route_output") is not None:
        raise SystemExit("confirmed_source_route_must_be_null")

    cases: list[dict[str, Any]] = []
    cases.append(
        make_case(
            "m3-f01",
            copy.deepcopy(confirmed),
            "m3-f01-bounded-confirmed.bundle.json",
        )
    )

    f02 = copy.deepcopy(confirmed)
    f02["route_output"] = build_route(f02, [])
    cases.append(make_case("m3-f02", f02, "m3-f02-route-compatible.bundle.json"))

    approval_message = (
        "M2 forward-input F03 proposes increasing the bounded fit ceiling from 2 to 3; "
        "no external approver identity is authenticated in this upstream record."
    )
    approved_change = {
        "constraint_id": "R-NEML-F01-D1-FITS",
        "previous_value": 2,
        "approved_value": 3,
        "unit": "fits",
        "approval_message_id": "m2-forward-f03-approved-change-2026-08-05",
        "approval_message_sha256": hashlib.sha256(approval_message.encode("utf-8")).hexdigest(),
    }
    f03 = copy.deepcopy(f02)
    f03["route_output"] = build_route(f03, [approved_change])
    cases.append(make_case("m3-f03", f03, "m3-f03-approved-change.bundle.json"))

    f05 = copy.deepcopy(confirmed)
    cases.append(
        make_case(
            "m3-f05",
            f05,
            "m3-f05-nuclear-ml.bundle.json",
            compact=True,
        )
    )

    f04 = {
        "case_id": "m3-f04",
        "input_path": None,
        "raw_sha256": None,
        "canonical_sha256": None,
        "validation_path": None,
        "m2_validation_status": "NOT_RUN",
        "m2_validation_errors": [],
        "m2_validation_evidence_gaps": [
            "no independently accepted complete non-nuclear M1/M2 input"
        ],
        "source_m1_artifact": M1_NON_NUCLEAR.relative_to(ROOT).as_posix(),
        "source_m1_raw_sha256": raw_sha256(M1_NON_NUCLEAR),
        "constructed_by_context": "m2-input-preparation-r2-2026-08-05:m3-f04",
        "reviewed_by_context": "m2-input-review-r2-2026-08-05:m3-f04",
        "does_not_prove": [
            "The available non-nuclear M1 source is evidence_incomplete and cannot support an M2 input.",
            "No non-nuclear M2 bundle or M3 method card was constructed.",
            "No measurement, calibration, experiment, or route execution ran.",
        ],
    }
    cases.insert(3, f04)

    manifest = {
        "schema_version": "m3.1-forward-inputs-r2",
        "evidence_class": "independent_m2_input_preparation",
        "preparation_context": "m2-input-preparation-r2-2026-08-05",
        "baseline_commit": BASELINE_COMMIT,
        "cases": cases,
        "notes": [
            "F01 and F05 are separate immutable byte snapshots of the same confirmed D1 M2 source; their fresh M3 contexts and frozen prompts remain independent.",
            "F03 preserves a non-empty proposed constraint change while leaving inherited_constraints equal to the selected direction limits; approval identity is deliberately not authenticated.",
            "F04 remains NOT_RUN because no independently accepted complete non-nuclear M1/M2 input is available.",
        ],
    }
    manifest_path = OUTPUT_ROOT / "manifest.json"
    if manifest_path.exists():
        raise SystemExit("forward_input_manifest_already_exists")
    write_json(manifest_path, manifest)
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
