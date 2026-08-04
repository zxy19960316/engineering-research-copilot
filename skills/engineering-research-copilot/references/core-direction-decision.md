# Direction Decision and Transfer Evidence

Use this file to compare research directions, reason about interdisciplinary transfer, define minimum decisive tests, and gate detailed route planning.

## Contents

- Return a bounded portfolio
- Pass hard gates first
- Permit innovation through transfer evidence
- Assign an evidence tier
- Compare feasible directions
- Define a minimum decisive test
- Require user confirmation

## Return a bounded portfolio

Return exactly these formal positions when evidence permits:

1. One provisional main direction optimized for current feasibility and evidence coverage.
2. One adjacent alternative that changes only one important problem, method, or data axis.
3. One transfer exploration direction that changes at least two axes or introduces a cross-disciplinary transfer.

Optionally add at most two unranked high-risk ideas in a separate section. Do not use weak variations of the same idea to fill the portfolio.

## Pass hard gates first

Require:

- verified evidence that the target problem, constraint, or engineering need exists;
- accessible or generatable data/observations;
- a feasible validation or falsification path;
- no unresolved resource, time, safety, ethics, or compliance blocker;
- verified metadata for core papers;
- an explicit map of concepts, units, scales, boundary conditions, and assumptions for cross-disciplinary work.

Do not allow a weighted score to override a failed hard gate.

## Permit innovation through transfer evidence

Do not require proof that the exact method has already succeeded in the exact target field. Build a transfer case from:

1. `target_problem_evidence`: show that the target need and constraints are real.
2. `source_success_evidence`: show verified success of the theory or method in a relevant source domain, mechanism, or data regime.
3. `transfer_compatibility`: compare inputs, outputs, physical mechanism, statistical structure, units, scales, boundary conditions, data volume, noise, and distribution shift.
4. `anti_transfer_factors`: identify differences that could invalidate the analogy.
5. `minimum_decisive_test`: test the most fragile transfer assumption at low cost.

Require similarity on dimensions that affect method success. Do not accept similar field names, titles, or the generic fact that both methods process data.

## Assign an evidence tier

| Tier | Basis | Allowed language |
|---|---|---|
| `established-in-target` | Direct target or highly equivalent validation exists | "Direct evidence supports applicability" |
| `transfer-supported` | Target problem, source success, compatibility map, anti-transfer analysis, and decisive test exist | "Recommended for priority validation" |
| `mechanism-plausible` | Principle or data compatibility is plausible but bridge evidence is incomplete | "Divergent exploration suggestion" |
| `speculative` | Mainly analogy or creative association | "High-uncertainty idea; excluded from formal ranking" |

Permit `transfer-supported` as the provisional main direction with at most medium confidence. Upgrade confidence only after target-domain validation. Keep `mechanism-plausible` and `speculative` out of primary conclusions.

## Compare feasible directions

Score 0–4 only after hard gates pass, using user-adjustable weights:

| Dimension | Default weight |
|---|---:|
| Scientific or engineering value | 15 |
| Gap and evidence quality | 15 |
| Data and resource fit | 20 |
| Validation and falsifiability | 15 |
| Method maturity | 10 |
| Time to first decisive signal | 10 |
| Interdisciplinary interface quality | 10 |
| Safety, ethics, and compliance | 5 |

For every score, show the evidence, confidence, unknowns, and new information that could change it. Present the total as a decision aid, not objective truth.

## Define a minimum decisive test

Include:

```yaml
direction: "Candidate direction"
hypothesis: "Falsifiable hypothesis"
minimum_decisive_test:
  inputs: []
  baseline: ""
  steps: []
  primary_metric: ""
  success_threshold: ""
  stop_condition: ""
  pivot_condition: ""
  expected_time: ""
  required_resources: []
evidence:
  target_problem: []
  source_method: []
  transfer_bridge: []
  counter_or_limit: []
unknowns: []
confidence: "low|medium|high"
```

Use measurable thresholds when the domain permits. When a meaningful numerical threshold cannot yet be justified, state what pilot data is needed to set it.

## Require user confirmation

After round two:

1. Show the updated paper map and exact citation index.
2. Show three direction cards with evidence, risks, unknowns, and decisive tests.
3. Mark the system recommendation `provisional`.
4. Ask the user to confirm, modify, or reject a direction.
5. Generate a detailed research route only when status becomes `user_confirmed`.

If the user rejects the direction, return to the feedback and rollback protocol. Do not quietly mutate the old direction or retain its score.
