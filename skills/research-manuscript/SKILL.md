---
name: research-manuscript
description: "Plan, draft, restructure, revise, or polish a research manuscript from author-provided claims, evidence, results, figures, notes, or reviewer decisions without inventing citations, data, experiments, results, numbers, or conclusions. Use for 论文写作、写摘要、写引言、写结果、写讨论、润色、改稿 or claim-led manuscript work. Do not use to simulate reviewers, answer as a reviewer, or add unsupported citations."
---

# Research Manuscript

Write from an explicit claim-evidence relationship, not from plausible-sounding filler. Apply [shared research governance](../engineering-research-copilot/references/core-research-governance.md) and the [handoff contract](../engineering-research-copilot/references/core-skill-handoffs.md).

In a generated host projection, read the linked copies inside this Skill. In the canonical source tree, the links resolve to the umbrella sibling. Do not reconstruct or weaken the shared rules.

## Establish the writing basis

Accept an idea, outline, notes, results, figures, draft, or approved reviewer-response decisions. Identify the requested section, audience, venue constraints, language, and whether the user wants planning, drafting, revision, or polishing.

Before substantive prose, create or validate the claim-evidence ledger. For every intended claim record its scope, evidence IDs, counterevidence, assumptions, falsifier, status, and allowed language. Mark missing support as a gap. Never create realistic-looking placeholder citations or fill a missing numerical result.

Keep `draft_mode` and `polish_mode` isolated. Drafting may organize author-approved claims into new prose. Polishing must preserve the existing claims and citations unless it explicitly proposes a mode change. If polishing repeatedly adds claims/citations or drafting activates on simple surface edits, split the modes into separate writing and polishing Skills while preserving the same claim ledger.

## Match prose strength to evidence

- State user-provided results as author-supplied and not independently reproduced.
- Distinguish observation, analysis output, interpretation, mechanism, causality, transfer, and recommendation.
- Use metadata only for bibliographic context, not substantive support.
- Use abstract-level evidence only within the abstract's verified scope.
- Use full-text claims only with inspected anchors.
- Keep contested evidence and alternative explanations visible.
- Do not claim novelty, priority, state of the art, or absence of prior work beyond the documented search boundary.

## Build the argument

Map each paragraph to one communicative job and one primary claim. Keep the sequence explicit: context or observation → gap/question → method or analysis → result → bounded interpretation → limitation/implication. Remove claims that have no admissible evidence or rewrite them as hypotheses, objectives, or limitations.

For polishing, preserve scientific meaning, numbers, units, citations, uncertainty, and author terminology unless a change is explicitly proposed. Flag ambiguous source wording instead of silently choosing a stronger meaning.

## Keep writing and file mutation separate

Return draft text in chat when requested. A request to review or advise is read-only and does not authorize modifying source files. If the user asks to edit a file, scope writes to the named file and preserve a visible change summary. Do not submit, upload, publish, or contact an editor.

## Hand off

Pass the manuscript snapshot, claim-evidence ledger, unresolved gaps, terminology constraints, and author-approved changes to `$research-cross-review` or `$research-evidence-adversary`. Preserve rejected suggestions and do not imply author approval.
