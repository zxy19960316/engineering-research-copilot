# F04 M2.1.1 Formal Direction Confirmation Gate

Status: `M2.1.1_VALID` and `waiting_for_user_confirmation`

The M2 bundle is [f04-m2-direction-bundle.json](./f04-m2-direction-bundle.json). It embeds the validator-passing M1.2 source whose canonical SHA-256 is `53f7ff7baad4f9b13b5f27ae1a52010dc640fe45cb7a2fdd05225019882c3924`. The M2 validator receipt is [f04-m2-validation.json](./f04-m2-validation.json).

## Formal directions

### `F04-D01` — provisional_main

Traceability-first public bearing-vibration data audit. Screen declared units, sensor/DAQ provenance, operating conditions, calibration clues, repeatability/reproducibility, and UQ readiness before comparing model claims. Tier: `transfer-supported`; confidence: `medium`; ceiling: 16 h offline analysis, six public records, zero downloads or equipment sessions.

Selected-direction excerpt SHA-256: `1f81072903df3afa27d49bd06c17209141014ac8ea5026973a8bc7bd8e69b310`

### `F04-D02` — adjacent_alternative

R&R-aware cross-dataset bearing measurement comparison. Pre-register compatible speed/load/fault strata and separate within-record, refit/mounting, and between-record variance. Tier: `transfer-supported`; confidence: `medium`; ceiling: 24 h offline analysis, four public records, zero downloads or equipment sessions.

Selected-direction excerpt SHA-256: `3646fd2fb8adceaedb8bf14cbf588bcb1b9c5415e57fef237a789020adc71246`

### `F04-D03` — transfer_exploration

Uncertainty-aware generalization under unseen bearing conditions. Treat uncertainty-weighted cross-condition transfer as a mechanism-plausible hypothesis and require provenance coverage plus held-out interval coverage. Tier: `mechanism-plausible`; confidence: `medium`; ceiling: 32 h offline analysis, five public records, zero downloads or equipment sessions.

Selected-direction excerpt SHA-256: `f5fa78278ae9b78d1d609a812745308a8827b13a31359136738581bf797cca07`

## Pre-confirmation binding

Pre-confirmation bundle SHA-256: `884e80387776ecdf3963a3db79c1bec3eb8fe48f65f17c0fc8852d61b54f8678`

This is the validator-defined canonical hash after normalizing the decision to `selected_direction_id=null`, `status=waiting_for_user_confirmation`, `permitted_next_actions=[confirm, modify, reject]`, and `confirmation_event=null`. The current bundle already has that exact state. `route_output` is `null`.

## User action

Send exactly one of these phrases to select a direction:

- `Confirm F04 direction F04-D01`
- `Confirm F04 direction F04-D02`
- `Confirm F04 direction F04-D03`

No confirmation event has been created in this upstream task. No route output, M3 method card, payload, prompt, outcome, or acceptance artifact has been generated.

## Boundaries

The portfolio preserves transfer hypotheses and counter-evidence. It does not establish a common calibration standard, instrument traceability for every public record, or target-domain success. Any later route requires the exact user confirmation event and must remain within the selected direction's gates and ceilings.
