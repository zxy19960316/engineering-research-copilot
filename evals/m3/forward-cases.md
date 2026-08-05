# M3 Fresh-Context Forward Cases

Freeze these cases before execution. Run each case in a separate, genuinely fresh context that receives only the root Skill, the named immutable M2 input, and the frozen prompt. Do not expose validator source, unit tests, adversarial fixtures, fixture builders, expected error codes, prior M3 outputs, or implementation conversation history.

## Shared execution contract

- Accept only a complete, independently preserved `m2.1.1` input. Do not create, mutate, normalize, repair, or backfill an M2 bundle for this evaluation.
- Record the fresh-context identifier, input path and raw SHA-256, prompt hash, references actually loaded, output path and raw SHA-256 when an output exists, validator output, evidence basis levels, side effects, deviations, and limitations.
- Load `skills/engineering-research-copilot/SKILL.md`, then only the references named for the case. Loading any validator, test, fixture, or fixture-builder source invalidates the fresh-context claim.
- Preserve the embedded M2 bundle verbatim. Recompute canonical source-bundle and selected-direction hashes and rederive claims, metrics, claim-specific preconditions, resource ceilings, and actual Go/Stop/Pivot coverage from upstream structures.
- Use only recommendation-eligible, allowed-status M1 candidate records already embedded in the M2 input. Map `metadata_level`, `abstract_level`, and `fulltext_level` exactly to `metadata`, `abstract`, and `full_text`; never upgrade a basis level.
- Return one closed `m3.1` JSON bundle when coaching is permitted. Validate it exactly once after finalization. Preserve an invalid, blocked, or not-run outcome; do not repair and retry within a case.
- Do not search the web, add or verify papers, execute a route, inspect research data, run an experiment or simulation, train or infer with a model, download data or weights, start a service, upload material, deploy software, allocate resources, or make an operational or safety judgment.
- Treat a valid result as workflow and offline structural evidence only. It never establishes method effectiveness, empirical performance, target-domain transfer, simulation validity, or safety.

## Case M3-F01 — Bounded coaching with no route

### Input prerequisites

Supply one independently accepted `m2.1.1` bundle with exactly one `user_confirmed` formal direction, valid confirmation and selected-direction hashes, `route_output: null`, empty or absent route-specific content as required by M2, and no unresolved blocking precondition. The selected direction must support `data_ml_hybrid`, contain eligible embedded source records, define resource ceilings, and contain applicable numeric `stop` and `pivot` criteria for its selected metric IDs. The input must not be derived from `evals/m3/build_fixtures.py` or any file under `evals/m3/fixtures/`.

### Frozen prompt

```text
Apply M3 method coaching to the supplied immutable m2.1.1 bundle. Validate the complete M2 bundle first and recompute all bindings. Because route_output is null, return one bounded data_ml_hybrid method card and no route-specific procedure. Copy only applicable numeric stop and pivot criteria already present in the selected direction, inherit every resource limit exactly, and use only eligible embedded sources at their exact basis levels. Keep supports, does_not_support, and limitations explicit. Do not invent a route, threshold, source, input, result, or resource allowance. Do not execute any research or external action.
```

### Expected references

- `skills/engineering-research-copilot/SKILL.md`
- `skills/engineering-research-copilot/references/core-method-coaching.md`
- `skills/engineering-research-copilot/references/method-data-ml-hybrid.md`

### Expected outcome and evidence basis

- Machine-visible: one validator-`valid` `m3.1` bundle with `coaching_mode: bounded`, one `data_ml_hybrid` card, no fabricated route, exact M2 hash bindings, exact inherited constraints, and ledger basis levels no stronger than their M1 records.
- User-visible: a bounded explanation of applicable assumptions, inputs, baseline, controls, uncertainty, failure modes, checks, numeric stop/pivot criteria, and why execution remains unauthorized.
- Evidence basis: the method card may reason only from the embedded candidate records and must label every ledger row as metadata-, abstract-, or full-text-level through `basis_level`. Structural validation is the only evaluation evidence.
- Stop and side-effect boundary: stop if the M2 bundle, confirmation, hashes, eligible source basis, resource ceilings, or applicable numeric criteria are missing or invalid. Produce no complete route and perform no side effect.
- Cannot prove: that the method works, that the selected direction is scientifically correct, that a dataset is usable, that a model generalizes, or that any experiment or route was run.

## Case M3-F02 — Route-specific coaching after traceability repair

### Input prerequisites

