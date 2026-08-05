# Modeling, Simulation, and VVUQ

Apply [Method coaching](core-method-coaching.md) first. Use this family protocol to populate only the closed card fields permitted by that protocol; do not create or execute a simulation route.

## Applicability

- Select `modeling_simulation_vvuq` for claims about mathematical or computational models, numerical predictions, scenario studies, digital twins, or multiphysics simulation.
- Bind the card only to M2-derived claims, decision metrics, required preconditions, and resource ceilings.
- Keep code verification, solution verification, validation, and uncertainty quantification distinct throughout the card.

## Assumptions

- State governing equations, constitutive relations, geometry, dimensionality, boundary and initial conditions, closure relations, coupling assumptions, and intended use.
- State the spatial, temporal, parameter, regime, and population domain over which conclusions may apply.
- Label surrogate validity, scale transfer, omitted physics, and extrapolation as unresolved hypotheses until decisive evidence supports them.

## Minimum resources

- Identify only the minimum code access, benchmark problems, reference solutions, discretizations, solver runs, validation observations, and compute budget needed for the bound claim.
- Bind every quantitative minimum to an inherited M2 ceiling as required by the core protocol.
- Treat missing reference solutions, convergence evidence, validation data, or compute capacity as explicit preconditions rather than silently simplifying the claim.

## Baselines and controls

- Include a simpler analytical, reduced-order, empirical, or lower-fidelity model baseline appropriate to the claim.
- Hold inputs and comparison conditions constant when attributing improvement to a model, coupling, closure, or solver change.
- Include limiting cases, conservation checks, or benchmark solutions as controls when available.

## Procedure

- Perform code verification against analytical solutions, manufactured solutions, trusted benchmarks, or independently checked invariants to test equation implementation.
- Perform solution verification with mesh, time-step, iteration, tolerance, or solver convergence studies where applicable; justify non-applicability explicitly.
- Perform validation against independent observations within a declared validation domain and quantify model discrepancy separately from numerical error.
- Perform sensitivity analysis before interpreting influential parameters or prioritizing uncertainty reduction.
- Perform UQ across input, parameter, numerical, and model-form uncertainty without collapsing them into one unexplained error term.
- Keep the outline advisory until the user separately authorizes simulation execution.

## Metrics

- Use only selected-direction metric IDs and units in `primary_metrics`, stop conditions, and pivot conditions.
- Report quantities appropriate to the claim, including conservation residuals, observed order, discretization uncertainty, benchmark error, validation discrepancy, calibration error, or predictive coverage.
- Pair aggregate fit metrics with local, regime-specific, transient, or worst-case errors when those affect the intended use.

## Uncertainty

- Separate parameter, input, numerical, structural, and observational uncertainty and state how each is represented and propagated.
- Report sensitivity to uncertain assumptions, priors, ranges, correlations, boundary conditions, and solver settings.
- Distinguish parameter calibration from validation and prevent calibration data from serving as independent validation evidence.

## Validation

- Verify code correctness, numerical convergence, and comparison-data independence before making predictive claims.
- Define the validation domain and intended use; identify every extrapolation beyond tested regimes.
- Treat simulation-to-observation agreement as conditional validation evidence, never as real-world proof, causal proof, operational qualification, or safety validation.
- Treat structural bundle validation as offline contract evidence, not as evidence that a model is correct or predictive.

## Failure modes

- List coding defects, unconverged solutions, unstable coupling, non-identifiable calibration, compensating errors, omitted physics, regime extrapolation, data reuse, and numerical artifacts when relevant.
- Explain how each listed failure could change the bound claim or metric.
- Preserve divergent, non-convergent, and invalid runs as failures rather than selecting only favorable solutions.

## Stop/Pivot conditions

- Set at least one numeric stop condition, with a selected-direction metric and unit, for failed convergence, unacceptable conservation residual, excessive validation discrepancy, or uncertainty too large for the decision.
- Stop predictive interpretation when code verification, solution verification, validation independence, or an M2-required precondition fails.
- Pivot only within inherited resources, for example to a simpler model, narrower validation domain, or different observable, and state which claim is reduced.

## Safety boundaries

- Require qualified domain and VVUQ review before using model output for hazardous design, operational limits, licensing, certification, or safety decisions.
- Do not execute simulation software, allocate compute, calibrate an operational model, or issue a safety determination through method coaching.
- Preserve conservative physical, facility, regulatory, and specialist constraints over apparent numerical agreement.

## Source-ledger limits

- Apply the closed ledger and eligibility rules in [Method coaching](core-method-coaching.md); label every row as metadata-, abstract-, or full-text-level.
- Use method sources only for the equations, numerical method, validation regime, uncertainty treatment, and limitations they actually report.
- State explicitly what each source does not support, including untested regimes, predictive accuracy, real-world transfer, operational qualification, or safety.
- Block conflicted or unresolved citations, and do not use a verified preprint as the sole support for a safety-related conclusion.
