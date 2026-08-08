# F01/F05 M2.1.1 pre-confirmation construction notes

Status: draft waiting for mandatory user confirmation; no confirmation event exists.

## Scope and provenance

- Baseline commit: `d0f5e9017044ba35d0ac4559591028228f3b22d8`.
- Upstream reference: accepted Case F pre-confirmation bundle only; its confirmation event and route output were not read into this construction.
- Embedded M1 source: copied from the upstream Case F bundle without changing its parsed content; no paper search, network request, citation addition, or external verification was performed.
- No M3 validator, test, fixture, old M3 output, route, experiment, training, download, service, deployment, or resource allocation was used.
- Embedded M1 canonical SHA-256: `667fcae265e6ac01699bf6b7f328ca6ef4bbcbb0ede2d508a9970d5c8474e376`.

## New formal directions

- `NEML-F01-D1` — provisional main: nuclear engineering × ML physics-constrained uncertainty-aware SB-LOCA diagnosis.
- `NEML-F01-D2` — adjacent alternative: forecast-assisted SB-LOCA break-extent diagnosis; one method-axis change from the main card.
- `NEML-F01-D3` — transfer exploration: open-set Bayesian SB-LOCA triage; at least two axis changes from the main card.

## Claim coverage

Every selected metric has role-matched evidence, explicit target-domain preconditions, and finite numeric `success`, `stop`, and `pivot` criteria. Stop takes precedence when a value also falls inside a broader pivot region.

### NEML-F01-D1
- `C-NEML-F01-D1-PRED` (predictive_performance) → `M-NEML-F01-D1-MAE`: success >= 5.0 percent; stop <= -5.0 percent; pivot < 5.0 percent.
- `C-NEML-F01-D1-UQ` (uncertainty_quality) → `M-NEML-F01-D1-ECE`: success <= 0.08 fraction; stop > 0.15 fraction; pivot > 0.08 fraction.
- `C-NEML-F01-D1-DATA` (data_availability) → `M-NEML-F01-D1-N`: success >= 30 count; stop < 20 count; pivot < 30 count.
- Target preconditions: P-NEML-F01-D1-MANIFEST, P-NEML-F01-D1-SPLIT, P-NEML-F01-D1-DOMAIN, P-NEML-F01-D1-PHYSICS.
- Resource ceilings: one GPU, 24 GiB peak VRAM, 14 calendar days, and two bounded fits.

### NEML-F01-D2
- `C-NEML-F01-D2-PRED` (predictive_performance) → `M-NEML-F01-D2-MAE`: success >= 5.0 percent; stop <= -5.0 percent; pivot < 5.0 percent.
- `C-NEML-F01-D2-UQ` (uncertainty_quality) → `M-NEML-F01-D2-COV`: success >= 0.85 fraction; stop < 0.7 fraction; pivot < 0.85 fraction.
- `C-NEML-F01-D2-DATA` (data_availability) → `M-NEML-F01-D2-N`: success >= 30 count; stop < 20 count; pivot < 30 count.
- Target preconditions: P-NEML-F01-D2-MANIFEST, P-NEML-F01-D2-SPLIT, P-NEML-F01-D2-DOMAIN.
- Resource ceilings: one GPU, 24 GiB peak VRAM, 14 calendar days, and two bounded fits.

### NEML-F01-D3
- `C-NEML-F01-D3-PRED` (predictive_performance) → `M-NEML-F01-D3-RECALL`: success >= 0.9 fraction; stop < 0.75 fraction; pivot < 0.9 fraction.
- `C-NEML-F01-D3-UQ` (uncertainty_quality) → `M-NEML-F01-D3-ECE`: success <= 0.08 fraction; stop > 0.15 fraction; pivot > 0.08 fraction.
- `C-NEML-F01-D3-OOD` (open_set_detection) → `M-NEML-F01-D3-AUROC`: success >= 0.85 area; stop < 0.7 area; pivot < 0.85 area.
- `C-NEML-F01-D3-DATA` (data_availability) → `M-NEML-F01-D3-N`: success >= 30 count; stop < 20 count; pivot < 30 count.
- Target preconditions: P-NEML-F01-D3-MANIFEST, P-NEML-F01-D3-SPLIT, P-NEML-F01-D3-DOMAIN, P-NEML-F01-D3-OOD.
- Resource ceilings: one GPU, 24 GiB peak VRAM, 14 calendar days, and two bounded fits.

## Confirmation gate

`direction_decision.status` is `waiting_for_user_confirmation`; `selected_direction_id` and `confirmation_event` are null; `route_output` is null. The only next step requested is the exact message:

`我确认正式方向<NEML-F01-D1>。`

The bundle is not accepted, and F02/F03/F05 work remains not started.

## Hashes

- Bundle canonical SHA-256: `6ab5d3d67f5450794214b2199d2f2e9ca3ed301e2773c763cff2adbfcb49dd8c`.
- Bundle file-byte SHA-256: `965eefbbd302ad173a252d2b7b60d3457f219d522d9cf9ddbcde2d1b47b3a339`.

## M2 validator receipt

- Validator result: `valid` with exit code `0`; this is an M2.1.1 structural contract result only.
- Raw receipt: `evals/m2/results/2026-08-05-f01-f05-nuclear-ml-pre-confirmation.validation.json`.
