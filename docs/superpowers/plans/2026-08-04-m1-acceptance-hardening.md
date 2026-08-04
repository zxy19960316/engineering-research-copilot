# M1.1 Acceptance Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the M1 acceptance contract to `m1.2` so terminal states, identity deduplication, feedback traceability, Brief/SearchPlan shape, paper-map equivalence, real forward artifacts, and offline CI form one machine-verifiable evidence chain.

**Architecture:** Keep the existing M1 workflow and historical Markdown evidence intact. Make `validate_m1_bundle.py` dispatch from an explicit top-level terminal-state contract, add deterministic identity and map helpers, migrate offline fixtures to `m1.2`, and publish separate machine artifacts for the accepted A/B/C forward cases. CI remains standard-library-only and replays fixtures and saved artifacts without network access.

**Tech Stack:** Python 3.13 standard library, JSON, Markdown Skill references, `unittest`, GitHub Actions, PowerShell for local gates.

## Global Constraints

- Work only on `M1.1 — M1 acceptance hardening`; keep M2–M5 `NOT_STARTED`.
- Preserve every existing failed and accepted Markdown evaluation file byte-for-byte unless adding a separate sidecar migration note.
- Keep discovery separate from verification and never manufacture a title, author, DOI, alternate ID, source result, or evidence basis.
- Keep all scripts offline and standard-library-only; CI must not perform live scholarly lookup.
- Keep the installable root Skill lightweight; `SKILL.md` stays below 500 lines and directly links every loadable reference.
- Run the standard Skill validator after any Skill/reference/script metadata change.
- Stage explicit paths and make one independent commit per task.
- Do not push, create a PR, or claim remote CI success without explicit user authorization.
- If the required Superpowers execution skills are unavailable, use fresh task contexts with implementation review followed by independent specification review.

## File Responsibility Map

- `STATUS.md`: sole active-milestone and final acceptance status.
- `skills/engineering-research-copilot/references/core-paper-calibration.md`: normative `m1.2` Bundle, terminal-state, Brief, SearchPlan, and FeedbackDelta contract.
- `skills/engineering-research-copilot/references/core-citation-integrity.md`: normative candidate identity precedence and stable-ID rules.
- `skills/engineering-research-copilot/references/core-feedback-rollback.md`: one closed FeedbackDelta item schema and causal query-change rules.
- `skills/engineering-research-copilot/references/core-paper-map.md`: one structured map and deterministic rendering contract.
- `skills/engineering-research-copilot/scripts/validate_m1_bundle.py`: offline `m1.2` validator and closed CLI statuses.
- `skills/engineering-research-copilot/scripts/render_m1_map.py`: deterministic Mermaid and text-fallback renderer shared by generation and validation.
- `skills/engineering-research-copilot/scripts/validate_citation_gate.py`: closed offline validator for Case C's non-RoundBundle terminal object.
- `tests/test_validate_m1_bundle.py`: Bundle factories and contract regression tests.
- `tests/test_render_m1_map.py`: deterministic rendering and escaping tests.
- `tests/test_validate_citation_gate.py`: citation-gate schema and CLI tests.
- `evals/m1/fixtures/*.json`: fixture-only `m1.2` acceptance and adversarial inputs.
- `evals/m1/offline-results.json`: frozen expected exit/status/error/gap results.
- `evals/m1/replay_offline_results.py`: CI-safe replay of expected nonzero fixture results.
- `evals/m1/results/*.bundle.json`: canonical A/B `m1.2` machine inputs.
- `evals/m1/results/*.validation.json`: exact closed validator outputs for A/B/C.
- `evals/m1/results/*.provenance.json`: source window, input isolation, commit, and artifact hashes.
- `evals/m1/results/2026-08-04-citation-audit.gate.json`: Case C citation-gate input.
- `evals/m1/replay_machine_artifacts.py`: verify hashes and reproduce saved validation results offline.
- `.github/workflows/m1-validation.yml`: compile, unit, fixture replay, artifact replay, and Skill validation gates.

---

### Task 1: Reopen M1 acceptance and freeze the `m1.2` boundary

**Files:**
- Modify: `STATUS.md`
- Modify: `docs/superpowers/plans/2026-08-04-m1-two-round-paper-calibration.md`
- Modify: `docs/superpowers/plans/2026-08-04-m1-acceptance-hardening.md`

**Interfaces:**
- Consumes: M1 feature closure commit `556a408`.
- Produces: active milestone `M1.1`, a visible blocking list, and an implementation record that later tasks update without rewriting history.

- [x] **Step 1: Assert the branch and clean baseline**

Run:

```powershell
git branch --show-current
git status --short
git rev-parse HEAD
```

Expected: branch `codex/m1-acceptance-hardening`, no worktree output before planned edits, and HEAD descended from `556a408`.

- [x] **Step 2: Reopen only the acceptance status**

Replace the active block in `STATUS.md` with:

```markdown
## Active milestone

`M1.1 — M1 acceptance hardening`

Status: `IN_PROGRESS`

M1 feature implementation is complete, but final acceptance remains open while validator-contract gaps are being corrected.

Blocking items:

- round-one evidence-incomplete early-stop validation;
- alternate identifier and manual-review identity handling;
- one closed FeedbackDelta, ResearchBrief, SearchPlan, and PaperMap schema;
- machine-valid forward-test artifacts;
- clean CI on the final hardening HEAD.
```

Keep M2–M5 exactly `NOT_STARTED`.

- [x] **Step 3: Add an implementation record without rewriting the M1 plan history**

Insert at the top of `2026-08-04-m1-two-round-paper-calibration.md`, below its title:

```markdown
## Implementation record

- Original implementation closed at: `556a408`
- Acceptance hardening branch: `codex/m1-acceptance-hardening`
- Canonical schema under hardening: `m1.2`
- Historical failed forward runs remain preserved under `evals/m1/results/`.
- Final M1.2 validation record will be `evals/m1/results/2026-08-04-m1.2-final-validation.md`.
```

- [x] **Step 4: Review and commit the status-only boundary**

Run:

```powershell
git diff --check
git diff -- STATUS.md docs/superpowers/plans/2026-08-04-m1-two-round-paper-calibration.md docs/superpowers/plans/2026-08-04-m1-acceptance-hardening.md
git add -- STATUS.md docs/superpowers/plans/2026-08-04-m1-two-round-paper-calibration.md docs/superpowers/plans/2026-08-04-m1-acceptance-hardening.md
git commit -m "docs: reopen M1 acceptance hardening"
```

Expected: one documentation commit; no Skill, validator, fixture, or evaluation result changes.

---

### Task 2: Validate explicit terminal states and true round-one early stops

**Files:**
- Modify: `skills/engineering-research-copilot/references/core-paper-calibration.md`
- Modify: `skills/engineering-research-copilot/scripts/validate_m1_bundle.py`
- Modify: `tests/test_validate_m1_bundle.py`
- Modify: `evals/m1/fixtures/valid-complete.json`
- Modify: `evals/m1/fixtures/evidence-incomplete.json`
- Create: `evals/m1/fixtures/round2-evidence-incomplete.json`
- Modify: `evals/m1/adversarial-cases.json`
- Modify: `evals/m1/offline-results.json`

