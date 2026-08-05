# Signal Processing and Diagnostics

Apply [Method coaching](core-method-coaching.md) first. Use this family protocol to populate only the closed card fields permitted by that protocol; do not create a diagnostic route or authorize acquisition or operational decisions.

## Applicability

- Select `signal_diagnostics` for claims about sensing, preprocessing, feature extraction, detection, localization, diagnosis, prognosis inputs, or condition monitoring.
- Bind the card only to M2-derived claims, decision metrics, required preconditions, and resource ceilings.
- Distinguish event detection, fault diagnosis, localization, and severity estimation so a metric for one task does not stand in for another.

## Assumptions

- State signal source, sensor response, sampling clock, bandwidth, synchronization, operating states, label origin, noise, missingness, and stationarity assumptions.
- State the independent unit and the boundaries between events, windows, assets, runs, operators, sites, and time periods.
- Label sensor equivalence, source-domain transfer, and unobserved-fault behavior as hypotheses until checked.

## Minimum resources

- Identify only the minimum raw signal provenance, sampling metadata, sensor calibration, labeled events, normal exposure, independent units, storage, and analysis capacity needed for the bound claim.
- Bind every quantitative minimum to an inherited M2 ceiling as required by the core protocol.
- Treat missing timestamps, sampling rates, labels, asset identities, or acquisition provenance as unmet preconditions rather than reconstructing them silently.

## Baselines and controls

- Include a simple threshold, spectral, statistical, or domain-rule baseline appropriate to the diagnostic task.
- Compare methods on identical independent units, operating regimes, label definitions, and evaluation windows.
- Include healthy or background exposure controls and known nuisance or sensor-artifact controls when available.

## Procedure

- Check sensor bandwidth, sampling rate, clock quality, anti-alias filtering, synchronization, saturation, clipping, and missing intervals before feature construction.
- Segment by asset, run, event, scenario, subject, site, or time boundary before splitting; prevent overlapping windows or correlated descendants from crossing partitions.
- Fit normalization, filtering parameters, imputation, feature selection, decomposition, thresholds, and learned preprocessing only on training data.
- Preserve a raw-to-segment provenance chain with label source and every preprocessing transform.
- Test performance across operating regimes, noise levels, sensor states, distribution shifts, and unseen units relevant to the claim.
- Keep the outline advisory until the user separately authorizes acquisition, processing, or operational use.

## Metrics

- Use only selected-direction metric IDs and units in `primary_metrics`, stop conditions, and pivot conditions.
- Use event- or time-aware detection metrics, class-sensitive diagnosis metrics, localization error, and severity error according to the bound task.
- Report false alarms with an exposure denominator such as time, cycle, asset, or opportunity; do not report a bare false-alarm count.
- Include missed-event rate, detection delay, per-class results, calibration, and uncertainty when they affect the claim.

## Uncertainty

- Quantify variation across independent units, acquisition periods, operating regimes, sensor states, labels, thresholds, and random seeds where applicable.
- Separate measurement noise, label uncertainty, sampling variability, threshold uncertainty, and distribution shift.
- Report confidence intervals or repeated-evaluation variability at the independent-unit level rather than treating overlapping windows as independent.

## Validation

- Verify signal provenance, units, sampling and aliasing assumptions, segmentation boundaries, train-only preprocessing, label alignment, and exposure accounting.
- Test shift across relevant assets, sites, regimes, time periods, fault types, or sensor failures and identify unsupported regions.
- Audit errors by class, regime, sensor state, and nuisance condition instead of relying on one aggregate score.
- Treat structural bundle validation as offline contract evidence, not as diagnostic accuracy, field performance, or operational qualification.

## Failure modes

- List aliasing, clipping, clock drift, leakage, duplicated windows, label delay, class imbalance, prevalence shift, sensor failure, domain shift, confounding operating states, and alert flooding when relevant.
- Explain how each listed failure could change the bound claim or metric.
- Preserve false alarms, missed events, invalid provenance, and unsupported shifts; do not hide them through favorable aggregation.

## Stop/Pivot conditions

- Set at least one numeric stop condition, with a selected-direction metric and unit, for excessive false-alarm exposure, missed events, detection delay, shift degradation, or invalid sampling behavior.
- Stop immediately when raw signal provenance, sampling rate, time alignment, partition independence, or label origin is invalid or unresolved.
- Pivot to corrected acquisition metadata, coarser claims, a simpler baseline, revised segmentation, or human review only within inherited resources and with the changed assumption explicit.

## Safety boundaries

- Require qualified signal, instrumentation, and domain review before using diagnostics for alarms, shutdowns, maintenance deferral, clinical action, or other safety-relevant decisions.
- Keep the diagnostic output advisory unless separately validated and authorized for its intended operational role; preserve existing protection and human oversight.
- Do not acquire signals, modify monitoring systems, deploy detectors, or issue operational decisions through method coaching.

## Source-ledger limits

- Apply the closed ledger and eligibility rules in [Method coaching](core-method-coaching.md); label every row as metadata-, abstract-, or full-text-level.
- Use method sources only within their reported sensors, sampling, segmentation, label quality, prevalence, operating regimes, and evaluation units.
- State explicitly what each source does not support, including unseen assets, field false-alarm burden, causal diagnosis, deployment, or safety.
- Block conflicted or unresolved citations, and do not use a verified preprint as the sole support for a safety-related conclusion.
