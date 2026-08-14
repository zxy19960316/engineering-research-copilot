# Research Skill Cluster Foundation Implementation Plan

**Goal:** Package the existing research copilot as a plugin of focused, interoperable Skills while preserving the historical M4.2 terminal state and implementing only the successor foundation slice.

**Architecture:** Keep `engineering-research-copilot` as a thin umbrella router. Add focused Skills with distinct triggers and success criteria. Put evidence, readiness, permissions, review independence, and handoff semantics in one shared reference owned by the umbrella Skill. Keep the cluster offline-capable and make external tools optional providers rather than hidden dependencies.

**Baseline:** Branch `codex/research-skill-cluster-strengthening`, base commit `c21c24e079631d2396a3989045c9f0945e17c24e`. Do not modify or rerun M4.2 authorization, claim, execution, result, or terminal evidence. Do not commit, push, publish, install, or communicate externally without separate authorization.

## Task 1: Freeze the successor contract

**Files:**

- Create `docs/product-spec-v0.5.md`.
- Create the two research reports under `docs/research/`.
- Append a successor-development entry to `STATUS.md` without changing historical M4.2 statements.

**Checks:**

- Record the old constraints that are retained, rejected, reset, and newly added.
- State that the former static-only direction-view preference is reset only for the new direction graph; the accepted M1 paper map remains unchanged.
- State that Skill-cluster packaging supersedes the single-Skill packaging rule for this successor branch.

## Task 2: Create the plugin and shared contract

**Files:**

- Create `.codex-plugin/plugin.json`.
- Create `skills/engineering-research-copilot/references/core-research-governance.md`.
- Create `skills/engineering-research-copilot/references/core-skill-handoffs.md`.
- Modify `skills/engineering-research-copilot/SKILL.md` and `agents/openai.yaml`.

**Checks:**

- The shared evidence record keeps source class, identity verification, content inspection, and claim relation orthogonal.
- The readiness state is one of `concept_sketch`, `route_preparation`, or `executable_route`.
- Route generation and route execution have separate gates.
- File writes, downloads, uploads, experiments, simulations, training, publication, and external communication each require scoped authorization.
- Cross-review preserves independent reports and disagreements before synthesis; the author owns substantive changes.

## Task 3: Add focused Skills

**Files:**

- Create `skills/research-direction-evidence/`.
- Create `skills/research-literature-evidence/`.
- Create `skills/research-method-transfer/`.
- Create `skills/research-manuscript/`.
- Create `skills/research-cross-review/`.
- Create `skills/research-data-comparison/`.
- Create `skills/research-evidence-adversary/`.
- Create `skills/research-figure-workflow/`.

Every folder receives a concise `SKILL.md` and `agents/openai.yaml`. Add local references or scripts only where a focused workflow needs them. Link the shared governance and handoff files directly from every focused Skill.

**Checks:**

- Direct, indirect, incomplete, non-trigger, and edge prompts have an unambiguous owning Skill.
- No focused Skill silently grants another Skill permission to write or execute.
- Handoffs carry case/brief identity, source hashes or anchors, evidence gaps, readiness, and permitted next actions.

## Task 4: Validate the foundation

**Files:**

- Create `tests/test_research_skill_cluster.py`.

**Commands:**

```powershell
D:\anaconda\python.exe -X utf8 C:\Users\94310\.codex\skills\.system\plugin-creator\scripts\validate_plugin.py D:\engineering-research-copilot
D:\anaconda\python.exe -X utf8 C:\Users\94310\.codex\skills\.system\skill-creator\scripts\quick_validate.py <each-skill-directory>
D:\anaconda\python.exe -X utf8 -m unittest tests.test_research_skill_cluster -v
```

Expected: plugin validation passes; all Skill validators pass; the cluster audit finds the exact Skill set, direct shared-contract links, valid default prompts, no unresolved markers, and no external runtime requirement.
