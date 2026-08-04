# Project Status

## Active milestone

`M1.1 — M1 acceptance hardening`

Status: `IN_PROGRESS`

M1 feature implementation is complete, but final acceptance remains open while validator-contract gaps are being corrected.

Blocking items:

- round-one evidence-incomplete early-stop validation;
- alternate identifier and manual-review identity handling;
- one closed FeedbackDelta, ResearchBrief, SearchPlan, and PaperMap schema;
- machine-valid forward-test artifacts;
- clean CI on the final hardening HEAD.

## M1 checklist

- [x] M0 baseline confirmed clean at root commit `5a5bcba`.
- [x] M1 implementation plan created outside the installable Skill.
- [x] Local work branch created: `codex/m1-paper-calibration`.
- [x] Adaptive research brief and query-plan contract implemented.
- [x] Verified 15–20-paper candidate-pool workflow implemented.
- [x] Eight-paper round-one evidence map and equivalent text fallback implemented.
- [x] Visible feedback delta and changed second-round search plan implemented.
- [x] Five-to-six-paper round-two output and disposition log implemented, with an honest incomplete stop when fewer than five papers have sufficient evidence.
- [x] Offline validator and adversarial fixtures pass.
- [x] Fresh-context real-search forward tests pass with current authoritative citation checks.
- [x] Standard Skill validation and final M1 scope audit pass.

## M1 result

Status: `COMPLETE`

Validated on `2026-08-04` with:

- standard Skill validator: exit `0`, `Skill is valid!`;
- M1 validator tests: 38 passed;
- adversarial fixture replay: all five exit/status pairs matched the frozen record;
- packaging audit: 106-line root Skill, zero missing or unlinked references, zero unresolved template markers;
- fresh-context Case A: 18 verified/deduplicated round-two candidates and six default recommendations;
- fresh-context Case B: 16 verified/deduplicated candidates, only three with sufficient basis, correctly stopped as `evidence_incomplete` / `WAITING_FOR_EVIDENCE_DECISION`;
- fresh-context Case C: live citation conflict blocked with `recommendation_eligible: false`.

Evidence is recorded under `evals/m1/`, including preserved failed runs and independent audits. M1 completion means the paper-calibration workflow and its stop behavior passed; it does not claim that incomplete Case B evidence became complete, that any experiment or simulation was run, or that M2 began.

## M0 checklist

- [x] D-drive project root created.
- [x] Local Git repository initialized on `main`.
- [x] Standard Skill scaffold generated.
- [x] Repository governance and product specification reviewed.
- [x] Thin root router and four core protocol references completed.
- [x] Standard Skill validation passed in UTF-8 mode: `Skill is valid!`.
- [x] Root references, placeholder count, and Skill length checks passed.
- [x] Initialization baseline prepared for one local root commit.

## Later milestones

- M2: `NOT_STARTED`
- M3: `NOT_STARTED`
- M4: `NOT_STARTED`
- M5: `NOT_STARTED`

## External state

- Git remote: `https://github.com/zxy19960316/engineering-research-copilot.git`
- Active local branch: `codex/m1-acceptance-hardening`
- External APIs/services configured: none
- RRC integration: not started
- Platform integration: not required for the local Skill competition track

## M0 result

Status: `COMPLETE`

Validated with:

```powershell
python -X utf8 C:\Users\94310\.codex\skills\.system\skill-creator\scripts\quick_validate.py D:\engineering-research-copilot\skills\engineering-research-copilot
```

The first validator attempt without UTF-8 mode did not reach Skill validation because the Windows GBK default could not decode Chinese trigger text. No Skill content was weakened; the same validator passed under Python UTF-8 mode.
