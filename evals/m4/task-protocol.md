# M4.0 Independent Task Protocol

Run a task only when a separate authorization artifact sets `fresh_execution_authorized=true`, binds an exact model version and tool implementation, and preserves every preparation hash. Until then, every planned task must not be launched.

Use one independent fresh context for exactly one task ID. Supply the common protocol, the case's exact `user_input`, and only that arm's rendered Skill instructions. Arm N receives no Skill instructions. Keep the model version, read-only tool profile, search budget, context ceiling, output ceiling, wall-clock boundary, user input, and scoring contract identical across all five arms.

Do not read another M4 task result, judge score, arm output, or execution transcript. Do not disclose the arm ID to a judge. Do not write to user files, start services, download models, upload research material, or execute a proposed experiment, simulation, training, deployment, or control action.

Finalize exactly once. Do not retry or repair a failed, malformed, incomplete, timed-out, or protocol-invalid task. Preserve the original final bytes and terminal state. Stop the current preregistered domain batch after an infrastructure or protocol failure; a successor revision may be prepared only without changing observed evidence.

Return one UTF-8 JSON object conforming to `schemas/task-result.schema.json`. Keep citations empty unless every identifier and metadata field was verified through an allowed read-only source in that same task. Label evidence level, transfer hypotheses, unsupported claims, direction confirmation state, resource ceilings, uncertainty sources, stop/pivot authority, and side effects explicitly.

The six domain batches contain two cases and five arms each. Batch boundaries limit fault radius only. They do not authorize changing later cases, prompts, variants, rubric, randomization, thresholds, or budgets after any result is observed.
