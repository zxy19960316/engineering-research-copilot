# M1 Two-Round Paper Calibration Implementation Plan

## Implementation record

- Original implementation closed at: `556a408`
- Acceptance hardening branch: `codex/m1-acceptance-hardening`
- Canonical schema under hardening: `m1.2`
- Historical failed forward runs remain preserved under `evals/m1/results/`.
- Final M1.2 validation record will be `evals/m1/results/2026-08-04-m1.2-final-validation.md`.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement and verify the Skill's adaptive research brief, two-round paper calibration, citation eligibility gates, static evidence map, and feedback-driven second search without adding a bundled retrieval service.

**Architecture:** Keep `SKILL.md` as a thin router and place the complete M1 workflow in one new one-level reference. Reuse the frozen citation, map, and rollback references for specialized rules. Add one deterministic, offline JSON bundle validator inside the Skill and keep all fixtures, evaluation prompts, and results outside the installable Skill.

**Tech Stack:** Markdown, YAML examples, Python 3.13 standard library, `unittest`, Mermaid, host-provided scholarly/web search tools.

## Global Constraints

- Execute only M1. Do not implement M2 direction ranking, route generation, M3 method cards, runtime services, deployment, or RRC integration.
- Keep `skills/engineering-research-copilot/SKILL.md` below 500 lines and link every loadable reference directly from it.
- Keep references one level deep and add a contents list when a reference exceeds 100 lines.
- Separate discovery from verification. Never infer a DOI, title, author list, publication status, or citation identifier.
- Block `conflicted`, `not_found`, and `manual_needed` records from recommendations.
- Treat offline fixtures as contract evidence only. They cannot establish that a real citation exists or that live scholarly verification succeeded.
- Keep audits read-only by default. Do not add a network provider, start a service, download a model, upload research material, or connect RRC.
- Run the standard Skill validator after changing `SKILL.md` or its metadata.
- Preserve incomplete and failing evaluation evidence. Do not relabel partial, offline, metadata-only, or abstract-only checks as real completion.
- Stage explicit paths. Do not push unless the user explicitly requests it.

## File Structure

- Modify `STATUS.md`: record M1 as active and later record each acceptance gate without erasing M0 evidence.
- Modify `skills/engineering-research-copilot/SKILL.md`: route paper-search requests through the M1 calibration reference and keep only the high-level control flow.
- Create `skills/engineering-research-copilot/references/core-paper-calibration.md`: define the adaptive brief, query plan, candidate pool, round bundles, evidence gaps, and round transition.
- Modify `skills/engineering-research-copilot/references/core-citation-integrity.md`: distinguish discovered candidates, verified records, recommendation eligibility, and real-verification provenance.
- Modify `skills/engineering-research-copilot/references/core-paper-map.md`: define round-specific selection counts, stable map semantics, and equivalent text fallback.
- Modify `skills/engineering-research-copilot/references/core-feedback-rollback.md`: define the visible `FeedbackDelta` and require feedback reasons to change the next query plan.
- Create `skills/engineering-research-copilot/scripts/validate_m1_bundle.py`: validate saved M1 JSON artifacts offline without making network calls.
- Create `tests/test_validate_m1_bundle.py`: exercise validator success, invalid, and incomplete classifications.
- Create `evals/m1/adversarial-cases.json`: declare fixture-only corruptions without presenting synthetic identifiers as real citations.
- Create `evals/m1/forward-cases.md`: define fresh-context live evaluation prompts and evidence requirements.
- Create `evals/m1/results/`: store dated pass, fail, and not-run evidence only when forward tests are actually executed.

---

### Task 1: Activate M1 and freeze its evidence boundary

**Files:**
- Modify: `STATUS.md`

**Interfaces:**
- Consumes: M0 status `COMPLETE`, root commit `5a5bcba`, and the public `origin` remote.
- Produces: one active milestone, `M1`, with separate offline-contract and live-forward-test gates.

- [x] **Step 1: Confirm the baseline is clean and M0 is complete**

Run:

```powershell
git status -sb
git log -1 --oneline
```

Expected: clean `main` tracking `origin/main` and root commit `5a5bcba`.

- [x] **Step 2: Create the M1 work branch**

Run:

```powershell
git switch -c codex/m1-paper-calibration
```

Expected: current branch becomes `codex/m1-paper-calibration` without changing tracked files.

