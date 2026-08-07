# r5.2-f02 One-Shot Fresh Execution Implementation Plan

> **For agentic workers:** Execute this plan inline in the current session. Do not delegate, create more than one task, send a follow-up turn, repair output, retry, aggregate revisions, close M3, or enter Gate 4. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Authorize, remotely gate, launch, observe, and consume exactly one new r5.2-f02 fresh task, preserving either an accepted transaction or a terminal-not-accepted failure without retry.

**Architecture:** Keep the five-field external authorization receipt separate from the model-visible prompt and from a hash-bound execution-control record. A read-only auditor proves the authorization HEAD is safe before launch; an exclusive launch claim makes the single task budget consumable; a pre-parser capture writes raw UTF-8 bytes and observation metadata before the strict parser, composer, or validator runs; a terminal auditor then proves exact counters, immutable history, closed artifacts, and either accepted or fail-closed state.

**Tech Stack:** Python 3.13 standard library, JSON Schema 2020-12 artifacts, SHA-256 and Git blob identities, `unittest`, exclusive filesystem creation (`O_CREAT | O_EXCL`), the existing M3 composer and validator, Codex `create_thread`, GitHub Actions, and Git.

## Global Constraints

- Start from Gate 2 exact HEAD `05e64d9678f9755126b1c1a0bfa4835bd8296e08`, whose branch and remote both point to that SHA and whose GitHub Actions run `31184790162` concluded `success`.
- Use branch `codex/m3.1.1-r5.2-f02-one-shot-fresh-execution`, revision `r5.2-f02`, case `m3-f02`, and result root `evals/m3/results/forward-r5.2-f02/`.
- Preserve `evals/m3/results/forward-r5/` from `1b696bce53ee0a11163bfe4f91a9a49ab3af6f49` and `evals/m3/results/forward-r5.1-f02/` from `fb5eec44bbf86446cf12bda2bddc76fcb07a7e69` byte-for-byte.
- Preserve every Gate 1 and Gate 2 frozen artifact byte-for-byte. The successor authorization receipt may be added at its reserved path, but the Gate 2 manifest remains a historical preparation snapshot with `new_fresh_run_authorized=false`.
- Before launch require `tasks/finalizations/composer/validator/retry = 0/0/0/0/0` and no logical result artifacts besides the empty `.gitkeep` marker.
- Create the five-field `execution-authorization.json` only in Gate 3. Its exact fields are `revision`, `authorized`, `prompt_sha256`, `input_binding_sha256`, and `authorized_task_count`; `authorized_task_count` must equal one.
- Recheck the current task-creation surface. Because it still exposes no request-level JSON Schema or response-format field, use the frozen `strict_text_json_fail_closed` mode and do not substitute a direct API.
- Submit the frozen prompt bytes as the complete initial user message. Do not prepend or append coordinator prose. Omit `model` and `thinking` because the current task tool requires the default unless the user explicitly selects a model.
- Create exactly one fresh worktree task from the remote-green authorization branch. Do not send a follow-up message or create a second task.
- Treat the first completed assistant final as the one consumable finalization. Persist its exact tool-boundary UTF-8 bytes and observation record before parsing.
- Never normalize, repair, strip fences, extract embedded JSON, retry the same task, or continue consuming after a failure.
- Success requires `tasks/finalizations/composer/validator/retry = 1/1/1/1/0`, strict JSON success, composer success, validator acceptance, completed transaction, no unexpected artifacts, no side effects, and unchanged historical evidence.
- Any failure must produce `terminal_not_accepted`, `accepted=false`, freeze the raw bytes, keep retry zero and forbidden, and stop Gate 3. Gate 4 remains unauthorized in both outcomes.
- Push the authorization HEAD before execution and require its own green remote CI. After terminalization, push the exact terminal HEAD and require its own green remote CI without amending or rebasing evidence commits.

## File Structure

- Create `evals/m3/forward-inputs-r5.2-f02/execution-authorization.json`: the exact five-field external authorization receipt.
- Create `evals/m3/forward-inputs-r5.2-f02/m3-f02.execution-control.json`: readiness HEAD/CI, current execution surface, task request projection, limits, forbidden operations, future paths, and history bindings.
- Create `evals/m3/forward-inputs-r5.2-f02/m3-f02.launch.schema.json`: closed launch-attempt and task-binding receipt contract.
- Create `evals/m3/r5_2_f02_execution_contract.py`: closed-shape validation, canonical hashing, exclusive writes, launch records, and terminal record validation.
- Create `evals/m3/audit_forward_r5_2_f02_execution_authorization.py`: read-only authorization audit against the Gate 2 Git snapshot and empty result root.
- Create `evals/m3/dispatch_forward_r5_2_f02_once.py`: explicit `claim` and `record-launch` operations with at-most-one task semantics.
- Create `evals/m3/consume_forward_r5_2_f02_once.py`: raw-first capture, strict parse, exactly-once composer/validator flow, context/transaction/terminal writes, and no retry.
- Create `evals/m3/audit_forward_r5_2_f02_terminal.py`: independent terminal artifact, counter, byte, history, and acceptance audit.
- Create focused tests for each new module under `tests/`.
- Modify `.github/workflows/m1-validation.yml`: compile the Gate 3 modules and run the stage-appropriate read-only audit.
- Modify `STATUS.md`: first record remote-gated authorization, then record the consumed terminal truth without closing M3.
- Create separate authorization and execution validation records under `evals/m3/results/`.

