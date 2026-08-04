# Citation Integrity

Apply this file whenever external literature is discovered, recommended, cited, mapped, or used to justify a direction.

## Contents

- Separate discovery candidates from verified records
- Verify against current authoritative sources
- Normalize without inventing
- Compare metadata
- Assign one verification state
- Determine recommendation eligibility
- Apply the preprint contract
- Deduplicate deterministically
- Resolve version relationships
- Produce a verified paper record
- State the real-evidence limitation
- Enforce hard gates

## Separate discovery candidates from verified records

Create a discovery record first. Keep its state exactly `unverified_candidate` until an authoritative source has been checked.

Use this shape for discovery output:

```yaml
discovery_candidate:
  candidate_id: ""
  discovery_state: "unverified_candidate"
  supplied_title: ""
  supplied_authors: []
  supplied_identifier: null
  discovery_source_type: "search_snippet|aggregator|ordinary_web|user_supplied|model_memory"
  discovery_source: ""
```

Preserve supplied strings as unverified observations. Do not repair an identifier, complete an author list, or convert a probable title into a bibliographic fact.

Do not let a search snippet, aggregator match, ordinary web page, user assertion, or model memory set a verified state. Do not place a discovery record directly in a recommendation list or paper map. Promote it to a `VerifiedPaperRecord` only after completing the verification object below.

## Verify against current authoritative sources

Check sources in this order when they apply:

1. Query the DOI registration agency record for a supplied DOI.
2. Query the official repository record and exact version for a supplied repository identifier.
3. Query the official PubMed record for a supplied PMID in biomedical intersections.
4. Cross-check the publisher landing page for title, authors, venue, work type, dates, corrections, and version relationships.
5. Use a structured aggregator only to discover a candidate or resolve ambiguity; never use it as the sole truth source when an authoritative registry or official repository exists.

Perform the authoritative lookup during the current calibration run for every real recommendation. Record every attempted authoritative source, including conflicts, unavailable responses, and not-found results. If a source cannot be checked, record that limitation instead of substituting model memory or an old search snippet.

## Normalize without inventing

- Strip `https://doi.org/`, `http://dx.doi.org/`, and `doi:` from supplied DOI input.
- Trim whitespace and trailing citation punctuation; lowercase the DOI.
- Preserve the supplied DOI body exactly after those normalization steps.
- Never change the DOI body, infer missing characters, or create an identifier from title similarity.
- Never treat an arXiv ID, PMID, ISBN, report number, or publisher URL as a DOI.
- Normalize an official alternate identifier only according to its owning authority; preserve its identifier type and version.
- Set `alternate_id` to `null` when no official alternate identifier is present. Otherwise require an object with exactly two fields: `authority`, containing the nonempty official authority type, and `value`, containing the nonempty authority-normalized identifier value. Reject a bare string, an empty value, a missing field, or any additional field.
- Preserve online-first and issue publication dates separately when both exist.

## Compare metadata

Compare at minimum:

- complete title;
- ordered author list;
- online and issue dates;
- journal, conference, repository, or other venue;
- publication type or work type;
- supplied and authoritative normalized DOI values, official alternate identifiers, and canonical identifiers;
- correction, retraction, and version relationships when available.

Classify a resolving identifier with materially inconsistent DOI, title, or author identity as `conflicted`. Treat two supplied or authoritative records with different normalized DOI values as a decisive identifier conflict when they are presented as the same candidate. Do not choose whichever DOI or version appears plausible, and do not use a weaker key to override that conflict.

Use normalized title plus first author only to find or review candidates when no stronger matching key is available. Require authoritative confirmation before treating that pair as the same work. Never assign a DOI or alternate identifier solely from fuzzy matching.

## Assign one verification state

Assign exactly one state from this closed set:

| State | Meaning | Recommendation eligibility |
|---|---|---|
| `verified_primary` | Registry or official repository and landing metadata agree | Eligible when no blocking reason remains |
| `verified_registry` | Registry metadata agrees; publisher landing page cannot currently be checked | Eligible with the unavailable cross-check disclosed |
| `verified_preprint` | Official preprint ID, exact version, title, and authors agree | Conditionally eligible under the preprint contract |
| `partial` | A record exists but important author, date, venue, or version data is incomplete | Supplemental context only |
| `conflicted` | An identifier resolves to materially different metadata or authoritative sources disagree | Blocked |
| `not_found` | No authoritative record is found within the stated search boundary | Blocked |
| `manual_needed` | Multiple plausible candidates or unresolved identity or version questions remain | Blocked pending human confirmation |

Do not introduce another verification-state label in a real record. Preserve unavailable checks inside `checked_sources` and limitations; do not relabel incomplete verification as success.

## Determine recommendation eligibility

Set `recommendation_eligible: true` only when all of these conditions hold:

- Set `verification.status` to `verified_primary` or `verified_registry`, or to `verified_preprint` under the preprint contract.
- Resolve title and author checks without `conflict`.
- Resolve work type and version identity sufficiently for the intended recommendation.
- Leave `blocking_reasons` empty.
- Complete a current authoritative lookup rather than relying on offline structure, discovery metadata, or model memory.

Set `recommendation_eligible: false` for `partial`. Use a partial record only as clearly labeled supplemental context outside the selected recommendation set, and state the missing verification.

Set `recommendation_eligible: false` for `conflicted`, `not_found`, and `manual_needed`. Exclude all three states from recommendation lists, selected IDs, paper-map nodes, direction support, and safety conclusions.