- [x] **Step 3: Mark M1 active without marking any implementation gate complete**

Set `STATUS.md` to `M1 — Two-round paper calibration and evidence map`, status `IN_PROGRESS`, and retain M0 as `COMPLETE`.

- [x] **Step 4: Review the status-only diff**

Run:

```powershell
git diff -- STATUS.md
```

Expected: only milestone activation and current Git remote/branch facts change.

### Task 2: Define the complete paper-calibration state contract

**Files:**
- Create: `skills/engineering-research-copilot/references/core-paper-calibration.md`
- Modify: `skills/engineering-research-copilot/SKILL.md`

**Interfaces:**
- Consumes: `core-citation-integrity.md`, `core-paper-map.md`, and `core-feedback-rollback.md`.
- Produces: `ResearchBrief`, `SearchPlan`, `CandidatePool`, `RoundBundle`, and `FeedbackDelta` contracts used by all later M1 tasks.

- [x] **Step 1: Add the M1 reference with explicit contents and state flow**

Write these sections in imperative language: `Build the brief`, `Plan the search`, `Assemble the pool`, `Select round one`, `Apply feedback`, `Select round two`, `Report incomplete evidence`, and `Stop at the M1 boundary`.

Define the brief exactly as:

```yaml
research_brief:
  brief_version: 1
  branch_id: "branch-a"
  engineering_object: ""
  target_problem: ""
  target_metric: ""
  available_data: []
  resources: []
  time_budget: ""
  preferred_routes: []
  excluded_routes: []
  hard_constraints: []
  soft_preferences: []
  open_questions: []
  evidence_needs: []
```

Ask at most three questions and only for missing fields that materially change query construction or recommendation eligibility.

- [x] **Step 2: Define a query plan that exposes purpose and boundaries**

Use:

```yaml
search_plan:
  round: 1
  brief_version: 1
  branch_id: "branch-a"
  time_boundary: ""
  language_boundary: []
  source_boundary: []
  queries:
    - query_id: "Q1"
      purpose: "direct_problem"
      query_text: ""
      expected_evidence_role: "direct_problem"
      inclusion_terms: []
      exclusion_terms: []
  limitations: []
```

Require the system to report a boundary instead of claiming exhaustive or novelty-complete coverage.

- [x] **Step 3: Define candidate and round bundles**

Use stable candidate IDs within one calibration cycle and require every selected ID to resolve to exactly one verified record:

```yaml
round_bundle:
  schema_version: "m1.1"
  round: 1
  research_brief: {}
  search_plan: {}
  candidate_pool: []
  selected_ids: []
  paper_map: {}
  evidence_gaps: []
  search_limitations: []
```

Require 15–20 verified, deduplicated round-one candidates and eight selected papers when reliable evidence exists. If the pool or role coverage is insufficient, return `evidence_incomplete`, keep the gap visible, and never pad with weak or unverified records.

- [x] **Step 4: Route paper calibration through the new reference**

In `SKILL.md`, change the paper route to load `core-paper-calibration.md` plus the three specialized core references. Keep the root sequence concise and remove duplicated low-level fields from the root if the new reference owns them.

- [x] **Step 5: Validate root routing**

Run:

```powershell
python -X utf8 C:\Users\94310\.codex\skills\.system\skill-creator\scripts\quick_validate.py D:\engineering-research-copilot\skills\engineering-research-copilot
```

Expected: `Skill is valid!`.

- [x] **Step 6: Commit the state contract**

Run:

```powershell
git add skills/engineering-research-copilot/SKILL.md skills/engineering-research-copilot/references/core-paper-calibration.md
git commit -m "feat: define M1 paper calibration workflow"
```

Expected: one commit containing only the root route and M1 workflow reference.

### Task 3: Tighten verification, deduplication, and eligibility gates

**Files:**
- Modify: `skills/engineering-research-copilot/references/core-citation-integrity.md`

**Interfaces:**
- Consumes: discovery hits from the host and the frozen verification states.
- Produces: a `VerifiedPaperRecord` plus `recommendation_eligible: true|false` and explicit provenance.

- [x] **Step 1: Separate candidate discovery records from verified records**

Require discovery records to remain `unverified_candidate` until an authoritative source has been checked. Do not allow a search snippet, aggregator match, or model memory to set a verified state.

- [x] **Step 2: Add closed provenance fields**

Require:

