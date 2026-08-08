# Frozen Engineering Research Instructions

<!-- source: SKILL.md; source_sha256: 3d53432d11963ee7b7532526b72236ed1a72cfda66c66feafadaa725b73bac44 -->
---
name: engineering-research-copilot
description: "Run evidence-grounded engineering research workflows for mechanical, nuclear, automation, computer, electrical, and interdisciplinary topics. Use when a researcher needs accurate two-round literature matching, a static paper evidence map, research-direction comparison, transfer-method reasoning, an executable experiment or simulation route, method coaching, data-result-claim auditing, manuscript red-team review, or Chinese requests such as 文献精准匹配、科研选题、交叉学科方向、科研路线、实验方案、仿真方案、方法迁移、证据检查、论文预审和科研辅助。"
---

# Engineering Research Copilot

Help engineering master's students and early doctoral researchers move from a vague or cross-disciplinary problem to literature, a defensible direction, and an executable research route. Keep claims proportional to evidence and keep the researcher in control of direction changes.

## Apply the operating contract

Use this default sequence:

```text
adaptive brief
  -> round-one verified paper map
  -> chat feedback
  -> visible feedback delta
  -> round-two search or direction reframe
  -> direction cards
  -> user direction confirmation
  -> detailed route or method coaching
```

Treat the two searches as one calibration cycle, not a permanent limit. If the user remains dissatisfied, diagnose the reason and start the appropriate new cycle.

## Route the task

| User need | Load and apply |
|---|---|
| Find, verify, compare, or re-search papers | [Paper calibration](references/core-paper-calibration.md), [Paper evidence map](references/core-paper-map.md), and [Feedback rollback](references/core-feedback-rollback.md) |
| Confirm or compare research directions | [Direction decision](references/core-direction-decision.md) |
| React to dissatisfaction or changed constraints | Use the feedback-rollback rules above |
| Plan an experiment, simulation, or minimum decisive test | Use the direction-decision rules above; require `user_confirmed` direction status first |
| Coach an engineering method | [Method coaching](references/core-method-coaching.md), then load only the applicable family: [Experiment, measurement, and UQ](references/method-experiment-measurement-uq.md), [Modeling, simulation, and VVUQ](references/method-modeling-simulation-vvuq.md), [Control, optimization, and identification](references/method-control-optimization-identification.md), [Signal processing and diagnostics](references/method-signal-diagnostics.md), [Data, machine learning, and hybrid methods](references/method-data-ml-hybrid.md), or [Reliability, safety, and risk](references/method-reliability-safety-risk.md); for nuclear engineering × ML, also apply the additive [Nuclear engineering × machine learning overlay](references/domain-nuclear-ml.md) |
| Check data-result-claim consistency | Perform a read-only claim-evidence audit; distinguish observed data, analysis output, interpretation, and speculation |
| Review writing, figures, or format | Perform a read-only red-team pass, then hand off execution to a dedicated writing, figure, document, or data Skill when available |

Load only the references required for the current route. Do not load every reference by default.

## Calibrate papers in two rounds

Load and apply Paper calibration as the state contract. Paper evidence map to each round view, and Feedback rollback to the round transition. Keep incomplete evidence visible and stop at the M1 boundary defined in the calibration reference.

## Decide a direction without suppressing innovation

Enter M2 only from an accepted `M1_COMPLETE` bundle. Preserve that bundle verbatim, bind it with its canonical SHA-256 hash, and apply the m2.1.1 state and data contract in Direction decision.

Return:

- one provisional main direction;
- one adjacent alternative;
- one transfer exploration direction;
- at most two separately labeled, unranked high-risk ideas.

Require direct evidence that the target problem exists. Do not require prior success of the exact method in the exact target domain. Permit similar-domain, mechanism, theory, or data-structure evidence to support a testable transfer hypothesis.

Never turn principle compatibility or analogy into an established conclusion. Label it as `transfer-supported`, `mechanism-plausible`, or `speculative` according to Direction decision.

## Enforce the direction gate

Mark the system's direction recommendation as `provisional`. Pass every hard gate before scoring. Show the M1 candidate lineage, evidence tier, closed core claims, structured data preconditions, risks, unknowns, and a bounded minimum decisive test with numeric success, stop, and pivot thresholds for each formal direction.

Do not generate a detailed route until the user explicitly confirms one formal direction ID. Record the exact confirmation message provenance and bind it to the canonical pre-confirmation bundle. On confirmation, set the direction status to `user_confirmed`; only then may the route gate open. Bind any route to the selected direction, confirmation event, confirmed bundle, claims, test metrics, preconditions, and resource limits, then produce:

- a falsifiable hypothesis;
- baseline and controls;
- executable experiment or simulation steps;
- inputs, outputs, controlled variables, and confounders;
- primary and secondary metrics;
- minimum meaningful improvement;
- uncertainty, sensitivity, and validity checks;
- Go, Stop, and Pivot conditions;
- an evidence chain from design to data, analysis, result, and claim.

If the direction is rejected, use Feedback rollback instead of silently adjusting the old plan.

## Coach methods with bounded claims

Load and apply Method coaching. Validate the confirmed M2 bundle before deriving claims, metrics, preconditions, conditions, resources, or sources. Keep coaching bounded when no route exists, and instantiate route-specific cards only from a compatible route. Treat domain-specific standards and safety judgments as specialist review boundaries.

## Audit evidence read-only

When checking data, conclusions, or a manuscript:

- separate data, analysis, result, interpretation, and claim;
- check leakage, invalid splits, missing controls, unit or scale mismatches, overclaiming, and omitted uncertainty;
- distinguish correlation from causation and simulation verification from validation;
- identify what would falsify each main claim;
- report issues and proposed corrections without modifying source files unless explicitly requested.

## Respect evidence and permission limits

- Use host-provided search tools; do not require a bundled database or private service.
- Do not start services, download models, upload research materials, execute arbitrary commands, or write back to user files without an explicit request.
- Treat RRC as an optional future backend. Keep the Skill usable without it.

<!-- source: references/core-direction-decision.md; source_sha256: 206c4f8d0f8c639bdd74e62845bbf768b6f096c2ce4cf5e996502e4bd34f95de -->
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

<!-- source: references/core-feedback-rollback.md; source_sha256: 083f5d7fd3b2fd7cec3d7049cc63f5a5794002129c62c18191e56061b1960fda -->
# Feedback, Search History, and Rollback

Use this file whenever the user reacts to papers, changes constraints, rejects a direction, questions a citation, or requests a reset.

## Contents

- Maintain a versioned research brief
- Diagnose dissatisfaction before searching
- Control history influence
- Produce the exact feedback delta
- Apply material feedback to queries
- Show the change log before searching
- Follow the state flow
- Preserve uncertainty

## Maintain a versioned research brief

Store the reasoning state in this shape:

```yaml
brief_version: 3
branch_id: "branch-b"
confirmed_constraints: []
soft_preferences: []
positive_signals: []
negative_signals:
  - object: "Paper, cluster, method, or direction"
    reason: "Too theoretical and no experimental data is available"
rejected_items: []
open_questions: []
inherited_from_previous: []
reset_from_previous: []
```

Store rejection reasons, not only paper or direction IDs. Apply the reason to new candidates when relevant; do not merely hide the rejected item and recommend a near duplicate.

## Diagnose dissatisfaction before searching

| Feedback | Preserve | Reset | Next action |
|---|---|---|---|
| Direction accepted, papers rejected | Direction, hard constraints, target metrics | Paper ranking and query expression | Re-search within the direction |
| Papers credible, direction rejected | Stable resource constraints and explicit rejection reasons | Direction scores and old anchoring | Reframe, create a new direction branch, then search |
| Citation metadata questioned | Topic and direction constraints | Status of questioned citations | Audit and replace metadata before changing direction |
| New resource, data, or time constraint | Still-applicable preferences | Evidence and directions invalidated by the constraint | Revise the brief, then choose local or full re-search |
| Papers and direction rejected | User-confirmed stable constraints | Current branch, rankings, and direction set | Create a new branch from round one |
| Full reset requested | Safety/compliance rules and only user-approved stable constraints | Semantic preferences, negative feedback, scores, and queries | Start an independent branch |

If the user says only "not satisfied," ask one short diagnostic question instead of launching a blind third search.

## Control history influence

Use these default query/candidate allocation budgets:

| Feedback state | Exploit confirmed information | Explore new space |
|---|---:|---:|
| Clear positive feedback | 70% | 30% |
| Mixed or neutral feedback | 50% | 50% |
| Direction accepted, papers rejected | 30% | 70% |
| Direction rejected, new branch | 20% | 80% |
| Full reset | 0% | 100% |

Treat these as allocation defaults, not probabilities. Let the user request a more conservative or more divergent search.

## Produce the exact feedback delta

Expose every round-one-to-round-two transition with exactly these top-level fields. Do not rename a field, omit a field, or hide an additional transition state outside this object:

```yaml
feedback_delta:
  from_brief_version: 1
  to_brief_version: 2
  inherited:
    - object_id: "public-data-only"
      value: "Use public data only"
  rejected:
    - object_id: "random-split-dependent-designs"
      value: "Designs that mix one physical source across train and test"
      reason: "They can inflate evaluation through leakage"
  reset:
    - object_id: "round-one-title-level-fit"
      previous_value: "Title relevance counted as preliminary fit"
      reason: "Title evidence cannot establish isolation or leakage resistance"
  added:
    - object_id: "cross-load-evaluation-priority"
      value: "Prioritize cross-load or unseen-condition evaluation"
      reason: "The user promoted this evidence to a primary filter"
  allocation:
    exploit: 30
    explore: 70
  query_changes:
    - query_id: "Q-STABLE"
      reason: "Exclude proprietary-data routes and expand public simulation evidence"
      cause_refs:
        - "feedback_delta.rejected[0]"
        - "feedback_delta.reset[0]"
        - "feedback_delta.added[0]"
      before: "data-driven control using proprietary industrial datasets"
      after: "data-driven control using public simulation datasets excluding proprietary data"
```

Increment `to_brief_version` beyond `from_brief_version`. Use one closed schema for each list: inherited items contain exactly `{object_id,value}`; rejected items exactly `{object_id,value,reason}`; reset items exactly `{object_id,previous_value,reason}`; and added items exactly `{object_id,value,reason}`. Reject unknown fields and require every field value to be non-empty text. Put inherited constraints and preferences in `inherited`, rejected objects in `rejected`, explicitly discarded assumptions or state in `reset`, and new constraints or evidence needs in `added`. Preserve the user's wording when it determines a hard exclusion; do not strengthen ambiguous dissatisfaction into a hard constraint.

Set integer `allocation.exploit` and `allocation.explore` values whose sum is exactly 100. Treat the values as percentages of the round-two query-and-candidate budget, not as probabilities, confidence, or evidence weights.

