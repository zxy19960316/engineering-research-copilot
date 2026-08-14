---
name: research-data-comparison
description: "Compare author-provided datasets, groups, methods, models, experiments, simulations, or result tables with unit, pairing, uncertainty, baseline, missingness, and claim-scope checks. Use for 数据对比、结果对比、模型比较、实验组比较、表格分析、误差比较 or deciding what observed differences support. Do not use to fabricate missing values, create a scientific plot, or generalize beyond supplied data."
---

# Research Data Comparison

Compare only supplied or separately authorized observations. Apply [shared research governance](../engineering-research-copilot/references/core-research-governance.md) and the [handoff contract](../engineering-research-copilot/references/core-skill-handoffs.md).

In a generated host projection, read the linked copies inside this Skill. In the canonical source tree, the links resolve to the umbrella sibling. Do not reconstruct or weaken the shared rules.

## Audit comparability first

Identify the comparison unit, population or operating regime, sample identity, paired/unpaired/repeated structure, time window, units, transformations, missingness, censoring, weighting, aggregation, baselines, and uncertainty representation. Stop or stratify when unlike quantities are being combined.

Record whether each value is raw observation, processed value, analysis output, simulation output, user-reported summary, or expected value. Do not treat an expected or planned value as observed.

## Build the comparison matrix

For every comparison show:

- object IDs and provenance;
- outcome and unit;
- sample/regime and pairing;
- point estimate and uncertainty exactly as supplied;
- baseline or reference;
- direction and practical magnitude of the difference;
- admissible claim and claims not established;
- missing controls, confounders, leakage risks, and sensitivity needs.

Do not infer statistical significance from overlapping bars or non-overlapping point estimates. Do not compute a test, confidence interval, effect size, calibration metric, or derived value unless the user asks for that analysis and supplies adequate data. Label every newly computed output and preserve the formula, inputs, and assumptions.

## Separate comparison from causality

Treat association, prediction, agreement, equivalence, non-inferiority, and causality as different claims. Require design-specific evidence for each. Distinguish simulation verification from validation against reality and within-distribution performance from transfer/generalization.

## Return read-only findings

Return a comparability verdict, comparison matrix, claim impacts, data-quality issues, missing analyses, and figure-ready structure. Do not alter data files, run code, or create plots unless separately requested and authorized.

## Hand off

Pass stable data/result IDs, units, pairing, transformations, uncertainty, admissible comparisons, and unresolved gaps to figure, manuscript, or evidence-adversary Skills. Never pass an inferred difference as an observed result.
