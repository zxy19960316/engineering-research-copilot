# M3 Engineering Method Cards Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an offline, closed, evidence-grounded M3 method-coaching contract with six general engineering method families, one nuclear engineering × machine learning overlay, and fail-closed M2.1.1 input protection.

**Architecture:** Keep the root Skill as a thin router and place every method protocol in a directly linked, one-level reference. Add one standard-library validator that first delegates to the accepted M2.1.1 validator, then derives the confirmed direction, claims, claim-specific preconditions, route condition coverage, resource ceilings, and source eligibility instead of trusting copied M3 declarations. Keep plans, fixtures, replay records, and acceptance evidence outside the installable Skill.

**Tech Stack:** Markdown, JSON, Python standard library, `unittest`, canonical UTF-8 JSON SHA-256, GitHub Actions.

## Global Constraints

- Start from exact commit `d0f5e9017044ba35d0ac4559591028228f3b22d8` on branch `codex/m3-engineering-method-cards`; do not base M3 on the current `origin/main`.
- Execute only M3 engineering method cards; keep M4, M5, runtime, deployment, platform integration, model downloads, service startup, training, experiment execution, simulation execution, and RRC integration out of scope.
- Keep `skills/engineering-research-copilot/SKILL.md` below 500 lines and keep all loadable references exactly one level under `references/`, linked directly from the root Skill.
- Keep plans, tests, fixtures, frozen replay output, and acceptance records outside the installable Skill folder.
- Use scripts only for deterministic offline validation and fixture generation.
- Validate the complete embedded M2 bundle with `validate_m2_direction_bundle.validate_bundle` before consuming any upstream field.
- Require `direction_decision.status == "user_confirmed"` and recompute the exact selected-direction and source-bundle hashes.
- Permit bounded method coaching when `route_output` is absent; permit route-specific instantiation only when the route is present and passes the additional M3 compatibility gate.
- Reject every non-empty `route_output.approved_constraint_changes` with `unsupported_approved_constraint_change_provenance`; display only the original selected-direction `resource_limits` and apply no change.
- Derive claim metrics, claim-specific preconditions, resource ceilings, and actual Go/Stop/Pivot metric coverage from M2 structures; do not trust route traceability labels alone.
- Keep citation discovery separate from verification, reject conflicted or unresolved sources, and label metadata-, abstract-, and full-text-level reasoning.
- Permit verified preprints for methods and exploration, but never as sole support for a main direction or safety-related conclusion.
- Treat cross-domain transfer as a hypothesis until a target-domain decisive test supports it.
- Require user direction confirmation before a full route and require separate explicit authorization before any side effect or execution.
- Use TDD, preserve red evidence, stage explicit paths, and do not push, merge, or configure a remote without explicit authorization.

## File Structure

