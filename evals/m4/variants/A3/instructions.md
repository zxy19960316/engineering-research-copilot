# Frozen Engineering Research Instructions

<!-- source: SKILL.md; source_sha256: 3d53432d11963ee7b7532526b72236ed1a72cfda66c66feafadaa725b73bac44 -->
---
name: engineering-research-copilot
description: "Run evidence-grounded engineering research workflows for mechanical, nuclear, automation, computer, electrical, and interdisciplinary topics. Use when a researcher needs accurate two-round literature matching, verified DOI/author/title metadata, a static paper evidence map, research-direction comparison, transfer-method reasoning, an executable experiment or simulation route, method coaching, data-result-claim auditing, manuscript red-team review, or Chinese requests such as 文献精准匹配、科研选题、交叉学科方向、科研路线、实验方案、仿真方案、方法迁移、证据检查、论文预审和科研辅助。"
---

# Engineering Research Copilot

Help engineering master's students and early doctoral researchers move from a vague or cross-disciplinary problem to verified literature, a defensible direction, and an executable research route. Keep claims proportional to evidence and keep the researcher in control of direction changes.

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
| Find, verify, compare, or re-search papers | [Paper calibration](references/core-paper-calibration.md), [Citation integrity](references/core-citation-integrity.md), [Paper evidence map](references/core-paper-map.md), and [Feedback rollback](references/core-feedback-rollback.md) |
| Confirm or compare research directions | [Direction decision](references/core-direction-decision.md) and, when papers are used, the citation-integrity rules above |
| React to dissatisfaction or changed constraints | Use the feedback-rollback rules above |
| Plan an experiment, simulation, or minimum decisive test | Use the direction-decision rules above; require `user_confirmed` direction status first |
| Check data-result-claim consistency | Perform a read-only claim-evidence audit; distinguish observed data, analysis output, interpretation, and speculation |
| Review writing, figures, or format | Perform a read-only red-team pass, then hand off execution to a dedicated writing, figure, document, or data Skill when available |

Load only the references required for the current route. Do not load every reference by default.

## Calibrate papers in two rounds

Load and apply Paper calibration as the state contract. Apply Citation integrity to candidate admission and recommendation eligibility, Paper evidence map to each round view, and Feedback rollback to the round transition. Keep incomplete evidence visible and stop at the M1 boundary defined in the calibration reference.

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

Mark the system's direction recommendation as `provisional`. Pass every hard gate before scoring. Show the M1 candidate lineage, evidence tier, closed core claims, structured data preconditions, risks, unknowns, and a bounded minimum decisive test for each formal direction.

Do not generate a detailed route until the user explicitly confirms one formal direction ID. Record the exact confirmation message provenance and bind it to the canonical pre-confirmation bundle. On confirmation, set the direction status to `user_confirmed`; only then may the route gate open. Bind any route to the selected direction, confirmation event, confirmed bundle, claims, test metrics, preconditions, and resource limits, then produce:

- a falsifiable hypothesis;
- baseline and controls;
- executable experiment or simulation steps;
- inputs, outputs, controlled variables, and confounders;
- primary and secondary metrics;
- minimum meaningful improvement;
- an evidence chain from design to data, analysis, result, and claim.

If the direction is rejected, use Feedback rollback instead of silently adjusting the old plan.

## Audit evidence read-only

When checking data, conclusions, or a manuscript:

- separate data, analysis, result, interpretation, and claim;
- check leakage, invalid splits, missing controls, unit or scale mismatches, overclaiming, and omitted uncertainty;
- distinguish correlation from causation and simulation verification from validation;
- identify what would falsify each main claim;
- report issues and proposed corrections without modifying source files unless explicitly requested.

## Respect evidence and permission limits

- Use only verified metadata in final citations; never guess identifiers.
- State whether reasoning is metadata-, abstract-, or full-text-level.
- Keep verified preprints out of sole support for main directions and safety-related conclusions.
- Use host-provided search tools; do not require a bundled database or private service.
- Do not start services, download models, upload research materials, execute arbitrary commands, or write back to user files without an explicit request.
- Treat RRC as an optional future backend. Keep the Skill usable without it.

<!-- source: references/core-citation-integrity.md; source_sha256: 2332b60ac90d3f9decf68548f74d661c4ce14974a37d007d3cdad398c4ebb4be -->
# Citation Integrity