## Apply the preprint contract

- Permit a `verified_preprint` only as method or exploration evidence.
- State the exact checked version and disclose that peer review may not have occurred.
- Set it eligible only when it is not the sole support for a main direction or safety-related conclusion.
- Link a journal version with `preprint_of` only after authoritative evidence establishes that relationship.
- Keep preprint and journal records separate when their content or relationship is unclear.
- Prefer a verified journal record for the same claim when it is available and applicable.

## Deduplicate deterministically

Apply these keys in order and do not fall back after a stronger key produces a match or mismatch:

1. When both records contain a DOI, compare their normalized DOI values. Treat equal values as a possible duplicate subject to metadata and version checks. Treat different values as a decisive mismatch: stop, retain separate observations, and do not compare official alternate identifiers or title plus first author to merge them.
2. Only when at least one record lacks a DOI, compare exact official alternate identifiers as `(authority, value)` pairs. Validate each non-null `alternate_id` as the closed two-field object before comparison; reject bare strings and incomplete objects instead of coercing them. When both records contain an official alternate identifier, treat equal pairs as a possible duplicate subject to metadata and version checks; treat different pairs, including different `authority` values, as a decisive mismatch and stop without using title plus first author to merge them.
3. Only when at least one record lacks a DOI and at least one record also lacks an official alternate identifier, compare normalized title plus normalized first author for candidate review.

Treat the third key as a review trigger, not as proof of identity. Do not auto-merge title-and-author matches without current authoritative confirmation of `same_work`. When a stronger identifier is later found, restart comparison at the DOI step.

When duplicate DOI or official alternate identifiers carry conflicting title, author, work-type, or version metadata, do not merge them. Set the record to `conflicted` or `manual_needed` as appropriate, retain both source observations, and block recommendation eligibility until the conflict is resolved.

Retain the more complete authoritative metadata only after all decisive identity fields agree. Preserve all checked-source provenance and identifier aliases when consolidating true duplicates; never merge conflicting fields silently.

## Resolve version relationships

Assign exactly one `version_relation` from `same_work`, `preprint_of`, `distinct`, or `unknown`.

- For an ordinary single paper, set `same_work` when the discovery candidate and current authoritative record agree and no separate preprint, edition, correction, or other version relationship is asserted. Do not use `unknown` merely because the paper has only one identified version.
- For `same_work`, consolidate duplicate observations only after authoritative metadata and work type agree.
- For `preprint_of`, retain separate preprint and published records and link them without treating the identifiers as interchangeable.
- For `distinct`, retain separate records even when titles are similar.
- For `unknown`, require a genuine unresolved identity or version ambiguity. Do not merge the ambiguous record, and use `manual_needed` only when that ambiguity affects identity or recommendation eligibility.
- When work type conflicts or the preprint-to-publication relation is unresolved, keep the records separate and blocked until an authoritative source or human confirmation resolves the relation.

## Produce a verified paper record

Require this verification object and all of its fields:

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

Use only `doi_registry`, `official_repository`, `pubmed`, and `publisher_landing` for `source_type`. Use only `match`, `conflict`, `not_found`, and `unavailable` for `result`. Record a timezone-aware ISO-8601 `checked_at` value and a source-resolvable `canonical_record` for every check. Do not fabricate either value when a check did not occur.

Use this enclosing `VerifiedPaperRecord` shape. Leave absent identifiers null; populate every bibliographic value only from checked metadata:

```yaml
verified_paper_record:
  paper_id: ""
  title: ""
  authors: []
  year_online: null
  year_issue: null
  venue: ""
  publication_type: ""
  doi: null
  canonical_url: ""
  alternate_id: null
  verification: {}
  evidence_role: ""
  supports: ""
  does_not_support: ""
  basis_level: "metadata_level|abstract_level|fulltext_level"
```

Keep `alternate_id` exactly `null` when absent. When present, replace `null` with an object containing only the required nonempty `authority` and `value` fields defined above. Do not serialize it as a bare identifier string or accept a partially populated object.

Mirror `verification.status` and `verification.recommendation_eligible` into a calibration candidate's summary fields without changing their values. Reject a candidate when the summary and nested verification object disagree.

Show the exact checked title, authors, year, venue, clickable canonical record, verification status, verification time, evidence role, support, limitation, and reasoning basis to the user.

## State the real-evidence limitation

Treat offline schema, fixture, and structural validation as contract checks only. They can verify required fields, closed states, deduplication behavior, and eligibility gates, but they cannot prove that a DOI or other citation identifier exists, that metadata is accurate, or that live scholarly verification succeeded.

Require a current authoritative lookup and recorded provenance for every real recommendation. If the lookup cannot be completed, keep the record partial or blocked and report `evidence_incomplete`; never promote an offline-valid object to a real verified citation.

## Enforce hard gates

- Require zero invented DOI, author, title, publication state, URL, or identifier fields.
- Block recommendations whose verification provenance is absent, stale for the current run, internally inconsistent, or based only on discovery sources.
- Do not claim novelty, priority, or absence of research without an explicit search boundary.
- Do not use citation count as a truth, quality, or applicability verdict.
- Label metadata-, abstract-, and full-text-level reasoning explicitly.
- Downgrade a conclusion when the evidence is partial, preprint-only, abstract-only, or transfer-only.
