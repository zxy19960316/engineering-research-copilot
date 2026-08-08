# F04 Confirmation And M3 R3 Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bind the user's exact `F04-D01` choice into an immutable M2.1.1 confirmation artifact, admit that independent non-nuclear lineage into M3 r3, consume five authorized one-shot fresh contexts only after every input is eligible, and close M3 only if every local and exact-HEAD remote gate succeeds.

**Architecture:** Preserve the independent F04 branch as the construction context and use the r3 branch as the distinct review and acceptance context. Confirmation creates a route-free successor of the pre-confirmation bundle; r3 references the accepted successor by raw and canonical hashes, freezes only eligible prompts, and preserves every fresh-context result without repair or retry. M4 and M5 remain outside this plan until M3 is formally closed.

**Tech Stack:** Python 3.12 standard library, UTF-8 JSON without BOM, SHA-256 raw and canonical hashes, existing M1/M2/M3 validators, `unittest`, PowerShell, Git, and GitHub Actions after an authorized push.

## Global Constraints

- Keep `evals/m3/results/forward-r2/` and `evals/m3/forward-inputs-r2/` byte-identical to the r2 freeze diagnostic.
- Preserve F04 construction commits `45c523a` and `c960b81` as independent commits; do not amend, squash, or rebase them.
- Bind the exact user excerpt `Confirm F04 direction F04-D01` from Codex task `019fd4f7-e1c4-7fd1-9799-786f62fda8e6`, message `item-46`.
- Require pre-confirmation canonical SHA-256 `884e80387776ecdf3963a3db79c1bec3eb8fe48f65f17c0fc8852d61b54f8678` and direction excerpt SHA-256 `1f81072903df3afa27d49bd06c17209141014ac8ea5026973a8bc7bd8e69b310` before confirmation.
- Keep the confirmed F04 `route_output` exactly `null`; confirmation admits M3 coaching but does not authorize or execute a research route.
- Consume no fresh context until F01-F05 are all `eligible`, their immutable inputs and prompts are frozen, and the acceptance manifest records zero prior r3 context consumption.
- Run each fresh case exactly once. Preserve invalid JSON, invalid bundles, unexpected blocks, and missing outputs without cleanup, extraction, repair, or retry.
- Keep M3 `IN_PROGRESS` and M4 `NOT_STARTED` unless all five results and every closure gate succeed.
- Do not start M4 or M5 implementation in this plan. After M3 closure, write a separate M4 plan; after M4 acceptance, write a separate M5 plan.
- Do not create a PR, merge, tag, or change `main`. Push only the r3 branch after the local closure candidate is green.

---

### Task 1: Commit The Active-Milestone Execution Plan

**Files:**
- Create: `docs/superpowers/plans/2026-08-06-f04-confirmation-r3-closure.md`

**Interfaces:**
- Consumes: r3 HEAD `99d5c03504ae662577f182b4a92fd41a6a766041` and F04 HEAD `c960b81`.
- Produces: one reviewable scope boundary before any confirmation or acceptance artifact changes.

- [ ] **Step 1: Verify both worktrees and ancestry**

Run:

```powershell
git -C D:\engineering-research-copilot status --short --branch
git -C C:\Users\94310\.codex\worktrees\7452\engineering-research-copilot status --short --branch
git -C D:\engineering-research-copilot merge-base codex/m3.1.1-r3-acceptance-repair codex/f04-upstream-evidence
```

Expected: both worktrees are clean and the merge base is `99d5c03504ae662577f182b4a92fd41a6a766041`.

- [ ] **Step 2: Commit only the plan**

```powershell
git add docs/superpowers/plans/2026-08-06-f04-confirmation-r3-closure.md
git diff --cached --name-status
git commit -m "docs: plan F04 confirmation and M3 r3 closure"
```

Expected: one commit containing only this plan.

### Task 2: Specify F04-D01 Confirmation Binding Red-First

**Files:**
- Create: `evals/f04-upstream/test_confirm_f04_d01.py`
- Create: `evals/f04-upstream/confirm_f04_d01.py`

