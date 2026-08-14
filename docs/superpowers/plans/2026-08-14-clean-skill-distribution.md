# Clean Skill Distribution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic v0.7.0 release artifact that contains only the installable nine-Skill cluster and its five required root adapter files, while preserving all development, test, and historical evidence in the source repository.

**Architecture:** Keep `skills/**` and the existing host manifests as the only hand-edited runtime source. Add one standard-library release builder outside the Skill tree; it selects tracked files through an exact allowlist, writes a byte-level manifest, and creates a cross-platform deterministic ZIP. Teach the existing installer to verify that manifest when it is present, while retaining source-repository installation when it is absent.

**Tech Stack:** Python 3.10+ standard library, `unittest`, JSON, SHA-256, ZIP_STORED, Git index enumeration, existing Skill and plugin validators.

**Execution record:** Implemented and validated locally on 2026-08-14. On 2026-08-15 the user separately authorized committing this S2 change set, pushing its feature branch, opening its pull request, and merging that pull request into `main`. Release upload, marketplace update, and real-host installation remain unauthorized. Checkboxes below preserve the original executable plan rather than acting as the status authority; use `STATUS.md` for exact results and hashes.

## Global Constraints

- Start from `origin/main` commit `8523f95ef4a823ab29eda5bd025b0a6e045d0d04` on branch `codex/clean-skill-distribution`.
- Keep one canonical Skill source under `skills/**`; never create a tracked release copy of those files.
- Set the cluster and native plugin version to exact semantic version `0.7.0`.
- Allow only `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`, `agent-hosts.json`, `install-skill.py`, `opencode.json`, and tracked files under the nine required `skills/<name>/**` directories into the payload, excluding the exact declared `source_only_paths`.
- Add only generated `release-manifest.json` to the ZIP; exclude `evals/**`, `tests/**`, `docs/**`, `.github/**`, `AGENTS.md`, `PROJECT_PLAN.md`, `README.md`, `STATUS.md`, the builder, Git metadata, caches, and every untracked file.
- Generate release bytes without network access, timestamps, source commit identifiers, absolute paths, host-specific separators, or environment-dependent compression.
- Keep `evals/m4/**` and `tests/test_m4*.py` byte-identical to baseline `c21c24e079631d2396a3989045c9f0945e17c24e`.
- Do not install into real host roots, modify host configuration, publish a release, upload an artifact, commit, push, open a pull request, or merge without separate authority.
- Keep the repository license decision explicit and unresolved; a local artifact is not a public software release.

---

### Task 1: Freeze the clean-release contract with failing tests

**Files:**
- Create: `tests/test_clean_release.py`
- Read: `agent-hosts.json`
- Read: `.codex-plugin/plugin.json`
- Read: `.claude-plugin/plugin.json`
- Read: `install-skill.py`

**Interfaces:**
- Consumes: canonical repository root and `agent-hosts.json.required_skills`.
- Produces: executable expectations for `build-release.py --check`, deterministic archive construction, `release-manifest.json`, extracted-package installation, tamper rejection, and version `0.7.0`.

- [ ] **Step 1: Write the builder command helper and exact top-level allowlist**

```python
RELEASE_TOP_LEVEL = {
    ".claude-plugin",
    ".codex-plugin",
    "agent-hosts.json",
    "install-skill.py",
    "opencode.json",
    "release-manifest.json",
    "skills",
}

def run_builder(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-X", "utf8", str(REPO_ROOT / "build-release.py"), *arguments],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
```

- [ ] **Step 2: Test read-only check mode and exact payload policy**

```python
def test_check_mode_is_read_only_and_reports_exact_policy(self):
    before = set(REPO_ROOT.iterdir())
    result = run_builder("--check", "--json")
    self.assertEqual(0, result.returncode, result.stderr)
    report = json.loads(result.stdout)
    self.assertEqual("valid", report["status"])
    self.assertEqual("0.7.0", report["cluster_version"])
    self.assertEqual(before, set(REPO_ROOT.iterdir()))
```

- [ ] **Step 3: Test deterministic ZIP bytes and forbidden-tree absence**

