#!/usr/bin/env python3
"""Replay frozen M2 fixtures and compare their exact contract outcomes."""

from __future__ import annotations

import json
import sys
from pathlib import Path


M2_DIR = Path(__file__).resolve().parent
REPO_ROOT = M2_DIR.parents[1]
SCRIPTS_DIR = REPO_ROOT / "skills" / "engineering-research-copilot" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from validate_m2_direction_bundle import validate_bundle  # noqa: E402


def evaluate(manifest_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    fixture_dir = manifest_path.parent / "fixtures"
    cases = []
    for declared in manifest["cases"]:
        fixture_path = fixture_dir / declared["fixture"]
        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
        actual = validate_bundle(payload)
        expected_errors = declared["expected_errors"]
        matched = (
            actual["status"] == declared["expected_status"]
            and all(code in actual["errors"] for code in expected_errors)
        )
        cases.append(
            {
                "fixture": declared["fixture"],
                "expected_status": declared["expected_status"],
                "expected_errors": expected_errors,
                "actual_status": actual["status"],
                "actual_errors": actual["errors"],
                "actual_evidence_gaps": actual["evidence_gaps"],
                "matched": matched,
            }
        )
    return {
        "schema_version": "m2.1.1-offline-results",
        "evidence_class": "offline_contract_fixture",
        "cases": cases,
        "all_matched": all(case["matched"] for case in cases),
        "proves": [
            "M2.1.1 source lineage, confirmation provenance, route binding, claim coverage, preprint, precondition, axis, scorecard, and bounded-test contracts"
        ],
        "does_not_prove": [
            "Real citation existence or metadata accuracy",
            "Host-system user identity",
            "Real research-direction merit",
            "Target-domain transfer success",
            "Execution of any experiment, simulation, training, download, deployment, or large-resource route",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    manifest_path = M2_DIR / "adversarial-cases.json"
    frozen_path = M2_DIR / "offline-results.json"
    current = evaluate(manifest_path)
    if arguments == ["--record"]:
        frozen_path.write_text(
            json.dumps(current, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        matched_frozen = True
    elif arguments:
        print(json.dumps({"status": "invalid", "error": "unexpected_arguments"}))
        return 1
    else:
        frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
        matched_frozen = current == frozen
    output = {
        "status": "valid" if current["all_matched"] and matched_frozen else "invalid",
        "case_count": len(current["cases"]),
        "all_matched": current["all_matched"],
        "matched_frozen_record": matched_frozen,
    }
    print(json.dumps(output, ensure_ascii=False, separators=(",", ":")))
    return 0 if output["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
