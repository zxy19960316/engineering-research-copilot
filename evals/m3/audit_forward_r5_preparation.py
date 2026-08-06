#!/usr/bin/env python3
"""Audit the r5 frozen preparation state without consuming a case."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from audit_forward_r5_acceptance import R4_MANIFEST_RELATIVE, _safe_file
from dispatch_forward_r5 import R5_RESULT_ROOT, preflight_batch
from r5_dispatch_contract import CASE_IDS, COUNTER_KEYS, R5_SCHEMA_VERSION


REPO_ROOT = Path(__file__).resolve().parents[2]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path, errors: list[str]) -> dict[str, Any] | None:
    try:
        raw = path.read_bytes()
        if raw.startswith(b"\xef\xbb\xbf"):
            raise ValueError("utf8_bom_forbidden")
        value = json.loads(raw.decode("utf-8", errors="strict"))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        errors.append("invalid_manifest_json")
        return None
    if not isinstance(value, dict):
        errors.append("manifest_object_required")
        return None
    return value


def _check_historical_r4(value: object, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append("historical_r4_reference_invalid")
        return {}
    if value.get("path") != R4_MANIFEST_RELATIVE:
        errors.append("historical_r4_path_invalid")
    if value.get("count_as_r5") is not False:
        errors.append("historical_r4_counting_forbidden")
    path = _safe_file(value.get("path"), "historical_r4_manifest", errors)
    if path is not None:
        if not isinstance(value.get("raw_sha256"), str) or _sha256(path) != value["raw_sha256"]:
            errors.append("historical_r4_manifest_hash_mismatch")
        try:
            historical = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            historical = None
        if not isinstance(historical, dict) or historical.get("status") != "blocked_not_accepted":
            errors.append("historical_r4_not_blocked")
    return {
        "path": value.get("path"),
        "raw_sha256": value.get("raw_sha256"),
        "status": value.get("status"),
        "count_as_r5": value.get("count_as_r5"),
    }


def _check_zero_counters(manifest: dict[str, Any], errors: list[str]) -> dict[str, int]:
    if "fresh_contexts_consumed" in manifest:
        errors.append("legacy_fresh_context_counter_forbidden")
    counters = manifest.get("counters")
    if not isinstance(counters, dict) or set(counters) != set(COUNTER_KEYS):
        errors.append("manifest_counter_keys_invalid")
        return {key: 0 for key in COUNTER_KEYS}
    for key in COUNTER_KEYS:
        if counters.get(key) != 0:
            errors.append(f"manifest_counter_nonzero:{key}")
    return {key: counters[key] for key in COUNTER_KEYS}


def audit_preparation(manifest_path: str | Path) -> dict[str, Any]:
    errors: list[str] = []
    manifest = _load_json(Path(manifest_path), errors)
    if manifest is None:
        return {
            "status": "invalid",
            "cases": [],
            "counters": {key: 0 for key in COUNTER_KEYS},
            "errors": sorted(set(errors)),
            "evidence_gaps": [],
            "batch_preflight": {"status": "NOT_RUN", "side_effects": []},
        }
    if manifest.get("schema_version") != R5_SCHEMA_VERSION:
        errors.append("manifest_schema_version_invalid")
    if manifest.get("status") != "ready_for_authorized_fresh_contexts":
        errors.append("manifest_status_not_ready")
    if manifest.get("prompts_frozen") is not True:
        errors.append("prompts_not_frozen")
    counters = _check_zero_counters(manifest, errors)
    try:
        declared_root = (REPO_ROOT / manifest.get("result_root", "")).resolve()
        if declared_root != R5_RESULT_ROOT.resolve():
            errors.append("result_root_not_canonical")
    except (AttributeError, TypeError, ValueError):
        errors.append("result_root_not_canonical")
    raw_cases = manifest.get("cases")
    if not isinstance(raw_cases, list) or len(raw_cases) != len(CASE_IDS):
        errors.append("manifest_cases_invalid")
    else:
        case_ids = [case.get("case_id") for case in raw_cases if isinstance(case, dict)]
        if case_ids != list(CASE_IDS) or len(set(case_ids)) != len(CASE_IDS):
            errors.append("manifest_case_ids_invalid")
        for case in raw_cases:
            if isinstance(case, dict):
                for key in case:
                    if key in {"task_id", "fresh_context_id", "state", "accepted"}:
                        errors.append(f"preparation_case_field_forbidden:{key}")
    historical = _check_historical_r4(manifest.get("historical_r4"), errors)
    batch = preflight_batch(Path(manifest_path), R5_RESULT_ROOT)
    errors.extend(batch.get("errors", []))
    cases = []
    for plan in batch.get("plans", []):
        cases.append(
            {
                "case_id": plan.get("case_id"),
                "status": "eligible" if plan.get("status") == "ready" else "invalid",
                "errors": plan.get("errors", []),
            }
        )
    if len(cases) != len(CASE_IDS):
        present = {case.get("case_id") for case in cases}
        for case_id in CASE_IDS:
            if case_id not in present:
                cases.append({"case_id": case_id, "status": "invalid", "errors": [f"case_not_preflighted:{case_id}"]})
    return {
        "status": "valid" if not errors else "invalid",
        "cases": cases,
        "counters": counters,
        "historical_r4": historical,
        "batch_preflight": {
            "status": "valid" if batch.get("status") == "ready" else "invalid",
            "case_ids_preflighted": batch.get("case_ids_preflighted", []),
            "side_effects": batch.get("side_effects", []),
        },
        "errors": sorted(set(errors)),
        "evidence_gaps": [],
    }


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) != 1:
        return 2
    result = audit_preparation(arguments[0])
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0 if result["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