```yaml
verification:
  status: "verified_primary"
  checked_sources:
    - source_type: "doi_registry"
      canonical_record: ""
      checked_at: "ISO-8601"
      result: "match"
  title_match: "exact|normalized|conflict|not_checked"
  author_match: "exact|compatible|conflict|not_checked"
  version_relation: "same_work|preprint_of|distinct|unknown"
  recommendation_eligible: true
  blocking_reasons: []
```

Permit `recommendation_eligible: true` only for `verified_primary`, `verified_registry`, and conditionally `verified_preprint`. Keep `partial` supplemental and block the three unresolved states.

- [x] **Step 3: Define deterministic deduplication order**

Apply normalized DOI first, then exact official alternate identifier, then normalized title plus first author for candidate review. Never merge records when work type or version relation remains unresolved.

- [x] **Step 4: Add an explicit real-evidence limitation**

State that structural validation can check fields and gates but cannot prove DOI existence. Require a current authoritative lookup for every real recommendation.

- [x] **Step 5: Validate and commit**

Run the standard Skill validator, then:

```powershell
git add skills/engineering-research-copilot/references/core-citation-integrity.md
git commit -m "feat: enforce M1 citation eligibility gates"
```

Expected: the reference validates and no unrelated file is staged.

### Task 4: Specify round-one mapping and feedback-driven round two

**Files:**
- Modify: `skills/engineering-research-copilot/references/core-paper-map.md`
- Modify: `skills/engineering-research-copilot/references/core-feedback-rollback.md`
- Modify: `skills/engineering-research-copilot/references/core-paper-calibration.md`

**Interfaces:**
- Consumes: verified candidate pool, selected round-one IDs, and natural-language user feedback.
- Produces: eight-paper round-one view, a visible `FeedbackDelta`, a changed second-round `SearchPlan`, and five-to-six-paper round-two view.

- [x] **Step 1: Freeze round-one selection behavior**

Select three direct-problem, two method, two transfer/bridge, and one counter/limitation paper when eligible evidence exists. Record a missing role as an evidence gap instead of filling the slot with a weaker paper.

- [x] **Step 2: Make map semantics machine-checkable**

Add these required fields:

```yaml
paper_map:
  round: 1
  node_size_basis: "user_fit"
  legend:
    evidence_roles: ["direct_problem", "method", "transfer_bridge", "counter_limitation"]
    basis_levels: ["metadata_level", "abstract_level", "fulltext_level"]
  nodes: []
  edges: []
  text_fallback: []
```

Require `text_fallback` to preserve the same IDs, roles, relation labels, verification states, and basis levels as Mermaid.

- [x] **Step 3: Define the feedback delta**

Use:

```yaml
feedback_delta:
  from_brief_version: 1
  to_brief_version: 2
  inherited: []
  rejected:
    - object_id: "P3"
      reason: "Requires inaccessible proprietary data"
  reset: []
  added: []
  allocation:
    exploit: 30
    explore: 70
  query_changes:
    - query_id: "Q2-R2"
      reason: "Exclude proprietary-data routes and expand public simulation evidence"
      before: ""
      after: ""
```

Require at least one `query_changes` entry whenever rejection reasons, new constraints, or a reset materially affect the search.

- [x] **Step 4: Define second-round dispositions**

Return five to six papers by default and attach exactly one disposition to each round-one selection: `retained`, `replaced`, `downgraded`, or `removed`. Give a reason and point to the feedback or new evidence that caused it. Expand to at most ten only after an explicit user request.

- [x] **Step 5: Validate and commit**

Run the standard Skill validator, then:

```powershell
git add skills/engineering-research-copilot/references/core-paper-calibration.md skills/engineering-research-copilot/references/core-paper-map.md skills/engineering-research-copilot/references/core-feedback-rollback.md
git commit -m "feat: add M1 feedback-driven paper rounds"
```

Expected: only M1 reference files are committed.

### Task 5: Add the deterministic offline M1 bundle validator

**Files:**
- Create: `skills/engineering-research-copilot/scripts/validate_m1_bundle.py`
- Create: `tests/test_validate_m1_bundle.py`

**Interfaces:**
- Consumes: a UTF-8 JSON file following `schema_version: m1.1`.
- Produces: one closed JSON result with status `valid`, `evidence_incomplete`, or `invalid`; exit codes `0`, `2`, and `1` respectively.