```python
def test_archive_is_byte_deterministic_and_contains_only_release_files(self):
    with tempfile.TemporaryDirectory() as temporary:
        first = Path(temporary) / "first.zip"
        second = Path(temporary) / "second.zip"
        self.assertEqual(0, run_builder("--output", str(first)).returncode)
        self.assertEqual(0, run_builder("--output", str(second)).returncode)
        self.assertEqual(first.read_bytes(), second.read_bytes())
        with zipfile.ZipFile(first) as bundle:
            names = bundle.namelist()
        self.assertEqual(RELEASE_TOP_LEVEL, {name.split("/", 1)[0] for name in names})
        self.assertFalse(any(name.startswith(("evals/", "tests/", "docs/", ".github/")) for name in names))
```

- [ ] **Step 4: Test manifest binding, extracted install, and tamper rejection**

```python
def test_manifest_hashes_every_payload_and_installer_rejects_tampering(self):
    with tempfile.TemporaryDirectory() as temporary:
        archive = Path(temporary) / "release.zip"
        self.assertEqual(0, run_builder("--output", str(archive)).returncode)
        extracted = Path(temporary) / "release"
        with zipfile.ZipFile(archive) as bundle:
            bundle.extractall(extracted)
        manifest = json.loads((extracted / "release-manifest.json").read_text(encoding="utf-8"))
        for entry in manifest["files"]:
            payload = (extracted / entry["path"]).read_bytes()
            self.assertEqual(entry["sha256"], hashlib.sha256(payload).hexdigest())
        clean = subprocess.run(
            [sys.executable, str(extracted / "install-skill.py"), "--source", str(extracted), "--agent", "codex", "--dry-run", "--json"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, clean.returncode, clean.stderr)
        skill = extracted / "skills" / "engineering-research-copilot" / "SKILL.md"
        skill.write_bytes(skill.read_bytes() + b"\n")
        tampered = subprocess.run(
            [sys.executable, str(extracted / "install-skill.py"), "--source", str(extracted), "--agent", "codex", "--dry-run"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(1, tampered.returncode)
        self.assertIn("release manifest hash mismatch", tampered.stderr.lower())
```

- [ ] **Step 5: Run the focused test to establish the expected red state**

Run: `python -X utf8 -m unittest tests.test_clean_release -v`

Expected: FAIL because `build-release.py` does not yet exist and versions remain `0.6.0`.

- [ ] **Step 6: Preserve the failure output in the implementation notes**

Record the exact exit code and failing test names in `STATUS.md`; do not call the failed run a partial pass.

### Task 2: Implement the deterministic allowlisted release builder

**Files:**
- Create: `build-release.py`
- Modify: `.gitignore`
- Modify: `.gitattributes`
- Test: `tests/test_clean_release.py`

**Interfaces:**
- Consumes: `agent-hosts.json`, Git index entries, canonical payload bytes, and an optional output path.
- Produces: `collect_payload(repository_root: Path) -> list[PayloadFile]`, `build_manifest(...) -> dict[str, object]`, `write_archive(...) -> None`, and CLI exit status `0` only for a valid clean payload.

- [ ] **Step 1: Define closed schemas and immutable payload records**

```python
RELEASE_SCHEMA = "engineering-research-clean-release.v1"
MANIFEST_FILENAME = "release-manifest.json"
ROOT_FILES = (
    ".claude-plugin/plugin.json",
    ".codex-plugin/plugin.json",
    "agent-hosts.json",
    "install-skill.py",
    "opencode.json",
)

@dataclass(frozen=True)
class PayloadFile:
    path: str
    payload: bytes
```

- [ ] **Step 2: Enumerate only Git-tracked canonical files**

```python
def tracked_paths(repository_root: Path, pathspecs: list[str]) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(repository_root), "ls-files", "-z", "--", *pathspecs],
        check=True,
        stdout=subprocess.PIPE,
    )
    return sorted(path.decode("utf-8") for path in result.stdout.split(b"\0") if path)
```

Require all root files, require exactly the matrix's nine Skill directories, reject symlinks, BOMs in `SKILL.md`, missing files, duplicate paths, and any path outside `ROOT_FILES` plus `skills/<required-name>/**`.

- [ ] **Step 3: Build the hash manifest from payload bytes**

