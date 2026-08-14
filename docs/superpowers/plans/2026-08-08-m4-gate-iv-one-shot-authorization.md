# M4 Gate IV One-Shot Authorization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Independently review the green M4 preparation baseline and issue one hash-bound, unconsumed authorization for the exact 60-task M4.0 matrix without launching a fresh context, creating a result root, scoring a result, retrying, or repairing.

**Architecture:** Preserve commit `c56c3c1ab384f65e51a70e9582672c6320d19121` as the immutable preparation baseline. Add a separate `evals/m4/authorization/` layer containing a deterministic review record, authorization receipt, execution control, schemas, builder, and read-only auditor. Bind the current configured Codex default `gpt-5.6-sol` with reasoning effort `max`, the existing project ID and worktree execution surface, all preparation hashes, the exact 60 task IDs, six batch boundaries, zero prelaunch counters, and an absent future launch-claim path. CI may prove readiness but must never consume the authorization.

**Tech Stack:** Python 3.13 standard library, closed JSON artifacts, `unittest`, Git blob/ancestry checks, GitHub Actions, Codex project metadata, UTF-8/LF.

## Global Constraints

- Branch from exact green preparation HEAD `c56c3c1ab384f65e51a70e9582672c6320d19121`; its exact-HEAD GitHub Actions run is `31237480839` with conclusion `success`.
- Keep `skills/engineering-research-copilot/`, `evals/m3/`, and every frozen M4 preparation artifact byte-identical to the preparation HEAD.
- Keep `evals/m4/results/`, `evals/m4/results-manifest.json`, and `evals/m4/execution/m4.0/launch-claim.json` absent throughout authorization work.
- Authorize exactly the 60 task IDs and six 10-task domain batches already frozen in `preparation-manifest.json`.
- Bind model `gpt-5.6-sol`, reasoning effort `max`, project ID `ff35b25f-4644-41c8-9073-74c697559439`, and execution surface `codex_app.create_thread`.
- Require the create-thread model and thinking fields to be omitted so the configured defaults are used; fail preflight if those defaults no longer equal the bound model and effort.
- Allow one fresh context and one finalization for each authorized task ID, with exactly zero retries and zero repairs.
- Permit future evidence writes only below each task's frozen `evals/m4/results/m4.0/<task-id>` root after the launch claim consumes the token.
- Keep judge execution, blind-map access, unblinding, result aggregation, threshold claims, and M4 closure unauthorized.
- Stop the current batch on infrastructure or protocol failure, preserve the failure, invalidate remaining launches under this revision, and require a successor revision.
- Do not call `codex_app.create_thread`, create a task, create a result root, or create a launch claim while implementing or validating authorization.

---

## File map

- `docs/superpowers/plans/2026-08-08-m4-gate-iv-one-shot-authorization.md`: this implementation and review sequence.
- `evals/m4/authorization/build_authorization.py`: deterministic builder for the review, authorization, and execution-control artifacts; `--check` compares bytes without writing.
- `evals/m4/authorization/audit_authorization.py`: read-only readiness auditor and execution preflight.
- `evals/m4/authorization/gate-iv-review.json`: independent preparation review record with zero findings.
- `evals/m4/authorization/execution-authorization.json`: exact matrix authority, token, permissions, model binding, and zero counters.
- `evals/m4/authorization/execution-control.json`: frozen batch/task order, paths, request policy, launch-claim contract, and stop rules.
- `evals/m4/authorization/execution-authorization.schema.json`: closed authorization receipt schema.
- `evals/m4/authorization/execution-control.schema.json`: closed execution-control schema.
- `tests/test_m4_authorization.py`: positive, no-side-effect, drift, counter, token, model, path, retry, blinding, and consumption tests.
- `.github/workflows/m1-validation.yml`: compile, regenerate-check, and audit the authorization on Linux and Windows without consuming it.
- `STATUS.md`: record Gate IV as authorized but unconsumed, with tasks, contexts, finalizations, results, retries, repairs, and judge scores still zero.

### Task 1: Specify the independent review and closed authorization contracts