**Interfaces:**
- Consumes: `evals/f04-upstream/m2/f04-m2-direction-bundle.json` in the exact waiting state.
- Produces: a pure `build_confirmed(draft: dict) -> tuple[dict, dict]` transform plus a CLI that writes confirmation artifacts only after every hash and state precondition passes.

- [ ] **Step 1: Write the failing contract tests**

The test module must load `confirm_f04_d01.py` by absolute module path and assert:

```python
confirmed, event = module.build_confirmed(draft)
self.assertEqual(confirmed["direction_decision"]["selected_direction_id"], "F04-D01")
self.assertEqual(confirmed["direction_decision"]["status"], "user_confirmed")
self.assertEqual(event["actor_role"], "user")
self.assertEqual(event["source_message_excerpt"], "Confirm F04 direction F04-D01")
self.assertEqual(event["previous_bundle_hash"], EXPECTED_PRECONFIRMATION_HASH)
self.assertIsNone(confirmed["route_output"])
self.assertEqual(draft["direction_decision"]["selected_direction_id"], None)
```

It must also mutate a deep copy of the draft and assert `build_confirmed` raises `ValueError` for a changed pre-confirmation bundle, a non-null route, a missing `F04-D01`, or a changed selected-direction excerpt hash.

- [ ] **Step 2: Prove red and commit the specification**

```powershell
python -X utf8 evals\f04-upstream\test_confirm_f04_d01.py -v
git add evals/f04-upstream/test_confirm_f04_d01.py
git commit -m "test: define F04-D01 confirmation binding"
```

Expected: tests fail because `confirm_f04_d01.py` does not exist.

### Task 3: Create And Validate The Immutable F04 Confirmation Successor

**Files:**
- Create: `evals/f04-upstream/confirm_f04_d01.py`
- Create: `evals/f04-upstream/m2/f04-m2-confirmed.bundle.json`
- Create: `evals/f04-upstream/m2/f04-m2-confirmed.validation.json`
- Create: `evals/f04-upstream/m2/f04-m2-confirmed.manifest.json`
- Create: `evals/f04-upstream/m2/f04-m2-confirmed.confirmation.md`

**Interfaces:**
- `canonical_sha256(value: Any) -> str` uses sorted compact UTF-8 JSON with `ensure_ascii=False` and `allow_nan=False`.
- `selected_direction_excerpt(direction: dict) -> str` must use the validator-defined direction excerpt representation already stored in the bundle; it must not invent a new summary.
- `main() -> int` refuses existing outputs, invokes `validate_m2_direction_bundle.py` exactly once, and writes evidence only when validation is `valid` with no errors or evidence gaps.

- [ ] **Step 1: Implement the exact confirmation event**

The produced event must be exactly:

```python
confirmation_event = {
    "actor_role": "user",
    "selected_direction_id": "F04-D01",
    "source_message_id": "codex-task:019fd4f7-e1c4-7fd1-9799-786f62fda8e6:item-46",
    "source_message_excerpt": "Confirm F04 direction F04-D01",
    "source_message_sha256": hashlib.sha256(
        b"Confirm F04 direction F04-D01"
    ).hexdigest(),
    "previous_bundle_hash": canonical_sha256(draft),
}
```

The successor decision must be exactly:

```python
confirmed["direction_decision"] = {
    "selected_direction_id": "F04-D01",
    "status": "user_confirmed",
    "permitted_next_actions": ["modify", "reject", "generate_route"],
    "confirmation_event": confirmation_event,
}
confirmed["route_output"] = None
```

- [ ] **Step 2: Run focused tests and generate once**

```powershell
python -X utf8 evals\f04-upstream\test_confirm_f04_d01.py -v
python -X utf8 evals\f04-upstream\confirm_f04_d01.py
python -X utf8 skills\engineering-research-copilot\scripts\validate_m2_direction_bundle.py evals\f04-upstream\m2\f04-m2-confirmed.bundle.json
```

