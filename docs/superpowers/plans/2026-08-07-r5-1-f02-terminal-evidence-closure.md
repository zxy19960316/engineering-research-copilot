# r5.1-f02 Terminal Evidence Closure Implementation Plan

> **For agentic workers:** Execute this plan inline and preserve the three review gates. Do not delegate or create a fresh context. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Freeze the consumed r5.1-f02 `payload_invalid_json` outcome as immutable `TERMINAL_NOT_ACCEPTED` evidence with a read-only auditor and a terminal CI gate.

**Architecture:** Add a closed terminal contract and hash-bound manifest over immutable Git blobs, then audit the current worktree against those frozen identities and the one-shot causal chain. Preserve predecessor readiness auditors unchanged and move only the current CI gate to the new terminal auditor. Tests mutate temporary copies or injected checks; they never rewrite real execution evidence.

**Tech Stack:** Python 3.13-compatible standard library, `unittest`, Git blob plumbing, JSON, GitHub Actions YAML.

## Global Constraints

- Start from execution evidence HEAD `a847b3eaf39a6f4f70353cd669e41e414afc658c` on `codex/m3.1.1-r5.1-f02-terminal-evidence-closure`.
- Preserve `evals/m3/results/forward-r5.1-f02/m3-f02.*` bytes exactly.
- Preserve `evals/m3/results/forward-r5/` relative to `1b696bce53ee0a11163bfe4f91a9a49ab3af6f49`.
- Preserve predecessor authorization artifacts relative to `85ce824c55a3a40f3f05153a57edb809dc68eee6`.
- Do not launch a task, invoke the dispatcher launch path, retry, repair, compose, validate, aggregate, close M3, merge, start M4, start r6, or push.
- Keep M3 `IN_PROGRESS`, historical r5 `BLOCKED_NOT_ACCEPTED`, aggregate `NOT_RUN`, M3 closure `NOT_RUN`, and M4 `NOT_STARTED`.

---

### Task 1: Closed terminal contract and manifest

**Files:**

- Create: `evals/m3/r5_1_f02_terminal_contract.py`
- Create: `evals/m3/results/forward-r5.1-f02/terminal-manifest.json`
- Test: `tests/test_audit_m3_forward_r5_1_f02_terminal.py`

**Interfaces:**

- Consumes: immutable Git blobs at execution evidence HEAD, authorization HEAD, and historical evidence HEAD.
- Produces: `validate_terminal_manifest_shape(value: object) -> list[str]`, strict JSON/hash helpers, fixed artifact-source bindings, closed result-root filename sets, and schema `m3.1-forward-r5.1-f02-terminal-v1`.

- [ ] **Step 1: Write red contract tests**

Create a test module that imports `audit_forward_r5_1_f02_terminal`, calls `audit_terminal(TERMINAL_MANIFEST)`, and expects `status == "terminal_not_accepted"`, empty errors/gaps/side effects, exact one-shot counters, `accepted is False`, and `payload_invalid_json`. Add temporary-copy mutation helpers before implementation so the import or assertions fail.

- [ ] **Step 2: Run the focused test to verify red**

Run: `python -X utf8 -m unittest tests.test_audit_m3_forward_r5_1_f02_terminal -v`

Expected: failure because the terminal auditor/contract/manifest do not exist.

- [ ] **Step 3: Implement the closed contract**

Define exact constants for revision, case, heads, CI run, task IDs, token, terminal counters and permissions. Implement strict UTF-8/no-BOM object parsing, raw and canonical SHA-256, exact manifest key validation, safe relative paths, and closed required/allowed/forbidden result filenames. Treat model-final and payload as expected malformed JSON and forbid canonical hashes for them.

- [ ] **Step 4: Freeze the manifest**

Record for each binding its fixed key, path, source head, Git blob OID, byte length, raw SHA-256, UTF-8 status, JSON status, and canonical SHA-256 only for valid JSON. Bind launch attempt/receipt, model final, payload, composer receipt, context, transaction, execution validation record, execution authorization, launch schema, authorization manifest, prompt, source input, input binding, replacement/base contracts, and supersession policy.

- [ ] **Step 5: Commit implementation evidence**

Stage only the terminal manifest, contract, and auditor after Task 2 passes. Commit as `eval: freeze r5.1-f02 terminal failure evidence`.

### Task 2: Read-only terminal auditor

**Files:**

- Create: `evals/m3/audit_forward_r5_1_f02_terminal.py`
- Test: `tests/test_audit_m3_forward_r5_1_f02_terminal.py`

**Interfaces:**

- Consumes: `audit_terminal(path, *, artifact_root=REPO_ROOT, git_root=REPO_ROOT, historical_check=None) -> dict[str, Any]`.
- Produces: deterministic receipt containing status, identities, counters, failure causality, historical immutability, empty errors/gaps/side effects, and `later_gates="NOT_RUN"`.

- [ ] **Step 1: Verify artifact identities**

