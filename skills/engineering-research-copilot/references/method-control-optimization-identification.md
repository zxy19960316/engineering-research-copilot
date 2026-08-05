# Control, Optimization, and System Identification

Apply [Method coaching](core-method-coaching.md) first. Use this family protocol to populate only the closed card fields permitted by that protocol; do not create a control route or authorize closed-loop operation.

## Applicability

- Select `control_optimization_identification` for claims about system identification, state or parameter estimation, controller design, constrained optimization, or closed-loop performance.
- Bind the card only to M2-derived claims, decision metrics, required preconditions, and resource ceilings.
- Put the plant or model identity, excitation and observation records, objective and constraint definitions, operating envelope, baseline implementation, and safety-limit specification in `applicability.required_inputs`.
- Put invalid provenance, unavailable safe excitation, failed identifiability or observability, undefined constraints or shutdown authority, unresolved required inputs, and unavailable specialist safety review in `applicability.incompatible_conditions`.
- Reserve `stop_conditions` and `pivot_conditions` exclusively for closed numeric criterion objects; do not encode missing artifacts, provenance failures, or safety gates there.
- Separate identification, estimation, optimization, and closed-loop claims so evidence for one does not automatically support another.

## Assumptions

- State model structure, operating region, observability, controllability, stationarity, noise, delay, actuator, sensor, and disturbance assumptions.
- State the objective, constraints, horizon, feasibility assumptions, and intended closed-loop operating envelope.
- Label linearization, plant-model equivalence, persistent excitation, and transfer to new regimes as hypotheses until checked.

## Minimum resources

- Put only finite, non-boolean numeric requirements such as excitation-sample counts, validation-scenario counts, sampling capacity, time, memory, or compute capacity in `minimum_resources`.
- Bind every row by `source_constraint_id`, `resource`, and `unit` to an inherited M2 resource ceiling whose operator is `<` or `<=`; remain strictly within that ceiling.
- Keep excitation records, sensors, plant or model definitions, objective and constraint records, baseline implementations, and shutdown specifications in `applicability.required_inputs`, not in `minimum_resources`.
- Treat an absent matching ceiling as an incompatible input state, not as permission to invent or widen a resource allowance.

## Baselines and controls

- Include a simple controller, estimator, identification model, or optimization heuristic as the primary baseline.
- Compare alternatives on identical disturbances, initial conditions, constraints, horizons, objectives, and data partitions.
- Include open-loop, nominal-model, or no-adaptation controls only when safe and relevant to the claim.

## Procedure

- Check that proposed excitation is informative over the target dynamics and remains within inherited and safety constraints.
- Check structural and practical identifiability, observability, parameter correlation, and uncertainty before interpreting fitted parameters.
- Define objectives and constraints independently of the candidate solution; check feasibility before comparing optimality.
- Evaluate stability margins, delay, saturation, disturbances, model mismatch, uncertainty, and constraint satisfaction before recommending closed-loop use.
- Separate offline identification or simulation checks from hardware-in-the-loop and real-system evidence.
- Keep the outline advisory until the user separately authorizes any excitation, optimization run, or closed-loop execution.

## Metrics

- Use only selected-direction metric IDs and units in `primary_metrics`, stop conditions, and pivot conditions.
- Report fit and residual diagnostics for identification; report tracking, regulation, effort, constraint violations, robustness margins, and worst-case behavior for control.
- Report feasibility, objective value, optimality gap or bound, run variability, and constraint violations for optimization when available.

## Uncertainty

- Quantify parameter, state, disturbance, noise, delay, model-form, and operating-condition uncertainty relevant to the decision.
- Propagate identification uncertainty into estimator, controller, or optimizer assessment rather than treating fitted values as exact.
- Test sensitivity to initialization, excitation spectrum, model order, regularization, horizons, weights, and solver settings where applicable.

## Validation

- Validate residual independence, held-out prediction, identifiability, and parameter plausibility before using an identified model.
- Validate robust stability, performance, and constraint satisfaction across declared uncertainties and credible disturbances before closed-loop claims.
- Verify optimization results with feasibility checks, repeat starts or bounds when appropriate, and comparison to the simple baseline.
- Treat structural bundle validation as offline contract evidence, not as plant, controller, or optimizer performance.

## Failure modes

- List insufficient excitation, non-identifiability, hidden feedback, biased noise, drift, actuator saturation, estimator divergence, unstable poles, infeasibility, local minima, and model mismatch when relevant.
- Explain how each listed failure could change the bound claim or metric.
- Preserve unstable, infeasible, and unidentifiable outcomes; do not discard them as tuning artifacts.

## Stop/Pivot conditions

- Populate `stop_conditions` and `pivot_conditions` only with the closed numeric criterion objects defined by [Method coaching](core-method-coaching.md).
- In `bounded` mode, copy each applicable `metric_id`, `operator`, finite `value`, and `unit` from a matching selected-direction `minimum_decisive_test` stop or pivot criterion; in `route_specific` mode, copy them from the corresponding validated route condition.
- Use only criteria relevant to instability, constraint violation, estimator divergence, infeasibility, or identifiability; preserve the upstream operator, value, and unit verbatim.
- Fail closed and request upstream criterion repair when no applicable numeric stop or pivot criterion exists; never invent, estimate, or tune a threshold inside M3.
- Put unsafe excitation, failed identifiability or observability, invalid provenance, undefined constraints or shutdown authority, and safety-review failures in `applicability.incompatible_conditions`, not in numeric condition lists.

## Safety boundaries

- Require qualified controls and domain review before hardware excitation, actuator commands, online adaptation, protection interaction, or operation near physical limits.
- Require independently defined interlocks, fallback control, shutdown criteria, and manual authority before any separately authorized closed-loop test.
- Do not execute identification, optimization, controller deployment, or plant operation through method coaching.

## Source-ledger limits

- Apply the closed ledger and eligibility rules in [Method coaching](core-method-coaching.md); label every row as metadata-, abstract-, or full-text-level.
- Use method sources only within their demonstrated plant class, excitation, constraints, uncertainty, and operating region.
- State explicitly what each source does not support, including stability beyond analyzed regimes, global optimality, online safety, deployment, or transfer.
- Block conflicted or unresolved citations, and do not use a verified preprint as the sole support for a safety-related conclusion.