- Modify `STATUS.md`: record the exact M3 baseline, active branch, guardrails, progress, and final local evidence without rewriting historical M1/M2 results.
- Modify `skills/engineering-research-copilot/SKILL.md`: route method coaching through the M3 input gate and directly link all eight new references.
- Create `skills/engineering-research-copilot/references/core-method-coaching.md`: define the M3 state flow, closed bundle, card, source-ledger, resource, and permission contracts.
- Create `skills/engineering-research-copilot/references/method-experiment-measurement-uq.md`: cover experimental design, measurement chains, calibration, repeatability, and uncertainty propagation.
- Create `skills/engineering-research-copilot/references/method-modeling-simulation-vvuq.md`: cover model hierarchy, code verification, solution verification, validation, sensitivity, and uncertainty quantification.
- Create `skills/engineering-research-copilot/references/method-control-optimization-identification.md`: cover excitation, identifiability, constraints, robustness, optimization baselines, and closed-loop safety.
- Create `skills/engineering-research-copilot/references/method-signal-diagnostics.md`: cover sampling, preprocessing, leakage-safe segmentation, detection/diagnosis metrics, shift, and false alarms.
- Create `skills/engineering-research-copilot/references/method-data-ml-hybrid.md`: cover leakage-safe splits, simple baselines, calibration, out-of-distribution behavior, ablation, and hybrid-model checks.
- Create `skills/engineering-research-copilot/references/method-reliability-safety-risk.md`: cover hazard framing, reliability data, uncertainty, rare events, defense in depth, and specialist sign-off boundaries.
- Create `skills/engineering-research-copilot/references/domain-nuclear-ml.md`: add nuclear-specific data, physics, VVUQ, safety, licensing, human-oversight, and transfer-hypothesis boundaries by referencing general cards rather than duplicating them.
- Create `skills/engineering-research-copilot/scripts/validate_m3_method_bundle.py`: implement the closed, deterministic, read-only M3 validator and CLI.
- Create `tests/test_validate_m3_method_bundle.py`: freeze validator behavior red-first.
- Create `tests/test_replay_m3_offline_results.py`: verify exact replay and byte-deterministic fixture generation.
- Create `evals/m3/build_fixtures.py`: generate valid and adversarial bundles from accepted test builders.
- Create `evals/m3/adversarial-cases.json`, `evals/m3/fixtures/*.json`, and `evals/m3/offline-results.json`: store deterministic offline contract evidence.
- Create `evals/m3/replay_offline_results.py`: replay each manifest case and compare exact status, errors, and evidence gaps.
- Create `evals/m3/forward-cases.md`: define fresh-context prompts and expected stop/pass boundaries before running them.
- Create `evals/m3/results/2026-08-05-forward-evaluation-not-run.md`: preserve an honest not-run record until the workflow exists and a fresh context is available.
- Modify `.github/workflows/m1-validation.yml`: retain every M1/M2 gate and add M3 compile, tests, fixture regeneration/diff, replay, and package audit steps.
- Create `evals/m3/results/2026-08-05-m3.1-final-validation.md`: record commands, exact counts, exits, provenance class, limitations, and remote-CI state at closure.

## Closed M3.1 Interfaces

Use this exact top-level object:

```yaml
schema_version: "m3.1"
source_m2_bundle: {}
source_m2_bundle_hash: ""
selected_direction_id: "D1"
selected_direction_hash: ""
coaching_mode: "bounded|route_specific"
method_cards: []
domain_overlays: []
```

Use this exact method-card object:

```yaml
schema_version: "m3.1"
card_id: "card:data-ml-hybrid:1"
method_family: "experiment_measurement_uq|modeling_simulation_vvuq|control_optimization_identification|signal_diagnostics|data_ml_hybrid|reliability_safety_risk"
applicability:
  supported_claim_types: []
  required_inputs: []
  incompatible_conditions: []
assumptions: []
minimum_resources: []
inherited_constraints: []
baselines: []
controls: []
procedure_outline: []
primary_metrics: []
uncertainty_handling: []
validation_checks: []
failure_modes: []
stop_conditions: []
pivot_conditions: []
safety_boundaries: []
source_ledger: []
```

Represent each minimum-resource row as `resource`, `required_value`, `unit`, and `source_constraint_id`. Match `source_constraint_id` to one inherited M2 resource limit; reject unmatched units and any required value that violates a `<` or `<=` ceiling. Copy the selected direction's `resource_limits` exactly into `inherited_constraints` for every card.

Represent every stop or pivot condition with `criterion_type`, `metric_id`, `operator`, finite numeric `value`, and `unit`. Use only `stop` in `stop_conditions`, only `pivot` in `pivot_conditions`, and only `<`, `<=`, `>`, or `>=` operators.

Use this exact source-ledger row:

```yaml
source_id: "source:P7"
candidate_id: "P7"
basis_level: "metadata|abstract|full_text"
support_types: ["bibliographic_identity|method|result|transfer|safety"]
supports: []
does_not_support: []
limitations: []
```

Resolve `candidate_id` against `source_m2_bundle.source_m1_bundle.round2.candidate_pool`. Map upstream basis levels only through the closed mapping `metadata_level -> metadata`, `abstract_level -> abstract`, and `fulltext_level -> full_text`; require exact equality after that mapping, recommendation eligibility, an allowed verified status, a non-empty closed `support_types` list, and non-empty `supports`, `does_not_support`, and `limitations` lists. Permit only `bibliographic_identity`, `method`, `result`, `transfer`, and `safety` support types. Metadata-only evidence may use only `bibliographic_identity`; never infer a support type from free text.

Use this exact domain-overlay object:

```yaml
schema_version: "m3.1"
overlay_id: "domain:nuclear-ml:1"
domain: "nuclear_engineering_ml"
base_card_ids: []
additional_assumptions: []
additional_failure_modes: []
additional_validation_checks: []
additional_stop_conditions: []
specialist_review_boundaries: []
transfer_status: "hypothesis"
source_ledger: []
```

Require each `base_card_id` to resolve to one method card in the same bundle. Keep `transfer_status` fixed to `hypothesis`; reject labels such as `validated`, `proven`, or `established` because M3 does not execute a target-domain decisive test.

---

### Task 1: Freeze the exact M3 baseline and activate status

**Files:**
- Create: `docs/superpowers/plans/2026-08-05-m3-engineering-method-cards.md`
- Modify: `STATUS.md`

**Interfaces:**
- Consumes: accepted M2.1.1 HEAD `d0f5e9017044ba35d0ac4559591028228f3b22d8` and exact-HEAD successful Actions run `30977286846`.
- Produces: branch `codex/m3-engineering-method-cards`, `M3 IN_PROGRESS`, and an explicit guardrail record.

- [ ] Verify `git rev-parse HEAD` prints `d0f5e9017044ba35d0ac4559591028228f3b22d8`, `git branch --show-current` prints `codex/m3-engineering-method-cards`, and `git status --short` prints nothing.
- [ ] Record the baseline, branch, Actions run, execution exclusions, and non-empty-approval fail-closed rule in `STATUS.md` while retaining all M1/M2 acceptance history.
- [ ] Run `git diff --check` and expect exit `0`.
- [ ] Stage only `STATUS.md` and this plan, then commit as `docs: activate M3 engineering method cards`.

### Task 2: Specify the M3 input gate and closed card schema red-first

**Files:**
- Create: `tests/test_validate_m3_method_bundle.py`

**Interfaces:**
- Consumes: `make_valid_m2_bundle`, `_confirm_bundle`, and `_route_output` from `tests/test_validate_m2_direction_bundle.py`.
- Produces: `make_valid_m3_bundle(coaching_mode: str = "bounded") -> dict` and named red tests for every acceptance guardrail.

- [ ] Add a valid M3 builder with an embedded confirmed M2.1.1 bundle, canonical bundle/direction hashes, one complete `data_ml_hybrid` card, and no domain overlay.
- [ ] Add the exact guardrail tests:

```python
def test_nonempty_approved_constraint_changes_fail_closed(self):
    bundle = make_valid_m3_bundle(coaching_mode="route_specific")
    bundle["source_m2_bundle"]["route_output"]["approved_constraint_changes"] = [{
        "constraint_id": "R-D1-VRAM",
        "previous_value": 24,
        "approved_value": 48,
        "unit": "GiB",
        "approval_message_id": "message:unverifiable-change",
        "approval_message_sha256": "0" * 64,
    }]
    self.assertIn(
        "unsupported_approved_constraint_change_provenance",
        validate_m3_bundle(bundle)["errors"],
    )

def test_route_preconditions_must_equal_claim_coverage(self):
    bundle = make_valid_m3_bundle(coaching_mode="route_specific")
    bundle["source_m2_bundle"]["route_output"]["route_traceability"][0][
        "source_precondition_ids"
    ] = []
    self.assertIn(
        "route_precondition_traceability_mismatch",
        validate_m3_bundle(bundle)["errors"],
    )

def test_route_condition_types_are_derived_from_actual_metric_conditions(self):
    bundle = make_valid_m3_bundle(coaching_mode="route_specific")
    bundle["source_m2_bundle"]["route_output"]["stop_conditions"] = [{
        "criterion_type": "stop",
        "metric_id": "M-COST",
        "operator": ">",
        "value": 2,
        "unit": "hours",
    }]
    self.assertIn(
        "route_condition_traceability_mismatch",
        validate_m3_bundle(bundle)["errors"],
    )
```

- [ ] Add tests for invalid embedded M2, non-confirmed direction, wrong direction hash, route-specific mode without a route, and bounded mode with no route.
- [ ] Add tests that remove assumptions, baselines, failure modes, uncertainty handling, or numeric stop conditions and assert their stable error codes.
- [ ] Add tests for a ledger row without `does_not_support`, mismatched basis level, ineligible source, unbound minimum resource, resource ceiling expansion, and an unknown method family.
- [ ] Add tests that reject a nuclear overlay without base cards, with a non-hypothesis transfer status, or with a preprint as sole safety support.
- [ ] Run `python -X utf8 -m unittest tests.test_validate_m3_method_bundle -v`; expect import failure for `validate_m3_method_bundle` and preserve that red result in the task notes before implementation.
- [ ] Stage only `tests/test_validate_m3_method_bundle.py`, then commit as `test: specify M3 method bundle contract`.