---

### Task 1: Freeze the five-field authorization and execution-control contract

**Files:**

- Create: `tests/test_r5_2_f02_execution_contract.py`
- Create: `evals/m3/r5_2_f02_execution_contract.py`
- Create: `evals/m3/forward-inputs-r5.2-f02/execution-authorization.json`
- Create: `evals/m3/forward-inputs-r5.2-f02/m3-f02.execution-control.json`
- Create: `evals/m3/forward-inputs-r5.2-f02/m3-f02.launch.schema.json`

**Interfaces:**

- `validate_execution_control(value: object) -> list[str]` rejects missing/unknown fields, non-one maxima, unsafe permissions, request-projection drift, and nonzero counters.
- `validate_launch_attempt(value: object, *, authorization_raw: bytes, control_raw: bytes) -> list[str]` validates the exclusive pre-launch claim.
- `validate_launch_receipt(value: object, *, attempt: dict[str, object], task_id: str | None = None) -> list[str]` binds one nonhistorical task and one launch.
- `write_new_bytes(path: Path, raw: bytes) -> None` and `write_new_json(path: Path, value: dict[str, object]) -> None` use exclusive creation and fsync.

- [x] **Step 1: Write red contract tests**

Test the exact five-field receipt through `validate_authorization_receipt`, execution-control identities, all maxima equal one, all counters zero, retry/repair/follow-up/second-finalization flags false, current request-surface fields, deterministic request and model-visible-message hashes, historical task rejection, and second-write failure.

```python
self.assertEqual(contract.validate_execution_control(CONTROL), [])
self.assertEqual(protocol.validate_authorization_receipt(
    RECEIPT,
    expected_prompt_sha256=contract.PROMPT_SHA256,
    expected_input_binding_sha256=contract.INPUT_BINDING_SHA256,
), [])
with self.assertRaises(FileExistsError):
    contract.write_new_bytes(path, b"second")
```

- [x] **Step 2: Run the focused test and observe the missing-module failure**

Run: `python -X utf8 -m unittest tests.test_r5_2_f02_execution_contract -v`

Expected: import failure for `r5_2_f02_execution_contract`.

- [x] **Step 3: Implement the minimal closed contracts and freeze JSON artifacts**

The authorization instance must be exactly:

```json
{"authorized":true,"authorized_task_count":1,"input_binding_sha256":"3d90ed7f02a865eb3cab0fd8f70f0407ce5a80a93e500996686e2fad54c1709d","prompt_sha256":"815eae213701505755fb7edc4d64d16089bd4e14e14dc6ec1e16c787918ea1df","revision":"r5.2-f02"}
```

The execution control must bind the Gate 2 HEAD/run, project ID `ff35b25f-4644-41c8-9073-74c697559439`, worktree branch, exact prompt as the sole initial user message, omitted model/thinking fields, strict-text mode, result/future paths, maxima `1/1/1/1`, retry zero, and Gate 4 false.

- [x] **Step 4: Run the focused test and commit**

Run: `python -X utf8 -m unittest tests.test_r5_2_f02_execution_contract -v`

Expected: all tests pass.

Commit: `eval: authorize one r5.2-f02 fresh task`

### Task 2: Add a read-only authorization auditor

**Files:**

- Create: `tests/test_audit_m3_forward_r5_2_f02_execution_authorization.py`
- Create: `evals/m3/audit_forward_r5_2_f02_execution_authorization.py`
- Modify: `tests/test_audit_m3_forward_r5_2_f02_preparation.py`

**Interfaces:**

- `audit_execution_authorization(path, *, result_root=RESULT_ROOT) -> dict[str, object]` returns `ready_for_one_shot_fresh_execution` only with a valid receipt/control, empty root, zero counters, prompt/input hashes, frozen Gate 2 blobs, green-readiness binding, current surface decision, and clean historical trees.
- The Gate 2 baseline test audits the immutable preparation snapshot by patching successor state to its original absent/empty values; it does not reinterpret the current successor worktree as Gate 2.

