# Engineering Research Copilot Repository Rules

These rules apply to the entire repository.

## Scope

- Preserve the accepted v0.4 root Skill at `skills/engineering-research-copilot/` as the umbrella and compatibility router.
- For the explicitly authorized S1 successor, package the repository as one plugin containing that umbrella plus focused Skills for direction evidence, literature evidence, method transfer, manuscript work, cross-review, data comparison, adversarial evidence audit, and scientific figures.
- For the explicitly authorized S1.1 extension, project that same nine-Skill source to Codex, Claude Code, OpenCode, Hermes, OpenClaw, and GitHub Copilot. Keep host paths, invocation facts, and packaging adapters outside the Skill instructions when possible.
- Keep the existing Research Retrieval Calibrator independent. Treat it only as a future optional retrieval backend.
- Execute only the active milestone in `STATUS.md`. Treat the terminal M4.2 evaluation as immutable predecessor evidence; S1 is not a retry, repair, continuation, or relabeling of it.
- Do not start later method-corpus, MCP/runtime, deployment, publication, or platform-integration work opportunistically.
- Keep development plans and evaluation artifacts outside the installable Skill folder.

## Skill design

- Keep every `SKILL.md` concise and below 500 lines.
- Place detailed rules one level deep under `references/`; link every loadable reference directly from `SKILL.md`.
- Keep shared evidence, permission, readiness, review, and handoff rules in one normative source and link it directly from every consuming focused Skill.
- Do not fork or rewrite the normative research workflow per Agent host. Treat generated host copies as hash-bound, self-contained projections of the same validated source.
- Do not add README, changelog, installation guide, book text, paper full text, model weights, caches, or generated evidence maps to the Skill.
- Add scripts only for deterministic repeated work. Scripts must run without network access unless a later milestone explicitly authorizes a networked provider.
- Use imperative instructions in Skill files.

## Evidence integrity

- Separate discovery from verification. Never invent or infer a DOI, title, author list, publication status, or citation identifier.
- Block conflicted or unresolved citations from recommendations.
- Label metadata-, abstract-, and full-text-level reasoning explicitly.
- Allow verified preprints as method or exploration evidence, but never as the sole basis for a main direction or safety-related conclusion.
- Label transfer reasoning as a hypothesis until a target-domain decisive test supports it.

## User control and safety

- Keep audits read-only by default.
- Do not write back to user files, start services, download models, upload research materials, or execute arbitrary commands without an explicit request.
- Require user direction confirmation before generating a full experimental or simulation route.
- Show inherited, rejected, reset, and newly added constraints before a new search branch.

## Validation and Git

- Run the standard Skill validator after changes to `SKILL.md` or its metadata.
- Validate native host manifests, exact projection paths, byte-identical shared-reference copies, audited projection rewrites, and rollback behavior after host-adapter changes. Distinguish static compatibility from a real host invocation.
- Forward-test with fresh context only after the relevant workflow is implemented.
- Preserve failing evidence; do not relabel partial, offline, or abstract-only checks as real completion.
- Review `git status --short` and stage explicit paths. Do not configure a remote or push unless the user requests it.