Supply one independently accepted `m2.1.1` route bundle whose `approved_constraint_changes` is empty. For each selected claim, `route_traceability.source_precondition_ids` must exactly equal `minimum_decisive_test.claim_coverage.required_precondition_ids`. The declared condition-type set must exactly equal the set rederived by intersecting that claim's metric IDs with the actual route `go_conditions`, `stop_conditions`, and `pivot_conditions`. The artifact must be produced and accepted upstream; the M3 evaluator must not repair Case F or construct a substitute.

### Frozen prompt

```text
Apply route-specific M3 method coaching to the supplied immutable m2.1.1 route bundle. Validate the complete M2 bundle, recompute every hash, and independently rederive claim metrics, claim-specific preconditions, inherited resource ceilings, and actual Go/Stop/Pivot coverage. Use route_specific only if every rederived set exactly matches the upstream route traceability and approved_constraint_changes is empty. Instantiate only the applicable method-family cards from the validated route. Copy numeric route conditions and resource limits exactly. Do not repair traceability, widen resources, create a new route, or execute any route step.
```

### Expected references

- `skills/engineering-research-copilot/SKILL.md`
- `skills/engineering-research-copilot/references/core-method-coaching.md`
- Exactly the method-family reference selected by the confirmed claims; for the current nuclear-data/ML lineage this is `skills/engineering-research-copilot/references/method-data-ml-hybrid.md`
- `skills/engineering-research-copilot/references/domain-nuclear-ml.md` only when the input is nuclear engineering × machine learning

### Expected outcome and evidence basis

- Machine-visible: one validator-`valid` bundle with `coaching_mode: route_specific`, exact source hashes, exact inherited constraints, and cards whose metrics, inputs, conditions, and sources are subsets of the validated route and selected direction.
- User-visible: a route-bound coaching explanation that distinguishes copied route authority from method commentary and says explicitly that no route step ran.
- Evidence basis: source-ledger entries remain limited to the exact embedded M1 basis levels; route traceability supplies structural bindings but is not empirical evidence.
- Stop and side-effect boundary: any precondition-set mismatch, condition-set mismatch, non-empty approved change, stale hash, unsupported family, or missing eligible source stops route-specific instantiation. No in-place repair and no side effect are permitted.
- Cannot prove: route feasibility, method performance, data quality, training success, target-domain transfer, operational readiness, or safety.

## Case M3-F03 — Unsupported approved-constraint provenance stop

### Input prerequisites

Supply one independently preserved, otherwise validator-acceptable `m2.1.1` route bundle with a genuinely upstream-authored, non-empty `approved_constraint_changes` list. Preserve the source artifact and approval fields exactly. Do not synthesize the record, copy the M3 adversarial fixture, or mutate a zero-change route solely to trigger this case.

### Frozen prompt

```text
Inspect the supplied immutable m2.1.1 bundle for M3 eligibility. If route_output.approved_constraint_changes is non-empty, stop before loading a method-family protocol or creating any method card. Return only unsupported_approved_constraint_change_provenance, show the original selected-direction resource_limits, apply none of the proposed changes, and request upstream provenance repair. Do not infer that a hash proves user identity or approval. Do not execute, allocate, download, or write anything.
```

### Expected references

- `skills/engineering-research-copilot/SKILL.md`
- `skills/engineering-research-copilot/references/core-method-coaching.md`
- No method-family or domain-overlay reference

### Expected outcome and evidence basis

- Machine-visible: no M3 method bundle; the terminal code is exactly `unsupported_approved_constraint_change_provenance`, and the original M2 resource limits remain unchanged.
- User-visible: the proposed change is not applied, the inherited limits are shown, and the user is asked to repair approval provenance upstream.
- Evidence basis: the decision rests only on the structural fact that the preserved list is non-empty. It does not authenticate an approver, message, or hash.
- Stop and side-effect boundary: stop before card or overlay construction and before any resource use. Do not validate the proposed change semantically, repair it, or fall back to expanded limits.
- Cannot prove: that approval was fraudulent or genuine, that the requested resources are needed, or that a route would succeed under either old or proposed limits.

## Case M3-F04 — Non-nuclear experiment and measurement family

### Input prerequisites

Supply one independently accepted, non-nuclear `m2.1.1` bundle with one `user_confirmed` direction whose claims require controlled physical measurement, calibration, repeatability or reproducibility, and measurement uncertainty. It must include compatible metric IDs and units, applicable numeric stop/pivot criteria, finite resource ceilings, required input/precondition records, and eligible source records. The input must not mention nuclear engineering as its domain or require the nuclear overlay.

### Frozen prompt

