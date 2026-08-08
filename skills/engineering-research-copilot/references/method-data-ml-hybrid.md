# Data, Machine Learning, and Hybrid Methods

Apply [Method coaching](core-method-coaching.md) first. Use this family protocol to populate only the closed card fields permitted by that protocol; do not create a data or training route, run a model, or authorize deployment.

## Applicability

- Select `data_ml_hybrid` for claims about statistical learning, machine learning, physics-informed learning, surrogate models, data fusion, or hybrid data-and-model methods.
- Bind the card only to M2-derived claims, decision metrics, required preconditions, and resource ceilings.
- Put dataset and label provenance, entity/scenario/time identities, split definitions, preprocessing specifications, feature and target definitions, intended-use conditions, calibration requirements, and the declared in-distribution and out-of-distribution boundaries in `applicability.required_inputs`.
- Put invalid provenance, non-independent partitions, unresolved leakage, unavailable labels or target definitions, unsupported deployment conditions, unresolved required inputs, and unavailable specialist safety review in `applicability.incompatible_conditions`.
- Reserve `stop_conditions` and `pivot_conditions` exclusively for closed numeric criterion objects; do not encode missing artifacts, provenance failures, or safety gates there.
- Separate predictive, causal, surrogate, anomaly-detection, and decision-support claims so performance evidence for one task does not support another automatically.

## Assumptions

- State the observational unit, target population, sampling mechanism, label process, missingness, dependence, stationarity, exchangeability, and class-prevalence assumptions.
- State the relationship between physics-based and learned components, including which constraints are exact, approximate, learned, or unchecked.
- Label generalization across entities, scenarios, sites, time periods, sensors, fidelities, or domains as a hypothesis until tested on the claimed target distribution.

## Minimum resources

- Put only finite, non-boolean numeric requirements such as independent-unit counts, labeled-event counts, repeat or seed counts, time, memory, storage, or compute capacity in `minimum_resources`.
- Bind every row by `source_constraint_id`, `resource`, and `unit` to an inherited M2 resource ceiling whose operator is `<` or `<=`; remain strictly within that ceiling.
- Keep datasets, labels, split manifests, preprocessing specifications, code identities, trained artifacts, and environment records in `applicability.required_inputs`, not in `minimum_resources`.
- Treat an absent matching ceiling as an incompatible input state, not as permission to invent or widen a resource allowance.

## Baselines and controls

- Include a simple non-ML, domain-rule, persistence, analytical, or classical statistical baseline appropriate to the claim.
- Compare every candidate on identical entity-, scenario-, and time-aware partitions, preprocessing provenance, evaluation units, and resource accounting.
- Include component-removal, shuffled-label, or no-physics controls when they isolate the claimed contribution without creating unsafe or misleading comparisons.

## Procedure

- Define entity, scenario, site, asset, subject, batch, and time boundaries before splitting; keep correlated descendants and future information out of training partitions.
- Fit imputation, normalization, augmentation, feature selection, dimensionality reduction, resampling, calibration, and learned preprocessing only on the training partition, then preserve the fitted-state provenance.
- Freeze the baseline, partitions, primary metrics, ablation plan, seeds or repeat policy, and numeric stop and pivot criteria before comparing methods.
- Run ablations that isolate every claimed learned, physical, fusion, or regularization component, and compare against the simple baseline under the same budget.
- Define calibration and OOD checks whenever the bound claim concerns probability quality, confidence, shift, transfer, novelty, alarms, or decision support.
- Keep the outline advisory until the user separately authorizes training, inference, data processing, or deployment.

## Metrics

- Use only selected-direction metric IDs and units in `primary_metrics`, stop conditions, and pivot conditions.
- Match metrics to the decision, prevalence, cost, and evaluation unit; pair aggregate scores with per-class, per-regime, and worst-slice results where relevant.
- Report calibration error or coverage when claims depend on confidence, and report OOD detection or shifted-domain degradation when claims depend on generalization or transfer.
- Compare accuracy or utility jointly with inherited compute, time, memory, data, and latency limits rather than hiding resource expansion.

## Uncertainty

- Quantify variation across independent entities, scenarios, sites, time periods, folds, random seeds, and repeated fits at the level relevant to the claim.
- Separate sampling, label, measurement, model, parameter, optimization, and distribution-shift uncertainty instead of collapsing them into one score.
- Report intervals or repeat distributions and state the aggregation rule; do not treat correlated rows, windows, or augmented samples as independent replicates.

## Validation

- Audit split independence and preprocessing isolation before interpreting any metric; verify that no label, future, test, or entity-linked information crosses the training boundary.
- Compare the simple baseline and all predeclared ablations under identical partitions and budgets, and preserve unfavorable or unstable repeats.
- Check calibration, OOD behavior, and distribution-shift sensitivity when the bound claim requires them.
- Slice errors by entity, scenario, time, class, operating regime, sensor state, missingness, and relevant protected or safety-critical subgroup; identify unsupported slices explicitly.
- Treat structural bundle validation as offline contract evidence, not as model performance, generalization, causal validity, or deployment qualification.

## Failure modes

- List entity or temporal leakage, preprocessing leakage, label contamination, shortcut learning, confounding, dataset shift, prevalence shift, class imbalance, missing-not-at-random data, overfitting, unstable optimization, miscalibration, OOD overconfidence, and failed hybrid constraints when relevant.
- Explain how each listed failure could change the bound claim or metric.
- Preserve failed seeds, negative ablations, unsupported slices, and shift failures; do not discard them as tuning noise.

## Stop/Pivot conditions

- Populate `stop_conditions` and `pivot_conditions` only with the closed numeric criterion objects defined by [Method coaching](core-method-coaching.md).
- In `bounded` mode, copy each applicable `metric_id`, `operator`, finite `value`, and `unit` from a matching selected-direction `minimum_decisive_test` stop or pivot criterion; in `route_specific` mode, copy them from the corresponding validated route condition.
- Use only criteria relevant to baseline underperformance, calibration failure, OOD or shift degradation, unacceptable slice error, repeat instability, or resource-limit performance; preserve the upstream operator, value, and unit verbatim.
- Fail closed and request upstream criterion repair when no applicable numeric stop or pivot criterion exists; never invent, estimate, tune, or optimize a threshold inside M3.
- Put invalid provenance, leakage, non-independent partitions, missing calibration or OOD definitions, unsupported deployment, and safety-review failures in `applicability.incompatible_conditions`, not in numeric condition lists.

## Safety boundaries

- Require qualified data, ML, domain, security, privacy, and safety review before using outputs for operational control, protection, maintenance deferral, personnel decisions, or other consequential actions.
- Preserve existing deterministic protections, interlocks, conservative rules, and human authority; a learned component must not silently replace them.
- Do not acquire or upload data, train or run models, download weights, allocate compute, deploy services, or issue operational decisions through method coaching.

## Source-ledger limits

- Populate `source_ledger` under the closed ledger and eligibility rules in [Method coaching](core-method-coaching.md); label every row as metadata-, abstract-, or full-text-level.
- Use sources only within their reported data provenance, populations, splits, baselines, metrics, shift conditions, uncertainty treatment, and intended use.
- State explicitly what each source does not support, including causal effects, unseen-domain transfer, calibration, robustness, deployment, or safety.
- Block conflicted or unresolved citations, and do not use a verified preprint as the sole support for a safety-related conclusion.
