# Project Status

## Active milestone

`M3 — Engineering method cards`

Status: `IN_PROGRESS`

Acceptance revision: `m3.1.1`

Input HEAD: `b0a1b9e41e85a1b57c80a8b571bac9ca01c88778`

M4: `NOT_STARTED`

M3.1 implementation is complete. M3.1.1 acceptance repair is in progress on branch `codex/m3.1.1-r3-acceptance-repair`, created directly from immutable r2 evidence HEAD `6ec576a47a804300e2a95e6bddfff1d00c5270a3`. R2 remains failed historical evidence and is not being retried or edited in place; r3 may supersede it for acceptance only after the revised contracts and all fresh cases pass. M3 remains limited to offline, evidence-grounded method coaching and deterministic validation artifacts. It does not authorize experiment or route execution, training, downloads, services, deployment, uploads, RRC integration, or platform integration.

Before route-specific method-card instantiation, M3.1.1 must validate the complete M2.1.1 bundle, require `user_confirmed`, recompute the selected-direction binding, reject every non-empty `approved_constraint_changes` list with `unsupported_approved_constraint_change_provenance`, and rederive claim metrics, claim-specific preconditions, resource ceilings, actual Go/Stop/Pivot coverage, safety-source eligibility, and method-card internal bindings from upstream structures.

## M3 checklist

- [x] Existing M3.1 implementation, references, 57 focused validator tests, 16 offline cases, local validation record, and package audit are preserved as historical evidence.
- [x] M3.1.1 branch `codex/m3.1.1-acceptance-hardening` created directly from exact input HEAD `b0a1b9e41e85a1b57c80a8b571bac9ca01c88778` with a clean worktree.
- [x] M3.1.1 acceptance plan created outside the installable Skill.
- [x] Safety-source, non-negative-resource, and method-card claim/metric binding gates implemented; focused validator suite passes 62/62.
- [x] Twenty deterministic M3 adversarial cases regenerated and replayed byte-stably.
- [x] Independent M2 input preparation preserved in the r2 worktree: F01/F02/F03/F05 M2-valid artifacts; F04 explicit NOT_RUN with its non-nuclear prerequisite gap.
- [x] R2 inputs, prompts, outputs, validation receipts, and context records frozen by raw SHA-256 and Git blob identity in `evals/m3/results/forward-r3/r2-freeze-diagnostic.json`; F01 JSON syntax coordinates and F05 missing-output evidence remain explicit.
- [x] R3 deterministic artifact composer, case-level eligibility auditor, expected-blocked F03 forward outcome, and exact one-shot outcome evidence runner implemented red-first; the full suite passes 314/314.
- [x] R3 F01/F02/F03 and revised route-specific F05 inputs are eligible; F05 reuses the route-compatible F02 lineage and the old route-free r2 F05 remains ineligible for the revised case.
- [x] Independent non-nuclear F04 upstream lineage reaches new M1_COMPLETE, valid provisional M2.1.1, explicit user confirmation, independent acceptance, and eligible case status before any new fresh-context run.
- [ ] Five genuinely fresh-context forward evaluations completed with accepted validator results. R3 consumed all five exactly once without repair or retry: F05 was accepted; F01, F02, F03, and F04 remain invalid. F03's model final expressed the expected blocked terminal code, but the sole validator invocation used a nonexistent source path and the resulting invalid receipt is preserved.
- [x] Complete local regression, package audit, Skill validation, and replay gates pass; the input HEAD `02d791275e6a8da16655a57aec5188d606c49357` passed GitHub Actions run `31006161680` on `2026-08-05`. This is historical implementation/replay CI; the r2 forward-input audit is `evidence_incomplete` for F04 and the fresh acceptance audit is invalid, so no closure CI is claimed.

## M3 local result

Status: `M3.1.1 R3_ACCEPTANCE_NOT_ACCEPTED; R2_ACCEPTANCE_BLOCKED`

Historical M3.1 local implementation and validation passed on `2026-08-05`; the M3.1.1 local hardening and deterministic replay also pass. Input HEAD `02d791275e6a8da16655a57aec5188d606c49357` passed GitHub Actions run `31006161680`, which covered the then-current implementation, replay, and package gates. That run does not close the forward acceptance repair. R3 architecture HEAD `0ba619a107f6616083a9531c2770ea7e0908e2af` passed 314 unit tests, unchanged M1/M2/M3 replay, package audit, and the standard Skill validator; this is local structural evidence only. The r3 preparation manifest is now `fresh_contexts_consumed_not_accepted`: F01-F05 were all eligible, their five immutable inputs and prompts were frozen by LF-preserved raw SHA-256, and all five authorized fresh contexts were consumed exactly once. F05 was accepted. F01 and F04 produced JSON payloads that the composer rejected as `malformed_m3_bundle`; F02 produced `route_incompatible` with empty cards and overlays and was rejected; F03 produced the expected blocked terminal code but its sole validator call used a nonexistent r3 source alias, so its preserved receipt is invalid. No failed r3 case was repaired or retried. F04-D01 remains backed by a new independent non-nuclear M1_COMPLETE lineage, a valid route-free M2.1.1 confirmation successor, and a distinct fresh-worktree review. The initial F04 review remains preserved as invalid because Windows CRLF checkout changed the filesystem raw hash; path-specific LF rules repaired byte materialization without modifying the F04 or frozen r2 Git blobs, and a new review at HEAD `738f337b2dd645fc5e0c8c159fd42d02b67defc5` passed M1, M2, byte, confirmation, and F04 eligibility gates. The historical blocked acceptance record is `evals/m3/results/2026-08-05-m3.1.1-final-validation.md`; the r2 records are `evals/m3/results/2026-08-05-forward-evaluation-r2.md` and `evals/m3/results/forward-r2/acceptance-manifest.json`. No stale claim that M3 closure candidate HEAD `b0a1b9e` passed Actions run `31000758678` is accepted here. The baseline M2.1.1 Actions run `30977286846` is not M3 implementation CI. R3 does not supersede r2 for acceptance; local closure gates, push, exact final closure CI, M4, and M5 were not run.

Neither the historical local result nor this acceptance revision claims a real experiment, simulation, training run, download, deployment, route execution, target-domain transfer result, operational readiness, or nuclear safety conclusion.

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
- Active local branch: `codex/m3.1.1-r3-acceptance-repair`
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