**Interfaces:**
- Consumes: existing round validators and `_Result.closed()` exit mapping.
- Produces: `SCHEMA_VERSION = "m1.2"`, `_validate_root_contract(bundle, result)`, `_validate_terminal_state_consistency(bundle, result)`, and state-directed optional round fields.

- [x] **Step 1: Write the terminal-state tests first**

Add these methods to `ValidateM1BundleTests`:

```python
def test_round_one_incomplete_bundle_is_valid_incomplete(self):
    bundle = make_round_one_incomplete_bundle()
    result = validate_bundle(bundle)
    self.assertEqual(result["status"], "evidence_incomplete")
    self.assertEqual(result["errors"], [])
    self.assertIn("round1_candidate_pool_below_target", result["evidence_gaps"])

def test_round_one_incomplete_rejects_round_two(self):
    bundle = make_round_one_incomplete_bundle()
    bundle["round2"] = _round_bundle(2, [])
    self.assertIn("round_two_fields_after_round_one_stop", validate_bundle(bundle)["errors"])

def test_round_one_incomplete_cannot_claim_m1_complete(self):
    bundle = make_round_one_incomplete_bundle()
    bundle["terminal_state"] = "M1_COMPLETE"
    self.assertIn("terminal_state_inconsistent", validate_bundle(bundle)["errors"])

def test_round_two_incomplete_requires_feedback_delta(self):
    bundle = make_round_two_incomplete_bundle()
    del bundle["feedback_delta"]
    self.assertIn("missing_feedback_delta", validate_bundle(bundle)["errors"])

def test_complete_bundle_requires_round_two_ready(self):
    bundle = make_complete_fixture_bundle()
    bundle["round2"]["selected_ids"] = bundle["round2"]["selected_ids"][:3]
    self.assertIn("complete_terminal_state_without_ready_round_two", validate_bundle(bundle)["errors"])
```

Define factories with exact root state:

```python
def _root_state(terminal_state: str, stopped_after_round: int, outcome: str) -> dict:
    return {
        "schema_version": "m1.2",
        "terminal_state": terminal_state,
        "stopped_after_round": stopped_after_round,
        "outcome": outcome,
        "fixture_mode": True,
        "evidence_class": "offline_contract_fixture",
    }

def make_round_one_incomplete_bundle() -> dict:
    bundle = _root_state("WAITING_FOR_EVIDENCE_DECISION", 1, "evidence_incomplete")
    round_one = _round_bundle(1, ["fixture:P01", "fixture:P02", "fixture:P03"])
    round_one["candidate_pool"] = round_one["candidate_pool"][:10]
    round_one["paper_map"] = _paper_map(1, round_one["selected_ids"])
    round_one["evidence_gaps"] = [
        {"role": "direct_problem", "missing_count": 2},
        {"role": "method", "missing_count": 2},
        {"role": "transfer_bridge", "missing_count": 2},
        {"role": "counter_limitation", "missing_count": 1},
    ]
    round_one["search_limitations"] = ["Only ten eligible fixture records were available"]
    bundle["round1"] = round_one
    return bundle

def make_round_two_incomplete_bundle() -> dict:
    bundle = make_complete_fixture_bundle()
    bundle.update({
        "terminal_state": "WAITING_FOR_EVIDENCE_DECISION",
        "stopped_after_round": 2,
        "outcome": "evidence_incomplete",
    })
    selected = ["fixture:P01", "fixture:P02", "fixture:P03"]
    bundle["round2"]["selected_ids"] = selected
    bundle["round2"]["paper_map"] = _paper_map(2, selected)
    bundle["round2"]["evidence_gaps"] = ["Two additional eligible papers are missing"]
    for entry in bundle["round2"]["round_one_dispositions"]:
        if entry["round_one_id"] in selected:
            entry.update({"disposition": "retained", "round_two_id": entry["round_one_id"]})
        else:
            entry.update({"disposition": "removed", "round_two_id": None})
    return bundle
```

- [x] **Step 2: Run only the five new tests and preserve the red result**

Run:

```powershell
python -m unittest `
  tests.test_validate_m1_bundle.ValidateM1BundleTests.test_round_one_incomplete_bundle_is_valid_incomplete `
  tests.test_validate_m1_bundle.ValidateM1BundleTests.test_round_one_incomplete_rejects_round_two `
  tests.test_validate_m1_bundle.ValidateM1BundleTests.test_round_one_incomplete_cannot_claim_m1_complete `
  tests.test_validate_m1_bundle.ValidateM1BundleTests.test_round_two_incomplete_requires_feedback_delta `
  tests.test_validate_m1_bundle.ValidateM1BundleTests.test_complete_bundle_requires_round_two_ready -v
```

Expected: FAIL because `m1.1` requires round two unconditionally and has no root terminal-state contract.

- [x] **Step 3: Implement state-directed validation**

Set these constants:

```python
SCHEMA_VERSION = "m1.2"
TERMINAL_STATES = {"WAITING_FOR_EVIDENCE_DECISION", "M1_COMPLETE"}
OUTCOMES = {"evidence_incomplete", "complete"}
ROOT_REQUIRED_FIELDS = {"schema_version", "terminal_state", "stopped_after_round", "outcome", "round1"}
ROOT_OPTIONAL_FIELDS = {"fixture_mode", "evidence_class", "feedback_delta", "round2"}
```

Add the root validator:

```python
def _validate_root_contract(bundle: dict, result: _Result) -> tuple[int | None, str | None, str | None]:
    unknown = set(bundle) - ROOT_REQUIRED_FIELDS - ROOT_OPTIONAL_FIELDS
    if unknown or not ROOT_REQUIRED_FIELDS.issubset(bundle):
        result.error("root_fields_invalid")
    stopped = bundle.get("stopped_after_round")
    terminal = bundle.get("terminal_state")
    outcome = bundle.get("outcome")
    if type(stopped) is not int or stopped not in {1, 2}:
        result.error("invalid_stopped_after_round")
    if terminal not in TERMINAL_STATES:
        result.error("invalid_terminal_state")
    if outcome not in OUTCOMES:
        result.error("invalid_outcome")
    return stopped if type(stopped) is int else None, terminal, outcome
```

Refactor `_validate_bundle` so round one is always validated, while feedback, round two, cross-round identity, and dispositions execute only for `stopped_after_round == 2`. Reject `feedback_delta` and `round2` when stopped after round one. Add terminal consistency:

```python
def _validate_terminal_state_consistency(
    stopped: int | None, terminal: str | None, outcome: str | None,
    round_two_ready: bool, result: _Result,
) -> None:
    expected = {
        (1, "evidence_incomplete"): "WAITING_FOR_EVIDENCE_DECISION",
        (2, "evidence_incomplete"): "WAITING_FOR_EVIDENCE_DECISION",
        (2, "complete"): "M1_COMPLETE",
    }
    if expected.get((stopped, outcome)) != terminal:
        result.error("terminal_state_inconsistent")
    if terminal == "M1_COMPLETE" and not round_two_ready:
        result.error("complete_terminal_state_without_ready_round_two")
