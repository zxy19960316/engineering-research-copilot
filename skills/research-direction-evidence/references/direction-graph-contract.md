# Direction Graph Contract

Use `direction-graph.v1` to visualize a research-direction portfolio after its claims, evidence, risks, tests, data, and constraints have been structured. The graph is a projection of those records, not a new evidence source.

## Use one closed source object

```yaml
schema_version: "direction-graph.v1"
graph_id: ""
title: ""
relevance_basis: "current_brief_fit"
root_id: "P0"
nodes: []
edges: []
```

Every node contains exactly:

```yaml
id: ""
node_type: "research_problem|direction|claim|evidence|user_material|risk|unknown|minimum_test|constraint|data"
portfolio_role: "root_problem|provisional_main|adjacent_alternative|transfer_exploration|high_risk|not_applicable"
label: ""
summary: ""
parent_id: null
relevance: 0.0
evidence_basis: "user_material|metadata_level|abstract_level|fulltext_level|analysis_only|not_applicable"
verification_status: "user_provided|verified_identity|derived|unverified|conflicted|not_applicable"
status: "admissible|hypothesis|unresolved|blocked|rejected"
source_refs: []
details: []
```

Every edge contains exactly:

```yaml
id: ""
source: ""
target: ""
relation: "contains|supports|contradicts|tensions|transfers|constrains|tests|depends_on|derives_from|uses_data"
strength: 0.0
basis: "explicit|inferred|transfer_hypothesis"
evidence_basis: "user_material|metadata_level|abstract_level|fulltext_level|analysis_only|not_applicable"
label: ""
```

Use `parent_id` only for deterministic layout hierarchy. Use an edge for every scientific or decision relation; do not infer support from parenthood.

## Encode relevance independently

Set `relevance_basis` exactly to `current_brief_fit`. Use a number from zero through one for each node. Size rendered node area, not radius, linearly from that relevance. Never substitute citation count, venue prestige, general popularity, evidence quality, confidence, or direction score.

Encode evidence basis, verification status, and claim status with separate visual channels and visible labels. A large node can remain unverified, hypothetical, or blocked. A full-text evidence node can remain small when it is peripheral to the current brief.

## Validate structure and evidence

- Require one `research_problem` root whose ID equals `root_id`, whose `parent_id` is null, and whose role is `root_problem`.
- Require exactly one direction for each of `provisional_main`, `adjacent_alternative`, and `transfer_exploration`; permit no more than two `high_risk` directions. Give every other node `not_applicable`.
- Require every other node to have one existing parent and a parent chain ending at the root.
- Reject duplicate IDs, hierarchy cycles, orphan endpoints, self-edges, unsupported fields, Boolean relevance/strength values, and values outside zero through one.
- Require an external `evidence` node at metadata, abstract, or full-text level to use `verified_identity` and at least one source reference.
- Block conflicted evidence from `admissible` status.
- Keep inferred and transfer-hypothesis edges visually dashed.
- Treat `strength` only as relationship strength in this graph.

## Render one source of truth

Generate the interactive HTML and text fallback from the same validated object with `scripts/render_direction_graph.py`. Preserve every node ID, parent, type, relevance, evidence basis, verification state, status, source reference, edge endpoint, relation, strength, edge basis, and label.

Use a deterministic hierarchical layout and self-contained HTML/SVG. Draw parent hierarchy with a visually separate non-semantic line, and state that it does not mean support. Provide pan, zoom, search, node/role/evidence/relation filters, keyboard-focusable nodes and edges, a details panel, legend, and text fallback. Do not load a CDN, font, analytics script, remote image, or graph service.

Escape all user text before inserting it into HTML or SVG. Put the source object into inert JSON with `<`, `>`, and `&` escaped. Use `textContent`, not `innerHTML`, when showing interactive details.

## Keep interaction non-authoritative

Filtering, hiding, zooming, clicking, focusing, or selecting changes only the current view. It cannot:

- upgrade evidence or resolve a citation;
- modify the source graph or user files;
- confirm or reject a direction;
- open a route gate;
- authorize a write, download, upload, experiment, simulation, training run, publication, or external communication.

When HTML output is not requested or file writing is not authorized, return the structured object plus text fallback in chat.