## Apply material feedback to queries

Treat a rejection reason, a new constraint, or a reset as material when it changes an inclusion term, exclusion term, source boundary, time boundary, language boundary, expected evidence role, query purpose, query text, or whether a query is added or removed.

Add at least one `query_changes` entry whenever any rejection reason, new constraint, or reset materially affects the next search. Require every query-change entry to contain a non-empty `cause_refs` list. Use only exact, zero-based object paths into `feedback_delta.rejected`, `feedback_delta.reset`, or `feedback_delta.added`, such as `feedback_delta.rejected[0]`, `feedback_delta.reset[0]`, or `feedback_delta.added[0]`. Never point `cause_refs` to `feedback_delta.inherited`.

Require every `cause_refs` path to resolve to an existing entry. Require every material item in `rejected`, `reset`, and `added` to appear in at least one query change's `cause_refs`; allow one material item to affect multiple query changes and one query change to cite multiple material items. Treat an unresolved path, a forbidden inherited path, or an uncovered material item as invalid.

State the causal reason. For a modified query, preserve one stable `query_id`, require that ID exactly once in each round, require `before` to equal only that round-one query's `query_text`, and require `after` to equal only that round-two query's `query_text`. For an added query, require its ID to be absent from round one and present exactly once in round two, with `after` equal to its `query_text`. For a removed query, require its ID exactly once in round one and absent from round two, with `before` equal to its `query_text`. Never use `query_id`, `purpose`, `expected_evidence_role`, terms, or any other query field as a substitute for `query_text`.

Set `before` to the exact round-one `query_text` and `after` to the exact round-two `query_text` for the same `query_id`. For an added query, allow only `before` to be empty. For a removed query, allow only `after` to be empty. For a modified query, require both values to be non-empty and different. Never leave both values empty for an applied material change. Require every non-empty `after` value to match the revised round-two query text. If feedback does not change a query because an existing query already enforces it, classify that feedback effect as non-material with a visible reason; do not create a false query change.

Treat material feedback with no traceable query change as invalid. Do not proceed to round-two selection until the discrepancy is fixed or the feedback is explicitly classified as non-material with a visible reason.

## Show the change log before searching

Always show:

```text
Inherited: confirmed constraints and preferences
Rejected: items and the reasons for exclusion
Reset: scores, queries, assumptions, or branches no longer active
Added: new constraints or evidence needs
Search allocation: exploitation / exploration
```

Allow the user to correct this summary. Recompute direction scores from the new brief after a direction rejection; never inherit the old ranking.

## Follow the state flow

Use this logical flow:

```text
CLARIFYING
  -> ROUND1_SEARCHING
  -> WAITING_FOR_FEEDBACK
  -> ROUND2_SEARCHING or DIRECTION_REFRAMING or CITATION_AUDIT or FULL_RESET
  -> WAITING_FOR_DIRECTION_CONFIRMATION
  -> ROUTE_PLANNING only after user confirmation
```

Treat one two-round sequence as a calibration cycle. When the user remains dissatisfied, start the diagnosed next cycle instead of appending unlimited papers to the old query.

## Preserve uncertainty

- Explain which feedback changed the new search.
- Mark weak negative feedback as a soft preference unless the user makes it a hard exclusion.
- Do not reintroduce a rejected item unless new evidence materially changes its status; explain the exception.
- Do not claim that a new direction is independent when it still inherits old semantic constraints.
- Keep unavailable searches and unverified citations visible as gaps rather than silently dropping them.

<!-- source: references/core-method-coaching.md; source_sha256: 0229429edcc98837362711099d9c7502fb4bd81def929a501c4c207f91fad2e8 -->
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

<!-- source: references/core-paper-calibration.md; source_sha256: b32803c3d15fd44fd9255bbb438f52ffcddde05378b4f2d545a55e654c6e1bac -->
# Paper Calibration State Contract

Apply this file when building or revising one two-round paper-calibration cycle. Load [Citation integrity](core-citation-integrity.md), [Static paper evidence map](core-paper-map.md), and [Feedback, search history, and rollback](core-feedback-rollback.md) from the root Skill before executing the corresponding verification, map, or feedback step.

## Contents

- Follow the state flow
- Build the brief
- Plan the search
- Assemble the pool
- Select round one
- Apply feedback
- Select round two
- Report incomplete evidence
- Stop at the M1 boundary

## Follow the state flow

Keep one `branch_id` and stable candidate IDs throughout one calibration cycle. Increment `brief_version` when feedback changes a constraint, preference, open question, or evidence need. Use this state flow:

```text
BUILDING_BRIEF
  -> PLANNING_ROUND_ONE
  -> VERIFYING_ROUND_ONE_CANDIDATES
     -> EVIDENCE_INCOMPLETE -> WAITING_FOR_EVIDENCE_DECISION
     -> ROUND_ONE_READY
  -> WAITING_FOR_FEEDBACK
  -> APPLYING_FEEDBACK
  -> PLANNING_ROUND_TWO
  -> VERIFYING_ROUND_TWO_CANDIDATES
     -> EVIDENCE_INCOMPLETE -> WAITING_FOR_EVIDENCE_DECISION
     -> ROUND_TWO_READY -> M1_COMPLETE
```

Treat `EVIDENCE_INCOMPLETE` and `WAITING_FOR_EVIDENCE_DECISION` as non-success states that end the current attempt. Do not transition either state to `M1_COMPLETE`. Resume from the affected round only after the user supplies evidence, changes the requirement, or authorizes an appropriate bounded follow-up search.

Do not skip verification when moving between states. Preserve the brief, search plan, candidate pool, selections, limitations, gaps, and feedback delta needed to explain every transition. Enter `M1_COMPLETE` only through `ROUND_TWO_READY` after both rounds satisfy their required evidence gates.

Record every saved calibration bundle with this exact terminal-state envelope:

```yaml
schema_version: "m1.2"
terminal_state: "WAITING_FOR_EVIDENCE_DECISION" # or "M1_COMPLETE"
stopped_after_round: 1 # or 2
outcome: "evidence_incomplete" # or "complete"
round1: {}
feedback_delta: {} # required only when stopped_after_round is 2
round2: {} # required only when stopped_after_round is 2
```

Use only these consistent terminal combinations: round one plus `evidence_incomplete` ends in `WAITING_FOR_EVIDENCE_DECISION`; round two plus `evidence_incomplete` also ends there; round two plus `complete` ends in `M1_COMPLETE`. When `stopped_after_round` is `1`, omit both `feedback_delta` and `round2`; reject either field if present. When it is `2`, require and preserve both fields even if round-two evidence is incomplete. Never claim `M1_COMPLETE` unless round one is ready and round two has a complete, gap-free eligible selection.

## Build the brief

Extract supplied facts before asking questions. Ask at most three short questions, and ask only for missing fields that materially change query construction or recommendation eligibility. Preserve unknowns as empty values or `open_questions`; do not infer them.

Use this exact shape:

```yaml
research_brief:
  brief_version: 1
  branch_id: "branch-a"
  engineering_object: ""
  target_problem: ""
  target_metric: ""
  available_data: []
  resources: []
  time_budget: ""
  preferred_routes: []
  excluded_routes: []
  hard_constraints: []
  soft_preferences: []
  open_questions: []
  evidence_needs: []
```

Use exactly these 14 fields. Set `brief_version` to a positive integer, never a boolean. Keep `branch_id`, `engineering_object`, `target_problem`, `target_metric`, and `time_budget` as non-empty text. Keep `available_data`, `resources`, `preferred_routes`, `excluded_routes`, `hard_constraints`, `soft_preferences`, `open_questions`, and `evidence_needs` as lists even when empty. Keep hard constraints separate from soft preferences. Record missing information in `open_questions` when it does not block a bounded search. Stop and ask before searching only when a missing answer would materially alter the query or make recommendation eligibility impossible to judge.

## Plan the search

Translate the current brief into queries with distinct purposes and expected evidence roles. Use this exact shape:

```yaml
search_plan:
  round: 1
  brief_version: 1
  branch_id: "branch-a"
  time_boundary: []
  language_boundary: []
  source_boundary: []
  queries:
    - query_id: "Q1"
      purpose: "direct_problem"
      query_text: ""
      expected_evidence_role: "direct_problem"
      inclusion_terms: []
      exclusion_terms: []
  limitations: []
```

Use exactly these eight plan fields, including every boundary and `limitations` even when its list is empty. Keep `time_boundary`, `language_boundary`, `source_boundary`, and `limitations` as lists. Match `round` to the enclosing round, and match `brief_version` and the non-empty `branch_id` to the current brief.

Use exactly these six fields for every query. Assign a non-empty `query_id` that is unique within the round, keep `query_text` non-empty, and use only `direct_problem`, `method`, `transfer_bridge`, or `counter_limitation` for `purpose` and `expected_evidence_role`. Keep `inclusion_terms` and `exclusion_terms` as lists. Keep query text traceable to the brief and expose exclusions instead of silently filtering results.

Report the searched boundary and its limitations. Never describe bounded results as exhaustive, novelty-complete, or proof that no prior work exists.

## Assemble the pool

Keep discovery hits separate from the candidate pool. Admit a record to `candidate_pool` only after applying [Citation integrity](core-citation-integrity.md). Use this item contract:

```yaml
candidate_pool:
  - candidate_id: "P1"
    verification_status: ""
    recommendation_eligible: false
    evidence_roles: ["direct_problem"]
    selection_role: "direct_problem"
    basis_level: "metadata_level"
    verified_record: {}
```

Assign each candidate one stable `candidate_id` across both rounds of the calibration cycle. Keep the same ID when the record is retained, downgraded, or reconsidered in round two. Never reuse one ID for a different work or assign a new ID to the same carried work.

Require each pool item to contain exactly one verified paper record and its current verification state. Require `selection_role` on every item and set it to exactly one of `direct_problem`, `method`, `transfer_bridge`, or `counter_limitation`. Require the selected value to appear in that item's `evidence_roles` list. Treat a missing, out-of-set, or unsupported `selection_role` as invalid.

Deduplicate records before selection. Do not place unresolved, conflicted, not-found, or manual-review records in the recommendation pool. Preserve such discovery outcomes separately as limitations or evidence gaps.

Assemble 15–20 verified, deduplicated candidates for round one when reliable evidence exists. Cover direct-problem, method, transfer or bridge, and counterexample or limitation needs where the evidence permits. Do not create metadata, identifiers, authors, titles, publication states, or evidence roles to reach the target count.

## Select round one