```

- [x] **Step 4: Replace the false early-stop fixture and add a round-two incomplete fixture**

Make `evidence-incomplete.json` contain only root state plus `round1`; it must not contain `feedback_delta` or `round2`. Create `round2-evidence-incomplete.json` with both rounds, feedback, three eligible round-two selections, complete dispositions, and an evidence gap `round2_selection_below_target`.

Update `offline-results.json` expected results to:

```json
[
  {"fixture":"evals/m1/fixtures/valid-complete.json","exit_code":0,"status":"valid"},
  {"fixture":"evals/m1/fixtures/blocked-conflict.json","exit_code":1,"status":"invalid"},
  {"fixture":"evals/m1/fixtures/feedback-ignored.json","exit_code":1,"status":"invalid"},
  {"fixture":"evals/m1/fixtures/map-citation-sized.json","exit_code":1,"status":"invalid"},
  {"fixture":"evals/m1/fixtures/evidence-incomplete.json","exit_code":2,"status":"evidence_incomplete"},
  {"fixture":"evals/m1/fixtures/round2-evidence-incomplete.json","exit_code":2,"status":"evidence_incomplete"}
]
```

Keep the existing `proves` and `does_not_prove` provenance fields around the full records.

- [x] **Step 5: Run the Task 2 gates**

Run:

```powershell
python -m unittest discover -s tests -p "test_validate_m1_bundle.py" -v
python skills/engineering-research-copilot/scripts/validate_m1_bundle.py evals/m1/fixtures/evidence-incomplete.json
python skills/engineering-research-copilot/scripts/validate_m1_bundle.py evals/m1/fixtures/round2-evidence-incomplete.json
python -X utf8 C:\Users\94310\.codex\skills\.system\skill-creator\scripts\quick_validate.py D:\engineering-research-copilot\skills\engineering-research-copilot
```

Expected: all unit tests pass; each incomplete fixture prints closed `evidence_incomplete` JSON and exits `2`; Skill validator prints `Skill is valid!`.

- [x] **Step 6: Commit terminal-state support**

```powershell
git add -- skills/engineering-research-copilot/references/core-paper-calibration.md skills/engineering-research-copilot/scripts/validate_m1_bundle.py tests/test_validate_m1_bundle.py evals/m1/fixtures evals/m1/adversarial-cases.json evals/m1/offline-results.json
git commit -m "fix: validate M1 early-stop terminal states"
```

---

### Task 3: Enforce deterministic candidate identity precedence

**Files:**
- Modify: `skills/engineering-research-copilot/references/core-citation-integrity.md`
- Modify: `skills/engineering-research-copilot/scripts/validate_m1_bundle.py`
- Modify: `tests/test_validate_m1_bundle.py`

**Interfaces:**
- Consumes: closed `verified_record.doi`, `alternate_id`, `title`, and ordered `authors`.
- Produces: `normalize_alternate_id()`, `normalize_title_first_author()`, `_compare_candidate_identity()`, within-round collision errors, and cross-round stable-ID errors.

- [x] **Step 1: Write identity precedence tests**

Add exactly these tests:

```python
def test_duplicate_alternate_id_is_invalid(self):
    bundle = make_structurally_valid_production_bundle()
    first, second = bundle["round1"]["candidate_pool"][:2]
    for candidate in (first, second):
        candidate["verified_record"]["doi"] = None
        candidate["verified_record"]["alternate_id"] = {"authority": "arxiv", "value": "2401.01234v2"}
    self.assertIn("duplicate_candidate_identity", validate_bundle(bundle)["errors"])

def test_duplicate_arxiv_id_with_different_candidate_ids(self):
    bundle = make_structurally_valid_production_bundle()
    first, second = bundle["round1"]["candidate_pool"][:2]
    first["verified_record"]["doi"] = second["verified_record"]["doi"] = None
    first["verified_record"]["alternate_id"] = {"authority": "arxiv", "value": "2401.01234V2"}
    second["verified_record"]["alternate_id"] = {"authority": "ArXiv", "value": "2401.01234v2"}
    self.assertIn("duplicate_candidate_identity", validate_bundle(bundle)["errors"])

def test_equal_alternate_id_conflicting_title_is_blocked(self):
    bundle = make_structurally_valid_production_bundle()
    first, second = bundle["round1"]["candidate_pool"][:2]
    first["verified_record"]["doi"] = second["verified_record"]["doi"] = None
    first["verified_record"]["alternate_id"] = second["verified_record"]["alternate_id"] = {"authority": "arxiv", "value": "2401.01234v2"}
    second["verified_record"]["title"] = "A conflicting work identity"
    self.assertIn("candidate_identity_conflict", validate_bundle(bundle)["errors"])

def test_different_alternate_ids_do_not_fallback_to_title_merge(self):
    bundle = make_structurally_valid_production_bundle()
    first, second = bundle["round1"]["candidate_pool"][:2]
    first["verified_record"]["doi"] = second["verified_record"]["doi"] = None
    second["verified_record"]["title"] = first["verified_record"]["title"]
    second["verified_record"]["authors"] = first["verified_record"]["authors"]
    first["verified_record"]["alternate_id"] = {"authority": "arxiv", "value": "2401.00001"}
    second["verified_record"]["alternate_id"] = {"authority": "arxiv", "value": "2401.00002"}
    errors = validate_bundle(bundle)["errors"]
    self.assertNotIn("duplicate_candidate_identity", errors)
    self.assertNotIn("candidate_identity_manual_review", errors)

def test_title_first_author_match_requires_manual_review(self):
    bundle = make_structurally_valid_production_bundle()
    first, second = bundle["round1"]["candidate_pool"][:2]
    first["verified_record"]["doi"] = second["verified_record"]["doi"] = None
    first["verified_record"]["alternate_id"] = second["verified_record"]["alternate_id"] = None
    second["verified_record"]["title"] = first["verified_record"]["title"]
    second["verified_record"]["authors"] = first["verified_record"]["authors"]
    self.assertIn("candidate_identity_manual_review", validate_bundle(bundle)["errors"])

def test_same_doi_with_conflicting_metadata_is_conflicted(self):
    bundle = make_structurally_valid_production_bundle()
    first, second = bundle["round1"]["candidate_pool"][:2]
    second["verified_record"]["doi"] = first["verified_record"]["doi"]
    second["verified_record"]["title"] = "A conflicting DOI identity"
    self.assertIn("candidate_identity_conflict", validate_bundle(bundle)["errors"])

def test_stable_candidate_alternate_id_cannot_change(self):
    bundle = make_structurally_valid_production_bundle()
    for round_name, value in (("round1", "2401.00001"), ("round2", "2401.00002")):
        record = bundle[round_name]["candidate_pool"][0]["verified_record"]
        record["doi"] = None
        record["alternate_id"] = {"authority": "arxiv", "value": value}
    self.assertIn("stable_candidate_identity_changed", validate_bundle(bundle)["errors"])
```

Use `alternate_id = {"authority": "arxiv", "value": "2401.01234v2"}` for equal-ID cases, two different arXiv values for the decisive-distinct case, and DOI `None` for title/first-author manual-review cases.

- [x] **Step 2: Verify the identity tests fail before implementation**

Run:

```powershell
python -m unittest tests.test_validate_m1_bundle.ValidateM1BundleTests -k "alternate_id or title_first_author or conflicting_metadata" -v
```

Expected: new tests fail because within-round identity comparison does not yet implement the full precedence.

- [x] **Step 3: Implement normalization and comparison**

Add:

```python
def normalize_alternate_id(value: Any) -> tuple[str, str] | None:
    if not isinstance(value, dict) or set(value) != {"authority", "value"}:
        return None
    authority, identifier = value.get("authority"), value.get("value")
    if not _nonempty_text(authority) or not _nonempty_text(identifier):
        return None
    return authority.strip().casefold(), identifier.strip().casefold()