```text
Apply M3 method coaching to the supplied immutable non-nuclear m2.1.1 bundle. Load the experiment_measurement_uq family only after the core M3 gate passes. Return one closed card covering the measurand, experimental unit, calibration trace, controls, randomization or blocking, repeatability, reproducibility, uncertainty budget, validation checks, failure modes, and upstream numeric stop/pivot criteria. Bind every resource and source to the M2 input. Do not add a nuclear overlay, invent apparatus facts, create a route, collect data, or operate equipment.
```

### Expected references

- `skills/engineering-research-copilot/SKILL.md`
- `skills/engineering-research-copilot/references/core-method-coaching.md`
- `skills/engineering-research-copilot/references/method-experiment-measurement-uq.md`
- No `domain-nuclear-ml.md`

### Expected outcome and evidence basis

- Machine-visible: one validator-`valid` bundle containing only an `experiment_measurement_uq` card and an empty `domain_overlays` list, with exact hashes, resource bindings, metric units, and closed source-ledger fields.
- User-visible: measurement coaching remains advisory and names the calibration, experimental-design, uncertainty, and specialist boundaries without claiming that apparatus or data were inspected.
- Evidence basis: all source support and non-support statements stay at the exact embedded metadata, abstract, or full-text basis. The source ledger cannot substitute for calibration or reproducibility records.
- Stop and side-effect boundary: missing calibration provenance, incompatible units, absent numeric criteria, unbound resources, hazardous-operation authorization, or insufficient source basis stops the card. No data collection, equipment control, or file write is permitted.
- Cannot prove: measurement traceability, apparatus fitness, causal effect, repeatability, reproducibility, uncertainty magnitude, or experimental success.

## Case M3-F05 — Nuclear engineering × ML transfer boundary

### Input prerequisites

Supply one independently accepted `m2.1.1` bundle with a `user_confirmed` nuclear engineering × ML direction, empty approved changes, explicit target-domain preconditions, applicable numeric criteria, and eligible embedded sources. At least one eligible non-preprint source must be capable of supporting only the safety-boundary statements actually recorded; otherwise the case must stop rather than invent safety support. Cross-domain transfer must remain unconfirmed by target-domain decisive evidence.

### Frozen prompt

```text
Apply bounded M3 coaching to the supplied immutable nuclear engineering × machine learning bundle. Build only the applicable general method card or cards, then add one additive nuclear_engineering_ml overlay. Keep transfer_status exactly hypothesis. Preserve simulator-to-plant, scale, scenario, sensor, configuration, physics, defense-in-depth, human-authority, and specialist-review boundaries. Require one eligible non-preprint safety ledger row and state what every source does not support. Do not claim plant validity, operational qualification, protection credit, licensing acceptance, or nuclear safety. Do not access plant data, run a simulator, train a model, deploy, or execute a route.
```

### Expected references

- `skills/engineering-research-copilot/SKILL.md`
- `skills/engineering-research-copilot/references/core-method-coaching.md`
- `skills/engineering-research-copilot/references/method-data-ml-hybrid.md`
- `skills/engineering-research-copilot/references/domain-nuclear-ml.md`
- Any additional general family reference only when an independently derived selected claim requires it

### Expected outcome and evidence basis

- Machine-visible: one validator-`valid` bounded bundle with at least one applicable general card, one additive `nuclear_engineering_ml` overlay, `transfer_status: hypothesis`, exact numeric conditions, and an eligible non-preprint safety-ledger row.
- User-visible: transfer is explicitly hypothetical; simulator-to-plant validity, physics coverage, safety functions, defense in depth, human authority, and specialist review remain visible limitations.
- Evidence basis: every ledger row retains its embedded metadata/abstract/full-text level. A safety support type is limited to the exact non-preprint source content and cannot imply plant transfer or regulatory acceptance.
- Stop and side-effect boundary: absent target-domain preconditions, missing non-preprint safety support, invalid VVUQ lineage, unsupported operational use, or missing specialist boundaries stops the overlay. No simulator, plant, data, model, or operational action is permitted.
- Cannot prove: target-domain transfer, plant representativeness, VVUQ completion, model performance, defense-in-depth adequacy, licensing acceptability, or nuclear safety.

## Required run artifacts

After a genuine run, preserve one case result record per case plus immutable input and output hashes. Create `evals/m3/results/2026-08-05-forward-evaluation.md`, `2026-08-05-forward-bundles.json`, and `2026-08-05-forward-validations.json` only from actual fresh-context results. Until all prerequisites exist, preserve the dated not-run record; offline fixtures and same-context rehearsals are not forward evidence.