Select eight recommendation-eligible records only when the pool supports this fixed allocation: three `direct_problem`, two `method`, two `transfer_bridge`, and one `counter_limitation`. Count the selected IDs strictly by their resolved candidate-pool item's `selection_role`; do not infer the quota role from the map, free text, or a different evidence role. Require every entry in `selected_ids` to resolve to exactly one candidate-pool item and exactly one verified paper record. Reject missing IDs, duplicate IDs, ambiguous resolutions, and blocked verification states.

Do not substitute a weaker record, a record from another role, or an ineligible discovery hit when any role quota is short. Leave the affected slot unfilled, record the missing role and count in `evidence_gaps`, set the outcome to `evidence_incomplete`, and end the attempt in `WAITING_FOR_EVIDENCE_DECISION`.

Build the user-facing static map and equivalent text fallback under [Static paper evidence map](core-paper-map.md). Keep every map claim within its declared metadata-, abstract-, or full-text-level basis.

Use this exact round bundle shape:

```yaml
round_bundle:
  schema_version: "m1.2"
  round: 1
  research_brief: {}
  search_plan: {}
  candidate_pool: []
  selected_ids: []
  paper_map: {}
  evidence_gaps: []
  search_limitations: []
```

Populate `research_brief` and `search_plan` with the complete current objects rather than summaries. Copy unresolved evidence needs into `evidence_gaps`, and copy tool, source, time, language, access, and full-text limits into `search_limitations`.

## Apply feedback

Accept ordinary chat feedback. Diagnose whether the user rejected papers, challenged citations, changed constraints, changed direction, or requested a reset by applying [Feedback, search history, and rollback](core-feedback-rollback.md).

Expose the transition in this contract:

```yaml
feedback_delta:
  from_brief_version: 1
  to_brief_version: 2
  inherited:
    - object_id: "public-data-only"
      value: "Use public data only"
  rejected:
    - object_id: "random-split-dependent-designs"
      value: "Designs that mix one physical source across train and test"
      reason: "They can inflate evaluation through leakage"
  reset:
    - object_id: "round-one-title-level-fit"
      previous_value: "Title relevance counted as preliminary fit"
      reason: "Title evidence cannot establish isolation or leakage resistance"
  added:
    - object_id: "cross-load-evaluation-priority"
      value: "Prioritize cross-load or unseen-condition evaluation"
      reason: "The user promoted this evidence to a primary filter"
  allocation:
    exploit: 30
    explore: 70
  query_changes:
    - query_id: "Q-STABLE"
      reason: "Exclude proprietary-data routes and expand public simulation evidence"
      cause_refs:
        - "feedback_delta.rejected[0]"
        - "feedback_delta.reset[0]"
        - "feedback_delta.added[0]"
      before: "data-driven control using proprietary industrial datasets"
      after: "data-driven control using public simulation datasets excluding proprietary data"
```

Use exactly the top-level fields shown in `feedback_delta`. Treat every item schema as closed: require inherited items to contain exactly `{object_id,value}`; rejected items exactly `{object_id,value,reason}`; reset items exactly `{object_id,previous_value,reason}`; and added items exactly `{object_id,value,reason}`. Reject unknown fields and require every field value to be non-empty text. Show inherited, rejected, reset, and newly added constraints before planning the next search branch. Make integer `allocation` values total 100 and treat them as a query-and-candidate budget, not a probability.

Create a new brief version before round two. Match the second-round plan to the new version. M1.2 has no branch-change object, so require one identical, non-empty `branch_id` across both ResearchBriefs and both SearchPlans. Add at least one `query_changes` entry whenever a rejection reason, new constraint, or reset materially affects the search.

Require each query change to contain a non-empty `cause_refs` list of exact paths to existing `feedback_delta.rejected`, `feedback_delta.reset`, or `feedback_delta.added` entries. Never cite `feedback_delta.inherited`. Cover every material rejected, reset, or added entry with at least one `cause_refs` path, and reject unresolved paths or uncovered material entries.

For a modified query, preserve one stable `query_id`: require it exactly once in each round, require `before` to equal only that round-one query's `query_text`, and require `after` to equal only that round-two query's `query_text`. For an added query, require its ID to be absent from round one and present exactly once in round two, with `after` equal to its `query_text`. For a removed query, require its ID exactly once in round one and absent from round two, with `before` equal to its `query_text`. Never use `query_id`, `purpose`, `expected_evidence_role`, terms, or any other query field as a substitute for `query_text`.

Set `before` to the exact corresponding round-one `query_text` and `after` to the exact corresponding round-two `query_text`. Allow an added query to leave only `before` empty, allow a removed query to leave only `after` empty, and require a modified query to provide two non-empty, different values. Require the revised plan to implement every non-empty recorded `after` value. Do not claim feedback was applied when the new plan is unchanged for no stated reason.

## Select round two

Build a second `RoundBundle` with `round: 2`, the revised brief, the revised search plan, and the verified candidate state used for selection. Keep candidate IDs stable for carried records and assign new IDs only to newly admitted works.

Return five to six recommendation-eligible papers by default when reliable evidence exists. Preserve missing role coverage and search limits instead of filling slots with weak records.

Add `round_two_request` only to a round-two bundle. Use this exact object when the user explicitly requests eight papers:

```yaml
round_bundle:
  schema_version: "m1.2"
  round: 2
  research_brief: {}
  search_plan: {}
  candidate_pool: []
  selected_ids: ["P1", "P2", "P4", "P5", "P9", "P16", "P17", "P18"]
  round_two_request:
    explicit_user_request: true
    requested_count: 8
  paper_map: {}
  round_one_dispositions: []
  evidence_gaps: []
  search_limitations: []
```

For the default five-to-six-paper result, omit `round_two_request` or set `explicit_user_request: false`; when the object is present, set integer `requested_count` to the exact number of round-two `selected_ids`. Allow seven to ten selected IDs only when `round_two_request.explicit_user_request` is exactly `true` and `round_two_request.requested_count` equals the selected-ID count. Treat seven to ten without that authorization, any requested-count mismatch, any count above ten, or any `round_two_request` field in a round-one bundle as invalid. Never infer expansion authorization from an old brief, allocation, or assistant suggestion.

Attach `round_one_dispositions` to the round-two bundle with this shape:

```yaml
round_one_dispositions:
  - round_one_id: "P3"
    disposition: "removed"
    round_two_id: null
    reason: "Requires inaccessible proprietary data"
    cause_type: "feedback_delta"
    cause_ref: "feedback_delta.rejected[0]"
```

Include exactly one disposition entry for every round-one `selected_id` and no entry for an ID that was not selected in round one. Use exactly one disposition from `retained`, `replaced`, `downgraded`, or `removed`:

- Set `retained` when the same stable candidate remains selected in round two; set `round_two_id` to the same ID.
- Set `replaced` when the round-one candidate leaves the selection and a newly admitted or newly preferred candidate takes its place; set `round_two_id` to that selected replacement ID.
- Set `downgraded` when new verification or reasoning evidence reduces the candidate's eligibility, role, or basis. Set `round_two_id` to the same ID only if it remains recommendation-eligible and selected; otherwise set it to null and keep the record as labeled supplemental or blocked evidence outside `selected_ids`.
- Set `removed` when the round-one candidate leaves without a one-for-one replacement; set `round_two_id` to null.

Give every disposition a non-empty `reason`. Set `cause_type` to `feedback_delta` or `new_evidence`. For a feedback cause, point `cause_ref` only to an exact existing `feedback_delta.rejected`, `feedback_delta.reset`, or `feedback_delta.added` item; never use `feedback_delta.inherited` as a material cause. For a new-evidence cause, point it to the exact newly checked verification source or evidence record that caused the disposition. Do not cite a vague narrative, model memory, or an unverified discovery hit as a cause.

Require the disposition entries to cover the round-one selection exactly once before calling round two ready. Keep a replaced candidate out of round-two `selected_ids`, require its non-null `round_two_id` to resolve to one eligible selected record, and keep retained IDs in round-two `selected_ids`.

Map replacement targets one-to-one. Require every `replaced.round_two_id` to be unique across the disposition list. Do not let two replaced entries share one round-two target, and do not let a replaced target equal the `round_two_id` claimed by a retained or downgraded entry. Treat a missing, null, duplicate, shared, or conflicting replacement target as invalid. Treat any other missing, duplicate, untraceable, or contradictory disposition as invalid.

## Report incomplete evidence

Set the outcome to `evidence_incomplete` whenever the verified pool, selection count, role coverage, source access, or reasoning basis cannot support the requested complete round. Keep `selected_ids` limited to eligible records and leave missing slots unfilled.

End the current attempt in `WAITING_FOR_EVIDENCE_DECISION`. Keep the M1 workflow incomplete, and do not reinterpret the visible gap as successful completion.

If the gap occurs in round one, save only the root terminal fields and `round1`; do not fabricate feedback or an empty second round. If the gap occurs in round two, preserve the applied `feedback_delta`, the attempted `round2`, its dispositions, limitations, and exact gaps so the attempt remains auditable.

Report:

- the completed checks and their evidence level;
- the exact missing count, role, source, or verification step;
- the boundary and limitation that caused the gap;
- the user decision or additional evidence needed to continue.

Do not convert discovery hits, partial metadata, abstract-only checks, fixtures, or offline structural validation into proof of real citation verification. Do not weaken a gate or invent a record to produce a complete-looking bundle.

## Stop at the M1 boundary

End the current output after reporting the available paper-calibration state, map, feedback effects, gaps, and limitations. Mark the two-round workflow `M1_COMPLETE` only when the complete `ROUND_TWO_READY` path succeeds. When the outcome is `evidence_incomplete`, end the output in `WAITING_FOR_EVIDENCE_DECISION` and keep M1 incomplete.

Treat `M1_COMPLETE` here as the successful workflow state, not as permission to mark the repository milestone complete before its external acceptance gates pass. Do not rank research directions, generate direction cards, choose a main direction, create a full experiment or simulation route, build a method corpus, connect RRC, add a retrieval service, download a model, deploy a runtime, or start platform integration.

Ask for the user's next direction explicitly when later work would cross this boundary. Keep audits read-only and do not write to user files without an explicit request.

<!-- source: references/core-paper-map.md; source_sha256: f9ea829896d0436c5d85f633af94de472eabb9cfa82c438778210fa2c10a179b -->
# Static Paper Evidence Map

Use this file after verified, deduplicated papers are available. Use the map for fast orientation before the user reads the papers; do not present it as an interactive knowledge base or a substitute for full-paper reading.

## Contents

- Select eligible papers by round
- Build the map
- Encode meaning consistently
- Label the evidence basis
- Keep notes minimal
- Render with graceful fallback
- Use the required data shape
- Enforce Mermaid and fallback equivalence
- Accept chat feedback

## Select eligible papers by round

For round one, select up to eight recommendation-eligible papers with this fixed role allocation:

- three `direct_problem` papers;
- two `method` papers;
- two `transfer_bridge` papers;
- one `counter_limitation` paper.