Apply this file whenever external literature is discovered, recommended, cited, mapped, or used to justify a direction.

## Separate discovery candidates from verified records

Create a discovery record first. Keep its state exactly `unverified_candidate` until an authoritative source has been checked.

Use this shape for discovery output:

```yaml
discovery_candidate:
  candidate_id: ""
  discovery_state: "unverified_candidate"
  supplied_title: ""
  supplied_authors: []
  supplied_identifier: null
  discovery_source_type: "search_snippet|aggregator|ordinary_web|user_supplied|model_memory"
  discovery_source: ""
```

Preserve supplied strings as unverified observations. Do not repair an identifier, complete an author list, or convert a probable title into a bibliographic fact.

Do not let a search snippet, aggregator match, ordinary web page, user assertion, or model memory set a verified state. Do not place a discovery record directly in a recommendation list or paper map. Promote it to a `VerifiedPaperRecord` only after completing the verification object below.

## Verify against current authoritative sources

Check sources in this order when they apply:

1. Query the DOI registration agency record for a supplied DOI.
2. Query the official repository record and exact version for a supplied repository identifier.
3. Query the official PubMed record for a supplied PMID in biomedical intersections.
4. Cross-check the publisher landing page for title, authors, venue, work type, dates, corrections, and version relationships.
5. Use a structured aggregator only to discover a candidate or resolve ambiguity; never use it as the sole truth source when an authoritative registry or official repository exists.

Perform the authoritative lookup during the current calibration run for every real recommendation. Record every attempted authoritative source, including conflicts, unavailable responses, and not-found results. If a source cannot be checked, record that limitation instead of substituting model memory or an old search snippet.

## Normalize without inventing

- Strip `https://doi.org/`, `http://dx.doi.org/`, and `doi:` from supplied DOI input.
- Trim whitespace and trailing citation punctuation; lowercase the DOI.
- Preserve the supplied DOI body exactly after those normalization steps.
- Never change the DOI body, infer missing characters, or create an identifier from title similarity.
- Never treat an arXiv ID, PMID, ISBN, report number, or publisher URL as a DOI.
- Normalize an official alternate identifier only according to its owning authority; preserve its identifier type and version.
- Set `alternate_id` to `null` when no official alternate identifier is present. Otherwise require an object with exactly two fields: `authority`, containing the nonempty official authority type, and `value`, containing the nonempty authority-normalized identifier value. Reject a bare string, an empty value, a missing field, or any additional field.
- Preserve online-first and issue publication dates separately when both exist.

## Compare metadata

Compare at minimum:

- complete title;
- ordered author list;
- online and issue dates;
- journal, conference, repository, or other venue;
- publication type or work type;
- supplied and authoritative normalized DOI values, official alternate identifiers, and canonical identifiers;
- correction, retraction, and version relationships when available.

Classify a resolving identifier with materially inconsistent DOI, title, or author identity as `conflicted`. Treat two supplied or authoritative records with different normalized DOI values as a decisive identifier conflict when they are presented as the same candidate. Do not choose whichever DOI or version appears plausible, and do not use a weaker key to override that conflict.

Use normalized title plus first author only to find or review candidates when no stronger matching key is available. Require authoritative confirmation before treating that pair as the same work. Never assign a DOI or alternate identifier solely from fuzzy matching.

## Assign one verification state

Assign exactly one state from this closed set:

| State | Meaning | Recommendation eligibility |
|---|---|---|
| `verified_primary` | Registry or official repository and landing metadata agree | Eligible when no blocking reason remains |
| `verified_registry` | Registry metadata agrees; publisher landing page cannot currently be checked | Eligible with the unavailable cross-check disclosed |
| `verified_preprint` | Official preprint ID, exact version, title, and authors agree | Conditionally eligible under the preprint contract |
| `partial` | A record exists but important author, date, venue, or version data is incomplete | Supplemental context only |
| `conflicted` | An identifier resolves to materially different metadata or authoritative sources disagree | Blocked |
| `not_found` | No authoritative record is found within the stated search boundary | Blocked |
| `manual_needed` | Multiple plausible candidates or unresolved identity or version questions remain | Blocked pending human confirmation |

