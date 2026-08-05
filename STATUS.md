# Project Status

## Active milestone

`M2 — Direction decision and route gate`

Status: `IN_PROGRESS`

Target contract: `m2.1`

Started from accepted M1.2 HEAD `f7d9009986527e72e5b60e22b43920886b0be179` on branch `codex/m2-direction-decision`.

M2 converts one hash-bound `M1_COMPLETE` evidence bundle into an auditable direction portfolio. Detailed experiment, simulation, training, download, deployment, or large-resource route content remains blocked until the selected direction status is `user_confirmed`.

## M2 checklist

- [x] M1.2 baseline confirmed complete and the M2 work branch confirmed clean.
- [x] M2 implementation plan created outside the installable Skill.
- [x] `m2.1` direction portfolio and source-evidence lineage contract frozen.
- [x] Hard-gate, evidence-tier, formal-position, axis-separation, scorecard, and decisive-test behavior specified red-first.
- [x] Offline M2 direction bundle validator implemented.
- [x] User confirmation gate enforced for detailed route content.
- [x] Adversarial fixtures and deterministic replay pass.
- [x] Fresh-context direction-decision forward evaluation passes or preserves honest incomplete/blocked evidence.
- [ ] Standard Skill validation, full unit suite, package audit, and final M2 scope audit pass.

## M1 acceptance baseline

Status: `COMPLETE`

Acceptance revision: `m1.2`

Validated by:

- clean local validation with 108 passing tests;
- successful first-round exact-HEAD GitHub Actions run `30965919907` on `2842b6bc99f48ea17561b67a97205e271a370e4d`;
- successful closure exact-HEAD GitHub Actions run `30966375373` on `37ac4617fa5c506f2d087628b61570cef9c4cdf9`;
- complete two-round machine-valid Case A;
- second-round `evidence_incomplete` machine-valid Case B;
- citation-conflict blocking gate Case C;
- DOI and alternate-ID identity tests;
- round-one and round-two terminal-state tests.

Acceptance evidence:

- pre-push executable-input HEAD: `e234e90364ace4aa203716575ab37a0130b4d322`;
- first remote-CI input HEAD: `2842b6bc99f48ea17561b67a97205e271a370e4d`;
- GitHub Actions workflow/job: `M1 Validation` run `30965919907`, job `92179712580`, conclusion `success`;
- closure commit: `37ac4617fa5c506f2d087628b61570cef9c4cdf9`;
- closure GitHub Actions workflow/job: `M1 Validation` run `30966375373`, job `92181118237`, conclusion `success`;
- Python compilation: exit `0`;
- unit tests: 108 passed;
- frozen fixture replay: `valid`, zero mismatches;
- machine artifacts: Case A `valid`, Case B `evidence_incomplete`, Case C blocking gate `valid`, zero mismatches;
- standard Skill validator: exit `0`, `Skill is valid!`;
- root Skill: 106 lines;
- closure record: `evals/m1/results/2026-08-04-m1.2-final-validation.md`.

Closure commit `37ac4617fa5c506f2d087628b61570cef9c4cdf9` was successfully validated by exact-HEAD `M1 Validation` run `30966375373`. This post-CI evidence-record commit cannot embed its own SHA or pre-claim its own final exact-HEAD run; root will push it and confirm that run externally. M1.2 completion does not claim that Case B became complete or that Case C's citation conflict was resolved.

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

- M2: `IN_PROGRESS`
- M3: `NOT_STARTED`
- M4: `NOT_STARTED`
- M5: `NOT_STARTED`

## External state

- Git remote: `https://github.com/zxy19960316/engineering-research-copilot.git`
- Active local branch: `codex/m2-direction-decision`
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
