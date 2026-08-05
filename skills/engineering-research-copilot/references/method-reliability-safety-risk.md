# Reliability, Safety, and Risk

Apply [Method coaching](core-method-coaching.md) first. Use this family protocol to populate only the closed card fields permitted by that protocol; do not create a safety case, execute a hazard analysis, or authorize an operational or regulatory decision.

## Applicability

- Select `reliability_safety_risk` for claims about reliability, availability, maintainability, hazards, failure probability, risk, resilience, or safety-related decision support.
- Bind the card only to M2-derived claims, decision metrics, required preconditions, and resource ceilings.
- Put the system and hazard scope, event and consequence definitions, exposure basis, population and observation windows, censoring rules, data-completeness record, dependency assumptions, and decision context in `applicability.required_inputs`.
- Put ambiguous events, missing exposure denominators, unknown data completeness, unresolved dependencies, unsupported rare-event extrapolation, absent defense-in-depth constraints, unresolved required inputs, and unavailable specialist review in `applicability.incompatible_conditions`.
- Reserve `stop_conditions` and `pivot_conditions` exclusively for closed numeric criterion objects; do not encode missing artifacts, provenance failures, or safety gates there.
- Separate reliability estimates, hazard identification, consequence analysis, risk aggregation, operational decisions, and regulatory conclusions so evidence for one does not automatically support another.

## Assumptions

- State system boundaries, mission time, operating states, event taxonomy, exposure unit, censoring, repair, recurrence, stationarity, independence, common-cause, and reporting assumptions.
- State the consequence categories, risk measure, uncertainty semantics, and any aggregation or risk-acceptance rule without presenting it as regulatory approval.
- Label sparse-event rates, dependence structures, surrogate consequences, external-hazard transfer, and extrapolation beyond observed exposure as hypotheses.

## Minimum resources

- Put only finite, non-boolean numeric requirements such as observed exposure, event counts, independent-unit counts, scenario counts, expert-review time, or analysis capacity in `minimum_resources`.
- Bind every row by `source_constraint_id`, `resource`, and `unit` to an inherited M2 resource ceiling whose operator is `<` or `<=`; remain strictly within that ceiling.
- Keep hazard logs, event records, exposure histories, maintenance histories, taxonomies, consequence models, dependency records, and review approvals in `applicability.required_inputs`, not in `minimum_resources`.
- Treat an absent matching ceiling as an incompatible input state, not as permission to invent or widen a resource allowance.

## Baselines and controls

- Include observed exposure-normalized rates, a simple classical reliability model, or a documented conservative reference as the primary baseline.
- Compare methods using identical event definitions, exposure windows, censoring rules, consequence categories, dependencies, and data-completeness assumptions.
- Preserve a defense-in-depth reference case and test whether the proposed method changes, bypasses, or weakens any independent protective layer.

## Procedure

- Freeze the system and hazard scope, event taxonomy, consequence categories, exposure denominator, observation period, censoring rules, and completeness criteria before estimation.
- Reconcile event and exposure records, quantify missing or excluded data, and distinguish zero observed events from zero risk.
- Map initiating events, dependencies, common causes, barriers, recovery paths, and consequences at the resolution needed by the bound claim.
- Fit or compare reliability and risk estimates only within supported populations and exposure; state rare-event limits and avoid unsupported tail extrapolation.
- Test sensitivity to event definitions, reporting completeness, dependence, common-cause assumptions, priors, distributions, consequence models, and exposure boundaries.
- Keep the outline advisory until the user separately authorizes analysis execution or any operational use.

## Metrics

- Use only selected-direction metric IDs and units in `primary_metrics`, stop conditions, and pivot conditions.
- Express events, failures, and false alarms with an explicit exposure basis such as hours, demands, cycles, missions, components, or opportunities.
- Pair mean or point estimates with uncertainty and tail, worst-case, barrier, and consequence measures appropriate to the decision.
- Do not substitute accuracy, availability, or a composite risk score for a safety claim whose event and consequence definitions differ.

## Uncertainty

- Separate aleatory variability, epistemic uncertainty, model-form uncertainty, parameter uncertainty, data incompleteness, reporting uncertainty, and expert-judgment uncertainty.
- Show sensitivity to distributions, priors, dependence, common causes, censoring, event classification, exposure boundaries, and consequence assumptions.
- Report rare-event interval width and identifiability limits; absence of observed failures is not evidence of negligible risk without adequate exposure and detection coverage.

## Validation

- Audit hazard scope, event definitions, exposure accounting, observation windows, censoring, completeness, traceability, and independence before interpreting risk estimates.
- Check model behavior against observed cases, limiting cases, known barriers, historical exposure, and conservative bounds where suitable.
- Stress assumptions governing rare events, common causes, dependencies, reporting loss, and consequence severity; show which assumptions control the conclusion.
- Verify that the proposed method preserves defense in depth, independent protection, conservative limits, human authority, and existing safety functions.
- Treat structural bundle validation as offline contract evidence, not as reliability demonstration, safety validation, operational qualification, or regulatory acceptance.

## Failure modes

- List ambiguous event taxonomy, denominator error, under-reporting, survivorship bias, informative censoring, dependence hidden as independence, common-cause omission, sparse-event overconfidence, tail-model misspecification, barrier-credit inflation, and consequence truncation when relevant.
- Explain how each listed failure could change the bound claim or metric.
- Preserve missing events, uncertain classifications, failed assumptions, and adverse sensitivity results; do not erase them through aggregation or expert averaging.

## Stop/Pivot conditions

- Populate `stop_conditions` and `pivot_conditions` only with the closed numeric criterion objects defined by [Method coaching](core-method-coaching.md).
- In `bounded` mode, copy each applicable `metric_id`, `operator`, finite `value`, and `unit` from a matching selected-direction `minimum_decisive_test` stop or pivot criterion; in `route_specific` mode, copy them from the corresponding validated route condition.
- Use only criteria relevant to exposure-normalized event rates, uncertainty width, adverse sensitivity, barrier performance, consequence bounds, or risk limits; preserve the upstream operator, value, and unit verbatim.
- Fail closed and request upstream criterion repair when no applicable numeric stop or pivot criterion exists; never invent, estimate, tune, or reinterpret a safety threshold inside M3.
- Put ambiguous events, missing exposure or completeness evidence, unresolved rare-event limitations, weakened defense in depth, and specialist-review failures in `applicability.incompatible_conditions`, not in numeric condition lists.

## Safety boundaries

- Preserve defense in depth, independent protection layers, conservative operating limits, fail-safe behavior, human oversight, and shutdown authority regardless of an estimated improvement.
- Require independent qualified specialist review before using a card for operational, licensing, certification, regulatory, or safety-significant conclusions.
- Do not issue a safety case, risk acceptance, operating permission, maintenance deferral, barrier credit, or regulatory conclusion through method coaching.

## Source-ledger limits

- Populate `source_ledger` under the closed ledger and eligibility rules in [Method coaching](core-method-coaching.md); label every row as metadata-, abstract-, or full-text-level.
- Use sources only for the hazards, systems, populations, exposure bases, event definitions, dependencies, consequence models, and uncertainty limits they actually report.
- State explicitly what each source does not support, including unobserved rare events, changed operating regimes, barrier credit, operational acceptance, transfer, licensing, or safety.
- Require non-preprint support for safety-related conclusions as defined by the core protocol; block conflicted, unresolved, or recommendation-ineligible citations.
