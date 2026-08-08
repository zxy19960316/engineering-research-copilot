# M2 Direction Decision and Route Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert one validated `M1_COMPLETE` evidence bundle into an auditable three-direction portfolio, block infeasible or overstated directions before ranking, and open detailed route planning only after explicit user confirmation.

**Architecture:** Keep `SKILL.md` as a thin router and make `core-direction-decision.md` the human-readable M2 contract. Add one deterministic standard-library validator that consumes an M2 bundle containing a hash-bound verbatim M1 source bundle, validates hard gates before scorecards, and enforces the confirmation transition independently of direction quality. Keep fixtures, replay records, forward prompts, and results outside the installable Skill.

**Tech Stack:** Markdown, JSON, Python 3.13 standard library, `unittest`, SHA-256 canonical JSON hashing, GitHub Actions.

## Global Constraints

- Execute only M2. Do not implement M3 method cards, runtime services, deployment, model downloads, platform integration, or RRC integration.
- Preserve every M1 candidate ID, verification status, recommendation-eligibility flag, basis level, and evidence gap; bind the exact source with `source_m1_bundle_hash`.
- Accept only `M1_COMPLETE` plus `outcome: complete` as an M2 source. Never upgrade `evidence_incomplete` to direction-ready evidence.
- Evaluate hard gates before scorecards. A failed gate makes the direction ineligible for formal ranking regardless of score.
- Keep `mechanism-plausible` out of the provisional-main position and keep `speculative` outside the formal portfolio.
- Mark every system recommendation `provisional` until the decision status is `user_confirmed`.
- Permit detailed experiment, simulation, training, download, deployment, or large-resource route content only when the selected direction is `user_confirmed`.
- Treat offline fixtures as contract evidence only; they do not prove real paper metadata, direction quality, or route feasibility.
- Keep `skills/engineering-research-copilot/SKILL.md` below 500 lines and link every loadable reference directly from it.
- Run the standard Skill validator after changes to Skill metadata or references, preserve failing evidence, stage explicit paths, and do not push without explicit user authorization.

## File Structure

- Modify `STATUS.md`: activate M2, track each acceptance gate, and retain the complete M1.2 record.
- Modify `skills/engineering-research-copilot/references/core-direction-decision.md`: define the `m2.1` bundle, state machine, hard gates, evidence-tier language, portfolio positions, axis separation, scorecard, decisive test, confirmation decision, and gated route shape.
- Modify `skills/engineering-research-copilot/SKILL.md`: route direction decisions and post-confirmation route work through the frozen M2 state contract.
- Create `skills/engineering-research-copilot/scripts/validate_m2_direction_bundle.py`: perform closed, deterministic, offline M2 validation.
- Create `tests/test_validate_m2_direction_bundle.py`: specify contract, hard-gate, tier, portfolio, source-evidence, score, decisive-test, and route-gate behavior before implementation.
- Create `evals/m2/fixtures/`: store a valid fixture plus one mutation fixture for each required adversarial case.
- Create `evals/m2/adversarial-cases.json`: map fixture names to expected status and error codes.
- Create `evals/m2/replay_offline_results.py`: replay all fixtures and compare exact expected classifications.
- Create `evals/m2/offline-results.json`: freeze replay results and state what they do and do not prove.
- Create `evals/m2/forward-cases.md`: freeze fresh-context direction-decision prompts and user-confirmation turns.
- Create `evals/m2/results/`: preserve dated forward outputs, validation records, and acceptance audits.
- Modify `.github/workflows/m1-validation.yml` or rename it to an M2-neutral workflow: compile and run both M1 and M2 validators/tests/replays without weakening M1.

---

### Task 1: Activate M2 and freeze the milestone boundary

**Files:**
- Create: `docs/superpowers/plans/2026-08-05-m2-direction-decision-and-route-gate.md`
- Modify: `STATUS.md`

**Interfaces:**
- Consumes: accepted M1.2 HEAD `f7d9009986527e72e5b60e22b43920886b0be179` and branch `codex/m2-direction-decision`.
- Produces: one active milestone, `M2`, with all implementation and acceptance boxes initially open.

- [ ] **Step 1: Verify the clean baseline**

Run `git status --short`, `git branch --show-current`, and `git rev-parse HEAD`.

