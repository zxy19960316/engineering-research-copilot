# r5.2-f02 Execution Protocol Preparation Implementation Plan

> **For agentic workers:** Execute this plan inline on the existing Gate 1 branch. Do not delegate, create or continue a task, call a model, generate an execution authorization instance, or enter Gate 3. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Freeze and audit a contradiction-free, fail-closed r5.2-f02 execution protocol while keeping the new result root logically empty, every execution counter at zero, and fresh execution unauthorized.

**Architecture:** Separate the process authorization layer from the model-visible task. Freeze an executable prompt, a future authorization-receipt schema, a strict raw-byte/JSON boundary parser, an output-mode capability assessment, and a raw-response observation schema. A preparation auditor binds every artifact and historical tree; a dispatcher exposes only a zero-side-effect readiness check until Gate 3 supplies a separately authorized receipt and new task ID.

**Tech Stack:** Python 3.13 standard library, JSON Schema 2020-12 artifacts, SHA-256/Git blob identities, `unittest`, existing M3 composer/validator callbacks, GitHub Actions, and the current Codex `create_thread` request contract.

## Global Constraints

- Continue on `codex/m3.1.1-r5.2-f02-root-cause-and-protocol-preparation` from Gate 1 HEAD `263af3df0d8c075d4cdd9835eabe0708dc4f4163`.
- Use revision `r5.2-f02`, case `m3-f02`, and result root `evals/m3/results/forward-r5.2-f02/`.
- Keep `new_fresh_run_authorized=false`, `reserved_task_id=null`, and r5.2 task/finalization/composer/validator/retry counters at zero.
- Do not create an execution-authorization receipt instance, task ID, launch receipt, raw response, finalization, payload, bundle, validator receipt, transaction, or terminal result.
- Preserve `evals/m3/results/forward-r5/` from `1b696bce53ee0a11163bfe4f91a9a49ab3af6f49` and `evals/m3/results/forward-r5.1-f02/` from `fb5eec44bbf86446cf12bda2bddc76fcb07a7e69` byte-for-byte.
- Preserve Gate 1 diagnosis and keep r5.1-f02 `TERMINAL_NOT_ACCEPTED`, accepted `false`, M3 `IN_PROGRESS`, aggregate/closure `NOT_RUN`, and M4 `NOT_STARTED`.
- Treat `.gitkeep` as a tracking marker only; require zero result artifacts besides that empty marker.
- The prompt must start with `This is the authorized r5.2-f02 execution.` followed by `Execute the frozen task now.` and must not contain `do not execute`, `future task`, or `without separate authorization`, case-insensitively.
- Require one JSON object: first non-whitespace byte `{`, last non-whitespace byte `}`, no Markdown fences, no surrounding prose, no comments, no duplicate keys, UTF-8 BOM rejected, and no automatic repair.
- Official OpenAI documentation records that GPT-5.6 Sol supports Structured Outputs, but the current Codex `create_thread` interface exposes no JSON Schema/response-format parameter. Freeze `strict_text_json_fail_closed` for this surface and require capability recheck before Gate 3.
- Push only after local gates pass. Require green exact-HEAD GitHub Actions and make no commit after that final CI run.

## File Structure

- Create `evals/m3/forward-inputs-r5.2-f02/m3-f02.prompt.txt`: contradiction-free model-visible task.
- Create `evals/m3/forward-inputs-r5.2-f02/m3-f02.input-binding.json`: immutable source/route/root-cause bindings.
- Create `evals/m3/forward-inputs-r5.2-f02/m3-model-output-contract.schema.json`: inherited method payload and strict output-boundary policy.
- Create `evals/m3/forward-inputs-r5.2-f02/m3-f02.authorization-receipt.schema.json`: future Gate 3 five-field authorization receipt.
- Create `evals/m3/forward-inputs-r5.2-f02/m3-f02.raw-response-observation.schema.json`: pre-parser raw response metadata contract.
- Create `evals/m3/forward-inputs-r5.2-f02/m3-f02.output-mode.json`: model capability versus current execution-surface decision.
- Create `evals/m3/forward-inputs-r5.2-f02/protocol-regression-cases.json`: nine frozen synthetic output cases.
- Create `evals/m3/forward-inputs-r5.2-f02/manifest.json`: all-zero preparation and future-path registry.
- Create `evals/m3/results/forward-r5.2-f02/.gitkeep`: empty tracking marker, not result evidence.
- Create `evals/m3/r5_2_f02_protocol.py`: strict parser, classifier, prompt lint, receipt validation, observation validation, and callback-counting synthetic processor.
- Create `evals/m3/audit_forward_r5_2_f02_preparation.py`: read-only artifact/history/result-root auditor.
- Create `evals/m3/dispatch_forward_r5_2_f02.py`: preparation preflight that cannot invoke its injected callback.
- Create `tests/test_r5_2_f02_protocol.py`: output-boundary and orchestration matrix.
- Create `tests/test_audit_m3_forward_r5_2_f02_preparation.py`: binding and mutation tests.
- Create `tests/test_dispatch_forward_r5_2_f02.py`: zero-callback/zero-side-effect tests.
- Modify `.github/workflows/m1-validation.yml`: compile and execute the Gate 2 preparation audit.
- Modify `STATUS.md`: record Gate 2 readiness without claiming execution.
- Create `evals/m3/results/2026-08-07-m3.1.1-r5.2-f02-protocol-preparation-validation.md`: exact local and remote handoff record.

