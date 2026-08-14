---
name: research-figure-workflow
description: "Select, plan, audit, or execute a scientific-figure workflow from the intended claim and data structure, covering regression, agreement, calibration, uncertainty, distributions, classification, survival, sensitivity, heatmaps, networks, and physical fields. Use for 科研绘图、论文配图、回归图、一致性分析图、Bland-Altman、校准图、消融图、热图、场图 or figure QA. Do not use for product dashboards or analysis with no figure outcome."
---

# Research Figure Workflow

Choose a figure for the scientific question before choosing aesthetics. Apply [shared research governance](../engineering-research-copilot/references/core-research-governance.md), the [handoff contract](../engineering-research-copilot/references/core-skill-handoffs.md), the [figure workflow](references/figure-workflow.md), [figure taxonomy](references/figure-taxonomy.md), and [evidence register](references/figure-evidence-register.md).

In a generated host projection, read the linked copies inside this Skill. In the canonical source tree, the links resolve to the umbrella sibling. Do not reconstruct or weaken the shared rules.

## Build the figure brief

Identify the intended conclusion, claim ID, audience, comparison unit, data structure, pairing/repetition, outcome and units, uncertainty, sample or regime, missingness, transformations, accessibility needs, target journal, and export formats. Keep expected values and real observations separate.

If the user wants an actual plot and has not chosen a backend, ask `Python or R?` and stop figure execution. Planning and audit may remain backend-neutral. Do not create a figure file during a read-only audit.

## Select an evidence-grounded recipe

Use `assets/figure-recipes.json` and `scripts/select_figure_recipe.py` after the recipe pack is validated. Use `assets/figure-brief-example.json` only as a synthetic contract example, never as real data or an empirical result. Match the intended claim and data shape, not just a named visual. Cover at least:

- regression fit and diagnostics;
- agreement, concordance, and Bland-Altman analysis;
- calibration and reliability;
- uncertainty and interval coverage;
- distributions and group comparisons;
- ROC, precision-recall, and decision curves;
- survival and time-to-event;
- sensitivity, robustness, and ablation;
- heatmaps and multivariate structure;
- networks, spatial fields, and multiphysics views.

State what the selected figure can and cannot establish, required analyses, assumptions, deceptive failure modes, minimum panels, uncertainty display, accessibility rules, and export targets. Stop when required pairing, units, comparator, outcome, uncertainty, or time/censoring structure is unknown.

## Keep the asset pack lawful and auditable

Use reusable recipes, source links, caption/figure anchors, and license notes. Do not copy or redistribute article panels, full papers, proprietary templates, or unlicensed code. Treat publisher figures as design evidence, not bundled assets. Distinguish method support, visual precedent, software documentation, and license provenance.

## Execute only when authorized

An explicit request to create or revise a figure may authorize the scoped artifact write, but does not authorize data modification, download, upload, simulation, experiment, training, or publication. Use only the chosen backend. Preserve source data, code or recipe identity, random seeds when relevant, and exact export settings.

Before delivery, verify legibility, units, axes, transformations, sample counts, uncertainty semantics, color accessibility, grayscale robustness, panel consistency, raster/vector resolution, font embedding, and agreement between caption and plotted data. Never add a trend, significance marker, or result not supported by the supplied or computed data.

## Hand off

Pass the figure brief, recipe ID/version, data/result IDs, admissible claim, limitations, provenance, QA findings, output path/hash when written, and permission state to manuscript or evidence-audit Skills.
