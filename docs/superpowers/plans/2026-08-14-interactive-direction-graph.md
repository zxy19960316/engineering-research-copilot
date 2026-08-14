# Interactive Direction Graph Implementation Plan

**Goal:** Produce a deterministic, offline, self-contained hierarchy graph for research-direction comparison in which relevance controls node area and relationships are inspectable edges.

**Architecture:** Add a new `direction-graph.v1` contract and renderer under `research-direction-evidence`. Keep structured nodes and edges as the sole facts. Generate HTML/SVG and text fallback from that same object. Use a deterministic hierarchical layout; client-side JavaScript only changes view state.

## Task 1: Specify the graph contract

**Files:**

- Create `skills/research-direction-evidence/references/direction-graph-contract.md`.
- Create `tests/test_render_direction_graph.py`.

Require a root problem, unique node IDs, valid parent hierarchy, non-orphan edges, relevance values from zero through one, closed node/evidence/status/relation sets, and explicit evidence basis on every node and edge. Reject hierarchy cycles and graph facts that exist only in rendered HTML or fallback text.

## Task 2: Implement the renderer

**Files:**

- Create `skills/research-direction-evidence/scripts/render_direction_graph.py`.

Expose pure functions `validate_graph(graph)`, `render_text_fallback(graph)`, and `render_html(graph)`, plus a CLI that writes only caller-selected output paths. Use node area for relevance, separate evidence/status styling, relation-specific edges, width for edge strength, dashed inferred/transfer edges, pan/zoom, search, filters, keyboard focus, a details panel, and a visible legend. Use no network or external asset.

## Task 3: Add a truthful fixture and workflow integration

**Files:**

- Create `skills/research-direction-evidence/assets/direction-graph-example.json`.
- Modify `skills/research-direction-evidence/SKILL.md`.

Label the example as a synthetic contract fixture. It may demonstrate main, adjacent, transfer, high-risk, evidence, contradiction, constraint, and minimum-test nodes, but it must not resemble a real research conclusion or citation.

## Task 4: Validate

```powershell
D:\anaconda\python.exe -X utf8 -m unittest tests.test_render_direction_graph -v
D:\anaconda\python.exe -X utf8 skills\research-direction-evidence\scripts\render_direction_graph.py skills\research-direction-evidence\assets\direction-graph-example.json --check
```

Expected: deterministic bytes, exact fallback equivalence, no external URL or script reference, unsafe text escaped, filters and accessibility labels present, and fixture validation succeeds without writing an output file under `--check`.
