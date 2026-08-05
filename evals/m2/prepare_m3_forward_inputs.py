#!/usr/bin/env python3
"""Prepare independent M2.1.1 inputs for the M3 forward boundary.

This script reads only accepted M1/M2 artifacts and M1/M2 validators. It does
not import or inspect any M3 implementation, fixture, test, or expected result.
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
M1_RESULTS = ROOT / "evals" / "m1" / "results"
M2_RESULTS = ROOT / "evals" / "m2" / "results"
OUT = ROOT / "evals" / "m3" / "forward-inputs"
SCRIPTS = ROOT / "skills" / "engineering-research-copilot" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from validate_m1_bundle import validate_bundle as validate_m1_bundle  # noqa: E402
from validate_m2_direction_bundle import (  # noqa: E402
    canonical_sha256,
    validate_bundle as validate_m2_bundle,
)


PREPARATION_CONTEXT = "m2-input-preparation-context-2026-08-05"
M1_ARTIFACT = "evals/m1/results/2026-08-04-pwr-sb-loca-rerun.bundle.json"
M1_PATH = ROOT / M1_ARTIFACT
F04_M1_ARTIFACT = "evals/m1/results/2026-08-04-bearing-fault-rerun-2.bundle.json"
F04_M1_PATH = ROOT / F04_M1_ARTIFACT
F02_SOURCE = M2_RESULTS / "2026-08-05-case-f.route.bundle.json"
F01_SOURCE = M2_RESULTS / "2026-08-05-case-f.confirmed.bundle.json"


def raw_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> tuple[str, str]:
    encoded = (
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    path.write_bytes(encoded)
    return hashlib.sha256(encoded).hexdigest(), canonical_sha256(value)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def m1_source_hash() -> str:
    return raw_sha256(M1_PATH)


def common_record(
    case_id: str,
    input_path: str | None,
    raw_hash: str | None,
    canonical_hash: str | None,
    status: str,
    errors: list[str],
    evidence_gaps: list[str],
    source_m1_artifact: str,
    source_m1_raw_hash: str,
    limitations: list[str],
    constructed_context: str | None = None,
    reviewed_context: str | None = None,
) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "input_path": input_path,
        "raw_sha256": raw_hash,
        "canonical_sha256": canonical_hash,
        "m2_validation_status": status,
        "m2_validation_errors": errors,
        "m2_validation_evidence_gaps": evidence_gaps,
        "source_m1_artifact": source_m1_artifact,
        "source_m1_raw_sha256": source_m1_raw_hash,
        "constructed_by_context": constructed_context
        or f"{PREPARATION_CONTEXT}:{case_id}",
        "reviewed_by_context": reviewed_context
        or f"{PREPARATION_CONTEXT}:{case_id}:validator-recheck",
        "does_not_prove": limitations,
    }


def write_validation(case_id: str, input_path: str, payload: dict) -> None:
    result = validate_m2_bundle(payload)
    validation = {
        "case_id": case_id,
        "input_path": input_path,
        "validator": "skills/engineering-research-copilot/scripts/validate_m2_direction_bundle.py",
        "invocation_count": 1,
        **result,
    }
    write_json(OUT / f"{case_id}.validation.json", validation)
    if result != {"status": "valid", "errors": [], "evidence_gaps": []}:
        raise SystemExit(f"{case_id}: unexpected M2 result {result}")


def prepare() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("m3-f*.bundle.json"):
        old.unlink()
    for old in OUT.glob("m3-f*.validation.json"):
        old.unlink()

    source_m1_hash = m1_source_hash()
    cases: list[dict[str, Any]] = []

    # F01 is intentionally preserved as NOT_RUN: the accepted no-route input
    # has success criteria but no upstream numeric stop/pivot criteria, and no
    # new user confirmation is available to authorize an M2 mutation.
    cases.append(
        common_record(
            "m3-f01",
            None,
            None,
            None,
            "NOT_RUN",
            [],
            [
                "no independently accepted user_confirmed no-route M2.1.1 input with upstream numeric stop/pivot criteria"
            ],
            "evals/m1/results/2026-08-04-pwr-sb-loca-rerun.bundle.json",
            source_m1_hash,
            [
                "No M3 bundle was constructed",
                "No empirical method performance or route execution",
                "No user confirmation was inferred for a modified M2 artifact",
            ],
        )
    )
    write_json(
        OUT / "m3-f01.validation.json",
        {
            "case_id": "m3-f01",
            "status": "NOT_RUN",
            "errors": [],
            "evidence_gaps": [
                "no independently accepted user_confirmed no-route M2.1.1 input with upstream numeric stop/pivot criteria"
            ],
            "invocation_count": 0,
        },
    )

    route = load_json(F02_SOURCE)
    f02_path = OUT / "m3-f02-route-compatible.bundle.json"
    f02_raw, f02_canonical = write_json(f02_path, route)
    f02_rel = "evals/m3/forward-inputs/m3-f02-route-compatible.bundle.json"
    write_validation("m3-f02", f02_rel, route)
    cases.append(
        common_record(
            "m3-f02",
            f02_rel,
            f02_raw,
            f02_canonical,
            "valid",
            [],
            [],
            M1_ARTIFACT,
            source_m1_hash,
            [
                "M2 structural validity does not prove route feasibility",
                "No route step, experiment, simulation, training, or resource allocation ran",
            ],
        )
    )

    f03 = copy.deepcopy(route)
    f03["route_output"]["approved_constraint_changes"] = [
        {
            "constraint_id": "R-D1-VRAM",
            "previous_value": 24,
            "approved_value": 48,
            "unit": "GiB",
            "approval_message_id": "message:m3-f03-unverified-change",
            "approval_message_sha256": hashlib.sha256(
                b"Unverified upstream constraint-change record for M3-F03"
            ).hexdigest(),
        }
    ]
    f03_path = OUT / "m3-f03-approved-change.bundle.json"
    f03_raw, f03_canonical = write_json(f03_path, f03)
    f03_rel = "evals/m3/forward-inputs/m3-f03-approved-change.bundle.json"
    write_validation("m3-f03", f03_rel, f03)
    cases.append(
        common_record(
            "m3-f03",
            f03_rel,
            f03_raw,
            f03_canonical,
            "valid",
            [],
            [],
            M1_ARTIFACT,
            source_m1_hash,
            [
                "The change record is preserved but does not authenticate approver identity",
                "M3 must apply none of the proposed resource expansion",
                "No empirical method performance or route execution",
            ],
        )
    )

    # F04 remains NOT_RUN because the existing independent non-nuclear M1
    # artifact is evidence_incomplete and cannot enter M2.1.1.
    f04_m1 = load_json(F04_M1_PATH)
    f04_m1_result = validate_m1_bundle(f04_m1)
    if f04_m1_result["status"] != "evidence_incomplete":
        raise SystemExit(f"m3-f04: unexpected M1 result {f04_m1_result}")
    f04_reason = "no independently accepted complete non-nuclear M1/M2 input"
    cases.append(
        common_record(
            "m3-f04",
            None,
            None,
            None,
            "NOT_RUN",
            [],
            [f04_reason, *f04_m1_result["evidence_gaps"]],
            F04_M1_ARTIFACT,
            raw_sha256(F04_M1_PATH),
            [
                "M1 stopped evidence_incomplete before M2",
                "No M2 bundle or M3 card was constructed",
                "No measurement, calibration, experiment, or route execution",
            ],
            constructed_context="019fd1cd-e259-72f3-9a47-b8570dd11d46",
            reviewed_context="019fd1cd-e259-72f3-9a47-b8570dd11d46:completed",
        )
    )
    (OUT / "m3-f04-not-run.md").write_text(
        "M3-F04: NOT_RUN\n"
        "reason: no independently accepted complete non-nuclear M1/M2 input\n"
        "M1 evidence status: evidence_incomplete\n"
        f"M1 evidence gaps: {', '.join(f04_m1_result['evidence_gaps'])}\n",
        encoding="utf-8",
        newline="\n",
    )

    f05 = copy.deepcopy(route)
    f05["route_output"][
        "hypothesis"
    ] = "Nuclear engineering ML transfer remains a bounded hypothesis pending target-domain decisive evidence"
    f05_path = OUT / "m3-f05-nuclear-ml.bundle.json"
    f05_raw, f05_canonical = write_json(f05_path, f05)
    f05_rel = "evals/m3/forward-inputs/m3-f05-nuclear-ml.bundle.json"
    write_validation("m3-f05", f05_rel, f05)
    cases.append(
        common_record(
            "m3-f05",
            f05_rel,
            f05_raw,
            f05_canonical,
            "valid",
            [],
            [],
            M1_ARTIFACT,
            source_m1_hash,
            [
                "Structural M2 validity does not prove nuclear transfer",
                "Safety support remains limited to exact embedded source basis",
                "No plant data, simulator, training, deployment, licensing, or safety conclusion",
            ],
        )
    )

    write_json(
        OUT / "manifest.json",
        {
            "schema_version": "m3.1-forward-inputs",
            "evidence_class": "independent_m2_input_preparation",
            "preparation_context": PREPARATION_CONTEXT,
            "cases": cases,
        },
    )


if __name__ == "__main__":
    prepare()