Fill a role slot only with a verified record that is recommendation-eligible and supported at the declared basis level. Do not reassign a weaker, blocked, partial, or merely discovered paper to fill a missing role. Do not borrow an eligible paper from another role to make the total look complete. Record every unfilled role and count in `evidence_gaps`, set the round outcome to `evidence_incomplete`, leave the slot empty, and stop on the non-success path defined by the calibration contract.

For round two, show five to six recommendation-eligible papers by default when reliable evidence supports that count. For this default, let the containing round-two bundle omit `round_two_request` or set `round_two_request.explicit_user_request: false` with `requested_count` equal to the selected-ID count.

Show seven to ten only when the containing round-two bundle records both `round_two_request.explicit_user_request: true` and a `round_two_request.requested_count` equal to the selected-ID count. Treat a missing or false authorization, a requested-count mismatch, or more than ten selected IDs as invalid. Do not put `round_two_request` in a round-one bundle, infer authorization, or pad a short second round with weak or ineligible evidence.

## Build the map

1. Place the current research problem or brief at the center.
2. Create two to four direction, problem, method, or transfer clusters.
3. Apply the round-specific selection rules above before drawing any paper node.
4. Preserve each candidate's stable ID throughout the calibration cycle and place exact citations in a table below the map.
5. Limit each paper to one or two explanatory edges.

## Encode meaning consistently

- Size a paper node by relative fit to the current `ResearchBrief`, not by citation count or general prestige.
- Color a paper node by evidence role: direct problem, method, transfer/bridge, or counter/limitation.
- Use the border or an explicit marker to distinguish `verified_primary`, `verified_registry`, and `verified_preprint`. Keep partial or blocked records outside selected paper nodes.
- Use only these edge relations:
  - `same_problem`
  - `shared_method`
  - `transfer_bridge`
  - `claim_support`
  - `claim_tension`
  - `same_data_or_benchmark`
- Use line thickness for relationship strength within the current map.
- Use a dashed line for inferred transfer or incomplete evidence.
- Label every conclusion relation with a scoped claim rather than saying that two whole papers agree.

## Label the evidence basis

Set one `basis_level` for each note and edge:

- `metadata_level`: based only on bibliographic metadata and keywords.
- `abstract_level`: based on a verified abstract.
- `fulltext_level`: based on inspected full text with a source anchor.

Never label an abstract-level comparison as a full-text conclusion check. When full text is unavailable, state the limitation in the graph legend and paper index.

## Keep notes minimal

For each paper, show only:

- short title or compact label;
- year;
- one-line relevance note;
- verification/basis marker when needed.

Below the graph, show exact title, ordered authors, year, venue, DOI or official ID, verification state, and one-line role. Keep detailed summaries out of the diagram.

## Render with graceful fallback

1. Emit Mermaid directly in Markdown by default.
2. If Mermaid is unsupported, emit a grouped text tree with the same paper labels, roles, and relations.
3. Export a static SVG only when the user explicitly requests a file or competition asset.
4. Do not create an interactive HTML application, click handlers, a graph service, or a new network dependency.

## Use the required data shape

Include all of these fields in every round map. Set `node_size_basis` exactly to `user_fit`; do not omit it or substitute citation count, venue prestige, or general popularity.

```yaml
paper_map:
  round: 1
  node_size_basis: "user_fit"
  legend:
    evidence_roles: ["direct_problem", "method", "transfer_bridge", "counter_limitation"]
    basis_levels: ["metadata_level", "abstract_level", "fulltext_level"]
  nodes:
    - id: "P1"
      node_type: "paper"
      fit_score: 0.86
      evidence_role: "transfer_bridge"
      verification_status: "verified_primary"
      basis_level: "abstract_level"
      short_note: "Method transfer evidence from a similar data regime"
    - id: "D2"
      node_type: "cluster"
      basis_level: "abstract_level"
      short_note: "Public simulation evidence cluster"
  edges:
    - source: "P1"
      target: "D2"
      relation: "transfer_bridge"
      strength: "medium"
      confidence: "medium"
      basis_level: "abstract_level"
      note: "Mechanism is similar; boundary conditions still require testing"
  text_fallback:
    - entry_type: "node"
      id: "P1"
      node_type: "paper"
      evidence_role: "transfer_bridge"
      verification_status: "verified_primary"
      basis_level: "abstract_level"
      text: "P1: Method transfer evidence from a similar data regime"
    - entry_type: "node"
      id: "D2"
      node_type: "cluster"
      basis_level: "abstract_level"
      text: "D2: Public simulation evidence cluster"
    - entry_type: "edge"
      source: "P1"
      target: "D2"
      relation: "transfer_bridge"
      basis_level: "abstract_level"
      text: "P1 --transfer_bridge--> D2: Mechanism is similar; boundary conditions still require testing"
  mermaid: |-
    flowchart TD
      n0["id=P1; type=paper; basis=abstract_level; role=transfer_bridge; status=verified_primary; fit=0.86; note=Method transfer evidence from a similar data regime"]
      n1["id=D2; type=cluster; basis=abstract_level; note=Public simulation evidence cluster"]
      n0 -- "relation=transfer_bridge; basis=abstract_level; strength=medium; confidence=medium; note=Mechanism is similar; boundary conditions still require testing" --> n1
```

Treat the seven `paper_map` fields as closed: `round`, `node_size_basis`, `legend`, `nodes`, `edges`, `text_fallback`, and `mermaid`. Treat `legend.evidence_roles` and `legend.basis_levels` as closed lists for M1. Use the exact role and basis tokens shown above. Require every selected paper ID to appear exactly once as a paper node. Do not place an unselected, blocked, partial, or unresolved citation in a paper node.

Require every paper node to contain exactly `id`, `node_type`, `fit_score`, `evidence_role`, `verification_status`, `basis_level`, and `short_note`. Set `fit_score` to a non-Boolean number from zero through one. Require every cluster node to contain exactly `id`, `node_type`, `basis_level`, and `short_note`; never put `fit_score`, `evidence_role`, or `verification_status` on a cluster. Require every edge to contain exactly `source`, `target`, `relation`, `strength`, `confidence`, `basis_level`, and `note`.

## Enforce Mermaid and fallback equivalence

Generate Mermaid and `text_fallback` from the same structured `nodes` and `edges`; do not maintain separate semantic versions by hand.

Call the deterministic renderers in `scripts/render_m1_map.py` after the structured nodes and edges are complete. Preserve their order; do not sort either collection. Treat `nodes` and `edges` as the only map facts and reject either rendered output unless it exactly equals the renderer result. Render node fallback text exactly as `{id}: {short_note}` and edge fallback text exactly as `{source} --{relation}--> {target}: {note}`. Escape backslash, quote, newline, bracket, and pipe characters in Mermaid labels so user text cannot alter the graph syntax.

Require the Mermaid rendering and text fallback to preserve all of the following without renaming:

- every node ID and edge endpoint;
- every paper's evidence role;
- every edge relation label;
- every paper's verification state;
- every node and edge basis level.

Add exactly one `entry_type: node` fallback entry for every structured node and exactly one `entry_type: edge` fallback entry for every structured edge. Keep the fallback IDs, roles, relation labels, verification states, and basis levels identical to their structured records and visible Mermaid markers or labels. Include non-paper brief or cluster nodes in both renderings when they appear in either one.

Reject a map when Mermaid and `text_fallback` differ on an ID, endpoint, role, relation, verification state, or basis level. Reject an edge whose declared basis exceeds the supporting paper basis. Treat an omitted fallback, an incomplete fallback, or a citation-count-sized map as invalid rather than as a degraded success.

## Accept chat feedback

Invite concise natural-language feedback such as:

```text
Focus more on D2; retain P1 and P5; exclude routes requiring private data;
prefer executable simulations; increase the share of transfer methods.
```

Do not require the user to click the map, read every paper, or score every node. Apply the feedback through the rollback protocol and show the change summary before searching again.

<!-- source: references/domain-nuclear-ml.md; source_sha256: 52cfc31f15dac1240235136b9f1c402e8e9d39069789a17d4b5468bba065727f -->
# Nuclear Engineering × Machine Learning Overlay

Apply [Method coaching](core-method-coaching.md) first. Use this additive `nuclear_engineering_ml` overlay only with applicable cards from [Data, machine learning, and hybrid methods](method-data-ml-hybrid.md), [Reliability, safety, and risk](method-reliability-safety-risk.md), [Modeling, simulation, and VVUQ](method-modeling-simulation-vvuq.md), [Signal processing and diagnostics](method-signal-diagnostics.md), [Control, optimization, and identification](method-control-optimization-identification.md), or [Experiment, measurement, and UQ](method-experiment-measurement-uq.md). Populate exactly the closed overlay fields `schema_version`, `overlay_id`, `domain`, `base_card_ids`, `additional_assumptions`, `additional_failure_modes`, `additional_validation_checks`, `additional_stop_conditions`, `specialist_review_boundaries`, `transfer_status`, and `source_ledger`. Treat the last eight as additive payload fields in addition to the first three identity fields; do not copy or replace general procedures.

## Base-card binding

- Populate `base_card_ids` only with unique card IDs from the same validated M3 bundle, and retain every base card's assumptions, resources, checks, failures, conditions, safety boundaries, and ledger.
- Select only the families needed by the confirmed claims and declared intended use; the overlay adds nuclear-specific constraints and never turns bounded coaching into a complete route.
- Keep plant, unit, design, simulator, scenario, operating mode, transient, accident class, fuel cycle, sensor configuration, and time period distinct wherever any of them can create dependence or distribution shift.

## Additional assumptions

- Record which observations are plant data, experimental data, simulator output, synthetic data, or expert judgment, and state the fidelity, operating envelope, configuration identity, and provenance of each.
- State the simulator-to-plant gap, scale and facility differences, physics coverage, sensor equivalence, scenario coverage, and intended nuclear function; do not infer plant validity from simulator performance.
- State the credited and non-credited safety functions, defense-in-depth layers, operator role, automation boundary, and whether the output is informational, advisory, control-related, or protection-related.
- State exactly: nuclear × ML transfer remains a `hypothesis` until a target-domain decisive test supports it.

## Additional failure modes

- Add plant or scenario leakage, simulator artifacts, unmodeled physics, non-conservative surrogate error, conservation-law violation, rare-transient scarcity, sensor drift or failure, OOD overconfidence, configuration drift, common-cause software failure, automation surprise, and misleading operator reliance when relevant.
- Add failures caused by conflating code verification, solution verification, model validation, uncertainty quantification, ML evaluation, and target-domain transfer evidence.
- Add loss or weakening of diversity, redundancy, independence, defense in depth, deterministic protection, conservative limits, human oversight, or shutdown authority as explicit failures.

## Additional validation checks

