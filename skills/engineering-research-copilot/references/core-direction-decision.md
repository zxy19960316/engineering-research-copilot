# Direction Decision and Route Gate

Use this file only after one paper-calibration branch reaches `M1_COMPLETE`. Convert that branch into an auditable direction portfolio, stop when direction evidence is incomplete, and open detailed route planning only after explicit user confirmation.

## Contents

- Follow the M2 state flow
- Preserve the M1 evidence source
- Return a bounded portfolio
- Pass hard gates before scoring
- Assign transfer-evidence tiers
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
  schema_version: "m2.1"
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
axis_changes: []
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

Optionally add at most two high-risk ideas under `high_risk_ideas`. Use exactly `direction_id`, `title`, `evidence_tier`, `supporting_candidate_ids`, `unknowns`, and `recommendation_status`. Require `evidence_tier: speculative` and `recommendation_status: unranked_high_risk`; never include a high-risk idea in formal scores or positions.

Set `portfolio_status` to `provisional` only when all three formal directions pass their hard gates and are eligible for comparison. Set it to `evidence_incomplete` when any formal direction fails a hard gate; do not disguise the stop by omitting the failed direction or promoting a high-risk idea.

## Pass hard gates before scoring

Require exactly these hard gates for every formal direction:

- `target_problem_evidence`;
- `data_availability`;
- `falsifiability`;
- `feasibility_and_governance`;
- `m1_citation_integrity`.

Use this exact gate shape:

```yaml
gate_id: "target_problem_evidence"
status: "pass"
evidence_candidate_ids: []
rationale: ""
blockers: []
```

Use only `pass` or `fail`. Require a non-empty rationale. Require target-problem and citation-integrity gates to cite at least one M1 candidate. Record every unresolved resource, time, safety, ethics, compliance, data, or validation blocker under `blockers` and set the affected gate to `fail`.

When any gate fails, require `scorecard: null` and `recommendation_status: excluded`. Do not compute, retain, or display a weighted total for that direction. Return portfolio status `evidence_incomplete` and decision status `direction_evidence_incomplete`; do not enter user confirmation.

## Assign transfer-evidence tiers

Use only this closed evidence-tier set and bind claims to the allowed language:

| Tier | Required basis | Allowed language and position |
|---|---|---|
| `established-in-target` | Direct target or highly equivalent validation exists | Say “Direct evidence supports applicability”; permit main, adjacent, or transfer exploration |
| `transfer-supported` | Target need, source success, compatibility map, anti-transfer analysis, and a decisive test exist | Say “Recommended for priority validation”; permit main with at most medium confidence, adjacent, or transfer exploration |
| `mechanism-plausible` | Principle or data compatibility is plausible but bridge evidence is incomplete | Say “Divergent exploration suggestion”; permit only transfer exploration and never a primary conclusion |
| `speculative` | Support is mainly analogy or creative association | Say “High-uncertainty idea”; permit only an unranked high-risk idea |

Do not require exact target-domain method success for `transfer-supported`. Do not upgrade compatibility of names, principles, mechanisms, or data shapes into established target applicability.

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

Represent a meaningful change with this exact object:

```yaml
axis: "method"
from: ""
to: ""
```

Use only `problem`, `method`, or `data` as the axis. Require different non-empty `from` and `to` values. Give the provisional main direction no axis changes, the adjacent alternative exactly one axis change, and the transfer exploration at least two distinct axis changes. Reject title-only changes, synonyms with identical axis values, duplicate axes, and three cards that express the same problem-method-data combination.

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

## Define a minimum decisive test

Use this exact object for every formal direction:

```yaml
hypothesis: ""
inputs: []
baseline: ""
steps: []
primary_metric: ""
success_threshold:
  metric: ""
  operator: ">="
  value: 0.0
  unit: ""
stop_condition:
  metric: ""
  operator: "<"
  value: 0.0
  unit: ""
pivot_condition:
  metric: ""
  operator: "<="
  value: 0.0
  unit: ""
expected_time: ""
required_resources: []
```

Require a falsifiable non-empty hypothesis, at least one input and step, a baseline, a primary metric, expected time, and at least one resource. Use only `>=`, `<=`, `>`, or `<` with a finite numeric value for every threshold. Keep the metric and unit explicit. If a defensible numeric value is not yet known, stop the direction at `DIRECTION_EVIDENCE_INCOMPLETE` and state the pilot evidence needed; do not substitute vague phrases such as “meaningful improvement.”

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

Before `user_confirmed`, reject complete experiment steps, complete simulation routes, training plans, model downloads, service deployment, and large-scale resource execution wherever those payloads appear in the M2 bundle. Treat unknown nested route fields as invalid. A minimum decisive test is a bounded direction gate artifact, not a full route.

## Validate post-confirmation route output

Allow `route_output` to remain `null` after confirmation until the user requests route generation. When present, require it to use exactly these fields:

```yaml
selected_direction_id: "D1"
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
evidence_chain:
  design: []
  data: []
  analysis: []
  result: []
  claim: []
```

Match `selected_direction_id` to the confirmed decision. Require every field to be non-empty and every list to contain at least one concrete item. Validate this envelope only; do not execute the route, start services, download models, upload materials, or allocate large resources without a separate explicit request.
