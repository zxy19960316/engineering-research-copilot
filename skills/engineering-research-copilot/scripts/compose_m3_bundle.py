#!/usr/bin/env python3
"""Compose one closed M3 bundle from immutable M2 and compact model payloads."""

from __future__ import annotations

import copy
import hashlib
import json
import math
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
METHOD_CARD_FIELDS = {
    "schema_version",
    "card_id",
    "method_family",
    "applicability",
    "assumptions",
    "minimum_resources",
    "inherited_constraints",
    "baselines",
    "controls",
    "procedure_outline",
    "primary_metrics",
    "uncertainty_handling",
    "validation_checks",
    "failure_modes",
    "stop_conditions",
    "pivot_conditions",
    "safety_boundaries",
    "source_ledger",
}
APPLICABILITY_FIELDS = {
    "supported_claim_types",
    "required_inputs",
    "incompatible_conditions",
}
RESOURCE_FIELDS = {"resource", "required_value", "unit", "source_constraint_id"}
CONSTRAINT_FIELDS = {"constraint_id", "resource", "operator", "value", "unit"}
CRITERION_FIELDS = {"criterion_type", "metric_id", "operator", "value", "unit"}
SOURCE_LEDGER_FIELDS = {
    "source_id",
    "candidate_id",
    "basis_level",
    "support_types",
    "supports",
    "does_not_support",
    "limitations",
}
OVERLAY_FIELDS = {
    "schema_version",
    "overlay_id",
    "domain",
    "base_card_ids",
    "additional_assumptions",
    "additional_failure_modes",
    "additional_validation_checks",
    "additional_stop_conditions",
    "specialist_review_boundaries",
    "transfer_status",
    "source_ledger",
}
NONEMPTY_TEXT_FIELDS = {
    "assumptions",
    "baselines",
    "controls",
    "procedure_outline",
    "uncertainty_handling",
    "validation_checks",
    "failure_modes",
    "safety_boundaries",
}
METHOD_FAMILIES = {
    "experiment_measurement_uq",
    "modeling_simulation_vvuq",
    "control_optimization_identification",
    "signal_diagnostics",
    "data_ml_hybrid",
    "reliability_safety_risk",
}
CRITERION_OPERATORS = {"<", "<=", ">", ">="}
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


def _contract_error(
    code: str, path: str, expected: Any
) -> dict[str, Any]:
    return {"code": code, "path": path, "expected": expected}


def _nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _finite_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def _check_closed_object(
    value: Any,
    fields: set[str],
    path: str,
    label: str,
    errors: list[dict[str, Any]],
) -> bool:
    if not isinstance(value, dict):
        errors.append(_contract_error(f"{label}_object", path, "object"))
        return False
    missing = sorted(fields - set(value))
    unknown = sorted(set(value) - fields)
    if missing or unknown:
        expected: dict[str, Any] = {"fields": sorted(fields)}
        if missing:
            expected["missing"] = missing
        if unknown:
            expected["unknown"] = unknown
        errors.append(_contract_error(f"{label}_fields", path, expected))
        return False
    return True


def _check_text_list(
    value: Any,
    path: str,
    errors: list[dict[str, Any]],
    *,
    min_items: int = 1,
) -> None:
    if not isinstance(value, list):
        errors.append(_contract_error("list_type", path, "array"))
        return
    if len(value) < min_items:
        errors.append(
            _contract_error(
                "list_min_items", path, f"at least {min_items} non-empty item(s)"
            )
        )
    for index, item in enumerate(value):
        if not _nonempty_text(item):
            errors.append(
                _contract_error(
                    "text_item_type", f"{path}[{index}]", "non-empty string"
                )
            )


def _check_criterion(
    value: Any,
    path: str,
    expected_type: str,
    errors: list[dict[str, Any]],
) -> None:
    if not _check_closed_object(
        value, CRITERION_FIELDS, path, "criterion", errors
    ):
        return
    if value.get("criterion_type") != expected_type:
        errors.append(
            _contract_error(
                "criterion_type",
                f"{path}.criterion_type",
                expected_type,
            )
        )
    if not _nonempty_text(value.get("metric_id")):
        errors.append(
            _contract_error("criterion_metric_id", f"{path}.metric_id", "string")
        )
    if value.get("operator") not in CRITERION_OPERATORS:
        errors.append(
            _contract_error(
                "criterion_operator",
                f"{path}.operator",
                sorted(CRITERION_OPERATORS),
            )
        )
    if not _finite_number(value.get("value")):
        errors.append(
            _contract_error("criterion_value", f"{path}.value", "finite number")
        )
    if not _nonempty_text(value.get("unit")):
        errors.append(
            _contract_error("criterion_unit", f"{path}.unit", "string")
        )


def _check_rows(
    value: Any,
    path: str,
    fields: set[str],
    label: str,
    errors: list[dict[str, Any]],
    *,
    min_items: int = 1,
) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        errors.append(_contract_error("list_type", path, "array"))
        return []
    if len(value) < min_items:
        errors.append(
            _contract_error(
                f"{label}_min_items", path, f"at least {min_items} item(s)"
            )
        )
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(value):
        row_path = f"{path}[{index}]"
        if _check_closed_object(row, fields, row_path, label, errors):
            rows.append(row)
    return rows


