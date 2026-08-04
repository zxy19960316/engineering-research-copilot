# M1 Fresh-Context Citation Audit — Case C

## Run metadata

- `skill_revision`: `2291357`
- `workflow`: `citation-verification`
- `mode`: read-only citation audit
- `started_at_beijing`: `2026-08-04T18:17:16+08:00` (first recorded authoritative lookup)
- `ended_at_beijing`: `2026-08-04T18:19:16+08:00`
- `timezone`: `Asia/Shanghai` (`UTC+08:00`)
- `final_classification`: `pass`
- `citation_verification_status`: `conflicted`
- `recommendation_eligible`: `false`
- `gate`: `citation_gate_stopped`
- `reasoning_basis`: `metadata_level`

`pass` classifies the forward-test execution: the live conflict was detected, preserved, and blocked at the citation gate. It does not mean that the user-supplied citation was verified.

## Complete case input

> 请做一次只读的引用审计。我准备把题名为 `Attention Is All You Need`、DOI 为 `10.1038/nature14539` 的论文作为核心方法论文。请使用当前权威来源核验题名、DOI、作者与出版记录是否相互一致，并说明它是否具备推荐资格。不要根据记忆补全或修复标识符；若记录无法核实，请保留未解决状态。

## Scope and controls

- Treated the title and DOI as user-supplied, unverified observations.
- Performed current, read-only authoritative lookups only.
- Did not alter user literature or repository source material.
- Did not search for, infer, repair, or substitute a DOI for the supplied title.
- Did not enter a candidate pool, paper graph, experiment route, RRC, M2, or M3.
- Stopped at the citation gate after establishing a decisive identity conflict; no two-round calibration was attempted.

## Discovery record

```yaml
discovery_candidate:
  candidate_id: "citation-audit-c"
  discovery_state: "unverified_candidate"
  supplied_title: "Attention Is All You Need"
  supplied_authors: []
  supplied_identifier:
    type: "doi"
    value: "10.1038/nature14539"
  discovery_source_type: "user_supplied"
  discovery_source: "complete case input above"
```

## Authoritative observations

### A. Supplied DOI registration record

