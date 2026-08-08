# Direction Decision and Route Gate

Use this file only after one paper-calibration branch reaches `M1_COMPLETE`. Convert that branch into an auditable direction portfolio, stop when direction evidence is incomplete, and open detailed route planning only after explicit user confirmation.

## Contents

- Follow the M2 state flow
- Preserve the M1 evidence source
- Return a bounded portfolio
- Pass hard gates before scoring
- Assign transfer-evidence tiers
- Enforce preprint support policy
- Separate directions by meaningful axes
- Compare eligible directions
- Define a minimum decisive test
- Require user confirmation
- Validate post-confirmation route output

## Follow the M2 state flow

Use this state flow:

```text
M1_COMPLETE
  -> BUILDING_DIRECTION_PORTFOLIO
  -> CHECKING_DIRECTION_HARD_GATES
     -> DIRECTION_EVIDENCE_INCOMPLETE
     -> DIRECTION_PORTFOLIO_READY
  -> WAITING_FOR_DIRECTION_CONFIRMATION
     -> DIRECTION_REJECTED
     -> DIRECTION_MODIFICATION_REQUESTED
     -> USER_CONFIRMED
  -> ROUTE_GATE_OPEN
```

Treat `DIRECTION_EVIDENCE_INCOMPLETE`, `DIRECTION_REJECTED`, and `DIRECTION_MODIFICATION_REQUESTED` as closed route-gate states. Enter `WAITING_FOR_DIRECTION_CONFIRMATION` only after every formal direction passes its hard gates. Enter `ROUTE_GATE_OPEN` only from `USER_CONFIRMED`; no score, confidence, or system recommendation may bypass this transition.

Save one M2 decision bundle with this exact top-level shape:

```yaml
source_m1_bundle: {}
direction_portfolio: {}
direction_decision: {}
route_output: null
```

Permit `fixture_mode`, `evidence_class`, `proves`, and `does_not_prove` only for clearly labeled offline contract fixtures. Reject other top-level fields.

## Preserve the M1 evidence source

Embed the complete accepted M1 bundle under `source_m1_bundle` without changing, deleting, or reclassifying any candidate ID, verification status, recommendation-eligibility flag, basis level, verified record, or evidence gap. Require the embedded bundle to satisfy all of these conditions:

- `schema_version` is `m1.2`;
- `terminal_state` is `M1_COMPLETE`;
- `stopped_after_round` is `2`;
- `outcome` is `complete`;
- the M1 validator returns `valid`.

Compute `source_m1_bundle_hash` as lowercase SHA-256 over the embedded bundle encoded as canonical UTF-8 JSON with sorted keys, compact separators, and non-ASCII characters preserved. Never accept a caller-supplied hash without recomputing it.

Resolve every M2 evidence reference against `source_m1_bundle.round2.candidate_pool`. Require the referenced candidate to retain its M1 ID, verification state, recommendation eligibility, and basis level. Reject unknown IDs, ambiguous IDs, blocked candidates, and references that exist only in discovery limitations. Preserve M1 evidence gaps even though a valid M2 source has no unresolved round-two selection gap; never reinterpret an incomplete M1 bundle as complete direction evidence.

## Return a bounded portfolio

Use this exact portfolio shape:

```yaml
direction_portfolio:
  schema_version: "m2.1.1"
  source_m1_terminal_state: "M1_COMPLETE"
  source_m1_bundle_hash: ""
  brief_version: 2
  branch_id: "branch-a"
  directions: []
  high_risk_ideas: []
  portfolio_status: "provisional"
```

Match `brief_version` and `branch_id` to the accepted M1 round-two research brief and search plan. Return exactly three formal directions when the portfolio is ready:

1. one `provisional_main`;
2. one `adjacent_alternative`;
3. one `transfer_exploration`.

Use this exact formal-direction shape:

```yaml
direction_id: "D1"
position: "provisional_main"
title: ""
evidence_tier: "transfer-supported"
claim_language: "Recommended for priority validation"
axis_profile:
  problem: ""
  method: ""
  data: ""
axis_changes: []
core_claims: []
resource_limits: []
hard_gates: []
transfer_case: {}
scorecard: {}
minimum_decisive_test: {}
supporting_candidate_ids: []
counter_candidate_ids: []
unknowns: []
confidence: "medium"
recommendation_status: "provisional"
```

Assign a unique non-empty direction ID and title. Require at least one recommendation-eligible supporting M1 candidate and one recommendation-eligible counter or limitation candidate for every formal direction. Keep the system recommendation `provisional` even when all hard gates pass.

