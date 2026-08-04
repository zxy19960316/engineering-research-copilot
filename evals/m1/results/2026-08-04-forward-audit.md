# M1 Fresh-Context Forward-Test Audit

- Audit date: `2026-08-04` (`Asia/Shanghai`)
- Skill revision under test: `2291357`
- Scope: independent review of the first execution of frozen forward cases A, B, and C
- Preservation rule: do not rewrite a failing execution into a pass; retain the original output and supersede it only with a separately recorded rerun.

## Case A — first execution

- Result file: `2026-08-04-pwr-sb-loca.md`
- Independent audit classification: `fail`
- Forward result is not eligible to close M1.

Blocking findings:

1. The frozen second-round feedback did not request eight papers, but the execution recorded `explicit_user_request: true` and `requested_count: 8`. The Skill defaults to five or six second-round recommendations unless the user explicitly requests seven to ten.
2. The second-round 18-paper pool was summarized without the complete per-record authoritative provenance and blocking fields needed for audit. Two records were promoted to `fulltext_level` without a recorded full-text anchor.
3. The second-round map omitted a structured `paper_map` with `node_size_basis: user_fit`, even though its Mermaid and text renderings were otherwise semantically aligned.
4. No compatible JSON bundle was produced, so the offline bundle validator was not run. The original result did not explicitly record this `not_run` state.
5. The file retained round-one header state beside a later final state without a separate document-level status block.

Required rerun boundary:

- Preserve the first execution unchanged.
- Use the captured round-one output as the only prior state.
- Supply only the frozen second-round feedback.
- Select five or six recommendations; do not invent expanded-count authorization.
- Record complete candidate provenance, basis levels, structured map, dispositions, deviations, and `validator_result: not_run` unless a compatible JSON artifact is actually produced.

## Case B — first execution

- Result file: `2026-08-04-bearing-fault.md`
- Independent audit classification: `fail`
- Forward result is not eligible to close M1.

Blocking findings:

1. The frozen second-round feedback did not request eight papers, but the execution recorded `explicit_user_request: true` and `requested_count: 8` instead of using the five-to-six default.
2. The result omitted the required validator result and did not record the injected count deviation.
3. The second-round `SearchPlan.limitations` was empty even though unavailable scholarly MCP coverage and lack of full-text checks were already known.

Preserved passing observations:

- Intake stopped after three material questions and did not search before frozen answers arrived.
- Round one recorded 18 verified, deduplicated candidates, the `3/2/2/1` eight-paper allocation, a citation index, and aligned Mermaid/text views.
- The second-round output correctly refused to treat metadata eligibility as proof of leakage-resistant evaluation and ended `evidence_incomplete` / `WAITING_FOR_EVIDENCE_DECISION`.

Required rerun boundary:

- Preserve the first execution unchanged.
- Use the captured round-one output as the only prior state.
- Supply only the frozen second-round feedback.
- Select five or six recommendations and recompute all eight round-one dispositions.
- Put known tool and evidence limitations in the revised SearchPlan.
- Keep the result `evidence_incomplete` unless decisive leakage-resistant split evidence is actually verified.
- Record `validator_result: not_run` unless a compatible JSON artifact is actually produced.

## Case C — citation audit

- Result file: `2026-08-04-citation-audit.md`
- Independent audit classification: `fail` for the Task 7 record contract; the citation-gate decision itself passed.

Blocking finding:

1. The result omitted `validator_result` and `deviations`. Because the citation conflict stopped the workflow before any compatible RoundBundle existed, the truthful validator state is `not_run`, not pass.

Preserved passing observations:

- Current Crossref metadata identifies the supplied DOI as `Deep learning`, and the official NeurIPS record identifies the supplied title as a distinct work.
- The record preserves `conflicted`, `recommendation_eligible: false`, and a citation-gate stop without repairing or substituting an identifier.
- `pass` is explicitly limited to correct workflow behavior and is not presented as a valid supplied citation.
- No candidate pool, two-round calibration, route, RRC, M2, or M3 work was performed.

Required correction:

- Append `validator_result: not_run` with the reason that no compatible RoundBundle was formed before the citation-gate stop.
- Append `deviations: none` if no other execution deviation is found.
