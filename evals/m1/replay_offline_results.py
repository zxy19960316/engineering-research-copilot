#!/usr/bin/env python3
"""Replay frozen M1 fixture results without network access."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


REPOSITORY = Path(__file__).resolve().parents[2]
SCRIPTS = REPOSITORY / "skills" / "engineering-research-copilot" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from validate_m1_bundle import validate_bundle  # noqa: E402


EXIT_BY_STATUS = {"valid": 0, "invalid": 1, "evidence_incomplete": 2}


def replay_records(records: list[dict[str, Any]], root: Path) -> dict[str, Any]:
    """Compare frozen expectations with fresh in-process validator results."""

    mismatches: list[dict[str, Any]] = []
    for expected in records:
        fixture = expected["fixture"]
        payload = json.loads((root / fixture).read_text(encoding="utf-8"))
        actual = validate_bundle(payload)
        actual_exit = EXIT_BY_STATUS[actual["status"]]
        compared = {
            "exit_code": actual_exit,
            "status": actual["status"],
            "errors": actual["errors"],
            "evidence_gaps": actual["evidence_gaps"],
        }
        wanted = {key: expected[key] for key in compared}
        if compared != wanted:
            mismatches.append(
                {"fixture": fixture, "expected": wanted, "actual": compared}
            )
    return {"status": "valid" if not mismatches else "invalid", "mismatches": mismatches}


def main() -> int:
    manifest = json.loads(
        (REPOSITORY / "evals" / "m1" / "offline-results.json").read_text(
            encoding="utf-8"
        )
    )
    result = replay_records(manifest["results"], REPOSITORY)
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return 0 if result["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