- [x] **Step 1: Write unit tests for the three result classes**

Create fixture builders that use `fixture_mode: true` and internal IDs such as `fixture:P01`. Do not attach DOI, PMID, arXiv ID, or `verified_primary` claims to synthetic records.

Test these cases explicitly:

```python
class ValidateM1BundleTests(unittest.TestCase):
    def test_valid_complete_bundle_returns_valid(self):
        result = validate_bundle(make_complete_fixture_bundle())
        self.assertEqual(result["status"], "valid")

    def test_blocked_status_in_selection_returns_invalid(self):
        bundle = make_complete_fixture_bundle()
        bundle["round1"]["candidate_pool"][0]["verification_status"] = "conflicted"
        result = validate_bundle(bundle)
        self.assertEqual(result["status"], "invalid")
        self.assertIn("selected_record_blocked", result["errors"])

    def test_duplicate_normalized_doi_returns_invalid(self):
        bundle = make_complete_fixture_bundle()
        bundle["fixture_duplicate_doi_tokens"] = ["doi:TEST/SHARED.", "test/shared"]
        result = validate_bundle(bundle)
        self.assertEqual(result["status"], "invalid")
        self.assertIn("duplicate_normalized_doi", result["errors"])

    def test_map_sized_by_citation_count_returns_invalid(self):
        bundle = make_complete_fixture_bundle()
        bundle["round1"]["paper_map"]["node_size_basis"] = "citation_count"
        result = validate_bundle(bundle)
        self.assertEqual(result["status"], "invalid")
        self.assertIn("invalid_node_size_basis", result["errors"])

    def test_feedback_reason_without_query_change_returns_invalid(self):
        bundle = make_complete_fixture_bundle()
        bundle["feedback_delta"]["query_changes"] = []
        result = validate_bundle(bundle)
        self.assertEqual(result["status"], "invalid")
        self.assertIn("feedback_not_applied_to_query", result["errors"])

    def test_short_pool_with_visible_search_limit_returns_incomplete(self):
        bundle = make_complete_fixture_bundle()
        bundle["round1"]["candidate_pool"] = bundle["round1"]["candidate_pool"][:10]
        bundle["round1"]["search_limitations"] = ["Only ten eligible fixture records remained"]
        result = validate_bundle(bundle)
        self.assertEqual(result["status"], "evidence_incomplete")

    def test_short_selection_without_gap_returns_invalid(self):
        bundle = make_complete_fixture_bundle()
        bundle["round1"]["selected_ids"] = bundle["round1"]["selected_ids"][:7]
        result = validate_bundle(bundle)
        self.assertEqual(result["status"], "invalid")
        self.assertIn("selection_count_without_gap", result["errors"])

    def test_abstract_edge_claiming_fulltext_returns_invalid(self):
        bundle = make_complete_fixture_bundle()
        bundle["round1"]["paper_map"]["edges"] = [{
            "source": "fixture:P01",
            "target": "fixture:P02",
            "basis_level": "fulltext_level",
        }]
        result = validate_bundle(bundle)
        self.assertEqual(result["status"], "invalid")
        self.assertIn("edge_basis_exceeds_source", result["errors"])
```

Define `make_complete_fixture_bundle()` in the same test file. Generate 15 candidate records with IDs `fixture:P01` through `fixture:P15`, `verification_status: fixture_only`, `recommendation_eligible: true`, and `basis_level: abstract_level`. Select eight IDs in round one and six in round two, set both maps to `node_size_basis: user_fit`, and include one rejection reason plus one matching query change. The validator may accept `fixture_only` only when `fixture_mode: true`.

- [x] **Step 2: Run tests to verify the validator is absent**

Run:

```powershell
python -m unittest discover -s tests -p "test_validate_m1_bundle.py" -v
```

Expected: FAIL because `validate_m1_bundle` cannot be imported.

- [x] **Step 3: Implement the validator with no network access**

Expose:

```python
def normalize_doi(value: str | None) -> str | None:
    """Normalize a supplied DOI without repairing or inferring it."""

def validate_bundle(bundle: dict) -> dict:
    """Return status, errors, and evidence_gaps without performing I/O."""

def main(argv: list[str] | None = None) -> int:
    """Read one JSON bundle, print one JSON result, and return 0, 1, or 2."""
```

Implement these closed checks:

