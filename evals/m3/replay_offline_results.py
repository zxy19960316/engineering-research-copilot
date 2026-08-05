#!/usr/bin/env python3
"""Replay frozen M3 fixtures and compare their exact contract outcomes."""

from __future__ import annotations

import json
import sys
from pathlib import Path


M3_DIR = Path(__file__).resolve().parent
REPO_ROOT = M3_DIR.parents[1]
SCRIPTS_DIR = REPO_ROOT / "skills" / "engineering-research-copilot" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from validate_m3_method_bundle import validate_m3_bundle  # noqa: E402


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


def evaluate(manifest_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    fixture_dir = manifest_path.parent / "fixtures"
    cases = []
    for declared in manifest["cases"]:
        fixture_path = fixture_dir / declared["fixture"]
        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
        actual = validate_m3_bundle(payload)
        expected = {
            "status": declared["expected_status"],
            "errors": declared["expected_errors"],
            "evidence_gaps": declared["expected_evidence_gaps"],
        }
        cases.append(
            {
                "fixture": declared["fixture"],
                "expected_status": expected["status"],
                "expected_errors": expected["errors"],
                "expected_evidence_gaps": expected["evidence_gaps"],
                "actual_status": actual["status"],
                "actual_errors": actual["errors"],
                "actual_evidence_gaps": actual["evidence_gaps"],
                "matched": actual == expected,
            }
        )
    return {
        "schema_version": "m3.1-offline-results",
        "evidence_class": "offline_contract_fixture",
        "cases": cases,
        "all_matched": all(case["matched"] for case in cases),
        "proves": [
            "M3.1 offline structural contract behavior for bounded and route-specific method coaching",
            "Exact rejection behavior for required card fields, source boundaries, confirmation, provenance, resource, route-traceability, and nuclear-transfer guards",
        ],
        "does_not_prove": [
            "Real citation existence or metadata accuracy",
            "Real experimental, simulation, model, transfer, or safety performance",
            "Execution of any experiment, simulation, training, download, deployment, service, or route",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    manifest_path = M3_DIR / "adversarial-cases.json"
    frozen_path = M3_DIR / "offline-results.json"
    current = evaluate(manifest_path)
    if arguments == ["--record"]:
        _write_json(frozen_path, current)
        matched_frozen = True
    elif arguments:
        print(json.dumps({"error": "unexpected_arguments", "status": "invalid"}))
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
    print(
        json.dumps(
            output,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        )
    )
    return 0 if output["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