**Files:**
- Create: `tests/test_m4_authorization.py`
- Create: `evals/m4/authorization/execution-authorization.schema.json`
- Create: `evals/m4/authorization/execution-control.schema.json`

**Interfaces:**
- Consumes: `evals/m4/preparation-manifest.json` at preparation HEAD `c56c3c1ab384f65e51a70e9582672c6320d19121`.
- Produces: exact closed field sets for `m4-gate-iv-review-v1`, `m4-execution-authorization-v1`, and `m4-execution-control-v1`.

- [ ] **Step 1: Write the failing repository-readiness test**

```python
def test_repository_authorization_is_ready_unconsumed_and_read_only(self) -> None:
    before = snapshot_guarded_paths(REPO_ROOT)
    result = audit_authorization(REPO_ROOT)
    self.assertEqual(result["status"], "READY_UNCONSUMED")
    self.assertEqual(result["authorized_task_count"], 60)
    self.assertEqual(result["existing_result_root_count"], 0)
    self.assertEqual(result["execution_counters"], ZERO_COUNTERS)
    self.assertFalse(result["launch_claim_present"])
    self.assertEqual(result["side_effects"], [])
    self.assertEqual(snapshot_guarded_paths(REPO_ROOT), before)
```

- [ ] **Step 2: Freeze the authorization field set**

```python
AUTHORIZATION_KEYS = {
    "schema_version", "milestone", "revision", "status",
    "preparation_baseline", "review", "model_binding",
    "execution_surface", "authority", "batch_policy",
    "prelaunch_counters", "consumption", "does_not_authorize",
    "authorization_token",
}
```

- [ ] **Step 3: Freeze exact zero counters and limits**

```python
ZERO_COUNTERS = {
    "authorized_tasks": 0,
    "created_contexts": 0,
    "dispatched_tasks": 0,
    "finalizations": 0,
    "results_observed": 0,
    "judge_scores": 0,
    "retries": 0,
    "repairs": 0,
    "unauthorized_side_effects": 0,
}
LIMITS = {
    "task_ids": 60,
    "fresh_contexts": 60,
    "independent_finalizations": 60,
    "attempts_per_task_id": 1,
    "retries": 0,
    "repairs": 0,
    "judge_contexts": 0,
}
```

- [ ] **Step 4: Run the new test and verify the intended red state**

Run: `python -X utf8 -m unittest tests.test_m4_authorization -v`

Expected: import failure because `evals/m4/authorization/audit_authorization.py` does not exist; no repository file changes.

- [ ] **Step 5: Commit the red contract**

```powershell
git add -- tests/test_m4_authorization.py evals/m4/authorization/execution-authorization.schema.json evals/m4/authorization/execution-control.schema.json
git commit -m "test: specify M4 Gate IV authorization"
```

### Task 2: Build hash-bound review, authorization, and execution control

**Files:**
- Create: `evals/m4/authorization/build_authorization.py`
- Create: `evals/m4/authorization/gate-iv-review.json`
- Create: `evals/m4/authorization/execution-authorization.json`
- Create: `evals/m4/authorization/execution-control.json`
- Modify: `tests/test_m4_authorization.py`

**Interfaces:**
- Consumes: preparation manifest bytes, its Git blob at `c56c3c1ab384f65e51a70e9582672c6320d19121`, the exact task order, blind mapping, batch roster, execution constraints, and GitHub run `31237480839`.
- Produces: `build_artifacts(repo_root: Path) -> dict[str, bytes]`, `canonical_bytes(value: object) -> bytes`, and `authorization_token(payload: dict[str, object]) -> str`.

- [ ] **Step 1: Implement canonical hashing and a token that excludes itself**

```python
def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")

def authorization_token(payload: dict[str, object]) -> str:
    unsigned = dict(payload)
    unsigned.pop("authorization_token", None)
    return "sha256:" + hashlib.sha256(canonical_bytes(unsigned)).hexdigest()
```

- [ ] **Step 2: Build the independent review record**

