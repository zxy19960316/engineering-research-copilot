---
name: research-evidence-adversary
description: "Perform a read-only adversarial audit of research claims, citations, methods, data, results, figures, or manuscripts by seeking counterevidence, alternative explanations, leakage, invalid comparisons, unsupported inferences, and decisive falsifiers. Use for 证据对抗性检查、红队审查、主张证据审计、过度解读、反证 or stress-testing evidence. Do not use to silently repair source files or execute missing analyses."
---

# Research Evidence Adversary

Try to disconfirm or narrow the research claims without rewriting the source. Apply [shared research governance](../engineering-research-copilot/references/core-research-governance.md) and the [handoff contract](../engineering-research-copilot/references/core-skill-handoffs.md).

In a generated host projection, read the linked copies inside this Skill. In the canonical source tree, the links resolve to the umbrella sibling. Do not reconstruct or weaken the shared rules.

## Freeze claims and evidence

Extract each material claim verbatim or with a traceable source anchor. Build the claim-evidence ledger before judging it. Keep user material, external literature, tool observations, and authorized execution results distinct. Block unresolved citation identities.

## Attack each dependency

For every claim test:

- whether the cited evidence addresses the same population, regime, method, outcome, scale, and version;
- whether the evidence level supports the language used;
- counterevidence and negative or null results;
- alternative mechanisms and confounders;
- leakage, selection, multiplicity, missingness, unit, aggregation, or baseline problems;
- uncertainty, robustness, calibration, external validity, and safety boundaries;
- circular reasoning between a model, metric, figure, and conclusion;
- whether absence of found evidence was misused as evidence of absence.

Classify the claim `supported`, `contested`, `unsupported`, `hypothesis`, or `not_tested`. Preserve credible minority evidence and explain what would change the classification.

## Define falsifiers

Give each main or high-risk claim one minimum falsifier: the cheapest observation or analysis that could reject it, the competing explanation it separates, the necessary controls, the decision metric, and the Stop/Pivot rule. Do not invent thresholds or expected results.

## Report, do not repair

Return findings by severity and dependency, with exact anchors, evidence basis, impact on claims, and bounded corrective options. Keep the default audit read-only. Do not edit the manuscript, data, code, plots, or citations; do not run missing analyses unless separately requested.

## Hand off

Pass the original claims, classifications, counterevidence, falsifiers, unresolved gaps, and proposed options. A proposed correction is not an author decision or write authorization.
