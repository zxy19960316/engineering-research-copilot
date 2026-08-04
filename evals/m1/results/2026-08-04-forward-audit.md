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

## Case A — clean second-round rerun

- Rerun file: `2026-08-04-pwr-sb-loca-rerun.md`
- Independent audit classification after one provenance correction: `pass`

The rerun used only the preserved round-one capture and the frozen feedback. It produced 18 current, deduplicated DOI records, six default recommendations, complete round-one dispositions, a structured `user_fit` map with aligned Mermaid/text renderings, basis labels, limitations, deviations, and an explicit `validator_result: not_run`. The audit found that two transient Crossref failures appeared in the tool log but not the affected candidate `checked_sources`; both unavailable attempts were added before their later successful matches without changing final status or eligibility. The reviewer rechecked the correction and returned `PASS`.

## Case B — first clean second-round rerun

- Rerun file: `2026-08-04-bearing-fault-rerun.md`
- Independent audit classification: `fail`
- The rerun is not eligible to close M1.

Blocking findings:

1. Three selected records were labeled `fulltext_level` even though their publisher lookups were unavailable and the cited material came from search-index snippets. One repeated non-overlapping-window claim had no inspected full-text anchor.
2. Another selected record logged a ScienceDirect publisher match despite a direct 403 response; search-index abstract/highlight text cannot be recorded as a successful publisher-landing check.
3. The described RoundBundle closed before the required `paper_map` object and was not a runnable JSON bundle. Its `validator_result: not_run` was truthful, but the incomplete bundle could not support `ROUND_TWO_READY`.

Preserved passing observations:

- The rerun used only the frozen first-round range and feedback, selected the default five papers, and created no expanded-count request.
- The 18 candidate DOI identities were unique and current Crossref spot checks matched.
- FeedbackDelta, query cause references, eight dispositions, SearchPlan limitations, deviations, map rendering parity, and node sizing were otherwise present.

Required next execution boundary:

- Preserve this failed rerun unchanged.
- Run a new fresh-context second-round evaluation from the same first-round capture and frozen feedback.
- Treat search snippets only as discovery. A 403/429 or unparseable publisher response is `unavailable`, never `match`.
- Require a directly inspected full-text source plus a section/page/table anchor for `fulltext_level`; otherwise keep the actual lower basis or block the claim.
- If fewer than five recommendation-eligible records remain, return `evidence_incomplete` / `WAITING_FOR_EVIDENCE_DECISION` instead of completing the workflow.

## Case B — second clean second-round rerun

- Rerun file: `2026-08-04-bearing-fault-rerun-2.md`
- Independent audit classification after one structural record correction: `pass`

The rerun used only the preserved intake/round-one range and the frozen feedback. It recorded 16 current, deduplicated candidates but found only three records with sufficient abstract- or full-text-level support for the revised evaluation-design criteria. It therefore stopped at `evidence_incomplete` / `WAITING_FOR_EVIDENCE_DECISION` instead of padding the default five-paper minimum.

The audit independently confirmed the three evidence anchors, the excluded erroneous DOI lookup, unavailable publisher responses, FeedbackDelta and query traceability, eight dispositions, map/rendering parity, and the honest validator `not_run` state. The initial Markdown object used summary references for ResearchBrief, SearchPlan, and Paper Map; those complete objects were embedded without changing candidates, selections, basis levels, dispositions, or final status. The reviewer rechecked the structural correction and returned `PASS`.

## Forward-test acceptance summary

- Case A: `pass` after a clean six-paper second-round rerun.
- Case B: `pass` as a behavior test because decisive evidence remained below the five-paper minimum and the workflow stopped with an honest `evidence_incomplete` result.
- Case C: `pass` as a citation-gate behavior test after the result-record supplement; the supplied citation itself remains `conflicted` and recommendation-ineligible.
- Initial failed runs and their findings remain committed and are not relabeled as passing evidence.
