# M1 Final Validation Record

- Validation date: `2026-08-04` (`Asia/Shanghai`)
- Branch: `codex/m1-paper-calibration`
- Scope: M1 only
- Final classification: `pass`

## Standard Skill validation

Command:

```powershell
python -X utf8 C:\Users\94310\.codex\skills\.system\skill-creator\scripts\quick_validate.py D:\engineering-research-copilot\skills\engineering-research-copilot
```

Result: exit `0`; output `Skill is valid!`.

## M1 unit tests

The first Task 8 command used the planned selector:

```powershell
python -m unittest discover -s tests -p "test_m1_*.py" -v
```

Result: exit `5`; `Ran 0 tests`; `NO TESTS RAN`. The selector did not match the planned Task 5 filename `test_validate_m1_bundle.py`. This failed attempt is preserved and was not counted as validation.

The plan selector was corrected, then the actual target was run:

```powershell
python -m unittest discover -s tests -p "test_validate_m1_bundle.py" -v
```

Result: exit `0`; `Ran 38 tests`; `OK`.

Compilation check:

```powershell
python -m py_compile skills/engineering-research-copilot/scripts/validate_m1_bundle.py tests/test_validate_m1_bundle.py
```

Result: exit `0`.

## Adversarial fixture replay

Each frozen fixture was rerun through `validate_m1_bundle.py`:

| Fixture | Exit | Status | Match frozen record |
|---|---:|---|---|
| `valid-complete.json` | 0 | `valid` | yes |
| `blocked-conflict.json` | 1 | `invalid` | yes |
| `feedback-ignored.json` | 1 | `invalid` | yes |
| `map-citation-sized.json` | 1 | `invalid` | yes |
| `evidence-incomplete.json` | 2 | `evidence_incomplete` | yes |

These fixtures prove offline contract behavior only. They do not prove real DOI existence, publisher metadata accuracy, or live search coverage.

## Router and packaging checks

- Root `SKILL.md`: 106 lines; below the 500-line limit.
- Direct reference links: 5.
- Missing linked references: 0.
- Unlinked `references/*.md` files: 0.
- Unresolved `TODO`, `FIXME`, `TBD`, `PLACEHOLDER`, mustache, or insertion markers inside the installable Skill: 0.

## Real forward-test acceptance

### Case A — PWR small-break LOCA

- Clean rerun: `2026-08-04-pwr-sb-loca-rerun.md`.
- Current verified/deduplicated round-two candidates: 18.
- Default round-two recommendations: 6.
- Independent review: `PASS` after preserving two transient `unavailable` Crossref attempts in the affected source chains.
- Remaining gaps are explicit: no direct public PWR SB-LOCA OOD validation, transfer claims remain hypotheses, and the 24 GB / 12-week feasibility boundary was not experimentally tested.

### Case B — bearing fault diagnosis

- Accepted clean rerun: `2026-08-04-bearing-fault-rerun-2.md`.
- Current verified/deduplicated round-two candidates: 16.
- Recommendation-eligible records with sufficient basis: 3.
- Result: `evidence_incomplete` / `WAITING_FOR_EVIDENCE_DECISION`, correctly below the default five-paper minimum.
- Independent review: `PASS` after the complete ResearchBrief, SearchPlan, and Paper Map objects were embedded in the RoundBundle without changing evidence or status.

### Case C — citation audit

- Result and supplement: `2026-08-04-citation-audit.md` and `2026-08-04-citation-audit-supplement.md`.
- Result: `conflicted`; `recommendation_eligible: false`; stopped at the citation gate.
- Validator: `not_run` because no RoundBundle existed before the gate stop.
- Independent review confirmed the live Crossref and official NeurIPS records identify distinct works.

## Acceptance audit

- Fabricated identifiers in accepted real recommendations: 0 found by independent DOI/title/author spot checks and source review.
- Blocked or conflicted records in recommendations: 0.
- Complete maps with `node_size_basis: user_fit`: present in accepted A and B results.
- Feedback reasons materially changing second-round queries: present and cause-referenced in accepted A and B results.
- Round-two output: A has six papers; B stops honestly incomplete with three; C stops at the citation gate.
- Full experimental/simulation route generation: not run.
- RRC integration, model downloads, services, M2, M3, deployment, and platform integration: not run.

## Completion decision

M1 passes because the implemented Skill succeeds on a complete two-round case, stops honestly when verified evidence cannot support the default recommendation count, and blocks a live conflicted citation. Failed initial executions remain preserved in Git and in `2026-08-04-forward-audit.md`; they are not relabeled as successful runs.
