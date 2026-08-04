# Citation Integrity

Apply this file whenever external literature is discovered, recommended, cited, mapped, or used to justify a direction.

## Contents

- Separate discovery from verification
- Normalize without inventing
- Compare metadata
- Assign one verification state
- Apply the preprint contract
- Deduplicate records
- Produce a verified paper record
- Enforce hard gates

## Separate discovery from verification

Treat every search hit as an unverified candidate. Do not expose it as a recommended citation until it passes identifier and metadata checks.

Use this source order:

1. Query the DOI registration agency record for DOI works.
2. Query the official arXiv record and exact version for arXiv works.
3. Query the official PubMed record for PMID works in biomedical intersections.
4. Use the publisher landing page to cross-check title, authors, venue, work type, dates, corrections, and version relationships.
5. Use structured aggregators for discovery or ambiguity checks, never as the sole truth source when a primary registry exists.
6. Treat scraped search results and ordinary web pages as discovery-only.

If a source fails, report that source as not run or unavailable. Do not replace current verification with model memory.

## Normalize without inventing

- Strip `https://doi.org/`, `http://dx.doi.org/`, and `doi:` from DOI input.
- Trim whitespace and trailing citation punctuation; lowercase the DOI.
- Never change the DOI body or infer missing characters.
- Never treat an arXiv ID, PMID, ISBN, report number, or publisher URL as a DOI.
- Preserve online-first and issue publication dates separately when both exist.

## Compare metadata

Compare at minimum:

- complete title;
- ordered author list;
- online and issue dates;
- journal, conference, repository, or other venue;
- publication type;
- DOI, arXiv ID/version, PMID, or other canonical identifier;
- correction, retraction, and version relationships when available.

If a DOI resolves but its title or author identity materially conflicts with the candidate, classify it as `conflicted`; do not choose the version that appears plausible.

When no DOI exists, search by normalized title and first author only to locate candidates. Require a strong title match, matching first author, and a reasonable date before manual or second-source confirmation. Never assign a DOI solely from fuzzy matching.

## Assign one verification state

| State | Meaning | Recommendation eligibility |
|---|---|---|
| `verified_primary` | Registry or official repository and landing metadata agree | Eligible |
| `verified_registry` | Registry metadata agrees; publisher landing page cannot currently be checked | Eligible with limitation |
| `verified_preprint` | Official preprint ID, version, title, and authors agree | Conditional evidence only |
| `partial` | A record exists but important author, date, venue, or version data is incomplete | Supplemental only; never sole core support |
| `conflicted` | Identifier resolves to materially different metadata or authoritative sources disagree | Blocked |
| `not_found` | No authoritative record is found within the stated search boundary | Blocked |
| `manual_needed` | Multiple plausible candidates remain | Blocked pending human confirmation |

Do not display `conflicted`, `not_found`, or `manual_needed` records in a recommendation list.

## Apply the preprint contract

- Permit a `verified_preprint` as method evidence or exploration evidence.
- State its version and that peer review may not have occurred.
- Link a journal version with `is_version_of` only after verifying the relationship.
- Keep preprint and journal records separate when their content or relationship is unclear.
- Never use preprints as the sole support for a main direction or safety-related conclusion.

## Deduplicate records

1. Use normalized DOI as the primary key.
2. When DOI is absent, compare normalized title tokens and first-author surname.
3. Preserve distinct work types and substantive versions even when titles are similar.
4. Prefer the more complete authoritative record; do not merge conflicting fields silently.

## Produce a verified paper record

Include:

```yaml
paper_id: "doi:10.xxxx/example"
title: "Complete title"
authors: ["Ordered author names"]
year_online: 2025
year_issue: 2026
venue: "Journal or conference"
publication_type: "journal_article"
doi: "10.xxxx/example"
canonical_url: "https://doi.org/10.xxxx/example"
alternate_id: null
verification_status: "verified_primary"
verified_against: ["registry", "publisher"]
verified_at: "ISO-8601 timestamp"
evidence_role: "direct"
supports: "Scoped statement this paper supports"
does_not_support: "Nearby claim this paper does not establish"
basis_level: "abstract_level"
```

Show the exact title, authors, year, venue, clickable identifier, verification status, verification time, evidence role, support, and limitation to the user.

## Enforce hard gates

- Require zero invented DOI, author, title, or identifier fields.
- Do not claim novelty, priority, or absence of research without an explicit search boundary.
- Do not use citation count as a truth, quality, or applicability verdict.
- Downgrade a conclusion when the evidence is partial, preprint-only, abstract-only, or transfer-only.
