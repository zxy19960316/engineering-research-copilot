# M3.1.1 R4 Fresh-Context Cases

These five cases are the successor r4 acceptance set. The immutable r2 and r3 evidence, and the prior blocked r4 byte receipt, remain historical evidence and are not inputs to a fresh context.

## Shared execution contract

- Read only `AGENTS.md`, the root Skill, the named method references, the manifest-selected immutable M2 input, the shared r4 model-output contract, and the case's frozen prompt.
- Do not read tests, fixtures, validators, composers, manifests, historical results, prompts from another case, or another task conversation.
- Do not use network access, external tools, services, or model/API providers.
- Do not write repository files. Finalize exactly once with exactly one compact JSON object and no Markdown fence, explanation, or surrounding text.
- Do not repair, retry, continue, or re-prompt after finalization or after a one-shot downstream invocation.
- Treat the selected M2 input as immutable. Derive every claim, metric, precondition, resource, condition, source, and binding from that input and the named references.

## Case matrix

| Case | Immutable input | Allowed method references | Required final shape |
|---|---|---|---|
| `m3-f01` | `evals/m3/forward-inputs-r2/m3-f01-bounded-confirmed.bundle.json` | `core-method-coaching.md`, `method-data-ml-hybrid.md` | bounded `data_ml_hybrid` payload; no overlay |
| `m3-f02` | `evals/m3/forward-inputs-r2/m3-f02-route-compatible.bundle.json` | `core-method-coaching.md`, `method-data-ml-hybrid.md`, `domain-nuclear-ml.md` | route-specific `data_ml_hybrid` payload with a nuclear overlay |
| `m3-f03` | `evals/m3/forward-inputs-r2/m3-f03-approved-change.bundle.json` | `core-method-coaching.md` | four-field blocked provenance-stop object |
| `m3-f04` | `evals/f04-upstream/m2/f04-m2-confirmed.bundle.json` | `core-method-coaching.md`, `method-experiment-measurement-uq.md` | bounded `experiment_measurement_uq` payload; no overlay |
| `m3-f05` | `evals/m3/forward-inputs-r2/m3-f02-route-compatible.bundle.json` | `core-method-coaching.md`, `method-data-ml-hybrid.md`, `domain-nuclear-ml.md` | route-specific `data_ml_hybrid` payload with explicit nuclear boundaries |

## Frozen acceptance matrix

The coordinator compares only observed, manifest-dispatched evidence against this matrix. A mismatch remains visible and prevents acceptance closure.

| Case | Outcome kind | Coaching mode | Terminal/validation status | Additional requirement |
|---|---|---|---|---|
| `m3-f01` | `bundle` | `bounded` | `accepted` | at least one valid data/ML hybrid card; empty overlay list |
| `m3-f02` | `bundle` | `route_specific` | `accepted` | compatible nuclear ML overlay bound to a base card |
| `m3-f03` | `blocked` | not applicable | `accepted_expected_block` | terminal code `unsupported_approved_constraint_change_provenance`; original limits preserved; applied changes empty |
| `m3-f04` | `bundle` | `bounded` | `accepted` | at least one valid experiment/measurement/UQ card; empty overlay list |
| `m3-f05` | `bundle` | `route_specific` | `accepted` | nuclear overlay includes all four required boundaries and an eligible non-preprint safety source |

## Consumption limits

- The five cases are independently fresh and may run concurrently only after the committed frozen-readiness HEAD exists.
- Each case has exactly one finalization. The manifest-owned dispatcher preflights the source, prompt, contract, hashes, eligibility, and all future output/receipt paths before invoking a consumable callback.
- F01, F02, F04, and F05 may invoke the applicable composer once and the one-shot validator once. F03 invokes no composer and one outcome validator at most once.
- Record the final byte hash, every generated artifact hash, invocation counts, observed status, terminal errors, and accepted/invalid state. Preserve missing, malformed, blocked, invalid, and unexpected evidence without relabeling.

## Scope boundary

This record is offline structural and evidence-grounded acceptance preparation. It does not claim research-route execution, experiment or simulation results, training or inference, download, deployment, operational readiness, target-domain transfer, licensing, protection, or nuclear safety.
