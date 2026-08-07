#!/usr/bin/env python3
"""Read-only audit of the r5.1-f02 root-cause report.

The default audit is repository-portable. Local source/child rollout files and
the external authorization attachment can be supplied explicitly for a deeper
hash and semantic check; they are never required by CI and are never modified.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from functools import lru_cache
from pathlib import Path, PurePosixPath
from typing import Any, Callable


REPO_ROOT = Path(__file__).resolve().parents[2]
REPORT_RELATIVE = Path(
    "evals/m3/results/diagnostics-r5.2-f02/root-cause-report.json"
)
REPORT = REPO_ROOT / REPORT_RELATIVE

GATE0_HEAD = "fb5eec44bbf86446cf12bda2bddc76fcb07a7e69"
HISTORICAL_R5_HEAD = "1b696bce53ee0a11163bfe4f91a9a49ab3af6f49"
TASK_ID = "019fdb7c-1728-7a92-b6cf-b0eb631a18b8"
CONSUMED_TURN_ID = "019fdb7c-201e-7a72-bbed-853b45fbfae9"
LATE_TURN_ID = "019fdb8e-9558-7a22-a7f5-edc52db5f9d9"
RAW_SHA256 = "75b4f9f5f4e2459b2886c0a9654c8cc1bda4015c525869cd154a302a2bc0589a"
REQUEST_ENVELOPE_SHA256 = (
    "42614c8fe17f6cf51782c684fec425d536b37e514a87f34008f2fc03e8c829f5"
)
MODEL_VISIBLE_MESSAGES_SHA256 = (
    "2da3fb7701acb7a7c2e0be8d37afce85c52f2dd10fa62156a77a4ff4d534da03"
)
OBSERVED_CONTEXT_SHA256 = (
    "b85d0f731f4050f9311ac062af373c3a8717db3855e9877d5cd9bb814624d7f2"
)
FINALIZATION_SHA256 = (
    "d112c2622de14edd8f648ca7d13fb4309294664fb5a232f3336979729e8ad007"
)
EXPECTED_FINAL = (
    "Acknowledged. I have preserved this as frozen preparation evidence and have "
    "not read files, used network access, written files, or executed the r5.1-f02 "
    "task. A separate explicit authorization is required to proceed."
).encode("utf-8")

TOP_LEVEL_KEYS = {
    "schema_version",
    "report_status",
    "report_mode",
    "revision",
    "case_id",
    "task_id",
    "consumed_turn_id",
    "late_authorized_turn_id",
    "gate0_head",
    "raw_output_bytes",
    "raw_output_sha256",
    "utf8_valid",
    "json_valid",
    "json_error",
    "content_classification",
    "model_visible_authorization",
    "finish_reason",
    "finish_reason_status",
    "output_tokens",
    "request_envelope_sha256",
    "model_visible_messages_sha256",
    "finalization_sha256",
    "context_layers",
    "platform_observation",
    "parser_replay",
    "hypotheses",
    "primary_root_cause",
    "protocol_implications",
    "immutable_evidence",
    "historical_immutability",
    "gate_state",
    "forbidden_actions",
    "limitations",
}

HYPOTHESIS_ORDER = (
    "model_did_not_see_authorization",
    "model_followed_do_not_execute_instruction",
    "output_truncated",
    "wrong_message_field_saved",
    "markdown_or_affix_broke_json",
    "composer_path_error",
)

EVIDENCE_SPECS = {
    "prompt": {
        "path": "evals/m3/forward-inputs-r5.1-f02/m3-f02.prompt.txt",
        "source_head": "85ce824c55a3a40f3f05153a57edb809dc68eee6",
        "git_blob_oid": "f2e9ab2a35b0f64924eea0f3716117362d996017",
        "byte_length": 4142,
        "raw_sha256": "4dccc73a442664088594d834805ad5c780674beffc4607309a74fd3f541ccd68",
    },
    "execution_authorization": {
        "path": "evals/m3/forward-inputs-r5.1-f02/execution-authorization.json",
        "source_head": "85ce824c55a3a40f3f05153a57edb809dc68eee6",
        "git_blob_oid": "d616391ab9ad60c4683fdce6602ad11588d7c60f",
        "byte_length": 7136,
        "raw_sha256": "aec40aef8e855cd42464080066f475bf3d05de5ef8a2936d8f12750783af81ff",
    },
    "terminal_manifest": {
        "path": "evals/m3/results/forward-r5.1-f02/terminal-manifest.json",
        "source_head": GATE0_HEAD,
        "git_blob_oid": "3b862581be63529012495b8579f29e16dbb6f02b",
        "byte_length": 8457,
        "raw_sha256": "c8d8060e781b601b9dc7120b0cdf2615f9a9709fd67d9745a8d31dd682b8f9db",
    },
    "model_final": {
        "path": "evals/m3/results/forward-r5.1-f02/m3-f02.model-final.json",
        "source_head": "a847b3eaf39a6f4f70353cd669e41e414afc658c",
        "git_blob_oid": "8c5ed1d1818039600c52e67544b746d34c41a857",
        "byte_length": 216,
        "raw_sha256": RAW_SHA256,
    },
    "payload": {
        "path": "evals/m3/results/forward-r5.1-f02/m3-f02.payload.json",
        "source_head": "a847b3eaf39a6f4f70353cd669e41e414afc658c",
        "git_blob_oid": "8c5ed1d1818039600c52e67544b746d34c41a857",
        "byte_length": 216,
        "raw_sha256": RAW_SHA256,
    },
    "composer_receipt": {
        "path": "evals/m3/results/forward-r5.1-f02/m3-f02.composer-receipt.json",
        "source_head": "a847b3eaf39a6f4f70353cd669e41e414afc658c",
        "git_blob_oid": "9050810ecf856ab1589d2f8b05e0c3f5a682aaef",
        "byte_length": 470,
        "raw_sha256": "befa69fec4d196ff6d76d3c2c2f88d726ff6d69ed9f75844d475f043b8c250e9",
    },
    "context": {
        "path": "evals/m3/results/forward-r5.1-f02/m3-f02.context.json",
        "source_head": "a847b3eaf39a6f4f70353cd669e41e414afc658c",
        "git_blob_oid": "19c412d218aebd630fbd840411a980b4fc65a1d2",
        "byte_length": 426,
        "raw_sha256": "71babe1b72d5cbb380fbe6d5af9e6fe8d54f60bdfec023cdbb1b95ad3f53320e",
    },
    "transaction": {
        "path": "evals/m3/results/forward-r5.1-f02/m3-f02.transaction.json",
        "source_head": "a847b3eaf39a6f4f70353cd669e41e414afc658c",
        "git_blob_oid": "161a2a7fa1730f3aa4be7d377ee221a9a2de49e4",
        "byte_length": 335,
        "raw_sha256": "ec6f5985e340176ee90bd5dcf2d52b981c9a818e5ca07934f714a21478206fa3",
    },
}

SOURCE_KEY_RECORD_HASHES = {
    203: "158604a9cd9f00e46cb47cdcfc2906fd99dcfde51c42e71411eb68b6b1bdb546",
    204: "34e34e050f498d93b481100bb1a9f951f83770e85aba783540ddc1f44cec47e9",
    303: "5c17b35b322e3bf8f022683184a3da196f838ad42a6a1ad04914d61006bd3664",
    304: "0a6d72bf9a2033b811926eb26297c47bc561249d3adcadf88cca5a8243b0fc21",
    330: "f8200c33ee772511200cd4010ac5ebb6ab40b8f8af5fecee1b4f5dd9b9c34ccf",
    331: "5f28517150cba5635b181f1c2d1d73747c4925ab1e5c6f36a5bfab24f04e6256",
    336: "a0949e973db9fe487e0ebce4d173e77f9ddacd6333d01da13ae9d9bab7b52c13",
    337: "89b8f4b85cd704e25a97f8d53ff4aa3e998a3c34be955ba18489a8a6235ce414",
    453: "2ad807413a3669e4ee160660e7ef78f42727005050920f65a3dbf3c443547761",
}

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
OID_RE = re.compile(r"^[0-9a-f]{40}$")


class _DuplicateKey(ValueError):
    pass


def _reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise _DuplicateKey(key)
        value[key] = item
    return value


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_sha256(value: Any) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return sha256(raw)


def _add(errors: list[str], code: str) -> None:
    if code not in errors:
        errors.append(code)


def _load_object(path: Path, errors: list[str], code: str) -> dict[str, Any] | None:
    try:
        raw = path.read_bytes()
    except OSError:
        _add(errors, f"{code}_unreadable")
        return None
    if raw.startswith(b"\xef\xbb\xbf"):
        _add(errors, f"{code}_utf8_bom_forbidden")
        return None
    try:
        value = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=_reject_duplicates,
            parse_constant=lambda token: (_ for _ in ()).throw(ValueError(token)),
        )
    except (UnicodeError, json.JSONDecodeError, ValueError):
        _add(errors, f"{code}_invalid_json")
        return None
    if not isinstance(value, dict):
        _add(errors, f"{code}_must_be_object")
        return None
    return value


def _expect(
    value: Any,
    required: Any,
    errors: list[str],
    code: str,
) -> None:
    if isinstance(required, int) and not isinstance(required, bool):
        if isinstance(value, bool) or not isinstance(value, int) or value != required:
            _add(errors, code)
    elif value != required:
        _add(errors, code)


def _safe_relative(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    path = PurePosixPath(value)
    return not path.is_absolute() and ".." not in path.parts and "\\" not in value


@lru_cache(maxsize=None)
def _git_blob(repo_root: Path, head: str, path: str) -> tuple[str, bytes] | None:
    try:
        oid = subprocess.run(
            ["git", "rev-parse", f"{head}:{path}"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        raw = subprocess.run(
            ["git", "show", f"{head}:{path}"],
            cwd=repo_root,
            capture_output=True,
            check=False,
        )
    except OSError:
        return None
    if oid.returncode != 0 or raw.returncode != 0:
        return None
    return oid.stdout.strip(), raw.stdout


@lru_cache(maxsize=None)
def _git_diff_empty(repo_root: Path, head: str, relative: str) -> bool:
    try:
        result = subprocess.run(
            ["git", "diff", "--exit-code", head, "HEAD", "--", relative],
            cwd=repo_root,
            capture_output=True,
            check=False,
        )
    except OSError:
        return False
    return result.returncode == 0 and not result.stdout and not result.stderr


def _gate0_is_ancestor(repo_root: Path) -> bool:
    try:
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", GATE0_HEAD, "HEAD"],
            cwd=repo_root,
            capture_output=True,
            check=False,
        )
    except OSError:
        return False
    return result.returncode == 0


def _text_content(message: dict[str, Any]) -> str:
    content = message.get("content")
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for item in content:
        if isinstance(item, dict) and isinstance(item.get("text"), str):
            parts.append(item["text"])
    return "".join(parts)


def _verify_report_shape(report: dict[str, Any], errors: list[str]) -> None:
    if set(report) != TOP_LEVEL_KEYS:
        _add(errors, "report_top_level_keys_invalid")

    expected_scalars = {
        "schema_version": "m3.1-r5.2-f02-root-cause-v1",
        "report_status": "root_cause_confirmed",
        "report_mode": "read_only_no_fresh_execution",
        "revision": "r5.1-f02",
        "case_id": "m3-f02",
        "task_id": TASK_ID,
        "consumed_turn_id": CONSUMED_TURN_ID,
        "late_authorized_turn_id": LATE_TURN_ID,
        "gate0_head": GATE0_HEAD,
        "raw_output_bytes": 216,
        "raw_output_sha256": RAW_SHA256,
        "utf8_valid": True,
        "json_valid": False,
        "content_classification": "non_json_authorization_deferral_prose",
        "model_visible_authorization": "absent_in_consumed_turn",
        "finish_reason": None,
        "finish_reason_status": "not_recorded",
        "output_tokens": 102,
        "request_envelope_sha256": REQUEST_ENVELOPE_SHA256,
        "model_visible_messages_sha256": MODEL_VISIBLE_MESSAGES_SHA256,
        "finalization_sha256": FINALIZATION_SHA256,
    }
    error_codes = {
        "task_id": "task_id_invalid",
        "raw_output_sha256": "raw_output_sha256_invalid",
        "output_tokens": "output_tokens_invalid",
    }
    for field, required in expected_scalars.items():
        _expect(
            report.get(field),
            required,
            errors,
            error_codes.get(field, f"report_field_invalid:{field}"),
        )

    if report.get("json_error") != {
        "message": "Expecting value",
        "line": 1,
        "column": 1,
        "byte_offset": 0,
    }:
        _add(errors, "json_error_invalid")

    for field in (
        "raw_output_sha256",
        "request_envelope_sha256",
        "model_visible_messages_sha256",
        "finalization_sha256",
    ):
        if not isinstance(report.get(field), str) or not SHA256_RE.fullmatch(
            report[field]
        ):
            _add(errors, f"sha256_invalid:{field}")

    layers = report.get("context_layers")
    if not isinstance(layers, dict) or set(layers) != {
        "frozen_repository_prompt",
        "consumed_turn_model_visible_context",
        "external_user_authorization",
        "late_authorized_turn",
    }:
        _add(errors, "context_layers_invalid")
        layers = {}
    prompt = layers.get("frozen_repository_prompt", {})
    consumed = layers.get("consumed_turn_model_visible_context", {})
    external = layers.get("external_user_authorization", {})
    late = layers.get("late_authorized_turn", {})

    for field in (
        "embedded_in_delegation_unchanged",
        "contains_future_task_instruction",
        "contains_do_not_execute_instruction",
        "requires_separate_authorization",
    ):
        if prompt.get(field) is not True:
            _add(errors, f"frozen_prompt_finding_invalid:{field}")
    if prompt.get("authorization_grant_present") is not False:
        _add(errors, "frozen_prompt_authorization_grant_invalid")
    if consumed.get("authorization_visible") is not False:
        _add(errors, "consumed_turn_authorization_visibility_invalid")
    if consumed.get("external_authorization_text_embedded") is not False:
        _add(errors, "consumed_turn_external_authorization_invalid")
    if consumed.get("turn_id") != CONSUMED_TURN_ID:
        _add(errors, "consumed_turn_id_invalid")
    if consumed.get("request_envelope_sha256") != REQUEST_ENVELOPE_SHA256:
        _add(errors, "request_envelope_binding_invalid")
    if consumed.get("model_visible_messages_sha256") != MODEL_VISIBLE_MESSAGES_SHA256:
        _add(errors, "model_visible_messages_binding_invalid")
    if consumed.get("observed_context_sha256") != OBSERVED_CONTEXT_SHA256:
        _add(errors, "observed_context_binding_invalid")
    if external.get("present") is not True:
        _add(errors, "external_authorization_presence_invalid")
    if external.get("visible_in_consumed_turn") is not False:
        _add(errors, "external_authorization_visibility_invalid")
    if external.get("present_before_child_creation") is not True:
        _add(errors, "external_authorization_timing_invalid")
    if late.get("turn_id") != LATE_TURN_ID:
        _add(errors, "late_turn_id_invalid")
    if late.get("authorization_visible") is not True:
        _add(errors, "late_authorization_visibility_invalid")
    for field in (
        "occurred_after_consumed_turn_completion",
        "occurred_after_terminal_consumption",
        "not_consumed_by_r5_1_finalizer",
    ):
        if late.get(field) is not True:
            _add(errors, "late_authorization_timing_invalid")
    if late.get("late_output_evidence_semantics") != (
        "post_terminal_observation_only_not_a_retry_or_repair"
    ):
        _add(errors, "late_output_semantics_invalid")

    platform = report.get("platform_observation")
    if not isinstance(platform, dict):
        _add(errors, "platform_observation_invalid")
        platform = {}
    platform_expected = {
        "model": "gpt-5.6-sol",
        "reasoning_effort": "xhigh",
        "request_id": None,
        "request_id_status": "not_recorded",
        "finish_reason": None,
        "finish_reason_status": "not_recorded",
        "platform_status": "completed",
        "incomplete_event_observed": False,
        "output_tokens": 102,
        "finalization_sha256": FINALIZATION_SHA256,
        "assistant_final_equals_task_complete_final": True,
        "assistant_final_equals_frozen_model_final": True,
    }
    for field, required in platform_expected.items():
        _expect(
            platform.get(field),
            required,
            errors,
            f"platform_observation_invalid:{field}",
        )

    replay = report.get("parser_replay")
    if not isinstance(replay, dict):
        _add(errors, "parser_replay_invalid")
        replay = {}
    replay_expected = {
        "mode": "offline_existing_composer_load_object",
        "replay_count": 1,
        "model_calls": 0,
        "writes": 0,
        "retry_count": 0,
        "utf8_valid": True,
        "failure_code": "payload_invalid_json",
        "message": "Expecting value",
        "line": 1,
        "column": 1,
        "position": 0,
        "byte_offset": 0,
        "composer_success": False,
        "validator_invocations": 0,
        "observation_only": True,
    }
    for field, required in replay_expected.items():
        before = len(errors)
        _expect(replay.get(field), required, errors, "parser_replay_invalid")
        if len(errors) > before:
            break

    hypotheses = report.get("hypotheses")
    if not isinstance(hypotheses, list) or [
        item.get("id") if isinstance(item, dict) else None for item in hypotheses
    ] != list(HYPOTHESIS_ORDER):
        _add(errors, "hypothesis_order_invalid")
        hypotheses = []
    dispositions = {
        "model_did_not_see_authorization": "confirmed",
        "model_followed_do_not_execute_instruction": "confirmed",
        "output_truncated": "ruled_out",
        "wrong_message_field_saved": "ruled_out",
        "markdown_or_affix_broke_json": "ruled_out",
        "composer_path_error": "ruled_out",
    }
    for item in hypotheses:
        if item.get("disposition") != dispositions.get(item.get("id")):
            _add(errors, f"hypothesis_disposition_invalid:{item.get('id')}")
        evidence = item.get("direct_evidence")
        if not isinstance(evidence, list) or not evidence or not all(
            isinstance(entry, str) and entry for entry in evidence
        ):
            _add(errors, f"hypothesis_evidence_invalid:{item.get('id')}")

    primary = report.get("primary_root_cause")
    if not isinstance(primary, dict) or primary.get("code") != (
        "authorization_not_visible_in_consumed_turn"
    ):
        _add(errors, "primary_root_cause_invalid")
    elif primary.get("confidence") != "direct_evidence":
        _add(errors, "primary_root_cause_confidence_invalid")

    implications = report.get("protocol_implications")
    if not isinstance(implications, dict) or implications.get("scope") != (
        "design_requirements_only_no_gate2_artifacts_or_execution"
    ):
        _add(errors, "protocol_implications_scope_invalid")

    state = report.get("gate_state")
    if not isinstance(state, dict):
        _add(errors, "gate_state_invalid")
        state = {}
    state_expected = {
        "gate1": "COMPLETE",
        "gate2": "NOT_STARTED",
        "fresh_execution": "NOT_RUN",
        "new_fresh_run_authorized": False,
        "r5_2_task_count": 0,
        "r5_2_finalization_count": 0,
        "r5_2_composer_count": 0,
        "r5_2_validator_count": 0,
        "r5_2_retry_count": 0,
        "r5_2_result_root": "ABSENT",
        "r5_1_f02": "TERMINAL_NOT_ACCEPTED",
        "r5_1_f02_accepted": False,
        "historical_r5": "BLOCKED_NOT_ACCEPTED",
        "m3": "IN_PROGRESS",
        "cross_revision_aggregate": "NOT_RUN",
        "m3_closure": "NOT_RUN",
        "m4": "NOT_STARTED",
    }
    for field, required in state_expected.items():
        code = (
            "fresh_execution_authorization_invalid"
            if field == "new_fresh_run_authorized"
            else f"gate_state_invalid:{field}"
        )
        _expect(state.get(field), required, errors, code)

    forbidden = report.get("forbidden_actions")
    if not isinstance(forbidden, list) or not {
        "fresh_task_creation",
        "fresh_model_execution",
        "forward_r5_2_result_creation",
        "push",
    }.issubset(set(forbidden)):
        _add(errors, "forbidden_actions_invalid")


def _verify_repository_evidence(
    report: dict[str, Any], repo_root: Path, errors: list[str]
) -> None:
    evidence = report.get("immutable_evidence")
    if not isinstance(evidence, dict) or set(evidence) != set(EVIDENCE_SPECS):
        _add(errors, "immutable_evidence_keys_invalid")
        evidence = {}
    raw_values: dict[str, bytes] = {}
    for key, expected in EVIDENCE_SPECS.items():
        binding = evidence.get(key)
        if binding != expected:
            _add(errors, f"immutable_evidence_binding_invalid:{key}")
        path = expected["path"]
        if not _safe_relative(path):
            _add(errors, f"immutable_evidence_path_invalid:{key}")
            continue
        file_path = repo_root / Path(path)
        try:
            raw = file_path.read_bytes()
        except OSError:
            _add(errors, f"immutable_evidence_unreadable:{key}")
            continue
        raw_values[key] = raw
        if len(raw) != expected["byte_length"]:
            _add(errors, f"immutable_evidence_length_mismatch:{key}")
        if sha256(raw) != expected["raw_sha256"]:
            _add(errors, f"immutable_evidence_hash_mismatch:{key}")
        blob = _git_blob(repo_root, expected["source_head"], path)
        if blob is None:
            _add(errors, f"immutable_evidence_git_blob_unavailable:{key}")
        else:
            oid, git_raw = blob
            if oid != expected["git_blob_oid"]:
                _add(errors, f"immutable_evidence_git_oid_mismatch:{key}")
            if git_raw != raw:
                _add(errors, f"immutable_evidence_worktree_drift:{key}")

    model_final = raw_values.get("model_final")
    payload = raw_values.get("payload")
    if model_final != EXPECTED_FINAL or payload != EXPECTED_FINAL:
        _add(errors, "raw_output_content_invalid")
    if model_final != payload:
        _add(errors, "model_final_payload_mismatch")
    if payload is not None:
        try:
            text = payload.decode("utf-8", errors="strict")
        except UnicodeError:
            _add(errors, "raw_output_utf8_invalid")
        else:
            if payload.startswith(b"\xef\xbb\xbf"):
                _add(errors, "raw_output_bom_present")
            stripped = text.strip()
            if not stripped.startswith("Acknowledged."):
                _add(errors, "raw_output_classification_invalid")
            if "```" in stripped or "{" in stripped or "}" in stripped:
                _add(errors, "raw_output_affix_classification_invalid")

    prompt_raw = raw_values.get("prompt")
    if prompt_raw is not None:
        try:
            prompt_text = prompt_raw.decode("utf-8", errors="strict")
        except UnicodeError:
            _add(errors, "frozen_prompt_utf8_invalid")
        else:
            for phrase in (
                "future r5.1-f02 replacement task",
                "do not execute it without a separate user authorization",
            ):
                if phrase not in prompt_text:
                    _add(errors, "frozen_prompt_contradiction_missing")

    parsed: dict[str, dict[str, Any]] = {}
    for key in ("terminal_manifest", "composer_receipt", "context", "transaction"):
        if key not in raw_values:
            continue
        try:
            value = json.loads(
                raw_values[key].decode("utf-8", errors="strict"),
                object_pairs_hook=_reject_duplicates,
            )
        except (UnicodeError, json.JSONDecodeError, ValueError):
            _add(errors, f"repository_json_invalid:{key}")
            continue
        if not isinstance(value, dict):
            _add(errors, f"repository_json_not_object:{key}")
            continue
        parsed[key] = value

    manifest = parsed.get("terminal_manifest", {})
    if manifest.get("status") != "terminal_not_accepted":
        _add(errors, "terminal_manifest_status_invalid")
    if manifest.get("accepted") is not False:
        _add(errors, "terminal_manifest_accepted_invalid")
    if manifest.get("fresh_task_id") != TASK_ID:
        _add(errors, "terminal_manifest_task_id_invalid")
    counters = manifest.get("counters", {})
    counter_expected = {
        "tasks_launched": 1,
        "task_finalizations_observed": 1,
        "composer_invocations": 1,
        "validator_invocations": 0,
        "retry_count": 0,
        "repair_count": 0,
    }
    for field, required in counter_expected.items():
        _expect(
            counters.get(field), required, errors, f"terminal_counter_invalid:{field}"
        )

    composer = parsed.get("composer_receipt", {})
    if composer.get("status") != "failed" or composer.get("failure_code") != (
        "payload_invalid_json"
    ):
        _add(errors, "composer_terminal_observation_invalid")
    context = parsed.get("context", {})
    transaction = parsed.get("transaction", {})
    for key, value in (("context", context), ("transaction", transaction)):
        if value.get("state") != "processing_failed" or value.get("accepted") is not False:
            _add(errors, f"transaction_state_invalid:{key}")
        if value.get("task_id") != TASK_ID:
            _add(errors, f"transaction_task_id_invalid:{key}")

    if not _gate0_is_ancestor(repo_root):
        _add(errors, "gate0_head_not_ancestor")


def _verify_child_rollout(
    path: Path,
    report: dict[str, Any],
    repo_root: Path,
    errors: list[str],
) -> None:
    try:
        raw = path.read_bytes()
    except OSError:
        _add(errors, "child_rollout_unreadable")
        return
    lines = raw.splitlines(keepends=True)
    if len(lines) < 105:
        _add(errors, "child_rollout_too_short")
        return
    try:
        records = [json.loads(line) for line in lines[:105]]
    except (UnicodeError, json.JSONDecodeError):
        _add(errors, "child_rollout_invalid_jsonl")
        return

    consumed = report["context_layers"]["consumed_turn_model_visible_context"]
    prefix = consumed["child_rollout_prefix"]
    prefix_raw = b"".join(lines[:15])
    if len(prefix_raw) != prefix.get("byte_length") or sha256(prefix_raw) != prefix.get(
        "raw_sha256"
    ):
        _add(errors, "child_consumed_prefix_mismatch")
    late = report["context_layers"]["late_authorized_turn"]
    late_raw = b"".join(lines[15:105])
    late_binding = late["child_rollout_segment"]
    if len(late_raw) != late_binding.get("byte_length") or sha256(
        late_raw
    ) != late_binding.get("raw_sha256"):
        _add(errors, "child_late_segment_mismatch")

    base = records[0].get("payload", {}).get("base_instructions")
    message_numbers = [3, 4, 5, 6, 9]
    messages = [records[number - 1].get("payload", {}) for number in message_numbers]
    if not isinstance(base, dict) or not isinstance(base.get("text"), str):
        _add(errors, "child_base_instructions_invalid")
        return
    visible_messages = [
        {
            "role": "system",
            "content": [{"type": "input_text", "text": base["text"]}],
        }
    ] + [
        {"role": message.get("role"), "content": message.get("content")}
        for message in messages
    ]
    request_projection = {
        "base_instructions": base,
        "messages": messages,
        "world_state": records[6].get("payload"),
        "turn_context": records[7].get("payload"),
    }
    observed_projection = {
        "records": [records[number - 1] for number in [1, 3, 4, 5, 6, 7, 8, 9]]
    }
    final_projection = {
        "assistant_final": records[12].get("payload"),
        "last_token_usage": records[13]
        .get("payload", {})
        .get("info", {})
        .get("last_token_usage"),
        "task_complete": records[14].get("payload"),
    }
    if canonical_sha256(request_projection) != REQUEST_ENVELOPE_SHA256:
        _add(errors, "child_request_envelope_mismatch")
    if canonical_sha256(visible_messages) != MODEL_VISIBLE_MESSAGES_SHA256:
        _add(errors, "child_visible_messages_mismatch")
    if canonical_sha256(observed_projection) != OBSERVED_CONTEXT_SHA256:
        _add(errors, "child_observed_context_mismatch")
    if canonical_sha256(final_projection) != FINALIZATION_SHA256:
        _add(errors, "child_finalization_mismatch")

    expected_messages = consumed.get("messages")
    observed_messages: list[dict[str, Any]] = []
    for number, message in zip(message_numbers, messages, strict=True):
        text = _text_content(message)
        text_raw = text.encode("utf-8")
        observed_messages.append(
            {
                "record_number": number,
                "role": message.get("role"),
                "message_id": message.get("id"),
                "byte_length": len(text_raw),
                "raw_sha256": sha256(text_raw),
            }
        )
    if observed_messages != expected_messages:
        _add(errors, "child_message_identities_mismatch")

    delegation_text = _text_content(messages[-1])
    if "<input>" not in delegation_text or "</input>" not in delegation_text:
        _add(errors, "child_delegation_envelope_invalid")
    else:
        embedded = delegation_text.split("<input>", 1)[1].rsplit("</input>", 1)[0]
        try:
            prompt_raw = (repo_root / EVIDENCE_SPECS["prompt"]["path"]).read_bytes()
        except OSError:
            _add(errors, "child_prompt_comparison_unavailable")
        else:
            if embedded.encode("utf-8") != prompt_raw:
                _add(errors, "child_embedded_prompt_mismatch")

    assistant_final = _text_content(records[12].get("payload", {})).encode("utf-8")
    complete_final = (
        records[14].get("payload", {}).get("last_agent_message", "").encode("utf-8")
    )
    if assistant_final != EXPECTED_FINAL or complete_final != EXPECTED_FINAL:
        _add(errors, "child_consumed_final_mismatch")
    if records[14].get("payload", {}).get("turn_id") != CONSUMED_TURN_ID:
        _add(errors, "child_consumed_turn_id_mismatch")
    if records[13].get("payload", {}).get("info", {}).get(
        "last_token_usage", {}
    ).get("output_tokens") != 102:
        _add(errors, "child_output_tokens_mismatch")

    late_auth = _text_content(records[18].get("payload", {})).encode("utf-8")
    if len(late_auth) != 7 or sha256(late_auth) != (
        "74c693d3f212ff7f7baedc1f7af150bee4012026aef934b76709aebb6a580ce7"
    ):
        _add(errors, "child_late_authorization_mismatch")
    late_final = _text_content(records[102].get("payload", {})).encode("utf-8")
    if len(late_final) != 12605 or sha256(late_final) != (
        "6bc32fb62507672d7d21a37a828217078443381f6ffb0413c93626e02f53e583"
    ):
        _add(errors, "child_late_final_mismatch")
    if records[17].get("payload", {}).get("turn_id") != LATE_TURN_ID:
        _add(errors, "child_late_turn_id_mismatch")


def _verify_source_rollout(path: Path, report: dict[str, Any], errors: list[str]) -> None:
    try:
        raw = path.read_bytes()
    except OSError:
        _add(errors, "source_rollout_unreadable")
        return
    lines = raw.splitlines(keepends=True)
    if len(lines) < 453:
        _add(errors, "source_rollout_too_short")
        return
    binding = report["historical_immutability"]["source_rollout_terminal_prefix"]
    prefix = b"".join(lines[:453])
    if len(prefix) != binding.get("byte_length") or sha256(prefix) != binding.get(
        "raw_sha256"
    ):
        _add(errors, "source_rollout_prefix_mismatch")
    for number, expected in SOURCE_KEY_RECORD_HASHES.items():
        if sha256(lines[number - 1]) != expected:
            _add(errors, f"source_rollout_record_mismatch:{number}")

    decoded = {number: lines[number - 1].decode("utf-8") for number in SOURCE_KEY_RECORD_HASHES}
    semantic_checks = {
        203: (
            "codex_app__create_thread",
            "m3-f02.prompt.txt",
            "codex/m3.1.1-r5.1-f02-one-shot-execution-authorization",
        ),
        304: (TASK_ID, CONSUMED_TURN_ID, "latestAssistantMessage"),
        330: ("latestAssistantMessage", "final_answer", "msg.text"),
        336: ("latestAssistantMessage", "final_answer", "msg.text"),
        337: (RAW_SHA256, "payload_invalid_json", "processing_failed"),
    }
    for number, terms in semantic_checks.items():
        if not all(term in decoded[number] for term in terms):
            _add(errors, f"source_rollout_semantics_invalid:{number}")
    for line in lines[203:337]:
        if b"tools.codex_app__send_message_to_thread" in line:
            _add(errors, "source_rollout_followup_message_detected")
            break


def _verify_external_authorization(
    path: Path,
    report: dict[str, Any],
    child_rollout: Path | None,
    errors: list[str],
) -> None:
    try:
        raw = path.read_bytes()
    except OSError:
        _add(errors, "external_authorization_unreadable")
        return
    binding = report["context_layers"]["external_user_authorization"]
    if len(raw) != binding.get("byte_length") or sha256(raw) != binding.get(
        "raw_sha256"
    ):
        _add(errors, "external_authorization_identity_mismatch")
        return
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeError:
        _add(errors, "external_authorization_utf8_invalid")
        return
    for phrase in (
        "这是第一次真正执行新的 replacement F02 fresh context",
        "创建且只创建一个新的 fresh F02 task",
        "获得且只获得一次 fresh finalization",
    ):
        if phrase not in text:
            _add(errors, "external_authorization_scope_invalid")
    if child_rollout is not None:
        try:
            lines = child_rollout.read_bytes().splitlines(keepends=True)
            records = [json.loads(lines[number - 1]) for number in (3, 4, 5, 6, 9)]
        except (OSError, UnicodeError, json.JSONDecodeError, IndexError):
            _add(errors, "external_authorization_child_comparison_unavailable")
        else:
            visible = "\n".join(_text_content(record.get("payload", {})) for record in records)
            if text in visible:
                _add(errors, "external_authorization_unexpectedly_visible")


def audit_report(
    path: str | Path,
    *,
    repo_root: Path = REPO_ROOT,
    child_rollout: str | Path | None = None,
    source_rollout: str | Path | None = None,
    external_authorization: str | Path | None = None,
    historical_r5_check: Callable[[], bool] | None = None,
    historical_r5_1_check: Callable[[], bool] | None = None,
    gate2_root_absent_check: Callable[[], bool] | None = None,
) -> dict[str, Any]:
    """Audit the report without executing, repairing, retrying, or writing."""

    errors: list[str] = []
    report = _load_object(Path(path), errors, "root_cause_report") or {}
    _verify_report_shape(report, errors)
    _verify_repository_evidence(report, repo_root, errors)

    historical_r5_ok = (
        historical_r5_check()
        if historical_r5_check is not None
        else _git_diff_empty(
            repo_root, HISTORICAL_R5_HEAD, "evals/m3/results/forward-r5"
        )
    )
    if not historical_r5_ok:
        _add(errors, "historical_r5_changed")
    historical_r5_1_ok = (
        historical_r5_1_check()
        if historical_r5_1_check is not None
        else _git_diff_empty(
            repo_root, GATE0_HEAD, "evals/m3/results/forward-r5.1-f02"
        )
    )
    if not historical_r5_1_ok:
        _add(errors, "historical_r5_1_f02_changed")
    gate2_root_absent = (
        gate2_root_absent_check()
        if gate2_root_absent_check is not None
        else not (repo_root / "evals/m3/results/forward-r5.2-f02").exists()
    )
    if not gate2_root_absent:
        _add(errors, "r5_2_result_root_present")

    child_path = Path(child_rollout) if child_rollout is not None else None
    source_path = Path(source_rollout) if source_rollout is not None else None
    authorization_path = (
        Path(external_authorization) if external_authorization is not None else None
    )
    if child_path is not None:
        _verify_child_rollout(child_path, report, repo_root, errors)
    if source_path is not None:
        _verify_source_rollout(source_path, report, errors)
    if authorization_path is not None:
        _verify_external_authorization(
            authorization_path, report, child_path, errors
        )

    errors = sorted(set(errors))
    primary = report.get("primary_root_cause")
    state = report.get("gate_state")
    return {
        "status": "root_cause_confirmed" if not errors else "invalid",
        "revision": report.get("revision"),
        "task_id": report.get("task_id"),
        "raw_output_bytes": report.get("raw_output_bytes"),
        "raw_output_sha256": report.get("raw_output_sha256"),
        "content_classification": report.get("content_classification"),
        "model_visible_authorization": report.get("model_visible_authorization"),
        "primary_root_cause": (
            primary.get("code") if isinstance(primary, dict) else None
        ),
        "fresh_execution_authorized": (
            state.get("new_fresh_run_authorized") if isinstance(state, dict) else None
        ),
        "fresh_execution": (
            state.get("fresh_execution") if isinstance(state, dict) else None
        ),
        "gate2_status": state.get("gate2") if isinstance(state, dict) else None,
        "historical_r5_unchanged": historical_r5_ok,
        "historical_r5_1_f02_unchanged": historical_r5_1_ok,
        "r5_2_result_root_absent": gate2_root_absent,
        "child_rollout_checked": child_path is not None,
        "source_rollout_checked": source_path is not None,
        "external_authorization_checked": authorization_path is not None,
        "errors": errors,
        "side_effects": [],
        "does_not_prove": [
            "r5.1-f02 acceptance or repair.",
            "Authorization or execution of r5.2-f02.",
            "Cross-revision aggregate acceptance.",
            "M3 closure or M4 start.",
        ],
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", nargs="?", default=str(REPORT))
    parser.add_argument("--child-rollout")
    parser.add_argument("--source-rollout")
    parser.add_argument("--external-authorization")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(sys.argv[1:] if argv is None else argv)
    result = audit_report(
        args.report,
        child_rollout=args.child_rollout,
        source_rollout=args.source_rollout,
        external_authorization=args.external_authorization,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0 if result["status"] == "root_cause_confirmed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
