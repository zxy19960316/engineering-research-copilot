#!/usr/bin/env python3
"""Replay frozen M1 machine artifacts without network access."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable


REPOSITORY = Path(__file__).resolve().parents[2]
RESULTS = REPOSITORY / "evals" / "m1" / "results"
SCRIPTS = REPOSITORY / "skills" / "engineering-research-copilot" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from validate_citation_gate import validate_gate  # noqa: E402
from validate_m1_bundle import validate_bundle  # noqa: E402


CASES: tuple[dict[str, Any], ...] = (
    {
        "case_id": "case-a-pwr-sb-loca",
        "artifact": "2026-08-04-pwr-sb-loca-rerun.bundle.json",
        "validation": "2026-08-04-pwr-sb-loca-rerun.validation.json",
        "provenance": "2026-08-04-pwr-sb-loca-rerun.provenance.json",
        "expected_status": "valid",
        "validator": validate_bundle,
    },
    {
        "case_id": "case-b-bearing-fault",
        "artifact": "2026-08-04-bearing-fault-rerun-2.bundle.json",
        "validation": "2026-08-04-bearing-fault-rerun-2.validation.json",
        "provenance": "2026-08-04-bearing-fault-rerun-2.provenance.json",
        "expected_status": "evidence_incomplete",
        "validator": validate_bundle,
    },
    {
        "case_id": "case-c-citation-audit",
        "artifact": "2026-08-04-citation-audit.gate.json",
        "validation": "2026-08-04-citation-audit.validation.json",
        "provenance": "2026-08-04-citation-audit.provenance.json",
        "expected_status": "valid",
        "validator": validate_gate,
    },
)
PROVENANCE_FIELDS = {
    "schema_version",
    "case_id",
    "run_commit",
    "input_markdown",
    "input_frozen_range",
    "read_other_cases",
    "verification_window",
    "tools",
    "authoritative_sources",
    "execution_deviations",
    "bundle_sha256",
    "validation_sha256",
}
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def _normalized_sha256(path: Path) -> str:
    content = path.read_bytes()
    normalized = content.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(normalized).hexdigest()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _valid_provenance(provenance: Any, case_id: str) -> bool:
    if not isinstance(provenance, dict) or set(provenance) != PROVENANCE_FIELDS:
        return False
    window = provenance.get("verification_window")
    list_fields = ("tools", "authoritative_sources", "execution_deviations")
    return (
        provenance.get("schema_version") == "m1-provenance.1"
        and provenance.get("case_id") == case_id
        and all(
            isinstance(provenance.get(field), str) and provenance[field].strip()
            for field in ("run_commit", "input_markdown", "input_frozen_range")
        )
        and provenance.get("read_other_cases") is False
        and isinstance(window, dict)
        and set(window) == {"timezone", "started_at", "ended_at"}
        and all(isinstance(value, str) and value.strip() for value in window.values())
        and all(
            isinstance(provenance.get(field), list)
            and all(isinstance(value, str) and value.strip() for value in provenance[field])
            for field in list_fields
        )
        and all(
            isinstance(provenance.get(field), str)
            and SHA256_PATTERN.fullmatch(provenance[field]) is not None
            for field in ("bundle_sha256", "validation_sha256")
        )
    )


def replay() -> dict[str, Any]:
    summaries: list[dict[str, Any]] = []
    mismatches: list[dict[str, str]] = []
    for case in CASES:
        case_id = case["case_id"]
        artifact_path = RESULTS / case["artifact"]
        validation_path = RESULTS / case["validation"]
        provenance_path = RESULTS / case["provenance"]
        try:
            artifact = _load_json(artifact_path)
            expected = _load_json(validation_path)
            provenance = _load_json(provenance_path)
        except (OSError, UnicodeError, json.JSONDecodeError):
            mismatches.append({"case_id": case_id, "reason": "unreadable_artifact"})
            continue

        if not _valid_provenance(provenance, case_id):
            mismatches.append({"case_id": case_id, "reason": "invalid_provenance"})
        if provenance.get("bundle_sha256") != _normalized_sha256(artifact_path):
            mismatches.append({"case_id": case_id, "reason": "artifact_hash_mismatch"})
        if provenance.get("validation_sha256") != _normalized_sha256(validation_path):
            mismatches.append({"case_id": case_id, "reason": "validation_hash_mismatch"})

        validator: Callable[[Any], dict[str, Any]] = case["validator"]
        actual = validator(artifact)
        if actual != expected:
            mismatches.append({"case_id": case_id, "reason": "validation_output_mismatch"})
        if actual.get("status") != case["expected_status"]:
            mismatches.append({"case_id": case_id, "reason": "unexpected_status"})
        summaries.append(
            {
                "case_id": case_id,
                "status": actual.get("status"),
                "artifact_sha256": _normalized_sha256(artifact_path),
                "validation_sha256": _normalized_sha256(validation_path),
            }
        )

    return {
        "status": "invalid" if mismatches else "valid",
        "cases": summaries,
        "mismatches": mismatches,
    }


def main() -> int:
    try:
        result = replay()
    except Exception:
        result = {
            "status": "invalid",
            "cases": [],
            "mismatches": [{"case_id": "replay", "reason": "malformed_artifact"}],
        }
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return 0 if result["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
