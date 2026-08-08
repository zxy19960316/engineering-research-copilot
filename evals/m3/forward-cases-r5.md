# M3.1.1 r5 five-case technical specification

This file is coordinator-side preparation evidence. It is not an allowed read path for a future task and contains no model result, expected answer, task identifier, or fresh-context receipt.

## Frozen boundary

- Schema: `m3.1-forward-acceptance-r5-v1`.
- Result root: `evals/m3/results/forward-r5/`.
- Every case must use the exact nine-key `future_paths` map from the r5 dispatcher contract.
- All future paths are reserved only during preparation; no result, receipt, context, or transaction file exists in the frozen preparation state.
- All task, finalization, preflight, processing, invocation, acceptance, and transaction counters are zero before authorization.

## Frozen cases

| Case | Immutable source lineage | Coaching boundary |
|---|---|---|
| m3-f01 | The r2 bounded-confirmed M2 bundle | Derive a bounded method payload; keep route output absent and preserve upstream constraints. |
| m3-f02 | The r2 route-compatible M2 bundle | Derive a route-specific method payload only from the immutable confirmed route. |
| m3-f03 | The exact r2 approved-change bundle at `evals/m3/forward-inputs-r2/m3-f03-approved-change.bundle.json` | Stop closed on unsupported approved-constraint-change provenance; do not create a card or overlay. |
| m3-f04 | The independently accepted non-nuclear F04 M2 bundle | Derive bounded measurement/uncertainty coaching without nuclear or operational credit. |
| m3-f05 | The r2 route-compatible M2 lineage used by the accepted F05 input audit | Preserve target-domain boundaries, specialist review, and transfer-as-hypothesis language. |

## Prompt and contract boundary

Each prompt is frozen separately under `evals/m3/results/forward-r5/prompts/`. Each prompt permits only the Skill, its named references, the shared r5 model-output contract, itself, and its manifest-selected immutable source input. No prompt authorizes network access, file writes, tests, fixtures, validators, composers, manifests, historical results, or other cases.

The shared contract is `evals/m3/forward-inputs-r5/m3-model-output-contract.schema.json`. It is case-result agnostic, closed at every object boundary, and requires metric IDs as strings in `primary_metrics`. The dispatcher and auditors treat its hash as a frozen input, not as a result.

## Processing contract

The future coordinator must dry-preflight all five cases before any case callback. A finalization is recorded independently from processing. Any post-finalization composer, validator, receipt, context, or transaction failure remains `processing_failed` and cannot be accepted or retried. The coordinator must stop at the authorization gate until the user explicitly authorizes the five frozen r5 contexts exactly once each.
