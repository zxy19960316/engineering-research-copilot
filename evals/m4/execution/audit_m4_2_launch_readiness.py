#!/usr/bin/env python3
"""Read-only Gate A launch-readiness audit for M4.2."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence

import audit_m4_2 as protocol
import build_m4_2_launch_claim as claim_builder
import record_m4_2_execution_evidence as recorder


SCHEMA_RELATIVES = (
    protocol.LAUNCH_SCHEMA_RELATIVE,
    protocol.DISPATCH_SCHEMA_RELATIVE,
    protocol.RESPONSE_ATTESTATION_SCHEMA_RELATIVE,
    protocol.TERMINAL_SCHEMA_RELATIVE,
)


def _add(errors: list[str], code: str) -> None:
    if code not in errors:
        errors.append(code)


def _git_identity(repo_root: Path) -> tuple[str | None, str | None]:
    head = protocol._git_text(repo_root, "rev-parse", "HEAD")
    tree = protocol._git_text(repo_root, "rev-parse", "HEAD^{tree}")
    return head, tree


def _source_contract(errors: list[str]) -> str:
    sources = {
        "claim_builder": Path(claim_builder.__file__).read_text(encoding="utf-8"),
        "recorder": Path(recorder.__file__).read_text(encoding="utf-8"),
    }
    forbidden = (
        "os.replace",
        "os.remove",
        ".unlink(",
        "rmtree(",
        "shutil.rmtree",
    )
    for label, source in sources.items():
        for marker in forbidden:
            if marker in source:
                _add(errors, f"{label}_destructive_primitive:{marker}")
    coordinator_errors: list[str] = []
    recorder_source = sources["recorder"]
    for marker in (
        "--check",
        "--next-action",
        "--record-dispatch",
        "--record-final",
        "--record-terminal",
        "record_dispatch(",
        "record_final(",
        "record_terminal(",
        "Path.read_bytes",
    ):
        if marker not in recorder_source:
            code = f"recorder_production_cli_marker_missing:{marker}"
            _add(errors, code)
            _add(coordinator_errors, code)
    for marker in forbidden:
        if marker in recorder_source:
            _add(coordinator_errors, f"recorder_destructive_primitive:{marker}")
    if "os.O_EXCL" not in Path(protocol.__file__).read_text(encoding="utf-8"):
        _add(errors, "exclusive_create_primitive_missing")
    claim_source = sources["claim_builder"]
    if "audit_m4_2_authorization" in claim_source:
        _add(errors, "preclaim_authorization_auditor_imported_postclaim")
    if "post-claim execution auditor" not in claim_source:
        _add(errors, "postclaim_execution_auditor_guard_missing")
    return "PRODUCTION_CLI_FROZEN" if not coordinator_errors else "INVALID"


def audit_launch_readiness(
    repo_root: Path = protocol.REPO_ROOT,
    *,
    verify_git: bool = True,
    enforce_frozen_hashes: bool = True,
    enforce_exact_changed_paths: bool = True,
    authorization_path: Path | None = None,
    control_path: Path | None = None,
    claim_path: Path | None = None,
    observations_base: Path | None = None,
    results_base: Path | None = None,
    terminal_path: Path | None = None,
    results_manifest_path: Path | None = None,
    m5_path: Path | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    state = protocol.audit_execution(
        repo_root,
        verify_git=verify_git,
        enforce_frozen_hashes=enforce_frozen_hashes,
        authorization_path=authorization_path,
        control_path=control_path,
        claim_path=claim_path,
        observations_base=observations_base,
        results_base=results_base,
        terminal_path=terminal_path,
        results_manifest_path=results_manifest_path,
        m5_path=m5_path,
    )
    if state["status"] != "READY_UNCLAIMED":
        _add(errors, "execution_audit_not_ready_unclaimed")
    for code in state["errors"]:
        _add(errors, f"execution:{code}")
    claim_check = claim_builder.check_claim_readiness(
        repo_root,
        verify_git=verify_git,
        enforce_frozen_hashes=enforce_frozen_hashes,
        authorization_path=authorization_path,
        control_path=control_path,
        claim_path=claim_path,
        observations_base=observations_base,
        results_base=results_base,
        terminal_path=terminal_path,
        results_manifest_path=results_manifest_path,
        m5_path=m5_path,
    )
    if claim_check["status"] != "READY_TO_CONSUME":
        _add(errors, "claim_builder_check_failed")
    recorder_check = recorder.check_recorder(
        repo_root,
        verify_git=verify_git,
        enforce_frozen_hashes=enforce_frozen_hashes,
        authorization_path=authorization_path,
        control_path=control_path,
        claim_path=claim_path,
        observations_base=observations_base,
        results_base=results_base,
        terminal_path=terminal_path,
        results_manifest_path=results_manifest_path,
        m5_path=m5_path,
    )
    if recorder_check["status"] != "READY_UNCLAIMED":
        _add(errors, "recorder_check_failed")
    for relative in SCHEMA_RELATIVES:
        try:
            schema = protocol._load_schema(repo_root, relative)
        except (OSError, protocol.ContractError):
            _add(errors, f"schema_unavailable:{relative.as_posix()}")
            continue
        if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            _add(errors, f"schema_draft_invalid:{relative.as_posix()}")
        if schema.get("x-real-instance-allowed-in-gate-a") is not False:
            _add(errors, f"schema_gate_a_instance_policy_invalid:{relative.as_posix()}")
        if not protocol.recursively_closed_schema(schema):
            _add(errors, f"schema_not_recursively_closed:{relative.as_posix()}")
    coordinator_check = _source_contract(errors)

    authorization, control, authorization_raw, control_raw, tasks, source_errors = (
        protocol.load_frozen_inputs(
            repo_root,
            policy=protocol.FrozenPolicy(
                enforce_raw_hashes=enforce_frozen_hashes,
                verify_git=verify_git,
            ),
            authorization_path=authorization_path,
            control_path=control_path,
        )
    )
    for code in source_errors:
        _add(errors, f"source:{code}")
    head, tree = _git_identity(repo_root) if verify_git else ("1" * 40, "2" * 40)
    writer_check = "INVALID"
    prompt_check = "INVALID"
    if head is None or tree is None:
        _add(errors, "candidate_git_identity_unavailable")
    elif len(tasks) == 60:
        gate_a = claim_builder.GateAAcceptance(
            candidate_head=head,
            candidate_tree=tree,
            push_run_id=1,
            pr_run_id=1,
        )
        try:
            first = claim_builder.build_claim(
                repo_root,
                gate_a=gate_a,
                claimed_at_utc="2000-01-01T00:00:00Z",
                verify_git=verify_git,
                enforce_frozen_hashes=enforce_frozen_hashes,
                authorization_path=authorization_path,
                control_path=control_path,
            )
            second = claim_builder.build_claim(
                repo_root,
                gate_a=gate_a,
                claimed_at_utc="2000-01-01T00:00:00Z",
                verify_git=verify_git,
                enforce_frozen_hashes=enforce_frozen_hashes,
                authorization_path=authorization_path,
                control_path=control_path,
            )
        except protocol.ContractError as error:
            _add(errors, f"claim_template:{error.code}")
        else:
            if protocol.json_bytes(first) == protocol.json_bytes(second):
                writer_check = "DETERMINISTIC_CHECK_ONLY"
            else:
                _add(errors, "claim_template_not_byte_deterministic")
            task_claims = first.get("task_claims")
            if isinstance(task_claims, list) and len(task_claims) == 60:
                prompt_errors: list[str] = []
                request_hashes: set[str] = set()
                for task, task_claim in zip(tasks, task_claims, strict=True):
                    try:
                        request = protocol.expected_create_thread_arguments(
                            repo_root, task, task_claim
                        )
                    except protocol.ContractError as error:
                        prompt_errors.append(error.code)
                        continue
                    if set(request) != {"prompt", "target", "title"}:
                        prompt_errors.append("request_keys_invalid")
                    if "model" in request or "thinking" in request:
                        prompt_errors.append("request_override_present")
                    request_hashes.add(protocol.canonical_sha256(request))
                if not prompt_errors and len(request_hashes) == 60:
                    prompt_check = "60_DETERMINISTIC_ISOLATED_REQUESTS"
                else:
                    for code in prompt_errors:
                        _add(errors, f"prompt:{code}")
                    if len(request_hashes) != 60:
                        _add(errors, "request_envelope_hash_duplicate")
    changed_paths: list[str] = []
    if enforce_exact_changed_paths:
        changed_paths, diff_errors = protocol.gate_a_changed_paths(repo_root)
        for code in diff_errors:
            _add(errors, code)
        if set(changed_paths) != set(protocol.GATE_A_ALLOWED_PATHS):
            missing = sorted(set(protocol.GATE_A_ALLOWED_PATHS) - set(changed_paths))
            extra = sorted(set(changed_paths) - set(protocol.GATE_A_ALLOWED_PATHS))
            if missing:
                _add(errors, "gate_a_changed_paths_missing:" + ",".join(missing))
            if extra:
                _add(errors, "gate_a_changed_paths_extra:" + ",".join(extra))
    status = "READY_FOR_ATOMIC_CLAIM" if not errors else "INVALID"
    return {
        "status": status,
        "errors": errors,
        "authorization_audit": state["authorization_audit_status"],
        "execution_audit": state["status"],
        "claim_builder_check": claim_check["status"],
        "recorder_check": recorder_check["status"],
        "writer_check": writer_check,
        "coordinator_check": coordinator_check,
        "prompt_check": prompt_check,
        "token": state["token"],
        "launch_claim": "ABSENT" if not state["launch_claim_present"] else "PRESENT",
        "result_root": "ABSENT" if state["result_root_count"] == 0 else "PRESENT",
        "terminal": "ABSENT" if not state["terminal_present"] else "PRESENT",
        "tasks": state["tasks"],
        "threads": state["threads"],
        "finalizations": state["finalizations"],
        "retries": state["retries"],
        "repairs": state["repairs"],
        "followups": state["followups"],
        "judge_calls": state["judge_calls"],
        "aggregation_calls": state["aggregation_calls"],
        "request_binding_aggregate_sha256": state[
            "request_binding_aggregate_sha256"
        ],
        "candidate_head": head,
        "candidate_tree": tree,
        "changed_paths": changed_paths,
        "later_gates_authorized": False,
        "gate_b_authorized": False,
        "writes": 0,
    }


def _compact(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--skip-exact-change-set",
        action="store_true",
        help="Diagnostic only; CI must not use this option.",
    )
    args = parser.parse_args(argv)
    result = audit_launch_readiness(
        protocol.REPO_ROOT,
        enforce_exact_changed_paths=not args.skip_exact_change_set,
    )
    print(_compact(result))
    return 0 if result["status"] == "READY_FOR_ATOMIC_CLAIM" else 1


if __name__ == "__main__":
    raise SystemExit(main())