### Task 3: Implement the read-only M2 compatibility gate

**Files:**
- Create: `skills/engineering-research-copilot/scripts/validate_m3_method_bundle.py`
- Modify: `tests/test_validate_m3_method_bundle.py`

**Interfaces:**
- Consumes: `validate_m2_direction_bundle.validate_bundle(bundle) -> dict` and `canonical_sha256(value) -> str`.
- Produces: `validate_m3_bundle(bundle: Any) -> dict`, `_derive_m2_context(source_m2_bundle: dict) -> dict`, and CLI exit codes `valid=0`, `invalid=1`, `evidence_incomplete=2`.

- [ ] Define exact top-level, card, applicability, resource, criterion, ledger, and overlay field sets from “Closed M3.1 Interfaces”; reject every unknown field.
- [ ] Implement `_derive_m2_context` so it validates the whole M2 bundle first, requires `user_confirmed`, locates the exact formal direction, and derives canonical hashes, claims, per-claim metrics, per-claim coverage preconditions, candidate eligibility/basis levels, and original resource limits.
- [ ] Reject non-empty `approved_constraint_changes` before any route-specific card processing and return only `unsupported_approved_constraint_change_provenance` for that compatibility boundary.
- [ ] For a route-specific request, require `route_output`, require each trace's precondition set to equal the corresponding `claim_coverage.required_precondition_ids`, and derive each claim's actual condition types by checking whether its metric IDs occur in `go_conditions`, `stop_conditions`, and `pivot_conditions`.
- [ ] Reject claimed condition types that differ from the derived set. Do not edit, migrate, or normalize the embedded M2 bundle.
- [ ] Run the focused input-gate tests and expect all guardrail cases to pass.
- [ ] Stage the validator and focused test changes, then commit as `feat: add M3 M2-input compatibility gate`.

### Task 4: Implement method-card, resource, ledger, and overlay validation

**Files:**
- Modify: `skills/engineering-research-copilot/scripts/validate_m3_method_bundle.py`
- Modify: `tests/test_validate_m3_method_bundle.py`

**Interfaces:**
- Consumes: `_derive_m2_context` output.
- Produces: `_validate_method_card`, `_validate_source_ledger`, `_validate_resource_bounds`, and `_validate_domain_overlay` with stable closed error codes.

- [ ] Require every card to contain non-empty applicability, assumptions, minimum resources, inherited constraints, baselines, controls, procedure outline, primary metrics, uncertainty handling, validation checks, failure modes, numeric stop/pivot conditions, safety boundaries, and source ledger.
- [ ] Require every `supported_claim_type` and primary metric to resolve to the selected direction's closed claims and required decision metrics.
- [ ] Copy-compare `inherited_constraints` with the selected direction's `resource_limits`; resolve every `source_constraint_id`; reject unknown resources, unit changes, non-finite values, and minimum values outside `<` or `<=` ceilings.
- [ ] Resolve each ledger `candidate_id` against the embedded M1 candidate pool, compare its basis level through the closed M1-to-M3 mapping, require recommendation eligibility, reject blocked citation states, and require a closed non-empty `support_types` list plus explicit support, non-support, and limitation lists. Permit only `bibliographic_identity`, `method`, `result`, `transfer`, and `safety`; metadata basis may use only `bibliographic_identity`.
- [ ] Require nuclear overlays to reference existing cards, add rather than replace safety boundaries, remain `hypothesis`, and use at least one eligible non-preprint source whose closed `support_types` includes `safety`.
- [ ] Run `python -X utf8 -m unittest tests.test_validate_m3_method_bundle -v` and expect all M3 unit tests to pass.
- [ ] Run the validator CLI once with a valid temporary fixture and once with an invalid temporary fixture; expect exit `0` and exit `1`, respectively, with compact JSON only.
- [ ] Stage the validator and tests, then commit as `feat: validate closed M3 method cards`.

