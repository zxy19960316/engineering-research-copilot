---
name: research-direction-evidence
description: "Investigate research claims and compare a provisional main direction, adjacent alternative, transfer exploration, and high-risk ideas with explicit evidence levels, risks, minimum falsification tests, readiness, and an interactive hierarchical evidence graph. Use for 研究方向、科研选题、主张调查、方向比较、观点图谱、知识图谱、研究空白 or deciding what to study. Do not use to implement or execute an already confirmed route."
---

# Research Direction Evidence

Turn the user's current material into an evidence-bounded direction portfolio. Apply [shared research governance](../engineering-research-copilot/references/core-research-governance.md), the [handoff contract](../engineering-research-copilot/references/core-skill-handoffs.md), the existing [direction decision gate](../engineering-research-copilot/references/core-direction-decision.md), and the [direction graph contract](references/direction-graph-contract.md).

In a generated host projection, read the linked copies inside this Skill. In the canonical source tree, the links resolve to the umbrella sibling. Do not reconstruct or weaken the shared rules.

## Enter from the current material

Accept an idea, question, papers, plan, preliminary result, outline, draft, or review comment. Build or update the research-case envelope. State which constraints are inherited, rejected, reset, and newly added before creating a new search or direction branch.

When external literature is needed, hand off discovery and verification to `$research-literature-evidence`. Do not treat a search result, citation count, venue, or title resemblance as verified support.

## Build claims and directions

Create the claim-evidence ledger before scoring directions. Require direct evidence that the target problem or need exists. Compare exactly:

- one `provisional_main` direction;
- one `adjacent_alternative` that changes one meaningful problem, method, or data axis;
- one `transfer_exploration` that changes at least two axes;
- at most two separately labeled, unranked `high_risk` ideas.

For each formal direction show the target problem, method, data, supporting and counter evidence, evidence basis, assumptions, resource/data preconditions, safety or ethics limits, unknowns, and confidence. Keep transfer claims as hypotheses until a target-domain decisive test supports them.

Give every high-risk idea one minimum falsification test containing the cheapest discriminating observation, baseline, primary metric, numeric or categorical success rule when justified, stop rule, pivot rule, maximum time/resource budget, and the claim it can and cannot establish. When a numeric threshold lacks evidence, mark it `threshold_to_be_set` and state what data must set it; do not invent a number.

## Render the direction graph

Build `direction-graph.v1` from the same portfolio and claim-evidence records. Use the deterministic renderer in `scripts/render_direction_graph.py` when an HTML artifact is explicitly requested.

- Use hierarchy: research problem → directions → claims/tests/risks → evidence/data/constraints.
- Size node area only by relevance to the current research brief.
- Encode evidence basis, verification status, and blocked/hypothesis state separately from size.
- Use edges for support, contradiction, tension, transfer, constraint, dependency, derivation, and testing.
- Preserve the exact text fallback and evidence index.
- Treat pan, zoom, filters, search, and node selection as view operations only.

Do not make graph interaction confirm a direction, change evidence, open the route gate, or authorize execution.

## Return honest readiness

Return `concept_sketch` when evidence, data, or constraints are insufficient. Return `route_preparation` when the portfolio and decisive tests are usable but the author has not confirmed one direction. Return `executable_route` only after exact direction confirmation and adequate preconditions.

Even at `executable_route`, produce a route only when requested. Never execute it without separate authorization for the exact experiment, simulation, training, download, upload, or file writes involved.

## Hand off

Pass stable claim, direction, evidence, risk, test, and constraint IDs. Include the graph source object's hash when a graph artifact is written. Carry counterevidence and blocked directions; never pass only the winner.