Optionally add at most two high-risk ideas under `high_risk_ideas`. Use exactly `direction_id`, `title`, `evidence_tier`, `claim_language`, `supporting_candidate_ids`, `unknowns`, and `recommendation_status`. Require `evidence_tier: speculative`, `claim_language: High-uncertainty idea`, and `recommendation_status: unranked_high_risk`; never include a high-risk idea in formal scores or positions.

Set `portfolio_status` to `provisional` only when all three formal directions pass their hard gates and are eligible for comparison. Set it to `evidence_incomplete` when any formal direction fails a hard gate; do not disguise the stop by omitting the failed direction or promoting a high-risk idea.

## Pass hard gates before scoring

Require exactly these hard gates for every formal direction:

- `target_problem_evidence`;
- `data_availability`;
- `falsifiability`;
- `resource_feasibility`;
- `time_feasibility`;
- `safety_ethics_compliance`;
- `m1_citation_integrity`.

Use this exact gate shape:

```yaml
gate_id: "target_problem_evidence"
status: "pass"
evidence_candidate_ids: []
required_precondition_ids: []
rationale: ""
blockers: []
```

Use only `pass` or `fail`. Require a non-empty rationale. Require target-problem and citation-integrity gates to cite at least one M1 candidate. Record every unresolved resource, time, safety, ethics, compliance, data, or validation blocker under `blockers` and set the affected gate to `fail`.

When any gate fails, require `scorecard: null` and `recommendation_status: excluded`. Do not compute, retain, or display a weighted total for that direction. Return portfolio status `evidence_incomplete` and decision status `direction_evidence_incomplete`; do not enter user confirmation.

Bind each gate to relevant structured preconditions through `required_precondition_ids`. If a precondition is `unresolved` and `blocking_if_unresolved: true`, require its named gate to fail, its direction scorecard to be `null`, its recommendation status to be `excluded`, and the portfolio and decision to stop at `evidence_incomplete`.

## Assign transfer-evidence tiers

Use only this closed evidence-tier set. Copy the exact allowed phrase into `claim_language`; do not paraphrase it into stronger wording:

| Tier | Required basis | Allowed language and position |
|---|---|---|
| `established-in-target` | Direct target or highly equivalent validation exists | Say “Direct evidence supports applicability”; permit main, adjacent, or transfer exploration |
| `transfer-supported` | Target need, source success, compatibility map, anti-transfer analysis, and a decisive test exist | Say “Recommended for priority validation”; permit main with at most medium confidence, adjacent, or transfer exploration |
| `mechanism-plausible` | Principle or data compatibility is plausible but bridge evidence is incomplete | Say “Divergent exploration suggestion”; permit only transfer exploration and never a primary conclusion |
| `speculative` | Support is mainly analogy or creative association | Say “High-uncertainty idea”; permit only an unranked high-risk idea |

Do not require exact target-domain method success for `transfer-supported`. Do not upgrade compatibility of names, principles, mechanisms, or data shapes into established target applicability.

## Enforce preprint support policy

Resolve support classes only from `source_m1_bundle.round2.candidate_pool`. Use the actual `verification_status` and `recommendation_eligible` fields; do not accept a direction-level source classification.

- Permit `verified_preprint` as method or exploration support.
- Require at least one recommendation-eligible `verified_primary` or `verified_registry` candidate in the supporting IDs of `provisional_main`.
- Require at least one recommendation-eligible non-preprint candidate for a passing `safety_ethics_compliance` gate when it cites evidence.
- Ignore `recommendation_eligible: false` and blocked candidates when checking for non-preprint support.
- Return `provisional_main_requires_non_preprint_support` or `safety_gate_requires_non_preprint_support` for the corresponding violation.

Use this exact transfer-case shape for every formal direction:

```yaml
target_problem_evidence: []
source_success_evidence: []
transfer_compatibility:
  concepts: []
  units: []
  scales: []
  boundary_conditions: []
  assumptions: []
anti_transfer_factors: []
```

Require candidate IDs in both evidence lists. Require every compatibility dimension and `anti_transfer_factors` to contain at least one non-empty entry for `transfer-supported`, `mechanism-plausible`, and the `transfer_exploration` position. Use explicit “not applicable because …” entries only for a genuinely direct, non-transfer `established-in-target` direction; never use an empty list to imply compatibility.

## Separate directions by meaningful axes

Give every formal direction one closed `axis_profile` with exactly `problem`, `method`, and `data`. Treat the provisional main profile as the common baseline. Derive `axis_changes` by comparing the other profile to that baseline; do not trust caller-declared changes.

Represent a meaningful change with this exact object:

