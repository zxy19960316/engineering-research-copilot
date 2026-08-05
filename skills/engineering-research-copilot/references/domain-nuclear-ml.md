# Nuclear Engineering × Machine Learning Overlay

Apply [Method coaching](core-method-coaching.md) first. Use this additive `nuclear_engineering_ml` overlay only with applicable cards from [Data, machine learning, and hybrid methods](method-data-ml-hybrid.md), [Reliability, safety, and risk](method-reliability-safety-risk.md), [Modeling, simulation, and VVUQ](method-modeling-simulation-vvuq.md), [Signal processing and diagnostics](method-signal-diagnostics.md), [Control, optimization, and identification](method-control-optimization-identification.md), or [Experiment, measurement, and UQ](method-experiment-measurement-uq.md). Populate exactly the closed overlay fields `schema_version`, `overlay_id`, `domain`, `base_card_ids`, `additional_assumptions`, `additional_failure_modes`, `additional_validation_checks`, `additional_stop_conditions`, `specialist_review_boundaries`, `transfer_status`, and `source_ledger`. Treat the last eight as additive payload fields in addition to the first three identity fields; do not copy or replace general procedures.

## Base-card binding

- Populate `base_card_ids` only with unique card IDs from the same validated M3 bundle, and retain every base card's assumptions, resources, checks, failures, conditions, safety boundaries, and ledger.
- Select only the families needed by the confirmed claims and declared intended use; the overlay adds nuclear-specific constraints and never turns bounded coaching into a complete route.
- Keep plant, unit, design, simulator, scenario, operating mode, transient, accident class, fuel cycle, sensor configuration, and time period distinct wherever any of them can create dependence or distribution shift.

## Additional assumptions

- Record which observations are plant data, experimental data, simulator output, synthetic data, or expert judgment, and state the fidelity, operating envelope, configuration identity, and provenance of each.
- State the simulator-to-plant gap, scale and facility differences, physics coverage, sensor equivalence, scenario coverage, and intended nuclear function; do not infer plant validity from simulator performance.
- State the credited and non-credited safety functions, defense-in-depth layers, operator role, automation boundary, and whether the output is informational, advisory, control-related, or protection-related.
- State exactly: nuclear × ML transfer remains a `hypothesis` until a target-domain decisive test supports it.

## Additional failure modes

- Add plant or scenario leakage, simulator artifacts, unmodeled physics, non-conservative surrogate error, conservation-law violation, rare-transient scarcity, sensor drift or failure, OOD overconfidence, configuration drift, common-cause software failure, automation surprise, and misleading operator reliance when relevant.
- Add failures caused by conflating code verification, solution verification, model validation, uncertainty quantification, ML evaluation, and target-domain transfer evidence.
- Add loss or weakening of diversity, redundancy, independence, defense in depth, deterministic protection, conservative limits, human oversight, or shutdown authority as explicit failures.

## Additional validation checks

- Enforce plant-, unit-, design-, scenario-, operating-mode-, configuration-, and time-aware separation before fitting or evaluation; keep correlated simulator descendants and plant records out of opposing partitions.
- Check governing physics, dimensional consistency, conservation of mass, energy, momentum, charge, or neutron balance as applicable, monotonic or limiting behavior, and conservative response in safety-relevant regimes.
- Test declared sensor loss, drift, saturation, bias, timing failure, missing channels, correlated failures, distribution shift, unseen transients, and OOD inputs; verify the fallback and human-visible uncertainty behavior.
- Keep code verification, solution verification, model validation, UQ, ML generalization, simulator-to-plant transfer, and operational qualification as separate evidence claims.
- Require independent nuclear-domain review of scenario coverage, physics checks, uncertainty treatment, safety-function interaction, defense-in-depth preservation, human factors, and claimed intended use.
- State exactly: offline contract validation is not nuclear-safety validation.

## Additional stop conditions

- Populate `additional_stop_conditions` only with the closed numeric `stop` criterion objects defined by [Method coaching](core-method-coaching.md), using selected-direction metric IDs and exact units.
- Copy each applicable operator and finite threshold from the selected-direction minimum decisive test in `bounded` mode or the validated route in `route_specific` mode; never invent or tune a nuclear-safety threshold in M3.
- Use only existing criteria relevant to physics or conservation residuals, target-domain error, OOD or sensor-failure degradation, uncertainty, false alarms, missed events, constraint violations, or defense-in-depth performance.
- Put missing plant/scenario separation, absent target-domain evidence, invalid VVUQ lineage, failed physics checks, unreviewed protection interaction, or licensing uncertainty in base-card `applicability.incompatible_conditions` or `specialist_review_boundaries`, not in fabricated numeric conditions.

## Specialist review boundaries

- Require independent qualified nuclear engineering, VVUQ, instrumentation and controls, human-factors, cybersecurity, radiation-protection, and safety specialists according to the proposed function and hazard scope.
- Preserve licensed technical specifications, regulatory commitments, approved safety analyses, deterministic protection, defense in depth, operator authority, and facility procedures over any method-card recommendation.
- Treat licensing basis, safety classification, software quality assurance, protection-system credit, technical-specification changes, operational limits, emergency procedures, and risk acceptance as regulator, licensee, and specialist decisions outside method coaching.
- Do not authorize plant data access, simulator or plant execution, model training, online adaptation, control action, protection action, maintenance deferral, deployment, licensing conclusions, or nuclear-safety conclusions.

## Source-ledger limits

- Populate the overlay `source_ledger` under the closed rules in [Method coaching](core-method-coaching.md); require at least one eligible non-preprint row whose `support_types` includes `safety`.
- Bind each source to the reported reactor or facility class, scenario, simulator or plant basis, sensor configuration, VVUQ level, safety function, operating envelope, and regulatory context.
- State what each source does not support, including plant transfer, unseen transients, operational qualification, protection credit, licensing acceptance, or nuclear safety.
- Keep preprints limited to method or exploration support and never use them as the sole basis for a main direction or safety-related conclusion.
