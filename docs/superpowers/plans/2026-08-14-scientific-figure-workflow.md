# Scientific Figure Workflow Implementation Plan

**Goal:** Add an evidence-grounded scientific-figure Skill and reusable recipe asset pack without redistributing paper figures or claiming that plotting has been executed.

**Architecture:** Synthesize primary method papers, publisher examples, and official plotting-library documentation into recipe records. Separate visual inspiration, statistical method support, software implementation support, and license status. Select a recipe from the intended claim and data shape before selecting aesthetics or a backend.

## Task 1: Synthesize the survey

**Files:**

- Consume `docs/research/2026-08-14-scientific-figure-workflow-survey.md`.
- Create `skills/research-figure-workflow/references/figure-evidence-register.md`.
- Create `skills/research-figure-workflow/references/figure-workflow.md`.

Record source links and access dates. Label popularity or citation-count signals as such unless a current authoritative count was checked. Do not copy article panels, captions beyond short compliant excerpts, or full papers into the Skill.

## Task 2: Build the recipe assets

**Files:**

- Create `skills/research-figure-workflow/assets/figure-recipes.json`.
- Create `skills/research-figure-workflow/references/figure-taxonomy.md`.

Cover regression/diagnostic, agreement/concordance, calibration, uncertainty, distribution, ROC/PR/decision curve, survival, sensitivity/ablation, heatmap/multivariate, and network/field/multiphysics families. Every recipe states purpose, admissible claims, required data, assumptions, minimum panels, deceptive failure modes, uncertainty display, accessibility, export targets, and source/license references.

## Task 3: Implement deterministic selection and validation

**Files:**

- Create `skills/research-figure-workflow/scripts/select_figure_recipe.py`.
- Create `tests/test_figure_recipe_workflow.py`.

Validate the closed recipe schema. Select candidate recipes from an explicit figure brief without inventing fields. Return a stop state when the outcome, comparator, uncertainty, units, or pairing structure required by a recipe is unknown. Do not generate plot data or files.

## Task 4: Validate

```powershell
D:\anaconda\python.exe -X utf8 -m unittest tests.test_figure_recipe_workflow -v
D:\anaconda\python.exe -X utf8 skills\research-figure-workflow\scripts\select_figure_recipe.py --validate-assets
```

Expected: every family is represented; all records have source/license provenance; invalid or under-specified briefs fail closed; selection is deterministic; no network, plotting, download, or output-file side effect occurs during validation.