- require `schema_version == "m1.1"`;
- reject unknown or duplicate candidate IDs;
- reject duplicate normalized DOI values;
- reject selected records with blocked or non-eligible states;
- require 15–20 round-one candidates and eight selected IDs for `valid`;
- require five to six round-two selected IDs for `valid`;
- classify short but honestly bounded pools as `evidence_incomplete`;
- reject short selections that omit an explicit evidence gap;
- require `paper_map.node_size_basis == "user_fit"`;
- require map nodes to match selected IDs;
- require feedback reasons and material constraint changes to produce `query_changes`;
- reject any edge whose claimed basis exceeds its supporting paper basis;
- reject `fixture:` identifiers unless `fixture_mode` is true;
- treat `fixture_duplicate_doi_tokens` as test-only normalization inputs and never as citation records;
- never make a network request or claim that structural checks verified a real identifier.

- [x] **Step 4: Run unit and CLI tests**

Run:

```powershell
python -m unittest discover -s tests -p "test_validate_m1_bundle.py" -v
```

Expected: all validator unit tests pass.

- [x] **Step 5: Commit the validator**

Run:

```powershell
git add skills/engineering-research-copilot/scripts/validate_m1_bundle.py tests/test_validate_m1_bundle.py
git commit -m "test: validate M1 calibration bundles"
```

Expected: deterministic validator and tests only.

### Task 6: Add adversarial fixtures without fabricating citation evidence

**Files:**
- Create: `evals/m1/adversarial-cases.json`
- Create: `evals/m1/fixtures/valid-complete.json`
- Create: `evals/m1/fixtures/blocked-conflict.json`
- Create: `evals/m1/fixtures/feedback-ignored.json`
- Create: `evals/m1/fixtures/map-citation-sized.json`
- Create: `evals/m1/fixtures/evidence-incomplete.json`

**Interfaces:**
- Consumes: validator interface from Task 5.
- Produces: reproducible offline evidence for structural and gating behavior only.

- [x] **Step 1: Declare fixture provenance**

Set `fixture_mode: true`, use only `fixture:` IDs, omit real citation identifiers, and include:

```json
{
  "evidence_class": "offline_contract_fixture",
  "proves": ["state gating", "deduplication behavior", "map semantics", "feedback traceability"],
  "does_not_prove": ["real DOI existence", "publisher metadata accuracy", "live search coverage"]
}
```

- [x] **Step 2: Encode each named failure independently**

Make every failing fixture differ from `valid-complete.json` by one targeted corruption. Record its expected status and exact error code in `adversarial-cases.json`.

- [x] **Step 3: Execute all fixtures and preserve results**

Run every fixture separately with:

```powershell
python skills/engineering-research-copilot/scripts/validate_m1_bundle.py evals/m1/fixtures/valid-complete.json
python skills/engineering-research-copilot/scripts/validate_m1_bundle.py evals/m1/fixtures/blocked-conflict.json
python skills/engineering-research-copilot/scripts/validate_m1_bundle.py evals/m1/fixtures/feedback-ignored.json
python skills/engineering-research-copilot/scripts/validate_m1_bundle.py evals/m1/fixtures/map-citation-sized.json
python skills/engineering-research-copilot/scripts/validate_m1_bundle.py evals/m1/fixtures/evidence-incomplete.json
```

Expect `valid`, `invalid`, `invalid`, `invalid`, and `evidence_incomplete` in the order listed above. Do not convert `evidence_incomplete` to pass.

- [x] **Step 4: Commit fixture evidence**

Run:

```powershell
git add evals/m1
git commit -m "test: add M1 adversarial fixtures"
```

Expected: only M1 evaluation artifacts are committed.

### Task 7: Forward-test real two-round behavior in fresh context

**Files:**
- Create: `evals/m1/forward-cases.md`
- Create on execution: `evals/m1/results/YYYY-MM-DD-<case-name>.md`
- Modify after execution: `STATUS.md`

**Interfaces:**
- Consumes: the completed Skill, host-provided scholarly/web tools, and fresh context.
- Produces: provenance-separated real-search evidence or an explicit failed/not-run record.

- [x] **Step 1: Freeze three prompts before execution**

Include:

1. A well-specified nuclear-engineering × machine-learning request with public-data and simulation constraints.
2. An underspecified non-nuclear engineering request that should ask no more than three high-impact questions.
3. A citation-conflict case where a supplied DOI resolves to metadata inconsistent with the supplied title.

