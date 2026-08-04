# Engineering Research Copilot Initialization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a clean, locally validated project and Skill baseline for an evidence-grounded engineering research workflow without modifying the existing RRC repository.

**Architecture:** Use a development repository at `D:\engineering-research-copilot` and keep the installable deliverable under `skills/engineering-research-copilot/`. The Skill uses a thin root router and one-level reference files; RRC remains an optional future retrieval backend rather than a bundled dependency.

**Tech Stack:** Markdown, YAML, Mermaid, Python 3.13 for local validation scripts, Git.

## Global Constraints

- Do not modify or copy runtime code from the existing `research-retrieval-calibrator` repository.
- Do not configure a remote, call external model services, download model weights, or start background services.
- Keep `SKILL.md` below 500 lines and load detailed rules from one-level `references/` files only when needed.
- Use exactly one installable root Skill for the first competition package.
- Treat verified metadata, citation conflicts, stage gates, and user-confirmed direction as low-freedom hard rules.
- Treat migration hypotheses and divergent ideas as bounded suggestions, never as established target-domain conclusions.
- Do not add books, paper full text, caches, generated graphs, or credentials to Git.

---

### Task 1: Create repository governance baseline

**Files:**
- Create: `.gitignore`
- Create: `AGENTS.md`
- Create: `PROJECT_PLAN.md`
- Create: `STATUS.md`

**Interfaces:**
- Consumes: user-confirmed scope and D-drive project location.
- Produces: repository-wide boundaries, milestone order, and a single active bootstrap status.

- [ ] **Step 1: Initialize local Git metadata**

Run: `git init --initial-branch=main`

Expected: an empty repository on branch `main`, with no remote configured.

- [ ] **Step 2: Add narrow ignore rules**

Create `.gitignore` with Python caches, virtual environments, generated evidence maps, local exports, credentials, and editor metadata excluded.

- [ ] **Step 3: Add repository governor**

Create `AGENTS.md` that requires explicit milestone scope, verified citations, read-only audits by default, no silent preprint/DOI inference, no external service setup during bootstrap, and validation before status advancement.

- [ ] **Step 4: Add milestone plan and status**

Create `PROJECT_PLAN.md` with milestones M0 through M5 and `STATUS.md` with M0 bootstrap as the only active milestone.

- [ ] **Step 5: Verify repository boundaries**

Run: `git remote -v`

Expected: no output.

Run: `git status --short`

Expected: only the new initialization files are untracked.

### Task 2: Initialize the standard Skill skeleton

**Files:**
- Create: `skills/engineering-research-copilot/SKILL.md`
- Create: `skills/engineering-research-copilot/agents/openai.yaml`
- Create: `skills/engineering-research-copilot/references/`
- Create: `skills/engineering-research-copilot/scripts/`

**Interfaces:**
- Consumes: Skill name `engineering-research-copilot` and confirmed one-root-router architecture.
- Produces: a discoverable Skill folder accepted by the standard Skill validator.

- [ ] **Step 1: Run the standard initializer**

Run:

```powershell
python 'C:\Users\94310\.codex\skills\.system\skill-creator\scripts\init_skill.py' engineering-research-copilot `
  --path 'D:\engineering-research-copilot\skills' `
  --resources scripts,references `
  --interface 'display_name=Engineering Research Copilot' `
  --interface 'short_description=Evidence-grounded engineering research workflows' `
  --interface 'default_prompt=Use $engineering-research-copilot to find and verify papers, compare research directions, and plan an executable engineering study.'
