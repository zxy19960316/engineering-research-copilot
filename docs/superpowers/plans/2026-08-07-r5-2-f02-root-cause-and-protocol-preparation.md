# r5.2-f02 Root-Cause and Protocol Preparation Implementation Plan

> **For agentic workers:** Execute this plan inline on the named branch. Do not delegate, create a task, send a thread message, or enter Gate 2. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a read-only, hash-bound diagnosis of the consumed r5.1-f02 finalization and prepare protocol requirements for r5.2-f02 without launching a model or creating the r5.2 result root.

**Architecture:** Bind the frozen repository artifacts to the append-only source/child rollout observations by SHA-256, turn IDs, timestamps, message identities, and output identities. A small auditor validates the closed report, reproduces repository identities, and optionally verifies local rollout prefixes; focused tests mutate temporary report copies. Keep future execution prompt, authorization receipt, result root, dispatcher changes, and structured-output configuration out of this gate.

**Tech Stack:** Python 3.13-compatible standard library, JSONL, SHA-256, Git blob plumbing, `unittest`, and existing M3 composer parsing semantics.

## Global Constraints

- Start from exact Gate 0 HEAD `fb5eec44bbf86446cf12bda2bddc76fcb07a7e69` on `codex/m3.1.1-r5.2-f02-root-cause-and-protocol-preparation`.
- Preserve all `evals/m3/results/forward-r5.1-f02/` and `evals/m3/results/forward-r5/` bytes and Git blobs.
- Do not create, fork, continue, message, retry, or otherwise run a Codex task.
- Do not create `evals/m3/results/forward-r5.2-f02/` or any r5.2 execution prompt, authorization receipt, task ID, launch receipt, finalization, composer receipt, or validator receipt.
- Perform exactly one explicit offline parser replay over the frozen 216-byte payload and record it as diagnostic evidence only.
- Treat external authorization, the child task's consumed-turn messages, and the frozen repository prompt as distinct evidence objects.
- Keep r5.1-f02 `TERMINAL_NOT_ACCEPTED`, historical r5 `BLOCKED_NOT_ACCEPTED`, M3 `IN_PROGRESS`, aggregate and closure `NOT_RUN`, and M4 `NOT_STARTED`.
- Do not push, create a pull request, merge, or begin Gate 2.

## File Structure

- Create `evals/m3/results/diagnostics-r5.2-f02/root-cause-report.json`: closed machine-readable diagnosis and protocol implications.
- Create `evals/m3/audit_r5_2_f02_root_cause.py`: read-only report/repository/optional-rollout auditor.
- Create `tests/test_audit_m3_r5_2_f02_root_cause.py`: deterministic shape, mutation, parser-observation, and immutability tests.
- Create `evals/m3/results/2026-08-07-m3.1.1-r5.2-f02-root-cause-validation.md`: exact local validation record.
- Modify `STATUS.md`: record Gate 1 root-cause completion without claiming r5.2 readiness or execution.

---

### Task 1: Closed root-cause report contract

**Files:**

- Create: `tests/test_audit_m3_r5_2_f02_root_cause.py`
- Create: `evals/m3/audit_r5_2_f02_root_cause.py`
- Create: `evals/m3/results/diagnostics-r5.2-f02/root-cause-report.json`

**Interfaces:**

- Consumes: frozen terminal manifest/artifacts, authorization/prompt Git blobs, exact Gate 0 HEAD, and hash-only observations from source/child rollout prefixes.
- Produces: `audit_report(path, *, repo_root=REPO_ROOT, child_rollout=None, source_rollout=None, external_authorization=None) -> dict[str, Any]` with `status="root_cause_confirmed"` only when all mandatory bindings and conclusions pass.

- [x] **Step 1: Write red shape and mutation tests**

Require exact top-level fields for revision, task/turn IDs, raw response identity, JSON error, model/platform metadata, the three context layers, hypothesis dispositions, primary root cause, parser replay, protocol implications, immutable evidence, and forbidden actions. Add mutations for raw hash, turn ID, authorization visibility, output-token count, late-turn timing, primary-cause code, historical diff, and accidental Gate 2 authorization.

```python
result = audit.audit_report(audit.REPORT)
self.assertEqual(result["status"], "root_cause_confirmed")
self.assertEqual(result["errors"], [])
self.assertEqual(result["primary_root_cause"], "authorization_not_visible_in_consumed_turn")
self.assertIs(result["fresh_execution_authorized"], False)
```

- [x] **Step 2: Confirm the red test**

Run: `python -X utf8 -m unittest tests.test_audit_m3_r5_2_f02_root_cause -v`

Expected: import failure because the auditor/report do not exist.

- [x] **Step 3: Implement strict report validation**

Use strict UTF-8/no-BOM JSON loading, exact key sets, non-boolean integer checks, lowercase SHA-256 validation, safe repository-relative paths, fixed IDs/HEADs, and closed hypothesis statuses `confirmed`, `ruled_out`, or `unresolved`.

```python
def canonical_sha256(value: Any) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()
```

- [x] **Step 4: Bind repository evidence**

Verify the 216-byte model-final and payload are byte-identical, raw SHA-256 `75b4f9f5f4e2459b2886c0a9654c8cc1bda4015c525869cd154a302a2bc0589a`, Git blob `8c5ed1d1818039600c52e67544b746d34c41a857`, UTF-8 valid, and expected invalid JSON. Verify prompt, authorization, terminal manifest, context, transaction, composer receipt, Gate 0 HEAD, and historical r5 zero-diff bindings.

### Task 2: Hash-bound forensic observations and hypothesis dispositions

**Files:**

