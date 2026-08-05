# M3.1.1 fresh-context forward evaluation — observed outcomes

Date: `2026-08-05`

Status: `NOT_ACCEPTED`; M3 remains `IN_PROGRESS`; M4 remains `NOT_STARTED`.

| Case | Observed validator result | One-shot evidence | Acceptance |
| --- | --- | --- | --- |
| m3-f01 | `invalid ['unreadable_or_invalid_json']` | `finalization=1, validator=1` | `False` |
| m3-f02 | `valid` | `finalization=1, validator=1` | `True` |
| m3-f03 | `invalid ['invalid_m3_bundle', 'invalid_source_m2_bundle', 'unknown_m3_bundle_fields']` | `finalization=1, validator=1` | `False` |
| m3-f04 | `NOT_RUN` | `finalization=0, validator=0` | `False` |
| m3-f05 | `invalid ['unreadable_or_invalid_json']` | `finalization=1, validator=1` | `False` |

F01 preserved `unreadable_or_invalid_json`; F02 is the only observed valid case; F03 preserved extra structural errors rather than being relabeled as the single expected code; F04 is `NOT_RUN`; F05 preserved a one-shot invalid receipt without an output bundle.

No method execution, experiment, simulation, training, download, service, deployment, resource allocation, or safety/operational claim occurred. The previous revision-one failure files remain preserved under `evals/m3/results/forward/`.

The exact closure-head push is intentionally not authorized by these results: the fresh acceptance gate and F04 prerequisite gate are not green.
