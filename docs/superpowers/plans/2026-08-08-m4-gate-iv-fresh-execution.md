# M4 Gate IV Fresh Execution Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Consume the single frozen M4.0 authorization exactly once and preserve the unmodified final output of up to 60 independent fresh-context tasks in six preregistered domain batches.

**Architecture:** The coordinator performs one fail-closed preflight, creates one exclusive launch claim, and then uses `codex_app.create_thread` once per frozen task ID from the authorized branch. Each task receives only the common protocol, its case `user_input`, its own arm instructions, its own identifiers, and the closed output contract; the coordinator preserves the returned final text below that task's frozen result root without exposing it to any other task. A protocol or infrastructure failure consumes the attempt, freezes the evidence, stops later batches, and requires a successor revision.

**Tech Stack:** Codex fresh worktree tasks, Python authorization auditors, closed JSON evidence, Git, UTF-8/LF.

## Global Constraints

- Start task worktrees from `codex/m4-cross-engineering-forward-evaluation-one-shot-authorization` at authorized HEAD `e3542201f96218f340a09f77458661822c98d876`.
- Require authorization token `sha256:09c940955104f2ae9278b55d155bc43a47d43a0eb9e80e4f90d7425eb3c0e292` to be `UNCONSUMED` before launch.
- Omit the create-thread `model` and `thinking` fields; require configured defaults `gpt-5.6-sol` and reasoning effort `max` immediately before claim.
- Create exactly one new worktree thread and accept exactly one finalization for each launched task ID.
- Use the six frozen batches in order: `M4-BATCH-NUC`, `M4-BATCH-MEC`, `M4-BATCH-ELE`, `M4-BATCH-AUT`, `M4-BATCH-COM`, and `M4-BATCH-MPH`.
- Never retry, repair, continue, or send a follow-up message to a task.
- Never expose another M4 result, execution transcript, judge score, or the complete blind mapping to a task.
- Preserve final text exactly as received. A malformed or non-JSON final is failure evidence, not input for normalization.
- Stop before judge execution, blind-map access, unblinding, aggregation, threshold claims, M4 closure, or M5.
- Keep `skills/engineering-research-copilot/`, `evals/m3/`, cases, variants, schemas, rubric, randomization, thresholds, and the preparation manifest unchanged.

---

## File map

- `docs/superpowers/plans/2026-08-08-m4-gate-iv-fresh-execution.md`: this one-shot execution sequence.
- `evals/m4/execution/m4.0/launch-claim.json`: exclusive whole-matrix token claim created before the first task.
- `evals/m4/results/m4.0/<task-id>/dispatch-receipt.json`: immutable task/thread binding written after successful creation.
- `evals/m4/results/m4.0/<task-id>/raw-final.txt`: exact final text returned by the fresh context.
- `evals/m4/results/m4.0/<task-id>/task-result.json`: created only when the exact final text is already one closed JSON object satisfying the task-result schema; its bytes equal `raw-final.txt` apart from a single terminal LF only when the returned text already has that LF.
- `evals/m4/execution/m4.0/pre-dispatch-failure.json`: immutable terminal record if the coordinator fails after claim but before any task creation.
- `evals/m4/execution/audit_m4_0.py`: read-only terminal auditor for the claimed, zero-task pre-dispatch failure state.
- `tests/test_m4_execution.py`: positive and adversarial terminal-state tests.

### Task 1: Revalidate and consume the authorization

**Files:**
- Create: `evals/m4/execution/m4.0/launch-claim.json`

**Interfaces:**
- Consumes: authorization receipt, execution control, current Codex defaults, project metadata, clean result roots, and absent claim.
- Produces: one exclusive `m4-launch-claim-v1` record bound to the authorization token and exact authorized HEAD.

- [ ] **Step 1: Run the configured-default preflight**

Run:

```powershell
python -X utf8 evals/m4/authorization/audit_authorization.py --configured-model gpt-5.6-sol --configured-reasoning-effort max --require-configured-defaults
```

