#!/usr/bin/env python3
"""Create the immutable M2.1.1 confirmation artifact for NEML-F01-D1."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "evals" / "m2" / "results"
DRAFT_PATH = RESULTS / "2026-08-05-f01-f05-nuclear-ml-pre-confirmation.bundle.json"
CONFIRMED_PATH = RESULTS / "2026-08-05-f01-f05-nuclear-ml-confirmed.bundle.json"
VALIDATION_PATH = RESULTS / "2026-08-05-f01-f05-nuclear-ml-confirmed.validation.json"
MANIFEST_PATH = RESULTS / "2026-08-05-f01-f05-nuclear-ml-confirmed.manifest.json"
NOTES_PATH = RESULTS / "2026-08-05-f01-f05-nuclear-ml-confirmed.confirmation.md"
VALIDATOR_PATH = (
    ROOT
    / "skills"
    / "engineering-research-copilot"
    / "scripts"
    / "validate_m2_direction_bundle.py"
)

BASELINE_COMMIT = "d0f5e9017044ba35d0ac4559591028228f3b22d8"
DIRECTION_ID = "NEML-F01-D1"
MESSAGE = "我确认正式方向<NEML-F01-D1>。"
MESSAGE_ID = "codex:2026-08-05:m3.1.1:forward-confirmation:neml-f01-d1"


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def raw_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    payload = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(payload)


def write_text(path: Path, value: str) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(value)


def validate_once(bundle_path: Path) -> tuple[dict[str, Any], str, int]:
    completed = subprocess.run(
        [sys.executable, "-X", "utf8", str(VALIDATOR_PATH), str(bundle_path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        check=False,
    )
    stdout = completed.stdout.rstrip("\r\n")
    if "\n" in stdout or "\r" in stdout or not stdout:
        raise RuntimeError("m2_validator_stdout_not_one_line_json")
    result = json.loads(stdout)
    if not isinstance(result, dict):
        raise RuntimeError("m2_validator_output_not_object")
    return result, stdout, completed.returncode


def main() -> int:
    if not DRAFT_PATH.is_file():
        raise SystemExit(f"missing draft: {DRAFT_PATH}")
    if any(path.exists() for path in (CONFIRMED_PATH, VALIDATION_PATH, MANIFEST_PATH, NOTES_PATH)):
        raise SystemExit("confirmation_artifact_already_exists")

    draft = json.loads(DRAFT_PATH.read_text(encoding="utf-8"))
    expected_decision = {
        "selected_direction_id": None,
        "status": "waiting_for_user_confirmation",
        "permitted_next_actions": ["confirm", "modify", "reject"],
        "confirmation_event": None,
    }
    if draft.get("direction_decision") != expected_decision:
        raise SystemExit("draft_is_not_immutable_waiting_confirmation_state")
    if draft.get("route_output") is not None:
        raise SystemExit("draft_route_output_must_be_null")

    previous_bundle_hash = canonical_sha256(draft)
    if previous_bundle_hash != "6ab5d3d67f5450794214b2199d2f2e9ca3ed301e2773c763cff2adbfcb49dd8c":
        raise SystemExit("unexpected_preconfirmation_bundle_hash")

    confirmation_event = {
        "actor_role": "user",
        "selected_direction_id": DIRECTION_ID,
        "source_message_id": MESSAGE_ID,
        "source_message_excerpt": MESSAGE,
        "source_message_sha256": hashlib.sha256(MESSAGE.encode("utf-8")).hexdigest(),
        "previous_bundle_hash": previous_bundle_hash,
    }

    confirmed = dict(draft)
    confirmed["direction_decision"] = {
        "selected_direction_id": DIRECTION_ID,
        "status": "user_confirmed",
        "permitted_next_actions": ["modify", "reject", "generate_route"],
        "confirmation_event": confirmation_event,
    }
    confirmed["route_output"] = None
    write_json(CONFIRMED_PATH, confirmed)

    validation, raw_output, exit_code = validate_once(CONFIRMED_PATH)
    write_json(VALIDATION_PATH, validation)
    if exit_code != 0 or validation.get("status") != "valid":
        raise SystemExit("confirmed_bundle_failed_m2_validation")

    manifest = {
        "manifest_kind": "m2.1.1_confirmed_bundle",
        "status": "user_confirmed",
        "baseline_commit": BASELINE_COMMIT,
        "upstream_preconfirmation_bundle": DRAFT_PATH.relative_to(ROOT).as_posix(),
        "preconfirmation_bundle_canonical_sha256": previous_bundle_hash,
        "bundle_path": CONFIRMED_PATH.relative_to(ROOT).as_posix(),
        "bundle_file_sha256": raw_sha256(CONFIRMED_PATH),
        "bundle_canonical_sha256": canonical_sha256(confirmed),
        "selected_direction_id": DIRECTION_ID,
        "confirmation_event": confirmation_event,
        "validator": {
            "script": VALIDATOR_PATH.relative_to(ROOT).as_posix(),
            "scope": "M2.1.1 structural contract only",
            "result": validation["status"],
            "exit_code": exit_code,
            "receipt_path": VALIDATION_PATH.relative_to(ROOT).as_posix(),
            "raw_output": raw_output,
        },
        "does_not_prove": [
            "empirical target-domain performance",
            "nuclear safety or plant deployment",
            "route execution, experiment, simulation, training, or resource allocation",
        ],
    }
    write_json(MANIFEST_PATH, manifest)

    notes = f"""# M2.1.1 confirmed direction: NEML-F01-D1

Status: `user_confirmed`.

This artifact is the immutable successor of the independent pre-confirmation draft.
The user confirmation message was recorded exactly as received; the confirmation event
binds it to the selected formal direction and the pre-confirmation canonical hash.

## Confirmation

- selected direction: `{DIRECTION_ID}`
- source message ID: `{MESSAGE_ID}`
- source message: `{MESSAGE}`
- pre-confirmation canonical SHA-256: `{previous_bundle_hash}`
- confirmation event message SHA-256: `{confirmation_event['source_message_sha256']}`

## Saved artifacts

- bundle: `{CONFIRMED_PATH.relative_to(ROOT).as_posix()}`
- bundle raw SHA-256: `{raw_sha256(CONFIRMED_PATH)}`
- bundle canonical SHA-256: `{canonical_sha256(confirmed)}`
- M2 validator receipt: `{VALIDATION_PATH.relative_to(ROOT).as_posix()}`
- M2 validator result: `{validation['status']}` with exit code `{exit_code}`

The validator result is an M2.1.1 structural contract result only. It does not prove
empirical target-domain performance, nuclear safety, route execution, or deployment.
No route output was generated in this confirmation step.
"""
    write_text(NOTES_PATH, notes)

    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
