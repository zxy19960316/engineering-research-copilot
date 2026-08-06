#!/usr/bin/env python3
"""Compose one closed M3 bundle from immutable M2 and compact model payloads."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

from validate_m2_direction_bundle import (
    canonical_sha256,
    validate_bundle as validate_m2_bundle,
)
from validate_m3_method_bundle import validate_m3_bundle


PAYLOAD_FIELDS = {"coaching_mode", "method_cards", "domain_overlays"}
SCHEMA_VERSION = "m3.1"


class _ComposeFailure(Exception):
    def __init__(self, code: str, **detail: Any) -> None:
        super().__init__(code)
        self.code = code
        self.detail = detail


def _closed_receipt(status: str, **fields: Any) -> dict[str, Any]:
    return {"status": status, **fields}


def _print_receipt(receipt: dict[str, Any]) -> None:
    print(
        json.dumps(
            receipt,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    )


def _reject_constant(_: str) -> None:
    raise ValueError("non-finite number")


def _load_object(path: Path, label: str) -> tuple[bytes, dict[str, Any]]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise _ComposeFailure(f"{label}_unreadable") from exc
    if raw.startswith(b"\xef\xbb\xbf"):
        raise _ComposeFailure(f"{label}_utf8_bom_forbidden")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise _ComposeFailure(
            f"{label}_invalid_utf8",
            byte_start=exc.start,
            byte_end=exc.end,
        ) from exc
    try:
        value = json.loads(text, parse_constant=_reject_constant)
    except json.JSONDecodeError as exc:
        raise _ComposeFailure(
            f"{label}_invalid_json",
            line=exc.lineno,
            column=exc.colno,
            position=exc.pos,
        ) from exc
    except ValueError as exc:
        raise _ComposeFailure(f"{label}_non_finite_number") from exc
    if not isinstance(value, dict):
        raise _ComposeFailure(f"{label}_must_be_object")
    return raw, value


def _selected_direction(source_m2: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    try:
        selected_id = source_m2["direction_decision"]["selected_direction_id"]
        directions = source_m2["direction_portfolio"]["directions"]
    except (KeyError, TypeError) as exc:
        raise _ComposeFailure("selected_direction_missing") from exc
    matches = [
        direction
        for direction in directions
        if isinstance(direction, dict) and direction.get("direction_id") == selected_id
    ]
    if not isinstance(selected_id, str) or len(matches) != 1:
        raise _ComposeFailure("selected_direction_missing")
    return selected_id, matches[0]


def compose_bundle(
    source_m2: dict[str, Any], model_payload: dict[str, Any]
) -> dict[str, Any]:
    """Return a deep-copied eight-field M3 envelope or fail closed."""

    m2_result = validate_m2_bundle(source_m2)
    if m2_result.get("status") != "valid":
        raise _ComposeFailure(
            "invalid_source_m2_bundle",
            validator_errors=m2_result.get("errors", []),
            validator_evidence_gaps=m2_result.get("evidence_gaps", []),
        )

    unknown = sorted(set(model_payload) - PAYLOAD_FIELDS)
    if unknown:
        raise _ComposeFailure("unknown_payload_fields", fields=unknown)
    missing = sorted(PAYLOAD_FIELDS - set(model_payload))
    if missing:
        raise _ComposeFailure("missing_payload_fields", fields=missing)
    if not isinstance(model_payload.get("coaching_mode"), str):
        raise _ComposeFailure("invalid_payload_coaching_mode")
    if not isinstance(model_payload.get("method_cards"), list):
        raise _ComposeFailure("invalid_payload_method_cards")
    if not isinstance(model_payload.get("domain_overlays"), list):
        raise _ComposeFailure("invalid_payload_domain_overlays")

    selected_id, selected_direction = _selected_direction(source_m2)
    bundle = {
        "schema_version": SCHEMA_VERSION,
        "source_m2_bundle": copy.deepcopy(source_m2),
        "source_m2_bundle_hash": canonical_sha256(source_m2),
        "selected_direction_id": selected_id,
        "selected_direction_hash": canonical_sha256(selected_direction),
        "coaching_mode": copy.deepcopy(model_payload["coaching_mode"]),
        "method_cards": copy.deepcopy(model_payload["method_cards"]),
        "domain_overlays": copy.deepcopy(model_payload["domain_overlays"]),
    }
    m3_result = validate_m3_bundle(bundle)
    if m3_result.get("status") != "valid":
        raise _ComposeFailure(
            "invalid_composed_m3_bundle",
            validator_errors=m3_result.get("errors", []),
            validator_evidence_gaps=m3_result.get("evidence_gaps", []),
        )
    return bundle


def _serialize_bundle(bundle: dict[str, Any]) -> bytes:
    return (
        json.dumps(
            bundle,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _atomic_write_new(path: Path, raw: bytes) -> None:
    if path.exists():
        raise _ComposeFailure("output_already_exists")
    if not path.parent.is_dir():
        raise _ComposeFailure("output_parent_missing")
    file_descriptor = -1
    staging_path: Path | None = None
    try:
        file_descriptor, staging_name = tempfile.mkstemp(
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
        )
        staging_path = Path(staging_name)
        with os.fdopen(file_descriptor, "wb") as stream:
            file_descriptor = -1
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        if path.exists():
            raise _ComposeFailure("output_already_exists")
        os.replace(staging_path, path)
        staging_path = None
    except _ComposeFailure:
        raise
    except OSError as exc:
        raise _ComposeFailure("output_write_failed") from exc
    finally:
        if file_descriptor >= 0:
            os.close(file_descriptor)
        if staging_path is not None:
            try:
                staging_path.unlink(missing_ok=True)
            except OSError:
                pass


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) != 3:
        _print_receipt(_closed_receipt("invalid", error="expected_three_paths"))
        return 1

    source_path, payload_path, output_path = map(Path, arguments)
    if output_path.exists():
        _print_receipt(_closed_receipt("invalid", error="output_already_exists"))
        return 1

    try:
        m2_raw, source_m2 = _load_object(source_path, "m2")
        payload_raw, model_payload = _load_object(payload_path, "payload")
        bundle = compose_bundle(source_m2, model_payload)
        output_raw = _serialize_bundle(bundle)
        _atomic_write_new(output_path, output_raw)
    except _ComposeFailure as exc:
        _print_receipt(_closed_receipt("invalid", error=exc.code, **exc.detail))
        return 1

    _print_receipt(
        _closed_receipt(
            "composed",
            m2_raw_sha256=hashlib.sha256(m2_raw).hexdigest(),
            m2_canonical_sha256=canonical_sha256(source_m2),
            payload_raw_sha256=hashlib.sha256(payload_raw).hexdigest(),
            payload_canonical_sha256=canonical_sha256(model_payload),
            output_raw_sha256=hashlib.sha256(output_raw).hexdigest(),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
