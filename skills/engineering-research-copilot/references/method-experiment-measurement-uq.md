# Experiment, Measurement, and Uncertainty Quantification

Apply [Method coaching](core-method-coaching.md) first. Use this family protocol to populate only the closed card fields permitted by that protocol; do not create a route or authorize data collection.

## Applicability

- Select `experiment_measurement_uq` for claims that require controlled intervention, physical measurement, calibration, repeatability, reproducibility, or propagated measurement uncertainty.
- Bind the card only to M2-derived claims, decision metrics, required preconditions, and resource ceilings.
- Put the measurement model, calibration trace, data provenance, control definition, randomization or blocking decision, repeatability and reproducibility plan, and uncertainty-budget specification in `applicability.required_inputs`.
- Put missing or invalid provenance, calibration outside its valid range, unresolved required inputs, unavailable safety approval, and any other qualitative condition that makes the method unsuitable in `applicability.incompatible_conditions`.
- Reserve `stop_conditions` and `pivot_conditions` exclusively for closed numeric criterion objects; do not encode missing artifacts, provenance failures, or safety gates there.
- Hand off modeling-, control-, or signal-dominant checks to their directly linked family protocol instead of duplicating them here.

## Assumptions

- State the measurand, operating range, experimental unit, response, intervention, nuisance factors, and independence assumptions.
- State whether the measurement chain is stable, traceable, and sensitive enough for the minimum meaningful effect.
- Mark unverified apparatus behavior, transfer, scale-up, and causal assumptions as hypotheses.

## Minimum resources

- Put only finite, non-boolean numeric requirements such as independent-unit counts, repetition counts, acquisition capacity, time, or analysis capacity in `minimum_resources`.
- Bind every row by `source_constraint_id`, `resource`, and `unit` to an inherited M2 resource ceiling whose operator is `<` or `<=`; remain strictly within that ceiling.
- Keep reference standards, sensors, calibration records, controls, protocols, and datasets in `applicability.required_inputs`, not in `minimum_resources`.
- Treat an absent matching ceiling as an incompatible input state, not as permission to invent or widen a resource allowance.

## Baselines and controls

- Include a status-quo or simplest credible baseline and a control that isolates the intervention where the claim is causal.
- Decide explicitly whether to randomize, block, counterbalance, or preserve natural order; name the factor controlled and justify any omission.
- Separate negative, positive, reference, blank, and sham controls when the measurement mechanism requires them.

## Procedure

- Define a measurement model from measurand through sensor or transducer, calibration, acquisition, processing, and reported quantity; preserve units at every step.
- Record a calibration trace with the reference identity, valid range, version or date, corrections, calibration uncertainty, and applicability limits.
- Specify repeatability checks under unchanged conditions and reproducibility checks across the relevant operator, instrument, batch, site, or time factors.
- Fix the randomization or blocking decision, control observations, uncertainty budget, and a numeric stop condition before recommending a data-collection design.
- Keep the outline advisory until the user separately authorizes execution.

## Metrics

- Use only selected-direction metric IDs and units in `primary_metrics`, stop conditions, and pivot conditions.
- Report effect size with uncertainty, calibration residuals, repeatability variation, reproducibility variation, missingness, and control drift when applicable.
- Match the estimand and aggregation level to the experimental unit; do not substitute sample count for independent replication.

## Uncertainty

- Build an uncertainty budget that identifies random and systematic components, distributions or bounds, correlations, calibration contributions, resolution, drift, sampling, and model-form contributions.
- Propagate uncertainty with a method appropriate to the measurement model and state coverage or confidence semantics.
- Separate aleatory variability from epistemic uncertainty and show which components dominate the decision metric.

## Validation

- Check measurement range, sensitivity, calibration residuals, control behavior, missingness, repeatability, reproducibility, and unit consistency.
- Verify that randomization or blocking addresses the stated nuisance factors and that analysis preserves the experimental unit.
- Treat structural bundle validation as offline contract evidence, not as confirmation that the apparatus, calibration, or experiment performs as claimed.

## Failure modes

- List saturation, drift, hysteresis, contamination, batch effects, confounding, pseudo-replication, failed blinding, missing-not-at-random data, and calibration extrapolation when relevant.
- Explain how each listed failure could change the bound claim or metric.
- Preserve observed failures and unresolved checks; do not relabel them as acceptable variation.

## Stop/Pivot conditions

- Populate `stop_conditions` and `pivot_conditions` only with the closed numeric criterion objects defined by [Method coaching](core-method-coaching.md).
- In `bounded` mode, copy each applicable `metric_id`, `operator`, finite `value`, and `unit` from a matching selected-direction `minimum_decisive_test` stop or pivot criterion; in `route_specific` mode, copy them from the corresponding validated route condition.
- Use only criteria relevant to invalid calibration, excessive drift, inadequate precision, failed controls, or excessive decision uncertainty; preserve the upstream operator, value, and unit verbatim.
- Fail closed and request upstream criterion repair when no applicable numeric stop or pivot criterion exists; never invent, estimate, or tune a threshold inside M3.
- Put missing measurement models, calibration traces, controls, uncertainty budgets, provenance, and safety approvals in `applicability.incompatible_conditions`, not in numeric condition lists.

## Safety boundaries

- Require qualified laboratory or domain review for hazardous materials, radiation, pressure, high voltage, biological exposure, human participants, destructive testing, or regulated measurements.
- Do not convert method coaching into equipment operation, specimen handling, data collection, or a safety determination.
- Apply the stricter facility, legal, ethical, and specialist boundary whenever it conflicts with a proposed design.

## Source-ledger limits

- Apply the closed ledger and eligibility rules in [Method coaching](core-method-coaching.md); label every row as metadata-, abstract-, or full-text-level.
- Use method sources to support design or uncertainty choices only within the reported apparatus, population, scale, and conditions.
- State explicitly what each source does not support, including untested calibration ranges, causal effects, reproducibility, transfer, or safety.
- Block conflicted or unresolved citations, and do not use a verified preprint as the sole support for a safety-related conclusion.