Expected: focused tests pass; generation succeeds once; the independent check returns `status=valid`, `errors=[]`, and `evidence_gaps=[]`. The generation-recorded validator invocation remains the sole invocation claimed by its receipt; the independent check is reported separately and is not relabelled as construction evidence.

- [ ] **Step 3: Commit explicit paths**

```powershell
git add evals/f04-upstream/confirm_f04_d01.py evals/f04-upstream/test_confirm_f04_d01.py evals/f04-upstream/m2/f04-m2-confirmed.bundle.json evals/f04-upstream/m2/f04-m2-confirmed.validation.json evals/f04-upstream/m2/f04-m2-confirmed.manifest.json evals/f04-upstream/m2/f04-m2-confirmed.confirmation.md
git diff --cached --name-status
git commit -m "eval: bind confirmed F04-D01 direction"
```

### Task 4: Integrate F04 Evidence Without Rewriting Its Commits

**Files:**
- Add to r3 by cherry-pick: every path introduced by `45c523a`, `c960b81`, and the two confirmation commits.

**Interfaces:**
- Consumes: the clean F04 branch with four commits after `99d5c03`.
- Produces: four independently reviewable cherry-picked commits with the same file bytes and semantic boundaries in r3; record both the original F04 source SHAs and the new r3 cherry-pick SHAs because their parents differ. No r2 path changes.

- [ ] **Step 1: Verify the exact commit list and byte scope**

```powershell
git log --reverse --format=%H 99d5c03..codex/f04-upstream-evidence
git diff --name-status 99d5c03..codex/f04-upstream-evidence
```

Expected: only the F04 plan, `evals/f04-upstream/` evidence, test, and confirmation tool appear.

- [ ] **Step 2: Cherry-pick in order**

```powershell
$f04Commits = @(git log --reverse --format=%H 99d5c03..codex/f04-upstream-evidence)
if ($f04Commits.Count -ne 4) { throw "unexpected F04 commit count" }
if ($f04Commits[0] -ne "45c523a93fbf82aea3b8e6d2704633f55a933745") { throw "unexpected F04 M1 commit" }
if ($f04Commits[1] -ne "c960b8139627f7b18fda3095aaa8bfee8020661c") { throw "unexpected F04 M2 commit" }
git cherry-pick $f04Commits
```

The two confirmation commit hashes are resolved only from the audited four-commit ancestry. Do not use ranges, amend, or squash.

- [ ] **Step 3: Recheck r2 freeze bytes**

Run the existing r2 freeze comparison against `evals/m3/results/forward-r3/r2-freeze-diagnostic.json`. Any mismatch aborts the sequence before F04 eligibility preparation.

### Task 5: Prepare And Audit The F04 R3 Input

**Files:**
- Create: `evals/m3/forward-inputs-r3/f04-upstream/acceptance-manifest.json`
- Modify: `evals/m3/forward-inputs-r3/m3-f04.m2-validation.json`
- Modify: `evals/m3/forward-inputs-r3/m3-f04.eligibility.json`
- Modify: `evals/m3/forward-inputs-r3/manifest.json`

**Interfaces:**
- Consumes: the confirmed F04 bundle, M1 calibration bundle, upstream M1/M2 receipts, and their raw/canonical hashes.
- Produces: one M2 validation receipt with `invocation_count=1`, construction context `codex-task:019fd4f7-e1c4-7fd1-9799-786f62fda8e6`, review context `codex-task:019fd467-790b-7551-9157-ddd3b2222ca1`, and one case eligibility receipt.

- [ ] **Step 1: Run one M2 acceptance invocation**

```powershell
python -X utf8 skills\engineering-research-copilot\scripts\validate_m2_direction_bundle.py evals\f04-upstream\m2\f04-m2-confirmed.bundle.json
```

Record the exact compact result and canonical input hash in `m3-f04.m2-validation.json`; do not reuse a fixture or an earlier provisional receipt.

- [ ] **Step 2: Run the case auditor**

```powershell
python -X utf8 evals\m3\audit_forward_case_input.py m3-f04 evals\f04-upstream\m2\f04-m2-confirmed.bundle.json evals\m3\forward-inputs-r3\m3-f04.m2-validation.json
```

