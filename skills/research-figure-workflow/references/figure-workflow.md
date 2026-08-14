# Scientific Figure Workflow

Use this workflow to select and audit a scientific figure before any plotting. Treat the static figure and its source-data/statistics records as the authoritative result; use interactive output only as an optional review companion.

## Freeze the figure brief

Record one intended claim per figure or panel, its claim-evidence status, the unit of observation, data columns and units, pairing or hierarchy, missingness, transformations, train/validation/test split, interval semantics, target journal, export size, backend, and current authorization.

Do not infer a residual definition, interval type, acceptable agreement limit, class prevalence, censoring rule, parameter distribution, seed/fold alignment, heatmap transformation, edge meaning, coordinate system, or color scale. Return a missing-information state when a selected recipe requires it.

## Select the recipe before aesthetics

Validate `assets/figure-recipes.json`, then run `scripts/select_figure_recipe.py` against a closed `figure-brief.v1` object. Select by the evidence question and data design. Return the primary recipe, adjacent recipes, the minimum falsification view, missing fields, and the limits on the claim.

Do not use a correlation plot as an agreement analysis, ROC as the sole imbalanced-class view, a bar chart as a distribution, `1-KM` as a competing-risk estimate, one-at-a-time perturbation as global sensitivity, or a smooth field rendering as evidence of validation.

## Separate computation and rendering

When execution is explicitly authorized:

1. Validate source IDs or local file hashes without modifying source data.
2. Generate a tidy statistics table with explicit formulas, algorithms, seeds, versions, splits, and interval semantics.
3. Render only from the authorized raw observations and the statistics table.
4. Preserve the selected recipe ID/version, backend, environment, transformations, and export settings.
5. Keep labels and text vector-based where possible; rasterize only dense layers when needed.

If execution is not authorized, return the figure specification, data-preparation list, recipe, and QA plan only. Do not install libraries, read unspecified files, compute statistics, or create a plot.

## Run adversarial QA

Check the choice most likely to change the conclusion: group, scale, split, threshold, binning, interval, bandwidth, censoring, parameter range, clustering, missing-value encoding, layout seed, interpolation, or color limit. Record the result and author decision; do not silently choose the favorable view.

Verify:

- observation unit, sample count, pairing/hierarchy, and missingness;
- labels, units, transformations, baselines, and uncertainty semantics;
- leakage-free evaluation and threshold/calibration separation;
- color-vision and grayscale readability with a non-color redundant channel;
- final physical size, font size, cropping, panel order, and caption completeness;
- static/source-data agreement and no local image manipulation;
- self-contained HTML with an equivalent static view when interaction is justified;
- source and software license provenance.

## Export without overclaiming

Use `journal-neutral` unless a current target-journal profile was checked. Treat Nature-family dimensions and formatting as a versioned profile, not a universal rule. Recheck the target journal before submission.

Plot creation does not authorize data edits, downloads, uploads, experiments, simulations, training, submission, publication, or external communication.