Do not introduce another verification-state label in a real record. Preserve unavailable checks inside `checked_sources` and limitations; do not relabel incomplete verification as success.

Keep verification status separate from recommendation eligibility. A record in `verified_primary`, `verified_registry`, or `verified_preprint` has closed current provenance and identity; it may still be `recommendation_eligible: false` because an explicit scope, role, transfer, safety, or preprint-use restriction blocks this recommendation. Preserve that verified status, record at least one specific `blocking_reasons` entry, and keep the record outside `selected_ids` and paper-map paper nodes. Count such an unselected record toward the deduplicated 15--20 verified-candidate target.

Do not change a verified record to `partial` merely to express recommendation ineligibility. Use `partial` only when current verification or identity is incomplete. Never count `partial`, `conflicted`, `not_found`, or `manual_needed` toward the verified-candidate target, even when their checked-source structure is populated.

## Determine recommendation eligibility

Set `recommendation_eligible: true` only when all of these conditions hold:

- Set `verification.status` to `verified_primary` or `verified_registry`, or to `verified_preprint` under the preprint contract.
- Resolve title and author checks without `conflict`.
- Resolve work type and version identity sufficiently for the intended recommendation.
- Leave `blocking_reasons` empty.
- Complete a current authoritative lookup rather than relying on offline structure, discovery metadata, or model memory.

Set `recommendation_eligible: false` for `partial`. Use a partial record only as clearly labeled supplemental context outside the selected recommendation set, and state the missing verification.

Set `recommendation_eligible: false` for `conflicted`, `not_found`, and `manual_needed`. Exclude all three states from recommendation lists, selected IDs, paper-map nodes, direction support, and safety conclusions.

For a verified status with `recommendation_eligible: false`, require nonempty `blocking_reasons`, at least one valid current checked source with a match and no conflict or not-found result, resolved title and author identity, and a closed `version_relation` other than `unknown`. Treat an empty reason, missing current source, or open identity as invalid. Never select an ineligible record regardless of its verification status.

## Deduplicate deterministically

Apply these keys in order and do not fall back after a stronger key produces a match or mismatch:

1. When both records contain a DOI, compare their normalized DOI values. Treat equal values as a possible duplicate subject to metadata and version checks. Treat different values as a decisive mismatch: stop, retain separate observations, and do not compare official alternate identifiers or title plus first author to merge them.
2. Only when at least one record lacks a DOI, compare exact official alternate identifiers as `(authority, value)` pairs. Validate each non-null `alternate_id` as the closed two-field object before comparison; reject bare strings and incomplete objects instead of coercing them. When both records contain an official alternate identifier, treat equal pairs as a possible duplicate subject to metadata and version checks; treat different pairs, including different `authority` values, as a decisive mismatch and stop without using title plus first author to merge them.
3. Only when at least one record lacks a DOI and at least one record also lacks an official alternate identifier, compare normalized title plus normalized first author for candidate review.

Treat the third key as a review trigger, not as proof of identity. Do not auto-merge title-and-author matches without current authoritative confirmation of `same_work`. When a stronger identifier is later found, restart comparison at the DOI step.

When duplicate DOI or official alternate identifiers carry conflicting title, author, work-type, or version metadata, do not merge them. Set the record to `conflicted` or `manual_needed` as appropriate, retain both source observations, and block recommendation eligibility until the conflict is resolved.

Retain the more complete authoritative metadata only after all decisive identity fields agree. Preserve all checked-source provenance and identifier aliases when consolidating true duplicates; never merge conflicting fields silently.

Compare every pair in each candidate pool, including records that are not selected. Reject compatible records with different `candidate_id` values as `duplicate_candidate_identity`. Reject equal DOI or alternate-ID identities with incompatible normalized title, ordered authors, publication type, or version relation as `candidate_identity_conflict`. Treat a title-plus-first-author match without a decisive identifier as `candidate_identity_manual_review`; never auto-merge it, and block selection when either related record is selected.

Across rounds, require one `candidate_id` to continue identifying the same work. Reject a changed DOI, a changed alternate identifier, or incompatible identity metadata as `stable_candidate_identity_changed`. Permit a DOI to be added only when the same normalized alternate identifier is present in both rounds. Without that stable alternate identifier, report `stable_candidate_identity_unresolved` instead of inferring continuity from title and first author.

