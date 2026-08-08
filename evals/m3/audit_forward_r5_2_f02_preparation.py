#!/usr/bin/env python3
"""Read-only audit of the r5.2-f02 Gate 2 protocol preparation."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from r5_2_f02_protocol import (
    AUTHORIZATION_RECEIPT_KEYS,
    CASE_ID,
    RAW_OBSERVATION_KEYS,
    REVISION,
    UTF8_BOM_POLICY,
    lint_execution_prompt,
    process_synthetic_final,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
PREPARATION_BASE_HEAD = "263af3df0d8c075d4cdd9835eabe0708dc4f4163"
R5_EVIDENCE_HEAD = "1b696bce53ee0a11163bfe4f91a9a49ab3af6f49"
R5_1_EVIDENCE_HEAD = "fb5eec44bbf86446cf12bda2bddc76fcb07a7e69"
SCHEMA_VERSION = "m3.1-forward-r5.2-f02-preparation-v1"
INPUT_ROOT = REPO_ROOT / "evals" / "m3" / "forward-inputs-r5.2-f02"
RESULT_ROOT = REPO_ROOT / "evals" / "m3" / "results" / "forward-r5.2-f02"
AUTHORIZATION_INSTANCE = INPUT_ROOT / "execution-authorization.json"
R5_RESULT_RELATIVE = "evals/m3/results/forward-r5"
R5_1_RESULT_RELATIVE = "evals/m3/results/forward-r5.1-f02"
COUNTER_KEYS = {"tasks", "finalizations", "composer", "validator", "retry"}
CONDITION_FIELDS = ["criterion_type", "metric_id", "operator", "value", "unit"]
EXPECTED_REGRESSION_CASES = {
    "valid_complete_object",
    "markdown_fenced_object",
    "leading_prose_object",
    "truncated_object",
    "utf8_bom_object",
    "duplicate_keys",
    "empty_output",
    "authorization_refusal_prose",
    "valid_json_schema_rejection",
}
EXPECTED_ARTIFACT_PATHS = {
    "prompt": "evals/m3/forward-inputs-r5.2-f02/m3-f02.prompt.txt",
    "input_binding": "evals/m3/forward-inputs-r5.2-f02/m3-f02.input-binding.json",
    "model_output_contract": (
        "evals/m3/forward-inputs-r5.2-f02/m3-model-output-contract.schema.json"
    ),
    "authorization_receipt_schema": (
        "evals/m3/forward-inputs-r5.2-f02/"
        "m3-f02.authorization-receipt.schema.json"
    ),
    "raw_response_observation_schema": (
        "evals/m3/forward-inputs-r5.2-f02/"
        "m3-f02.raw-response-observation.schema.json"
    ),
    "output_mode": "evals/m3/forward-inputs-r5.2-f02/m3-f02.output-mode.json",
    "protocol_regression_cases": (
        "evals/m3/forward-inputs-r5.2-f02/protocol-regression-cases.json"
    ),
    "protocol_module": "evals/m3/r5_2_f02_protocol.py",
}


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return sha256(canonical_bytes(value))


def _add(errors: list[str], code: str) -> None:
    if code not in errors:
        errors.append(code)


def _load_json(path: Path, code: str, errors: list[str]) -> dict[str, Any] | None:
    try:
        raw = path.read_bytes()
        if raw.startswith(b"\xef\xbb\xbf"):
            raise ValueError("utf8_bom_forbidden")
        value = json.loads(raw.decode("utf-8", errors="strict"))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
        _add(errors, f"{code}_invalid_json")
        return None
    if not isinstance(value, dict):
        _add(errors, f"{code}_object_required")
        return None
    return value


def _safe_file(relative: object, code: str, errors: list[str]) -> Path | None:
    if not isinstance(relative, str) or not relative:
        _add(errors, f"{code}_path_invalid")
        return None
    candidate = (REPO_ROOT / relative).resolve()
    try:
        candidate.relative_to(REPO_ROOT.resolve())
    except ValueError:
        _add(errors, f"{code}_outside_repository")
        return None
    if not candidate.is_file() or candidate.is_symlink():
        _add(errors, f"{code}_missing")
        return None
    return candidate


def _bound_artifact(
    artifacts: object,
    key: str,
    errors: list[str],
    *,
    json_required: bool,
) -> tuple[Path | None, dict[str, Any] | None]:
    if not isinstance(artifacts, dict):
        _add(errors, "manifest_artifacts_invalid")
        return None, None
    reference = artifacts.get(key)
    if not isinstance(reference, dict):
        _add(errors, f"{key}_reference_invalid")
        return None, None
    if reference.get("path") != EXPECTED_ARTIFACT_PATHS[key]:
        _add(errors, f"{key}_path_not_canonical")
    path = _safe_file(reference.get("path"), key, errors)
    if path is None:
        return None, None
    try:
        raw = path.read_bytes()
    except OSError:
        _add(errors, f"{key}_unreadable")
        return None, None
    if reference.get("raw_sha256") != sha256(raw):
        _add(errors, f"{key}_raw_sha256_mismatch")
    if not json_required:
        return path, None
    value = _load_json(path, key, errors)
    if value is not None and reference.get("canonical_sha256") != canonical_sha256(value):
        _add(errors, f"{key}_canonical_sha256_mismatch")
    return path, value


def _git_object(head: str, relative: str) -> tuple[str, bytes] | None:
    try:
        oid = subprocess.run(
            ["git", "rev-parse", f"{head}:{relative}"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        raw = subprocess.run(
            ["git", "show", f"{head}:{relative}"],
            cwd=REPO_ROOT,
            capture_output=True,
            check=False,
        )
    except OSError:
        return None
    if oid.returncode != 0 or raw.returncode != 0:
        return None
    return oid.stdout.strip(), raw.stdout


def _verify_git_reference(
    reference: object,
    *,
    head: str,
    code: str,
    errors: list[str],
    raw_field: str = "raw_sha256",
    json_required: bool = True,
) -> dict[str, Any] | None:
    if not isinstance(reference, dict):
        _add(errors, f"{code}_reference_invalid")
        return None
    relative = reference.get("path")
    if not isinstance(relative, str):
        _add(errors, f"{code}_path_invalid")
        return None
    historical = _git_object(head, relative)
    if historical is None:
        _add(errors, f"{code}_historical_blob_missing")
        return None
    oid, raw = historical
    if reference.get("git_blob_oid") != oid:
        _add(errors, f"{code}_git_blob_oid_mismatch")
    if reference.get(raw_field) != sha256(raw):
        _add(errors, f"{code}_{raw_field}_mismatch")
    if not json_required:
        return None
    try:
        value = json.loads(raw.decode("utf-8", errors="strict"))
    except (UnicodeError, json.JSONDecodeError):
        _add(errors, f"{code}_historical_json_invalid")
        return None
    return value if isinstance(value, dict) else None


def _check_input_binding(value: dict[str, Any], errors: list[str]) -> None:
    if value.get("schema_version") != "m3.1-forward-r5.2-f02-input-binding-v1":
        _add(errors, "input_binding_schema_invalid")
    if value.get("revision") != REVISION or value.get("case_id") != CASE_ID:
        _add(errors, "input_binding_identity_invalid")
    if value.get("preparation_base_head") != PREPARATION_BASE_HEAD:
        _add(errors, "input_binding_preparation_head_drift")
    if value.get("historical_evidence_heads") != {
        "forward_r5": R5_EVIDENCE_HEAD,
        "forward_r5_1_f02": R5_1_EVIDENCE_HEAD,
    }:
        _add(errors, "input_binding_historical_heads_invalid")

    source_ref = value.get("source_input")
    source = _verify_git_reference(
        source_ref,
        head=R5_EVIDENCE_HEAD,
        code="source_input",
        errors=errors,
    )
    if isinstance(source_ref, dict) and isinstance(source, dict):
        if source_ref.get("canonical_sha256") != canonical_sha256(source):
            _add(errors, "source_input_canonical_sha256_mismatch")
        route = source.get("route_output")
        authority = value.get("route_condition_authority")
        if not isinstance(route, dict) or not isinstance(authority, dict):
            _add(errors, "route_condition_authority_invalid")
        else:
            projection = {
                "stop_conditions": route.get("stop_conditions"),
                "pivot_conditions": route.get("pivot_conditions"),
            }
            if authority.get("source_pointer") != "route_output":
                _add(errors, "route_condition_authority_pointer_invalid")
            if authority.get("condition_fields") != CONDITION_FIELDS:
                _add(errors, "route_condition_authority_fields_invalid")
            if authority.get("stop_condition_count") != len(
                projection.get("stop_conditions") or []
            ):
                _add(errors, "route_stop_condition_count_mismatch")
            if authority.get("pivot_condition_count") != len(
                projection.get("pivot_conditions") or []
            ):
                _add(errors, "route_pivot_condition_count_mismatch")
            if authority.get("canonical_sha256") != canonical_sha256(projection):
                _add(errors, "route_condition_authority_sha256_mismatch")

    for key, required_status in (("m2_validation", "valid"), ("eligibility", "eligible")):
        reference = value.get(key)
        receipt = _verify_git_reference(
            reference,
            head=R5_EVIDENCE_HEAD,
            code=key,
            errors=errors,
        )
        if not isinstance(reference, dict) or reference.get("required_status") != required_status:
            _add(errors, f"{key}_required_status_invalid")
        if not isinstance(receipt, dict) or receipt.get("status") != required_status:
            _add(errors, f"{key}_status_invalid")

    report_ref = value.get("root_cause_report")
    report_head = report_ref.get("source_head") if isinstance(report_ref, dict) else ""
    report = _verify_git_reference(
        report_ref,
        head=report_head,
        code="root_cause_report",
        errors=errors,
    )
    if not isinstance(report_ref, dict) or report_head != "86a24a4d1895a565ce54ce087627e32ebbb4c30f":
        _add(errors, "root_cause_report_source_head_invalid")
    if not isinstance(report, dict):
        _add(errors, "root_cause_report_invalid")
    else:
        if report.get("report_status") != report_ref.get("required_status"):
            _add(errors, "root_cause_report_status_invalid")
        if report.get("primary_root_cause", {}).get("code") != report_ref.get(
            "required_primary_code"
        ):
            _add(errors, "root_cause_primary_code_invalid")

    tasks = value.get("historical_failed_tasks")
    expected_tasks = [
        ("r5", "019fd687-5575-7143-8cf3-1ab3069611f5", R5_RESULT_RELATIVE),
        ("r5.1-f02", "019fdb7c-1728-7a92-b6cf-b0eb631a18b8", R5_1_RESULT_RELATIVE),
    ]
    if not isinstance(tasks, list) or len(tasks) != 2:
        _add(errors, "historical_failed_tasks_invalid")
    else:
        for task, expected in zip(tasks, expected_tasks, strict=True):
            if (
                not isinstance(task, dict)
                or (task.get("revision"), task.get("task_id"), task.get("result_root"))
                != expected
                or task.get("retry_forbidden") is not True
            ):
                _add(errors, f"historical_failed_task_invalid:{expected[0]}")
        terminal = tasks[1] if isinstance(tasks[1], dict) else {}
        _verify_git_reference(
            terminal.get("terminal_manifest"),
            head=R5_1_EVIDENCE_HEAD,
            code="historical_terminal_manifest",
            errors=errors,
        )
        raw_final = terminal.get("raw_model_final")
        _verify_git_reference(
            raw_final,
            head=R5_1_EVIDENCE_HEAD,
            code="historical_raw_model_final",
            errors=errors,
            json_required=False,
        )
        if not isinstance(raw_final, dict) or raw_final.get("byte_length") != 216:
            _add(errors, "historical_raw_model_final_length_invalid")

    separation = value.get("authorization_context_separation")
    if (
        not isinstance(separation, dict)
        or separation.get("gate_2_execution_authorized") is not False
        or set(separation)
        != {
            "frozen_repository_prompt",
            "model_visible_execution_context",
            "external_process_authorization",
            "gate_2_execution_authorized",
        }
    ):
        _add(errors, "authorization_context_separation_invalid")


def _check_contract(value: dict[str, Any], errors: list[str]) -> None:
    if value.get("$id") != "m3.1-forward-r5.2-f02-model-output-contract-v1":
        _add(errors, "model_output_contract_identity_invalid")
    if value.get("allOf") != [
        {"$ref": "../forward-inputs-r5/m3-model-output-contract.schema.json"}
    ]:
        _add(errors, "model_output_contract_base_ref_invalid")
    boundary = value.get("x-output-boundary")
    expected_boundary = {
        "encoding": "UTF-8",
        "utf8_bom": UTF8_BOM_POLICY,
        "first_non_whitespace_byte": "{",
        "last_non_whitespace_byte": "}",
        "exactly_one_json_object": True,
        "markdown_fences_allowed": False,
        "leading_or_trailing_prose_allowed": False,
        "comments_allowed": False,
        "duplicate_object_keys_allowed": False,
        "non_finite_numbers_allowed": False,
        "automatic_repair_allowed": False,
    }
    if boundary != expected_boundary:
        _add(errors, "model_output_boundary_invalid")
    authority = value.get("x-authority-inheritance")
    if not isinstance(authority, dict) or authority.get("condition_fields") != CONDITION_FIELDS:
        _add(errors, "model_output_authority_invalid")
    base = value.get("x-base-contract-binding")
    _verify_git_reference(
        base,
        head=R5_EVIDENCE_HEAD,
        code="base_model_output_contract",
        errors=errors,
        raw_field="git_blob_sha256",
    )
    request = value.get("x-request-constraint")
    if not isinstance(request, dict) or request != {
        "selected_mode": "strict_text_json_fail_closed",
        "native_structured_output_model_support": True,
        "current_execution_surface_exposes_schema_parameter": False,
        "capability_recheck_required_before_gate_3": True,
        "request_level_schema_config_sha256": None,
    }:
        _add(errors, "model_output_request_constraint_invalid")


def _check_authorization_schema(
    value: dict[str, Any],
    artifacts: dict[str, Any],
    errors: list[str],
) -> None:
    if value.get("type") != "object" or value.get("additionalProperties") is not False:
        _add(errors, "authorization_receipt_schema_not_closed")
    if set(value.get("required", [])) != AUTHORIZATION_RECEIPT_KEYS:
        _add(errors, "authorization_receipt_required_fields_invalid")
    properties = value.get("properties")
    if not isinstance(properties, dict) or set(properties) != AUTHORIZATION_RECEIPT_KEYS:
        _add(errors, "authorization_receipt_properties_invalid")
        return
    expected_prompt = artifacts.get("prompt", {}).get("raw_sha256")
    expected_input = artifacts.get("input_binding", {}).get("raw_sha256")
    if properties.get("revision") != {"const": REVISION}:
        _add(errors, "authorization_receipt_revision_const_invalid")
    if properties.get("authorized") != {"const": True}:
        _add(errors, "authorization_receipt_authorized_const_invalid")
    if properties.get("prompt_sha256") != {"const": expected_prompt}:
        _add(errors, "authorization_receipt_prompt_hash_const_invalid")
    if properties.get("input_binding_sha256") != {"const": expected_input}:
        _add(errors, "authorization_receipt_input_hash_const_invalid")
    if properties.get("authorized_task_count") != {"const": 1}:
        _add(errors, "authorization_receipt_task_count_const_invalid")
    if value.get("x-gate-2-instance-present") is not False:
        _add(errors, "authorization_receipt_gate_2_state_invalid")


def _check_observation_schema(value: dict[str, Any], errors: list[str]) -> None:
    if value.get("type") != "object" or value.get("additionalProperties") is not False:
        _add(errors, "raw_observation_schema_not_closed")
    if set(value.get("required", [])) != RAW_OBSERVATION_KEYS:
        _add(errors, "raw_observation_required_fields_invalid")
    properties = value.get("properties")
    if not isinstance(properties, dict) or set(properties) != RAW_OBSERVATION_KEYS:
        _add(errors, "raw_observation_properties_invalid")
    if value.get("x-repair-allowed") is not False:
        _add(errors, "raw_observation_repair_policy_invalid")
    if value.get("x-observation-order") != (
        "persist raw bytes and this observation before parser invocation"
    ):
        _add(errors, "raw_observation_order_invalid")


def _check_output_mode(value: dict[str, Any], errors: list[str]) -> None:
    if value.get("schema_version") != "m3.1-r5.2-f02-output-mode-v1":
        _add(errors, "output_mode_schema_invalid")
    if value.get("revision") != REVISION or value.get("case_id") != CASE_ID:
        _add(errors, "output_mode_identity_invalid")
    model = value.get("model_capability")
    if (
        not isinstance(model, dict)
        or model.get("model") != "gpt-5.6-sol"
        or model.get("native_structured_outputs_supported") is not True
        or not str(model.get("official_model_documentation", "")).startswith(
            "https://developers.openai.com/"
        )
        or not str(model.get("official_structured_outputs_guide", "")).startswith(
            "https://developers.openai.com/"
        )
    ):
        _add(errors, "output_mode_model_capability_invalid")
    surface = value.get("execution_surface")
    if not isinstance(surface, dict):
        _add(errors, "output_mode_surface_invalid")
    else:
        if surface.get("request_fields_observed") != [
            "model",
            "prompt",
            "target",
            "thinking",
            "title",
        ]:
            _add(errors, "output_mode_surface_fields_invalid")
        for field in (
            "response_format_field_exposed",
            "json_schema_field_exposed",
            "provider_request_id_exposed",
            "finish_reason_exposed",
            "token_usage_exposed",
        ):
            if surface.get(field) is not False:
                _add(errors, f"output_mode_surface_field_invalid:{field}")
        if value.get("surface_request_contract_canonical_sha256") != canonical_sha256(
            surface
        ):
            _add(errors, "output_mode_surface_contract_hash_invalid")
    decision = value.get("decision")
    if not isinstance(decision, dict) or decision != {
        "selected_mode": "strict_text_json_fail_closed",
        "structured_output_request_config": None,
        "automatic_repair_allowed": False,
        "capability_recheck_required_before_gate_3": True,
        "surface_change_requires_new_hash": True,
        "direct_api_substitution_authorized": False,
    }:
        _add(errors, "output_mode_decision_invalid")
    observation = value.get("observability_policy")
    if (
        not isinstance(observation, dict)
        or observation.get("preserve_before_parser") is not True
        or observation.get("capture_tool_boundary_final_as_raw_utf8_bytes") is not True
        or observation.get("model_visible_message_hash_includes_authorized_execution_prefix")
        is not True
    ):
        _add(errors, "output_mode_observability_policy_invalid")


def _check_regression_cases(value: dict[str, Any], errors: list[str]) -> None:
    if value.get("revision") != REVISION or value.get("case_id") != CASE_ID:
        _add(errors, "protocol_regression_identity_invalid")
    if value.get("utf8_bom_policy") != UTF8_BOM_POLICY:
        _add(errors, "protocol_regression_bom_policy_invalid")
    if value.get("repair_allowed") is not False:
        _add(errors, "protocol_regression_repair_policy_invalid")
    cases = value.get("cases")
    if (
        not isinstance(cases, list)
        or len(cases) != len(EXPECTED_REGRESSION_CASES)
        or {item.get("case_id") for item in cases if isinstance(item, dict)}
        != EXPECTED_REGRESSION_CASES
    ):
        _add(errors, "protocol_regression_case_set_invalid")
        return
    for case in cases:
        if not isinstance(case, dict):
            _add(errors, "protocol_regression_case_invalid")
            continue
        try:
            raw = (
                bytes.fromhex(case["raw_hex"])
                if "raw_hex" in case
                else case["raw_text"].encode("utf-8")
            )
            validator_errors = case.get("validator_errors", [])
            result = process_synthetic_final(raw, lambda _payload: validator_errors)
        except (KeyError, TypeError, ValueError):
            _add(errors, f"protocol_regression_case_invalid:{case.get('case_id')}")
            continue
        projection = {
            "status": result.get("status"),
            "reason": result.get("reason"),
            "counters": result.get("counters"),
        }
        expected = {
            "status": case.get("expected_status"),
            "reason": case.get("expected_reason"),
            "counters": case.get("expected_counters"),
        }
        if projection != expected:
            _add(errors, f"protocol_regression_outcome_mismatch:{case.get('case_id')}")


def _check_zero_counters(value: object, errors: list[str]) -> dict[str, int]:
    counters = value if isinstance(value, dict) else {}
    if set(counters) != COUNTER_KEYS:
        _add(errors, "manifest_counter_keys_invalid")
    result: dict[str, int] = {}
    for key in sorted(COUNTER_KEYS):
        raw = counters.get(key)
        result[key] = raw if isinstance(raw, int) and not isinstance(raw, bool) else -1
        if raw != 0 or isinstance(raw, bool):
            _add(errors, f"manifest_counter_nonzero:{key}")
    return result


def _check_result_root(manifest: dict[str, Any], errors: list[str]) -> int:
    try:
        declared = (REPO_ROOT / manifest.get("result_root", "")).resolve()
    except (AttributeError, TypeError, ValueError):
        declared = None
    if declared != RESULT_ROOT.resolve():
        _add(errors, "result_root_not_canonical")
    if manifest.get("result_root_allowlist") != [".gitkeep"]:
        _add(errors, "result_root_allowlist_invalid")
    if manifest.get("logical_result_artifact_count") != 0:
        _add(errors, "manifest_result_artifact_count_nonzero")
    if not RESULT_ROOT.is_dir() or RESULT_ROOT.is_symlink():
        _add(errors, "result_root_missing")
        return 0
    entries = list(RESULT_ROOT.iterdir())
    marker = RESULT_ROOT / ".gitkeep"
    if not marker.is_file() or marker.is_symlink() or marker.read_bytes() != b"":
        _add(errors, "result_root_marker_invalid")
    artifacts = [path for path in entries if path.name != ".gitkeep"]
    if artifacts:
        _add(errors, "result_root_not_logically_empty")
    return len(artifacts)


def _authorization_instance_absent() -> bool:
    return not AUTHORIZATION_INSTANCE.exists()


def _historical_tree_clean(head: str, relative: str) -> bool:
    try:
        baseline = subprocess.run(
            ["git", "ls-tree", "-r", head, "--", relative],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        current = subprocess.run(
            ["git", "ls-tree", "-r", "HEAD", "--", relative],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        unstaged = subprocess.run(
            ["git", "diff", "--quiet", "--", relative],
            cwd=REPO_ROOT,
            check=False,
        )
        staged = subprocess.run(
            ["git", "diff", "--cached", "--quiet", "--", relative],
            cwd=REPO_ROOT,
            check=False,
        )
    except OSError:
        return False
    if (
        baseline.returncode != 0
        or current.returncode != 0
        or unstaged.returncode != 0
        or staged.returncode != 0
    ):
        return False
    if baseline.stdout != current.stdout:
        return False
    expected = {
        line.split("\t", 1)[1]
        for line in baseline.stdout.splitlines()
        if "\t" in line
    }
    root = REPO_ROOT / relative
    if not root.is_dir() or root.is_symlink():
        return False
    actual = {
        path.relative_to(REPO_ROOT).as_posix()
        for path in root.rglob("*")
        if path.is_file()
    }
    if actual != expected:
        return False
    for item in actual:
        if (REPO_ROOT / item).is_symlink():
            return False
    return True


def audit_preparation(manifest_path: str | Path) -> dict[str, Any]:
    """Audit frozen files and history without writing or launching anything."""

    errors: list[str] = []
    manifest = _load_json(Path(manifest_path), "manifest", errors)
    default_counters = {key: 0 for key in sorted(COUNTER_KEYS)}
    if manifest is None:
        return {
            "status": "invalid",
            "revision": REVISION,
            "case_id": CASE_ID,
            "new_fresh_run_authorized": False,
            "fresh_execution": "NOT_RUN",
            "logical_result_artifact_count": 0,
            "counters": default_counters,
            "prompt_lint_errors": [],
            "historical_r5_diff": "unverified",
            "historical_r5_1_f02_diff": "unverified",
            "errors": sorted(errors),
        }

    if manifest.get("schema_version") != SCHEMA_VERSION:
        _add(errors, "manifest_schema_invalid")
    if manifest.get("status") != "protocol_prepared_awaiting_gate_3_authorization":
        _add(errors, "manifest_status_invalid")
    if manifest.get("revision") != REVISION or manifest.get("case_id") != CASE_ID:
        _add(errors, "manifest_identity_invalid")
    if manifest.get("based_on_head") != PREPARATION_BASE_HEAD:
        _add(errors, "manifest_base_head_drift")
    if manifest.get("m3_status") != "IN_PROGRESS" or manifest.get("m4_status") != "NOT_STARTED":
        _add(errors, "milestone_status_drift")
    if manifest.get("preparation_authorized") is not True:
        _add(errors, "preparation_authorization_missing")
    if manifest.get("new_fresh_run_authorized") is not False:
        _add(errors, "fresh_run_authorization_must_be_false")
    if manifest.get("execution_authorization_instance_present") is not False:
        _add(errors, "manifest_execution_authorization_state_invalid")
    if manifest.get("reserved_task_id") is not None:
        _add(errors, "reserved_task_id_must_be_null")

    counters = _check_zero_counters(manifest.get("counters"), errors)
    artifact_count = _check_result_root(manifest, errors)
    if not _authorization_instance_absent():
        _add(errors, "execution_authorization_instance_present")

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict) or set(artifacts) != set(EXPECTED_ARTIFACT_PATHS):
        _add(errors, "manifest_artifact_set_invalid")
        artifacts = artifacts if isinstance(artifacts, dict) else {}

    prompt_path, _ = _bound_artifact(
        artifacts, "prompt", errors, json_required=False
    )
    _, input_binding = _bound_artifact(
        artifacts, "input_binding", errors, json_required=True
    )
    _, contract = _bound_artifact(
        artifacts, "model_output_contract", errors, json_required=True
    )
    _, authorization_schema = _bound_artifact(
        artifacts, "authorization_receipt_schema", errors, json_required=True
    )
    _, observation_schema = _bound_artifact(
        artifacts, "raw_response_observation_schema", errors, json_required=True
    )
    _, output_mode = _bound_artifact(
        artifacts, "output_mode", errors, json_required=True
    )
    _, regression_cases = _bound_artifact(
        artifacts, "protocol_regression_cases", errors, json_required=True
    )
    _bound_artifact(artifacts, "protocol_module", errors, json_required=False)

    prompt_lint_errors: list[str] = []
    if prompt_path is not None:
        try:
            prompt = prompt_path.read_text(encoding="utf-8", errors="strict")
        except (OSError, UnicodeError):
            _add(errors, "prompt_invalid_utf8")
        else:
            prompt_lint_errors = lint_execution_prompt(prompt)
            for code in prompt_lint_errors:
                _add(errors, f"prompt_lint:{code}")
    if input_binding is not None:
        _check_input_binding(input_binding, errors)
    if contract is not None:
        _check_contract(contract, errors)
    if authorization_schema is not None:
        _check_authorization_schema(authorization_schema, artifacts, errors)
    if observation_schema is not None:
        _check_observation_schema(observation_schema, errors)
    if output_mode is not None:
        _check_output_mode(output_mode, errors)
    if regression_cases is not None:
        _check_regression_cases(regression_cases, errors)

    protocol = manifest.get("authorization_protocol")
    if (
        not isinstance(protocol, dict)
        or protocol.get("receipt_instance_must_be_absent_in_gate_2") is not True
        or protocol.get("authorized_task_count_after_gate_3_receipt") != 1
        or protocol.get("prompt_hash_includes_model_visible_authorization") is not True
        or protocol.get("dispatcher_must_validate_before_task_creation") is not True
    ):
        _add(errors, "manifest_authorization_protocol_invalid")
    output_protocol = manifest.get("output_protocol")
    if (
        not isinstance(output_protocol, dict)
        or output_protocol.get("selected_mode") != "strict_text_json_fail_closed"
        or output_protocol.get("structured_output_request_config") is not None
        or output_protocol.get("capability_recheck_required_before_gate_3") is not True
        or output_protocol.get("automatic_repair_allowed") is not False
        or output_protocol.get("same_task_retry_allowed") is not False
    ):
        _add(errors, "manifest_output_protocol_invalid")

    r5_clean = _historical_tree_clean(R5_EVIDENCE_HEAD, R5_RESULT_RELATIVE)
    r5_1_clean = _historical_tree_clean(R5_1_EVIDENCE_HEAD, R5_1_RESULT_RELATIVE)
    if not r5_clean:
        _add(errors, "immutable_forward_r5_changed")
    if not r5_1_clean:
        _add(errors, "immutable_forward_r5_1_f02_changed")

    return {
        "status": "gate_2_preparation_valid" if not errors else "invalid",
        "revision": manifest.get("revision"),
        "case_id": manifest.get("case_id"),
        "new_fresh_run_authorized": manifest.get("new_fresh_run_authorized"),
        "fresh_execution": "NOT_RUN",
        "logical_result_artifact_count": artifact_count,
        "counters": counters,
        "selected_output_mode": (
            output_mode.get("decision", {}).get("selected_mode")
            if isinstance(output_mode, dict)
            else None
        ),
        "prompt_lint_errors": prompt_lint_errors,
        "historical_r5_diff": "empty" if r5_clean else "changed",
        "historical_r5_1_f02_diff": "empty" if r5_1_clean else "changed",
        "errors": sorted(errors),
        "does_not_prove": [
            "Gate 2 preparation validity is not a Gate 3 execution authorization.",
            "No task, model output, finalization, composition, validation, acceptance, aggregation, closure, or M4 work occurred.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) > 1:
        return 2
    manifest = (
        Path(arguments[0]) if arguments else INPUT_ROOT / "manifest.json"
    )
    result = audit_preparation(manifest)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0 if result["status"] == "gate_2_preparation_valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