```yaml
axis: "method"
from: ""
to: ""
```

Use only `problem`, `method`, or `data` as the axis. Require different non-empty `from` and `to` values. Give the provisional main direction no axis changes, the adjacent alternative exactly one axis change, and the transfer exploration at least two distinct axis changes. Reject title-only changes, synonyms with identical axis values, duplicate axes, and three cards that express the same problem-method-data combination.

Use this closed core-claim structure:

```yaml
core_claims:
  - claim_id: "C1"
    claim: ""
    claim_type: "predictive_performance|uncertainty_quality|open_set_detection|data_availability|safety"
    evidence_candidate_ids: []
    required_decision_metrics:
      - metric_id: "M1"
        metric: ""
        metric_role: "predictive_performance|uncertainty_quality|open_set_detection|data_availability|safety"
        unit: ""
```

Require every cited candidate ID to resolve to an eligible M1 record. Require the metric role corresponding to the claim type. In particular, do not let an uncertainty-quality claim rely only on a predictive-error metric, and do not let an open-set claim rely only on closed-set accuracy.

Record numeric resource ceilings with `constraint_id`, `resource`, `operator`, finite `value`, and `unit`. Use only `>=`, `<=`, `>`, or `<` as operators.

## Compare eligible directions

Score only directions whose hard gates all pass. Use the same weights for all ranked directions and require integer weights totaling 100:

| Dimension | Default weight |
|---|---:|
| `engineering_value` | 15 |
| `gap_and_evidence_quality` | 15 |
| `data_and_resource_fit` | 20 |
| `validation_and_falsifiability` | 15 |
| `method_maturity` | 10 |
| `time_to_decisive_signal` | 10 |
| `interdisciplinary_interface_quality` | 10 |
| `safety_ethics_compliance` | 5 |

Use this exact scorecard shape:

```yaml
dimensions:
  - dimension: "engineering_value"
    weight: 15
    score: 0
    evidence_candidate_ids: []
    evidence: ""
    confidence: "low"
    unknowns: []
    change_triggers: []
weighted_total: 0.0
```

Use integer scores from 0 through 5. Recompute `weighted_total` as the sum of `score * weight / 5` and reject mismatches. Require non-empty evidence, confidence, unknowns, and change triggers for every dimension. Present totals only as decision aids; a larger total cannot override a hard gate or the user confirmation gate.

Apply these anchors within each named dimension:

| Score | Meaning |
|---:|---|
| 0 | The dimension fails or has no admissible support. |
| 1 | Support is very weak and a material blocker dominates. |
| 2 | Support is weak-to-mixed: stronger than 1 but below a defensible midpoint. |
| 3 | Support is adequate but material uncertainty remains. |
| 4 | Support is strong: better than 3 but not comprehensive enough for 5. |
| 5 | Support is unusually strong, specific, and limitation-aware for this decision stage. |

Explain the score using evidence, unknowns, and change triggers specific to that dimension. Permit candidate IDs to overlap across dimensions, but reject an exact normalized duplicate of the full rationale triple. Do not infer score quality with open-ended NLP.

## Define a minimum decisive test

Use this exact object for every formal direction:

```yaml
scope: "minimum_decisive_test"
hypothesis: ""
inputs: []
baseline: ""
steps:
  - step_id: "S1"
    action: ""
    bounded_output: ""
primary_metric_id: "M1"
claim_coverage:
  - claim_id: "C1"
    metric_ids: ["M1"]
    decision_criteria:
      - criterion_type: "success"
        metric_id: "M1"
        operator: ">="
        value: 0.0
        unit: ""
    required_precondition_ids: []
required_preconditions:
  - precondition_id: "P1"
    description: ""
    gate_id: "data_availability"
    status: "verified"
    evidence_candidate_ids: []
    blocking_if_unresolved: true
    preflight_check: ""
    stop_condition:
      metric: ""
      operator: "<"
      value: 0.0
      unit: ""
expected_time: ""
required_resources: []
```

Require a falsifiable non-empty hypothesis, inputs, baseline, primary metric ID, expected time, resources, and exactly two to four closed step objects. Limit each step field and the total serialized object to the validator bounds; reject nested route objects, long route payloads, training matrices, deployment stages, download plans, service topologies, or full resource schedules through closed structure and size limits.

Cover every core claim exactly once. Require every claim metric to have a finite numeric success, stop, pivot, or falsification criterion with an explicit unit. Bind data-availability claims to structured preconditions. Trace all material inputs, labels, splits, sample counts, sampling rates, and horizons as `verified`, `bounded_testable`, or `unresolved`; require a bounded preflight check and numeric stop condition. If a defensible numeric criterion is not known, stop at `DIRECTION_EVIDENCE_INCOMPLETE` instead of substituting “meaningful improvement.”