```python
review = {
    "schema_version": "m4-gate-iv-review-v1",
    "review_date": "2026-08-08",
    "status": "PASSED",
    "preparation_head": PREPARATION_HEAD,
    "preparation_ci_run_id": 31237480839,
    "preparation_ci_conclusion": "success",
    "case_count": 12,
    "arm_count": 5,
    "planned_task_count": 60,
    "domain_batch_count": 6,
    "result_root_count": 0,
    "findings": [],
}
```

- [ ] **Step 3: Bind the model, app surface, and exact authority**

```python
model_binding = {
    "exact_model_id": "gpt-5.6-sol",
    "reasoning_effort": "max",
    "configured_default_required": True,
    "model_argument_policy": "OMIT_AND_VERIFY_CONFIGURED_DEFAULT",
    "thinking_argument_policy": "OMIT_AND_VERIFY_CONFIGURED_DEFAULT",
}
execution_surface = {
    "tool": "codex_app.create_thread",
    "project_id": "ff35b25f-4644-41c8-9073-74c697559439",
    "project_is_git_repository": True,
    "environment": "worktree",
    "starting_branch": "codex/m4-cross-engineering-forward-evaluation-one-shot-authorization",
}
```

- [ ] **Step 4: Freeze one matrix claim and the future paths**

```python
consumption = {
    "authorization_token_status": "UNCONSUMED",
    "claim_count": 0,
    "launch_claim_path": "evals/m4/execution/m4.0/launch-claim.json",
    "launch_claim_must_be_absent": True,
    "claim_consumes_entire_matrix_authorization": True,
    "partial_or_failed_matrix_requires_new_revision": True,
}
```

- [ ] **Step 5: Generate artifacts and verify byte-stable check mode**

Run: `python -X utf8 evals/m4/authorization/build_authorization.py`

Run: `python -X utf8 evals/m4/authorization/build_authorization.py --check`

Expected: three JSON artifacts are LF-terminated; check mode returns `status=valid`, zero mismatches, 12 cases, 5 arms, 60 tasks, six batches, and token status `UNCONSUMED`.

- [ ] **Step 6: Commit generated authorization inputs**

```powershell
git add -- evals/m4/authorization/build_authorization.py evals/m4/authorization/gate-iv-review.json evals/m4/authorization/execution-authorization.json evals/m4/authorization/execution-control.json tests/test_m4_authorization.py
git commit -m "eval: build M4 Gate IV authorization"
```

### Task 3: Implement the read-only fail-closed authorization audit

**Files:**
- Create: `evals/m4/authorization/audit_authorization.py`
- Modify: `tests/test_m4_authorization.py`

**Interfaces:**
- Consumes: the three generated artifacts, both closed schemas, preparation Git blobs, worktree result/claim state, and optional configured model/effort values.
- Produces: `audit_authorization(repo_root: Path, review_path: Path | None = None, authorization_path: Path | None = None, control_path: Path | None = None, launch_claim_path: Path | None = None, results_base: Path | None = None, configured_model: str | None = None, configured_reasoning_effort: str | None = None, verify_git: bool = True) -> dict[str, object]`.

- [ ] **Step 1: Require immutable preparation ancestry and Git blobs**

```python
require_git_ancestor(PREPARATION_HEAD, "HEAD")
for relative in FROZEN_PREPARATION_PATHS:
    require_equal_git_blobs(PREPARATION_HEAD, "HEAD", relative)
```

- [ ] **Step 2: Validate token, task, batch, model, permission, and counter bindings**

```python
if authorization["authorization_token"] != authorization_token(authorization):
    errors.append("authorization_token_invalid")
if authorization["authority"]["authorized_task_ids"] != prepared_task_ids:
    errors.append("authorized_task_ids_invalid")
if authorization["prelaunch_counters"] != ZERO_COUNTERS:
    errors.append("prelaunch_counters_nonzero")
if authorization["model_binding"] != EXPECTED_MODEL_BINDING:
    errors.append("model_binding_invalid")
```

- [ ] **Step 3: Fail closed on any consumed or observable execution state**