Expected: no short-status entries, branch `codex/m2-direction-decision`, and HEAD `f7d9009986527e72e5b60e22b43920886b0be179`.

- [ ] **Step 2: Mark M2 `IN_PROGRESS`**

Set the active milestone to `M2 — Direction decision and route gate`, retain M1 as `COMPLETE`, add an unchecked M2 checklist for Tasks 1–8, and keep M3–M5 `NOT_STARTED`.

- [ ] **Step 3: Commit only activation artifacts**

```powershell
git add STATUS.md docs/superpowers/plans/2026-08-05-m2-direction-decision-and-route-gate.md
git commit -m "docs: activate M2 direction decision"
```

Expected: one documentation-only commit.

### Task 2: Freeze the `m2.1` direction portfolio contract

**Files:**
- Modify: `skills/engineering-research-copilot/references/core-direction-decision.md`
- Modify: `skills/engineering-research-copilot/SKILL.md`
- Modify: `STATUS.md`

**Interfaces:**
- Consumes: a verbatim M1.2 bundle with terminal state `M1_COMPLETE`.
- Produces: `direction_portfolio`, three formal `direction` objects, optional `high_risk_ideas`, `direction_decision`, and optional post-confirmation `route_output`.

- [ ] **Step 1: Define the state machine and source binding**

Use exactly this transition spine:

```text
M1_COMPLETE -> BUILDING_DIRECTION_PORTFOLIO -> CHECKING_DIRECTION_HARD_GATES
  -> DIRECTION_EVIDENCE_INCOMPLETE | DIRECTION_PORTFOLIO_READY
  -> WAITING_FOR_DIRECTION_CONFIRMATION
  -> DIRECTION_REJECTED | DIRECTION_MODIFICATION_REQUESTED | USER_CONFIRMED
  -> ROUTE_GATE_OPEN
```

Require `source_m1_bundle` to be preserved verbatim and require `source_m1_bundle_hash` to equal SHA-256 over canonical UTF-8 JSON (`sort_keys=True`, compact separators, `ensure_ascii=False`).

- [ ] **Step 2: Define the closed formal positions and tier language**

Require exactly `provisional_main`, `adjacent_alternative`, and `transfer_exploration`. Permit `established-in-target` and `transfer-supported` for the main and adjacent positions; permit `mechanism-plausible` only for transfer exploration; permit `speculative` only in at most two separate unranked high-risk ideas.

- [ ] **Step 3: Define machine-checkable decisive thresholds**

Represent every success, stop, and pivot threshold as:

```yaml
metric: ""
operator: ">=|<=|>|<"
value: 0.0
unit: ""
```

Require a non-empty falsifiable hypothesis, inputs, baseline, steps, primary metric, expected time, and resources.

- [ ] **Step 4: Validate the Skill and commit the contract**

Run the standard Skill validator and expect `Skill is valid!`, then commit the two Skill files and `STATUS.md` with `docs: define M2 direction portfolio contract`.

### Task 3: Specify M2 gate behavior with failing tests

**Files:**
- Create: `tests/test_validate_m2_direction_bundle.py`

**Interfaces:**
- Consumes: helper-built complete M1.2 and M2.1 fixture objects.
- Produces: executable expectations for `validate_bundle(bundle) -> {status, errors, evidence_gaps}` and CLI exit codes `0`, `1`, and `2`.

- [ ] **Step 1: Write a valid fixture builder**

Build three directions with distinct titles and axis changes, passing hard gates, hash-bound M1 evidence, complete transfer cases, 0–5 scores, and structured thresholds. Mark the decision `waiting_for_user_confirmation` and set `route_output` to `null`.

- [ ] **Step 2: Write the initial red tests**

Add named tests for invalid source terminal state, source-hash mismatch, unknown supporting ID, blocked M1 citation, changed basis/status, hard-gate override by high score, illegal tier/position pair, duplicate meaningful axes, missing anti-transfer factor, vague decisive test, and route content before confirmation.

- [ ] **Step 3: Run and preserve the expected red state**

Run:

```powershell
python -m unittest tests.test_validate_m2_direction_bundle -v
```

Expected: import failure for `validate_m2_direction_bundle` before implementation. Do not weaken or delete the tests.

- [ ] **Step 4: Commit the red specification**

