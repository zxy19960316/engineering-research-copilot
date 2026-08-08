#!/usr/bin/env python3
"""Create the immutable route-free F04-D01 M2.1.1 confirmation successor."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
M2_DIR = ROOT / "evals" / "f04-upstream" / "m2"
DRAFT_PATH = M2_DIR / "f04-m2-direction-bundle.json"
CONFIRMED_PATH = M2_DIR / "f04-m2-confirmed.bundle.json"
VALIDATION_PATH = M2_DIR / "f04-m2-confirmed.validation.json"
MANIFEST_PATH = M2_DIR / "f04-m2-confirmed.manifest.json"
NOTES_PATH = M2_DIR / "f04-m2-confirmed.confirmation.md"
VALIDATOR_PATH = (
    ROOT
    / "skills"
    / "engineering-research-copilot"
    / "scripts"
    / "validate_m2_direction_bundle.py"
)

DIRECTION_ID = "F04-D01"
SOURCE_MESSAGE_ID = "codex-task:019fd4f7-e1c4-7fd1-9799-786f62fda8e6:item-46"
SOURCE_MESSAGE_EXCERPT = "Confirm F04 direction F04-D01"
EXPECTED_PRECONFIRMATION_HASH = (
    "884e80387776ecdf3963a3db79c1bec3eb8fe48f65f17c0fc8852d61b54f8678"
)
EXPECTED_DIRECTION_HASH = (
    "1f81072903df3afa27d49bd06c17209141014ac8ea5026973a8bc7bd8e69b310"
)
CONSTRUCTION_CONTEXT = "codex-task:019fd467-790b-7551-9157-ddd3b2222ca1"


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def formatted_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode(
        "utf-8"
    )


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _selected_direction(draft: dict[str, Any]) -> dict[str, Any]:
    portfolio = draft.get("direction_portfolio")
    directions = portfolio.get("directions") if isinstance(portfolio, dict) else None
    if not isinstance(directions, list):
        raise TypeError("selected_direction_missing")
    matches = [
        direction
        for direction in directions
        if isinstance(direction, dict) and direction.get("direction_id") == DIRECTION_ID
    ]
    if len(matches) != 1:
        raise ValueError("selected_direction_missing")
    return matches[0]


def build_confirmed(draft: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    if not isinstance(draft, dict):
        raise TypeError("draft_json_object_required")
    expected_decision = {
        "selected_direction_id": None,
        "status": "waiting_for_user_confirmation",
        "permitted_next_actions": ["confirm", "modify", "reject"],
        "confirmation_event": None,
    }
    if draft.get("direction_decision") != expected_decision:
        raise ValueError("draft_not_waiting_for_confirmation")
    if draft.get("route_output") is not None:
        raise ValueError("draft_route_output_must_be_null")

    direction = _selected_direction(draft)
    if canonical_sha256(direction) != EXPECTED_DIRECTION_HASH:
        raise ValueError("selected_direction_hash_mismatch")
    previous_bundle_hash = canonical_sha256(draft)
    if previous_bundle_hash != EXPECTED_PRECONFIRMATION_HASH:
        raise ValueError("preconfirmation_bundle_hash_mismatch")

    confirmation_event = {
        "actor_role": "user",
        "selected_direction_id": DIRECTION_ID,
        "source_message_id": SOURCE_MESSAGE_ID,
        "source_message_excerpt": SOURCE_MESSAGE_EXCERPT,
        "source_message_sha256": hashlib.sha256(
            SOURCE_MESSAGE_EXCERPT.encode("utf-8")
        ).hexdigest(),
        "previous_bundle_hash": previous_bundle_hash,
    }
    confirmed = copy.deepcopy(draft)
    confirmed["direction_decision"] = {
        "selected_direction_id": DIRECTION_ID,
        "status": "user_confirmed",
        "permitted_next_actions": ["modify", "reject", "generate_route"],
        "confirmation_event": confirmation_event,
    }
    confirmed["route_output"] = None
    return confirmed, confirmation_event


def _validate_once(bundle_path: Path) -> tuple[dict[str, Any], str, int]:
    completed = subprocess.run(
        [sys.executable, "-X", "utf8", str(VALIDATOR_PATH), str(bundle_path)],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if completed.stderr:
        raise RuntimeError("m2_validator_stderr_not_empty")
    raw_output = completed.stdout.decode("utf-8", errors="strict")
    lines = raw_output.splitlines()
    if len(lines) != 1 or not lines[0]:
        raise RuntimeError("m2_validator_stdout_not_one_line_json")
    result = json.loads(lines[0])
    if not isinstance(result, dict):
        raise TypeError("m2_validator_output_not_object")
    return result, lines[0], completed.returncode


def _write_staged(path: Path, content: bytes) -> None:
    descriptor, staging_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    staging_path = Path(staging_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(staging_path, path)
    finally:
        if staging_path.exists():
            staging_path.unlink()


def main() -> int:
    outputs = (CONFIRMED_PATH, VALIDATION_PATH, MANIFEST_PATH, NOTES_PATH)
    if any(path.exists() for path in outputs):
        raise SystemExit("confirmation_artifact_already_exists")

    draft = json.loads(DRAFT_PATH.read_text(encoding="utf-8"))
    confirmed, confirmation_event = build_confirmed(draft)
    confirmed_bytes = formatted_json_bytes(confirmed)

    with tempfile.TemporaryDirectory(prefix=".f04-confirm-", dir=M2_DIR) as temp_name:
        validation_input = Path(temp_name) / CONFIRMED_PATH.name
        validation_input.write_bytes(confirmed_bytes)
        validation_result, raw_output, exit_code = _validate_once(validation_input)

    if (
        exit_code != 0
        or validation_result.get("status") != "valid"
        or validation_result.get("errors") != []
        or validation_result.get("evidence_gaps") != []
    ):
        raise SystemExit("confirmed_bundle_failed_m2_validation")

    confirmed_raw_hash = sha256_bytes(confirmed_bytes)
    confirmed_canonical_hash = canonical_sha256(confirmed)
    executed_at = datetime.now().astimezone().isoformat(timespec="seconds")
    relative_confirmed = CONFIRMED_PATH.relative_to(ROOT).as_posix()
    relative_validator = VALIDATOR_PATH.relative_to(ROOT).as_posix()

    validation_receipt = {
        "schema_version": "f04-m2.1.1-confirmation-validation-v1",
        "artifact": relative_confirmed,
        "validator": relative_validator,
        "command": (
            "python -X utf8 "
            f"{relative_validator} {relative_confirmed}"
        ),
        "executed_at": executed_at,
        "exit_code": exit_code,
        "invocation_count": 1,
        "input_raw_sha256": confirmed_raw_hash,
        "input_canonical_sha256": confirmed_canonical_hash,
        "validator_output": validation_result,
        "validator_stdout": raw_output,
        "constructed_by_context": CONSTRUCTION_CONTEXT,
        "proves": [
            "The route-free F04-D01 successor satisfies the M2.1.1 structural contract.",
            "The exact user excerpt is bound to F04-D01 and the immutable pre-confirmation bundle hash.",
        ],
        "does_not_prove": [
            "Route execution, experiment, simulation, training, or deployment.",
            "Empirical bearing-dataset comparability or calibration traceability.",
            "M3 eligibility or fresh-context acceptance.",
        ],
    }

    manifest = {
        "schema_version": "f04-m2.1.1-confirmed-manifest-v1",
        "status": "user_confirmed",
        "selected_direction_id": DIRECTION_ID,
        "selected_direction_canonical_sha256": EXPECTED_DIRECTION_HASH,
        "preconfirmation_bundle_path": DRAFT_PATH.relative_to(ROOT).as_posix(),
        "preconfirmation_bundle_canonical_sha256": EXPECTED_PRECONFIRMATION_HASH,
        "confirmed_bundle_path": relative_confirmed,
        "confirmed_bundle_raw_sha256": confirmed_raw_hash,
        "confirmed_bundle_canonical_sha256": confirmed_canonical_hash,
        "confirmation_event": confirmation_event,
        "route_output": None,
        "validation_receipt_path": VALIDATION_PATH.relative_to(ROOT).as_posix(),
        "construction_context": CONSTRUCTION_CONTEXT,
        "limitations": [
            "Confirmation selects a formal direction but does not generate a route.",
            "The evidence remains public-record and literature based; no dataset or equipment run occurred.",
            "Target-domain transfer remains a hypothesis until a decisive test is separately authorized.",
        ],
    }

    notes = f"""# F04-D01 confirmed direction binding

Status: `user_confirmed`; `route_output` remains `null`.

- selected direction: `{DIRECTION_ID}`
- exact user excerpt: `{SOURCE_MESSAGE_EXCERPT}`
- source message ID: `{SOURCE_MESSAGE_ID}`
- selected-direction canonical SHA-256: `{EXPECTED_DIRECTION_HASH}`
- pre-confirmation canonical SHA-256: `{EXPECTED_PRECONFIRMATION_HASH}`
- confirmed bundle raw SHA-256: `{confirmed_raw_hash}`
- confirmed bundle canonical SHA-256: `{confirmed_canonical_hash}`
- validator status: `valid`, exit `0`, invocation count `1`

This confirmation successor does not contain or authorize a route, experiment,
simulation, training run, deployment, dataset download, equipment action, or empirical
measurement claim. M3 eligibility and fresh-context acceptance remain separate gates.
"""

    prepared = {
        CONFIRMED_PATH: confirmed_bytes,
        VALIDATION_PATH: formatted_json_bytes(validation_receipt),
        MANIFEST_PATH: formatted_json_bytes(manifest),
        NOTES_PATH: notes.encode("utf-8"),
    }
    for path, content in prepared.items():
        _write_staged(path, content)

    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