```python
if launch_claim_path.exists():
    errors.append("authorization_already_claimed")
if results_manifest_path.exists():
    errors.append("results_manifest_present_before_launch")
if any(result_root.exists() for result_root in prepared_result_roots):
    errors.append("result_root_present_before_launch")
```

- [ ] **Step 4: Add adversarial tests**

```python
def _audit_mutation(self, name: str, mutate) -> dict[str, object]:
    source = AUTHORIZATION_ROOT / name
    value = json.loads(source.read_text(encoding="utf-8"))
    mutate(value)
    with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
        changed = Path(temp_dir) / name
        changed.write_bytes(canonical_bytes(value) + b"\n")
        kwargs = {
            "review_path": REVIEW_PATH,
            "authorization_path": AUTHORIZATION_PATH,
            "control_path": CONTROL_PATH,
        }
        kwargs[
            {
                "gate-iv-review.json": "review_path",
                "execution-authorization.json": "authorization_path",
                "execution-control.json": "control_path",
            }[name]
        ] = changed
        return audit_authorization(REPO_ROOT, verify_git=False, **kwargs)

def test_rejects_model_or_reasoning_drift(self):
    result = self._audit_mutation(
        "execution-authorization.json",
        lambda value: value["model_binding"].__setitem__(
            "exact_model_id", "gpt-5.6-terra"
        ),
    )
    self.assertIn("model_binding_invalid", result["errors"])

def test_rejects_nonzero_counter_or_retry_authority(self):
    result = self._audit_mutation(
        "execution-authorization.json",
        lambda value: value["prelaunch_counters"].__setitem__("retries", 1),
    )
    self.assertIn("prelaunch_counters_nonzero", result["errors"])

def test_rejects_token_tampering(self):
    result = self._audit_mutation(
        "execution-authorization.json",
        lambda value: value.__setitem__("authorization_token", "sha256:" + "0" * 64),
    )
    self.assertIn("authorization_token_invalid", result["errors"])

def test_rejects_task_or_batch_roster_drift(self):
    result = self._audit_mutation(
        "execution-control.json",
        lambda value: value["batch_order"].reverse(),
    )
    self.assertIn("batch_order_invalid", result["errors"])

def test_rejects_launch_claim_or_result_root(self):
    with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
        root = Path(temp_dir)
        claim = root / "launch-claim.json"
        claim.write_bytes(b"{}\n")
        result_base = root / "results" / "m4.0"
        (result_base / "M4-ELE-B-A2").mkdir(parents=True)
        result = audit_authorization(
            REPO_ROOT,
            launch_claim_path=claim,
            results_base=result_base,
            verify_git=False,
        )
    self.assertIn("authorization_already_claimed", result["errors"])
    self.assertIn("result_root_present_before_launch", result["errors"])

def test_rejects_judge_scoring_authority(self):
    result = self._audit_mutation(
        "execution-authorization.json",
        lambda value: value["authority"].__setitem__(
            "judge_execution_authorized", True
        ),
    )
    self.assertIn("judge_authority_forbidden", result["errors"])

def test_audit_has_no_callbacks_writes_or_network(self):
    before = snapshot_guarded_paths(REPO_ROOT)
    with mock.patch("urllib.request.urlopen") as network:
        result = audit_authorization(REPO_ROOT)
    network.assert_not_called()
    self.assertEqual(result["side_effects"], [])
    self.assertEqual(snapshot_guarded_paths(REPO_ROOT), before)
```

- [ ] **Step 5: Run focused authorization and preparation gates**

Run: `python -X utf8 -m unittest tests.test_m4_authorization tests.test_m4_preparation tests.test_m4_results -v`

Run: `python -X utf8 evals/m4/authorization/build_authorization.py --check`

Run: `python -X utf8 evals/m4/authorization/audit_authorization.py`

Expected: all tests pass; auditor returns `READY_UNCONSUMED`, 60 authorized task IDs, zero execution counters, no launch claim, no results, no side effects, and no errors.

- [ ] **Step 6: Commit the auditor**

