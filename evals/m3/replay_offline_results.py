#!/usr/bin/env python3
"""Replay frozen M3 fixtures and compare their exact contract outcomes."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import NoReturn


M3_DIR = Path(__file__).resolve().parent
REPO_ROOT = M3_DIR.parents[1]
SCRIPTS_DIR = REPO_ROOT / "skills" / "engineering-research-copilot" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from validate_m3_method_bundle import validate_m3_bundle  # noqa: E402


MANIFEST_FIELDS = {"schema_version", "evidence_class", "cases"}
CASE_FIELDS = {
    "case_id",
    "fixture",
    "expected_status",
    "expected_errors",
    "expected_evidence_gaps",
}


class ReplayContractError(ValueError):
    """Signal a closed replay input failure without exposing input details."""


def _reject_contract() -> NoReturn:
    raise ReplayContractError("invalid_replay_contract")


def _reject_constant(_value: str) -> NoReturn:
    _reject_contract()


def _closed_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            _reject_contract()
        result[key] = value
    return result


def _load_json(path: Path) -> object:
    try:
        return json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_closed_object,
            parse_constant=_reject_constant,
        )
    except ReplayContractError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError):
        _reject_contract()


def _valid_string_list(value: object) -> bool:
    return (
        isinstance(value, list)
        and all(isinstance(item, str) and bool(item.strip()) for item in value)
        and len(value) == len(set(value))
    )


def _validated_cases(manifest: object, fixture_dir: Path) -> list[dict]:
    if not isinstance(manifest, dict) or set(manifest) != MANIFEST_FIELDS:
        _reject_contract()
    if (
        manifest["schema_version"] != "m3.1-adversarial-cases"
        or manifest["evidence_class"] != "offline_contract_fixture"
        or not isinstance(manifest["cases"], list)
        or not manifest["cases"]
    ):
        _reject_contract()

    case_ids: set[str] = set()
    fixture_names: set[str] = set()
    for declared in manifest["cases"]:
        if not isinstance(declared, dict) or set(declared) != CASE_FIELDS:
            _reject_contract()
        case_id = declared["case_id"]
        fixture_name = declared["fixture"]
        if (
            not isinstance(case_id, str)
            or not case_id.strip()
            or case_id in case_ids
            or not isinstance(fixture_name, str)
            or not fixture_name
            or fixture_name in fixture_names
            or not isinstance(declared["expected_status"], str)
            or declared["expected_status"] not in {"valid", "invalid"}
            or not _valid_string_list(declared["expected_errors"])
            or not _valid_string_list(declared["expected_evidence_gaps"])
        ):
            _reject_contract()
        fixture_path = Path(fixture_name)
        if (
            fixture_path.is_absolute()
            or fixture_path.name != fixture_name
            or fixture_path.suffix != ".json"
        ):
            _reject_contract()
        case_ids.add(case_id)
        fixture_names.add(fixture_name)

    try:
        fixture_root = fixture_dir.resolve(strict=True)
        if not fixture_root.is_dir():
            _reject_contract()
        entries = list(fixture_root.iterdir())
    except ReplayContractError:
        raise
    except OSError:
        _reject_contract()
    try:
        if any(
            not entry.is_file() or entry.is_symlink() or entry.suffix != ".json"
            for entry in entries
        ):
            _reject_contract()
    except OSError:
        _reject_contract()
    if {entry.name for entry in entries} != fixture_names:
        _reject_contract()
    for fixture_name in fixture_names:
        declared_path = fixture_root / fixture_name
        try:
            resolved = declared_path.resolve(strict=True)
        except (OSError, RuntimeError):
            _reject_contract()
        if resolved.parent != fixture_root or not resolved.is_file():
            _reject_contract()
    return manifest["cases"]


def _json_bytes(payload: object) -> bytes:
    return (
        json.dumps(
            payload,
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _write_json_atomic(path: Path, payload: object) -> None:
    descriptor = -1
    temp_path: Path | None = None
    try:
        descriptor, temp_name = tempfile.mkstemp(
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
        )
        temp_path = Path(temp_name)
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = -1
            handle.write(_json_bytes(payload))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
        temp_path = None
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if temp_path is not None:
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass


def evaluate(manifest_path: Path) -> dict:
    manifest = _load_json(manifest_path)
    fixture_dir = manifest_path.parent / "fixtures"
    declared_cases = _validated_cases(manifest, fixture_dir)
    cases = []
    for declared in declared_cases:
        fixture_path = fixture_dir / declared["fixture"]
        payload = _load_json(fixture_path)
        if not isinstance(payload, dict):
            _reject_contract()
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
    if arguments not in ([], ["--record"]):
        print(json.dumps({"error": "unexpected_arguments", "status": "invalid"}))
        return 1
    manifest_path = M3_DIR / "adversarial-cases.json"
    frozen_path = M3_DIR / "offline-results.json"
    try:
        current = evaluate(manifest_path)
    except ReplayContractError:
        print(json.dumps({"error": "invalid_replay_contract", "status": "invalid"}))
        return 1
    if arguments == ["--record"]:
        if not current["all_matched"]:
            matched_frozen = False
        else:
            try:
                _write_json_atomic(frozen_path, current)
            except (OSError, TypeError, ValueError):
                print(json.dumps({"error": "record_write_failed", "status": "invalid"}))
                return 1
            matched_frozen = True
    else:
        try:
            frozen = _load_json(frozen_path)
        except ReplayContractError:
            print(json.dumps({"error": "invalid_frozen_record", "status": "invalid"}))
            return 1
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