### Task 5: Route method coaching and define the core protocol

**Files:**
- Modify: `skills/engineering-research-copilot/SKILL.md`
- Create: `skills/engineering-research-copilot/references/core-method-coaching.md`

**Interfaces:**
- Consumes: the `m3.1` validator contract and all accepted M1/M2 evidence rules.
- Produces: one M3 state flow and direct links from the root Skill to all eight M3 references.

- [ ] Add this state flow to `core-method-coaching.md`:

```text
M2_BUNDLE_VALID
  -> DIRECTION_USER_CONFIRMED
  -> SELECTED_DIRECTION_HASH_VALID
  -> ROUTE_ABSENT: BOUNDED_METHOD_COACHING
  -> ROUTE_PRESENT_AND_M3_COMPATIBLE: ROUTE_SPECIFIC_METHOD_CARD
  -> UNSUPPORTED_CONSTRAINT_APPROVAL: STOP_FOR_PROVENANCE_REPAIR
```

- [ ] Specify the closed top-level, method-card, source-ledger, and domain-overlay objects exactly as defined in this plan.
- [ ] State that bounded coaching may explain methods and checks but may not manufacture a complete route, execute a route, widen resources, or claim empirical success.
- [ ] Replace the generic method-coaching row in `SKILL.md` with a route through `core-method-coaching.md` and add direct links to each family and domain reference.
- [ ] Keep every M3 reference directly linked from `SKILL.md`; do not create nested reference directories.
- [ ] Run the standard Skill validator:

```powershell
python -X utf8 C:\Users\94310\.codex\skills\.system\skill-creator\scripts\quick_validate.py D:\engineering-research-copilot\skills\engineering-research-copilot
```

Expected: exit `0` and `Skill is valid!`.
- [ ] Stage only `SKILL.md` and `core-method-coaching.md`, then commit as `docs: add M3 method coaching protocol`.

### Task 6: Add experiment, simulation, control, and signal method families

**Files:**
- Create: `skills/engineering-research-copilot/references/method-experiment-measurement-uq.md`
- Create: `skills/engineering-research-copilot/references/method-modeling-simulation-vvuq.md`
- Create: `skills/engineering-research-copilot/references/method-control-optimization-identification.md`
- Create: `skills/engineering-research-copilot/references/method-signal-diagnostics.md`
- Modify: `skills/engineering-research-copilot/SKILL.md`

**Interfaces:**
- Consumes: the core method-card fields and M2-derived claims, metrics, preconditions, and ceilings.
- Produces: four directly loadable, non-overlapping family protocols.

- [ ] In the experiment reference, require a measurement model, calibration trace, randomization/blocking decision, repeatability/reproducibility check, uncertainty budget, baseline/control, and numeric stop rule before recommending data collection.
- [ ] In the modeling reference, separate code verification, solution verification, validation, and UQ; require a simpler model baseline, mesh/time-step or solver convergence checks where applicable, sensitivity analysis, and a validation boundary that prevents simulation agreement from becoming real-world proof.
- [ ] In the control reference, require excitation and identifiability checks, a simple controller or estimator baseline, constraint and robustness checks, closed-loop safety limits, and a stop rule for unstable or unidentifiable operation.
- [ ] In the signal reference, require sampling/aliasing checks, leakage-safe segmentation, preprocessing fitted only on training data, task-appropriate detection and diagnosis metrics, false-alarm accounting, shift checks, and a stop rule for invalid signal provenance.
- [ ] Give every reference the same sections: Applicability, Assumptions, Minimum resources, Baselines and controls, Procedure, Metrics, Uncertainty, Validation, Failure modes, Stop/Pivot conditions, Safety boundaries, and Source-ledger limits.
- [ ] Run the standard Skill validator and the package link audit; expect all references linked and root `SKILL.md` below 500 lines.
- [ ] Stage only the four references and root Skill link changes, then commit as `docs: add physical-system method cards`.

### Task 7: Add data/ML, reliability/safety/risk, and nuclear × ML guidance

**Files:**
- Create: `skills/engineering-research-copilot/references/method-data-ml-hybrid.md`
- Create: `skills/engineering-research-copilot/references/method-reliability-safety-risk.md`
- Create: `skills/engineering-research-copilot/references/domain-nuclear-ml.md`
- Modify: `skills/engineering-research-copilot/SKILL.md`

