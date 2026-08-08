#!/usr/bin/env python3
"""Freeze observed M3.1.1 forward outcomes without rerunning any validator."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "evals" / "m3" / "results" / "forward-r2"
INPUTS = ROOT / "evals" / "m3" / "forward-inputs-r2"
PROMPTS = RESULTS / "prompts"
MANIFEST_PATH = RESULTS / "acceptance-manifest.json"
REPORT_PATH = ROOT / "evals" / "m3" / "results" / "2026-08-05-forward-evaluation-r2.md"

EXPECTED: dict[str, tuple[str, list[str], list[str]]] = {
    "m3-f01": ("valid", [], []),
    "m3-f02": ("valid", [], []),
    "m3-f03": ("invalid", ["unsupported_approved_constraint_change_provenance"], []),
    "m3-f04": ("valid", [], []),
    "m3-f05": ("valid", [], []),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_context(path: Path | None) -> dict[str, Any]:
    if path is None or not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        value = None
    if isinstance(value, dict):
        return value
    values: dict[str, Any] = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, raw = line.split(":", 1)
        key = key.strip()
        if not key.replace("_", "").isalnum() or not key:
            continue
        raw = raw.strip()
        try:
            values[key] = json.loads(raw)
        except json.JSONDecodeError:
            values[key] = raw.strip('"\'')
    return values


def load_validation(path: Path | None) -> dict[str, Any]:
    if path is None or not path.is_file():
        return {"status": "NOT_RUN", "errors": [], "evidence_gaps": []}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {"status": "invalid_receipt", "errors": ["invalid_validation_json"], "evidence_gaps": []}
    if not isinstance(value, dict):
        return {"status": "invalid_receipt", "errors": ["validation_not_object"], "evidence_gaps": []}
    return {
        "status": value.get("status", "invalid_receipt"),
        "errors": value.get("errors", []),
        "evidence_gaps": value.get("evidence_gaps", []),
    }


def build_case(case_id: str) -> dict[str, Any]:
    input_names = {
        "m3-f01": "m3-f01-bounded-confirmed.bundle.json",
        "m3-f02": "m3-f02-route-compatible.bundle.json",
        "m3-f03": "m3-f03-approved-change.bundle.json",
        "m3-f05": "m3-f05-nuclear-ml.bundle.json",
    }
    input_path = INPUTS / input_names[case_id] if case_id in input_names else None
    prompt_path = PROMPTS / f"{case_id}.prompt.txt"
    output_path = RESULTS / f"{case_id}.output.json"
    validation_path = RESULTS / f"{case_id}.validation.json"
    context_path = RESULTS / f"{case_id}.context.md"
    if case_id == "m3-f04":
        input_path = None
        output_path = None
        validation_path = None
        context_path = RESULTS / "m3-f04.not-run.md"

    observed = load_validation(validation_path)
    context = parse_context(context_path)
    expected_status, expected_errors, expected_gaps = EXPECTED[case_id]
    observed_tuple = (
        observed["status"],
        observed["errors"],
        observed["evidence_gaps"],
    )
    accepted = (
        observed_tuple == EXPECTED[case_id]
        and input_path is not None
        and output_path is not None
        and output_path.is_file()
        and validation_path is not None
        and validation_path.is_file()
        and context.get("finalization_count") == 1
        and context.get("validator_invocation_count") == 1
        and context.get("side_effects") == []
        and context.get("deviations") == []
    )
    return {
        "case_id": case_id,
        "input_path": input_path.relative_to(ROOT).as_posix() if input_path else None,
        "input_raw_sha256": sha256(input_path) if input_path and input_path.is_file() else None,
        "prompt_path": prompt_path.relative_to(ROOT).as_posix(),
        "prompt_sha256": sha256(prompt_path),
        "output_path": output_path.relative_to(ROOT).as_posix() if output_path and output_path.is_file() else None,
        "output_raw_sha256": sha256(output_path) if output_path and output_path.is_file() else None,
        "validation_path": validation_path.relative_to(ROOT).as_posix() if validation_path and validation_path.is_file() else None,
        "validation_raw_sha256": sha256(validation_path) if validation_path and validation_path.is_file() else None,
        "context_path": context_path.relative_to(ROOT).as_posix() if context_path.is_file() else None,
        "expected_status": expected_status,
        "expected_errors": expected_errors,
        "expected_evidence_gaps": expected_gaps,
        "observed_status": observed["status"],
        "observed_errors": observed["errors"],
        "observed_evidence_gaps": observed["evidence_gaps"],
        "finalization_count": context.get("finalization_count", 0),
        "validator_invocation_count": context.get("validator_invocation_count", 0),
        "loaded_references": context.get("loaded_references", []),
        "side_effects": context.get("side_effects", []),
        "deviations": context.get("deviations", []),
        "limitations": context.get("limitations", []),
        "accepted": accepted,
    }


def main() -> int:
    refresh = "--refresh" in sys.argv[1:]
    if not refresh and (MANIFEST_PATH.exists() or REPORT_PATH.exists()):
        raise SystemExit("acceptance_record_already_exists")
    cases = [build_case(case_id) for case_id in ("m3-f01", "m3-f02", "m3-f03", "m3-f04", "m3-f05")]
    previous_paths = []
    for case_id in ("m3-f02", "m3-f03", "m3-f05"):
        for suffix in ("output.json", "validation.json", "context.md"):
            path = ROOT / "evals" / "m3" / "results" / "forward" / f"{case_id}.{suffix}"
            previous_paths.append({"path": path.relative_to(ROOT).as_posix(), "raw_sha256": sha256(path)})
    manifest = {
        "schema_version": "m3.1-forward-acceptance-r2",
        "status": "not_accepted",
        "m3_status": "IN_PROGRESS",
        "m4_status": "NOT_STARTED",
        "cases": cases,
        "preserved_previous_results": previous_paths,
        "notes": [
            "This record freezes observed fresh-context outcomes and is not a closure claim.",
            "F01, F03, and F05 retain one-shot validator failures; F04 is NOT_RUN because its upstream non-nuclear M1/M2 prerequisite is absent.",
            "Only F02 matched its closure expectation. No case was repaired or retried.",
        ],
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    with MANIFEST_PATH.open("w", encoding="utf-8", newline="") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    lines = [
        "# M3.1.1 fresh-context forward evaluation — observed outcomes",
        "",
        "Date: `2026-08-05`",
        "",
        "Status: `NOT_ACCEPTED`; M3 remains `IN_PROGRESS`; M4 remains `NOT_STARTED`.",
        "",
        "| Case | Observed validator result | One-shot evidence | Acceptance |",
        "| --- | --- | --- | --- |",
    ]
    for case in cases:
        observed = f"{case['observed_status']} {case['observed_errors']}" if case["observed_errors"] else case["observed_status"]
        one_shot = f"finalization={case['finalization_count']}, validator={case['validator_invocation_count']}"
        lines.append(f"| {case['case_id']} | `{observed}` | `{one_shot}` | `{case['accepted']}` |")
    lines.extend(
        [
            "",
            "F01 preserved `unreadable_or_invalid_json`; F02 is the only observed valid case; F03 preserved extra structural errors rather than being relabeled as the single expected code; F04 is `NOT_RUN`; F05 preserved a one-shot invalid receipt without an output bundle.",
            "",
            "No method execution, experiment, simulation, training, download, service, deployment, resource allocation, or safety/operational claim occurred. The previous revision-one failure files remain preserved under `evals/m3/results/forward/`.",
            "",
            "The exact closure-head push is intentionally not authorized by these results: the fresh acceptance gate and F04 prerequisite gate are not green.",
            "",
        ]
    )
    with REPORT_PATH.open("w", encoding="utf-8", newline="") as handle:
        handle.write("\n".join(lines))
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
