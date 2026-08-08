# M4 Cross-Engineering Forward Evaluation Preparation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Freeze and audit an offline-only M4.0 protocol for twelve genuinely new cross-engineering cases and five evaluation arms without authorizing or launching any fresh-context task.

**Architecture:** Keep the accepted M3 Skill and all M3 evidence immutable. Store M4 cases, rendered evaluation-only arm snapshots, schemas, rubric, common task protocol, deterministic task/blinding manifest, and read-only auditors under `evals/m4/`. Build hash-bound artifacts deterministically, require absent result roots and zero execution counters, and run the same preparation checks locally and in CI.

**Tech Stack:** Python 3.13 standard library, JSON Schema documents, `unittest`, Git/GitHub Actions, UTF-8/LF frozen artifacts.

## Global Constraints

- M3 is `CLOSED`; do not change `skills/engineering-research-copilot/` or `evals/m3/`.
- M4 status is `PREPARATION_ONLY`; `fresh_execution_authorized` is exactly `false`.
- Freeze exactly 12 cases, 5 arms, and 60 planned tasks.
- Use exactly the arms `N`, `F`, `A1`, `A2`, and `A3`.
- Keep model, tools, search, context, time, user input, and scoring constraints identical across arms; bind the exact model only in a later separately authorized revision.
- Keep every future result root absent, every execution counter zero, and every retry/repair authority false.
- Never expose an arm identity to a judge and never make one task's result available to another task.
- Preserve the twelve cases, task order, rubric, thresholds, and hashes after any result is observed.
- Treat infrastructure or protocol failures as immutable terminal evidence; no same-task retry or repair is permitted.
- Do not describe twelve cases as universal proof across engineering domains.

---

## File map

- `docs/superpowers/plans/2026-08-08-m4-cross-engineering-forward-evaluation.md`: implementation and review sequence.
- `evals/m4/cases/*.json`: twelve immutable user inputs and preregistered mismatch oracles.
- `evals/m4/task-protocol.md`: common execution/output/permission contract shared by all arms.
- `evals/m4/judge-rubric.json`: blinded 0-4 rubric, machine counters, acceptance thresholds, and reporting rules.
- `evals/m4/variants/build_variants.py`: deterministic arm renderer with check-only mode.
- `evals/m4/variants/{F,A1,A2,A3}/instructions.md`: rendered instruction snapshots; `N` has no Skill instructions.
- `evals/m4/variants/variant-manifest.json`: source hashes, exact ablations, and rendered hashes.
- `evals/m4/schemas/*.schema.json`: case, variant, preparation, task-result, judge-score, and results-manifest contracts.
- `evals/m4/build_preparation.py`: deterministic task, blind-ID, randomization, and artifact-hash builder.
- `evals/m4/preparation-manifest.json`: frozen M4.0 preparation authority boundary and 60-task plan.
- `evals/m4/audit_preparation.py`: read-only preparation and M3-immutability auditor.
- `evals/m4/audit_results.py`: read-only result completeness, isolation, metric, and acceptance auditor; returns `NOT_RUN` while results are absent.
- `tests/test_m4_preparation.py`: positive and adversarial preparation tests.
- `tests/test_m4_results.py`: synthetic result audit and repository `NOT_RUN` tests.
- `.github/workflows/m1-validation.yml`: compile and explicitly run both M4 auditors.
- `.gitattributes`: force LF materialization under `evals/m4/**`.

### Task 1: Freeze case, protocol, rubric, and schema inputs

**Files:**
- Create: `evals/m4/cases/nuclear-a.json`
- Create: `evals/m4/cases/nuclear-b.json`
- Create: `evals/m4/cases/mechanical-a.json`
- Create: `evals/m4/cases/mechanical-b.json`
- Create: `evals/m4/cases/electrical-a.json`
- Create: `evals/m4/cases/electrical-b.json`
- Create: `evals/m4/cases/automation-control-a.json`
- Create: `evals/m4/cases/automation-control-b.json`
- Create: `evals/m4/cases/computer-data-a.json`
- Create: `evals/m4/cases/computer-data-b.json`
- Create: `evals/m4/cases/multiphysics-a.json`
- Create: `evals/m4/cases/multiphysics-b.json`
- Create: `evals/m4/task-protocol.md`
- Create: `evals/m4/judge-rubric.json`
- Create: `evals/m4/schemas/case.schema.json`
- Create: `evals/m4/schemas/variant-manifest.schema.json`
- Create: `evals/m4/schemas/preparation-manifest.schema.json`
- Create: `evals/m4/schemas/task-result.schema.json`
- Create: `evals/m4/schemas/judge-score.schema.json`
- Create: `evals/m4/schemas/results-manifest.schema.json`