```

Expected: `SKILL.md`, `agents/openai.yaml`, `references/`, and `scripts/` are created without examples.

- [ ] **Step 2: Inspect generated metadata**

Run: `Get-Content skills\engineering-research-copilot\agents\openai.yaml`

Expected: all strings are quoted and the default prompt explicitly mentions `$engineering-research-copilot`.

### Task 3: Freeze the confirmed product specification

**Files:**
- Create: `docs/product-spec-v0.4.md`
- Create: `skills/engineering-research-copilot/references/core-citation-integrity.md`
- Create: `skills/engineering-research-copilot/references/core-paper-map.md`
- Create: `skills/engineering-research-copilot/references/core-direction-decision.md`
- Create: `skills/engineering-research-copilot/references/core-feedback-rollback.md`

**Interfaces:**
- Consumes: PREPRINT-01, TRANSFER-01, DIRECTION-PORTFOLIO-01, PAPER-PORTFOLIO-01, PAPER-MAP-01, GRAPH-RENDER-01, INTAKE-01, and DIRECTION-GATE-01.
- Produces: a versioned specification and four directly loadable core rule files.

- [ ] **Step 1: Write the product specification**

Record the complete workflow from adaptive research brief through two-round retrieval, evidence map feedback, direction confirmation, route planning, method coaching, evidence audit, and manuscript red-team handoff.

- [ ] **Step 2: Write citation-integrity rules**

Require real DOI/arXiv/PMID identifiers, authoritative metadata checks, explicit verification states, no guessed DOI, no conflicted citation in recommendations, and preprint evidence limits.

- [ ] **Step 3: Write paper-map rules**

Define node size as user-fit rather than citation count; define evidence-role colors, relation labels, abstract/full-text basis levels, dashed transfer inference, and Mermaid/text/SVG fallback.

- [ ] **Step 4: Write direction-decision rules**

Define one main direction, one adjacent alternative, one transfer exploration direction, up to two unranked high-risk ideas, evidence tiers, minimum decisive tests, and the user-confirmation gate.

- [ ] **Step 5: Write feedback and rollback rules**

Define paper dissatisfaction, direction dissatisfaction, citation distrust, constraint change, and full reset branches; carry forward only visible, versioned constraints and rejection reasons.

### Task 4: Replace the template with a thin usable router

**Files:**
- Modify: `skills/engineering-research-copilot/SKILL.md`

**Interfaces:**
- Consumes: four core reference files from Task 3.
- Produces: root routing instructions that load only the references required by the current research stage.

- [ ] **Step 1: Write valid frontmatter**

Use only `name` and `description`, with triggers covering engineering literature search, research direction selection, route planning, method coaching, evidence audit, and manuscript red-team review.

- [ ] **Step 2: Define the stage router**

Route to adaptive intake, paper calibration, direction decision, route planning, method coaching, evidence audit, or handoff. Always load citation-integrity rules whenever external literature is used.

- [ ] **Step 3: Define hard stop conditions**

Stop recommendation on unresolved citation conflicts; stop detailed route generation before user direction confirmation; downgrade claims when only abstract-level or transfer evidence is available.

- [ ] **Step 4: Keep permissions narrow**

Default to read-only input handling, host-provided web search, Mermaid output, and no service startup, model download, arbitrary shell execution, or write-back without user request.

### Task 5: Validate and freeze the initialization baseline

**Files:**
- Modify: `STATUS.md`

**Interfaces:**
- Consumes: initialized Skill and repository baseline.
- Produces: validated M0 initialization evidence and a clean local commit.

- [ ] **Step 1: Run the standard Skill validator**

Run:

```powershell
python 'C:\Users\94310\.codex\skills\.system\skill-creator\scripts\quick_validate.py' 'D:\engineering-research-copilot\skills\engineering-research-copilot'
```

Expected: `Skill is valid!`

- [ ] **Step 2: Check for forbidden placeholders and files**

Run:

```powershell
Get-ChildItem -Recurse -File | Select-String -Pattern 'TODO|TBD|fill in' -CaseSensitive
```

Expected: no placeholder inside the installable Skill; any literal examples in this plan are reviewed separately.

- [ ] **Step 3: Record status**

Set M0 to complete only after validation succeeds; keep M1 evidence-corpus construction not started.

- [ ] **Step 4: Review exact commit scope**

Run: `git status --short`

Expected: only initialization baseline files under this new project.

- [ ] **Step 5: Create the local baseline commit**

Run:

```powershell
git add .gitignore AGENTS.md PROJECT_PLAN.md STATUS.md docs skills
git commit -m "chore: initialize engineering research copilot"
```

Expected: one local root commit; no remote configured and no push performed.