**Interfaces:**
- Consumes: core method cards plus the experiment, simulation, control, and signal references.
- Produces: two general family protocols and one additive nuclear-domain overlay.

- [ ] In the data/ML reference, require entity/scenario/time-aware splits, preprocessing isolation, a simple non-ML or classical baseline, calibration and OOD checks when claims require them, ablations, seed/repeat uncertainty, error slicing, and numeric stop/pivot rules.
- [ ] In the reliability/safety/risk reference, require hazard scope, event definitions, exposure basis, data completeness, uncertainty separation, rare-event limitations, sensitivity to assumptions, defense-in-depth preservation, and specialist review for operational or regulatory conclusions.
- [ ] In the nuclear × ML overlay, reference the relevant general cards by link, then add plant/scenario separation, simulator-to-plant transfer limits, physics and conservation checks, sensor failure/OOD handling, VVUQ distinctions, defense-in-depth, human oversight, licensing boundaries, and independent nuclear-domain review.
- [ ] State verbatim that nuclear × ML transfer remains a `hypothesis` until a target-domain decisive test supports it and that offline contract validation is not nuclear-safety validation.
- [ ] Do not copy complete general-card procedures into the nuclear overlay; add only domain-specific constraints, failure modes, checks, stops, and specialist boundaries.
- [ ] Run the standard Skill validator and the package link audit; expect all eight M3 references linked directly from root.
- [ ] Stage only the three references and root Skill link changes, then commit as `docs: add data risk and nuclear ML method cards`.

### Task 8: Freeze deterministic adversarial fixtures and replay

**Files:**
- Create: `evals/m3/build_fixtures.py`
- Create: `evals/m3/adversarial-cases.json`
- Create: `evals/m3/fixtures/*.json`
- Create: `evals/m3/offline-results.json`
- Create: `evals/m3/replay_offline_results.py`
- Create: `tests/test_replay_m3_offline_results.py`

**Interfaces:**
- Consumes: `make_valid_m3_bundle` and `validate_m3_bundle`.
- Produces: byte-stable fixtures and exact `(status, errors, evidence_gaps)` replay output.

- [ ] Generate two positive fixtures: `valid-bounded.json` with no route and `valid-route-specific.json` with condition metrics genuinely traced for every claim.
- [ ] Generate negative fixtures named `missing-assumptions.json`, `missing-baseline.json`, `missing-failure-mode.json`, `missing-uncertainty-handling.json`, `nonnumeric-stop-condition.json`, `source-missing-does-not-support.json`, `unconfirmed-direction.json`, `nonempty-approved-constraint-changes.json`, `resource-expansion.json`, `route-precondition-mismatch.json`, `route-condition-mismatch.json`, and `nuclear-transfer-overclaim.json`.
- [ ] Serialize with UTF-8, `sort_keys=True`, `indent=2`, `ensure_ascii=False`, one trailing newline, and `allow_nan=False`.
- [ ] Implement `evaluate(manifest_path: Path) -> dict` to load every declared fixture, run the M3 validator, and compare exact status, errors, and evidence gaps.
- [ ] Add replay tests that assert the frozen record matches, an edited expectation is exposed as a mismatch, and a second fixture generation produces identical bytes.
- [ ] Run `python -X utf8 evals/m3/build_fixtures.py`, then `python -X utf8 evals/m3/replay_offline_results.py`; write `offline-results.json` only from the actual replay.
- [ ] Regenerate and run `git diff --exit-code -- evals/m3/adversarial-cases.json evals/m3/fixtures`; expect exit `0`.
- [ ] Stage only M3 evaluation and replay-test paths, then commit as `test: freeze M3 adversarial replay`.

### Task 9: Define and run fresh-context forward evaluation only after implementation

**Files:**
- Create: `evals/m3/forward-cases.md`
- Create: `evals/m3/results/2026-08-05-forward-evaluation-not-run.md`
- Create after a real fresh-context run: `evals/m3/results/2026-08-05-forward-evaluation.md`
- Create after a real fresh-context run: `evals/m3/results/2026-08-05-forward-bundles.json`
- Create after a real fresh-context run: `evals/m3/results/2026-08-05-forward-validations.json`

