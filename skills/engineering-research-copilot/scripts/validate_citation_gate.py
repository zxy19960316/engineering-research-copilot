#!/usr/bin/env python3
"""Validate an offline citation-conflict terminal object."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "citation-gate.1"
ROOT_FIELDS = {
    "schema_version",
    "terminal_state",
    "verification_status",
    "recommendation_eligible",
    "checked_sources",
    "blocking_reasons",
}
SOURCE_FIELDS = {"source_type", "canonical_record", "checked_at", "result"}
SOURCE_TYPES = {"doi_registry", "official_repository", "pubmed", "publisher_landing"}
SOURCE_RESULTS = {"match", "conflict", "not_found", "unavailable"}


def _closed(status: str, errors: list[str] | None = None) -> dict[str, Any]:
    return {"status": status, "errors": errors or [], "evidence_gaps": []}


def _add(errors: list[str], code: str) -> None:
    if code not in errors:
        errors.append(code)


def _nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _valid_timestamp(value: Any) -> bool:
    if not _nonempty_text(value):
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def _valid_source(source: Any) -> bool:
    return (
        isinstance(source, dict)
        and set(source) == SOURCE_FIELDS
        and source.get("source_type") in SOURCE_TYPES
        and _nonempty_text(source.get("canonical_record"))
        and _valid_timestamp(source.get("checked_at"))
        and source.get("result") in SOURCE_RESULTS
    )


def _validate_gate(gate: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if "round1" in gate or "round2" in gate:
        _add(errors, "round_field_in_citation_gate")
    unknown = set(gate) - ROOT_FIELDS
    if unknown:
        _add(errors, "unknown_root_field")
    if set(gate) - unknown != ROOT_FIELDS:
        _add(errors, "missing_root_field")
    if gate.get("schema_version") != SCHEMA_VERSION:
        _add(errors, "invalid_schema_version")
    if gate.get("terminal_state") != "CITATION_BLOCKED":
        _add(errors, "invalid_terminal_state")
    if gate.get("verification_status") != "conflicted":
        _add(errors, "invalid_verification_status")
    if gate.get("recommendation_eligible") is not False:
        _add(errors, "citation_gate_marked_eligible")

    sources = gate.get("checked_sources")
    if not isinstance(sources, list) or not sources:
        _add(errors, "missing_checked_sources")
    elif any(not _valid_source(source) for source in sources):
        _add(errors, "invalid_checked_source")
    elif not any(source["result"] == "conflict" for source in sources):
        _add(errors, "missing_conflicting_source")

    reasons = gate.get("blocking_reasons")
    if (
        not isinstance(reasons, list)
        or not reasons
        or any(not _nonempty_text(reason) for reason in reasons)
    ):
        _add(errors, "invalid_blocking_reasons")
    return _closed("invalid", errors) if errors else _closed("valid")


def validate_gate(gate: Any) -> dict[str, Any]:
    """Return one closed result without performing I/O."""

    if not isinstance(gate, dict):
        return _closed("invalid", ["malformed_gate"])
    try:
        return _validate_gate(gate)
    except Exception:
        return _closed("invalid", ["malformed_gate"])


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) != 1:
        output = _closed("invalid", ["expected_one_json_path"])
    else:
        try:
            payload = json.loads(Path(arguments[0]).read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            output = _closed("invalid", ["unreadable_or_invalid_json"])
        else:
            output = validate_gate(payload)
    print(json.dumps(output, ensure_ascii=False, separators=(",", ":")))
    return 0 if output["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
