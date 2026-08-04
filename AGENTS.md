# Engineering Research Copilot Repository Rules

These rules apply to the entire repository.

## Scope

- Build one lightweight, installable root Skill at `skills/engineering-research-copilot/`.
- Keep the existing Research Retrieval Calibrator independent. Treat it only as a future optional retrieval backend.
- Execute only the active milestone in `STATUS.md`. Do not start later method-corpus, runtime, deployment, or platform-integration work opportunistically.
- Keep development plans and evaluation artifacts outside the installable Skill folder.

## Skill design

- Keep `SKILL.md` concise and below 500 lines.
- Place detailed rules one level deep under `references/`; link every loadable reference directly from `SKILL.md`.
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
- Forward-test with fresh context only after the relevant workflow is implemented.
- Preserve failing evidence; do not relabel partial, offline, or abstract-only checks as real completion.
- Review `git status --short` and stage explicit paths. Do not configure a remote or push unless the user requests it.