- Modify: `evals/m3/results/diagnostics-r5.2-f02/root-cause-report.json`
- Modify: `evals/m3/audit_r5_2_f02_root_cause.py`
- Modify: `tests/test_audit_m3_r5_2_f02_root_cause.py`

**Interfaces:**

- Consumes: source rollout prefix through the consumed finalization, child rollout records for both completed turns, and the original external authorization attachment.
- Produces: canonical `request_envelope_sha256`, `model_visible_messages_sha256`, `observed_context_sha256`, `finalization_sha256`, individual message hashes, prefix hashes/lengths, and an evidence-ranked root-cause conclusion.

- [x] **Step 1: Record the three distinct context layers**

Record separately:

```json
{
  "frozen_repository_prompt": {"path": "...", "raw_sha256": "..."},
  "consumed_turn_model_visible_context": {"turn_id": "...", "messages_sha256": "..."},
  "external_user_authorization": {"present": true, "raw_sha256": "..."}
}
```

The consumed turn must state `authorization_visible=false`; the later turn must state `authorization_visible=true` and `occurred_after_terminal_consumption=true`.

- [x] **Step 2: Perform the single offline parser replay**

Call the existing composer's `_load_object(payload_path, "payload")` once without invoking a model, composer transaction, or validator. Record `payload_invalid_json`, line `1`, column `1`, position/byte offset `0`, UTF-8 valid, replay count `1`, model calls `0`, writes `0`, and retries `0`.

- [x] **Step 3: Dispose hypotheses in the required order**

Record:

1. `model_did_not_see_authorization`: confirmed for the consumed turn.
2. `model_followed_do_not_execute_instruction`: confirmed by exact first-final equality.
3. `output_truncated`: ruled out by completed platform status, exact task-complete equality, coherent terminal prose, and 102 output tokens; keep `finish_reason` itself unresolved because it was not recorded.
4. `wrong_message_field_saved`: ruled out for the consumed turn because wait output, assistant final, task-complete final, model-final, and payload are byte-identical; separately record that a later authorized turn exists but was outside the consumed finalization.
5. `markdown_or_affix_broke_json`: ruled out because the entire consumed output is non-JSON authorization-deferral prose with no JSON object or fence.
6. `composer_path_error`: ruled out by the single offline parser replay at byte offset zero.

- [x] **Step 4: State the primary root cause and protocol implications**

Use primary code `authorization_not_visible_in_consumed_turn`. State that the launcher created an immediately executing task from a frozen prompt containing `future task` and `do not execute`, while the external authorization was not included in that turn; the one-shot consumer then correctly finalized the first completed turn. Record only Gate 2 design requirements: dispatcher preflight must verify authorization before task creation, the model-facing prompt must contain explicit current authorization, and the receipt must bind prompt/input/message hashes and an authorized task count of one.

### Task 3: Validation, status, and independent commits

**Files:**

- Create: `evals/m3/results/2026-08-07-m3.1.1-r5.2-f02-root-cause-validation.md`
- Modify: `STATUS.md`
- Include: `docs/superpowers/plans/2026-08-07-r5-2-f02-root-cause-and-protocol-preparation.md`

**Interfaces:**

- Consumes: committed diagnosis implementation and exact local gate outputs.
- Produces: an auditable Gate 1 completion record while keeping Gate 2 and all execution counters untouched.

- [x] **Step 1: Run focused and full validation**

Run:

```text
python -X utf8 -m py_compile evals/m3/audit_r5_2_f02_root_cause.py
python -X utf8 -m unittest tests.test_audit_m3_r5_2_f02_root_cause -v
python -X utf8 -m unittest discover -s tests -p "test_*.py" -v
python -X utf8 evals/m3/audit_forward_r5_1_f02_terminal.py
python -X utf8 evals/m3/audit_m3_r5_1_ci_state.py
git diff --check
git diff --exit-code 1b696bce53ee0a11163bfe4f91a9a49ab3af6f49 HEAD -- evals/m3/results/forward-r5
git diff --exit-code fb5eec44bbf86446cf12bda2bddc76fcb07a7e69 HEAD -- evals/m3/results/forward-r5.1-f02
```

Expected: all tests/audits pass; both historical evidence diffs are empty.

- [x] **Step 2: Update STATUS without advancing Gate 2**

Add a Gate 1 section stating root cause confirmed, consumed-turn authorization absent, later authorization outside the one-shot window, parser replay diagnostic only, r5.2 result root absent, no fresh task, and Gate 2 `NOT_STARTED`.

- [x] **Step 3: Commit diagnosis implementation**

Stage only the report, auditor, and focused test. Commit:

```text
eval: record r5.1-f02 authorization visibility root cause
```

- [x] **Step 4: Commit plan and validation record**

Stage only the plan, validation record, and STATUS. Commit:

```text
docs: record r5.2-f02 protocol preparation gate
```

### Task 4: Final Gate 1 audit and stop

**Files:** None.

**Interfaces:**

- Consumes: the two Gate 1 commits.
- Produces: clean local handoff with no remote publication and no Gate 2 artifacts.

- [x] **Step 1: Verify exit conditions**

Require: 216 bytes fully classified; consumed-turn message hash fixed; external authorization separated and hash-bound; primary root cause directly evidenced; remaining hypotheses ruled out or explicitly unresolved; worktree clean; historical evidence diffs empty; `forward-r5.2-f02` absent.

- [x] **Step 2: Stop**

Report `Gate 1 = COMPLETE`, `fresh execution = NOT_RUN`, `Gate 2 = NOT_STARTED`, `Pushed = NO`, and do not create any successor task or branch.