Expected: `READY_UNCONSUMED`, `configured_default_check=MATCHED`, 60 authorized tasks, no claim, no result roots, and zero counters.

- [ ] **Step 2: Verify the authorized project surface**

Expected: project ID `ff35b25f-4644-41c8-9073-74c697559439`, Git repository `true`, environment `worktree`, and authorized starting branch present at `e3542201f96218f340a09f77458661822c98d876`.

- [ ] **Step 3: Create the launch claim exclusively**

The claim contains schema version, claim ID, UTC timestamp, authorization token, authorization HEAD, project ID, starting branch, exact model/default policy, six ordered batch IDs, 60 task IDs, and `claim_count=1`. Creation must fail if the path already exists.

- [ ] **Step 4: Confirm the readiness auditor now rejects reuse**

Expected: authorization audit reports `authorization_already_claimed`. This is proof of consumption, not a failed execution precondition.

### Task 2: Build the frozen per-task request in memory

**Files:**
- Read: `evals/m4/authorization/execution-control.json`
- Read: `evals/m4/task-protocol.md`
- Read: each task's exact case JSON and optional variant instruction snapshot

**Interfaces:**
- Consumes: only each task's `task_id`, own `blind_id`, case `user_input`, common protocol, own variant instructions, execution constraints, and preassigned unique context/finalization IDs.
- Produces: one initial prompt; no prompt file and no follow-up prompt.

- [ ] **Step 1: Verify every referenced byte hash before composing prompts**

Expected: case, user input, common protocol, variant instructions, rubric, and execution-constraint hashes equal `execution-control.json`.

- [ ] **Step 2: Compose the common closed output contract**

Require one JSON object with `schema_version=m4-task-result-v1`, the supplied task/blind/context/finalization IDs, attempt 1, retry 0, independent finalization true, no visible task IDs, the research response as a JSON string, citation records, all eight machine metrics, detected mismatch IDs, side effects, and one terminal state.

- [ ] **Step 3: Keep task context isolated**

Embed the exact task inputs in the initial prompt and forbid repository-result reads, filesystem writes, model downloads, services, uploads, experiments, simulations, training, deployment, and physical control.

### Task 3: Execute the six frozen batches

**Files:**
- Create: `evals/m4/results/m4.0/<task-id>/dispatch-receipt.json`
- Create: `evals/m4/results/m4.0/<task-id>/raw-final.txt`

**Interfaces:**
- Consumes: the launch claim and the exact batch roster from execution control.
- Produces: at most 60 distinct thread IDs and at most 60 untouched final texts.

- [ ] **Step 1: Launch the ten nuclear tasks once and wait for terminal states**

- [ ] **Step 2: If and only if the nuclear batch has no infrastructure or protocol failure, launch the ten mechanical tasks once**

- [ ] **Step 3: If and only if prior batches are valid, launch the ten electrical tasks once**

- [ ] **Step 4: If and only if prior batches are valid, launch the ten automation/control tasks once**

- [ ] **Step 5: If and only if prior batches are valid, launch the ten computer/data tasks once**

- [ ] **Step 6: If and only if prior batches are valid, launch the ten multiphysics tasks once**

For every creation, record the returned thread ID without sending a follow-up. For every completion, preserve its exact final text once. If creation, timeout, tool transport, schema, identifier, or protocol validation fails, write the available evidence, stop all later batches, and do not repair or retry.

### Task 4: Audit the unjudged execution evidence

**Files:**
- Read: every created receipt and raw final
- Do not create: `evals/m4/results-manifest.json`
- Do not create: any judge score

**Interfaces:**
- Consumes: the immutable launch claim and created task roots.
- Produces: a truthful execution-only count and failure inventory, without scoring or acceptance claims.

- [ ] **Step 1: Verify unique task, thread, context, and finalization identifiers**

Expected for a complete run: 60 unique task IDs, 60 unique thread IDs, 60 unique context IDs, and 60 unique finalization IDs.