- Enforce plant-, unit-, design-, scenario-, operating-mode-, configuration-, and time-aware separation before fitting or evaluation; keep correlated simulator descendants and plant records out of opposing partitions.
- Check governing physics, dimensional consistency, conservation of mass, energy, momentum, charge, or neutron balance as applicable, monotonic or limiting behavior, and conservative response in safety-relevant regimes.
- Test declared sensor loss, drift, saturation, bias, timing failure, missing channels, correlated failures, distribution shift, unseen transients, and OOD inputs; verify the fallback and human-visible uncertainty behavior.
- Keep code verification, solution verification, model validation, UQ, ML generalization, simulator-to-plant transfer, and operational qualification as separate evidence claims.
- Require independent nuclear-domain review of scenario coverage, physics checks, uncertainty treatment, safety-function interaction, defense-in-depth preservation, human factors, and claimed intended use.
- State exactly: offline contract validation is not nuclear-safety validation.

## Additional stop conditions

- Populate `additional_stop_conditions` only with the closed numeric `stop` criterion objects defined by [Method coaching](core-method-coaching.md), using selected-direction metric IDs and exact units.
- Copy each applicable operator and finite threshold from the selected-direction minimum decisive test in `bounded` mode or the validated route in `route_specific` mode; never invent or tune a nuclear-safety threshold in M3.
- Use only existing criteria relevant to physics or conservation residuals, target-domain error, OOD or sensor-failure degradation, uncertainty, false alarms, missed events, constraint violations, or defense-in-depth performance.
- Put missing plant/scenario separation, absent target-domain evidence, invalid VVUQ lineage, failed physics checks, unreviewed protection interaction, or licensing uncertainty in base-card `applicability.incompatible_conditions` or `specialist_review_boundaries`, not in fabricated numeric conditions.

## Specialist review boundaries

- Require independent qualified nuclear engineering, VVUQ, instrumentation and controls, human-factors, cybersecurity, radiation-protection, and safety specialists according to the proposed function and hazard scope.
- Preserve licensed technical specifications, regulatory commitments, approved safety analyses, deterministic protection, defense in depth, operator authority, and facility procedures over any method-card recommendation.
- Treat licensing basis, safety classification, software quality assurance, protection-system credit, technical-specification changes, operational limits, emergency procedures, and risk acceptance as regulator, licensee, and specialist decisions outside method coaching.
- Do not authorize plant data access, simulator or plant execution, model training, online adaptation, control action, protection action, maintenance deferral, deployment, licensing conclusions, or nuclear-safety conclusions.

## Source-ledger limits

- Populate the overlay `source_ledger` under the closed rules in [Method coaching](core-method-coaching.md); require at least one eligible non-preprint row whose `support_types` includes `safety`.
- Bind each source to the reported reactor or facility class, scenario, simulator or plant basis, sensor configuration, VVUQ level, safety function, operating envelope, and regulatory context.
- State what each source does not support, including plant transfer, unseen transients, operational qualification, protection credit, licensing acceptance, or nuclear safety.
- Keep preprints limited to method or exploration support and never use them as the sole basis for a main direction or safety-related conclusion.

<!-- source: references/method-control-optimization-identification.md; source_sha256: d118b2baec078b9b991619b3fb75de24b4df54866e2329e893092a6a005a7805 -->
# Control, Optimization, and System Identification

Apply [Method coaching](core-method-coaching.md) first. Use this family protocol to populate only the closed card fields permitted by that protocol; do not create a control route or authorize closed-loop operation.

## Applicability

- Select `control_optimization_identification` for claims about system identification, state or parameter estimation, controller design, constrained optimization, or closed-loop performance.
- Bind the card only to M2-derived claims, decision metrics, required preconditions, and resource ceilings.
- Put the plant or model identity, excitation and observation records, objective and constraint definitions, operating envelope, baseline implementation, and safety-limit specification in `applicability.required_inputs`.
- Put invalid provenance, unavailable safe excitation, failed identifiability or observability, undefined constraints or shutdown authority, unresolved required inputs, and unavailable specialist safety review in `applicability.incompatible_conditions`.
- Reserve `stop_conditions` and `pivot_conditions` exclusively for closed numeric criterion objects; do not encode missing artifacts, provenance failures, or safety gates there.
- Separate identification, estimation, optimization, and closed-loop claims so evidence for one does not automatically support another.

## Assumptions

- State model structure, operating region, observability, controllability, stationarity, noise, delay, actuator, sensor, and disturbance assumptions.
- State the objective, constraints, horizon, feasibility assumptions, and intended closed-loop operating envelope.
- Label linearization, plant-model equivalence, persistent excitation, and transfer to new regimes as hypotheses until checked.

## Minimum resources

- Put only finite, non-boolean numeric requirements such as excitation-sample counts, validation-scenario counts, sampling capacity, time, memory, or compute capacity in `minimum_resources`.
- Bind every row by `source_constraint_id`, `resource`, and `unit` to an inherited M2 resource ceiling whose operator is `<` or `<=`; remain strictly within that ceiling.
- Keep excitation records, sensors, plant or model definitions, objective and constraint records, baseline implementations, and shutdown specifications in `applicability.required_inputs`, not in `minimum_resources`.
- Treat an absent matching ceiling as an incompatible input state, not as permission to invent or widen a resource allowance.

## Baselines and controls

- Include a simple controller, estimator, identification model, or optimization heuristic as the primary baseline.
- Compare alternatives on identical disturbances, initial conditions, constraints, horizons, objectives, and data partitions.
- Include open-loop, nominal-model, or no-adaptation controls only when safe and relevant to the claim.

## Procedure

- Check that proposed excitation is informative over the target dynamics and remains within inherited and safety constraints.
- Check structural and practical identifiability, observability, parameter correlation, and uncertainty before interpreting fitted parameters.
- Define objectives and constraints independently of the candidate solution; check feasibility before comparing optimality.
- Evaluate stability margins, delay, saturation, disturbances, model mismatch, uncertainty, and constraint satisfaction before recommending closed-loop use.
- Separate offline identification or simulation checks from hardware-in-the-loop and real-system evidence.
- Keep the outline advisory until the user separately authorizes any excitation, optimization run, or closed-loop execution.

## Metrics

- Use only selected-direction metric IDs and units in `primary_metrics`, stop conditions, and pivot conditions.
- Report fit and residual diagnostics for identification; report tracking, regulation, effort, constraint violations, robustness margins, and worst-case behavior for control.
- Report feasibility, objective value, optimality gap or bound, run variability, and constraint violations for optimization when available.

## Uncertainty

- Quantify parameter, state, disturbance, noise, delay, model-form, and operating-condition uncertainty relevant to the decision.
- Propagate identification uncertainty into estimator, controller, or optimizer assessment rather than treating fitted values as exact.
- Test sensitivity to initialization, excitation spectrum, model order, regularization, horizons, weights, and solver settings where applicable.

## Validation

- Validate residual independence, held-out prediction, identifiability, and parameter plausibility before using an identified model.
- Validate robust stability, performance, and constraint satisfaction across declared uncertainties and credible disturbances before closed-loop claims.
- Verify optimization results with feasibility checks, repeat starts or bounds when appropriate, and comparison to the simple baseline.
- Treat structural bundle validation as offline contract evidence, not as plant, controller, or optimizer performance.

## Failure modes

- List insufficient excitation, non-identifiability, hidden feedback, biased noise, drift, actuator saturation, estimator divergence, unstable poles, infeasibility, local minima, and model mismatch when relevant.
- Explain how each listed failure could change the bound claim or metric.
- Preserve unstable, infeasible, and unidentifiable outcomes; do not discard them as tuning artifacts.

## Stop/Pivot conditions

- Populate `stop_conditions` and `pivot_conditions` only with the closed numeric criterion objects defined by [Method coaching](core-method-coaching.md).
- In `bounded` mode, copy each applicable `metric_id`, `operator`, finite `value`, and `unit` from a matching selected-direction `minimum_decisive_test` stop or pivot criterion; in `route_specific` mode, copy them from the corresponding validated route condition.
- Use only criteria relevant to instability, constraint violation, estimator divergence, infeasibility, or identifiability; preserve the upstream operator, value, and unit verbatim.
- Fail closed and request upstream criterion repair when no applicable numeric stop or pivot criterion exists; never invent, estimate, or tune a threshold inside M3.
- Put unsafe excitation, failed identifiability or observability, invalid provenance, undefined constraints or shutdown authority, and safety-review failures in `applicability.incompatible_conditions`, not in numeric condition lists.

## Safety boundaries

- Require qualified controls and domain review before hardware excitation, actuator commands, online adaptation, protection interaction, or operation near physical limits.
- Require independently defined interlocks, fallback control, shutdown criteria, and manual authority before any separately authorized closed-loop test.
- Do not execute identification, optimization, controller deployment, or plant operation through method coaching.

## Source-ledger limits

- Apply the closed ledger and eligibility rules in [Method coaching](core-method-coaching.md); label every row as metadata-, abstract-, or full-text-level.
- Use method sources only within their demonstrated plant class, excitation, constraints, uncertainty, and operating region.
- State explicitly what each source does not support, including stability beyond analyzed regimes, global optimality, online safety, deployment, or transfer.
- Block conflicted or unresolved citations, and do not use a verified preprint as the sole support for a safety-related conclusion.

<!-- source: references/method-data-ml-hybrid.md; source_sha256: 3740fdf7223d63d36355f6ba04ba920ca905f058c3041b06180236244e4b1da8 -->
# Data, Machine Learning, and Hybrid Methods

Apply [Method coaching](core-method-coaching.md) first. Use this family protocol to populate only the closed card fields permitted by that protocol; do not create a data or training route, run a model, or authorize deployment.

## Applicability

- Select `data_ml_hybrid` for claims about statistical learning, machine learning, physics-informed learning, surrogate models, data fusion, or hybrid data-and-model methods.
- Bind the card only to M2-derived claims, decision metrics, required preconditions, and resource ceilings.
- Put dataset and label provenance, entity/scenario/time identities, split definitions, preprocessing specifications, feature and target definitions, intended-use conditions, calibration requirements, and the declared in-distribution and out-of-distribution boundaries in `applicability.required_inputs`.
- Put invalid provenance, non-independent partitions, unresolved leakage, unavailable labels or target definitions, unsupported deployment conditions, unresolved required inputs, and unavailable specialist safety review in `applicability.incompatible_conditions`.
- Reserve `stop_conditions` and `pivot_conditions` exclusively for closed numeric criterion objects; do not encode missing artifacts, provenance failures, or safety gates there.
- Separate predictive, causal, surrogate, anomaly-detection, and decision-support claims so performance evidence for one task does not support another automatically.

## Assumptions

