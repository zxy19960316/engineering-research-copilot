# Engineering Research Copilot Project Plan

## Objective

Deliver a small engineering-general research Skill package for master's students through early-stage doctoral researchers. Prioritize accurate paper matching, interdisciplinary direction selection, executable route decisions, and method coaching.

## Architecture

- Development repository: `D:\engineering-research-copilot`
- Installable package: `skills/engineering-research-copilot/`
- One root Skill routes to one-level reference modules.
- Host-provided scholarly/web tools perform discovery; the Skill enforces metadata verification and evidence labeling.
- Research Retrieval Calibrator may be connected later as an optional backend but is not bundled.

## Milestones

### M0 — Bootstrap and frozen core contracts

Create repository governance, standard Skill skeleton, confirmed product specification, thin root router, four core protocols, and local validation evidence.

Acceptance:

- Standard Skill validator passes.
- No template placeholders remain in the installable Skill.
- No remote, external service, model dependency, or RRC code is added.
- The Git baseline contains only initialization files.

### M1 — Two-round paper calibration and evidence map

Implement the adaptive brief, verified 15–20-paper candidate pool, first-round eight-paper map, feedback delta, second-round five-to-six-paper map, and text fallback.

Acceptance:

- Zero fabricated citation identifiers in adversarial fixtures.
- Conflicted citations cannot enter recommendations.
- Graph size represents user fit rather than citation count.
- Feedback reasons change the next query and are visible to the user.

### M2 — Direction decision and route gate

Implement the three-direction portfolio, transfer-evidence tiers, minimum decisive tests, user-confirmation gate, and executable experiment/simulation route output.

Acceptance:

- Direct target-method precedent is not required for a transfer-supported direction.
- Speculative analogies cannot be presented as established conclusions.
- Full route generation is blocked until direction status is `user_confirmed`.

### M3 — Engineering method cards

Add concise cards for experiment/measurement/UQ, modeling/simulation/VVUQ, control/optimization/system identification, signal/diagnostics, data/ML/hybrid methods, and reliability/safety/risk. Add nuclear engineering × machine learning as the first deep domain pack.

Acceptance:

- Each card states assumptions, minimum resources, baselines, failure modes, uncertainty handling, and stop conditions.
- Source ledger entries state what each source supports and does not support.

### M4 — Cross-engineering forward evaluation

Evaluate twelve fresh cases across nuclear, mechanical, electrical, automation, computer/data, and multiphysics research. Compare no-Skill, full-Skill, and ablated variants.

Acceptance:

- Full Skill improves direction feasibility, mismatch detection, and plan executability.
- No fabricated citations or unauthorized side effects occur.
- Failures remain visible and drive general fixes rather than case-specific prompt patches.

### M5 — Competition package

Freeze the installable Skill, add only required submission explanations and examples outside the Skill folder, demonstrate nuclear × ML plus one non-nuclear case, and verify local-tool use without Qingxiaoda platform APIs.

Acceptance:

- Submission contains the required Skill files and stays within the competition size rules.
- The demo does not require a private service, model download, or interactive web application.

## Deferred work

- RRC service integration, CNKI connectors, multi-agent runtime, vector database, interactive graph UI, model downloads, and deployment are outside M0–M5 unless separately authorized.