def _check_card(card: Any, index: int, errors: list[dict[str, Any]]) -> None:
    path = f"method_cards[{index}]"
    if not _check_closed_object(
        card, METHOD_CARD_FIELDS, path, "method_card", errors
    ):
        return
    if card.get("schema_version") != SCHEMA_VERSION:
        errors.append(
            _contract_error("schema_version", f"{path}.schema_version", SCHEMA_VERSION)
        )
    if not _nonempty_text(card.get("card_id")):
        errors.append(_contract_error("card_id_type", f"{path}.card_id", "string"))
    if card.get("method_family") not in METHOD_FAMILIES:
        errors.append(
            _contract_error(
                "method_family_enum", f"{path}.method_family", sorted(METHOD_FAMILIES)
            )
        )
    if _check_closed_object(
        card.get("applicability"),
        APPLICABILITY_FIELDS,
        f"{path}.applicability",
        "applicability",
        errors,
    ):
        for field in sorted(APPLICABILITY_FIELDS):
            _check_text_list(
                card["applicability"][field],
                f"{path}.applicability.{field}",
                errors,
            )
    for field in sorted(NONEMPTY_TEXT_FIELDS):
        _check_text_list(card[field], f"{path}.{field}", errors)
    _check_rows(
        card["minimum_resources"],
        f"{path}.minimum_resources",
        RESOURCE_FIELDS,
        "minimum_resource",
        errors,
    )
    for resource_index, resource in enumerate(card["minimum_resources"]):
        resource_path = f"{path}.minimum_resources[{resource_index}]"
        if not isinstance(resource, dict) or set(resource) != RESOURCE_FIELDS:
            continue
        for field in ("resource", "unit", "source_constraint_id"):
            if not _nonempty_text(resource[field]):
                errors.append(
                    _contract_error(
                        "resource_text_type", f"{resource_path}.{field}", "string"
                    )
                )
        if not _finite_number(resource["required_value"]) or resource["required_value"] < 0:
            errors.append(
                _contract_error(
                    "resource_required_value", f"{resource_path}.required_value", "finite nonnegative number"
                )
            )
    _check_rows(
        card["inherited_constraints"],
        f"{path}.inherited_constraints",
        CONSTRAINT_FIELDS,
        "constraint",
        errors,
    )
    for constraint_index, constraint in enumerate(card["inherited_constraints"]):
        constraint_path = f"{path}.inherited_constraints[{constraint_index}]"
        if not isinstance(constraint, dict) or set(constraint) != CONSTRAINT_FIELDS:
            continue
        for field in ("constraint_id", "resource", "unit"):
            if not _nonempty_text(constraint[field]):
                errors.append(
                    _contract_error(
                        "constraint_text_type", f"{constraint_path}.{field}", "string"
                    )
                )
        if constraint["operator"] not in CRITERION_OPERATORS:
            errors.append(
                _contract_error(
                    "constraint_operator", f"{constraint_path}.operator", sorted(CRITERION_OPERATORS)
                )
            )
        if not _finite_number(constraint["value"]):
            errors.append(
                _contract_error(
                    "constraint_value", f"{constraint_path}.value", "finite number"
                )
            )
    primary_metrics = card["primary_metrics"]
    if not isinstance(primary_metrics, list):
        errors.append(_contract_error("primary_metrics_type", f"{path}.primary_metrics", "array"))
    else:
        if not primary_metrics:
            errors.append(
                _contract_error(
                    "primary_metrics_min_items", f"{path}.primary_metrics", "at least one metric ID"
                )
            )
        for metric_index, metric_id in enumerate(primary_metrics):
            if not _nonempty_text(metric_id):
                errors.append(
                    _contract_error(
                        "primary_metrics_item_type",
                        f"{path}.primary_metrics[{metric_index}]",
                        "string metric_id",
                    )
                )
    for field, criterion_type in (("stop_conditions", "stop"), ("pivot_conditions", "pivot")):
        criteria = card[field]
        if not isinstance(criteria, list):
            errors.append(_contract_error("list_type", f"{path}.{field}", "array"))
            continue
        if not criteria:
            errors.append(
                _contract_error(
                    f"{field}_min_items", f"{path}.{field}", "at least one criterion"
                )
            )
        for criterion_index, criterion in enumerate(criteria):
            _check_criterion(
                criterion,
                f"{path}.{field}[{criterion_index}]",
                criterion_type,
                errors,
            )
    _check_rows(
        card["source_ledger"],
        f"{path}.source_ledger",
        SOURCE_LEDGER_FIELDS,
        "source_ledger",
        errors,
    )
    for row_index, row in enumerate(card["source_ledger"]):
        row_path = f"{path}.source_ledger[{row_index}]"
        if not isinstance(row, dict) or set(row) != SOURCE_LEDGER_FIELDS:
            continue
        for field in ("source_id", "candidate_id", "basis_level"):
            if not _nonempty_text(row[field]):
                errors.append(
                    _contract_error("source_ledger_text_type", f"{row_path}.{field}", "string")
                )
        for field in ("support_types", "supports", "does_not_support", "limitations"):
            _check_text_list(row[field], f"{row_path}.{field}", errors)


