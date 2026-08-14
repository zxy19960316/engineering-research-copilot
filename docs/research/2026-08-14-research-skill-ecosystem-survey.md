# Research Skill Ecosystem Survey: from one Copilot Skill to a bounded research plugin

**Date:** 2026-08-14 (Asia/Shanghai)
**Repository baseline inspected:** `c21c24e079631d2396a3989045c9f0945e17c24e`
**Mode:** read-only market and architecture survey. No third-party Skill was installed; no experiment, download corpus, upload, publication, or external communication was performed. This report is the only file written by this survey.

## 1. Executive recommendation

Turn Engineering Research Copilot into a **plugin that contains a thin umbrella router, eight focused first-release Skills, shared versioned contracts, and deterministic validators**. Keep the current accepted single-Skill artifacts intact. Introduce the cluster as a successor version instead of silently rewriting historical evidence or the terminal M4.2 record.

The first release should remain instructions-first and offline-capable:

- Use `.codex-plugin/plugin.json` as the installation boundary and `skills/` as the capability boundary.
- Keep `engineering-research-copilot` as the compatibility/intake router. It selects one owning Skill and one next safe step; it does not run the whole pipeline automatically.
- Add focused Skills for direction/evidence, literature/evidence, method/transfer, data comparison, adversarial evidence audit, scientific figures, manuscript work, and independent cross-review.
- Put provenance, evidence level, readiness, permissions, review independence, graph semantics, and hand-off fields into shared machine-checkable contracts. A hand-off transfers context, never authority.
- Preserve discovery and verification as separate states even where they initially share one Skill folder. If activation tests show trigger overlap, split them without changing the shared contracts.
- Make a canonical evidence-graph JSON the source of truth. Render a deterministic static view by default and an optional self-contained interactive view only after scoped file-write permission. A later MCP app can provide a full-screen graph, but it is not needed for the foundation release.
- Build the scientific-figure asset pack from original or clearly licensed templates and synthetic fixtures. Store observations and source locators for published examples; do not copy journal figures into the distributable package merely because a paper is highly cited.
- Keep audits read-only. File write, network search, download, upload, dependency installation, experiment, simulation, training, external communication, and publication remain separate scoped grants.

This is deliberately smaller than a “research operating system.” It covers the user’s requested flow while keeping triggers, evidence semantics, and permissions testable.

## 2. What is official, and what is only market convention

The distinction matters because marketplace patterns are not security or compatibility guarantees.

### 2.1 First-party OpenAI architecture facts

