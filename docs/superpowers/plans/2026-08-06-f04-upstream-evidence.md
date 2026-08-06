# F04 Upstream Evidence Lineage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a new, independently searched M1.2 literature-calibration bundle and a validator-valid provisional M2.1.1 direction portfolio for public rolling-bearing vibration measurement, calibration, repeatability, reproducibility, and measurement uncertainty/UQ, then stop at the formal direction-confirmation gate.

**Architecture:** Keep all new evidence under `evals/f04-upstream/` and preserve the accepted M1 bundle verbatim inside M2. Use authoritative DOI-registry and publisher records for current citation verification, keep discovery and verification logs separate, bind raw and canonical hashes, and generate deterministic M1 maps through the repository renderer. Leave `route_output: null`, `confirmation_event: null`, and create no M3 artifact.

**Tech Stack:** UTF-8 JSON, Markdown/Mermaid, Python 3.12 with `-X utf8`, the repository's four permitted offline validators/renderers, public Crossref/publisher bibliographic pages, and the `nature-academic-search` multi-source/citation-verification workflow.

## Global Constraints

- Work only in `C:\Users\94310\.codex\worktrees\7452\engineering-research-copilot` on `codex/f04-upstream-evidence`.
- Read and attest only the permitted repository files; do not read tests, fixtures, prior bearing results, or any `evals/m3/` path.
- Create exactly one new M1.2 two-round calibration artifact and one provisional M2.1.1 portfolio with exactly three formal positions.
- Enter `M1_COMPLETE` only with a real 15–20-record verified round-one pool, exact 3/2/2/1 round-one role allocation, feedback-traceable second-round search, and five-to-six eligible round-two selections.
- Use `verified_primary`, `verified_registry`, or contract-valid `verified_preprint` only after current authoritative checks; never infer metadata or identifiers.
- Include explicit units, calibration provenance, repeatability, reproducibility, UQ prerequisites, finite resource ceilings, and numeric success/stop/pivot criteria only where source and contract evidence justify them.
- Do not create `user_confirmed`, `route_output`, M3 cards, M3 payloads, M3 prompts, M3 outcomes, or any path under `evals/m3/`.
- Validate M1 before creating M2, validate M2 before the confirmation gate, review status, stage explicit paths, and make independent local commits; do not push, merge, tag, or open a PR.

---

### Task 1: Freeze the independent search brief and evidence ledger

**Files:**
- Create: `evals/f04-upstream/m1/f04-m1-search-verification-provenance.json`
- Create: `evals/f04-upstream/m1/f04-m1-citation-ledger.json`
- Modify: `docs/superpowers/plans/2026-08-06-f04-upstream-evidence.md`

**Interfaces:**
- Consumes: the user-authorized F04 topic, repository M1.2 contract, and current public bibliographic search results.
- Produces: a natural-language brief, two round query plans, discovery records, authoritative verification attempts, evidence-level labels, limitations, and stable candidate IDs used by the M1 bundle.

- [ ] Record the brief with at most three high-impact open questions, public-data and no-side-effect constraints, and a unique F04 branch ID.
- [ ] Run first-round discovery across Crossref/T1-style registry and publisher records, using semantic/broad search only for candidate discovery; preserve raw query, source, timestamp, result URL, and supplied metadata without promoting snippets to facts.
- [ ] Verify every admitted record against a current DOI registry or official repository and publisher landing record when available; record exact title, ordered authors, dates, venue, work type, identifier, checked time, result, evidence role, basis level, support, limitation, and no-inference notes.
- [ ] Deduplicate on DOI first, then official alternate ID, then manual title/first-author review; block conflicts and unresolved identities rather than repairing them.
- [ ] Commit the independent discovery/verification ledger as a reviewable evidence-only commit before composing the M1 bundle.

### Task 2: Compose and validate the two-round M1.2 artifact

**Files:**
- Create: `evals/f04-upstream/m1/f04-m1-calibration.json`
- Create: `evals/f04-upstream/m1/f04-m1-map.md`
- Create: `evals/f04-upstream/m1/f04-m1-validation.json`
- Create: `evals/f04-upstream/m1/f04-m1-hashes.json`

**Interfaces:**
- Consumes: `f04-m1-citation-ledger.json`, the round-one/round-two search provenance, and deterministic map renderer.
- Produces: a machine-valid `schema_version: m1.2`, `terminal_state: M1_COMPLETE`, `outcome: complete` bundle only if every M1 gate is satisfied, plus validator receipt and raw/canonical hash bindings.

