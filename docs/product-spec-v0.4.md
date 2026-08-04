# Engineering Research Copilot Product Specification v0.4

## Product outcome

Help engineering master's students and early doctoral researchers move from a vague or cross-disciplinary problem to verified papers, a defensible direction, and an executable research route. Cover mechanical, nuclear, automation, computer, electrical, and adjacent engineering fields without claiming exhaustive domain expertise.

## Priority order

1. Accurate two-round paper matching.
2. Interdisciplinary research-direction confirmation.
3. Evidence-grounded route decisions and minimum decisive tests.
4. Engineering method coaching.
5. Read-only evidence audit and specialist handoff for writing, figures, and data execution.

## Core flow

```text
adaptive research brief
  -> round-one discovery, verification, deduplication, and evidence map
  -> user feedback in chat
  -> visible feedback delta and search-history budget
  -> round-two search or direction reframe
  -> updated map and three direction cards
  -> user direction confirmation
  -> executable experiment/simulation route
  -> method coaching, evidence audit, or specialist handoff
```

## Confirmed policies

| ID | Contract |
|---|---|
| PREPRINT-01 | Verified preprints may support methods and exploration but cannot solely support a main direction or safety-related conclusion. |
| TRANSFER-01 | Target-domain direct method success is not required; similar-domain, mechanism, or data-structure success may support a testable transfer hypothesis. |
| DIRECTION-PORTFOLIO-01 | Return one main direction, one adjacent alternative, one transfer exploration direction, and at most two unranked high-risk ideas. |
| PAPER-PORTFOLIO-01 | Verify and deduplicate 15–20 first-round candidates, show eight, then show five to six after feedback; expand to ten only on request. |
| PAPER-MAP-01 | Use a static evidence map for fast orientation and accept all modifications through ordinary chat. |
| GRAPH-RENDER-01 | Render Mermaid by default, fall back to grouped text, and export static SVG only when explicitly needed. |
| INTAKE-01 | Extract a minimal research brief from natural language and ask at most three missing high-impact questions. |
| DIRECTION-GATE-01 | Mark the recommended direction provisional and require user confirmation before full route generation. |

## Paper-verification contract

- Discovery never implies verification.
- Resolve DOI records through the relevant registration agency and compare title, authors, dates, venue, and work type.
- Use official arXiv or PubMed identifiers when DOI does not exist; state that no DOI is assigned.
- Classify records as `verified_primary`, `verified_registry`, `verified_preprint`, `partial`, `conflicted`, `not_found`, or `manual_needed`.
- Block `conflicted`, `not_found`, and `manual_needed` records from all recommendations.
- Show title, ordered authors, year, venue, canonical identifier, verification status, verification time, evidence role, support, and limitation.

## First-round evidence map

- Build an internal pool of 15–20 verified and deduplicated candidates.
- Show eight papers by default: three direct-problem, two method, two transfer/bridge, and one counter/limitation target when reliable evidence exists.
- Size paper nodes by user-fit score, never by citation count.
- Color by evidence role; use dashed edges for inferred transfer relations.
- Limit each paper to one or two useful edges and two to four clusters.
- Label relations as problem, method, bridge, claim support/tension, or shared data/benchmark.
- Mark every relation as metadata-, abstract-, or full-text-level.
- Place exact citation metadata in a compact table below the map.

## Feedback and history

Classify dissatisfaction before acting:

- Direction accepted, papers rejected: re-search within the direction.
- Papers credible, direction rejected: reframe the problem and start a new direction branch.
- Citation questioned: audit metadata before changing direction.
- Constraints changed: revise the brief and invalidate only affected evidence.
- Papers and direction rejected: start a new branch while retaining only user-confirmed stable constraints.
- Full reset requested: allocate zero semantic influence to the previous branch.

Default exploitation/exploration budgets are 70/30 after positive feedback, 50/50 for mixed feedback, 30/70 when papers are rejected within an accepted direction, 20/80 after direction rejection, and 0/100 after full reset.

Before a new search, show inherited constraints, rejected items and reasons, reset assumptions, new constraints, and the exploration budget.

## Direction decision

Require direct evidence that the target problem and engineering need exist. Do not require an exact target-domain precedent for the chosen method.

Classify method-direction evidence:

- `established-in-target`: direct target or highly equivalent validation exists.
- `transfer-supported`: target problem exists, source-domain success is verified, transfer conditions are mapped, and a decisive test is feasible.
- `mechanism-plausible`: principles or data structure appear compatible but bridge evidence is incomplete.
- `speculative`: mainly creative analogy; keep outside the ranked portfolio.

A `transfer-supported` direction may be the provisional main recommendation with at most medium confidence until its target-domain decisive test succeeds.

Every formal direction includes problem evidence, source-method evidence, transfer compatibility, anti-transfer factors, available resources, uncertainty, a counter/limitation check, and a minimum decisive test with baseline, primary metric, success threshold, stop condition, pivot condition, time, and resources.

## Direction gate and route output

After round two, show the evidence map and three decision cards. Do not produce detailed routes for every candidate. Wait for the user to confirm one direction, then produce:

- falsifiable hypothesis;
- baseline and controls;
- experiment or simulation sequence;
- inputs, outputs, controlled variables, and confounders;
- primary and secondary metrics;
- minimum meaningful improvement;
- uncertainty, sensitivity, and validity checks;
- Go, Stop, and Pivot conditions;
- evidence chain from design through data, analysis, result, and claim.

## Permission budget

- Read only user-provided artifacts by default.
- Use host-provided scholarly/web search when necessary.
- Do not write back, upload research materials, start services, download models, execute arbitrary commands, or connect RRC without explicit authorization.
- Keep manuscript red-team review read-only and hand off specialized writing, figure, or data execution when an appropriate Skill is available.

## v1 size boundary

- One root `SKILL.md`, targeted at 150–250 lines and always below 500.
- One-level reference modules loaded on demand.
- No paper/book corpus, model, database, or interactive front end.
- Evidence corpus target in later milestones: 50–80 curated authoritative, foundational, recent-consensus, and counter/limitation sources.