- State the observational unit, target population, sampling mechanism, label process, missingness, dependence, stationarity, exchangeability, and class-prevalence assumptions.
- State the relationship between physics-based and learned components, including which constraints are exact, approximate, learned, or unchecked.
- Label generalization across entities, scenarios, sites, time periods, sensors, fidelities, or domains as a hypothesis until tested on the claimed target distribution.

## Minimum resources

- Put only finite, non-boolean numeric requirements such as independent-unit counts, labeled-event counts, repeat or seed counts, time, memory, storage, or compute capacity in `minimum_resources`.
- Bind every row by `source_constraint_id`, `resource`, and `unit` to an inherited M2 resource ceiling whose operator is `<` or `<=`; remain strictly within that ceiling.
- Keep datasets, labels, split manifests, preprocessing specifications, code identities, trained artifacts, and environment records in `applicability.required_inputs`, not in `minimum_resources`.
- Treat an absent matching ceiling as an incompatible input state, not as permission to invent or widen a resource allowance.

## Baselines and controls

- Include a simple non-ML, domain-rule, persistence, analytical, or classical statistical baseline appropriate to the claim.
- Compare every candidate on identical entity-, scenario-, and time-aware partitions, preprocessing provenance, evaluation units, and resource accounting.
- Include component-removal, shuffled-label, or no-physics controls when they isolate the claimed contribution without creating unsafe or misleading comparisons.

## Procedure

- Define entity, scenario, site, asset, subject, batch, and time boundaries before splitting; keep correlated descendants and future information out of training partitions.
- Fit imputation, normalization, augmentation, feature selection, dimensionality reduction, resampling, calibration, and learned preprocessing only on the training partition, then preserve the fitted-state provenance.
- Freeze the baseline, partitions, primary metrics, ablation plan, seeds or repeat policy, and numeric stop and pivot criteria before comparing methods.
- Run ablations that isolate every claimed learned, physical, fusion, or regularization component, and compare against the simple baseline under the same budget.
- Define calibration and OOD checks whenever the bound claim concerns probability quality, confidence, shift, transfer, novelty, alarms, or decision support.
- Keep the outline advisory until the user separately authorizes training, inference, data processing, or deployment.

## Metrics

- Use only selected-direction metric IDs and units in `primary_metrics`, stop conditions, and pivot conditions.
- Match metrics to the decision, prevalence, cost, and evaluation unit; pair aggregate scores with per-class, per-regime, and worst-slice results where relevant.
- Report calibration error or coverage when claims depend on confidence, and report OOD detection or shifted-domain degradation when claims depend on generalization or transfer.
- Compare accuracy or utility jointly with inherited compute, time, memory, data, and latency limits rather than hiding resource expansion.

## Uncertainty

- Quantify variation across independent entities, scenarios, sites, time periods, folds, random seeds, and repeated fits at the level relevant to the claim.
- Separate sampling, label, measurement, model, parameter, optimization, and distribution-shift uncertainty instead of collapsing them into one score.
- Report intervals or repeat distributions and state the aggregation rule; do not treat correlated rows, windows, or augmented samples as independent replicates.

## Validation

- Audit split independence and preprocessing isolation before interpreting any metric; verify that no label, future, test, or entity-linked information crosses the training boundary.
- Compare the simple baseline and all predeclared ablations under identical partitions and budgets, and preserve unfavorable or unstable repeats.
- Check calibration, OOD behavior, and distribution-shift sensitivity when the bound claim requires them.
- Slice errors by entity, scenario, time, class, operating regime, sensor state, missingness, and relevant protected or safety-critical subgroup; identify unsupported slices explicitly.
- Treat structural bundle validation as offline contract evidence, not as model performance, generalization, causal validity, or deployment qualification.

## Failure modes

- List entity or temporal leakage, preprocessing leakage, label contamination, shortcut learning, confounding, dataset shift, prevalence shift, class imbalance, missing-not-at-random data, overfitting, unstable optimization, miscalibration, OOD overconfidence, and failed hybrid constraints when relevant.
- Explain how each listed failure could change the bound claim or metric.
- Preserve failed seeds, negative ablations, unsupported slices, and shift failures; do not discard them as tuning noise.

## Stop/Pivot conditions

- Populate `stop_conditions` and `pivot_conditions` only with the closed numeric criterion objects defined by [Method coaching](core-method-coaching.md).
- In `bounded` mode, copy each applicable `metric_id`, `operator`, finite `value`, and `unit` from a matching selected-direction `minimum_decisive_test` stop or pivot criterion; in `route_specific` mode, copy them from the corresponding validated route condition.
- Use only criteria relevant to baseline underperformance, calibration failure, OOD or shift degradation, unacceptable slice error, repeat instability, or resource-limit performance; preserve the upstream operator, value, and unit verbatim.
- Fail closed and request upstream criterion repair when no applicable numeric stop or pivot criterion exists; never invent, estimate, tune, or optimize a threshold inside M3.
- Put invalid provenance, leakage, non-independent partitions, missing calibration or OOD definitions, unsupported deployment, and safety-review failures in `applicability.incompatible_conditions`, not in numeric condition lists.

## Safety boundaries

- Require qualified data, ML, domain, security, privacy, and safety review before using outputs for operational control, protection, maintenance deferral, personnel decisions, or other consequential actions.
- Preserve existing deterministic protections, interlocks, conservative rules, and human authority; a learned component must not silently replace them.
- Do not acquire or upload data, train or run models, download weights, allocate compute, deploy services, or issue operational decisions through method coaching.

## Source-ledger limits

- Populate `source_ledger` under the closed ledger and eligibility rules in [Method coaching](core-method-coaching.md); label every row as metadata-, abstract-, or full-text-level.
- Use sources only within their reported data provenance, populations, splits, baselines, metrics, shift conditions, uncertainty treatment, and intended use.
- State explicitly what each source does not support, including causal effects, unseen-domain transfer, calibration, robustness, deployment, or safety.
- Block conflicted or unresolved citations, and do not use a verified preprint as the sole support for a safety-related conclusion.

<!-- source: references/method-experiment-measurement-uq.md; source_sha256: 5bea276a78d044f5a15349c932ee152e45800c61ae6b43e03fe4f67cd7fb92ec -->
# Experiment, Measurement, and Uncertainty Quantification

Apply [Method coaching](core-method-coaching.md) first. Use this family protocol to populate only the closed card fields permitted by that protocol; do not create a route or authorize data collection.

## Applicability

- Select `experiment_measurement_uq` for claims that require controlled intervention, physical measurement, calibration, repeatability, reproducibility, or propagated measurement uncertainty.
- Bind the card only to M2-derived claims, decision metrics, required preconditions, and resource ceilings.
- Put the measurement model, calibration trace, data provenance, control definition, randomization or blocking decision, repeatability and reproducibility plan, and uncertainty-budget specification in `applicability.required_inputs`.
- Put missing or invalid provenance, calibration outside its valid range, unresolved required inputs, unavailable safety approval, and any other qualitative condition that makes the method unsuitable in `applicability.incompatible_conditions`.
- Reserve `stop_conditions` and `pivot_conditions` exclusively for closed numeric criterion objects; do not encode missing artifacts, provenance failures, or safety gates there.
- Hand off modeling-, control-, or signal-dominant checks to their directly linked family protocol instead of duplicating them here.

## Assumptions

- State the measurand, operating range, experimental unit, response, intervention, nuisance factors, and independence assumptions.
- State whether the measurement chain is stable, traceable, and sensitive enough for the minimum meaningful effect.
- Mark unverified apparatus behavior, transfer, scale-up, and causal assumptions as hypotheses.

## Minimum resources

- Put only finite, non-boolean numeric requirements such as independent-unit counts, repetition counts, acquisition capacity, time, or analysis capacity in `minimum_resources`.
- Bind every row by `source_constraint_id`, `resource`, and `unit` to an inherited M2 resource ceiling whose operator is `<` or `<=`; remain strictly within that ceiling.
- Keep reference standards, sensors, calibration records, controls, protocols, and datasets in `applicability.required_inputs`, not in `minimum_resources`.
- Treat an absent matching ceiling as an incompatible input state, not as permission to invent or widen a resource allowance.

## Baselines and controls

- Include a status-quo or simplest credible baseline and a control that isolates the intervention where the claim is causal.
- Decide explicitly whether to randomize, block, counterbalance, or preserve natural order; name the factor controlled and justify any omission.
- Separate negative, positive, reference, blank, and sham controls when the measurement mechanism requires them.

## Procedure

- Define a measurement model from measurand through sensor or transducer, calibration, acquisition, processing, and reported quantity; preserve units at every step.
- Record a calibration trace with the reference identity, valid range, version or date, corrections, calibration uncertainty, and applicability limits.
- Specify repeatability checks under unchanged conditions and reproducibility checks across the relevant operator, instrument, batch, site, or time factors.
- Fix the randomization or blocking decision, control observations, uncertainty budget, and a numeric stop condition before recommending a data-collection design.
- Keep the outline advisory until the user separately authorizes execution.

## Metrics

- Use only selected-direction metric IDs and units in `primary_metrics`, stop conditions, and pivot conditions.
- Report effect size with uncertainty, calibration residuals, repeatability variation, reproducibility variation, missingness, and control drift when applicable.
- Match the estimand and aggregation level to the experimental unit; do not substitute sample count for independent replication.

## Uncertainty

- Build an uncertainty budget that identifies random and systematic components, distributions or bounds, correlations, calibration contributions, resolution, drift, sampling, and model-form contributions.
- Propagate uncertainty with a method appropriate to the measurement model and state coverage or confidence semantics.
- Separate aleatory variability from epistemic uncertainty and show which components dominate the decision metric.

## Validation

- Check measurement range, sensitivity, calibration residuals, control behavior, missingness, repeatability, reproducibility, and unit consistency.
- Verify that randomization or blocking addresses the stated nuisance factors and that analysis preserves the experimental unit.
- Treat structural bundle validation as offline contract evidence, not as confirmation that the apparatus, calibration, or experiment performs as claimed.

## Failure modes

- List saturation, drift, hysteresis, contamination, batch effects, confounding, pseudo-replication, failed blinding, missing-not-at-random data, and calibration extrapolation when relevant.
- Explain how each listed failure could change the bound claim or metric.
- Preserve observed failures and unresolved checks; do not relabel them as acceptable variation.

## Stop/Pivot conditions

- Populate `stop_conditions` and `pivot_conditions` only with the closed numeric criterion objects defined by [Method coaching](core-method-coaching.md).
- In `bounded` mode, copy each applicable `metric_id`, `operator`, finite `value`, and `unit` from a matching selected-direction `minimum_decisive_test` stop or pivot criterion; in `route_specific` mode, copy them from the corresponding validated route condition.
- Use only criteria relevant to invalid calibration, excessive drift, inadequate precision, failed controls, or excessive decision uncertainty; preserve the upstream operator, value, and unit verbatim.
- Fail closed and request upstream criterion repair when no applicable numeric stop or pivot criterion exists; never invent, estimate, or tune a threshold inside M3.
- Put missing measurement models, calibration traces, controls, uncertainty budgets, provenance, and safety approvals in `applicability.incompatible_conditions`, not in numeric condition lists.