```python
def build_manifest(matrix: dict[str, object], files: list[PayloadFile]) -> dict[str, object]:
    return {
        "schema_version": RELEASE_SCHEMA,
        "cluster_name": matrix["cluster_name"],
        "cluster_version": matrix["cluster_version"],
        "payload_policy": "git-tracked-explicit-allowlist",
        "file_count": len(files),
        "files": [
            {"path": item.path, "sha256": hashlib.sha256(item.payload).hexdigest(), "size": len(item.payload)}
            for item in files
        ],
    }
```

- [ ] **Step 4: Write deterministic ZIP entries**

Use sorted POSIX paths, `ZIP_STORED`, timestamp `(1980, 1, 1, 0, 0, 0)`, UTF-8 names, create-system `3`, mode `0755` only for root `install-skill.py` and `skills/*/scripts/*.py`, mode `0644` otherwise, and LF JSON with `sort_keys=True`. Refuse to overwrite an existing output unless `--force` is present. Write to a sibling temporary file and replace the final path only after the archive validates.

- [ ] **Step 5: Keep generated outputs untracked and byte-stable**

Add `/dist/` to `.gitignore` and add LF rules for `/build-release.py` and `/tests/test_clean_release.py` to `.gitattributes`.

- [ ] **Step 6: Run focused tests**

Run: `python -X utf8 -m unittest tests.test_clean_release -v`

Expected: manifest-independent tests pass; installer tamper verification remains red until Task 3.

### Task 3: Verify clean-release manifests before installation

**Files:**
- Modify: `install-skill.py`
- Test: `tests/test_clean_release.py`
- Test: `tests/test_agent_host_projection.py`

**Interfaces:**
- Consumes: optional root `release-manifest.json` with schema `engineering-research-clean-release.v1`.
- Produces: `validate_release_manifest(repository_root: Path) -> None`; source repositories without a release manifest retain existing behavior.

- [ ] **Step 1: Add strict optional-manifest validation**

```python
def validate_release_manifest(repository_root: Path) -> None:
    path = repository_root / RELEASE_MANIFEST_FILENAME
    if not path.exists():
        return
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != RELEASE_SCHEMA:
        raise ValueError("Unsupported release manifest schema")
```

Require closed top-level and file-entry key sets, POSIX relative paths, sorted unique entries, exact file count, exact filesystem file set excluding the manifest itself, exact byte sizes and SHA-256 values, and matching cluster name/version from `agent-hosts.json`. Reject symlinks and any unexpected file.

- [ ] **Step 2: Invoke manifest verification before canonical package validation**

Call `validate_release_manifest(package.repository_root)` as the first operation in `validate_package(package)` so tampered bytes fail before projection planning or writes.

- [ ] **Step 3: Prove source-repository compatibility**

Run: `python -X utf8 -m unittest tests.test_agent_host_projection -v`

Expected: all existing host projection tests pass with no release manifest present in the development root.

- [ ] **Step 4: Prove extracted-release integrity enforcement**

Run: `python -X utf8 -m unittest tests.test_clean_release -v`

Expected: clean archive dry-run passes and modified, missing, or extra payload files fail before installation writes.

### Task 4: Remove milestone-coupled runtime material without erasing historical evidence

**Files:**
- Modify: `agent-hosts.json`
- Modify: `build-release.py`
- Modify: `install-skill.py`
- Rewrite: `skills/engineering-research-copilot/references/core-paper-calibration.md`
- Rewrite: `skills/engineering-research-copilot/references/core-direction-decision.md`
- Rewrite: `skills/engineering-research-copilot/references/core-method-coaching.md`
- Modify: `skills/engineering-research-copilot/references/core-citation-integrity.md`
- Modify: `skills/engineering-research-copilot/references/core-paper-map.md`
- Modify: `skills/engineering-research-copilot/references/domain-nuclear-ml.md`
- Modify: `skills/engineering-research-copilot/references/method-control-optimization-identification.md`
- Modify: `skills/engineering-research-copilot/references/method-data-ml-hybrid.md`
- Modify: `skills/engineering-research-copilot/references/method-experiment-measurement-uq.md`
- Modify: `skills/engineering-research-copilot/references/method-modeling-simulation-vvuq.md`
- Modify: `skills/engineering-research-copilot/references/method-reliability-safety-risk.md`
- Modify: `skills/engineering-research-copilot/references/method-signal-diagnostics.md`
- Modify: `skills/engineering-research-copilot/references/core-paper-map.md`
- Test: `tests/test_clean_release.py`
- Test: `tests/test_agent_host_projection.py`