- [ ] **Step 2: Verify one attempt and no follow-ups, retries, repairs, or cross-task visibility**

Expected: attempt count 1 per launched task and all prohibited counters zero.

- [ ] **Step 3: Preserve the truthful terminal state**

Do not run `audit_results.py` as an acceptance audit because judge execution and aggregation remain unauthorized. Record fresh execution as complete-unjudged only if all 60 raw finals are present and protocol-valid; otherwise record the exact stopped batch and failure.

- [ ] **Step 4: Commit and push only immutable execution evidence**

Stage explicit plan, claim, receipt, and raw-final paths. Do not include cases, variants, Skill, M3, judge artifacts, aggregate results, threshold claims, or closure changes.

## Self-review checklist

- [ ] Every task starts from the authorized branch and uses omitted model/thinking fields.
- [ ] The claim is absent before preflight and created exactly once before the first task.
- [ ] No task receives another result or the complete blind mapping.
- [ ] No task is retried, repaired, or continued.
- [ ] Later batches do not start after an infrastructure or protocol failure.
- [ ] Raw final text is never normalized into a passing result.
- [ ] No judge, aggregation, threshold, closure, or M5 action occurs.

### Task 5: Close out an observed pre-dispatch failure without repair

**Files:**
- Create: `evals/m4/execution/m4.0/pre-dispatch-failure.json`
- Create: `evals/m4/execution/audit_m4_0.py`
- Create: `tests/test_m4_execution.py`
- Modify: `STATUS.md`
- Modify: `tests/test_m3_r5_erratum.py`

**Interfaces:**
- Consumes: the immutable launch claim, exact raw coordinator exception, authorization/control bindings, and absence of all task result roots.
- Produces: `audit_execution(repo_root: Path, claim_path: Path | None = None, failure_path: Path | None = None, results_base: Path | None = None, verify_git: bool = True) -> dict[str, object]` with terminal status `PRE_DISPATCH_FAILED_PRESERVED`.

- [ ] **Step 1: Freeze the exact failure and zero counters**

Require `failed_stage=frozen_request_bundle_hash_verification`, batch `M4-BATCH-NUC`, `task_id=null`, the exact missing `System.Convert.ToHexString` method error, and all task/finalization/result/retry/repair/follow-up/judge counters equal to zero.

- [ ] **Step 2: Write the failing terminal-audit tests**

Test the repository terminal status, immutable claim/failure binding, no writes during audit, rejection of token/counter drift, rejection of any result root, and unchanged frozen M3/M4 preparation trees.

Run:

```powershell
python -X utf8 -m unittest tests.test_m4_execution -v
```

Expected before the auditor exists: import failure for `evals.m4.execution.audit_m4_0`.

- [ ] **Step 3: Implement the minimal read-only auditor**

The auditor parses both JSON objects, verifies raw SHA-256 bindings, compares all 60 task IDs and six batches with authorization control, requires the claimed model/default policy, requires zero result roots and absent results manifest, and checks frozen paths against preparation HEAD `c56c3c1ab384f65e51a70e9582672c6320d19121`.

- [ ] **Step 4: Record the truthful repository transition**

Set M4.0 to `PRE_DISPATCH_FAILED`, token `CONSUMED`, claim count `1`, fresh result state `NOT_RUN`, all execution counters `0`, same-revision continuation `false`, successor revision required, and fresh execution authorization `false` pending separate M4.1 review.

- [ ] **Step 5: Validate and publish immutable closeout evidence**

Run:

```powershell
python -X utf8 -m unittest tests.test_m4_execution tests.test_m4_authorization tests.test_m4_preparation tests.test_m4_results -v
python -X utf8 evals/m4/execution/audit_m4_0.py
python -X utf8 -m unittest discover -s tests -p "test_*.py" -v
```

Expected: terminal audit returns `PRE_DISPATCH_FAILED_PRESERVED`; no task or result is created; the complete suite passes. Commit and push the execution branch without amending, squashing, retrying, or launching a successor revision.
