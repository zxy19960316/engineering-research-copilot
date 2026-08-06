#!/usr/bin/env python3
"""Print a read-only, complete M3 prerequisite audit with byte diagnostics."""

from __future__ import annotations

import json
import sys

from audit_forward_inputs import audit_manifest


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) != 1:
        return 2
    result = audit_manifest(arguments[0])
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0 if result.get("status") == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