---

### Task 1: Strict output and authorization protocol

**Files:**

- Create: `tests/test_r5_2_f02_protocol.py`
- Create: `evals/m3/r5_2_f02_protocol.py`
- Create: `evals/m3/forward-inputs-r5.2-f02/protocol-regression-cases.json`
- Create: `evals/m3/forward-inputs-r5.2-f02/m3-f02.authorization-receipt.schema.json`
- Create: `evals/m3/forward-inputs-r5.2-f02/m3-f02.raw-response-observation.schema.json`

**Interfaces:**

- `parse_strict_json_object(raw: bytes) -> ParseResult` accepts exactly one UTF-8 JSON object and rejects BOM, empty output, fences, affixes, truncation, comments, duplicate keys, non-object roots, and non-finite values.
- `lint_execution_prompt(raw: bytes) -> list[str]` enforces the required prefix, forbidden phrase list, and every output-boundary statement.
- `validate_authorization_receipt(value: object, *, prompt_sha256: str, input_binding_sha256: str) -> list[str]` validates only the future five-field receipt.
- `validate_raw_observation(value: object) -> list[str]` validates metadata without parsing or repairing raw output.
- `process_synthetic_final(raw: bytes, *, compose_once, validate_once) -> dict[str, Any]` counts one composer boundary and at most one validator callback without writing.

- [ ] **Step 1: Write red protocol tests**

Cover valid object, fenced object, leading prose plus JSON, truncated object, BOM, duplicate keys, empty output, authorization-deferral prose, and valid JSON followed by validator rejection. Assert exact classifications and `composer/validator` counts.

```python
result = protocol.process_synthetic_final(
    raw,
    compose_once=compose,
    validate_once=validate,
)
self.assertEqual(result["composer_invocations"], 1)
self.assertLessEqual(result["validator_invocations"], 1)
```

- [ ] **Step 2: Confirm red import failure**

Run: `python -X utf8 -m unittest tests.test_r5_2_f02_protocol -v`

Expected: import failure because `r5_2_f02_protocol.py` does not exist.

- [ ] **Step 3: Implement the strict parser and classifier**

Use `json.loads(..., object_pairs_hook=...)`, reject duplicate keys explicitly, reject non-finite constants, and return closed codes such as `payload_invalid_json`, `payload_duplicate_key`, `payload_utf8_bom_forbidden`, and `payload_empty`. Never mutate raw bytes or synthesize repaired JSON.

- [ ] **Step 4: Implement receipt, observation, prompt-lint, and synthetic processing contracts**

The authorization schema requires exactly:

```json
{
  "revision": "r5.2-f02",
  "authorized": true,
  "prompt_sha256": "<frozen prompt hash>",
  "input_binding_sha256": "<frozen binding hash>",
  "authorized_task_count": 1
}
```

Do not create this instance in Gate 2.

- [ ] **Step 5: Run focused protocol tests and commit**

Run: `python -X utf8 -m unittest tests.test_r5_2_f02_protocol -v`

Commit: `eval: prepare r5.2-f02 strict execution protocol`

### Task 2: Frozen prompt, capability decision, and preparation manifest

**Files:**

- Create all remaining files under `evals/m3/forward-inputs-r5.2-f02/`
- Create: `evals/m3/results/forward-r5.2-f02/.gitkeep`
- Create: `tests/test_audit_m3_forward_r5_2_f02_preparation.py`
- Create: `tests/test_dispatch_forward_r5_2_f02.py`
- Create: `evals/m3/audit_forward_r5_2_f02_preparation.py`
- Create: `evals/m3/dispatch_forward_r5_2_f02.py`

**Interfaces:**

- `audit_preparation(path, *, repo_root=REPO_ROOT, historical_r5_check=None, historical_r5_1_check=None) -> dict[str, Any]` returns `ready_for_separate_execution_authorization` only when every binding, counter, prompt lint, schema, future path, result-root, and historical check passes.
- `preflight_dispatch(path, callback) -> dict[str, Any]` always leaves `callback_invocations=0` and returns `fresh_run_not_authorized` after a valid audit.

- [ ] **Step 1: Freeze the executable prompt and schemas**

