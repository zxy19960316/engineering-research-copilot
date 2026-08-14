---
name: research-method-transfer
description: "Select, compare, adapt, or transfer research methods with assumption mapping, target/source compatibility, anti-transfer analysis, controls, uncertainty, minimum falsification tests, and route readiness. Use for 科研方法、方法迁移、跨学科方法、实验方案、仿真方案、模型选择、最小验证 or assessing source-to-target transfer. Do not use to run an experiment, simulation, training job, or confirmed implementation."
---

# Research Method Transfer

Turn a confirmed problem or provisional direction into bounded method reasoning. Apply [shared research governance](../engineering-research-copilot/references/core-research-governance.md), the [handoff contract](../engineering-research-copilot/references/core-skill-handoffs.md), [method coaching](../engineering-research-copilot/references/core-method-coaching.md), and the [direction gate](../engineering-research-copilot/references/core-direction-decision.md).

In a generated host projection, read the linked copies inside this Skill. In the canonical source tree, the links resolve to the umbrella sibling. Do not reconstruct or weaken the shared rules.

## Establish the input state

Accept a method question, confirmed direction, source-domain method, existing plan, preliminary result, or failure. Identify the exact claim the method must test or enable. Validate the supplied evidence IDs, direction status, data/resources, and permission ledger before expanding the route.

If no direction is confirmed, stay at `concept_sketch` or `route_preparation`. You may compare methods and define a minimum decisive test, but do not produce a full route.

Keep `method_design_mode` and `transfer_assessment_mode` isolated. Method design starts from the target claim and constraints; transfer assessment additionally requires a named source method and source/target mapping. If transfer analogies repeatedly leak into unverified target recommendations, split these modes into separate Skills without changing the shared claim, evidence, readiness, or permission contracts.

## Map transfer explicitly

For every source-to-target transfer, show:

- source success and its inspected evidence level;
- target problem evidence;
- matching and mismatching concepts, units, scales, data distributions, boundary/initial conditions, mechanisms, and assumptions;
- anti-transfer factors and failure modes;
- data, instrumentation, software, compute, time, safety, ethics, and specialist-review preconditions;
- what can be inherited unchanged, adapted, newly calibrated, or rejected.

Use `established-in-target`, `transfer-supported`, `mechanism-plausible`, or `speculative` only at the strength allowed by the inspected evidence. Do not turn principle compatibility into target-domain performance.

## Define the minimum falsification test first

Specify the cheapest test that can reject the transfer claim before a full route:

- falsifiable claim and alternative explanation;
- baseline, negative control, and positive/reference control when available;
- train/validation/test or experimental separation needed to prevent leakage;
- primary metric matched to the claim, uncertainty, and decision rule;
- success, stop, and pivot conditions;
- maximum resource/time budget;
- analysis that will remain inconclusive even after the test.

Do not invent thresholds. Derive them from requirements, prior inspected evidence, a pilot-design rule, or mark them unresolved.

## Produce the real output level

- `concept_sketch`: method families, transfer hypotheses, assumptions, and missing evidence.
- `route_preparation`: candidate method stack, decisive-test design, controls, preconditions, and Go/Stop/Pivot rules.
- `executable_route`: stepwise route only after explicit direction confirmation and adequate preconditions.

A generated route is a document, not authorization to run. Keep experiment, simulation, training, file-write, download, and upload permissions separate.

## Hand off

Pass claim-to-metric mappings, assumptions, controls, transfer gaps, test rules, readiness, and permissions to data, figure, writing, or evidence-audit Skills. Do not pass expected results as observed results.