## Require user confirmation

Use this exact decision shape:

```yaml
direction_decision:
  selected_direction_id: null
  status: "waiting_for_user_confirmation"
  permitted_next_actions:
    - confirm
    - modify
    - reject
  confirmation_event: null
```

Use only these consistent combinations:

| Status | Selected ID | Permitted next actions | Route output |
|---|---|---|---|
| `direction_evidence_incomplete` | `null` | `modify`, `reject` | `null` |
| `waiting_for_user_confirmation` | `null` | `confirm`, `modify`, `reject` | `null` |
| `modification_requested` | `null` | `modify`, `reject` | `null` |
| `rejected` | `null` | `modify` | `null` |
| `user_confirmed` | one formal direction ID | `modify`, `reject`, `generate_route` | `null` or one valid route object |

Do not treat natural-language enthusiasm, a score, an accepted paper map, or a system recommendation as confirmation. Require an explicit user choice of one formal direction ID. On modification or rejection, apply the feedback and rollback protocol and preserve the previous bundle; do not silently mutate it.

Require `confirmation_event: null` for every non-confirmed state. For `user_confirmed`, require this closed event:

```yaml
confirmation_event:
  actor_role: "user"
  selected_direction_id: "D1"
  source_message_id: ""
  source_message_excerpt: ""
  source_message_sha256: ""
  previous_bundle_hash: ""
```

Require the excerpt to explicitly contain the selected formal direction ID and hash its exact UTF-8 text. Reconstruct the waiting pre-confirmation bundle, recompute its canonical SHA-256, and match `previous_bundle_hash`. Match the event ID to `direction_decision.selected_direction_id`. Reject missing events, non-user actors, high-risk or unknown IDs, stale bundle hashes, and confirmation events attached to non-confirmed states. This contract proves internal provenance consistency; it does not authenticate the host-system identity of the user.

Before `user_confirmed`, reject complete experiment steps, complete simulation routes, training plans, model downloads, service deployment, and large-scale resource execution wherever those payloads appear in the M2 bundle. Treat unknown nested route fields as invalid. A minimum decisive test is a bounded direction gate artifact, not a full route.

## Validate post-confirmation route output

Allow `route_output` to remain `null` after confirmation until the user requests route generation. When present, require it to use exactly these fields:

```yaml
selected_direction_id: "D1"
source_direction_hash: ""
confirmation_event_hash: ""
source_bundle_hash: ""
hypothesis: ""
baselines: []
controls: []
sequence: []
inputs: []
outputs: []
controlled_variables: []
confounders: []
primary_metrics: []
secondary_metrics: []
minimum_meaningful_improvement: ""
uncertainty_checks: []
sensitivity_checks: []
validity_checks: []
go_conditions: []
stop_conditions: []
pivot_conditions: []
route_traceability: []
source_test_mapping: []
inherited_constraints: []
approved_constraint_changes: []
evidence_chain:
  design: []
  data: []
  analysis: []
  result: []
  claim: []
```

Match `selected_direction_id` to the confirmed decision. Recompute `source_direction_hash` from the exact selected direction, `confirmation_event_hash` from the exact confirmation event, and `source_bundle_hash` from the confirmed bundle with `route_output: null`.

Use structured numeric conditions for Go, Stop, and Pivot. Require `route_traceability` and `source_test_mapping` to cover every selected-direction core claim and every minimum-test metric. Require route metrics, preconditions, resource limits, and conditions to trace to the selected direction. Copy `resource_limits` exactly into `inherited_constraints`; permit a change only through a closed `approved_constraint_changes` record containing the old and approved finite values, unit, approval message ID, and approval-message SHA-256. Reject copied routes, stale bundle bindings, missing claim mappings, and silent resource expansion.

Require all remaining envelope fields to be non-empty, except that `approved_constraint_changes` may be an empty list when no change was approved. Validate the envelope only; do not execute the route, start services, download models, upload materials, or allocate large resources without a separate explicit request.

## Record the m2.1.1 compatibility boundary

Treat m2.1.1 as a breaking validation revision. New required fields include confirmation provenance, axis profiles, core claims, resource limits, structured preconditions and claim coverage, plus route hashes and traceability. Do not accept an m2.1 bundle as m2.1.1 by treating these fields as optional. Read legacy fixtures only with the frozen m2.1 validator or an explicit migration helper. The canonical JSON and CLI status/exit-code rules remain non-breaking.
