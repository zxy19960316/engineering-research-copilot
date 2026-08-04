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

Keep hard constraints separate from soft preferences. Record missing information in `open_questions` when it does not block a bounded search. Stop and ask before searching only when a missing answer would materially alter the query or make recommendation eligibility impossible to judge.

## Plan the search

Translate the current brief into queries with distinct purposes and expected evidence roles. Use this exact shape:

```yaml
search_plan:
  round: 1
  brief_version: 1
  branch_id: "branch-a"
  time_boundary: ""
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

Match `brief_version` and `branch_id` to the current brief. State the time, language, and source boundaries actually used. Assign a unique `query_id` within the cycle. Keep query text traceable to the brief and expose exclusions instead of silently filtering results.

Report the searched boundary and its limitations. Never describe bounded results as exhaustive, novelty-complete, or proof that no prior work exists.

## Assemble the pool

Keep discovery hits separate from the candidate pool. Admit a record to `candidate_pool` only after applying [Citation integrity](core-citation-integrity.md). Use this item contract:

```yaml
candidate_pool:
  - candidate_id: "P1"
    verification_status: ""
    recommendation_eligible: false
    evidence_roles: []
    basis_level: "metadata_level"
    verified_record: {}
```

Assign each candidate one stable `candidate_id` within the calibration cycle. Keep the same ID when the record is retained, downgraded, or reconsidered in round two. Never reuse one ID for a different work.

Require each pool item to contain exactly one verified paper record and its current verification state. Deduplicate records before selection. Do not place unresolved, conflicted, not-found, or manual-review records in the recommendation pool. Preserve such discovery outcomes separately as limitations or evidence gaps.

Assemble 15–20 verified, deduplicated candidates for round one when reliable evidence exists. Cover direct-problem, method, transfer or bridge, and counterexample or limitation needs where the evidence permits. Do not create metadata, identifiers, authors, titles, publication states, or evidence roles to reach the target count.

## Select round one

Select eight recommendation-eligible records when the pool and evidence-role coverage support eight. Require every entry in `selected_ids` to resolve to exactly one candidate-pool item and exactly one verified paper record. Reject missing IDs, duplicate IDs, ambiguous resolutions, and blocked verification states.

Build the user-facing static map and equivalent text fallback under [Static paper evidence map](core-paper-map.md). Keep every map claim within its declared metadata-, abstract-, or full-text-level basis.

Use this exact round bundle shape:

```yaml
round_bundle:
  schema_version: "m1.1"
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
  inherited: []
  rejected: []
  reset: []
  added: []
  allocation:
    exploit: 50
    explore: 50
  query_changes: []
```

Record reasons with rejected items. Show inherited, rejected, reset, and newly added constraints before planning the next search branch. Make `allocation` total 100 and treat it as a query-and-candidate budget, not a probability.

Create a new brief version before round two. Match the second-round plan to the new version and retain the same branch only when the rollback rules permit it. Explain each material query change caused by rejection reasons, new constraints, or resets. Do not claim feedback was applied when the new plan is unchanged for no stated reason.

## Select round two

Build a second `RoundBundle` with `round: 2`, the revised brief, the revised search plan, and the verified candidate state used for selection. Keep candidate IDs stable for carried records and assign new IDs only to newly admitted works.

Return five to six recommendation-eligible papers by default when reliable evidence exists. Expand to at most ten only after an explicit user request. Explain which first-round items remain, change status, or leave the selection and tie each change to feedback or newly verified evidence. Preserve missing role coverage and search limits instead of filling slots with weak records.

## Report incomplete evidence

Set the outcome to `evidence_incomplete` whenever the verified pool, selection count, role coverage, source access, or reasoning basis cannot support the requested complete round. Keep `selected_ids` limited to eligible records and leave missing slots unfilled.

End the current attempt in `WAITING_FOR_EVIDENCE_DECISION`. Keep the M1 workflow incomplete, and do not reinterpret the visible gap as successful completion.

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
