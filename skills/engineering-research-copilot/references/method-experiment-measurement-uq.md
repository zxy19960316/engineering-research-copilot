# Experiment, Measurement, and Uncertainty Quantification

Apply [Method coaching](core-method-coaching.md) first. Use this family protocol to populate only the closed card fields permitted by that protocol; do not create a route or authorize data collection.

## Applicability

- Select `experiment_measurement_uq` for claims that require controlled intervention, physical measurement, calibration, repeatability, reproducibility, or propagated measurement uncertainty.
- Bind the card only to M2-derived claims, decision metrics, required preconditions, and resource ceilings.
- Hand off modeling-, control-, or signal-dominant checks to their directly linked family protocol instead of duplicating them here.

## Assumptions

- State the measurand, operating range, experimental unit, response, intervention, nuisance factors, and independence assumptions.
- State whether the measurement chain is stable, traceable, and sensitive enough for the minimum meaningful effect.
- Mark unverified apparatus behavior, transfer, scale-up, and causal assumptions as hypotheses.

## Minimum resources

- Identify only the minimum specimens or units, repetitions, reference standards, sensors, acquisition capacity, time, and analysis resources needed for the bound claim.
- Bind every quantitative minimum to an inherited M2 ceiling as required by the core protocol.
- Treat unavailable calibration, control, or uncertainty inputs as unmet preconditions, not as permission to widen resources.

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

- Set at least one numeric stop condition, with a selected-direction metric and unit, for invalid calibration, excessive drift, inadequate precision, failed controls, or an uncertainty interval too wide for the decision.
- Stop before collection when the measurement model, calibration trace, control, uncertainty budget, or required precondition is missing.
- Pivot only to a bounded alternative that remains within inherited resources and state which assumption or design element changes.

## Safety boundaries

- Require qualified laboratory or domain review for hazardous materials, radiation, pressure, high voltage, biological exposure, human participants, destructive testing, or regulated measurements.
- Do not convert method coaching into equipment operation, specimen handling, data collection, or a safety determination.
- Apply the stricter facility, legal, ethical, and specialist boundary whenever it conflicts with a proposed design.

## Source-ledger limits

- Apply the closed ledger and eligibility rules in [Method coaching](core-method-coaching.md); label every row as metadata-, abstract-, or full-text-level.
- Use method sources to support design or uncertainty choices only within the reported apparatus, population, scale, and conditions.
- State explicitly what each source does not support, including untested calibration ranges, causal effects, reproducibility, transfer, or safety.
- Block conflicted or unresolved citations, and do not use a verified preprint as the sole support for a safety-related conclusion.
