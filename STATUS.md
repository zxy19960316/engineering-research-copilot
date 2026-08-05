# Project Status

## Active milestone

`M3 — Engineering method cards`

Status: `IN_PROGRESS`

Acceptance revision: `m3.1`

Acceptance input HEAD: `d0f5e9017044ba35d0ac4559591028228f3b22d8`

Baseline Actions run: `30977286846` (`push`, exact HEAD, `success`).

M3 started from the exact accepted M2.1.1 closure HEAD on branch `codex/m3-engineering-method-cards`; it was not created from the older `origin/main` HEAD `f7d9009986527e72e5b60e22b43920886b0be179`. M3 is limited to offline, evidence-grounded method coaching and its deterministic validation artifacts. It does not authorize experiment or route execution, training, downloads, services, deployment, uploads, RRC integration, or platform integration.

Before route-specific method-card instantiation, M3 must validate the complete M2.1.1 bundle, require `user_confirmed`, recompute the selected-direction binding, reject every non-empty `approved_constraint_changes` list with `unsupported_approved_constraint_change_provenance`, and rederive claim metrics, claim-specific preconditions, resource ceilings, and actual Go/Stop/Pivot coverage from upstream structures.

## M3 checklist

- [x] Exact accepted M2.1.1 input HEAD, clean worktree, remote branch, and exact-HEAD Actions success confirmed.
- [x] Local branch `codex/m3-engineering-method-cards` created directly from `d0f5e9017044ba35d0ac4559591028228f3b22d8`.
- [x] M3 implementation plan created outside the installable Skill.
- [x] M3 input compatibility and fail-closed provenance gates specified red-first in 33 test methods; collection stops solely because the M3 validator module is intentionally absent.
- [x] Closed `m3.1` method-card, typed source-ledger, resource-bound, upstream-threshold-bound, and nuclear-overlay schema implemented offline; 57 focused M3 validator tests pass.
- [x] Six general method families and the nuclear engineering × machine learning overlay implemented as directly linked one-level references; the root Skill links all eight M3 references.
- [x] Sixteen M3 adversarial fixtures, including two unbound-threshold cases, deterministic regeneration, strict manifest replay, and frozen replay pass without changing accepted M1/M2 evidence.
- [x] Existing M1 and M2 validation remain green; the tracked M3 package audit enforces 13 unique rendered Markdown links to 13 readable regular top-level references, with no dangling, unlinked, duplicate, nested, linked/reparse, forbidden, or marker violations.
- [x] M3 implementation and local validation refreshed on input HEAD `4a31fae47d85a1ce70ea944db38fb2ebfa7c4eb6`: 247 unit tests, 34/34 M2 replay cases, 16/16 M3 replay cases, byte-stable fixture regeneration, standard Skill validation, and the tracked package audit all passed on first attempt.
- [ ] Required genuinely fresh-context M3 forward evaluation remains `NOT_RUN`; the independent accepted upstream inputs listed in `evals/m3/results/2026-08-05-forward-evaluation-not-run.md` are unavailable.
- [ ] Exact-closure-HEAD GitHub Actions remains `NOT_RUN — push not authorized`; baseline run `30977286846` is not M3 implementation CI.

## M3 local result

Status: `LOCAL_IMPLEMENTATION_AND_VALIDATION_COMPLETE; ACCEPTANCE_PENDING`

M3.1 passed all local implementation, regression, deterministic replay, standard Skill validation, and package-audit gates on `2026-08-05`. The local record is `evals/m3/results/2026-08-05-m3.1-final-validation.md`. M3 remains `IN_PROGRESS`, because fresh-context forward evaluation and exact-closure-HEAD remote CI are both honestly preserved as `NOT_RUN`; no offline fixture or baseline M2.1.1 Actions run is relabeled as those missing gates.

This local result does not claim a real experiment, simulation, training run, download, deployment, route execution, target-domain transfer result, operational readiness, or nuclear safety conclusion.