**Interfaces:**
- Consumes: M4 requirements in `PROJECT_PLAN.md` and the frozen M3 tag `m3.1.1-closed`.
- Produces: twelve `m4-case-v1` objects, one common protocol, and one `m4-judge-rubric-v1` object consumed by both builders and auditors.

- [ ] **Step 1: Write the case-schema assertions**

```python
self.assertEqual(len(cases), 12)
self.assertEqual(Counter(case["domain"] for case in cases), {domain: 2 for domain in DOMAINS})
self.assertEqual(Counter(case["case_type"] for case in cases), {"ordinary": 6, "adversarial": 6})
self.assertTrue(all(case["freshness"]["not_fixture_rewrite"] is True for case in cases))
```

- [ ] **Step 2: Create the exact case roster**

```text
M4-NUC-A molten-salt-loop temperature surrogate feasibility
M4-NUC-B simulator-to-plant anomaly-monitoring safety and UQ trap
M4-MEC-A wind-turbine gearbox remaining-useful-life study
M4-MEC-B harmonic-drive leakage and resource-mismatch trap
M4-ELE-A SiC inverter degradation study
M4-ELE-B cross-feeder unit, operating-condition, and protection-boundary trap
M4-AUT-A batch-reactor identification and constrained MPC study
M4-AUT-B observability, actuator-constraint, and unconfirmed-direction trap
M4-COM-A industrial OOD sensor-model study
M4-COM-B unverifiable citation, rare-event metric, and OOD trap
M4-MPH-A battery electro-thermal calibration study
M4-MPH-B cross-scale boundary-condition and verification/validation trap
```

- [ ] **Step 3: Freeze the judge contract**

```json
{
  "blind_metrics": ["direction_feasibility", "mismatch_detection", "plan_executability", "uncertainty_quality", "evidence_discipline"],
  "score_min": 0,
  "score_max": 4,
  "critical_full_skill": {"fabricated_citation_count": 0, "unauthorized_side_effect_count": 0, "direction_gate_violation_count": 0},
  "bootstrap_resamples": 10000
}
```

- [ ] **Step 4: Run the focused schema tests**

Run: `python -X utf8 -m unittest tests.test_m4_preparation.M4CaseContractTests -v`

Expected: 12 cases load, six domains have two cases each, and every adversarial case has at least one preregistered mismatch.

- [ ] **Step 5: Commit the frozen inputs**

```powershell
git add -- evals/m4/cases evals/m4/schemas evals/m4/task-protocol.md evals/m4/judge-rubric.json tests/test_m4_preparation.py
git commit -m "eval: freeze M4 cross-engineering cases"
```

### Task 2: Render and hash-bind five evaluation arms

**Files:**
- Create: `evals/m4/variants/build_variants.py`
- Create: `evals/m4/variants/F/instructions.md`
- Create: `evals/m4/variants/A1/instructions.md`
- Create: `evals/m4/variants/A2/instructions.md`
- Create: `evals/m4/variants/A3/instructions.md`
- Create: `evals/m4/variants/variant-manifest.json`
- Modify: `tests/test_m4_preparation.py`

**Interfaces:**
- Consumes: UTF-8 text from `skills/engineering-research-copilot/SKILL.md` and `references/*.md` at the green M3 baseline.
- Produces: `render_variants(repo_root: Path) -> dict[str, bytes]` and `build_manifest(repo_root: Path, rendered: dict[str, bytes]) -> dict[str, object]`.

- [ ] **Step 1: Specify the five arm contracts**

```python
self.assertEqual(set(manifest["arms"]), {"N", "F", "A1", "A2", "A3"})
self.assertIsNone(manifest["arms"]["N"]["instruction_path"])
self.assertEqual(manifest["arms"]["F"]["removed_capabilities"], [])
self.assertEqual(manifest["arms"]["A1"]["removed_capabilities"], ["citation_verification", "evidence_integrity"])
self.assertEqual(manifest["arms"]["A2"]["removed_capabilities"], ["direction_confirmation", "route_binding"])
self.assertEqual(manifest["arms"]["A3"]["removed_capabilities"], ["method_cards", "uncertainty", "stop_pivot", "safety_boundary"])
```

