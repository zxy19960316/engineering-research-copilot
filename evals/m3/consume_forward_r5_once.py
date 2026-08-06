#!/usr/bin/env python3
"""Process one already-observed r5 final exactly once in a temp-safe contract."""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Callable

from r5_dispatch_contract import validate_case_record, validate_future_paths


SAFE_CODE = re.compile(r"^[a-z0-9][a-z0-9_.:-]{0,127}$")
COMPOSITION_FAILURE_CODES = {
    "composer_callable_missing",
    "invalid_source_m2_bundle",
    "m2_invalid_json",
    "m2_object_required",
    "payload_invalid_json",
    "payload_object_required",
}


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _safe_codes(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return sorted(
        {
            item
            for item in value
            if isinstance(item, str) and SAFE_CODE.fullmatch(item) is not None
        }
    )


def _source_sha256(plan: dict[str, Any]) -> str | None:
    source = plan.get("source_input_path")
    if not isinstance(source, Path):
        return None
    try:
        return _sha256(source.read_bytes())
    except OSError:
        return None


def _failure_diagnostic(
    plan: dict[str, Any],
    final_raw: bytes,
    *,
    stage: str,
    code: str,
    contract_errors: Any = None,
    validator_errors: Any = None,
    evidence_gaps: Any = None,
) -> dict[str, Any]:
    return {
        "failure_stage": stage,
        "failure_code": code,
        "contract_errors": _safe_codes(contract_errors),
        "validator_errors": _safe_codes(validator_errors),
        "evidence_gaps": _safe_codes(evidence_gaps),
        "source_sha256": _source_sha256(plan),
        "model_final_sha256": _sha256(final_raw),
        "payload_sha256": _sha256(final_raw) if plan.get("case_id") != "m3-f03" else None,
        "retry_count": 0,
    }


def _exception_diagnostic(
    plan: dict[str, Any], final_raw: bytes, exception: Exception
) -> dict[str, Any]:
    code = getattr(exception, "code", None)
    detail = getattr(exception, "detail", None)
    safe_detail = detail if isinstance(detail, dict) else {}
    if code == "payload_contract_invalid":
        stage = "payload_contract"
    elif code == "invalid_composed_m3_bundle":
        stage = "m3_validation"
    elif code in COMPOSITION_FAILURE_CODES:
        stage = "composition"
    else:
        return _failure_diagnostic(
            plan,
            final_raw,
            stage="unexpected",
            code="unexpected_processing_failure",
        )
    return _failure_diagnostic(
        plan,
        final_raw,
        stage=stage,
        code=code,
        contract_errors=safe_detail.get("contract_errors"),
        validator_errors=safe_detail.get("validator_errors"),
        evidence_gaps=safe_detail.get("validator_evidence_gaps"),
    )


def _path_for(plan: dict[str, Any], key: str) -> Path | None:
    raw = plan["future_paths"].get(key)
    if raw is None:
        return None
    return Path(plan["result_root"]) / raw


def _write_new_bytes(path: Path, raw: bytes) -> None:
    if path.exists():
        raise FileExistsError("output_already_exists")
    descriptor = -1
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = -1
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def _write_new_json(path: Path, value: dict[str, Any]) -> None:
    raw = (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    _write_new_bytes(path, raw)


def _failure_code(stage: str) -> str:
    return {
        "payload": "payload_write_failed",
        "composer": "composer_invocation_failed",
        "bundle": "bundle_write_failed",
        "composer_receipt": "composer_receipt_write_failed",
        "outcome": "outcome_write_failed",
        "validator": "validator_invocation_failed",
        "validation": "validation_write_failed",
        "validator_receipt": "validator_receipt_write_failed",
        "context": "context_write_failed",
        "transaction": "transaction_write_failed",
    }.get(stage, "processing_failed")


def _base_record(plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": plan["case_id"],
        "task_id": plan.get("task_id"),
        "state": "processing_failed",
        "tasks_launched": 1,
        "task_finalizations_observed": 1,
        "dispatcher_cases_preflighted": 1,
        "dispatcher_cases_processed": 0,
        "composer_invocations": 0,
        "validator_invocations": 0,
        "accepted": False,
        "transaction_failures": [],
    }


def _write_context_and_transaction(
    plan: dict[str, Any],
    record: dict[str, Any],
    final_raw: bytes,
    *,
    validation_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    context_path = _path_for(plan, "context_finalization_json")
    transaction_path = _path_for(plan, "case_transaction_json")
    context = {
        "case_id": record["case_id"],
        "task_id": record["task_id"],
        "state": record["state"],
        "task_finalizations_observed": record["task_finalizations_observed"],
        "dispatcher_cases_preflighted": record["dispatcher_cases_preflighted"],
        "dispatcher_cases_processed": record["dispatcher_cases_processed"],
        "composer_invocations": record["composer_invocations"],
        "validator_invocations": record["validator_invocations"],
        "accepted": record["accepted"],
        "final_raw_sha256": _sha256(final_raw),
        "final_byte_length": len(final_raw),
        "transaction_failures": record["transaction_failures"],
    }
    if validation_result is not None:
        context["validation_status"] = validation_result.get("status")
    try:
        if context_path is None:
            raise RuntimeError("context_path_missing")
        _write_new_json(context_path, context)
    except Exception:
        if not record["transaction_failures"]:
            record["transaction_failures"].append(_failure_code("context"))
        record["state"] = "processing_failed"
        record["dispatcher_cases_processed"] = 0
        record["accepted"] = False
    try:
        if transaction_path is None:
            raise RuntimeError("transaction_path_missing")
        _write_new_json(transaction_path, record)
    except Exception:
        if not record["transaction_failures"]:
            record["transaction_failures"].append(_failure_code("transaction"))
        record["state"] = "processing_failed"
        record["dispatcher_cases_processed"] = 0
        record["accepted"] = False
    return record


def _failure_result(
    plan: dict[str, Any],
    record: dict[str, Any],
    final_raw: bytes,
    code: str,
    *,
    validation_result: dict[str, Any] | None = None,
    diagnostic: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if code not in record["transaction_failures"]:
        record["transaction_failures"].append(code)
    record["state"] = "processing_failed"
    record["dispatcher_cases_processed"] = 0
    record["accepted"] = False
    _write_context_and_transaction(plan, record, final_raw, validation_result=validation_result)
    return {
        "status": "processing_failed",
        "errors": sorted(set(record["transaction_failures"])),
        "record": record,
        "failure": diagnostic
        or _failure_diagnostic(
            plan,
            final_raw,
            stage="unexpected",
            code="unexpected_processing_failure",
        ),
    }


def consume_case_once(
    plan: dict[str, Any],
    final_raw: bytes,
    *,
    compose_once: Callable[[Path, Path], dict[str, Any]] | None,
    validate_once: Callable[[Path], dict[str, Any]],
) -> dict[str, Any]:
    """Consume one final with no retry and no overwrite."""

    if not isinstance(final_raw, bytes):
        return {"status": "blocked", "errors": ["final_bytes_required"], "record": None}
    try:
        final_raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return {"status": "blocked", "errors": ["final_utf8_invalid"], "record": None}
    if final_raw.startswith(b"\xef\xbb\xbf"):
        return {"status": "blocked", "errors": ["final_utf8_bom_forbidden"], "record": None}
    task_id = plan.get("task_id")
    if not isinstance(task_id, str) or not task_id:
        return {"status": "blocked", "errors": ["task_id_required"], "record": None}
    result_root = Path(plan["result_root"])
    errors = validate_future_paths(plan.get("case_id"), plan.get("future_paths"), result_root)
    if not result_root.is_dir():
        errors.append("future_result_root_missing")
    if errors:
        return {"status": "blocked", "errors": sorted(set(errors)), "record": None}

    model_final_path = _path_for(plan, "model_final_json")
    if model_final_path is None:
        return {"status": "blocked", "errors": ["model_final_path_missing"], "record": None}
    try:
        _write_new_bytes(model_final_path, final_raw)
    except Exception:
        return {"status": "blocked", "errors": ["model_final_write_failed"], "record": None}
    record = _base_record(plan)
    case_id = plan["case_id"]

    if case_id != "m3-f03":
        payload_path = _path_for(plan, "payload_json")
        bundle_path = _path_for(plan, "composed_bundle_json")
        composer_receipt_path = _path_for(plan, "composer_invocation_receipt_json")
        if payload_path is None or bundle_path is None or composer_receipt_path is None:
            return _failure_result(plan, record, final_raw, "composer_path_missing")
        try:
            _write_new_bytes(payload_path, final_raw)
        except Exception:
            return _failure_result(plan, record, final_raw, _failure_code("payload"))
        record["composer_invocations"] = 1
        if compose_once is None:
            diagnostic = _failure_diagnostic(
                plan,
                final_raw,
                stage="composition",
                code="composer_callable_missing",
            )
            try:
                _write_new_json(
                    composer_receipt_path,
                    {
                        "case_id": case_id,
                        "composer_invocation_count": 1,
                        "status": "failed",
                        **diagnostic,
                    },
                )
            except Exception:
                pass
            return _failure_result(
                plan,
                record,
                final_raw,
                "composer_callable_missing",
                diagnostic=diagnostic,
            )
        try:
            composed = compose_once(payload_path, bundle_path)
            if not isinstance(composed, dict):
                raise TypeError("composer_result_object_required")
            _write_new_json(bundle_path, composed)
        except Exception as exception:
            diagnostic = _exception_diagnostic(plan, final_raw, exception)
            try:
                _write_new_json(
                    composer_receipt_path,
                    {
                        "case_id": case_id,
                        "composer_invocation_count": 1,
                        "status": "failed",
                        **diagnostic,
                    },
                )
            except Exception:
                pass
            return _failure_result(
                plan,
                record,
                final_raw,
                _failure_code("composer"),
                diagnostic=diagnostic,
            )
        try:
            _write_new_json(
                composer_receipt_path,
                {
                    "case_id": case_id,
                    "composer_invocation_count": 1,
                    "status": "invoked",
                    "bundle_path_key": "composed_bundle_json",
                },
            )
        except Exception:
            return _failure_result(plan, record, final_raw, _failure_code("composer_receipt"))
        validation_input = bundle_path
    else:
        outcome_path = _path_for(plan, "outcome_json")
        if outcome_path is None:
            return _failure_result(plan, record, final_raw, _failure_code("outcome"))
        try:
            _write_new_bytes(outcome_path, final_raw)
        except Exception:
            return _failure_result(plan, record, final_raw, _failure_code("outcome"))
        validation_input = outcome_path

    record["validator_invocations"] = 1
    try:
        validation_result = validate_once(validation_input)
        if not isinstance(validation_result, dict):
            raise TypeError("validator_result_object_required")
    except Exception:
        diagnostic = _failure_diagnostic(
            plan,
            final_raw,
            stage="unexpected",
            code="validator_invocation_failed",
        )
        validator_receipt_path = _path_for(plan, "validator_receipt_json")
        if validator_receipt_path is not None:
            try:
                _write_new_json(
                    validator_receipt_path,
                    {
                        "case_id": case_id,
                        "validator_invocation_count": 1,
                        "status": "failed",
                        **diagnostic,
                    },
                )
            except Exception:
                pass
        return _failure_result(
            plan,
            record,
            final_raw,
            _failure_code("validator"),
            diagnostic=diagnostic,
        )

    validation_path = _path_for(plan, "validation_json")
    if validation_path is None:
        return _failure_result(plan, record, final_raw, _failure_code("validation"), validation_result=validation_result)
    try:
        _write_new_json(validation_path, validation_result)
    except Exception:
        return _failure_result(plan, record, final_raw, _failure_code("validation"), validation_result=validation_result)

    if case_id != "m3-f03":
        outcome_path = _path_for(plan, "outcome_json")
        if outcome_path is None:
            return _failure_result(plan, record, final_raw, _failure_code("outcome"), validation_result=validation_result)
        try:
            _write_new_json(
                outcome_path,
                {
                    "case_id": case_id,
                    "accepted": validation_result.get("accepted") is True,
                    "validation_status": validation_result.get("status"),
                },
            )
        except Exception:
            return _failure_result(plan, record, final_raw, _failure_code("outcome"), validation_result=validation_result)

    validator_receipt_path = _path_for(plan, "validator_receipt_json")
    if validator_receipt_path is None:
        return _failure_result(plan, record, final_raw, _failure_code("validator_receipt"), validation_result=validation_result)
    try:
        _write_new_json(
            validator_receipt_path,
            {
                "case_id": case_id,
                "validator_invocation_count": 1,
                "status": "invoked",
                "validation_path_key": "validation_json",
            },
        )
    except Exception:
        return _failure_result(plan, record, final_raw, _failure_code("validator_receipt"), validation_result=validation_result)

    record["dispatcher_cases_processed"] = 1
    record["accepted"] = validation_result.get("accepted") is True
    record["state"] = "processed_accepted" if record["accepted"] else "processed_invalid"
    _write_context_and_transaction(plan, record, final_raw, validation_result=validation_result)
    if record["transaction_failures"]:
        return {
            "status": "processing_failed",
            "errors": sorted(set(record["transaction_failures"])),
            "record": record,
        }
    validation_errors = validate_case_record(record)
    if validation_errors:
        return {"status": "processing_failed", "errors": validation_errors, "record": record}
    return {"status": "processed", "errors": [], "record": record}