**Interfaces:**
- Consumes: fully implemented references and validator; accepted Case F only as upstream structure, never as executed-route evidence.
- Produces: honest fresh-context evidence or a preserved not-run record.

- [ ] Define at least one bounded no-route case, one valid route-specific case with repaired traceability, one unverified resource-change stop, one non-nuclear method-family case, and one nuclear × ML transfer-boundary case.
- [ ] Require each case record to state input provenance, loaded references, metadata/abstract/full-text basis, validation result, side effects, and what the result does not prove.
- [ ] Use a genuinely fresh context only after all referenced workflows exist. If unavailable, retain `2026-08-05-forward-evaluation-not-run.md` and do not describe same-context fixtures as forward evaluation.
- [ ] Do not execute a route, train a model, download data or weights, start a service, or make an operational safety judgment during forward evaluation.
- [ ] Stage only actual forward-evaluation artifacts and commit as `eval: record M3 forward evaluation` when evidence exists; otherwise leave the not-run record explicit.

### Task 10: Extend CI, run closure gates, and record acceptance honestly

**Files:**
- Modify: `.github/workflows/m1-validation.yml`
- Modify: `STATUS.md`
- Create: `evals/m3/results/2026-08-05-m3.1-final-validation.md`

**Interfaces:**
- Produces: complete local regression evidence, deterministic M3 CI, a package audit, and an exact statement of any remote-CI or forward-evaluation gate not run.

- [ ] Add M3 validator, builder, and replay scripts to compilation; keep every existing M1/M2 compile and replay command unchanged.
- [ ] Keep full `unittest` discovery and add M3 fixture generation, zero-diff enforcement, and frozen replay after the existing M2 steps.
- [ ] Keep the root-Skill line, direct-reference link, forbidden-file, and marker audit; verify all eight new references are directly linked.
- [ ] Run locally:

```powershell
python -X utf8 -m py_compile skills/engineering-research-copilot/scripts/validate_m3_method_bundle.py evals/m3/build_fixtures.py evals/m3/replay_offline_results.py
python -X utf8 -m unittest discover -s tests -p "test_*.py" -v
python -X utf8 evals/m1/replay_offline_results.py
python -X utf8 evals/m1/replay_machine_artifacts.py
python -X utf8 evals/m2/build_fixtures.py
git diff --exit-code -- evals/m2/adversarial-cases.json evals/m2/fixtures
python -X utf8 evals/m2/replay_offline_results.py
python -X utf8 evals/m3/build_fixtures.py
git diff --exit-code -- evals/m3/adversarial-cases.json evals/m3/fixtures
python -X utf8 evals/m3/replay_offline_results.py
python -X utf8 C:\Users\94310\.codex\skills\.system\skill-creator\scripts\quick_validate.py D:\engineering-research-copilot\skills\engineering-research-copilot
git diff --check
```

- [ ] Record exact counts, statuses, command exits, fixture hashes or zero-diff result, and the distinction between offline validation and empirical evidence in the final validation record.
- [ ] Mark M3 complete only when its implemented workflow, regressions, deterministic replay, Skill validation, package audit, and required forward-evaluation gate satisfy the acceptance policy. Preserve any failed or not-run gate as failed or not run.
- [ ] If pushing remains unauthorized, record closure exact-HEAD GitHub Actions as `NOT_RUN — push not authorized`; do not reuse baseline run `30977286846` as M3 implementation CI.
- [ ] Stage explicit closure paths, commit as `docs: close M3 method card validation`, and finish with `git status --short` plus `git log -5 --oneline`; do not push or merge.

## Self-Review Results

- Spec coverage: tasks cover the six required method families, nuclear × ML overlay, required card fields, source support/non-support ledger, confirmation gate, resource guard, provenance repair stop, offline validation, backward regression, and honest forward-evaluation boundary.
- Scope coverage: no task starts M4/M5, executes a route, downloads a model, creates a service, integrates RRC, or adds a bundled paper corpus.
- Type consistency: all tasks use `schema_version: "m3.1"`, `validate_m3_bundle`, `source_m2_bundle`, `coaching_mode`, `method_cards`, `domain_overlays`, and the same closed card/ledger/overlay field names.
- Placeholder scan: the plan contains concrete paths, functions, fixtures, error codes, commands, expected outcomes, and commit scopes.