Do not include expected paper titles or the desired answer in the prompts.

- [x] **Step 2: Obtain explicit authorization for fresh-context execution**

Use a new user-authorized subagent or task. Pass only the Skill path and one frozen prompt. Do not leak intended fixes, expected papers, or validator conclusions.

- [x] **Step 3: Run round one and record provenance**

Require current authoritative metadata checks, 15–20 verified/deduplicated candidates or an explicit `evidence_incomplete` result, an eight-paper view when evidence permits, Mermaid plus text fallback, exact citation index, and basis labels.

- [x] **Step 4: Supply frozen feedback and run round two**

Require a visible feedback delta, a materially changed query plan, five-to-six recommendations, and dispositions for round-one papers.

- [x] **Step 5: Record pass, fail, or not run without repair-by-relabeling**

Initial failed forward attempts remain preserved in `evals/m1/results/2026-08-04-forward-audit.md` and Git. Accepted reruns and their machine artifacts are named and hash-bound in `evals/m1/results/2026-08-04-m1.2-final-validation.md`; Case B remains `evidence_incomplete`, and Case C validates only the blocking gate.

For every case, record timestamp, tools/sources used, round counts, blocked citations, unresolved conflicts, output basis levels, validator result, and deviations. A search or registry outage remains `not_run` or `evidence_incomplete`.

- [x] **Step 6: Commit forward-test evidence**

Run:

```powershell
git add evals/m1/forward-cases.md evals/m1/results STATUS.md
git commit -m "test: forward-evaluate M1 paper calibration"
```

Expected: prompts, immutable result records, and status evidence only.

### Task 8: Close M1 only after every gate is evidenced

**Files:**
- Modify: `STATUS.md`

**Interfaces:**
- Consumes: standard validator, offline unit tests, adversarial fixture results, and fresh-context real-search results.
- Produces: M1 `COMPLETE` or an honest `IN_PROGRESS`/`BLOCKED` status with later milestones untouched.

- [x] **Step 1: Run all local gates**

Run:

```powershell
python -X utf8 C:\Users\94310\.codex\skills\.system\skill-creator\scripts\quick_validate.py D:\engineering-research-copilot\skills\engineering-research-copilot
python -m unittest discover -s tests -p "test_validate_m1_bundle.py" -v
```

Expected: `Skill is valid!` and all M1 unit tests pass.

- [x] **Step 2: Check router links, line count, and placeholders**

Run a deterministic local check that every `references/*.md` link in `SKILL.md` exists, `SKILL.md` is below 500 lines, and no unresolved template marker remains inside the installable Skill.

Expected: zero missing references, root length below 500, zero placeholders.

- [x] **Step 3: Audit acceptance evidence**

Require evidence for:

- zero fabricated identifiers in real forward-test recommendations;
- zero blocked citation states in recommendations;
- `node_size_basis: user_fit` in every complete map;
- feedback reasons visibly changing the second-round query plan;
- five-to-six second-round papers or an honest incomplete result;
- no M2 route generation before user direction confirmation.

- [x] **Step 4: Update status without overstating completion**

Set M1 to `COMPLETE` only if every required offline and real forward-test gate passes. Otherwise leave M1 `IN_PROGRESS` and list the failed or not-run gate; keep M2–M5 `NOT_STARTED`.

- [x] **Step 5: Review exact final scope**

Run:

```powershell
git status --short
git log --oneline origin/main..HEAD
```

Expected: only planned M1 files and independent M1 commits appear; no RRC, deployment, corpus, or platform work is present.

## Self-Review Record

- Spec coverage: Tasks 2–4 cover adaptive intake, 15–20 candidates, eight-paper round one, visible feedback delta, five-to-six-paper round two, and text fallback. Tasks 5–7 cover offline and real evidence separately. Task 8 enforces all M1 acceptance criteria.
- Boundary check: Direction portfolios and route gates remain existing frozen contracts; this plan does not implement M2 ranking or route generation.
- Placeholder scan: The plan contains no incomplete implementation marker or omitted production-code step.
- Type consistency: `ResearchBrief`, `SearchPlan`, `RoundBundle`, `FeedbackDelta`, and validator status names are consistent across all tasks.
- Evidence integrity: Synthetic fixtures use `fixture:` identifiers and explicitly cannot establish live citation correctness; M1 completion requires separate real forward-test evidence.
