# Scientific Figure Evidence Register

This register summarizes the selected sources used by `figure-recipes.v1`. The full read-only survey, figure/caption anchors, popularity snapshots, and 37-source table are stored outside the installable Skill at `docs/research/2026-08-14-scientific-figure-workflow-survey.md`.

## Evidence rules

- Treat GitHub stars and indexed citation counts as dated discovery signals only. Do not score recipe quality or applicability with them.
- Use publisher figures and captions as visual precedents with exact anchors. Do not package article panels, screenshots, PDFs, source data, fonts, or publisher styles.
- Use official software documentation for API behavior and the current repository license for software reuse. Recheck the license at the version or commit actually installed.
- Keep method support, visual precedent, software implementation, journal specification, and license provenance as separate source roles.

## Selected primary anchors

| Source ID | Evidence | Use | Reuse boundary |
|---|---|---|---|
| `nature-figure-spec` | Nature Research Figure Guide, full official guidance | versioned Nature-family export profile | summarize and link; recheck before submission |
| `nature-image-integrity` | Nature Research Figure Guide, full official guidance | image-integrity blocking checks | do not copy page media |
| `statsmodels-regression` | official software documentation | regression and influence diagnostics | BSD-3-Clause implementation dependency |
| `bland-altman-1986` | PubMed identity and abstract | agreement question and method identity | abstract-level method summary only |
| `statsmodels-agreement` | official software documentation | basic mean-difference plot | does not solve repeated-measure LoA |
| `sklearn-calibration` | official software documentation | reliability curve and bin behavior | BSD-3-Clause implementation dependency |
| `error-bars-nmeth` | inspected Nature Methods article/figures | interval and error-bar semantics | link and summarize; no bundled panel |
| `dabest-method` | inspected Nature Methods article plus official tutorial | raw data, effect size, and interval view | article and software licenses remain separate |
| `sklearn-roc-pr` | official software documentation | ROC, PR, thresholds, AP semantics | BSD-3-Clause implementation dependency |
| `saito-pr-roc` | inspected PLOS article | PR evidence under class imbalance | open-license attribution still required for reuse |
| `lifelines-km` | official software documentation | KM input, censoring, delayed entry, interval | MIT implementation dependency |
| `survival-nmeth` | inspected Nature Methods article/figures | censoring and KM visual method | link and summarize; inspect credit lines before reuse |
| `salib-docs` | official software documentation | Sobol/Morris/FAST design and outputs | MIT implementation dependency |
| `complexheatmap-book` | official project documentation | annotations and complex heatmap layout | MIT software; book content summarized only |
| `networkx-drawing` | official software documentation | network layout and export boundary | BSD-3-Clause implementation dependency |
| `matplotlib-fields` | official software documentation | contour, vector, and stream field inputs | Matplotlib License implementation dependency |
| `pyvista-streamlines` | official software documentation | optional three-dimensional field companion | MIT software; do not bundle example data without review |
| `crameri-colour` | inspected Nature Communications article | perceptual color and rainbow/red-green risks | link and summarize; inspect third-party credits |
| `plotly-offline` | official software documentation | optional self-contained HTML | MIT software; forbid CDN mode |

The recipe asset stores these URLs, evidence levels, source roles, checked date, and license notes in machine-readable form. A source entry supports only its stated role and does not establish correctness on the user's target data.