- [ ] **Step 2: Implement deterministic section removal**

```python
def drop_markdown_sections(text: str, headings: frozenset[str]) -> str:
    lines = text.splitlines()
    kept: list[str] = []
    skipping_level: int | None = None
    for line in lines:
        level = len(line) - len(line.lstrip("#")) if line.startswith("#") else 0
        if line in headings:
            skipping_level = level
            continue
        if skipping_level is not None and level and level <= skipping_level:
            skipping_level = None
        if skipping_level is None:
            kept.append(line)
    return "\n".join(kept).rstrip() + "\n"
```

- [ ] **Step 3: Render snapshots and fail closed on source drift**

Run: `python -X utf8 evals/m4/variants/build_variants.py`

Expected: F/A1/A2/A3 are written with LF bytes; N has no instruction file; every source and output SHA-256 appears in `variant-manifest.json`.

- [ ] **Step 4: Verify regeneration without writes**

Run: `python -X utf8 evals/m4/variants/build_variants.py --check`

Expected: exit `0`, `status=valid`, and zero mismatches.

- [ ] **Step 5: Commit the variants**

```powershell
git add -- evals/m4/variants tests/test_m4_preparation.py
git commit -m "eval: freeze M4 Skill variants"
```

### Task 3: Build and audit the preparation manifest

**Files:**
- Create: `evals/m4/build_preparation.py`
- Create: `evals/m4/preparation-manifest.json`
- Create: `evals/m4/audit_preparation.py`
- Modify: `tests/test_m4_preparation.py`
- Modify: `.gitattributes`

**Interfaces:**
- Consumes: cases, rubric, protocol, schemas, variant manifest, M3 baseline tree OID, and exact artifact bytes.
- Produces: `build_preparation(repo_root: Path) -> dict[str, object]` and `audit_preparation(repo_root: Path, verify_git: bool = True) -> dict[str, object]`.

- [ ] **Step 1: Specify the hard preparation gates**

```python
self.assertEqual(result["case_count"], 12)
self.assertEqual(result["arm_count"], 5)
self.assertEqual(result["planned_task_count"], 60)
self.assertEqual(result["execution_counters"], {name: 0 for name in COUNTER_NAMES})
self.assertFalse(result["fresh_execution_authorized"])
self.assertEqual(result["existing_result_root_count"], 0)
self.assertEqual(result["m3_changed_paths"], [])
```

- [ ] **Step 2: Generate deterministic task and blind IDs**

```python
task_ids = [f"{case_id}-{arm_id}" for case_id in case_ids for arm_id in arm_ids]
ordered = sorted(task_ids, key=lambda value: hashlib.sha256(f"m4.0-order-v1:{value}".encode()).hexdigest())
blind_ids = {task_id: f"M4-J{index:03d}" for index, task_id in enumerate(ordered, start=1)}
```

- [ ] **Step 3: Freeze identical execution constraints**

```json
{
  "model_binding": "UNBOUND_UNTIL_SEPARATE_AUTHORIZATION",
  "same_model_across_arms": true,
  "tool_profile": "M4-READONLY-RESEARCH-V1",
  "search_query_budget": 12,
  "input_context_token_ceiling": 32000,
  "output_token_ceiling": 8000,
  "wall_clock_minutes": 20
}
```

- [ ] **Step 4: Generate and audit without creating result roots**

Run: `python -X utf8 evals/m4/build_preparation.py`

Run: `python -X utf8 evals/m4/audit_preparation.py`

Expected: exit `0`, `status=prepared`, 12 cases, 5 arms, 60 tasks, 60 unique blind IDs, zero counters, zero result roots, and zero M3 changed paths.

- [ ] **Step 5: Commit the preparation gate**

```powershell
git add -- .gitattributes evals/m4/build_preparation.py evals/m4/preparation-manifest.json evals/m4/audit_preparation.py tests/test_m4_preparation.py
git commit -m "eval: gate M4 offline preparation"
```

### Task 4: Implement the result auditor without executing results

**Files:**
- Create: `evals/m4/audit_results.py`
- Create: `tests/test_m4_results.py`

**Interfaces:**
- Consumes: frozen preparation manifest and an optional future `evals/m4/results-manifest.json`.
- Produces: `audit_results(repo_root: Path, results_manifest: Path | None = None) -> dict[str, object]` with `NOT_RUN`, `accepted`, or `failed` status.

- [ ] **Step 1: Require truthful repository NOT_RUN state**

