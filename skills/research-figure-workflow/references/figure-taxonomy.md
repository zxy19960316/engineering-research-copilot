# Scientific Figure Taxonomy

Choose a family from the scientific decision, not from visual fashion.

| Family | Primary question | Minimum view | Fail-closed trigger |
|---|---|---|---|
| `regression_diagnostics` | Does the fitted relationship generalize and where does the error structure fail? | observed-versus-fitted plus residual diagnostics | evaluation split or residual definition unknown |
| `agreement_concordance` | Are two methods close enough to be interchangeable within an external tolerance? | Bland-Altman bias and limits of agreement with uncertainty | pairing/repetition or acceptable difference unknown |
| `calibration_reliability` | Do predicted probabilities match observed frequencies? | reliability curve, bin counts/distribution, interval | calibration and evaluation split or interval unknown |
| `uncertainty_interval` | What uncertainty surrounds an estimate and what does the interval mean? | point-interval or forest display | interval type or level unknown |
| `distribution_estimation` | What is the observation-level distribution and effect magnitude? | raw points/ECDF plus effect estimate and interval | observation unit or pairing declaration unknown |
| `classification_curves` | How do ranking, precision-recall, and decision thresholds behave? | ROC and PR with prevalence baseline; threshold table | test split or prevalence unknown |
| `survival_time_event` | How does event-free probability or cumulative incidence change over time? | KM or cumulative-incidence curve with risk table | time origin, event, censoring, or competing-risk rule unknown |
| `sensitivity_ablation` | Which parameters/components drive the outcome under a valid design? | S1/ST or paired ablation deltas with intervals | input design or seed/fold alignment unknown |
| `heatmap_multivariate` | What high-dimensional pattern exists under declared transform and ordering? | heatmap with color scale, missing code, and annotations | transform, missingness, distance/linkage, or order unknown |
| `network_relationships` | What entities and scoped relations form the network? | filtered static network with legend and recorded layout seed | edge semantics, filtering, or layout seed unknown |
| `field_multiphysics` | How do scalar/vector fields and model-reference differences vary in space/time? | reference, model, and difference using shared coordinates/scales | coordinates, units, grid/interpolation, or shared scale unknown |

Use recipe-specific adjacent alternatives for complementary evidence. An adjacent plot cannot replace the primary statistical design. Use the recorded minimum falsification view to expose the most likely alternative explanation before polishing a multi-panel figure.