Commit only the new test file with `test: specify M2 direction gate behavior`.

### Task 4: Implement portfolio, hard-gate, evidence-tier, and scoring validation

**Files:**
- Create: `skills/engineering-research-copilot/scripts/validate_m2_direction_bundle.py`
- Modify: `tests/test_validate_m2_direction_bundle.py`
- Modify: `STATUS.md`

**Interfaces:**
- Consumes: one decoded JSON object.
- Produces: closed output with only `status`, `errors`, and `evidence_gaps`; catches malformed shapes without traceback.

- [ ] **Step 1: Implement closed root and source validation**

Require exact M2 root fields, validate the embedded M1 bundle through `validate_m1_bundle.validate_bundle`, require `M1_COMPLETE`/`complete`, recompute the canonical hash, and build the only allowed candidate-ID ledger from M1 round two.

- [ ] **Step 2: Implement hard gates before scorecards**

Require passing gates for target evidence, data availability/generation, falsifiability, feasibility/governance, and M1 citation integrity. Require transfer-boundary coverage of concepts, units, scales, boundary conditions, assumptions, and anti-transfer factors. When any gate fails, require `scorecard: null`, `recommendation_status: excluded`, and portfolio status `evidence_incomplete`.

- [ ] **Step 3: Implement portfolio and score validation**

Require one unique direction per formal position, an exactly one-axis adjacent alternative, an at-least-two-axis transfer exploration, uniform weights totaling 100, scores from 0 through 5, and an exactly recomputed weighted total from 0 through 100.

- [ ] **Step 4: Implement decisive-test validation and closed CLI behavior**

Reject missing numeric thresholds or stop/pivot conditions. Make the CLI print one compact JSON line and return `0` for `valid`, `1` for `invalid`, and `2` for `evidence_incomplete`.

- [ ] **Step 5: Run tests and commit**

Run the M2 test module until all tests pass, then commit the validator, tests, and `STATUS.md` with `feat: validate M2 direction portfolios`.

### Task 5: Enforce explicit user confirmation before route output

**Files:**
- Modify: `skills/engineering-research-copilot/scripts/validate_m2_direction_bundle.py`
- Modify: `tests/test_validate_m2_direction_bundle.py`
- Modify: `skills/engineering-research-copilot/references/core-direction-decision.md`
- Modify: `STATUS.md`

**Interfaces:**
- Consumes: `direction_decision.status`, `selected_direction_id`, `permitted_next_actions`, and `route_output`.
- Produces: an independent route gate that cannot be opened by a high score or recommendation status.

- [ ] **Step 1: Add transition-table tests**

Test waiting, modification-requested, rejected, and user-confirmed decisions. Require `selected_direction_id: null` before confirmation; require one formal ID after confirmation; require `route_output: null` in every non-confirmed state.

- [ ] **Step 2: Reject prohibited pre-confirmation content**

Recursively reject route payload keys for full experiment steps, full simulation routes, training plans, model downloads, service deployment, and large-scale resource execution whenever status is not `user_confirmed`.

- [ ] **Step 3: Validate the post-confirmation route envelope**

Require hypothesis, baselines, controls, sequence, variables, confounders, metrics, minimum meaningful improvement, uncertainty, sensitivity, validity checks, Go/Stop/Pivot conditions, and the design-to-claim evidence chain.

- [ ] **Step 4: Run tests and commit**

Commit the validator, tests, reference, and status change with `feat: enforce user direction confirmation gate`.

### Task 6: Add adversarial fixtures and deterministic replay

**Files:**
- Create: `evals/m2/fixtures/*.json`
- Create: `evals/m2/adversarial-cases.json`
- Create: `evals/m2/replay_offline_results.py`
- Create: `evals/m2/offline-results.json`
- Modify: `.github/workflows/m1-validation.yml`
- Modify: `STATUS.md`

**Interfaces:**
- Consumes: the public M2 validator CLI.
- Produces: frozen exact fixture path, expected status, expected error code, actual status, and replay match.

- [ ] **Step 1: Materialize the required cases**

Include valid waiting, valid confirmed, hard-gate score override, speculative main, blocked citation, missing supporting ID, pre-confirmation route, renamed duplicate direction, missing anti-transfer factor, vague decisive test, and incomplete M1 source fixtures.