- [x] **Step 1: Write red drift and read-only tests**

Cover receipt field drift, prompt/input mismatch, control/request projection drift, unsafe permission, nonzero counter, unexpected result artifact, Gate 2 blob drift, historical r5/r5.1 drift, and repeatability with `side_effects=[]`.

```python
result = audit.audit_execution_authorization(AUTHORIZATION, result_root=result_root)
self.assertEqual(result["status"], "ready_for_one_shot_fresh_execution")
self.assertEqual(result["counters"], {"tasks": 0, "finalizations": 0, "composer": 0, "validator": 0, "retry": 0})
self.assertEqual(result["side_effects"], [])
```

- [x] **Step 2: Run the focused test and observe failure**

Run: `python -X utf8 -m unittest tests.test_audit_m3_forward_r5_2_f02_execution_authorization -v`

Expected: import failure for the auditor.

- [x] **Step 3: Implement snapshot-bound auditing**

Read frozen Gate 2 artifacts from `05e64d...` with Git plumbing, compare current bytes, validate the five-field receipt and execution control, require only a zero-byte `.gitkeep`, and compare both historical evidence directories to their evidence heads. Do not call a launcher or write files.

- [x] **Step 4: Run both Gate 2 and authorization tests and commit**

Run:

```text
python -X utf8 -m unittest tests.test_audit_m3_forward_r5_2_f02_preparation -v
python -X utf8 -m unittest tests.test_audit_m3_forward_r5_2_f02_execution_authorization -v
```

Expected: all tests pass and the live authorization audit reports ready with zero side effects.

Commit: `test: audit r5.2-f02 execution authorization`

### Task 3: Implement one-shot launch, raw-first consumption, and terminal audit

**Files:**

- Create: `tests/test_dispatch_forward_r5_2_f02_once.py`
- Create: `tests/test_consume_forward_r5_2_f02_once.py`
- Create: `tests/test_audit_m3_forward_r5_2_f02_terminal.py`
- Create: `evals/m3/dispatch_forward_r5_2_f02_once.py`
- Create: `evals/m3/consume_forward_r5_2_f02_once.py`
- Create: `evals/m3/audit_forward_r5_2_f02_terminal.py`

**Interfaces:**

- `claim_launch_once(authorization_path, *, result_root=RESULT_ROOT, observed_at: str) -> dict[str, object]` creates `m3-f02.launch-attempt.json` exclusively before task creation.
- `record_launch_once(authorization_path, *, task_id: str, model_id: str, task_created_at: str, result_root=RESULT_ROOT) -> dict[str, object]` creates `m3-f02.launch.json` exclusively and rejects historical or second task IDs.
- `consume_final_once(..., final_raw: bytes, observation: dict[str, object], compose_once, validate_once) -> dict[str, object]` writes raw bytes and observation first, then invokes the strict parser/composer boundary once and validator at most once, finally writing context, transaction, and terminal manifest.
- `audit_terminal(result_root=RESULT_ROOT) -> dict[str, object]` independently recomputes bytes, counters, accepted state, artifact allowlist, immutable histories, and retry zero.

- [x] **Step 1: Write red exactly-once and terminal matrix tests**

Use temporary result roots. Prove preflight writes nothing; claim writes once; a second claim/task/finalization fails without callbacks or overwrite; raw bytes exist before a deliberately failing parser callback; invalid JSON ends `terminal_not_accepted` with `1/1/1/0/0`; valid accepted payload ends `accepted` with `1/1/1/1/0`; and no failure path retries.

```python
self.assertEqual(result["counters"], {
    "tasks": 1,
    "finalizations": 1,
    "composer": 1,
    "validator": 1,
    "retry": 0,
})
self.assertTrue((root / "m3-f02.model-final.raw").exists())
```

- [x] **Step 2: Run focused tests and observe missing-module failures**

Run the three new `unittest` modules with `python -X utf8`.

- [x] **Step 3: Implement exclusive launch operations**

Every mutating operation must validate the authorization first. `claim` writes the authorization/control hashes and one-attempt/no-retry limits before any external call. `record-launch` binds exactly one new task and records the frozen request/message projection hashes and coordinator-observed creation time.

- [x] **Step 4: Implement raw-first terminal consumption**

Write `m3-f02.model-final.raw` and `m3-f02.raw-response-observation.json` with exclusive creation and fsync before `parse_strict_json_object`. On parse or composer failure, write a failed composer receipt, context, transaction, and terminal manifest with validator zero. On composition success, write the payload/bundle/composer receipt, invoke the existing validator once, write validation/validator receipt, and accept only `status=valid` with empty errors and gaps. All terminal records set retry zero and forbidden.

- [x] **Step 5: Implement independent terminal audit and commit**

