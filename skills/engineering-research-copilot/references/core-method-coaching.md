# Method Coaching

Use this protocol only after an M2.1.1 direction is explicitly user-confirmed. Validate inputs read-only, derive every M3 binding from the accepted M2 bundle, and return closed `m3.1` method cards without executing research work.

## Contents

- Follow the M3 state flow
- Derive the trusted M2 context
- Choose the coaching mode
- Return a closed M3 bundle
- Build closed method cards
- Bind resources and conditions
- Keep a typed source ledger
- Add domain overlays
- Respect evidence and permission boundaries

## Follow the M3 state flow

Use this exact state flow:

```text
M2_BUNDLE_VALID
  -> DIRECTION_USER_CONFIRMED
  -> SELECTED_DIRECTION_HASH_VALID
  -> ROUTE_ABSENT: BOUNDED_METHOD_COACHING
  -> ROUTE_PRESENT_AND_M3_COMPATIBLE: ROUTE_SPECIFIC_METHOD_CARD
  -> UNSUPPORTED_CONSTRAINT_APPROVAL: STOP_FOR_PROVENANCE_REPAIR
```

Stop before method-card processing if the embedded M2 bundle is invalid, the direction is not `user_confirmed`, the selected direction or bundle hash is stale, or the selected direction does not resolve to exactly one formal direction.

If `route_output.approved_constraint_changes` is non-empty, return only `unsupported_approved_constraint_change_provenance`. Show the original selected-direction `resource_limits`, apply no proposed change, and request provenance repair.

## Derive the trusted M2 context

Validate the complete embedded bundle with `validate_m2_direction_bundle.validate_bundle` before reading any M2 field. Preserve the bundle verbatim; do not migrate, normalize, repair, or write it back.

Derive these values instead of trusting copied M3 declarations:

- locate the selected formal direction from `direction_decision.selected_direction_id`;
- recompute the source-bundle and selected-direction hashes with canonical UTF-8 JSON;
- derive claims and claim types from `selected_direction.core_claims`;
- derive each claim's metric IDs from `required_decision_metrics`;
- derive each claim's required precondition IDs from `minimum_decisive_test.claim_coverage`;
- derive the precondition records from `minimum_decisive_test.required_preconditions`;
- derive resource ceilings from `selected_direction.resource_limits`;
- derive eligible source records from `source_m1_bundle.round2.candidate_pool`;
- preserve all upstream evidence gaps and verification limits.

For route-specific coaching, require every `route_traceability.source_precondition_ids` set to equal the corresponding claim-coverage precondition set. Derive actual Go, Stop, and Pivot coverage by intersecting each claim's metric IDs with the metric IDs in `route_output.go_conditions`, `stop_conditions`, and `pivot_conditions`. Reject any declared `route_condition_types` set that differs from the derived set.

## Choose the coaching mode

Use `bounded` only when `route_output` is absent. Explain applicable methods, assumptions, baselines, checks, uncertainty handling, failure modes, and numeric stop or pivot criteria tied to the confirmed direction. Do not manufacture a complete route, fill missing route traceability, widen resources, execute a route, or claim empirical success.

Use `route_specific` only when `route_output` is present, the M2 validator accepts it, the M3 compatibility derivations agree, and approved constraint changes are empty. Instantiate cards from the selected claims, metrics, preconditions, conditions, and original resource limits; do not treat route prose as independent authority.

## Return a closed M3 bundle

Return exactly these top-level fields:

```yaml
schema_version: "m3.1"
source_m2_bundle: {}
source_m2_bundle_hash: ""
selected_direction_id: "D1"
selected_direction_hash: ""
coaching_mode: "bounded|route_specific"
method_cards: []
domain_overlays: []
```

Set both hashes to recomputed canonical SHA-256 values. Reject unknown top-level fields. Require at least one valid method card; permit an empty `domain_overlays` list.

## Build closed method cards

Use exactly one of these method families:

- `experiment_measurement_uq`;
- `modeling_simulation_vvuq`;
- `control_optimization_identification`;
- `signal_diagnostics`;
- `data_ml_hybrid`;
- `reliability_safety_risk`.

Use exactly these fields for every card:

```yaml
schema_version: "m3.1"
card_id: "card:data-ml-hybrid:1"
method_family: "data_ml_hybrid"
applicability:
  supported_claim_types: []
  required_inputs: []
  incompatible_conditions: []
assumptions: []
minimum_resources: []
inherited_constraints: []
baselines: []
controls: []
procedure_outline: []
primary_metrics: []
uncertainty_handling: []
validation_checks: []
failure_modes: []
stop_conditions: []
pivot_conditions: []
safety_boundaries: []
source_ledger: []
```