For each contract-fixed binding, resolve the exact Git blob at its fixed source head, compare manifest identity, compare worktree bytes, reproduce UTF-8/JSON status, and verify canonical hash only for valid JSON objects.

- [ ] **Step 2: Verify one-shot causality**

Cross-check task ID across launch/context/transaction/manifest; verify launch and finalization counts are one; verify model-final bytes equal payload bytes; reproduce payload JSON parse failure; verify composer receipt `failed/composition/payload_invalid_json`; verify transaction `processing_failed`, composer one, validator zero, accepted false, and `composer_invocation_failed`.

- [ ] **Step 3: Verify closed state**

Reject missing required files, unknown files, bundle/outcome/validation/validator receipt presence, historical task reuse, retry/repair permissions, stale artifact hashes, predecessor authorization drift, prompt/source drift, or historical r5 diff.

- [ ] **Step 4: Keep output read-only and deterministic**

The CLI prints one compact JSON line and exits zero only for `terminal_not_accepted`. Snapshot all copied test artifacts before and after two repeated audits and require identical results and bytes.

### Task 3: Focused terminal-integrity tests and CI migration

**Files:**

- Create: `tests/test_audit_m3_forward_r5_1_f02_terminal.py`
- Modify: `.github/workflows/m1-validation.yml`

**Interfaces:**

- Consumes: terminal auditor dependency-injection boundaries and temporary artifact copies.
- Produces: at least 25 deterministic tests covering the real terminal state and every required drift/failure class.

- [ ] **Step 1: Cover the required mutations**

Test valid real terminal state; accepted/state/stage/code drift; parseable payload; payload hash drift; final/payload mismatch; composer/validator/retry/count drift; second task/final evidence; task ID mismatch; historical task reuse; historical r5 drift; authorization/prompt/source drift; stale manifest hash; missing composer/transaction; inconsistent failure causality; zero side effects; and repeatability.

- [ ] **Step 2: Run focused tests**

Run: `python -X utf8 -m unittest tests.test_audit_m3_forward_r5_1_f02_terminal -v`

Expected: every terminal test passes and no real evidence bytes change.

- [ ] **Step 3: Migrate CI current-state gate**

Add the terminal contract/auditor to `py_compile`. Remove current-worktree preparation/readiness/execution-authorization audit steps that require an empty result root and replace them with `Audit r5.1-f02 terminal one-shot evidence` running `python evals/m3/audit_forward_r5_1_f02_terminal.py`. Keep predecessor code/tests and all historical, replay, fixture, package, and cross-platform gates.

- [ ] **Step 4: Commit tests and CI**

Stage only the focused test and workflow. Commit as `test: enforce r5.1-f02 terminal evidence closure`.

### Task 4: Complete local validation and terminal documentation

**Files:**

- Create: `evals/m3/results/2026-08-07-m3.1.1-r5.1-f02-terminal-evidence-closure-validation.md`
- Modify: `STATUS.md`
- Include: `docs/superpowers/plans/2026-08-07-r5-1-f02-terminal-evidence-closure.md`

**Interfaces:**

- Consumes: committed terminal implementation/test HEADs and exact local gate outputs.
- Produces: terminal validation record and current state `TERMINAL_NOT_ACCEPTED` without claiming F02 acceptance or later gates.

- [ ] **Step 1: Run complete gates**

Run py_compile; focused tests; full unittest discovery; M1 offline and machine replays; M2/M3 fixture regeneration and zero diffs; M2 34/34 and M3 20/20 replays; package audit; standard Skill validator; historical/current r5 blocked audit; terminal audit; `git diff --check`; and historical `forward-r5` zero diff.

- [ ] **Step 2: Record exact results**

Write branch, execution evidence HEAD, terminal implementation HEAD, authorization HEAD/run, task ID, failure/counters, every local gate outcome, hashes, clean historical diff, and explicit `does_not_prove` boundaries. Do not preclaim the documentation commit SHA or remote CI.

- [ ] **Step 3: Update STATUS**

Set r5.1-f02 to `TERMINAL_NOT_ACCEPTED`; task budget `CONSUMED`; token `CONSUMED / TERMINAL`; retry `FORBIDDEN`; while preserving M3/historical r5/later-gate states.

- [ ] **Step 4: Commit documentation**

Stage only the validation record, STATUS, and this plan. Commit as `docs: record r5.1-f02 terminal not-accepted state`.

### Task 5: Final audit and stop

**Files:** None.

**Interfaces:**

- Consumes: final three commits.
- Produces: clean local handoff with `Pushed=NO`.

- [ ] **Step 1: Verify final repository state**

Run branch/HEAD/status, three-commit log, `git diff --check`, historical r5 diff, terminal audit, and remote branch absence checks.

- [ ] **Step 2: Stop at terminal closure**

Report `r5.1-f02 = TERMINAL_NOT_ACCEPTED`, `M3 = IN_PROGRESS`, aggregate and closure `NOT_RUN`, `M4 = NOT_STARTED`, and `Pushed = NO`.