## Safety boundaries

- Require qualified laboratory or domain review for hazardous materials, radiation, pressure, high voltage, biological exposure, human participants, destructive testing, or regulated measurements.
- Do not convert method coaching into equipment operation, specimen handling, data collection, or a safety determination.
- Apply the stricter facility, legal, ethical, and specialist boundary whenever it conflicts with a proposed design.

## Source-ledger limits

- Apply the closed ledger and eligibility rules in [Method coaching](core-method-coaching.md); label every row as metadata-, abstract-, or full-text-level.
- Use method sources to support design or uncertainty choices only within the reported apparatus, population, scale, and conditions.
- State explicitly what each source does not support, including untested calibration ranges, causal effects, reproducibility, transfer, or safety.
- Block conflicted or unresolved citations, and do not use a verified preprint as the sole support for a safety-related conclusion.

<!-- source: references/method-modeling-simulation-vvuq.md; source_sha256: 848dbb654055a3030920ad1304bc0d251ce4a84fddf49efea42ab47d4cb92ce5 -->
# Modeling, Simulation, and VVUQ

Apply [Method coaching](core-method-coaching.md) first. Use this family protocol to populate only the closed card fields permitted by that protocol; do not create or execute a simulation route.

## Applicability

- Select `modeling_simulation_vvuq` for claims about mathematical or computational models, numerical predictions, scenario studies, digital twins, or multiphysics simulation.
- Bind the card only to M2-derived claims, decision metrics, required preconditions, and resource ceilings.
- Put the governing-model specification, code and configuration identity, benchmark or reference solution, convergence-study inputs, validation-data provenance, and uncertainty specification in `applicability.required_inputs`.
- Put missing or invalid code, benchmark, configuration, or validation provenance; use outside the declared validation domain; unresolved required inputs; and unavailable specialist safety review in `applicability.incompatible_conditions`.
- Reserve `stop_conditions` and `pivot_conditions` exclusively for closed numeric criterion objects; do not encode missing artifacts, provenance failures, or safety gates there.
- Keep code verification, solution verification, validation, and uncertainty quantification distinct throughout the card.

## Assumptions

- State governing equations, constitutive relations, geometry, dimensionality, boundary and initial conditions, closure relations, coupling assumptions, and intended use.
- State the spatial, temporal, parameter, regime, and population domain over which conclusions may apply.
- Label surrogate validity, scale transfer, omitted physics, and extrapolation as unresolved hypotheses until decisive evidence supports them.

## Minimum resources

- Put only finite, non-boolean numeric requirements such as solver-run counts, discretization counts, validation-observation counts, time, memory, or compute capacity in `minimum_resources`.
- Bind every row by `source_constraint_id`, `resource`, and `unit` to an inherited M2 resource ceiling whose operator is `<` or `<=`; remain strictly within that ceiling.
- Keep code access, model files, benchmark definitions, reference solutions, solver configurations, and validation datasets in `applicability.required_inputs`, not in `minimum_resources`.
- Treat an absent matching ceiling as an incompatible input state, not as permission to invent or widen a resource allowance.

## Baselines and controls

- Include a simpler analytical, reduced-order, empirical, or lower-fidelity model baseline appropriate to the claim.
- Hold inputs and comparison conditions constant when attributing improvement to a model, coupling, closure, or solver change.
- Include limiting cases, conservation checks, or benchmark solutions as controls when available.

## Procedure

- Perform code verification against analytical solutions, manufactured solutions, trusted benchmarks, or independently checked invariants to test equation implementation.
- Perform solution verification with mesh, time-step, iteration, tolerance, or solver convergence studies where applicable; justify non-applicability explicitly.
- Perform validation against independent observations within a declared validation domain and quantify model discrepancy separately from numerical error.
- Perform sensitivity analysis before interpreting influential parameters or prioritizing uncertainty reduction.
- Perform UQ across input, parameter, numerical, and model-form uncertainty without collapsing them into one unexplained error term.
- Keep the outline advisory until the user separately authorizes simulation execution.

## Metrics

- Use only selected-direction metric IDs and units in `primary_metrics`, stop conditions, and pivot conditions.
- Report quantities appropriate to the claim, including conservation residuals, observed order, discretization uncertainty, benchmark error, validation discrepancy, calibration error, or predictive coverage.
- Pair aggregate fit metrics with local, regime-specific, transient, or worst-case errors when those affect the intended use.

## Uncertainty

- Separate parameter, input, numerical, structural, and observational uncertainty and state how each is represented and propagated.
- Report sensitivity to uncertain assumptions, priors, ranges, correlations, boundary conditions, and solver settings.
- Distinguish parameter calibration from validation and prevent calibration data from serving as independent validation evidence.

## Validation

- Verify code correctness, numerical convergence, and comparison-data independence before making predictive claims.
- Define the validation domain and intended use; identify every extrapolation beyond tested regimes.
- Treat simulation-to-observation agreement as conditional validation evidence, never as real-world proof, causal proof, operational qualification, or safety validation.
- Treat structural bundle validation as offline contract evidence, not as evidence that a model is correct or predictive.

## Failure modes

- List coding defects, unconverged solutions, unstable coupling, non-identifiable calibration, compensating errors, omitted physics, regime extrapolation, data reuse, and numerical artifacts when relevant.
- Explain how each listed failure could change the bound claim or metric.
- Preserve divergent, non-convergent, and invalid runs as failures rather than selecting only favorable solutions.

## Stop/Pivot conditions

- Populate `stop_conditions` and `pivot_conditions` only with the closed numeric criterion objects defined by [Method coaching](core-method-coaching.md).
- In `bounded` mode, copy each applicable `metric_id`, `operator`, finite `value`, and `unit` from a matching selected-direction `minimum_decisive_test` stop or pivot criterion; in `route_specific` mode, copy them from the corresponding validated route condition.
- Use only criteria relevant to convergence, conservation residual, validation discrepancy, or decision uncertainty; preserve the upstream operator, value, and unit verbatim.
- Fail closed and request upstream criterion repair when no applicable numeric stop or pivot criterion exists; never invent, estimate, or tune a threshold inside M3.
- Put failed code verification, missing solution verification, non-independent validation, invalid provenance, extrapolation beyond the validation domain, and safety-review failures in `applicability.incompatible_conditions`, not in numeric condition lists.

## Safety boundaries

- Require qualified domain and VVUQ review before using model output for hazardous design, operational limits, licensing, certification, or safety decisions.
- Do not execute simulation software, allocate compute, calibrate an operational model, or issue a safety determination through method coaching.
- Preserve conservative physical, facility, regulatory, and specialist constraints over apparent numerical agreement.

## Source-ledger limits

- Apply the closed ledger and eligibility rules in [Method coaching](core-method-coaching.md); label every row as metadata-, abstract-, or full-text-level.
- Use method sources only for the equations, numerical method, validation regime, uncertainty treatment, and limitations they actually report.
- State explicitly what each source does not support, including untested regimes, predictive accuracy, real-world transfer, operational qualification, or safety.
- Block conflicted or unresolved citations, and do not use a verified preprint as the sole support for a safety-related conclusion.

<!-- source: references/method-reliability-safety-risk.md; source_sha256: bfe6a022c0f7e5ad74f0d3a822055613cf6760930fc6f853562c6b843f947839 -->
# Reliability, Safety, and Risk

Apply [Method coaching](core-method-coaching.md) first. Use this family protocol to populate only the closed card fields permitted by that protocol; do not create a safety case, execute a hazard analysis, or authorize an operational or regulatory decision.

## Applicability

- Select `reliability_safety_risk` for claims about reliability, availability, maintainability, hazards, failure probability, risk, resilience, or safety-related decision support.
- Bind the card only to M2-derived claims, decision metrics, required preconditions, and resource ceilings.
- Put the system and hazard scope, event and consequence definitions, exposure basis, population and observation windows, censoring rules, data-completeness record, dependency assumptions, and decision context in `applicability.required_inputs`.
- Put ambiguous events, missing exposure denominators, unknown data completeness, unresolved dependencies, unsupported rare-event extrapolation, absent defense-in-depth constraints, unresolved required inputs, and unavailable specialist review in `applicability.incompatible_conditions`.
- Reserve `stop_conditions` and `pivot_conditions` exclusively for closed numeric criterion objects; do not encode missing artifacts, provenance failures, or safety gates there.
- Separate reliability estimates, hazard identification, consequence analysis, risk aggregation, operational decisions, and regulatory conclusions so evidence for one does not automatically support another.

## Assumptions

- State system boundaries, mission time, operating states, event taxonomy, exposure unit, censoring, repair, recurrence, stationarity, independence, common-cause, and reporting assumptions.
- State the consequence categories, risk measure, uncertainty semantics, and any aggregation or risk-acceptance rule without presenting it as regulatory approval.
- Label sparse-event rates, dependence structures, surrogate consequences, external-hazard transfer, and extrapolation beyond observed exposure as hypotheses.

## Minimum resources

- Put only finite, non-boolean numeric requirements such as observed exposure, event counts, independent-unit counts, scenario counts, expert-review time, or analysis capacity in `minimum_resources`.
- Bind every row by `source_constraint_id`, `resource`, and `unit` to an inherited M2 resource ceiling whose operator is `<` or `<=`; remain strictly within that ceiling.
- Keep hazard logs, event records, exposure histories, maintenance histories, taxonomies, consequence models, dependency records, and review approvals in `applicability.required_inputs`, not in `minimum_resources`.
- Treat an absent matching ceiling as an incompatible input state, not as permission to invent or widen a resource allowance.

## Baselines and controls

- Include observed exposure-normalized rates, a simple classical reliability model, or a documented conservative reference as the primary baseline.
- Compare methods using identical event definitions, exposure windows, censoring rules, consequence categories, dependencies, and data-completeness assumptions.
- Preserve a defense-in-depth reference case and test whether the proposed method changes, bypasses, or weakens any independent protective layer.

## Procedure

- Freeze the system and hazard scope, event taxonomy, consequence categories, exposure denominator, observation period, censoring rules, and completeness criteria before estimation.
- Reconcile event and exposure records, quantify missing or excluded data, and distinguish zero observed events from zero risk.
- Map initiating events, dependencies, common causes, barriers, recovery paths, and consequences at the resolution needed by the bound claim.
- Fit or compare reliability and risk estimates only within supported populations and exposure; state rare-event limits and avoid unsupported tail extrapolation.
- Test sensitivity to event definitions, reporting completeness, dependence, common-cause assumptions, priors, distributions, consequence models, and exposure boundaries.
- Keep the outline advisory until the user separately authorizes analysis execution or any operational use.