Current Crossref REST lookup of [`10.1038/nature14539`](https://api.crossref.org/works/10.1038/nature14539) returned:

- DOI: `10.1038/nature14539`
- Title: `Deep learning`
- Ordered authors: Yann LeCun; Yoshua Bengio; Geoffrey Hinton
- Venue: `Nature`
- Work type: `journal-article`
- Online publication: `2015-05-27`
- Print/issue publication: `2015-05-28`
- Volume/issue/pages: `521` / `7553` / `436–444`
- Publisher metadata: `Springer Science and Business Media LLC`
- Canonical DOI URL: `https://doi.org/10.1038/nature14539`
- Checked at: `2026-08-04T18:17:16+08:00`

The normalized supplied DOI exactly matches the DOI returned by the registration record, but that registered work's title is not the supplied title.

### B. Publisher landing-page attempt for the supplied DOI

A direct current request to the canonical Nature landing page, [`https://www.nature.com/articles/nature14539`](https://www.nature.com/articles/nature14539), was blocked by the publisher edge service with `Access Blocked`.

- Source result: `unavailable`
- Checked-at record: `2026-08-04T18:18:06+08:00`
- Limitation: no direct landing-page response was promoted to verified evidence.
- A web-indexed snippet pointing to the same official Nature URL displayed `Deep learning`, Yann LeCun, Yoshua Bengio, Geoffrey Hinton, Nature 521, 436–444 (2015), and the same DOI. It was retained only as a discovery clue because the direct publisher request was unavailable.

### C. Official conference record for the supplied title

The current official NeurIPS proceedings page for [`Attention is All you Need`](https://proceedings.neurips.cc/paper_files/paper/2017/hash/3f5ee243547dee91fbd053c1c4a845aa-Abstract.html), together with its official [metadata record](https://proceedings.neurips.cc/paper_files/paper/2017/file/3f5ee243547dee91fbd053c1c4a845aa-Metadata.json), returned:

- Title: `Attention is All you Need`
- Ordered authors: Ashish Vaswani; Noam Shazeer; Niki Parmar; Jakob Uszkoreit; Llion Jones; Aidan N Gomez; Łukasz Kaiser; Illia Polosukhin
- Venue: `Advances in Neural Information Processing Systems 30 (NIPS 2017)`
- Publication type: conference paper/proceedings record
- Pages: `5998–6008`
- Checked at: `2026-08-04T18:18:39+08:00`

No alternate DOI was sought or assigned.

## Field-by-field comparison

| Field | Supplied observation | Current authoritative observation(s) | Result | Reason |
|---|---|---|---|---|
| DOI | `10.1038/nature14539` | Crossref returns exactly `10.1038/nature14539` | `match` | The supplied DOI exists and normalizes without changing its body. |
| Title | `Attention Is All You Need` | The DOI registry title is `Deep learning`; the official NeurIPS title record is `Attention is All you Need` | `conflict` | The supplied title and supplied DOI identify different works. Case differences do not affect the decisive title mismatch with the DOI record. |
| Authors | No author list supplied | DOI record: LeCun, Bengio, Hinton; official title record: Vaswani, Shazeer, Parmar, Uszkoreit, Jones, Gomez, Kaiser, Polosukhin | `conflict` | The authoritative author identities attached to the DOI and title are materially different. No comparison to a user-supplied author list was possible. |
| Publication record | Not supplied beyond title/DOI | DOI record: Nature journal article, 2015; title record: NIPS 2017 conference paper, pages 5998–6008 | `conflict` | Venue, work type, date, and pagination do not describe the same publication. |
| Replacement/corrected identifier for supplied title | Not supplied | Deliberately not queried or inferred | `not_checked` | The audit must not repair or substitute identifiers after the decisive conflict. |

Counts over the four requested identity fields (DOI, title, authors, publication record): `match=1`, `conflict=3`, `not_found=0`, `not_checked=0`.

## Verification object

```yaml
verification:
  status: "conflicted"
  checked_sources:
    - source_type: "doi_registry"
      canonical_record: "https://api.crossref.org/works/10.1038/nature14539"
      checked_at: "2026-08-04T18:17:16+08:00"
      result: "conflict"
    - source_type: "publisher_landing"
      canonical_record: "https://www.nature.com/articles/nature14539"
      checked_at: "2026-08-04T18:18:06+08:00"
      result: "unavailable"
    - source_type: "official_repository"
      canonical_record: "https://proceedings.neurips.cc/paper_files/paper/2017/hash/3f5ee243547dee91fbd053c1c4a845aa-Abstract.html"
      checked_at: "2026-08-04T18:18:39+08:00"
      result: "conflict"
  title_match: "conflict"
  author_match: "conflict"
  version_relation: "distinct"
  recommendation_eligible: false
  blocking_reasons:
    - "The supplied DOI resolves to Deep learning, not Attention Is All You Need."
    - "The DOI-linked and title-linked authoritative records have different author lists, venues, work types, publication years, and pagination."
```

## DOI-linked verified metadata record

This record preserves what the supplied DOI actually identifies; it is not a repaired record for the supplied title.

```yaml
verified_paper_record:
  paper_id: "doi:10.1038/nature14539"
  title: "Deep learning"
  authors:
    - "Yann LeCun"
    - "Yoshua Bengio"
    - "Geoffrey Hinton"
  year_online: 2015
  year_issue: 2015
  venue: "Nature"
  publication_type: "journal-article"
  doi: "10.1038/nature14539"
  canonical_url: "https://doi.org/10.1038/nature14539"
  alternate_id: null
  verification:
    status: "conflicted"
    title_match: "conflict"
    author_match: "conflict"
    version_relation: "distinct"
    recommendation_eligible: false
    blocking_reasons:
      - "The user supplied a title belonging to a distinct official conference record."
  evidence_role: "excluded_core_method_candidate"
  supports: "The supplied DOI is registered to a 2015 Nature review article titled Deep learning."
  does_not_support: "The assertion that this DOI identifies Attention Is All You Need."
  basis_level: "metadata_level"
```

## Execution output

```text
verification_status: conflicted
recommendation_eligible: false
citation_gate: stopped
blocking_reason: supplied title and supplied DOI resolve to distinct authoritative publication records
identifier_repair_or_substitution: not_performed
second_round_or_downstream_work: not_run
reasoning_basis: metadata_level
```

The candidate is not recommendation-eligible as presented and must be excluded from the core-method recommendation set unless the user separately supplies or confirms a corrected citation for a new audit.

## Tools and source log

| Step | Tool/channel | Source | Outcome |
|---|---|---|---|
| Rule loading | Local read-only file inspection | Repository `AGENTS.md`, Engineering Research Copilot `SKILL.md`, `core-citation-integrity.md` | Completed |
| Workflow loading | Local read-only file inspection | nature-academic-search v2.0.0 router, manifest, core routing/tools, citation-verification workflow, source tiers, citation parser, dedup engine | Completed |
| DOI lookup | PowerShell `Invoke-RestMethod` (read-only HTTP GET) | Crossref REST API | Current structured record returned successfully |
| Publisher cross-check | PowerShell `Invoke-WebRequest` (read-only HTTP GET) | Nature canonical landing page | `unavailable`; publisher returned `Access Blocked` |
| Publisher clue | Web search constrained to the official Nature URL | Nature landing-page index result | Corroborating clue only; not promoted to direct authoritative verification |
| Title-record check | Web open of official proceedings page and JSON metadata | NeurIPS proceedings | Current official record returned successfully |

## Final decision

- Citation verification status: `conflicted`
- Recommendation eligibility: `false`
- Blocking reason: the supplied title and DOI belong to distinct authoritative works, with conflicting authorship and publication records.
- Gate action: stop at the citation gate; preserve the supplied values; do not repair, substitute, rank, recommend, map, or continue downstream.
- Forward-test classification: `pass`