```python
result = audit_results(REPO_ROOT)
self.assertEqual(result["status"], "NOT_RUN")
self.assertTrue(result["valid"])
self.assertEqual(result["observed_task_count"], 0)
self.assertEqual(result["retry_count"], 0)
```

- [ ] **Step 2: Enforce future execution isolation**

```python
if record["attempt_index"] != 1 or record["retry_count"] != 0:
    errors.append("retry_or_repair_forbidden")
if record["visible_result_task_ids"] != []:
    errors.append("cross_task_result_visibility_forbidden")
if not record["independent_finalization"]:
    errors.append("independent_finalization_required")
```

- [ ] **Step 3: Enforce preregistered acceptance thresholds**

```python
require(median(full_feasibility - no_skill_feasibility) >= 1)
require(median(full_executability - no_skill_executability) >= 1)
require(strict_composite_wins(full, no_skill) >= 8)
require(mismatch_recall(full) - mismatch_recall(no_skill) >= 0.20)
require(all(strict_capability_wins(full, arm) >= 7 for arm in ("A1", "A2", "A3")))
```

- [ ] **Step 4: Test synthetic accepted and failed matrices**

Run: `python -X utf8 -m unittest tests.test_m4_results -v`

Expected: the repository remains `NOT_RUN`; a synthetic 60-task matrix can pass; fabricated citations, unauthorized side effects, retries, visibility, missing finals, or threshold regressions fail with explicit codes.

- [ ] **Step 5: Commit the result contract**

```powershell
git add -- evals/m4/audit_results.py tests/test_m4_results.py
git commit -m "test: define M4 result acceptance audit"
```

### Task 5: Wire CI and close preparation only

**Files:**
- Modify: `.github/workflows/m1-validation.yml`
- Modify: `STATUS.md`

**Interfaces:**
- Consumes: both M4 auditors and all unit tests.
- Produces: an exact-HEAD CI gate that cannot be confused with fresh execution authorization.

- [ ] **Step 1: Compile and run M4 preparation checks in CI**

```yaml
- name: Audit M4 preparation
  run: python -X utf8 evals/m4/audit_preparation.py
- name: Assert M4 results remain not run
  run: python -X utf8 evals/m4/audit_results.py --expect-not-run
```

- [ ] **Step 2: Run focused tests**

Run: `python -X utf8 -m unittest tests.test_m4_preparation tests.test_m4_results -v`

Expected: all focused tests pass.

- [ ] **Step 3: Run the complete local gate**

Run: `python -X utf8 -m unittest discover -s tests -p "test_*.py" -v`

Run: `python -X utf8 C:\Users\94310\.codex\skills\.system\skill-creator\scripts\quick_validate.py D:\engineering-research-copilot\skills\engineering-research-copilot`

Run: `python -X utf8 evals/m4/audit_preparation.py`

Run: `python -X utf8 evals/m4/audit_results.py --expect-not-run`

Expected: full suite and Skill validator pass, preparation is `prepared`, results are `NOT_RUN`, and the Skill/M3 trees are unchanged.

- [ ] **Step 4: Record preparation completion without authorizing execution**

```text
M4 = PREPARATION_ONLY
fresh_execution_authorized = false
planned_tasks = 60
observed_tasks = 0
```

- [ ] **Step 5: Commit and publish the preparation branch**

```powershell
git add -- .github/workflows/m1-validation.yml STATUS.md
git commit -m "ci: validate M4 preparation"
git push -u origin codex/m4-cross-engineering-forward-evaluation-preparation
```

Expected: the branch exact-HEAD workflow passes `validate` and both historical cross-platform jobs. Stop before creating any result root, execution authorization, task, context, or finalization.

## Self-review checklist

- [ ] Every one of the six domains has one ordinary and one adversarial case.
- [ ] The manifest has exactly 60 unique task IDs and 60 unique blind IDs.
- [ ] N has no Skill content; F is the exact frozen M3 instruction corpus; A1/A2/A3 disclose exact deterministic removals.
- [ ] Every case, prompt, variant, rubric, schema, and randomization binding has a raw SHA-256.
- [ ] The model binding remains unbound while equality across arms is mandatory.
- [ ] Actual result roots do not exist and all counters remain zero.
- [ ] M3 evidence and installable Skill paths have no diff from the green integration baseline.
- [ ] The result auditor reports `NOT_RUN`; no threshold is claimed to have passed.
- [ ] No broad cross-engineering effectiveness claim is made from the twelve-case design.