Reject unknown fields and duplicate `card_id` values. Make every listed field non-empty. Use non-empty text rows for the narrative lists. Use only selected-direction claim types in `supported_claim_types`, and use only selected-direction metric IDs in `primary_metrics`; reject duplicates. Keep every required input and incompatible condition explicit rather than inferring either from method-family prose.

## Bind resources and conditions

Copy `selected_direction.resource_limits` exactly, including order and value types, into every card's `inherited_constraints`. Use exactly these fields for each minimum-resource row:

```yaml
resource: "CPU time"
required_value: 1
unit: "hours"
source_constraint_id: "R-CPU-HOURS"
```

Use a finite, non-boolean numeric `required_value`. Resolve `source_constraint_id` to one inherited resource limit, and match its `resource` and `unit` exactly. Bind minimum resources only to `<` or `<=` ceilings. Reject a value equal to a `<` ceiling or greater than a `<=` ceiling. Never reinterpret a lower-bound constraint as a ceiling.

Use exactly these fields for every stop or pivot condition:

```yaml
criterion_type: "stop|pivot"
metric_id: "M1"
operator: "<|<=|>|>="
value: 0.0
unit: "ratio"
```

Use `stop` only in `stop_conditions` and `pivot` only in `pivot_conditions`. Use a finite, non-boolean numeric value, resolve the metric ID to the selected direction, and match the metric unit exactly.

## Keep a typed source ledger

Use exactly these fields for every source-ledger row:

```yaml
source_id: "source:P7"
candidate_id: "P7"
basis_level: "metadata|abstract|full_text"
support_types:
  - "bibliographic_identity|method|result|transfer|safety"
supports: []
does_not_support: []
limitations: []
```

Give each row a unique, non-empty `source_id`. Resolve `candidate_id` against `source_m2_bundle.source_m1_bundle.round2.candidate_pool`. Require recommendation eligibility and an allowed verified status. Reject `partial`, `conflicted`, `not_found`, `manual_needed`, unknown, ambiguous, or ineligible candidates.

Map basis levels only as follows, and require exact equality:

| M1 basis | M3 basis |
|---|---|
| `metadata_level` | `metadata` |
| `abstract_level` | `abstract` |
| `fulltext_level` | `full_text` |

Use a non-empty, duplicate-free subset of `bibliographic_identity`, `method`, `result`, `transfer`, and `safety` in `support_types`. Allow metadata-only evidence to use only `bibliographic_identity`; never infer support types from free text. Make `supports`, `does_not_support`, and `limitations` non-empty lists of explicit text. Keep verified preprints eligible for method or exploration support, but never use them as the sole basis for a main direction or safety-related conclusion.

Use `fixture_only` sources only inside an explicitly labeled offline fixture. Do not present fixture validation as literature verification, method performance, route execution, or empirical evidence.

## Add domain overlays

Use exactly these fields for a domain overlay:

```yaml
schema_version: "m3.1"
overlay_id: "domain:nuclear-ml:1"
domain: "nuclear_engineering_ml"
base_card_ids: []
additional_assumptions: []
additional_failure_modes: []
additional_validation_checks: []
additional_stop_conditions: []
specialist_review_boundaries: []
transfer_status: "hypothesis"
source_ledger: []
```

Reject unknown fields and duplicate overlay IDs. Resolve every unique `base_card_id` to a card in the same bundle. Add domain constraints; do not replace base-card assumptions, checks, failures, stops, or safety boundaries. Keep every additive list and the overlay ledger non-empty. Validate `additional_stop_conditions` with the same closed numeric condition object and selected-direction metric bindings used for card stop conditions.

Keep `domain` fixed to `nuclear_engineering_ml` and `transfer_status` fixed to `hypothesis`. Require at least one eligible non-preprint ledger row whose `support_types` includes `safety`. Treat operational, regulatory, and safety conclusions as specialist-review boundaries.

## Respect evidence and permission boundaries

- Separate discovery from verification; never invent or infer titles, authors, publication states, DOIs, or other identifiers.
- Label every assertion as metadata-, abstract-, or full-text-level through its ledger basis.
- Keep conflicted, unresolved, and recommendation-ineligible citations out of cards and overlays.
- Label cross-domain transfer as a hypothesis until a target-domain decisive test supports it.
- Treat validation of the closed bundle as structural, deterministic, offline contract evidence only.
- Do not claim that a valid card proves method effectiveness, simulation validity, transfer success, or safety.
- Do not execute experiments, simulations, training, downloads, uploads, service startup, deployment, resource allocation, or file writes as part of method coaching.
- Require a separate explicit user request before any authorized side effect, and re-check the applicable safety and resource boundary before acting.
