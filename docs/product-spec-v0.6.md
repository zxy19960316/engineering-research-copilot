# Engineering Research Workbench Product Specification v0.6

## Successor extension

Extend the accepted S1 Skill-cluster foundation with portable projections for Codex, Claude Code, OpenCode, Hermes, OpenClaw, and GitHub Copilot CLI. Keep one normative cluster of nine Agent Skills. Treat host adaptation as packaging, discovery, invocation, and path compatibility; do not fork research governance or rewrite Skill instructions per host.

This extension remains separate from the terminal M4.2 evaluation. It does not retry, repair, consume, reinterpret, or modify any M4 authorization, claim, execution, result, terminal, or frozen evaluation artifact.

## Portable source contract

- Keep every `SKILL.md` valid under the open Agent Skills frontmatter contract.
- Require `name` to match the Skill directory and keep path-derived IDs lowercase kebab-case.
- Keep host-only metadata out of the portable source unless it is required by the workflow itself.
- Keep `agents/openai.yaml` as an optional Codex presentation/policy adapter that other hosts may ignore.
- Keep one hand-edited canonical nine-Skill cluster. Generate host projections deterministically; never edit the canonical source during projection.
- Keep shared governance and handoff documents normative only in `engineering-research-copilot/references/`.
- Make every installed Skill self-contained. Copy each referenced normative file byte-for-byte into `references/shared/`, rewrite only its location in the projected `SKILL.md`, and record source and projected SHA-256 values.
- For Hermes only, replace the projected frontmatter description with the unique matrix-bound value of at most 60 characters. Record the change and never change permissions or research instructions.

## Host projection contract

Bind the supported roots, invocation forms, refresh behavior, native package locators, and official sources in `agent-hosts.json`. Resolve user and project roots at install time.

Support:

1. Codex user and project Agent Skills roots plus `.codex-plugin/plugin.json`.
2. Claude Code user and project standalone roots plus `.claude-plugin/plugin.json` for namespaced plugin loading.
3. OpenCode user and project native Skill roots plus a repository-root `opencode.json` source adapter. Treat stable native `skill`-tool loading as confirmed; do not claim slash invocation without a fixed-version runtime test.
4. Hermes user root. Fail closed for project scope because Hermes requires an explicit `skills.external_dirs` configuration and the installer is not authorized to mutate host configuration.
5. OpenClaw user managed root and project `.agents/skills` root.
6. GitHub Copilot CLI user and project roots retained from the published predecessor.

Do not claim a host runtime was exercised when its executable is absent. Static compatibility, isolated projection tests, native manifest validation, and real host invocation are distinct evidence levels.

## Installer contract

Provide one standard-library Python installer that:

- accepts one or more host names or `all`;
- supports local offline source and a repository download fallback;
- validates the exact nine-Skill inventory, portable frontmatter, shared normative references, and synchronized native manifest versions before writes;
- prints a deterministic JSON dry-run plan without creating target directories;
- preflights every target before any projection write;
- stages the whole cluster per target root before activation;
- refuses existing target Skills by default;
- upgrades only with explicit `--upgrade`, backing up exact target Skill directories and rolling them back on failure;
- deduplicates physical roots shared by selected hosts;
- never rewrites the canonical `SKILL.md`, host configuration, permissions file, or user research material;
- limits projected `SKILL.md` changes to audited cross-reference locations and the Hermes description override, and emits `projection-manifest.json` with an empty `permission_changes` list;
- rejects unsafe ZIP paths and source-tree installation targets.

## Invocation and authority

Explicit host invocation loads a workflow. Description-based host discovery may also select a focused Skill. Neither path confirms a research direction, generates execution authority, or strengthens the shared permission ledger.

Keep file writes, downloads, uploads, experiments, simulations, training, publication, and external communication as separately scoped authorizations after activation. Keep review and audit read-only by default.

## Acceptance

- Both native plugin manifests and `agent-hosts.json` bind version `0.6.0` and the same cluster identity; `opencode.json` points only to the canonical `./skills` root.
- All nine canonical Skill manifests validate without host-specific frontmatter.
- Isolated user projections contain all nine self-contained Skill trees at every documented host root; copied shared references match canonical bytes and every generated change is hash-bound.
- Hermes projections use the exact unique short descriptions declared in `agent-hosts.json`; every other host keeps the canonical frontmatter.
- Project projections deduplicate shared physical roots and reject unsupported Hermes project scope before writes.
- Dry-run, default refusal, explicit upgrade, staging cleanup, shared-reference resolution, and unsafe archive rejection pass focused tests.
- Existing S1 graph, figure, evidence, permission, readiness, review, and handoff tests remain green.
- Standard Skill validators pass for all nine Skills.
- `evals/m4/**` has no diff and no M4 evaluator, experiment, simulation, training, publication, upload, or external communication is run as part of local acceptance.