OpenAI’s current documentation describes a plugin as a package that can contain Skills and, when needed, MCP tools and an app UI. It recommends starting with the smallest useful package: use a Skill for repeatable instructions and outputs, MCP for controlled live tools/authenticated actions, and UI only where interaction materially improves the workflow ([Plugins](https://developers.openai.com/plugins/concepts/plugins), [Build plugins](https://developers.openai.com/plugins/build/plugins)).

For Skills, the model first sees the `name` and `description`, then loads the full instructions when the request matches or the Skill is invoked directly. Trigger quality therefore depends heavily on a narrow description with positive and negative conditions ([Skills](https://developers.openai.com/plugins/concepts/skills)). OpenAI’s build guidance says to split Skills when triggers, inputs, or success criteria differ; keep detailed references and deterministic scripts behind concise entry instructions; and test direct, indirect, incomplete, negative, and edge prompts ([Build Skills](https://developers.openai.com/plugins/build/skills)).

Official security guidance emphasizes least privilege, explicit consent, minimal data exposure, and confirmation before irreversible or open-world actions ([Security and privacy](https://developers.openai.com/plugins/guides/security-privacy)). MCP tools should accurately describe read-only, open-world, and destructive behavior, and an app must not hide side effects behind ordinary-looking interactions ([App guidelines](https://developers.openai.com/plugins/app-guidelines)). For the requested graph, OpenAI’s UI guidance treats full-screen surfaces as appropriate for interactive diagrams and requires accessible contrast, alt text, and responsive layout ([UI guidelines](https://developers.openai.com/plugins/concepts/ui-guidelines)).

Consequences for this project:

1. `.codex-plugin/plugin.json` is the plugin manifest; a repository-specific `manifest.yaml` inside a Skill is not a substitute for it.
2. A broad router is useful only as an intake fallback. Direct requests should activate a focused owning Skill.
3. “Internal Skill” flags seen in third-party repositories are not documented as an OpenAI security or visibility boundary. Do not rely on them to protect privileged actions.
4. Shared contracts are ordinary bundled resources, not a special official “shared Skill” primitive. Every consuming `SKILL.md` must link the needed contract explicitly.
5. MCP and UI are optional later layers. They must not be introduced simply to make the package look more complete.

### 2.2 Marketplace conventions and their evidentiary value

[skills.sh](https://skills.sh/) describes an open ecosystem and exposes install counts and a leaderboard. The survey ran discovery-only searches with `npx -y skills find`; it never ran an install command. Queries included:

```text
scientific visualization plotting
research direction hypothesis evaluation
literature search citation verification
academic writing polishing manuscript
peer review adversarial evidence audit
scientific method transfer research design
data comparison statistical analysis
interactive knowledge graph evidence map
regression Bland Altman agreement plot
```

On 2026-08-14, examples of CLI-reported install signals included `nature-polishing` about 8.5K, `nature-statistics` about 3.9K, one literature-search Skill about 2.2K, and several K-Dense literature/peer-review/statistics Skills around 1.3K. The leaderboard also showed unusually large signals for RigorPilot’s `paper-context-resolver` and `ai-research-explore`, while the corresponding repository had only 483 GitHub stars. These numbers establish discoverability and adoption only. They do **not** establish scientific correctness, license cleanliness, security, maintenance quality, or fit for this project.

GitHub stars below are likewise dated popularity signals, not evaluation scores. Architectural recommendations come from inspected source, not rankings.

## 3. Current Copilot baseline: strengths to preserve and gaps to close

At the inspected base commit, the existing root Skill already has unusually strong research-governance semantics:

- discovery candidates are kept separate from verified source identity;
- metadata-, abstract-, and full-text-level reasoning are labeled;
- the direction portfolio distinguishes a provisional main direction, an adjacent alternative, and a transfer exploration;
- high-risk ideas require a minimum decisive falsification test;
- route generation requires direction confirmation and does not authorize execution;
- claim audit and red-team review preserve uncertainty rather than inventing support;
- the paper map already has typed nodes/edges, verification styling, transfer hypotheses, and a structured representation with static fallback.

The successor work should therefore **extend the contract and renderer, not replace the epistemic model**.

The base commit’s main gaps for the new request are:

- one broad Skill owns too many distinct triggers and success criteria;
- it is not packaged as a multi-Skill OpenAI plugin;
- the accepted map contract is static-only and cannot supply the requested graph exploration;
- there is no shared hand-off envelope that guarantees evidence IDs, readiness, and permissions survive a Skill transition;
- scientific plotting is a workflow branch, not yet a reusable recipe-and-validation subsystem;
- cross-review can be strengthened so raw independent reports and disagreements remain first-class artifacts before synthesis;
- a future public distribution needs an explicit repository license and an asset-level provenance/license ledger. Absence of a repository license should be treated as “all rights reserved,” not as permission to reuse.

The historical accepted paper map should remain immutable. The interactive direction graph should receive a new schema/version and an explicit successor decision that resets the old static-only preference for this new artifact only.

## 4. Findings from representative source inspection

### 4.1 Strongest patterns to adopt

**Typed evidence graphs and fail-closed validation.** GitHub’s MIT-licensed [`build-evidence-map`](https://github.com/github/awesome-copilot/blob/main/skills/build-evidence-map/SKILL.md) uses a canonical graph, typed positions/claims/evidence/unknowns, supports/contradicts/qualifies/missing relations, exact locators, preserved counterevidence, and an offline validator. This is the closest public analogue to the requested graph. Its crucial lesson is that topology is not scientific confidence: node degree and edge count must not silently become evidence strength.

**Few entry points with narrow capabilities behind them.** The Apache-2.0 [RW Research Skill](https://github.com/ozrwayne/rw-research-skill) has an actual [OpenAI plugin manifest](https://github.com/ozrwayne/rw-research-skill/blob/main/.codex-plugin/plugin.json), a compact intake router, and focused evidence-map, claim-audit, referee, literature, data, and design Skills. Its [`rw-evidence-map`](https://github.com/ozrwayne/rw-research-skill/blob/main/skills/rw-evidence-map/SKILL.md) fixes node/relation definitions before rendering and keeps effect direction, size, and uncertainty separate. Adopt the “one bottleneck, one owner, one next step” behavior. Rewrite its internal/public distinction as trigger policy rather than trusting nonstandard metadata.

**Scientific-object schemas and deterministic checks.** The MIT-licensed [K-Dense scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills) provides detailed hypothesis, peer-review, statistical-analysis, and visualization packages. Its [`hypothesis-generation`](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/skills/hypothesis-generation/SKILL.md) distinguishes hypotheses, rivals, predictions, operationalization, and falsification controls; [`peer-review`](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/skills/peer-review/SKILL.md) separates claims, methods, statistics, reproducibility, ethics, and figures; and [`scientific-visualization`](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/skills/scientific-visualization/SKILL.md) separates static and interactive outputs, provenance, accessibility, and visual QA. Adopt the typed objects and local validators. Avoid its hundred-plus-Skill breadth and any workflow that installs dependencies or invokes external generators without a separate grant.

**Progressive disclosure and backend gates.** The locally installed `nature-*` bundle and its Apache-2.0 upstream [nature-skills](https://github.com/Yuan1z0825/nature-skills) use concise `SKILL.md` routers, small manifest-defined axes, always-loaded core rules, and on-demand references. `nature-figure` requires an explicit Python-or-R choice and separates evidence logic, export, and QA; `nature-reviewer` returns multiple reports plus synthesis; `nature-writing` and `nature-polishing` separate drafting from surface revision. Adopt the progressive loading and backend choice. Treat the per-Skill `manifest.yaml` as a local convention that must be validated by our own tests, not as an OpenAI-standard manifest.

**Independent review before repair.** The MIT-licensed [`adversarial-review`](https://github.com/VincenzoImp/academic-research-skills/blob/main/skills/adversarial-review/SKILL.md) keeps review lanes separate and follows “review, never fix” before synthesis. This matches the user’s requirement better than systems that average reviewer scores. Its default report writing and repository scaffold coupling must be removed; audit output stays in the conversation unless a path-specific write is authorized.

**Source/target structure mapping for transfer.** The MIT-licensed [`method-transfer-engine`](https://github.com/Data-Wise/claude-plugins/blob/main/statistical-research/skills/research/method-transfer-engine/SKILL.md) maps source assumptions, target objects, preserved properties, adaptations, and verification. The structure is useful, but generic feasibility scores and weak citation gates are not. Clean-room rewrite it as a transfer hypothesis with anti-transfer factors and a minimum decisive target-domain test.

**Bounded exploration authorization.** MIT-licensed [RigorPilot-Skills](https://github.com/lllllllama/RigorPilot-Skills) sharply separates candidate exploration from reproduction and execution. [`ai-research-explore`](https://github.com/lllllllama/RigorPilot-Skills/blob/main/skills/ai-research-explore/SKILL.md) requires a durable current-research anchor, explicit exploration authorization, frozen benchmark/evaluation/budget, and stops at checkpoints; [`paper-context-resolver`](https://github.com/lllllllama/RigorPilot-Skills/blob/main/skills/paper-context-resolver/SKILL.md) answers only a narrow reproduction-critical gap. Adopt the lane and checkpoint discipline. Do not inherit its deep-learning-specific artifacts or automatic write locations.

### 4.2 Patterns to avoid or rewrite

**Do not equate high citation, high install count, or graph centrality with quality.** Highly cited papers are useful discovery anchors for a plotting taxonomy, but age, field size, and social visibility confound the signal. Use citation counts only to prioritize manual inspection. Evidence quality must come from identity/content verification, study design, relevance, uncertainty, and directness.

**Do not copy paper figures into an asset pack by default.** Repository licenses do not grant rights to third-party figures bundled inside them, and article access does not imply redistribution rights. Published exemplars should be stored as bibliographic records, figure locators, design observations, and license status. Only original, synthetic, public-domain, or clearly licensed assets may enter the distributable plugin.

**Do not auto-install, download, write, or upload.** The MIT-licensed [Galaxy-Dawn/claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar) contains useful result-analysis and publication-chart decomposition, but its plotting workflow can install missing tooling, and its ideation workflow can write to Zotero or attach PDFs. Those behaviors conflict with this project’s permission model. Likewise, broad literature Skills that invoke external providers or create output directories automatically are not safe defaults.

**Do not invent placeholder citations.** The unlicensed [lingzhi227/agent-research-skills](https://github.com/lingzhi227/agent-research-skills) is popular in skills.sh results but contains hard-coded paths, post-install behavior, broad triggers, and a citation “fix” pattern that can create placeholder bibliography entries. None of those patterns is acceptable. Because the repository has no detected license, no text, code, template, or asset should be copied.

**Do not collapse reviewers into a score average or editorial verdict.** Several market Skills simulate personas and then average scores or emit accept/reject decisions. That destroys the disagreement the user explicitly wants preserved. The plugin may synthesize issue clusters only after immutable raw reports exist, and substantive changes remain an author decision.

**Do not bake journal specifications in as timeless constants.** The MIT-licensed [wentorai/research-plugins](https://github.com/wentorai/research-plugins) has a useful visualization taxonomy and separate static/interactive paths, but its large nested routers and hard-coded “typical journal” defaults are too broad and can drift. Stable figure principles belong in the Skill; live journal specifications must be verified from the current primary author guidelines when submission formatting is requested.

**Do not reuse unlicensed content.** The unlicensed [jurgendn/agent-skills](https://github.com/jurgendn/agent-skills) offers valuable conceptual patterns—timeline-aware direction mapping, structural cross-domain analogy, triangulation, and cheapest falsifying tests—but they are observation inputs only. Any implementation must be a clean-room rewrite grounded in this project’s own contracts.

## 5. Implementable first-release plugin topology

The most bounded migration is **eight focused Skills plus the existing umbrella router**:

```text
.codex-plugin/plugin.json
skills/
  engineering-research-copilot/      # compatibility and ambiguous-intake router
  research-direction-evidence/       # claims, three-way direction portfolio, graph
  research-literature-evidence/      # discovery and verification as isolated modes
  research-method-transfer/          # method design and transfer as isolated modes
  research-data-comparison/          # descriptive/comparative analysis, no invented data
  research-evidence-adversary/       # claim-evidence and counterevidence audit
  research-figure-workflow/          # static/interactive scientific figures and QA
  research-manuscript/               # claim-ledger-led drafting or polishing modes
  research-cross-review/             # independent reports, disagreements, author decision
shared/
  references/                        # normative cross-Skill protocols
  schemas/                           # versioned JSON Schemas
  figure-recipes/                    # original templates and synthetic fixtures only
scripts/                             # deterministic offline validators/renderers
tests/                               # activation, contract, hand-off, permission, render evals
```

This grouping is a migration choice, not a claim that discovery and verification are the same task. Three paired Skills need hard internal mode boundaries:

| First-release Skill | Mode A | Mode B | Mandatory split trigger |
|---|---|---|---|
| `research-literature-evidence` | discover candidate records | verify identity and inspect content | either mode activates incorrectly on more than the allowed negative-test threshold, or needs different tool permissions |
| `research-method-transfer` | design a target-domain method | assess transfer from source to target | transfer reasoning repeatedly leaks into an unverified method recommendation |
| `research-manuscript` | draft from a claim ledger | polish existing prose without adding claims | polishing adds new claims/citations or drafting triggers on simple style edits |

If a split trigger fires, create `literature-discovery`/`source-verification`, `method-design`/`transfer-assessment`, or `manuscript-writing`/`academic-polishing`. The shared schemas make this a packaging change rather than a semantic migration.

### 5.1 Trigger and success boundaries

| Owning Skill | Positive trigger | Negative trigger / hand-off | Success condition |
|---|---|---|---|
| umbrella router | input is ambiguous among idea, literature, plan, results, outline, draft, or reviewer comments | a focused goal is already clear | classify input, display inherited/rejected/reset/new constraints, choose one owner and one next step |
| direction/evidence | compare main, adjacent, and transfer directions; investigate claims; build direction graph | user already confirmed a direction and asks only for implementation | formal portfolio, graph, high-risk falsifier, readiness state; no full route before confirmation |
| literature/evidence | search for candidates or verify a citation/content claim | prose drafting, method execution | separate discovery register and verification register; unresolved conflicts blocked |
| method/transfer | design a method or assess cross-domain transfer | run experiment/simulation/training | assumptions, alternatives, anti-transfer map, minimum decisive test, route readiness; no execution |
| data comparison | compare supplied data/results with suitable descriptive or inferential methods | fabricate missing values or generalize beyond data | reproducible comparison specification and bounded findings with uncertainty |
| evidence adversary | stress-test claims, evidence chains, missing counterevidence, or contradictions | silently repair manuscript/data | read-only finding ledger with severity, confidence, locator, and cheapest discriminating test |
| figure workflow | select, generate, revise, or audit a scientific plot | dashboard/product UI, or analysis without plotting | validated figure contract, accessible render/export plan, provenance manifest; generation only with write permission |
| manuscript | draft or polish a manuscript artifact | create unsupported claims/citations, or answer reviewer comments as the reviewer | claim-ledger-aligned text; additions and evidence gaps explicit |
| cross-review | independent pre-submission or artifact review | author rebuttal or automatic substantive rewrite | raw independent reports, disagreement register, synthesis, and separate author-decision ledger |

The root router should never be invoked simply because the package exists. Focused descriptions should state both “use when” and “do not use when,” and direct invocation must remain possible.

## 6. Shared contracts: the cluster’s real integration layer

Every artifact should carry `schema_version`, `case_id`, `artifact_id`, `producer_skill`, `created_at`, input anchors/hashes where available, and `supersedes`. The following contracts are sufficient for the first release.

### 6.1 `ResearchMaterialEnvelope`

- `material_class`: `vague_idea | literature | research_plan | results | outline | draft | reviewer_comments`
- `origin`: user-provided path/text, verified public source, or generated working artifact
- `sensitivity` and redaction constraints
- `requested_goal`
- inherited, rejected, reset, and newly added constraints
- `permission_ledger_ref`

This lets the user enter anywhere without pretending all starting materials have equal evidentiary status.

### 6.2 `EvidenceRecord`

Keep four axes orthogonal:

1. **Discovery state:** candidate pointer vs verified identity.
2. **Source class:** user material, publisher record, repository/data record, preprint, secondary synthesis, or other.
3. **Inspection basis:** metadata, abstract, full text with locator, user-supplied full artifact/data, or uninspected.
4. **Claim relation:** supports, contradicts, qualifies, contextualizes, non-comparable, or unknown.

Required fields include title/identifier only when actually resolved, source URL/path, exact locator, inspection timestamp, conflict state, verification method, and recommendation eligibility. “User material” is not automatically above full text; it is first-party evidence for what the user supplied, not independent validation of its interpretation or generalizability.

### 6.3 `ClaimEvidenceLedger`

For every claim record:

- exact claim and scope;
- claim type: observation, method fact, comparison, causal claim, interpretation, forecast, or transfer hypothesis;
- supporting, contradicting, and qualifying evidence IDs;
- evidence basis used;
- inference steps and uncertainty;
- falsifier or decisive discriminating test;
- state: `supported | qualified | disputed | unsupported | unassessable`.

Writing and plotting must consume this ledger. They cannot create citations, results, or numerical conclusions that are absent from it.

### 6.4 `DirectionPortfolio`

- exactly one `provisional_main` when a main direction is supportable;
- one `adjacent_alternative` and one `transfer_exploration` where evidence permits;
- up to two unranked high-risk ideas;
- hard-gate results, assumptions, disqualifiers, and minimum decisive tests;
- `readiness`: `concept_sketch | route_preparation | executable_route`;
- explicit direction-confirmation record when present;
- route artifact reference, which remains null until requested.

`executable_route` means “specific enough to be executed after separate authorization.” It does not set experiment, simulation, training, file-write, or external-action permission.

### 6.5 `EvidenceGraph`

- node types: direction, claim, evidence, method, dataset/result, constraint, unknown;
- edge types: supports, contradicts, qualifies, depends-on, same-problem, shared-method, transfer-bridge, non-comparable, unresolved;
- exact evidence/source locator on evidence-bearing nodes or edges;
- `display_weight` and its reason, separate from evidence quality;
- ordinal `relation_strength` with an explicit rationale, separate from edge count;
- evidence-basis and verification styling fields;
- static and interactive renderer versions.

### 6.6 `PermissionLedger`

Use separate, scoped grants rather than one broad “approved” flag:

```text
local_read
local_write(path/scope)
network_search(domain/scope)
download(source/destination)
upload(destination/material)
dependency_install(environment/package)
experiment(scope/budget)
simulation(scope/budget)
training(scope/budget)
external_communication(recipient/channel)
publication(destination/artifact)
```

Default every field except in-scope read to denied/unset. A Skill may narrow a grant but never broaden or inherit one implicitly.

### 6.7 `ReviewPacket` and `AuthorDecisionLedger`

Freeze a shared input packet hash. Produce independent first-pass reports without exposing one reviewer’s conclusions to the others. Keep the raw reports immutable; record agreement and disagreement separately; then synthesize issues without averaging away minority objections. The author records each substantive proposal as accepted, rejected, deferred, or needs-evidence, with a reason. Review does not edit the source artifact by default.

### 6.8 `HandoffEnvelope`

Every hand-off must state:

- source and target Skill;
- input artifact IDs, paths/URLs, hashes, and source anchors;
- completed checks and unresolved conflicts;
- evidence and readiness states;
- active permission ledger and explicitly allowed next actions;
- blockers and return conditions;
- human confirmation provenance where required.

The receiver must reject a hand-off with missing identity, ambiguous permissions, unsupported readiness escalation, or broken hashes. No hand-off grants execution merely because a route exists.

## 7. Interactive direction graph design

The requested visual weighting is useful, but it needs a semantic guardrail. Use **display prominence for decision relevance**, not for truth.

### 7.1 Canonical semantics

- Make graph JSON canonical. Mermaid/SVG and interactive HTML/UI are renderings, not separate evidence stores.
- Compute node area from declared user-fit and decision relevance, with a capped, documented mapping. Show the value and rationale on click.
- Encode evidence quality through border/badge/pattern and evidence basis through an explicit label. Never encode quality through node size alone.
- Encode relation type by color/shape and relation strength by a small ordinal width scale. Dashed edges mean inferred or transfer-hypothesis relations.
- Preserve contradictions, non-comparability, unknowns, and rejected directions. Do not delete them when the graph is refreshed.
- Require a text/table fallback with the same nodes, edges, and locators.

### 7.2 Useful interactions

- filter by main/adjacent/transfer position;
- filter by relation type and verification state;
- toggle metadata, abstract, full-text, and user-material bases;
- expand/collapse clusters without deleting hidden evidence;
- click a node/edge to show source, exact locator, inspection basis, claim relation, caveat, and verification date;
- highlight shortest evidence paths and contradiction paths without treating path length as causality;
- compare graph versions and show added, changed, rejected, and unresolved items;
- export the visible view plus the complete canonical JSON and a static accessibility fallback.

### 7.3 Delivery levels

1. **Foundation:** deterministic static Mermaid/SVG from canonical JSON; no new runtime.
2. **Local interactive artifact:** self-contained HTML generated only after scoped write permission; no service, telemetry, or network dependency.
3. **Optional plugin UI:** a read-only MCP/UI surface for large graphs when navigation materially benefits; use full-screen layout, accessible contrast, keyboard navigation, alt text, and explicit tool annotations.

The accepted historical static map should not be mutated to simulate this feature. Create a versioned successor graph and test semantic parity between renderers.

## 8. Scientific-figure Skill and asset-pack architecture

The plotting subsystem should separate **scientific validity**, **visual encoding**, and **publication export**.

### 8.1 Asset policy

Maintain two different collections:

- `figure-pattern-index`: bibliographic record, DOI/URL, journal, figure locator, chart family, observed design pattern, why it is useful, access/license status, and inspection basis. It may point to high-impact or highly cited examples but does not redistribute the image.
- `figure-recipes`: original code/templates, synthetic input fixtures, expected outputs, validation rules, and an asset-level license/provenance ledger.

Do not treat “available on arXiv,” “visible on Nature/Science,” or “inside an Apache/MIT repository” as permission to redistribute a third-party figure. If an exemplar’s license is unclear, store only a citation and design observation.

### 8.2 Initial recipe taxonomy

Prioritize reusable scientific questions rather than journal aesthetics:

- comparison: paired/unpaired groups, repeated measures, distributions, estimation plots;
- association: regression, nonlinear fit, residuals, uncertainty, influence diagnostics;
- agreement: Bland–Altman and method-comparison variants;
- prediction: calibration, discrimination, decision curves, confusion/error structure;
- robustness: ablation, sensitivity, subgroup/heterogeneity, uncertainty decomposition;
- sequence: time series, trajectories, event-aligned/repeated observations;
- synthesis: forest/meta-analysis, heatmaps, matrices, network/evidence graphs;
- image/multimodal: panels with scale, registration, annotations, and source linkage.

Each recipe must state valid use, invalid inference, input schema, replicate/unit-of-analysis assumptions, required uncertainty/statistics, missing-data behavior, accessibility checks, Python/R implementation boundary, export formats, and a synthetic gold fixture.

### 8.3 Workflow

```text
claim or figure conclusion
→ evidence/data and unit-of-analysis audit
→ chart-family decision
→ statistical contract
→ explicit Python/R backend choice
→ draft render
→ perceptual, accessibility, and deception checks
→ export at final physical size
→ visual inspection of rendered outputs
→ provenance and source-data manifest
```

Static SVG/PDF/TIFF/PNG and optional interactive HTML must use the same transformed data and semantic specification. Interactive views may add exploration, never a different conclusion. Current journal-specific dimensions, fonts, file types, and limits should be fetched from primary author guidelines only when the user requests submission formatting and grants network access.

## 9. Router and hand-off semantics

The router should ask only the minimum question needed to establish an owner. Its decision order is:

1. What material is present?
2. What outcome is requested?
3. Is the request audit-only, artifact generation, route generation, or execution?
4. What evidence basis is available?
5. What permissions are explicitly granted?

It then returns the material envelope, chosen Skill, missing blockers, and one next action. It must not chain Skills merely because downstream steps are possible.

A safe high-level flow is:

```text
intake
→ direction/evidence
→ literature discovery → identity/content verification
→ user direction confirmation
→ method/transfer readiness
→ route artifact (only if requested)
→ separately authorized analysis/figure/writing work
→ independent cross-review
→ synthesis + author decisions
```

Users may enter at any node. For example, reviewer comments can go directly to cross-review/intake; a supplied result table can go to data comparison; a finished paragraph can go to manuscript polishing. Entering late does not waive upstream evidence checks required by the requested claim.

## 10. Evaluation strategy and rollout gates

### 10.1 Activation and routing

For every Skill, freeze at least:

- direct request;
- indirect natural-language request;
- incomplete request;
- hard negative / near-neighbor request;
- mixed request needing exactly one owner and one hand-off;
- permission-sensitive edge case.

Fail if two Skills claim ownership without a deterministic precedence rule, if the umbrella router activates on every research request, or if a polishing request triggers claim generation.

### 10.2 Contract and evidence invariants

- validate every shared schema offline;
- reject metadata/abstract evidence relabeled as full-text evidence;
- reject invented DOI/title/author/status and conflicted citation identities;
- block a preprint-only main direction or safety conclusion;
- preserve evidence IDs, hashes, locators, contradictions, and unknowns through hand-offs;
- prohibit readiness promotion when its required gates are absent;
- ensure route generation never changes execution permissions.

### 10.3 Graph evaluation

- canonical JSON round-trip and deterministic render hash;
- static/interactive node-edge parity;
- visible legend and accessible text fallback;
- no confidence inferred from citation count, degree, layout proximity, or node area;
- counterevidence and unknown nodes survive filtering/version updates;
- click-through exposes source and exact locator;
- synthetic large-graph case remains navigable and responsive.

### 10.4 Figure evaluation

Use synthetic gold datasets for regression, agreement, calibration, repeated measures, missingness, uncertainty, and subgroup examples. Verify units, replicate handling, intervals, transformations, axis integrity, color accessibility, final-size legibility, and vector/raster export. Render final files and inspect them visually; code completion alone is not a plotting pass.

### 10.5 Independent review evaluation

- reviewers share the same immutable packet but not each other’s first-pass conclusions;
- raw reports remain available after synthesis;
- disagreement is represented explicitly, including minority high-severity concerns;
- synthesis cannot silently turn “unsupported” into “supported”;
- no source edits occur without author selection and write permission.

### 10.6 Permission tests

Use negative fixtures for every action boundary. An audit must remain read-only. Network search cannot imply download; download cannot imply upload; local write cannot imply dependency installation; route generation cannot imply experiment, simulation, or training; reviewer synthesis cannot imply publication or external communication.

### 10.7 Successor rollout

1. **Foundation:** plugin manifest, eight focused Skills, shared contracts, validators, activation and permission tests.
2. **Graph v2:** canonical schema, deterministic static renderer, then self-contained interactive artifact under explicit write permission.
3. **Figure recipes:** original/synthetic asset pack, regression/agreement/comparison starters, render-and-inspect QA.
4. **Workflow forward tests:** fresh-context cases entering from each material type; preserve failed evidence.
5. **Optional integrations:** only after separate authorization, add scholarly MCP providers and a read-only full-screen graph UI.

Because the inspected M4.2 execution record is terminal, none of these phases should be described as continuation or repair of that one-shot run. They require a successor milestone and their own acceptance evidence.

## 11. Adopt, avoid, and clean-room rewrite decisions

| Decision | Items |
|---|---|
| Adopt as architecture | thin fallback router; focused triggers; progressive reference loading; typed evidence/claim/graph objects; exact source locators; falsification controls; deterministic offline validation; independent review lanes; static/interactive parity; explicit backend choice |
| Avoid | mega-pack routing; automatic install/download/write/upload; placeholder citations; hidden side effects; automatic editorial verdicts; reviewer-score averaging; copied paper-figure galleries; hard-coded live journal rules; graph popularity as evidence quality |
| Clean-room rewrite | all external workflow text/templates; method-transfer scoring; evidence-map schema mapped to this project’s formal directions and evidence strata; plotting recipes; review rubric and disagreement ledger; all ideas observed in repositories with missing/unclear licenses |
| Keep external/optional | live database search, publisher/full-text retrieval, Zotero, authenticated connectors, graph UI service, dependency installation, model download, experiment/simulation/training, submission/publication |

## 12. Final comparison table

Popularity signals were verified on 2026-08-14 and may change. Licenses are repository-level SPDX/file observations and do not automatically cover third-party assets bundled inside a repository.

| Source inspected | Actual package/source evidence | License and dated popularity signal | Strong contribution | Main risk or mismatch | Decision for this plugin |
|---|---|---|---|---|---|
| [OpenAI plugin and Skill docs](https://developers.openai.com/plugins/) | official plugin manifest, Skill trigger/loading model, optional MCP/UI, tool annotations, eval guidance | first-party specification; no popularity metric | authoritative packaging, least privilege, focused Skill boundary | does not define our research semantics | follow directly for package, trigger, permission, and UI architecture |
| [GitHub `build-evidence-map`](https://github.com/github/awesome-copilot/blob/main/skills/build-evidence-map/SKILL.md) | actual `SKILL.md`, schema references, offline validator source | MIT; parent repo 37,812 stars | typed graph, exact locators, unknown/counterevidence, fail-closed validator | generic debate/evidence model | clean-room adapt to direction portfolio, evidence strata, and permission contracts |
| [RW Research Skill](https://github.com/ozrwayne/rw-research-skill) | actual `.codex-plugin/plugin.json`; router, evidence-map, claim-audit, referee Skills | Apache-2.0; 168 stars | few public entry points, one-bottleneck routing, typed research artifacts | nonstandard internal-Skill convention; substantial repeated instructions | adopt router/handoff shape; do not use hidden metadata as a boundary |
| [K-Dense scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills) | actual hypothesis, peer-review, statistical-analysis, visualization Skills; scripts/assets/tests; non-OpenAI root `plugin.json` | MIT; 33,492 stars | rich scientific object schemas, falsification, QA, local validators | very broad pack; dependency/network behaviors vary; trigger overlap | borrow taxonomy and test ideas, rewrite narrowly and permission-first |
| [nature-skills](https://github.com/Yuan1z0825/nature-skills) and installed local `nature-*` | actual local `SKILL.md`, per-Skill manifests, references/scripts/assets; upstream source/license | Apache-2.0; 35,172 stars; skills.sh examples up to about 8.5K installs | concise routers, progressive disclosure, backend gate, writing/figure/reviewer specialization | local manifests are convention; third-party figure/code asset provenance may be mixed; review disagreement not first-class | reuse architecture principles; build fresh contracts and a clean asset ledger |
| [wentor research-plugins](https://github.com/wentorai/research-plugins) | actual dataviz router and publication/network/interactive visualization Skills | MIT; 273 stars | broad chart taxonomy; static-vs-interactive selection | oversized nested routers; hard-coded typical journal rules; no OpenAI plugin manifest | use taxonomy as discovery input, not runtime architecture or live policy |
| [co-researcher](https://github.com/poemswe/co-researcher) | actual `.codex-plugin/plugin.json`, 14 Skills, project-manager workflow and eval cases | MIT; 127 stars | direct/negative activation tests, explicit responsibility boundaries | automatic project writes, global routing, score/editorial synthesis | adopt eval matrix; reject implicit writes and verdict aggregation |
| [academic-research-skills](https://github.com/VincenzoImp/academic-research-skills) | actual adversarial-review, contribution, SOTA, writing Skills | MIT; 0 stars | review-before-fix, lane preservation, falsifiability preflight | tied to a specific scaffold and default report writes | adopt independent read-only review semantics, rewrite outputs/contracts |
| [Data-Wise method-transfer-engine](https://github.com/Data-Wise/claude-plugins/blob/main/statistical-research/skills/research/method-transfer-engine/SKILL.md) | actual Claude Skill and plugin manifest | MIT; parent repo 7 stars | source/target assumptions, preserved properties, adaptation and verification | generic feasibility scoring; weak identity/evidence gate; non-OpenAI manifest | clean-room transfer contract with anti-transfer map and decisive test |
| [RigorPilot-Skills](https://github.com/lllllllama/RigorPilot-Skills) | actual exploration and paper-context Skills; no OpenAI plugin manifest found | MIT; 483 stars; skills.sh outlier install signals above 200K for selected Skills | explicit lane authorization, durable anchor, frozen evaluation/budget, narrow helper | deep-learning/repository-specific and write-oriented artifacts | adopt checkpoint and lane semantics; keep execution and writes separate |
| [Galaxy-Dawn/claude-scholar](https://github.com/Galaxy-Dawn/claude-scholar) | actual Claude manifest; publication-chart, results-analysis, ideation, self-review Skills | MIT; 5,112 stars | clear analysis/figure responsibility and useful plotting recipe categories | auto-install and configured external writes; generic review synthesis | use categories only; prohibit implicit dependency and external actions |
| [jurgendn/agent-skills](https://github.com/jurgendn/agent-skills) | actual direction mapper, cross-domain analogy, stress-test, triangulation Skills | no detected repository license; 2 stars | structural transfer gate, temporal direction map, cheapest falsifier, disagreement search | no reuse permission; domain-specific assumptions | observation only; clean-room rewrite, no copied text/code/assets |
| [lingzhi agent-research-skills](https://github.com/lingzhi227/agent-research-skills) | actual literature/citation/figure/review Skills and install-oriented repository structure | no detected repository license; 272 stars; literature-search about 2.2K installs | wide discoverability and workflow coverage | placeholder citation behavior, fixed paths, post-install/dependency actions, score averaging | do not reuse; retain only as negative-pattern evidence |
