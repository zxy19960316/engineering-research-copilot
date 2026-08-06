# M3.1.1 r3 fresh-context forward evaluation — observed outcomes

Date: `2026-08-06`

Status: `NOT_ACCEPTED`; M3 remains `IN_PROGRESS`; M4 and M5 remain `NOT_STARTED`.

All five inputs were eligible and all five prompts were hash-frozen before dispatch. Each fresh task produced exactly one final answer. Each applicable composer was invoked exactly once, and each outcome validator was invoked exactly once. No failed case was repaired or retried.

| Case | Fresh task | Model final / composer result | One-shot validator result | Acceptance |
| --- | --- | --- | --- | --- |
| `m3-f01` | `019fd576-bd71-7f40-ab82-4b59b450094f` | JSON final; composer rejected `malformed_m3_bundle` | `invalid ['unreadable_or_invalid_forward_outcome_input']` | `False` |
| `m3-f02` | `019fd576-cb45-7d51-ad50-39a23a7e388d` | `route_incompatible` with empty cards/overlays; composer rejected `empty_method_cards`, `invalid_coaching_mode` | `invalid ['unreadable_or_invalid_forward_outcome_input']` | `False` |
| `m3-f03` | `019fd576-d9de-7032-8bf5-0756a5c360d6` | Expected blocked JSON with `unsupported_approved_constraint_change_provenance` | `invalid ['unreadable_or_invalid_forward_outcome_input']`; sole invocation used a nonexistent r3 source alias | `False` |
| `m3-f04` | `019fd57b-5ac9-7893-b22d-22a9f7bb58cb` | JSON final; composer rejected `malformed_m3_bundle` | `invalid ['unreadable_or_invalid_forward_outcome_input']` | `False` |
| `m3-f05` | `019fd57b-584b-7860-80d9-ede998cd74da` | Route-specific JSON composed successfully | `accepted`, method bundle `valid`, no errors or gaps | `True` |

F03's model final itself expressed the expected fail-closed terminal code, but the operator passed `evals/m3/forward-inputs-r3/m3-f03.bundle.json` instead of the frozen `evals/m3/forward-inputs-r2/m3-f03-approved-change.bundle.json` to the sole validator invocation. The resulting invalid receipt is preserved as consumable evidence. It was not rerun.

Because only one of five cases was accepted, r3 does not supersede r2 for acceptance. The local closure suite, closure commit, push, exact-HEAD GitHub Actions validation, M4, and M5 were not run.

No method route, experiment, simulation, training, inference, download, network service, deployment, target-domain transfer validation, operational decision, or nuclear-safety validation occurred or is claimed.
