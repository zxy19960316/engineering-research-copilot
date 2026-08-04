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
    - query_id: "Q2-R2"
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

State the causal reason. For an added or modified query, set `query_changes.query_id` to the ID of exactly one query in the revised round-two `SearchPlan`. For a removed query, set `query_changes.query_id` to the deleted round-one `SearchPlan` query ID; require that ID to exist in round one and be absent from round two. Do not require a removed query ID to resolve in the round-two plan.

Set `before` to the exact round-one query expression or boundary and `after` to the exact round-two query expression or boundary. For an added query, allow only `before` to be empty. For a removed query, allow only `after` to be empty. For a modified query or boundary, require both values to be non-empty and different. Never leave both values empty for an applied material change. Require every non-empty `after` value to match the revised round-two plan. If feedback does not change a query because an existing query already enforces it, classify that feedback effect as non-material with a visible reason; do not create a false query change.

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