Expected exactly: `case_id=m3-f04`, `status=eligible`, `coaching_mode=bounded`, `errors=[]`, `evidence_gaps=[]`.

- [ ] **Step 3: Update the r3 manifest and commit**

Change the manifest status from `blocked_by_f04_upstream_input` to `ready_to_freeze_prompts`, bind the F04 paths and hashes, keep `fresh_contexts_consumed=0`, and keep `prompts_frozen=false`.

```powershell
git add evals/m3/forward-inputs-r3
git commit -m "eval: admit independently confirmed F04 input"
```

### Task 6: Freeze Five Eligible Inputs And Prompts

**Files:**
- Create: `evals/m3/forward-cases-r3.md`
- Create: `evals/m3/results/forward-r3/prompts/m3-f01.prompt.txt`
- Create: `evals/m3/results/forward-r3/prompts/m3-f02.prompt.txt`
- Create: `evals/m3/results/forward-r3/prompts/m3-f03.prompt.txt`
- Create: `evals/m3/results/forward-r3/prompts/m3-f04.prompt.txt`
- Create: `evals/m3/results/forward-r3/prompts/m3-f05.prompt.txt`
- Create: `evals/m3/results/forward-r3/acceptance-manifest.json`
- Modify: `evals/m3/forward-inputs-r3/manifest.json`

**Interfaces:**
- Consumes: five `eligible` receipts and immutable input hashes.
- Produces: five prompts with only the named Skill/reference paths, one input path/hash, one output contract, and one exact composer/outcome-validator command.

- [ ] **Step 1: Re-run all five eligibility audits before writing prompts**

Use each manifest case's immutable input and M2 receipt. Abort if any status differs from `eligible`.

- [ ] **Step 2: Freeze the outcome matrix**

Record:

```text
m3-f01 -> bundle, bounded, accepted
m3-f02 -> bundle, route_specific, accepted
m3-f03 -> blocked, unsupported_approved_constraint_change_provenance, accepted_expected_block
m3-f04 -> bundle, bounded, accepted
m3-f05 -> bundle, route_specific, accepted
```

Each prompt must prohibit retries, route execution, empirical claims, hidden file access, and JSON repair. F04 must require the experiment/measurement/UQ card family; F05 must require the nuclear overlay and four recorded model boundaries.

- [ ] **Step 3: Hash inputs/prompts and commit**

Set `prompts_frozen=true` and keep `fresh_contexts_consumed=0`.

```powershell
git add evals/m3/forward-cases-r3.md evals/m3/forward-inputs-r3/manifest.json evals/m3/results/forward-r3/prompts evals/m3/results/forward-r3/acceptance-manifest.json
git commit -m "eval: freeze M3.1.1 r3 prompts and inputs"
```

### Task 7: Execute Five Authorized Fresh Contexts Exactly Once

**Files:**
- Create under `evals/m3/results/forward-r3/`: one context record, raw final output, payload or blocked outcome, validation receipt, and case manifest for each F01-F05.
- Modify: `evals/m3/results/forward-r3/acceptance-manifest.json`

**Interfaces:**
- Consumes: only each frozen prompt, allowed Skill references, and the named immutable input.
- Produces: exactly one finalization and one `run_forward_outcome_validation_once.py` invocation per case.

- [ ] **Step 1: Dispatch each frozen case to a genuinely fresh context**

Do not include this task's conversation, r2 outputs, other case outputs, tests, fixtures, or acceptance expectations beyond the case's own frozen prompt.

- [ ] **Step 2: Preserve output bytes and validate once**

For every case run:

