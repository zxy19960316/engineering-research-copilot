# S1.1 Agent-host projection implementation plan

## Goal

Publish the same S1 research-workbench Skill cluster to Codex, Claude Code, OpenCode, Hermes, OpenClaw, and GitHub Copilot without creating divergent research rules or weakening evidence and permission gates.

## Work sequence

1. Verify each host's official Skill locations, discovery behavior, explicit invocation, packaging options, and refresh semantics.
2. Freeze a machine-readable host matrix and a portable-source contract.
3. Add native Codex and Claude plugin manifests bound to one version.
4. Implement a standard-library installer with dry-run, multi-host projection, exact-inventory validation, fail-closed overwrite behavior, explicit rollback-capable upgrade, and safe archive extraction.
5. Add host-neutral fallback instructions for shared sibling references.
6. Forward-test every host projection in isolated temporary roots without mutating real host configuration.
7. Run all S1 and historical non-M4 acceptance gates; verify no `evals/m4/**` change.
8. Integrate current `origin/main`, publish a pull request, wait for exact-head checks, and merge only when green.

## Boundaries

- Do not install into the operator's real host directories during repository acceptance.
- Do not claim end-to-end runtime invocation for host executables that are absent.
- Do not mutate Hermes configuration to simulate project-level support.
- Do not rewrite portable Skill frontmatter per host.
- Do not touch or run frozen M4.2 evaluation artifacts.
