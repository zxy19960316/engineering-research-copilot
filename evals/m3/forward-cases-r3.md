# M3.1.1 R3 Fresh-Context Cases

These five cases are new one-shot evaluations. The frozen r2 evidence remains historical and must not be read by a fresh context. Every case starts from one immutable, eligibility-audited M2.1.1 input and one frozen prompt.

## Shared execution contract

- Read `AGENTS.md`, the root Skill, the prompt, the named M2 input, `core-method-coaching.md`, and only the family or overlay references named for the case.
- Do not read tests, fixtures, r2 prompts or results, r3 results from another case, validators, composers, acceptance manifests, or another task conversation.
- Do not use network access or any external tool.
- Do not execute a route, experiment, simulation, training, inference, download, upload, service, deployment, equipment operation, resource allocation, or safety action.
- Finalize exactly once with exactly one compact JSON object and no Markdown fence, explanation, or surrounding text.
- Do not repair or retry malformed or validator-rejected output. The first finalization is the consumed result.

## Case matrix

| Case | Immutable input | Allowed method references | Required result |
|---|---|---|---|
| `m3-f01` | `evals/m3/forward-inputs-r2/m3-f01-bounded-confirmed.bundle.json` | `core-method-coaching.md`, `method-data-ml-hybrid.md` | bounded `data_ml_hybrid` payload; no overlay |
| `m3-f02` | `evals/m3/forward-inputs-r2/m3-f02-route-compatible.bundle.json` | `core-method-coaching.md`, `method-data-ml-hybrid.md`, `domain-nuclear-ml.md` | route-specific `data_ml_hybrid` payload with nuclear overlay |
| `m3-f03` | `evals/m3/forward-inputs-r2/m3-f03-approved-change.bundle.json` | `core-method-coaching.md` | exact expected blocked outcome; no cards or overlay |
| `m3-f04` | `evals/f04-upstream/m2/f04-m2-confirmed.bundle.json` | `core-method-coaching.md`, `method-experiment-measurement-uq.md` | bounded `experiment_measurement_uq` payload; no overlay |
| `m3-f05` | `evals/m3/forward-inputs-r2/m3-f02-route-compatible.bundle.json` | `core-method-coaching.md`, `method-data-ml-hybrid.md`, `domain-nuclear-ml.md` | route-specific `data_ml_hybrid` payload with explicit nuclear boundaries |

For F01, F02, F04, and F05, the final JSON object is a three-field model payload. A deterministic composer later embeds the immutable M2 source and recomputes both hashes. For F03, the final JSON object is already the complete blocked outcome. No fresh context writes a bundle, outcome wrapper, receipt, context record, or repository file.

## Expected acceptance states

```text
m3-f01 -> outcome_kind=bundle, coaching_mode=bounded, status=accepted
m3-f02 -> outcome_kind=bundle, coaching_mode=route_specific, status=accepted
m3-f03 -> outcome_kind=blocked, terminal_code=unsupported_approved_constraint_change_provenance, status=accepted_expected_block
m3-f04 -> outcome_kind=bundle, coaching_mode=bounded, status=accepted
m3-f05 -> outcome_kind=bundle, coaching_mode=route_specific, status=accepted
```

These are contract expectations, not empirical performance expectations. A mismatch remains visible and blocks M3 closure.