def normalize_title_first_author(record: dict) -> tuple[str, str] | None:
    title = record.get("title")
    authors = record.get("authors")
    if not _nonempty_text(title) or not isinstance(authors, list) or not authors:
        return None
    normalized_title = " ".join(title.split()).casefold()
    normalized_author = " ".join(str(authors[0]).split()).casefold()
    return normalized_title, normalized_author
```

Define comparison precedence:

```python
def _compare_candidate_identity(first: dict, second: dict) -> str:
    first_doi, second_doi = normalize_doi(first.get("doi")), normalize_doi(second.get("doi"))
    if first_doi is not None and second_doi is not None:
        return "duplicate" if first_doi == second_doi else "distinct"
    first_alt, second_alt = normalize_alternate_id(first.get("alternate_id")), normalize_alternate_id(second.get("alternate_id"))
    if first_alt is not None and second_alt is not None:
        return "duplicate" if first_alt == second_alt else "distinct"
    if normalize_title_first_author(first) == normalize_title_first_author(second) and normalize_title_first_author(first) is not None:
        return "manual_needed"
    return "distinct"
```

After a `duplicate` identity result, compare normalized title, ordered author identity, publication type, and version relation; emit `duplicate_candidate_identity` when compatible and `candidate_identity_conflict` when incompatible. Never auto-merge `manual_needed`; emit `candidate_identity_manual_review` and block either record from selection.

- [x] **Step 4: Apply the same precedence across rounds**

For identical `candidate_id` values, reject a changed normalized DOI, changed equal-authority alternate ID, or incompatible metadata. Allow a newly added DOI only when a stable equal alternate ID already proves continuity; otherwise emit `stable_candidate_identity_unresolved`.

- [x] **Step 5: Run identity and full regression gates**

```powershell
python -m unittest discover -s tests -p "test_validate_m1_bundle.py" -v
python -m py_compile skills/engineering-research-copilot/scripts/validate_m1_bundle.py tests/test_validate_m1_bundle.py
```

Expected: all identity tests and prior terminal-state tests pass.

- [x] **Step 6: Commit identity hardening**

```powershell
git add -- skills/engineering-research-copilot/references/core-citation-integrity.md skills/engineering-research-copilot/scripts/validate_m1_bundle.py tests/test_validate_m1_bundle.py
git commit -m "fix: enforce deterministic candidate identity deduplication"
```

---

### Task 4: Align one closed FeedbackDelta schema

**Files:**
- Modify: `skills/engineering-research-copilot/references/core-paper-calibration.md`
- Modify: `skills/engineering-research-copilot/references/core-feedback-rollback.md`
- Modify: `skills/engineering-research-copilot/scripts/validate_m1_bundle.py`
- Modify: `tests/test_validate_m1_bundle.py`
- Modify: `evals/m1/fixtures/*.json`
- Create: `evals/m1/results/2026-08-04-m1.1-to-m1.2-migration.md`

**Interfaces:**
- Consumes: material cause paths `feedback_delta.rejected|reset|added[index]`.
- Produces: exact object shapes for all four feedback lists while preserving the existing path grammar.

- [ ] **Step 1: Freeze the canonical item shapes in both references**

Use these exact closed objects:

```yaml
inherited:
  - object_id: "public-data-only"
    value: "Use public data only"
rejected:
  - object_id: "random-split-dependent-designs"
    value: "Designs that mix one physical source across train and test"
    reason: "They can inflate evaluation through leakage"
reset:
  - object_id: "round-one-title-level-fit"
    previous_value: "Title relevance counted as preliminary fit"
    reason: "Title evidence cannot establish isolation or leakage resistance"
added:
  - object_id: "cross-load-evaluation-priority"
    value: "Prioritize cross-load or unseen-condition evaluation"
    reason: "The user promoted this evidence to a primary filter"
```

The allowed/required fields are identical: inherited `{object_id,value}`; rejected `{object_id,value,reason}`; reset `{object_id,previous_value,reason}`; added `{object_id,value,reason}`. Unknown fields are invalid.

- [ ] **Step 2: Add FeedbackDelta schema tests**

Add:

```python
def test_added_requires_value_and_reason(self):
    for missing in ("value", "reason"):
        bundle = make_complete_fixture_bundle()
        del bundle["feedback_delta"]["added"][0][missing]
        self.assertIn("feedback_added_fields_invalid", validate_bundle(bundle)["errors"])

def test_reset_requires_previous_value_and_reason(self):
    for missing in ("previous_value", "reason"):
        bundle = make_complete_fixture_bundle()
        bundle["feedback_delta"]["reset"] = [{"object_id": "old-fit", "previous_value": "title fit", "reason": "insufficient"}]
        bundle["feedback_delta"]["query_changes"][0]["cause_refs"].append("feedback_delta.reset[0]")
        del bundle["feedback_delta"]["reset"][0][missing]
        self.assertIn("feedback_reset_fields_invalid", validate_bundle(bundle)["errors"])

def test_rejected_requires_value_and_reason(self):
    for missing in ("value", "reason"):
        bundle = make_complete_fixture_bundle()
        del bundle["feedback_delta"]["rejected"][0][missing]
        self.assertIn("feedback_rejected_fields_invalid", validate_bundle(bundle)["errors"])

def test_inherited_requires_object_id_and_value(self):
    bundle = make_complete_fixture_bundle()
    bundle["feedback_delta"]["inherited"] = [{"object_id": "public-data-only"}]
    self.assertIn("feedback_inherited_fields_invalid", validate_bundle(bundle)["errors"])

def test_feedback_item_unknown_fields_are_invalid(self):
    bundle = make_complete_fixture_bundle()
    bundle["feedback_delta"]["added"][0]["extra"] = "closed schema"
    self.assertIn("feedback_added_fields_invalid", validate_bundle(bundle)["errors"])

def test_feedback_material_refs_resolve_after_schema_change(self):
    bundle = make_complete_fixture_bundle()
    result = validate_bundle(bundle)
    self.assertNotIn("feedback_material_cause_untracked", result["errors"])
    self.assertNotIn("feedback_query_cause_unresolved", result["errors"])
```

Each test mutates one otherwise-valid `m1.2` bundle and asserts a stable closed error code.

- [ ] **Step 3: Implement the item validator**

Add:

```python
FEEDBACK_ITEM_FIELDS = {
    "inherited": {"object_id", "value"},
    "rejected": {"object_id", "value", "reason"},
    "reset": {"object_id", "previous_value", "reason"},
    "added": {"object_id", "value", "reason"},
}

def _validate_feedback_items(feedback: dict, result: _Result) -> None:
    for kind, expected in FEEDBACK_ITEM_FIELDS.items():
        items = _as_list(feedback.get(kind), result, f"invalid_feedback_{kind}")
        for item in items:
            if not isinstance(item, dict) or set(item) != expected:
                result.error(f"feedback_{kind}_fields_invalid")
                continue
            if any(not _nonempty_text(item[field]) for field in expected):
                result.error(f"feedback_{kind}_value_invalid")
```

Retain material cause refs only for rejected/reset/added. Inherited remains visible but cannot be used as a material query-change cause.

- [ ] **Step 4: Migrate generators and all fixtures atomically**

Update the test factory and all six fixture files to emit the exact item shapes. Do not edit historical result Markdown. Add the migration sidecar with:

```markdown
# M1.1 to M1.2 Evaluation Migration

- Historical Markdown result schema: `m1.1`
- Canonical machine schema after hardening: `m1.2`
- Historical result files are preserved and are not validator inputs.
- Accepted machine artifacts are separate `.bundle.json`, `.validation.json`, and `.provenance.json` files.
```

- [ ] **Step 5: Run the full test, fixture, and Skill gates**

```powershell
python -m unittest discover -s tests -p "test_validate_m1_bundle.py" -v
python -X utf8 C:\Users\94310\.codex\skills\.system\skill-creator\scripts\quick_validate.py D:\engineering-research-copilot\skills\engineering-research-copilot
```

Run all six fixture CLIs and compare their closed outputs with `offline-results.json` using the existing Task 2 read-only fixture check; expected exit/status pairs are `0/valid`, three `1/invalid`, and two `2/evidence_incomplete`.

- [ ] **Step 6: Commit FeedbackDelta alignment**

```powershell
git add -- skills/engineering-research-copilot/references/core-paper-calibration.md skills/engineering-research-copilot/references/core-feedback-rollback.md skills/engineering-research-copilot/scripts/validate_m1_bundle.py tests/test_validate_m1_bundle.py evals/m1/fixtures evals/m1/results/2026-08-04-m1.1-to-m1.2-migration.md
git commit -m "fix: align FeedbackDelta schema across contracts and validator"
```

---

### Task 5: Close ResearchBrief, SearchPlan, and query-change binding

**Files:**
- Modify: `skills/engineering-research-copilot/references/core-paper-calibration.md`
- Modify: `skills/engineering-research-copilot/references/core-feedback-rollback.md`
- Modify: `skills/engineering-research-copilot/scripts/validate_m1_bundle.py`
- Modify: `tests/test_validate_m1_bundle.py`
- Modify: `evals/m1/fixtures/*.json`

**Interfaces:**
- Consumes: complete per-round `research_brief`, `search_plan`, and FeedbackDelta `query_changes`.
- Produces: `_validate_research_brief()`, `_validate_search_plan()`, and same-query-ID before/after binding.

- [ ] **Step 1: Add closed-shape tests**

Add:

```python
def test_feedback_before_must_match_same_query_id(self):
    bundle = make_complete_fixture_bundle()
    bundle["feedback_delta"]["query_changes"][0]["query_id"] = "Q1-R1"
    self.assertIn("feedback_after_query_id_mismatch", validate_bundle(bundle)["errors"])

def test_duplicate_query_id_is_invalid(self):
    bundle = make_complete_fixture_bundle()
    query = json.loads(json.dumps(bundle["round2"]["search_plan"]["queries"][0]))
    bundle["round2"]["search_plan"]["queries"].append(query)
    self.assertIn("duplicate_query_id", validate_bundle(bundle)["errors"])

def test_missing_query_text_is_invalid(self):
    bundle = make_complete_fixture_bundle()
    del bundle["round1"]["search_plan"]["queries"][0]["query_text"]
    self.assertIn("query_fields_invalid", validate_bundle(bundle)["errors"])

def test_query_branch_id_mismatch_is_invalid(self):
    bundle = make_complete_fixture_bundle()
    bundle["round2"]["search_plan"]["branch_id"] = "branch-b"
    self.assertIn("search_plan_branch_mismatch", validate_bundle(bundle)["errors"])

def test_brief_unknown_field_is_invalid(self):
    bundle = make_complete_fixture_bundle()
    bundle["round1"]["research_brief"]["extra"] = "closed schema"
    self.assertIn("research_brief_fields_invalid", validate_bundle(bundle)["errors"])

def test_plan_missing_boundary_is_invalid(self):
    bundle = make_complete_fixture_bundle()
    del bundle["round1"]["search_plan"]["source_boundary"]
    self.assertIn("search_plan_fields_invalid", validate_bundle(bundle)["errors"])

def test_boolean_brief_version_is_invalid(self):
    bundle = make_complete_fixture_bundle()
    bundle["round1"]["research_brief"]["brief_version"] = True
    self.assertIn("invalid_brief_version", validate_bundle(bundle)["errors"])

def test_round_two_branch_id_mismatch_is_invalid(self):
    bundle = make_complete_fixture_bundle()
    bundle["round2"]["research_brief"]["branch_id"] = "branch-b"
    bundle["round2"]["search_plan"]["branch_id"] = "branch-b"
    self.assertIn("cross_round_branch_mismatch", validate_bundle(bundle)["errors"])
```

- [ ] **Step 2: Add exact field constants and validators**

Use:

```python
RESEARCH_BRIEF_FIELDS = {
    "brief_version", "branch_id", "engineering_object", "target_problem",
    "target_metric", "available_data", "resources", "time_budget",
    "preferred_routes", "excluded_routes", "hard_constraints",
    "soft_preferences", "open_questions", "evidence_needs",
}
SEARCH_PLAN_FIELDS = {
    "round", "brief_version", "branch_id", "time_boundary",
    "language_boundary", "source_boundary", "queries", "limitations",
}
QUERY_FIELDS = {
    "query_id", "purpose", "query_text", "expected_evidence_role",
    "inclusion_terms", "exclusion_terms",
}
QUERY_PURPOSES = {"direct_problem", "method", "transfer_bridge", "counter_limitation"}
```

Reject missing and unknown fields. Require positive non-boolean integer `brief_version`; nonempty `branch_id`; string fields for object/problem/metric/time budget; list values for every plural Brief field and all Plan boundaries/limitations; unique nonempty query IDs and query text; closed purposes and evidence roles.

- [ ] **Step 3: Bind every query change to its own ID**

Replace global text search with indexed lookup:

```python
queries_one = {query["query_id"]: query for query in plan_one["queries"]}
queries_two = {query["query_id"]: query for query in plan_two["queries"]}
for change in feedback["query_changes"]:
    query_id, before, after = change["query_id"], change["before"], change["after"]
    first, second = queries_one.get(query_id), queries_two.get(query_id)
    if before and (first is None or not _contains_exact_text(first, before)):
        result.error("feedback_before_query_id_mismatch")
    if after and (second is None or not _contains_exact_text(second, after)):
        result.error("feedback_after_query_id_mismatch")
```

For a newly added query, require ID absent from round one and present in round two. For a removed query, require ID present in round one and absent from round two. M1.2 does not introduce a branch-change object, so require the same nonempty `branch_id` in both Briefs and both Plans.

- [ ] **Step 4: Run all validator tests and fixture replay**

```powershell
python -m unittest discover -s tests -p "test_validate_m1_bundle.py" -v
```

Expected: all tests pass. Re-run the six Task 2 fixture commands and require their exit/status/error/gap arrays to match the frozen results.

- [ ] **Step 5: Commit Brief/Plan closure**

```powershell
git add -- skills/engineering-research-copilot/references/core-paper-calibration.md skills/engineering-research-copilot/references/core-feedback-rollback.md skills/engineering-research-copilot/scripts/validate_m1_bundle.py tests/test_validate_m1_bundle.py evals/m1/fixtures
git commit -m "fix: close research brief and search plan validation"
```

---

### Task 6: Generate and validate paper-map renderings deterministically

**Files:**
- Create: `skills/engineering-research-copilot/scripts/render_m1_map.py`
- Modify: `skills/engineering-research-copilot/scripts/validate_m1_bundle.py`
- Modify: `skills/engineering-research-copilot/references/core-paper-map.md`
- Create: `tests/test_render_m1_map.py`
- Modify: `tests/test_validate_m1_bundle.py`
- Modify: `evals/m1/fixtures/*.json`

**Interfaces:**
- Consumes: structured `paper_map.nodes` and `paper_map.edges`.
- Produces: `render_mermaid(paper_map) -> str`, `render_text_fallback(paper_map) -> list[dict]`, and exact rendering validation.

- [ ] **Step 1: Write deterministic renderer tests**

Create tests for:

```python
def test_fit_score_is_required(self):
    bundle = make_complete_fixture_bundle()
    del bundle["round1"]["paper_map"]["nodes"][0]["fit_score"]
    self.assertIn("invalid_fit_score", validate_bundle(bundle)["errors"])

def test_fit_score_out_of_range_is_invalid(self):
    bundle = make_complete_fixture_bundle()
    bundle["round1"]["paper_map"]["nodes"][0]["fit_score"] = 1.01
    self.assertIn("invalid_fit_score", validate_bundle(bundle)["errors"])

def test_fallback_text_must_preserve_node_note(self):
    bundle = make_complete_fixture_bundle()
    bundle["round1"]["paper_map"]["text_fallback"][0]["text"] = "changed"
    self.assertIn("map_fallback_not_deterministic", validate_bundle(bundle)["errors"])

def test_fallback_edge_must_preserve_edge_note(self):
    bundle = make_complete_fixture_bundle()
    bundle["round1"]["paper_map"]["edges"] = [{"source":"fixture:P01","target":"fixture:P02","relation":"shared_method","strength":"medium","confidence":"medium","basis_level":"metadata_level","note":"same deterministic method"}]
    bundle["round1"]["paper_map"]["text_fallback"] = render_text_fallback(bundle["round1"]["paper_map"])
    bundle["round1"]["paper_map"]["text_fallback"][-1]["text"] = "changed"
    self.assertIn("map_fallback_not_deterministic", validate_bundle(bundle)["errors"])

def test_selected_paper_node_must_have_fit_score(self):
    bundle = make_complete_fixture_bundle()
    bundle["round2"]["paper_map"]["nodes"][0]["fit_score"] = True
    self.assertIn("invalid_fit_score", validate_bundle(bundle)["errors"])

def test_render_text_fallback_is_deterministic(self):
    paper_map = _paper_map(1, ["fixture:P01"])
    self.assertEqual(render_text_fallback(paper_map), render_text_fallback(paper_map))

def test_render_mermaid_is_deterministic_and_escaped(self):
    paper_map = _paper_map(1, ["fixture:P01"])
    paper_map["nodes"][0]["short_note"] = 'quote " and pipe |'
    rendered = render_mermaid(paper_map)
    self.assertEqual(rendered, render_mermaid(paper_map))
    self.assertNotIn('quote " and pipe |', rendered)
```

Expected fallback text is exactly `"{id}: {short_note}"` for nodes and `"{source} --{relation}--> {target}: {note}"` for edges.

- [ ] **Step 2: Implement the pure renderers**

Create `render_m1_map.py` with no file or network I/O:

```python
from __future__ import annotations
from typing import Any

def render_text_fallback(paper_map: dict[str, Any]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for node in paper_map["nodes"]:
        entry = {key: node[key] for key in ("id", "node_type", "basis_level")}
        entry["entry_type"] = "node"
        if node["node_type"] == "paper":
            entry.update({
                "evidence_role": node["evidence_role"],
                "verification_status": node["verification_status"],
            })
        entry["text"] = f'{node["id"]}: {node["short_note"]}'
        output.append(entry)
    for edge in paper_map["edges"]:
        output.append({
            "entry_type": "edge", "source": edge["source"],
            "target": edge["target"], "relation": edge["relation"],
            "basis_level": edge["basis_level"],
            "text": f'{edge["source"]} --{edge["relation"]}--> {edge["target"]}: {edge["note"]}',
        })
    return output
```

`render_mermaid()` must sort neither nodes nor edges; preserve structured order, escape backslash, quote, newline, bracket, and pipe characters, and include ID, node type, paper role/status, basis, fit score, relation, and edge basis in visible labels.

- [ ] **Step 3: Require exact generated outputs**

Add `mermaid` to the closed PaperMap fields. For each paper node require `type(fit_score) in {int, float}` while rejecting booleans, and enforce `0 <= fit_score <= 1`. Cluster nodes must not contain `fit_score`, `evidence_role`, or `verification_status`.

Validate:

```python
if paper_map.get("text_fallback") != render_text_fallback(paper_map):
    result.error("map_fallback_not_deterministic")
if paper_map.get("mermaid") != render_mermaid(paper_map):
    result.error("map_mermaid_not_deterministic")
```

- [ ] **Step 4: Regenerate fixture maps from the structured source**

Update `_paper_map()` to call both renderers after nodes and edges exist. Regenerate each fixture map through the same helper; do not hand-edit fallback or Mermaid separately.

- [ ] **Step 5: Run renderer, validator, and Skill gates**

```powershell
python -m unittest discover -s tests -p "test_render_m1_map.py" -v
python -m unittest discover -s tests -p "test_validate_m1_bundle.py" -v
python -m py_compile skills/engineering-research-copilot/scripts/render_m1_map.py skills/engineering-research-copilot/scripts/validate_m1_bundle.py
python -X utf8 C:\Users\94310\.codex\skills\.system\skill-creator\scripts\quick_validate.py D:\engineering-research-copilot\skills\engineering-research-copilot
```

- [ ] **Step 6: Commit deterministic map equivalence**

```powershell
git add -- skills/engineering-research-copilot/scripts/render_m1_map.py skills/engineering-research-copilot/scripts/validate_m1_bundle.py skills/engineering-research-copilot/references/core-paper-map.md tests/test_render_m1_map.py tests/test_validate_m1_bundle.py evals/m1/fixtures
git commit -m "fix: enforce paper map and fallback equivalence"
```

---

### Task 7: Convert accepted real cases into machine-verifiable artifacts

**Files:**
- Create: `skills/engineering-research-copilot/scripts/validate_citation_gate.py`
- Create: `tests/test_validate_citation_gate.py`
- Create: `evals/m1/results/2026-08-04-pwr-sb-loca-rerun.bundle.json`
- Create: `evals/m1/results/2026-08-04-pwr-sb-loca-rerun.validation.json`
- Create: `evals/m1/results/2026-08-04-pwr-sb-loca-rerun.provenance.json`
- Create: `evals/m1/results/2026-08-04-bearing-fault-rerun-2.bundle.json`
- Create: `evals/m1/results/2026-08-04-bearing-fault-rerun-2.validation.json`
- Create: `evals/m1/results/2026-08-04-bearing-fault-rerun-2.provenance.json`
- Create: `evals/m1/results/2026-08-04-citation-audit.gate.json`
- Create: `evals/m1/results/2026-08-04-citation-audit.validation.json`
- Create: `evals/m1/results/2026-08-04-citation-audit.provenance.json`
- Create: `evals/m1/replay_machine_artifacts.py`

**Interfaces:**
- Consumes: accepted Markdown evidence A `2026-08-04-pwr-sb-loca-rerun.md`, B `2026-08-04-bearing-fault-rerun-2.md`, C `2026-08-04-citation-audit.md` plus supplement, and the final `m1.2` validators.
- Produces: one complete A Bundle, one second-round-incomplete B Bundle, one citation-gate C object, exact validator outputs, provenance hashes, and an offline replay gate.

- [ ] **Step 1: Define and test the citation-gate schema**

Require exactly:

```json
{
  "schema_version": "citation-gate.1",
  "terminal_state": "CITATION_BLOCKED",
  "verification_status": "conflicted",
  "recommendation_eligible": false,
  "checked_sources": [],
  "blocking_reasons": []
}
```

`checked_sources` must be nonempty closed source objects using the same source types/results/timestamps as M1. `blocking_reasons` must be nonempty strings. The CLI prints `{status,errors,evidence_gaps}` and uses exit `0` for a structurally valid blocked gate, exit `1` for invalid input.

Add tests that reject `recommendation_eligible: true`, a non-conflicted status, a missing source, unknown fields, invalid timestamps, and any `round1`/`round2` field.

- [ ] **Step 2: Transcribe Case A into a complete canonical Bundle**

Copy every accepted round-one and clean-rerun round-two object, including all candidates and checked sources, into `2026-08-04-pwr-sb-loca-rerun.bundle.json`. Set only:

```json
{
  "schema_version": "m1.2",
  "terminal_state": "M1_COMPLETE",
  "stopped_after_round": 2,
  "outcome": "complete"
}
```

Migrate the accepted semantics into the closed `m1.2` FeedbackDelta, Brief, Plan, and map shapes from Tasks 4–6; do not copy obsolete `m1.1` field shapes. Do not add fixture mode. Generate both maps through `render_m1_map.py`. Run the Bundle validator, require exit `0`, and save its exact stdout object as `.validation.json`.

- [ ] **Step 3: Transcribe Case B into a second-round incomplete Bundle**

Copy the accepted second clean rerun exactly. Keep 16 verified/deduplicated candidates and only P17, P18, and P25 selected. Set:

```json
{
  "schema_version": "m1.2",
  "terminal_state": "WAITING_FOR_EVIDENCE_DECISION",
  "stopped_after_round": 2,
  "outcome": "evidence_incomplete"
}
```

Keep the exact missing-two-paper evidence gap. Run the Bundle validator, require exit `2`, and save exact stdout as `.validation.json`. Do not expand the selection to obtain exit `0`.

Migrate only schema representation: preserve every accepted candidate identity, checked source, basis, disposition, limitation, and evidence gap from the Markdown.

- [ ] **Step 4: Transcribe Case C without inventing rounds**

Create the citation-gate object from the live Crossref and official NeurIPS checked sources already recorded. Preserve the supplied title/DOI conflict, `recommendation_eligible: false`, and both blocking reasons. Run `validate_citation_gate.py`, require exit `0`, and save exact stdout.

- [ ] **Step 5: Bind each artifact to provenance hashes**

Each provenance object must use this closed shape:

```json
{
  "schema_version": "m1-provenance.1",
  "case_id": "case-a-pwr-sb-loca",
  "run_commit": "123a03779d001198c895e60949fa7b9c53e2f56d",
  "input_markdown": "evals/m1/results/2026-08-04-pwr-sb-loca-rerun.md",
  "input_frozen_range": "round-one capture plus frozen feedback recorded in the result",
  "read_other_cases": false,
  "verification_window": {"timezone": "Asia/Shanghai", "started_at": "2026-08-04T19:01:35+08:00", "ended_at": "2026-08-04T19:03:27+08:00"},
  "tools": [],
  "authoritative_sources": [],
  "execution_deviations": [],
  "bundle_sha256": "64 lowercase hexadecimal characters",
  "validation_sha256": "64 lowercase hexadecimal characters"
}
```

Use the actual times/tools/sources from each case, not the example values from another case. Compute SHA-256 over exact saved bytes after newline normalization is finalized.

- [ ] **Step 6: Implement offline artifact replay**

`replay_machine_artifacts.py` must:

1. load A/B Bundle plus C gate;
2. recompute and compare provenance hashes;
3. call the correct in-process validator;
4. compare the returned object byte-semantically with `.validation.json`;
5. assert A `valid`, B `evidence_incomplete`, C `valid`;
6. exit `1` with closed JSON on any mismatch and `0` with a per-case summary on success.

- [ ] **Step 7: Run and independently audit machine artifacts**

```powershell
python evals/m1/replay_machine_artifacts.py
python skills/engineering-research-copilot/scripts/validate_m1_bundle.py evals/m1/results/2026-08-04-pwr-sb-loca-rerun.bundle.json
python skills/engineering-research-copilot/scripts/validate_m1_bundle.py evals/m1/results/2026-08-04-bearing-fault-rerun-2.bundle.json
python skills/engineering-research-copilot/scripts/validate_citation_gate.py evals/m1/results/2026-08-04-citation-audit.gate.json
```

Expected exits/statuses: A `0/valid`; B `2/evidence_incomplete`; C `0/valid`. A fresh reviewer must compare every selected ID, status, basis, source, disposition, and gap against the preserved Markdown before approval.

- [ ] **Step 8: Commit machine-valid forward evidence**

```powershell
git add -- skills/engineering-research-copilot/scripts/validate_citation_gate.py tests/test_validate_citation_gate.py evals/m1/results/*.bundle.json evals/m1/results/*.gate.json evals/m1/results/*.validation.json evals/m1/results/*.provenance.json evals/m1/replay_machine_artifacts.py
git commit -m "test: add machine-valid M1 forward evaluation bundles"
```

---

### Task 8: Add deterministic offline replay and CI

**Files:**
- Create: `evals/m1/replay_offline_results.py`
- Create: `tests/test_replay_offline_results.py`
- Create: `.github/workflows/m1-validation.yml`
- Modify: `evals/m1/offline-results.json`

**Interfaces:**
- Consumes: unit tests, six frozen fixtures, A/B/C machine artifacts, validators, and the standard Skill validator.
- Produces: one Linux CI job requiring no networked scholarly source.

- [ ] **Step 1: Implement fixture replay before the workflow**

The script loads `offline-results.json`, runs each stored fixture through `validate_bundle()` in process, derives exit `{valid:0, invalid:1, evidence_incomplete:2}`, and compares status, errors, and evidence gaps exactly. It prints one closed JSON object and exits `0` only when every record matches.

Implement the reusable core as:

```python
EXIT_BY_STATUS = {"valid": 0, "invalid": 1, "evidence_incomplete": 2}

def replay_records(records: list[dict], root: Path) -> dict:
    mismatches: list[dict] = []
    for expected in records:
        payload = json.loads((root / expected["fixture"]).read_text(encoding="utf-8"))
        actual = validate_bundle(payload)
        actual_exit = EXIT_BY_STATUS[actual["status"]]
        compared = {
            "exit_code": actual_exit,
            "status": actual["status"],
            "errors": actual["errors"],
            "evidence_gaps": actual["evidence_gaps"],
        }
        wanted = {key: expected[key] for key in compared}
        if compared != wanted:
            mismatches.append({"fixture": expected["fixture"], "expected": wanted, "actual": compared})
    return {"status": "valid" if not mismatches else "invalid", "mismatches": mismatches}
```

- [ ] **Step 2: Test replay against one intentional mismatch**

Add a unit test that supplies an expected `valid` status for the blocked-conflict fixture and asserts replay returns a mismatch without changing the fixture or validator.

```python
def test_replay_reports_expected_status_mismatch(tmp_path: Path) -> None:
    repository = Path(__file__).resolve().parents[1]
    frozen = json.loads((repository / "evals/m1/offline-results.json").read_text(encoding="utf-8"))
    expected = next(record.copy() for record in frozen["results"] if record["fixture"].endswith("blocked-conflict.json"))
    expected.update({"exit_code": 0, "status": "valid", "errors": [], "evidence_gaps": []})
    result = replay_records([expected], repository)
    assert result["status"] == "invalid"
    assert result["mismatches"][0]["fixture"].endswith("blocked-conflict.json")
```

- [ ] **Step 3: Create the GitHub Actions workflow**

Use:

```yaml
name: M1 Validation

on:
  push:
    branches:
      - main
      - "codex/**"
  pull_request:

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.13"
      - name: Compile
        run: |
          python -m py_compile \
            skills/engineering-research-copilot/scripts/validate_m1_bundle.py \
            skills/engineering-research-copilot/scripts/render_m1_map.py \
            skills/engineering-research-copilot/scripts/validate_citation_gate.py \
            evals/m1/replay_offline_results.py \
            evals/m1/replay_machine_artifacts.py
      - name: Unit tests
        run: python -m unittest discover -s tests -p "test_*.py" -v
      - name: Replay fixtures
        run: python evals/m1/replay_offline_results.py
      - name: Replay machine artifacts
        run: python evals/m1/replay_machine_artifacts.py
```

The official Skill validator is environment-owned and remains a required local gate; the GitHub workflow must not reference a nonexistent runner `$HOME/.codex` path.

- [ ] **Step 4: Run the exact Linux-equivalent commands locally**

```powershell
python -m py_compile skills/engineering-research-copilot/scripts/validate_m1_bundle.py skills/engineering-research-copilot/scripts/render_m1_map.py skills/engineering-research-copilot/scripts/validate_citation_gate.py evals/m1/replay_offline_results.py evals/m1/replay_machine_artifacts.py
python -m unittest discover -s tests -p "test_*.py" -v
python evals/m1/replay_offline_results.py
python evals/m1/replay_machine_artifacts.py
python -X utf8 C:\Users\94310\.codex\skills\.system\skill-creator\scripts\quick_validate.py D:\engineering-research-copilot\skills\engineering-research-copilot
```

Expected: every command exits `0`; fixture replay internally accepts expected exit `1` and `2` cases without failing the job.

- [ ] **Step 5: Commit CI**

```powershell
git add -- evals/m1/replay_offline_results.py evals/m1/offline-results.json .github/workflows/m1-validation.yml tests/test_replay_offline_results.py
git commit -m "ci: validate M1 contracts and fixtures"
```

---

### Task 9: Close M1.2 only after local and remote acceptance

**Files:**
- Create: `evals/m1/results/2026-08-04-m1.2-final-validation.md`
- Modify: `STATUS.md`
- Modify: `docs/superpowers/plans/2026-08-04-m1-two-round-paper-calibration.md`
- Modify: `docs/superpowers/plans/2026-08-04-m1-acceptance-hardening.md`

**Interfaces:**
- Consumes: all local gates, machine artifacts, independent reviews, final branch HEAD, and a clean GitHub Actions run on that exact HEAD.
- Produces: honest M1 `COMPLETE`, acceptance revision `m1.2`, or retained `IN_PROGRESS` with the exact unpassed gate.

- [ ] **Step 1: Run the final local gate matrix**

Run all Task 8 commands, plus:

```powershell
$skill='skills/engineering-research-copilot/SKILL.md'
(Get-Content -LiteralPath $skill -Encoding UTF8).Count
git diff --check
git status --short
git log --oneline codex/m1-paper-calibration..HEAD
```

Expected: root Skill below 500 lines; all validation commands exit `0`; only planned M1.1 files and independent commits exist.

- [ ] **Step 2: Write the exact final validation record**

Record command, exit, test count, fixture summary, A/B/C artifact hashes and statuses, standard Skill validator output, branch, HEAD, clean-tree result, and independent review decisions. Preserve failed test attempts separately and never replace them with a later pass.

- [ ] **Step 3: Obtain authorization before remote mutation**

If the user has not explicitly requested a push for this hardening branch, stop with M1.1 `IN_PROGRESS` and ask for push authorization. Do not infer authorization from the earlier M1 branch push.

- [ ] **Step 4: Push and require exact-HEAD CI**

After authorization:

```powershell
git push -u origin codex/m1-acceptance-hardening
gh run list --branch codex/m1-acceptance-hardening --workflow "M1 Validation" --limit 5
```

Wait for the run whose `headSha` equals local `git rev-parse HEAD`. Require conclusion `success`; a run on another SHA does not satisfy the gate.

- [ ] **Step 5: Update status only after the CI gate**

Set:

```markdown
## Active milestone

`M1 — Two-round paper calibration and evidence map`

Status: `COMPLETE`

Acceptance revision: `m1.2`

Validated by:

- clean CI run on the final HEAD;
- complete two-round machine-valid Case A;
- second-round evidence-incomplete machine-valid Case B;
- citation-conflict gate Case C;
- DOI and alternate-ID identity tests;
- round-one and round-two terminal-state tests.
```

Keep M2–M5 `NOT_STARTED`.

- [ ] **Step 6: Mark executed plan items and commit closure**

Mark only actually executed checkboxes. Under forward tests record that initial failures remain preserved and accepted reruns/artifacts are named in the final record.

```powershell
git add -- STATUS.md docs/superpowers/plans/2026-08-04-m1-two-round-paper-calibration.md docs/superpowers/plans/2026-08-04-m1-acceptance-hardening.md evals/m1/results/2026-08-04-m1.2-final-validation.md
git commit -m "docs: close M1.2 acceptance hardening"
```

- [ ] **Step 7: Re-run exact-HEAD CI after the closure commit**

Because the closure commit changes HEAD, push it only with authorization and require a second successful `M1 Validation` run on the closure SHA. If it does not pass, revert `STATUS.md` to `IN_PROGRESS` in a new commit and record the failing check; do not claim completion from the pre-closure run.

---

## Self-Review Record

- Spec coverage: Tasks 2–6 cover terminal states, identity, FeedbackDelta, Brief/Plan, and map equivalence. Task 7 converts A/B/C into machine artifacts without rewriting historical Markdown. Task 8 adds standard-library offline CI. Task 9 makes exact-HEAD remote CI a hard completion condition.
- Boundary check: M2–M5, RRC, model downloads, runtime services, method corpus, deployment, and platform integration remain excluded.
- Evidence integrity: Round-one and round-two incomplete states stay `evidence_incomplete`; Case C uses a separate citation-gate schema; expected nonzero fixture exits are asserted rather than suppressed.
- Omission scan: every file, function, schema token, test name, command, status, and commit message required by the plan is explicit.
- Type consistency: root Bundle state uses `schema_version`, `terminal_state`, `stopped_after_round`, and `outcome`; both validators return the same `{status,errors,evidence_gaps}` result object; map renderers consume the same structured map validated by the Bundle validator.