## M2 checklist

- [x] Accepted M2 input HEAD, clean worktree, and exact-HEAD Actions success confirmed.
- [x] M2.1.1 implementation plan created outside the installable Skill.
- [x] `m2.1.1` provenance and semantic gates specified red-first.
- [x] Confirmation and route provenance hash-bound.
- [x] Claim coverage, preprint support, and data-precondition policies enforced.
- [x] Direction axes derived and scorecard rationales hardened.
- [x] M2.1.1 adversarial fixtures generated and replayed deterministically.
- [x] Case A repaired and Case F audited without route execution.
- [x] Local validation and acceptance record pass; implementation HEAD `94a41f423d12630c1058451da2d84b278a5285cf` passed exact-HEAD GitHub Actions run `30977203464`.

### Accepted M2.1 baseline

- [x] M1.2 baseline confirmed complete and the M2 work branch confirmed clean.
- [x] M2 implementation plan created outside the installable Skill.
- [x] `m2.1` direction portfolio and source-evidence lineage contract frozen.
- [x] Hard-gate, evidence-tier, formal-position, axis-separation, scorecard, and decisive-test behavior specified red-first.
- [x] Offline M2 direction bundle validator implemented.
- [x] User confirmation gate enforced for detailed route content.
- [x] Adversarial fixtures and deterministic replay pass.
- [x] Fresh-context direction-decision forward evaluation passes or preserves honest incomplete/blocked evidence.
- [x] Standard Skill validation, full unit suite, package audit, and final M2 scope audit pass.

## M2 result

Status: `M2.1 COMPLETE; M2.1.1 COMPLETE`

M2.1.1 local acceptance passed on `2026-08-05` from implementation HEAD `b66bb5122c11730377ee587d59df3717a37e90ba` with 163 unit tests, both unchanged M1 replays, 34/34 M2.1.1 adversarial cases, byte-stable fixture regeneration, the local standard Skill validator, a repository package audit, revised Case A, and independent Case F. The final implementation-and-evidence HEAD `94a41f423d12630c1058451da2d84b278a5285cf` passed exact-HEAD GitHub Actions run `30977203464`; M2.1.1 is complete and M3 remains `NOT_STARTED`. See `evals/m2/results/2026-08-05-m2.1.1-final-validation.md`.

Validated on `2026-08-05` from acceptance input HEAD `aec8531fa0565e87651b87761717158994afaec1` with:

- Python compilation: exit `0`;
- unit tests: 138 passed;
- M1 frozen replay and machine-artifact replay: valid with the preserved Case B `evidence_incomplete` outcome;
- M2 adversarial replay: 12/12 exact matches;
- standard Skill validator: exit `0`, `Skill is valid!`;
- package audit: 108-line root Skill, five linked references, zero missing or unlinked references, zero unresolved template markers;
- fresh-context Case A/B/D/E bundles: `valid`, zero errors and gaps;
- fresh-context Case C: correctly stopped at M1 `evidence_incomplete`, expected exit `2`;
- confirmation gate: pre-confirmation route refused; explicit D1 confirmation opened the gate without generating or executing a route;
- final record: `evals/m2/results/2026-08-05-m2.1-final-validation.md`.

The accepted M2 closure HEAD `f0a44890fb9e3244ad86fb60f01065715ddb4de0` later passed exact-HEAD GitHub Actions run `30972309423`, job `92199125940`. This supersedes the earlier pre-push remote-not-run state without erasing that historical sequence. M2 completion does not claim empirical transfer success, experiment or simulation performance, model training, download, deployment, operational nuclear safety, or M3 work.

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

- M2: `M2.1 COMPLETE; M2.1.1 COMPLETE`
- M3: `IN_PROGRESS`
- M4: `NOT_STARTED`
- M5: `NOT_STARTED`

## External state

- Git remote: `https://github.com/zxy19960316/engineering-research-copilot.git`
- Active local branch: `codex/m3-engineering-method-cards`
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
