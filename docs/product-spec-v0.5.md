# Engineering Research Workbench Product Specification v0.5

## Successor scope

Evolve the single Engineering Research Copilot Skill into one installable research-workbench plugin containing focused Skills and a small umbrella router. Treat this as a successor product line from baseline commit `c21c24e079631d2396a3989045c9f0945e17c24e`; do not reopen, retry, repair, or relabel the terminal M4.2 evaluation.

The first successor slice delivers shared governance, direction evidence graphs, and scientific-figure workflow selection. It does not claim completion of the full research lifecycle, empirical validation, experiment execution, model training, publication, or external communication.

## Entry points

Accept any of these user inputs without forcing a fixed starting phase:

- a vague idea or research question;
- one or more papers or citation records;
- a research plan, outline, draft, result table, figure, or dataset description;
- reviewer or editor comments;
- an existing claim-evidence ledger or direction portfolio.

Extract the smallest usable research-case envelope, state what remains unknown, and route only to the Skills required for the requested outcome.

## Plugin and Skill architecture

Package the repository as one plugin with these model-invoked Skills:

1. `engineering-research-copilot`: ambiguous-entry and full-lifecycle router.
2. `research-direction-evidence`: research-claim and direction investigation, readiness, and direction graph.
3. `research-literature-evidence`: discovery, identity verification, and content inspection.
4. `research-method-transfer`: method selection, transfer analysis, and minimum falsification tests.
5. `research-manuscript`: claim-led drafting, restructuring, and polishing.
6. `research-cross-review`: independent reviewer reports, disagreement preservation, and synthesis.
7. `research-data-comparison`: unit-aware, uncertainty-aware comparison of user-provided data and results.
8. `research-evidence-adversary`: adversarial claim-evidence and validity audit.
9. `research-figure-workflow`: figure-purpose selection, recipe planning, rendering handoff, and figure QA.

Keep evidence, permission, readiness, provenance, and handoff rules in one shared contract linked by every focused Skill. Do not copy the shared rules into divergent local variants.

## Evidence model

Keep these dimensions independent:

- `source_class`: external literature, user material, tool observation, or authorized execution result;
- `identity_status`: discovered, identity verified, conflicted, unresolved, or not applicable;
- `content_level`: none, metadata, abstract, inspected full text, or user-provided content;
- `claim_relation`: supports, contradicts, limits, motivates, or does not establish.

Discovery locates candidates; it never verifies identity or content. A metadata match does not establish a paper's substantive claim. User material may be analyzed as supplied but must not be relabeled as externally verified. Every citation, number, experiment, result, and conclusion must remain absent unless supported by inspected evidence or explicitly supplied material.

## Direction portfolio and interactive graph

Compare one provisional main direction, one adjacent alternative, one transfer exploration, and no more than two unranked high-risk ideas. Give every high-risk idea a bounded minimum falsification test.

Project the comparison into a deterministic `direction-graph.v1` artifact:

- place the research problem at the root, then directions, claims/tests/risks, and evidence/data/constraints by hierarchy;
- size node area by relevance to the current research brief, never by citation count, venue prestige, or evidence quality;
- encode evidence level and verification status separately from relevance;
- use relation-specific edges for support, contradiction, tension, transfer, constraint, dependency, derivation, and testing;
- use edge width only for relationship strength and dashed edges for inferred or transfer-hypothesis relations;
- preserve an equivalent text fallback and evidence index;
- support offline pan, zoom, search, filtering, keyboard focus, and node details without a CDN or service.

Interaction changes only the view. Clicking, filtering, or selecting a node does not alter evidence state, confirm a direction, authorize route generation, or authorize execution.

The accepted M1 paper-map contract remains static and unchanged. `direction-graph.v1` is a successor projection for direction work and does not retroactively change M1 evidence.

## Readiness and authority

Return exactly the highest honest readiness level:

- `concept_sketch`: the question, evidence, data, or constraints are too incomplete for route preparation;
- `route_preparation`: a provisional direction and decisive-test requirements can be stated, but a full route is not yet open;
- `executable_route`: the author explicitly confirmed a formal direction and the route can be written.

Route generation is not route execution. Maintain separate authorization entries for file writing, file download, upload, experiment, simulation, training, publication, and external communication. Default audits and reviews to read-only. Scope every authorization to the exact operation, target, and current request.

## Writing and review

Build a claim-evidence ledger before drafting substantive prose. Mark unsupported intended claims as gaps or hypotheses. Never create a citation placeholder that resembles a real reference, or invent data, sample sizes, numerical effects, experimental conditions, outcomes, or conclusions.

For cross-review, preserve each independent reviewer report before synthesis. Show agreements and disagreements explicitly. Treat suggested substantive changes as proposals; the author decides which claims, methods, analyses, and conclusions to change. Writing a revised file requires separate write authorization.

## Scientific-figure asset policy

Build a reusable recipe and workflow asset pack, not a copied-paper image corpus. Store taxonomy, figure-purpose rules, data requirements, statistical assumptions, accessibility checks, export requirements, source links, and licenses. Use paper figures and captions only as inspected design evidence with source anchors; do not redistribute copyrighted panels or full papers.

Cover at least regression diagnostics, agreement and concordance, calibration, uncertainty, distributions, ROC/PR/decision curves, survival, sensitivity and ablation, heatmaps and multivariate views, and network/field/multiphysics figures. Select Python or R before executing a plot workflow, and keep audits read-only until figure-file creation is explicitly requested.

## First-slice acceptance

- The plugin manifest and all nine Skill manifests validate.
- Shared evidence and authorization rules are linked by every focused Skill.
- The graph validator rejects invalid evidence levels, orphan endpoints, cycles, duplicate IDs, unsafe relevance values, and unsupported relations.
- The renderer produces deterministic, self-contained interactive HTML plus an equivalent text fallback.
- Figure recipes have explicit purpose, required data, assumptions, failure modes, minimum panels, accessibility checks, export targets, and source/license provenance.
- Focused tests and the prior M1/M2/M3 contract tests pass without modifying frozen evaluation evidence.
- No external service, paper corpus, copied figure, model, experiment, simulation, training run, upload, publication, or communication is created by acceptance work.
