---
name: research-cross-review
description: "Review a manuscript, plan, result package, or response from separated reviewer perspectives; preserve each report and disagreements before synthesis, then leave substantive revision decisions to the author. Use for 交叉审阅、模拟审稿、预审、审稿人视角、多人审阅 or disagreement-aware critique. Do not use for an author rebuttal, automatic manuscript rewrite, or averaged reviewer verdict."
---

# Research Cross Review

Preserve reviewer separation before combining issues. Apply [shared research governance](../engineering-research-copilot/references/core-research-governance.md) and the [handoff contract](../engineering-research-copilot/references/core-skill-handoffs.md).

In a generated host projection, read the linked copies inside this Skill. In the canonical source tree, the links resolve to the umbrella sibling. Do not reconstruct or weaken the shared rules.

## Freeze the review input

Identify the exact manuscript, plan, figures, data, supplementary material, and claim-evidence ledger that each pass may inspect. Record missing items and the evidence level. Keep the review read-only unless the author separately requests file edits.

## Run separated passes

Create at least these three source-only passes without exposing one pass's findings to the next before each report is frozen:

1. `R1_contribution_and_positioning`: question, significance, novelty boundary, related-work coverage, and claim scope.
2. `R2_methods_and_validity`: design, controls, leakage, statistics, uncertainty, reproducibility, safety, and alternative explanations.
3. `R3_results_and_communication`: result-to-claim consistency, figures/tables, limitations, writing clarity, and decision usefulness.

If actual independent agents produced the reports, state that fact and preserve their identities. If one agent performed separated passes, label them `separated_passes`, not independent agents.

Each report must contain strengths, major concerns, minor concerns, evidence anchors, confidence, missing-information dependencies, and a provisional recommendation. Do not tune later reports to create artificial agreement.

## Preserve disagreement before synthesis

After freezing all reports, build a cross-review matrix:

```yaml
issue_id: "X1"
reviewer_positions: {}
agreement_state: "agreement|partial_agreement|disagreement|single_reviewer"
evidence_dependencies: []
resolution_needed: ""
```

Show minority findings, contradictory recommendations, and issues that disappear only because a reviewer lacked information. Then synthesize duplicates, priority, and dependencies. Do not delete a finding merely because it is inconvenient or stylistic.

## Leave decisions to the author

Return an author decision ledger with `accept`, `reject`, `modify`, or `defer` unset for every substantive proposal. Explain the consequence of each choice. Do not revise claims, methods, analyses, conclusions, or files until the author chooses. Editorial corrections that change no scientific meaning may be listed separately.

## Hand off

Pass frozen reports, disagreement matrix, synthesis, and author decisions. A synthesis is not evidence that every reviewer agreed and is not authorization to edit, rerun analyses, or communicate with a journal.