- [ ] Build round one with 15–20 real verified/deduplicated candidates and exactly eight selected records in roles 3 direct-problem, 2 method, 2 transfer-bridge, and 1 counter/limitation.
- [ ] Render round-one and round-two Mermaid/text maps from the structured node/edge lists with `render_m1_map.py`; keep every map relation at metadata, abstract, or full-text basis explicitly.
- [ ] Record a visible feedback delta that changes the second-round brief/query text and cites every material rejected/reset/added item.
- [ ] Re-verify carried IDs with stable identity and add only newly verified candidates; select five or six round-two records without padding.
- [ ] Run `python -X utf8 skills/engineering-research-copilot/scripts/validate_m1_bundle.py evals/f04-upstream/m1/f04-m1-calibration.json`; stop honestly with `WAITING_FOR_EVIDENCE_DECISION` if any real gate is incomplete.
- [ ] If valid, compute raw file SHA-256, canonical UTF-8 sorted-compact JSON SHA-256, and the M1 validator receipt; do not call offline validation real citation proof.
- [ ] Commit the accepted M1 artifact and receipts independently before creating M2.

### Task 3: Derive, validate, and freeze the provisional M2.1.1 portfolio

**Files:**
- Create: `evals/f04-upstream/m2/f04-m2-direction-bundle.json`
- Create: `evals/f04-upstream/m2/f04-m2-validation.json`
- Create: `evals/f04-upstream/m2/f04-m2-hashes.json`
- Create: `evals/f04-upstream/m2/f04-m2-confirmation-gate.md`

**Interfaces:**
- Consumes: the complete accepted M1 bundle and its canonical hash.
- Produces: exactly one `provisional_main`, one `adjacent_alternative`, and one `transfer_exploration`, optional high-risk ideas only if independently justified, a waiting-for-confirmation decision, and no route.

- [ ] Embed the complete M1 JSON verbatim and bind `source_m1_bundle_hash` to canonical UTF-8 JSON.
- [ ] Derive three materially different problem/method/data axis profiles, with zero/one/at-least-two axis changes for main/adjacent/transfer positions.
- [ ] For each direction, include eligible supporting and counter IDs, transfer compatibility, anti-transfer factors, units/scales/boundary conditions, UQ and data preconditions, finite resource limits, and numeric minimum-decisive-test success/stop/pivot criteria with explicit units.
- [ ] Keep all seven hard gates, equal 100-point scorecard weights, and `recommendation_status: provisional`; keep any speculative idea outside formal ranking.
- [ ] Set `direction_decision` to the exact waiting state with `selected_direction_id: null`, `confirmation_event: null`, and `route_output: null`.
- [ ] Run `python -X utf8 skills/engineering-research-copilot/scripts/validate_m2_direction_bundle.py evals/f04-upstream/m2/f04-m2-direction-bundle.json` and preserve any incomplete/blocked result rather than weakening evidence.
- [ ] Compute selected-direction excerpt hashes and the pre-confirmation bundle hash, then write the exact user confirmation phrase without creating a confirmation event.

### Task 4: Audit, commit, and stop at the direction gate

**Files:**
- Modify: `evals/f04-upstream/m1/f04-m1-hashes.json`
- Modify: `evals/f04-upstream/m2/f04-m2-hashes.json`
- Modify: `evals/f04-upstream/m2/f04-m2-confirmation-gate.md`

**Interfaces:**
- Consumes: validated M1/M2 artifacts, validator receipts, raw/canonical hashes, and the repository read-path log.
- Produces: final confirmation-gate report and independently reviewable local commits, with no downstream route or M3 state.

- [ ] Add the complete repository read-path attestation, including every repository file actually opened and the explicit excluded paths not read.
- [ ] Recompute hashes from filesystem bytes and canonical payloads, verify embedded M1 identity, verify validator exit/status receipts, and check `git status --short`.
- [ ] Stage only `docs/superpowers/plans/2026-08-06-f04-upstream-evidence.md` and `evals/f04-upstream/**`, then commit the final audit without touching `STATUS.md` or historical evidence.
- [ ] Final response must report the branch, commit(s), M1/M2 validation status, formal direction IDs, concise summaries, selected-direction excerpt hashes, pre-confirmation bundle hash, exact phrase `Confirm F04 direction <DIRECTION_ID>`, and the hard stop. Do not emit or write a `user_confirmed` event.

## Self-review checklist

- [ ] Search/verification provenance separates discovery from authoritative verification and contains no inferred identifiers.
- [ ] M1 has complete role counts, stable IDs, feedback query changes, deterministic maps, current timestamps, and honest evidence-level limitations.
- [ ] M2 embeds M1 without mutation, passes all hard gates, has exactly the required formal positions, and remains provisional.
- [ ] All numeric criteria have explicit units and trace to source-supported claims or bounded preconditions.
- [ ] No route, experiment execution, model/data download, service, upload, M3 artifact, or confirmation event exists.
- [ ] Plan contains no unresolved placeholders and all listed files/commands match the actual deliverable paths.