Require the exact terminal allowlist, matching raw SHA/length, launch/task/finalization bindings, transaction/receipt counters, history diffs empty, no unexpected artifacts, no side effects, and either the complete accepted predicate or explicit terminal-not-accepted predicate.

Commit: `eval: enforce r5.2-f02 one-shot terminal consumption`

### Task 4: Build and remotely gate the pre-execution authorization HEAD

**Files:**

- Modify: `.github/workflows/m1-validation.yml`
- Modify: `STATUS.md`
- Create: `evals/m3/results/2026-08-07-m3.1.1-r5.2-f02-one-shot-authorization-validation.md`

**Interfaces:**

- CI compiles every Gate 3 module and runs only the read-only authorization auditor while the result root remains logically empty.
- The validation record distinguishes local evidence from the later exact-HEAD remote run.

- [x] **Step 1: Run compile, focused, full, replay, package, Skill, history, and authorization gates**

Require zero failures, unchanged M1/M2/M3 replay outputs, empty historical diffs, exact zero counters, one zero-byte `.gitkeep`, `ready_for_one_shot_fresh_execution`, and no callback or side effect.

- [x] **Step 2: Write the authorization evidence and status**

Record Gate 2 HEAD/run, new authorization receipt/control hashes, local counts, current surface recheck, exact request/message projections, and stopped state `fresh_execution=NOT_RUN`.

- [x] **Step 3: Commit and push without launching**

Commit: `docs: record r5.2-f02 one-shot authorization readiness`

Push the branch, wait for the pushed exact HEAD, and require all GitHub Actions jobs green. Do not create the task if the SHA or CI conclusion differs.

### Task 5: Consume the authorization exactly once

**Files:**

- Runtime-create only the declared result artifacts under `evals/m3/results/forward-r5.2-f02/`.

**Interfaces:**

- The coordinator uses the exact frozen prompt as `create_thread.prompt` and the frozen worktree target from the execution control.
- The first completed assistant final is encoded as UTF-8 and passed once to `consume_final_once`; no follow-up thread message is permitted.

- [x] **Step 1: Re-run the read-only preflight immediately before launch**

Require the pushed authorization SHA, green exact-HEAD CI, clean worktree, empty root, zero counters, current no-schema surface, and clean histories.

- [x] **Step 2: Exclusively claim the launch budget**

Run the dispatcher `claim` operation. If claim creation fails, stop without calling `create_thread`.

- [x] **Step 3: Create one fresh task**

Call `create_thread` once with project `ff35b25f-4644-41c8-9073-74c697559439`, a worktree from branch `codex/m3.1.1-r5.2-f02-one-shot-fresh-execution`, the exact prompt contents, and no explicit model/thinking. Record the returned task/model identity once.

- [x] **Step 4: Wait for and capture the first finalization**

Use bounded task waits/read-only inspection. Do not send a message. When complete, encode the first final exactly as UTF-8, build the observation with exposed metadata and explicit `null/not_exposed` provider fields, then call the consumer once.

- [x] **Step 5: Stop at the terminal result**

If accepted, continue only to evidence auditing. If not accepted, freeze the terminal failure and do not retry, repair, or enter Gate 4.

### Task 6: Audit and publish the terminal Gate 3 evidence

**Files:**

- Modify: `.github/workflows/m1-validation.yml`
- Modify: `STATUS.md`
- Create: `evals/m3/results/2026-08-07-m3.1.1-r5.2-f02-one-shot-execution-validation.md`
- Include: all runtime-created result artifacts.

**Interfaces:**

- CI switches from pre-execution authorization audit to terminal audit only after a terminal manifest exists.
- Status records either accepted `1/1/1/1/0` or terminal-not-accepted with the exact observed counters; M3 remains `IN_PROGRESS` and Gate 4 remains `NOT_STARTED`.

- [x] **Step 1: Run the independent terminal and immutable-history audits**

Require exact raw byte/hash agreement, no unexpected artifacts, no side effects, retry zero, historical r5/r5.1 diffs empty, and terminal semantics matching every receipt and transaction.

- [x] **Step 2: Run focused/full/replay/package/Skill gates**

Do not weaken or relabel a failing gate. Record exact counts and outputs.

- [x] **Step 3: Write final Gate 3 evidence and status**

Record the task ID, raw byte count/hash, observation availability, parser/composer/validator outcome, transaction state, exact counters, terminal status, immutable-history checks, and explicit `Gate 4=NOT_STARTED`.

- [ ] **Step 4: Commit, push, and require terminal exact-HEAD CI**

Commit the terminal evidence without amend/rebase, push the branch, and wait for its exact HEAD CI. A CI failure does not authorize code repair on the consumed result; preserve and report it separately.