- [ ] **Step 2: Implement exact replay comparison**

Require each declared fixture to exist, run the validator once, and fail if status or required error code differs. Emit no network calls and no repairs.

- [ ] **Step 3: Extend CI without dropping M1 gates**

Compile the M2 validator/replayer, run all `test_*.py` modules, then run both M1 and M2 replay scripts.

- [ ] **Step 4: Freeze results and commit**

Record `proves` as structural gate behavior and `does_not_prove` as real citations, real direction merit, live transfer success, or route execution. Commit with `test: add M2 adversarial fixtures`.

### Task 7: Forward-evaluate M2 decisions with fresh context

**Files:**
- Create: `evals/m2/forward-cases.md`
- Create: `evals/m2/results/2026-08-05-*.md`
- Create: `evals/m2/results/2026-08-05-*.bundle.json`
- Create: `evals/m2/results/2026-08-05-*.validation.json`
- Modify: `STATUS.md`

**Interfaces:**
- Consumes: frozen accepted M1 bundles and frozen user confirmation/modification/rejection turns.
- Produces: provenance-separated direction-decision evidence and no real route execution.

- [ ] **Step 1: Freeze cases before execution**

Include one complete target-domain case, one cross-disciplinary transfer case, one M1 evidence-incomplete stop, and one pre-confirmation route request that must be refused.

- [ ] **Step 2: Use genuinely fresh context**

Pass only the Skill path, frozen M1 input, and case prompt. Do not expose fixture mutations, validator conclusions, or expected direction titles.

- [ ] **Step 3: Validate and preserve each outcome**

Record paper-ID lineage, evidence tiers, hard-gate results, unknowns, decisive thresholds, user-decision state, route-gate result, tools used, basis levels, validation output, and deviations. Preserve failed, incomplete, and not-run cases without relabeling.

- [ ] **Step 4: Commit forward evidence**

Commit only frozen cases, immutable results, and status evidence with `test: forward-evaluate M2 direction decisions`.

### Task 8: Close M2 only after all acceptance gates pass

**Files:**
- Modify: `STATUS.md`
- Create: `evals/m2/results/2026-08-05-m2.1-final-validation.md`

**Interfaces:**
- Consumes: standard Skill validation, all M1/M2 unit tests, fixture replay, fresh-context results, packaging audit, and scope audit.
- Produces: M2 `COMPLETE` or an honest `IN_PROGRESS`/`BLOCKED` record.

- [ ] **Step 1: Run all local gates**

Run Python compilation, `python -m unittest discover -s tests -p "test_*.py" -v`, M1 replay, M2 replay, and the standard Skill validator. Record exact counts and exit codes.

- [ ] **Step 2: Audit package and scope**

Require `SKILL.md` below 500 lines, every reference link present, no unlinked loadable reference, no unresolved template marker, no network call, and no M3/runtime/deployment/RRC additions.

- [ ] **Step 3: Audit semantic acceptance**

Confirm that transfer-supported does not require direct target precedent, speculative analogies never become formal recommendations, every failed hard gate is excluded before ranking, M1 lineage remains hash-bound and unchanged, and every pre-confirmation detailed-route attempt is rejected.

- [ ] **Step 4: Update status and commit**

Set M2 to `COMPLETE` only if every required offline and fresh-context gate is evidenced. Otherwise keep it `IN_PROGRESS` and list every failed or not-run gate. Commit with `docs: close M2 acceptance` only when complete.

## Self-Review Record

- Spec coverage: Tasks 2–5 cover the full state machine, three-direction portfolio, evidence tiers, hard gates, scorecards, decisive tests, M1 lineage, and user confirmation gate. Tasks 6–8 cover adversarial, forward, and closure evidence.
- Boundary check: The plan defines route output validation after confirmation but does not generate or execute a route, download a model, start a service, or begin M3.
- Placeholder scan: The plan contains no unresolved implementation marker or omitted acceptance command.
- Type consistency: `m2.1`, formal positions, evidence tiers, decision states, validator statuses, and CLI exit codes are consistent across tasks.
- Evidence integrity: Offline fixtures remain explicitly synthetic; M1 incomplete and blocked states stay non-successful and cannot be upgraded by M2 scoring.