## Metrics

- Use only selected-direction metric IDs and units in `primary_metrics`, stop conditions, and pivot conditions.
- Express events, failures, and false alarms with an explicit exposure basis such as hours, demands, cycles, missions, components, or opportunities.
- Pair mean or point estimates with uncertainty and tail, worst-case, barrier, and consequence measures appropriate to the decision.
- Do not substitute accuracy, availability, or a composite risk score for a safety claim whose event and consequence definitions differ.

## Uncertainty

- Separate aleatory variability, epistemic uncertainty, model-form uncertainty, parameter uncertainty, data incompleteness, reporting uncertainty, and expert-judgment uncertainty.
- Show sensitivity to distributions, priors, dependence, common causes, censoring, event classification, exposure boundaries, and consequence assumptions.
- Report rare-event interval width and identifiability limits; absence of observed failures is not evidence of negligible risk without adequate exposure and detection coverage.

## Validation

- Audit hazard scope, event definitions, exposure accounting, observation windows, censoring, completeness, traceability, and independence before interpreting risk estimates.
- Check model behavior against observed cases, limiting cases, known barriers, historical exposure, and conservative bounds where suitable.
- Stress assumptions governing rare events, common causes, dependencies, reporting loss, and consequence severity; show which assumptions control the conclusion.
- Verify that the proposed method preserves defense in depth, independent protection, conservative limits, human authority, and existing safety functions.
- Treat structural bundle validation as offline contract evidence, not as reliability demonstration, safety validation, operational qualification, or regulatory acceptance.

## Failure modes

- List ambiguous event taxonomy, denominator error, under-reporting, survivorship bias, informative censoring, dependence hidden as independence, common-cause omission, sparse-event overconfidence, tail-model misspecification, barrier-credit inflation, and consequence truncation when relevant.
- Explain how each listed failure could change the bound claim or metric.
- Preserve missing events, uncertain classifications, failed assumptions, and adverse sensitivity results; do not erase them through aggregation or expert averaging.

## Stop/Pivot conditions

- Populate `stop_conditions` and `pivot_conditions` only with the closed numeric criterion objects defined by [Method coaching](core-method-coaching.md).
- In `bounded` mode, copy each applicable `metric_id`, `operator`, finite `value`, and `unit` from a matching selected-direction `minimum_decisive_test` stop or pivot criterion; in `route_specific` mode, copy them from the corresponding validated route condition.
- Use only criteria relevant to exposure-normalized event rates, uncertainty width, adverse sensitivity, barrier performance, consequence bounds, or risk limits; preserve the upstream operator, value, and unit verbatim.
- Fail closed and request upstream criterion repair when no applicable numeric stop or pivot criterion exists; never invent, estimate, tune, or reinterpret a safety threshold inside M3.
- Put ambiguous events, missing exposure or completeness evidence, unresolved rare-event limitations, weakened defense in depth, and specialist-review failures in `applicability.incompatible_conditions`, not in numeric condition lists.

## Safety boundaries

- Preserve defense in depth, independent protection layers, conservative operating limits, fail-safe behavior, human oversight, and shutdown authority regardless of an estimated improvement.
- Require independent qualified specialist review before using a card for operational, licensing, certification, regulatory, or safety-significant conclusions.
- Do not issue a safety case, risk acceptance, operating permission, maintenance deferral, barrier credit, or regulatory conclusion through method coaching.

## Source-ledger limits

- Populate `source_ledger` under the closed ledger and eligibility rules in [Method coaching](core-method-coaching.md); label every row as metadata-, abstract-, or full-text-level.
- Use sources only for the hazards, systems, populations, exposure bases, event definitions, dependencies, consequence models, and uncertainty limits they actually report.
- State explicitly what each source does not support, including unobserved rare events, changed operating regimes, barrier credit, operational acceptance, transfer, licensing, or safety.
- Require non-preprint support for safety-related conclusions as defined by the core protocol; block conflicted, unresolved, or recommendation-ineligible citations.

<!-- source: references/method-signal-diagnostics.md; source_sha256: 97ed8870abd7ff549d095d4c8839c9b549e20e8a4de5a605597638dc93990b2b -->
# Signal Processing and Diagnostics

Apply [Method coaching](core-method-coaching.md) first. Use this family protocol to populate only the closed card fields permitted by that protocol; do not create a diagnostic route or authorize acquisition or operational decisions.

## Applicability

- Select `signal_diagnostics` for claims about sensing, preprocessing, feature extraction, detection, localization, diagnosis, prognosis inputs, or condition monitoring.
- Bind the card only to M2-derived claims, decision metrics, required preconditions, and resource ceilings.
- Put raw-signal provenance, sampling and clock metadata, sensor calibration, label definitions and provenance, independent-unit identities, segmentation boundaries, and preprocessing specifications in `applicability.required_inputs`.
- Put invalid signal or label provenance, unresolved sampling or alignment, non-independent partitions, unsupported operational use, unresolved required inputs, and unavailable specialist safety review in `applicability.incompatible_conditions`.
- Reserve `stop_conditions` and `pivot_conditions` exclusively for closed numeric criterion objects; do not encode missing artifacts, provenance failures, or safety gates there.
- Distinguish event detection, fault diagnosis, localization, and severity estimation so a metric for one task does not stand in for another.

## Assumptions

- State signal source, sensor response, sampling clock, bandwidth, synchronization, operating states, label origin, noise, missingness, and stationarity assumptions.
- State the independent unit and the boundaries between events, windows, assets, runs, operators, sites, and time periods.
- Label sensor equivalence, source-domain transfer, and unobserved-fault behavior as hypotheses until checked.

## Minimum resources

- Put only finite, non-boolean numeric requirements such as labeled-event counts, normal-exposure duration, independent-unit counts, storage, time, or analysis capacity in `minimum_resources`.
- Bind every row by `source_constraint_id`, `resource`, and `unit` to an inherited M2 resource ceiling whose operator is `<` or `<=`; remain strictly within that ceiling.
- Keep raw signals, timestamps, sampling metadata, calibration records, labels, asset identities, split definitions, and preprocessing specifications in `applicability.required_inputs`, not in `minimum_resources`.
- Treat an absent matching ceiling as an incompatible input state, not as permission to invent or widen a resource allowance.

## Baselines and controls

- Include a simple threshold, spectral, statistical, or domain-rule baseline appropriate to the diagnostic task.
- Compare methods on identical independent units, operating regimes, label definitions, and evaluation windows.
- Include healthy or background exposure controls and known nuisance or sensor-artifact controls when available.

## Procedure

- Check sensor bandwidth, sampling rate, clock quality, anti-alias filtering, synchronization, saturation, clipping, and missing intervals before feature construction.
- Segment by asset, run, event, scenario, subject, site, or time boundary before splitting; prevent overlapping windows or correlated descendants from crossing partitions.
- Fit normalization, filtering parameters, imputation, feature selection, decomposition, thresholds, and learned preprocessing only on training data.
- Preserve a raw-to-segment provenance chain with label source and every preprocessing transform.
- Test performance across operating regimes, noise levels, sensor states, distribution shifts, and unseen units relevant to the claim.
- Keep the outline advisory until the user separately authorizes acquisition, processing, or operational use.

## Metrics

- Use only selected-direction metric IDs and units in `primary_metrics`, stop conditions, and pivot conditions.
- Use event- or time-aware detection metrics, class-sensitive diagnosis metrics, localization error, and severity error according to the bound task.
- Report false alarms with an exposure denominator such as time, cycle, asset, or opportunity; do not report a bare false-alarm count.
- Include missed-event rate, detection delay, per-class results, calibration, and uncertainty when they affect the claim.

## Uncertainty

- Quantify variation across independent units, acquisition periods, operating regimes, sensor states, labels, thresholds, and random seeds where applicable.
- Separate measurement noise, label uncertainty, sampling variability, threshold uncertainty, and distribution shift.
- Report confidence intervals or repeated-evaluation variability at the independent-unit level rather than treating overlapping windows as independent.

## Validation

- Verify signal provenance, units, sampling and aliasing assumptions, segmentation boundaries, train-only preprocessing, label alignment, and exposure accounting.
- Test shift across relevant assets, sites, regimes, time periods, fault types, or sensor failures and identify unsupported regions.
- Audit errors by class, regime, sensor state, and nuisance condition instead of relying on one aggregate score.
- Treat structural bundle validation as offline contract evidence, not as diagnostic accuracy, field performance, or operational qualification.

## Failure modes

- List aliasing, clipping, clock drift, leakage, duplicated windows, label delay, class imbalance, prevalence shift, sensor failure, domain shift, confounding operating states, and alert flooding when relevant.
- Explain how each listed failure could change the bound claim or metric.
- Preserve false alarms, missed events, invalid provenance, and unsupported shifts; do not hide them through favorable aggregation.

## Stop/Pivot conditions

- Populate `stop_conditions` and `pivot_conditions` only with the closed numeric criterion objects defined by [Method coaching](core-method-coaching.md).
- In `bounded` mode, copy each applicable `metric_id`, `operator`, finite `value`, and `unit` from a matching selected-direction `minimum_decisive_test` stop or pivot criterion; in `route_specific` mode, copy them from the corresponding validated route condition.
- Use only criteria relevant to false-alarm exposure, missed events, detection delay, sampling validity, or shift degradation; preserve the upstream operator, value, and unit verbatim.
- Fail closed and request upstream criterion repair when no applicable numeric stop or pivot criterion exists; never invent, estimate, or tune a threshold inside M3.
- Put invalid signal or label provenance, unresolved sampling or alignment, non-independent partitions, unsupported operational use, and safety-review failures in `applicability.incompatible_conditions`, not in numeric condition lists.

## Safety boundaries

- Require qualified signal, instrumentation, and domain review before using diagnostics for alarms, shutdowns, maintenance deferral, clinical action, or other safety-relevant decisions.
- Keep the diagnostic output advisory unless separately validated and authorized for its intended operational role; preserve existing protection and human oversight.
- Do not acquire signals, modify monitoring systems, deploy detectors, or issue operational decisions through method coaching.

## Source-ledger limits

- Apply the closed ledger and eligibility rules in [Method coaching](core-method-coaching.md); label every row as metadata-, abstract-, or full-text-level.
- Use method sources only within their reported sensors, sampling, segmentation, label quality, prevalence, operating regimes, and evaluation units.
- State explicitly what each source does not support, including unseen assets, field false-alarm burden, causal diagnosis, deployment, or safety.
- Block conflicted or unresolved citations, and do not use a verified preprint as the sole support for a safety-related conclusion.
