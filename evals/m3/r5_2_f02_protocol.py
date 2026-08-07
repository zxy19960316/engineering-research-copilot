#!/usr/bin/env python3
"""Fail-closed r5.2-f02 text/JSON and observation contracts.

This module operates on supplied bytes only. It does not launch tasks, call a
model, repair output, write evidence, or retry a failed finalization.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Callable


REVISION = "r5.2-f02"
CASE_ID = "m3-f02"
UTF8_BOM_POLICY = "reject"
AUTHORIZED_EXECUTION_PREFIX = (
    "This is the authorized r5.2-f02 execution.\n"
    "Execute the frozen task now.\n"
)
FORBIDDEN_PROMPT_PHRASES = (
    "do not execute",
    "future task",
    "without separate authorization",
)
AUTHORIZATION_RECEIPT_KEYS = {
    "revision",
    "authorized",
    "prompt_sha256",
    "input_binding_sha256",
    "authorized_task_count",
}
RAW_OBSERVATION_KEYS = {
    "schema_version",
    "revision",
    "case_id",
    "task_id",
    "model_id",
    "request_id",
    "request_id_status",
    "finalization_id",
    "raw_response_path",
    "raw_output_bytes",
    "raw_output_sha256",
    "finish_reason",
    "finish_reason_status",
    "input_tokens",
    "input_tokens_status",
    "output_tokens",
    "output_tokens_status",
    "task_created_at",
    "task_completed_at",
    "request_envelope_sha256",
    "model_visible_messages_sha256",
}
_JSON_WHITESPACE = b" \t\r\n"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_UTC_TIMESTAMP_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"
)


@dataclass(frozen=True)
class ParseResult:
    """A deterministic parser outcome with no inferred or repaired payload."""

    ok: bool
    value: dict[str, Any] | None
    failure_code: str | None
    classification: str
    json_error: dict[str, Any] | None


class _DuplicateObjectKey(ValueError):
    def __init__(self, key: str) -> None:
        super().__init__(f"duplicate object key: {key}")
        self.key = key


class _NonFiniteNumber(ValueError):
    pass


def _json_error(
    message: str,
    *,
    line: int = 1,
    column: int = 1,
    byte_offset: int = 0,
) -> dict[str, Any]:
    return {
        "message": message,
        "line": line,
        "column": column,
        "byte_offset": byte_offset,
    }


def _failure(
    classification: str,
    message: str,
    *,
    failure_code: str = "payload_invalid_json",
    line: int = 1,
    column: int = 1,
    byte_offset: int = 0,
) -> ParseResult:
    return ParseResult(
        ok=False,
        value=None,
        failure_code=failure_code,
        classification=classification,
        json_error=_json_error(
            message,
            line=line,
            column=column,
            byte_offset=byte_offset,
        ),
    )


def _closed_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise _DuplicateObjectKey(key)
        value[key] = item
    return value


def _reject_non_finite(token: str) -> Any:
    raise _NonFiniteNumber(f"non-finite JSON number: {token}")


def _decode_json_value(raw: bytes) -> tuple[Any, str] | ParseResult:
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        return _failure(
            "invalid_utf8",
            "raw response is not valid UTF-8",
            byte_offset=error.start,
        )
    try:
        value = json.loads(
            text,
            object_pairs_hook=_closed_object,
            parse_constant=_reject_non_finite,
        )
    except _DuplicateObjectKey as error:
        encoded_key = json.dumps(error.key, ensure_ascii=False).encode("utf-8")
        first = raw.find(encoded_key)
        second = raw.find(encoded_key, first + len(encoded_key))
        offset = second if second >= 0 else 0
        return _failure(
            "duplicate_object_key",
            f"duplicate object key: {error.key}",
            byte_offset=offset,
        )
    except _NonFiniteNumber as error:
        return _failure("non_finite_json_number", str(error))
    except json.JSONDecodeError as error:
        byte_offset = len(text[: error.pos].encode("utf-8"))
        classification = (
            "multiple_json_values"
            if error.msg == "Extra data"
            else "invalid_json_syntax"
        )
        return _failure(
            classification,
            error.msg,
            line=error.lineno,
            column=error.colno,
            byte_offset=byte_offset,
        )
    return value, text


def parse_strict_json_object(raw: bytes) -> ParseResult:
    """Accept one UTF-8 JSON object with strict, byte-level boundaries.

    JSON whitespace around the object is allowed. A UTF-8 BOM, Markdown,
    prose, comments, duplicate keys, multiple values, non-finite numbers, and
    non-object roots are rejected. No normalization or repair is attempted.
    """

    if not isinstance(raw, bytes):
        raise TypeError("raw response must be bytes")
    stripped = raw.strip(_JSON_WHITESPACE)
    if not stripped:
        return _failure(
            "empty_output",
            "raw response is empty",
            failure_code="empty_output_terminal_failure",
        )
    if stripped.startswith(b"\xef\xbb\xbf"):
        return _failure("utf8_bom", "UTF-8 BOM is forbidden")

    if stripped[:1] != b"{":
        if stripped.startswith(b"```"):
            return _failure(
                "markdown_fenced_json", "Markdown code fences are forbidden"
            )
        decoded = _decode_json_value(stripped)
        if isinstance(decoded, ParseResult):
            if b"{" in stripped:
                return _failure(
                    "leading_prose", "prose before the JSON object is forbidden"
                )
            if decoded.classification == "invalid_utf8":
                return decoded
            return _failure(
                "non_json_prose", "first non-whitespace byte must be '{'"
            )
        value, _ = decoded
        if not isinstance(value, dict):
            return _failure("non_object_json", "top-level JSON value must be an object")
        return _failure("leading_prose", "first non-whitespace byte must be '{'")

    if stripped[-1:] != b"}":
        if b"}" in stripped:
            return _failure(
                "trailing_prose", "prose after the JSON object is forbidden"
            )
        return _failure("truncated_json", "last non-whitespace byte must be '}'")

    decoded = _decode_json_value(stripped)
    if isinstance(decoded, ParseResult):
        return decoded
    value, _ = decoded
    if not isinstance(value, dict):
        return _failure("non_object_json", "top-level JSON value must be an object")
    return ParseResult(
        ok=True,
        value=value,
        failure_code=None,
        classification="json_object",
        json_error=None,
    )


def lint_execution_prompt(prompt: str) -> list[str]:
    """Reject authorization contradictions in the model-visible prompt."""

    errors: list[str] = []
    if not isinstance(prompt, str) or not prompt.startswith(AUTHORIZED_EXECUTION_PREFIX):
        errors.append("authorized_execution_prefix_missing")
    lowered = prompt.lower() if isinstance(prompt, str) else ""
    for phrase in FORBIDDEN_PROMPT_PHRASES:
        if phrase in lowered:
            errors.append(f"forbidden_prompt_phrase:{phrase}")
    return errors


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and _SHA256_RE.fullmatch(value) is not None


def validate_authorization_receipt(
    value: object,
    *,
    expected_prompt_sha256: str,
    expected_input_binding_sha256: str,
) -> list[str]:
    """Validate the five-field Gate 3 receipt shape without authorizing a run."""

    if not isinstance(value, dict):
        return ["authorization_receipt_object_required"]
    errors: list[str] = []
    if set(value) != AUTHORIZATION_RECEIPT_KEYS:
        errors.append("authorization_receipt_fields_invalid")
    if value.get("revision") != REVISION:
        errors.append("authorization_receipt_revision_invalid")
    if value.get("authorized") is not True:
        errors.append("authorization_receipt_authorized_invalid")
    prompt_sha = value.get("prompt_sha256")
    if not _is_sha256(prompt_sha) or prompt_sha != expected_prompt_sha256:
        errors.append("authorization_receipt_prompt_sha256_invalid")
    input_sha = value.get("input_binding_sha256")
    if not _is_sha256(input_sha) or input_sha != expected_input_binding_sha256:
        errors.append("authorization_receipt_input_binding_sha256_invalid")
    task_count = value.get("authorized_task_count")
    if isinstance(task_count, bool) or task_count != 1:
        errors.append("authorization_receipt_task_count_invalid")
    return sorted(set(errors))


def validate_raw_observation(value: object, *, raw_bytes: bytes) -> list[str]:
    """Validate metadata captured before parsing against the preserved bytes."""

    if not isinstance(value, dict):
        return ["raw_observation_object_required"]
    errors: list[str] = []
    if set(value) != RAW_OBSERVATION_KEYS:
        errors.append("raw_observation_fields_invalid")
    expected = {
        "schema_version": "m3.1-r5.2-f02-raw-response-observation-v1",
        "revision": REVISION,
        "case_id": CASE_ID,
        "raw_response_path": "m3-f02.model-final.raw",
    }
    for field, required in expected.items():
        if value.get(field) != required:
            errors.append(f"raw_observation_field_invalid:{field}")
    for field in ("task_id", "model_id", "finalization_id"):
        item = value.get(field)
        if not isinstance(item, str) or not item:
            errors.append(f"raw_observation_field_invalid:{field}")
    for field in ("raw_output_bytes",):
        item = value.get(field)
        if isinstance(item, bool) or not isinstance(item, int) or item < 0:
            errors.append(f"raw_observation_field_invalid:{field}")
    for field, status_field, expected_kind in (
        ("request_id", "request_id_status", "string"),
        ("finish_reason", "finish_reason_status", "string"),
        ("input_tokens", "input_tokens_status", "integer"),
        ("output_tokens", "output_tokens_status", "integer"),
    ):
        status = value.get(status_field)
        item = value.get(field)
        if status == "recorded":
            if expected_kind == "string":
                valid = isinstance(item, str) and bool(item)
            else:
                valid = (
                    isinstance(item, int)
                    and not isinstance(item, bool)
                    and item >= 0
                )
            if not valid:
                errors.append(f"raw_observation_field_invalid:{field}")
        elif status == "not_exposed":
            if item is not None:
                errors.append(f"raw_observation_field_invalid:{field}")
        else:
            errors.append(f"raw_observation_field_invalid:{status_field}")
    for field in (
        "raw_output_sha256",
        "request_envelope_sha256",
        "model_visible_messages_sha256",
    ):
        if not _is_sha256(value.get(field)):
            errors.append(f"raw_observation_field_invalid:{field}")
    for field in ("task_created_at", "task_completed_at"):
        item = value.get(field)
        if not isinstance(item, str) or _UTC_TIMESTAMP_RE.fullmatch(item) is None:
            errors.append(f"raw_observation_field_invalid:{field}")
    if value.get("raw_output_bytes") != len(raw_bytes):
        errors.append("raw_observation_byte_length_mismatch")
    if value.get("raw_output_sha256") != hashlib.sha256(raw_bytes).hexdigest():
        errors.append("raw_observation_sha256_mismatch")
    return sorted(set(errors))


def process_synthetic_final(
    raw: bytes,
    validator: Callable[[dict[str, Any]], list[str]],
) -> dict[str, Any]:
    """Exercise composer/validator boundaries on synthetic bytes only."""

    parsed = parse_strict_json_object(raw)
    counters = {"composer": 1, "validator": 0, "retry": 0}
    if not parsed.ok:
        return {
            "status": "terminal_not_accepted",
            "accepted": False,
            "reason": parsed.failure_code,
            "classification": parsed.classification,
            "validator_errors": [],
            "counters": counters,
        }

    counters["validator"] = 1
    assert parsed.value is not None
    validator_errors = validator(parsed.value)
    if validator_errors:
        return {
            "status": "terminal_not_accepted",
            "accepted": False,
            "reason": "validator_rejected",
            "classification": "json_object_schema_rejected",
            "validator_errors": list(validator_errors),
            "counters": counters,
        }
    return {
        "status": "accepted",
        "accepted": True,
        "reason": "accepted",
        "classification": "json_object_schema_accepted",
        "validator_errors": [],
        "counters": counters,
    }