```powershell
$caseRuns = @(
  @{ id="m3-f01"; input="evals/m3/forward-inputs-r2/m3-f01-bounded-confirmed.bundle.json" },
  @{ id="m3-f02"; input="evals/m3/forward-inputs-r2/m3-f02-route-compatible.bundle.json" },
  @{ id="m3-f03"; input="evals/m3/forward-inputs-r2/m3-f03-approved-change.bundle.json" },
  @{ id="m3-f04"; input="evals/f04-upstream/m2/f04-m2-confirmed.bundle.json" },
  @{ id="m3-f05"; input="evals/m3/forward-inputs-r2/m3-f02-route-compatible.bundle.json" }
)
foreach ($case in $caseRuns) {
  python -X utf8 evals/m3/run_forward_outcome_validation_once.py `
    $case.id `
    $case.input `
    "evals/m3/results/forward-r3/$($case.id).outcome.json" `
    "evals/m3/results/forward-r3/$($case.id).one-shot-receipt.json"
  if ($LASTEXITCODE -ne 0) { throw "$($case.id) outcome validation failed" }
}
```

The raw outcome files must already be the immutable bytes finalized by their corresponding fresh contexts. Never rerun a failed case.

- [ ] **Step 3: Commit observed evidence**

Update each case independently as `accepted`, `accepted_expected_block`, or `invalid`; set `fresh_contexts_consumed=5` only after all five contexts have finalized.

```powershell
git add evals/m3/results/forward-r3
git commit -m "eval: record one-shot M3.1.1 r3 outcomes"
```

### Task 8: Close M3 Only If Every Gate Is Green

**Files:**
- Create: `evals/m3/results/2026-08-06-m3.1.1-r3-final-validation.md`
- Modify: `STATUS.md`

**Interfaces:**
- Consumes: five accepted case outcomes, deterministic replays, package audit, full tests, Skill validation, clean tree, and exact r2 byte preservation.
- Produces: a local closure candidate; remote closure is valid only when GitHub Actions reports success for that exact candidate HEAD.

- [ ] **Step 1: Run deterministic closure gates**

```powershell
C:\Users\94310\AppData\Local\Programs\Python\Python312\python.exe -X utf8 -m unittest discover -s tests -v
C:\Users\94310\AppData\Local\Programs\Python\Python312\python.exe -X utf8 evals\m1\replay_offline_results.py
C:\Users\94310\AppData\Local\Programs\Python\Python312\python.exe -X utf8 evals\m2\replay_offline_results.py
C:\Users\94310\AppData\Local\Programs\Python\Python312\python.exe -X utf8 evals\m3\replay_offline_results.py
C:\Users\94310\AppData\Local\Programs\Python\Python312\python.exe -X utf8 evals\m3\audit_skill_package.py
C:\Users\94310\AppData\Local\Programs\Python\Python312\python.exe -X utf8 C:\Users\94310\.codex\skills\.system\skill-creator\scripts\quick_validate.py D:\engineering-research-copilot\skills\engineering-research-copilot
git diff --check
```

Any failure keeps M3 `IN_PROGRESS` and M4 `NOT_STARTED`.

- [ ] **Step 2: Commit the local closure candidate**

Only if every gate and all five outcomes pass, record exact commands, exits, counts, hashes, and limitations; update M3 to a local closure candidate without claiming remote CI.

```powershell
git add STATUS.md evals/m3/results/2026-08-06-m3.1.1-r3-final-validation.md
git commit -m "docs: record M3.1.1 r3 local closure candidate"
```

- [ ] **Step 3: Push and verify the exact HEAD**

```powershell
git push -u origin codex/m3.1.1-r3-acceptance-repair
gh run list --branch codex/m3.1.1-r3-acceptance-repair --limit 5
```

Require the successful run's `headSha` to equal `git rev-parse HEAD`. If it fails or points to an older SHA, do not mark M3 complete and do not start M4.

## Self-Review Checklist

- [ ] The plan changes only the active M3 acceptance path and its independent F04 prerequisite.
- [ ] F04's exact user phrase, direction ID, selected-direction excerpt hash, and pre-confirmation hash are all bound.
- [ ] Confirmed F04 remains route-free and makes no empirical or operational claim.
- [ ] Construction and review contexts differ.
- [ ] All five prompts are frozen only after all five inputs are eligible.
- [ ] Fresh outcomes are never repaired or retried.
- [ ] r2 remains byte-identical and visible as failed historical evidence.
- [ ] M4 and M5 remain untouched until their predecessor milestones formally close.
