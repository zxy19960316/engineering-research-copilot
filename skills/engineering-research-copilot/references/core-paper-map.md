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