def _check_overlay(overlay: Any, index: int, errors: list[dict[str, Any]]) -> None:
    path = f"domain_overlays[{index}]"
    if not _check_closed_object(overlay, OVERLAY_FIELDS, path, "domain_overlay", errors):
        return
    if overlay.get("schema_version") != SCHEMA_VERSION:
        errors.append(
            _contract_error("schema_version", f"{path}.schema_version", SCHEMA_VERSION)
        )
    if not _nonempty_text(overlay.get("overlay_id")):
        errors.append(_contract_error("overlay_id_type", f"{path}.overlay_id", "string"))
    if overlay.get("domain") != "nuclear_engineering_ml":
        errors.append(
            _contract_error(
                "domain_enum", f"{path}.domain", "nuclear_engineering_ml"
            )
        )
    _check_text_list(overlay["base_card_ids"], f"{path}.base_card_ids", errors)
    for field in (
        "additional_assumptions",
        "additional_failure_modes",
        "additional_validation_checks",
        "specialist_review_boundaries",
    ):
        _check_text_list(overlay[field], f"{path}.{field}", errors)
    additional_stop = overlay["additional_stop_conditions"]
    if not isinstance(additional_stop, list):
        errors.append(_contract_error("list_type", f"{path}.additional_stop_conditions", "array"))
    else:
        if not additional_stop:
            errors.append(
                _contract_error(
                    "additional_stop_conditions_min_items",
                    f"{path}.additional_stop_conditions",
                    "at least one criterion",
                )
            )
        for criterion_index, criterion in enumerate(additional_stop):
            _check_criterion(
                criterion,
                f"{path}.additional_stop_conditions[{criterion_index}]",
                "stop",
                errors,
            )
    if overlay.get("transfer_status") != "hypothesis":
        errors.append(
            _contract_error("transfer_status", f"{path}.transfer_status", "hypothesis")
        )
    _check_rows(
        overlay["source_ledger"],
        f"{path}.source_ledger",
        SOURCE_LEDGER_FIELDS,
        "source_ledger",
        errors,
    )
    for row_index, row in enumerate(overlay["source_ledger"]):
        row_path = f"{path}.source_ledger[{row_index}]"
        if not isinstance(row, dict) or set(row) != SOURCE_LEDGER_FIELDS:
            continue
        for field in ("source_id", "candidate_id", "basis_level"):
            if not _nonempty_text(row[field]):
                errors.append(
                    _contract_error("source_ledger_text_type", f"{row_path}.{field}", "string")
                )
        for field in ("support_types", "supports", "does_not_support", "limitations"):
            _check_text_list(row[field], f"{row_path}.{field}", errors)


def validate_model_payload_contract(payload: Any) -> list[dict[str, Any]]:
    """Return sorted closed field diagnostics without mutation or I/O."""

    errors: list[dict[str, Any]] = []
    if not isinstance(payload, dict):
        return [_contract_error("payload_object", "payload", "object")]
    if set(payload) != PAYLOAD_FIELDS:
        missing = sorted(PAYLOAD_FIELDS - set(payload))
        unknown = sorted(set(payload) - PAYLOAD_FIELDS)
        expected: dict[str, Any] = {"fields": sorted(PAYLOAD_FIELDS)}
        if missing:
            expected["missing"] = missing
        if unknown:
            expected["unknown"] = unknown
        errors.append(_contract_error("payload_fields", "payload", expected))
        return errors
    if payload.get("coaching_mode") not in {"bounded", "route_specific"}:
        errors.append(
            _contract_error(
                "coaching_mode_enum",
                "coaching_mode",
                ["bounded", "route_specific"],
            )
        )
    cards = payload.get("method_cards")
    if not isinstance(cards, list):
        errors.append(_contract_error("method_cards_type", "method_cards", "array"))
    else:
        if not cards:
            errors.append(
                _contract_error(
                    "method_cards_min_items",
                    "method_cards",
                    "at least one closed method card",
                )
            )
        for index, card in enumerate(cards):
            _check_card(card, index, errors)
    overlays = payload.get("domain_overlays")
    if not isinstance(overlays, list):
        errors.append(_contract_error("domain_overlays_type", "domain_overlays", "array"))
    else:
        for index, overlay in enumerate(overlays):
            _check_overlay(overlay, index, errors)
    return sorted(
        errors,
        key=lambda error: (
            str(error.get("path", "")),
            str(error.get("code", "")),
            json.dumps(error.get("expected"), ensure_ascii=False, sort_keys=True),
        ),
    )


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

    contract_errors = validate_model_payload_contract(model_payload)
    if contract_errors:
        raise _ComposeFailure("payload_contract_invalid", contract_errors=contract_errors)

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
