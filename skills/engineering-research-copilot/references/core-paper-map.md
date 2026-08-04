# Static Paper Evidence Map

Use this file after verified, deduplicated papers are available. Use the map for fast orientation before the user reads the papers; do not present it as an interactive knowledge base or a substitute for full-paper reading.

## Build the map

1. Place the current research problem or brief at the center.
2. Create two to four direction, problem, method, or transfer clusters.
3. Show eight papers in round one and five to six in round two by default.
4. Assign stable labels `P1` through `P8` within a round and place exact citations in a table below the map.
5. Limit each paper to one or two explanatory edges.

## Encode meaning consistently

- Size a paper node by relative fit to the current `ResearchBrief`, not by citation count or general prestige.
- Color a paper node by evidence role: direct problem, method, transfer/bridge, or counter/limitation.
- Use the border to distinguish formal publication, verified preprint, and limited/partial evidence.
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

## Use this data shape

```yaml
paper_map:
  round: 1
  brief_version: 2
  nodes:
    - id: "P1"
      node_type: "paper"
      fit_score: 0.86
      evidence_role: "transfer_bridge"
      verification_status: "verified_primary"
      basis_level: "abstract_level"
      short_note: "Method transfer evidence from a similar data regime"
  edges:
    - source: "P1"
      target: "D2"
      relation: "transfer_bridge"
      strength: "medium"
      confidence: "medium"
      basis_level: "abstract_level"
      note: "Mechanism is similar; boundary conditions still require testing"
```

## Accept chat feedback

Invite concise natural-language feedback such as:

```text
Focus more on D2; retain P1 and P5; exclude routes requiring private data;
prefer executable simulations; increase the share of transfer methods.
```

Do not require the user to click the map, read every paper, or score every node. Apply the feedback through the rollback protocol and show the change summary before searching again.