```powershell
git add -- evals/m4/authorization/audit_authorization.py tests/test_m4_authorization.py
git commit -m "eval: audit M4 Gate IV authorization"
```

### Task 4: Wire exact-HEAD CI and publish authorization without consuming it

**Files:**
- Modify: `.github/workflows/m1-validation.yml`
- Modify: `STATUS.md`
- Modify: `tests/test_m3_r5_erratum.py`

**Interfaces:**
- Consumes: all M4 authorization artifacts and auditors.
- Produces: an exact-HEAD CI result that proves authorization readiness while all execution counters remain zero.

- [ ] **Step 1: Add non-consuming authorization checks to CI**

```yaml
- name: Require M4 authorization regeneration diff to be empty
  run: python -X utf8 evals/m4/authorization/build_authorization.py --check
- name: Audit M4 Gate IV authorization remains unconsumed
  run: python -X utf8 evals/m4/authorization/audit_authorization.py
```

- [ ] **Step 2: Record the truthful STATUS transition**

```text
M4 = GATE_IV_AUTHORIZED_UNCONSUMED
fresh_execution_authorized = true
authorization_token_status = UNCONSUMED
authorized_tasks = 60
created_contexts = 0
finalizations = 0
results = 0
retries = 0
repairs = 0
judge_scores = 0
```

- [ ] **Step 3: Keep the historical M3 assertion compatible with the new M4 state**

```python
self.assertIn("M3: `CLOSED`", current)
self.assertIn("M4: `GATE_IV_AUTHORIZED_UNCONSUMED`", current)
self.assertIn("M4 authorization token status: `UNCONSUMED`", current)
```

- [ ] **Step 4: Run the complete local gate**

Run: `python -X utf8 -m unittest discover -s tests -p "test_*.py" -v`

Run: `python -X utf8 evals/m4/variants/build_variants.py --check`

Run: `python -X utf8 evals/m4/build_preparation.py --check`

Run: `python -X utf8 evals/m4/audit_preparation.py`

Run: `python -X utf8 evals/m4/authorization/build_authorization.py --check`

Run: `python -X utf8 evals/m4/authorization/audit_authorization.py`

Run: `python -X utf8 evals/m4/audit_results.py --expect-not-run`

Run: `python -X utf8 C:\Users\94310\.codex\skills\.system\skill-creator\scripts\quick_validate.py D:\engineering-research-copilot\skills\engineering-research-copilot`

Expected: full suite and every auditor pass; preparation remains the frozen unauthorized historical baseline, the separate authorization is `READY_UNCONSUMED`, results remain `NOT_RUN`, and Skill/M3 diffs remain empty.

- [ ] **Step 5: Commit and publish the one-shot authorization**

```powershell
git add -- .github/workflows/m1-validation.yml STATUS.md tests/test_m3_r5_erratum.py
git commit -m "ci: authorize M4 Gate IV one-shot execution"
git push -u origin codex/m4-cross-engineering-forward-evaluation-one-shot-authorization
```

Expected: `validate`, Ubuntu historical audit, and Windows historical audit pass on the exact authorization HEAD. Stop with `authorization_token_status=UNCONSUMED`; do not create a fresh task, launch claim, result root, judge score, retry, repair, or M4 closure claim.

## Self-review checklist

- [ ] The plan changes no frozen Skill, M3 evidence, case, variant, preparation, rubric, threshold, schema, randomization, or result artifact.
- [ ] The independent review binds the green preparation HEAD and CI with zero findings.
- [ ] The authorization binds exactly `gpt-5.6-sol`, reasoning effort `max`, the existing Codex project, and all 60 prepared task IDs.
- [ ] The entire matrix has one unconsumed token and each task ID has exactly one allowed attempt.
- [ ] Result writes are limited to frozen task roots and cannot begin before the launch claim.
- [ ] Judge execution, blind-map access, aggregation, acceptance, and closure remain unauthorized.
- [ ] Every current counter is zero and every future execution/result path is absent.
- [ ] CI proves readiness without launching or consuming anything.
- [ ] No effectiveness, empirical, operational, transfer, or safety result is claimed.