## Resolve version relationships

Assign exactly one `version_relation` from `same_work`, `preprint_of`, `distinct`, or `unknown`.

- For an ordinary single paper, set `same_work` when the discovery candidate and current authoritative record agree and no separate preprint, edition, correction, or other version relationship is asserted. Do not use `unknown` merely because the paper has only one identified version.
- For `same_work`, consolidate duplicate observations only after authoritative metadata and work type agree.
- For `preprint_of`, retain separate preprint and published records and link them without treating the identifiers as interchangeable.
- For `distinct`, retain separate records even when titles are similar.
- For `unknown`, require a genuine unresolved identity or version ambiguity. Do not merge the ambiguous record, and use `manual_needed` only when that ambiguity affects identity or recommendation eligibility.
- When work type conflicts or the preprint-to-publication relation is unresolved, keep the records separate and blocked until an authoritative source or human confirmation resolves the relation.

## Produce a verified paper record

Require this verification object and all of its fields:

```yaml
verification:
  status: "verified_primary"
  checked_sources:
    - source_type: "doi_registry"
      canonical_record: ""
      checked_at: "ISO-8601"
      result: "match"
  title_match: "exact|normalized|conflict|not_checked"
  author_match: "exact|compatible|conflict|not_checked"
  version_relation: "same_work|preprint_of|distinct|unknown"
  recommendation_eligible: true
  blocking_reasons: []
```

Use only `doi_registry`, `official_repository`, `pubmed`, and `publisher_landing` for `source_type`. Use only `match`, `conflict`, `not_found`, and `unavailable` for `result`. Record a timezone-aware ISO-8601 `checked_at` value and a source-resolvable `canonical_record` for every check. Do not fabricate either value when a check did not occur.

Use this enclosing `VerifiedPaperRecord` shape. Leave absent identifiers null; populate every bibliographic value only from checked metadata:

```yaml
verified_paper_record:
  paper_id: ""
  title: ""
  authors: []
  year_online: null
  year_issue: null
  venue: ""
  publication_type: ""
  doi: null
  canonical_url: ""
  alternate_id: null
  verification: {}
  evidence_role: ""
  supports: ""
  does_not_support: ""
  basis_level: "metadata_level|abstract_level|fulltext_level"
```

Keep `alternate_id` exactly `null` when absent. When present, replace `null` with an object containing only the required nonempty `authority` and `value` fields defined above. Do not serialize it as a bare identifier string or accept a partially populated object.

Mirror `verification.status` and `verification.recommendation_eligible` into a calibration candidate's summary fields without changing their values. Reject a candidate when the summary and nested verification object disagree.

Show the exact checked title, authors, year, venue, clickable canonical record, verification status, verification time, evidence role, support, limitation, and reasoning basis to the user.

## State the real-evidence limitation

Treat offline schema, fixture, and structural validation as contract checks only. They can verify required fields, closed states, deduplication behavior, and eligibility gates, but they cannot prove that a DOI or other citation identifier exists, that metadata is accurate, or that live scholarly verification succeeded.

Require a current authoritative lookup and recorded provenance for every real recommendation. If the lookup cannot be completed, keep the record partial or blocked and report `evidence_incomplete`; never promote an offline-valid object to a real verified citation.

## Enforce hard gates

- Require zero invented DOI, author, title, publication state, URL, or identifier fields.
- Block recommendations whose verification provenance is absent, stale for the current run, internally inconsistent, or based only on discovery sources.
- Do not claim novelty, priority, or absence of research without an explicit search boundary.
- Do not use citation count as a truth, quality, or applicability verdict.
- Label metadata-, abstract-, and full-text-level reasoning explicitly.
- Downgrade a conclusion when the evidence is partial, preprint-only, abstract-only, or transfer-only.

<!-- source: references/core-direction-decision.md; source_sha256: 206c4f8d0f8c639bdd74e62845bbf768b6f096c2ce4cf5e996502e4bd34f95de -->
# Direction Decision and Route Gate

Use this file only after one paper-calibration branch reaches `M1_COMPLETE`. Convert that branch into an auditable direction portfolio, stop when direction evidence is incomplete, and open detailed route planning only after explicit user confirmation.

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