**Interfaces:**
- Consumes: five legacy machine-package scripts retained at their historical source paths for repository evidence replay.
- Produces: `agent-hosts.json.source_only_paths`, a milestone-neutral runtime reference set, one inline deterministic paper-map rendering contract, and projections/releases with zero legacy script members or milestone workflow tokens.

- [ ] **Step 1: Declare the five historical source-only scripts**

```json
"source_only_paths": [
  "skills/engineering-research-copilot/scripts/compose_m3_bundle.py",
  "skills/engineering-research-copilot/scripts/render_m1_map.py",
  "skills/engineering-research-copilot/scripts/validate_m1_bundle.py",
  "skills/engineering-research-copilot/scripts/validate_m2_direction_bundle.py",
  "skills/engineering-research-copilot/scripts/validate_m3_method_bundle.py"
]
```

Require sorted unique canonical paths under a required Skill. The release builder skips exactly these tracked files; the installer removes them from source-repository projections after copying. They remain unchanged in the development checkout.

- [ ] **Step 2: Write the failing semantic-purity tests**

Assert that the clean ZIP and every staged host projection omit all five `source_only_paths`. Scan emitted `.md` and `.py` runtime bytes for milestone tokens `M1`, `M1.2`, `M2`, `M2.1.1`, `M3`, `M3.1.1`, and `M4`; require zero matches. Confirm the development source still contains all five historical scripts.

- [ ] **Step 3: Replace milestone state machines with workflow-neutral guidance**

Rewrite paper calibration around `research_brief`, discovery records, verified identities, content observations, evidence gaps, feedback delta, and `ready`, `evidence_incomplete`, or `citation_conflict` readiness. Rewrite direction decision around main/adjacent/transfer portfolios, evidence tiers, relevance axes, falsification tests, user confirmation, and route readiness. Rewrite method coaching around exploratory versus direction-bound cards, assumptions, inputs, baselines, uncertainty, transfer risks, stop conditions, and explicit execution authority.

- [ ] **Step 4: Neutralize remaining method and citation vocabulary**

Replace milestone-bound phrases in citation, paper-map, six method-family, and nuclear-ML references with evidence-ledger, confirmed-direction, route-contract, and method-plan terms. Preserve existing scientific constraints and fail-closed behavior.

- [ ] **Step 5: Make the paper-map rendering contract milestone-neutral**

Specify both Mermaid and text-fallback rendering directly from the same ordered `nodes` and `edges` object in `core-paper-map.md`, including exact fallback forms and escaping rules. Keep the historical renderer byte-unchanged as a source-only development artifact; do not ship or reference it from runtime guidance.

- [ ] **Step 6: Rebuild and prove semantic purity**

Run: `python -X utf8 -m unittest tests.test_clean_release tests.test_agent_host_projection -v`

Expected: clean releases and source-based projections exclude all five historical scripts, runtime token scan reports zero M1–M4 workflow references, and historical source paths still exist.

### Task 5: Bind v0.7.0 across host manifests and document the development/release split

**Files:**
- Modify: `agent-hosts.json`
- Modify: `.codex-plugin/plugin.json`
- Modify: `.claude-plugin/plugin.json`
- Modify: `README.md`
- Modify: `PROJECT_PLAN.md`
- Modify: `STATUS.md`
- Test: `tests/test_clean_release.py`
- Test: `tests/test_research_skill_cluster.py`

**Interfaces:**
- Consumes: accepted clean-release implementation and current nine-Skill list.
- Produces: exact version `0.7.0`, a documented local build command, and an explicit S2 authority/boundary record.

- [ ] **Step 1: Bump the three version bindings**

Set `agent-hosts.json.cluster_version`, `.codex-plugin/plugin.json.version`, and `.claude-plugin/plugin.json.version` to `0.7.0`. Do not add a cachebuster because no installed marketplace plugin is being refreshed.

- [ ] **Step 2: Document the clean build without adding documentation inside a Skill**

Add a concise README section using:

```powershell
python .\build-release.py --check --json
python .\build-release.py --output .\dist\engineering-research-workbench-0.7.0.zip
```

State that the ZIP contains only the nine Skills, five root adapter files, and the generated manifest; extraction plus `install-skill.py --source <extracted-root>` is the supported local flow.

- [ ] **Step 3: Record S2 scope and authority**

Add `S2 — Clean Skill distribution` above the historical S1 plan. In `STATUS.md`, record local file-write/build/test authority, no commit/push/PR/merge/publication authority, no real host installation, and zero changes to frozen M4 artifacts.

- [ ] **Step 4: Re-run cluster and version tests**

Run: `python -X utf8 -m unittest tests.test_clean_release tests.test_research_skill_cluster tests.test_agent_host_projection -v`

Expected: every test passes and all version fields equal `0.7.0`.

### Task 6: Build and audit the local clean artifact

**Files:**
- Generate, ignored: `dist/engineering-research-workbench-0.7.0.zip`
- Validate: all nine `skills/*/SKILL.md`
- Validate: `.codex-plugin/plugin.json`

**Interfaces:**
- Consumes: completed v0.7.0 source and clean-release builder.
- Produces: one local deterministic ZIP, its SHA-256, member count, manifest file count, validation logs, and a clean tracked worktree apart from intended source edits.

- [ ] **Step 1: Validate all nine Skills**

Run the standard `quick_validate.py` once for every directory named by `agent-hosts.json.required_skills`.

Expected: `9/9` report `Skill is valid!`.

- [ ] **Step 2: Validate the Codex plugin manifest**

Run: `python -X utf8 C:\Users\94310\.codex\skills\.system\plugin-creator\scripts\validate_plugin.py D:\engineering-research-copilot`

Expected: exit `0` with a valid `engineering-research-workbench` manifest.

- [ ] **Step 3: Run focused regression suites**

Run: `python -X utf8 -m unittest tests.test_clean_release tests.test_research_skill_cluster tests.test_agent_host_projection tests.test_figure_recipe_workflow tests.test_render_direction_graph -v`

Expected: all focused tests pass with no network access or real host writes.

- [ ] **Step 4: Generate the ignored release ZIP and inspect every member**

Run: `python -X utf8 build-release.py --output dist/engineering-research-workbench-0.7.0.zip --json`

Expected: status `built`, exact version `0.7.0`, no forbidden member, and a reported SHA-256 matching a separate filesystem hash.

- [ ] **Step 5: Rebuild independently and compare exact bytes**

Build a second ZIP under a temporary directory and require byte equality with the `dist` ZIP. Extract it, run installer dry-run for Codex, Claude Code, OpenCode, OpenClaw, and GitHub Copilot project scope, and run Hermes user-scope dry-run. Do not write to real host roots.

- [ ] **Step 6: Audit frozen and tracked boundaries**

Run `git diff --check`, require zero diff from `c21c24e079631d2396a3989045c9f0945e17c24e` under `evals/m4/**` and `tests/test_m4*.py`, list every changed tracked path, and confirm `dist/**` remains ignored and untracked.

- [ ] **Step 7: Stop at the delivery boundary**

Report the local artifact path, hash, tests, limitations, and uncommitted source changes. Do not stage, commit, push, open a pull request, publish a GitHub release, or merge until the user explicitly grants the corresponding authority.

## Self-Review

- Spec coverage: the plan separates the development repository from the clean artifact, preserves M1–M4 evidence, removes milestone-coupled runtime material from releases and projections, keeps one canonical runtime source, creates a usable ZIP, binds versions, verifies hashes, and excludes every named development path.
- Placeholder scan: every task names concrete files, interfaces, commands, outcomes, and failure behavior; no deferred implementation marker remains.
- Type consistency: `PayloadFile`, `collect_payload`, `build_manifest`, `write_archive`, `validate_release_manifest`, `RELEASE_SCHEMA`, and `release-manifest.json` use the same names across tasks and tests.
- Authority check: local implementation, local artifact generation, and validation are in scope; commit, push, PR, merge, host installation, publication, and release upload remain out of scope.

## Execution Mode

The user selected the recommended non-destructive design and authorized proceeding in this session. Execute inline with the task-level test gates above; do not dispatch subagents or cross the external-delivery boundary.
