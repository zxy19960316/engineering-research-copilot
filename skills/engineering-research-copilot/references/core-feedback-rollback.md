# Feedback, Search History, and Rollback

Use this file whenever the user reacts to papers, changes constraints, rejects a direction, questions a citation, or requests a reset.

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