Keep the r5.1 scientific task content and authority-copy rules, replace the contradictory opening, add all strict JSON boundary lines, and bind the inherited base contract.

- [ ] **Step 2: Freeze the output-mode decision**

Record official model support, the current `create_thread` request fields, `native_json_schema_parameter_exposed=false`, `structured_output_request_config=null`, `selected_mode=strict_text_json_fail_closed`, and `capability_recheck_required_before_gate3=true`.

- [ ] **Step 3: Write red preparation and dispatcher tests**

Mutate authorization state, task ID, counters, prompt phrases, output-mode selection, schema hashes, result artifacts, historical checks, and callback behavior. Require zero side effects.

- [ ] **Step 4: Implement the read-only auditor and non-launching dispatcher**

Verify raw/canonical/Git identities, zero result artifacts besides `.gitkeep`, no future authorization instance, all counters zero, root-cause binding, prompt lint, current surface decision, and immutable historical trees.

- [ ] **Step 5: Run focused preparation tests and commit**

Run:

```text
python -X utf8 -m unittest tests.test_audit_m3_forward_r5_2_f02_preparation -v
python -X utf8 -m unittest tests.test_dispatch_forward_r5_2_f02 -v
python -X utf8 evals/m3/audit_forward_r5_2_f02_preparation.py
python -X utf8 evals/m3/dispatch_forward_r5_2_f02.py
```

Commit: `eval: gate r5.2-f02 preparation without execution`

### Task 3: CI, full validation, and status

**Files:**

- Modify: `.github/workflows/m1-validation.yml`
- Modify: `STATUS.md`
- Create: `evals/m3/results/2026-08-07-m3.1.1-r5.2-f02-protocol-preparation-validation.md`
- Include: this plan

- [ ] **Step 1: Add the preparation auditor to CI**

Compile the three Gate 2 Python modules and add a named Gate 2 audit step after the preserved r5.1 terminal audit.

- [ ] **Step 2: Run focused and full local validation**

Run:

```text
python -X utf8 -m py_compile evals/m3/r5_2_f02_protocol.py evals/m3/audit_forward_r5_2_f02_preparation.py evals/m3/dispatch_forward_r5_2_f02.py
python -X utf8 -m unittest tests.test_r5_2_f02_protocol tests.test_audit_m3_forward_r5_2_f02_preparation tests.test_dispatch_forward_r5_2_f02 -v
python -X utf8 -m unittest discover -s tests -p "test_*.py" -v
python -X utf8 evals/m1/replay_offline_results.py
python -X utf8 evals/m1/replay_machine_artifacts.py
python -X utf8 evals/m2/build_fixtures.py
git diff --exit-code -- evals/m2/adversarial-cases.json evals/m2/fixtures
python -X utf8 evals/m2/replay_offline_results.py
python -X utf8 evals/m3/build_fixtures.py
git diff --exit-code -- evals/m3/adversarial-cases.json evals/m3/fixtures
python -X utf8 evals/m3/replay_offline_results.py
python -X utf8 evals/m3/audit_skill_package.py
python -X utf8 evals/m3/audit_forward_r5_1_f02_terminal.py
python -X utf8 evals/m3/audit_forward_r5_2_f02_preparation.py
git diff --check
```

- [ ] **Step 3: Verify historical and result-root gates**

Require both historical diffs empty, `.gitkeep` empty, zero other result files, no execution authorization instance, and `git status --short` limited to intended Gate 2 files before commit.

- [ ] **Step 4: Update STATUS and validation record, then commit**

Record Gate 2 `READY_FOR_SEPARATE_EXECUTION_AUTHORIZATION`, fresh execution `NOT_RUN`, counters `0/0/0/0/0`, selected output mode, historical diffs empty, and remote exact-HEAD CI `NOT_RUN` until publication.

Commit: `docs: record r5.2-f02 protocol preparation gate`

### Task 4: Publish exact HEAD and stop before Gate 3

**Files:** None.

- [ ] **Step 1: Push the current branch without creating a PR**

Run: `git push --set-upstream origin codex/m3.1.1-r5.2-f02-root-cause-and-protocol-preparation`

- [ ] **Step 2: Require exact-HEAD GitHub Actions success**

Resolve the run for the pushed SHA, require `validate`, Ubuntu historical audit, and Windows historical audit to conclude `success`, and verify the remote branch SHA equals local HEAD.

- [ ] **Step 3: Verify final exit conditions and stop**

Require: worktree clean; remote SHA exact; CI green; prompt lint pass; result artifact count zero; all r5.2 counters zero; `new_fresh_run_authorized=false`; M1/M2/M3 replay unchanged; historical r5/r5.1 diffs empty; Gate 3 `NOT_STARTED`. Do not create an authorization receipt or fresh task.
