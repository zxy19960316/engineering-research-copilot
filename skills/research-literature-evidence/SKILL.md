---
name: research-literature-evidence
description: "Discover, deduplicate, verify, and inspect scholarly literature while separating candidate discovery, bibliographic identity, metadata, abstract, full-text, and user-material evidence. Use for 文献检索、查论文、引文核验、DOI核对、作者题名核对、相关工作 or evidence support for another research Skill. Do not use to draft prose, execute a method, or create placeholder citations."
---

# Research Literature Evidence

Find literature without allowing discovery records to masquerade as verified evidence. Apply [shared research governance](../engineering-research-copilot/references/core-research-governance.md), the [handoff contract](../engineering-research-copilot/references/core-skill-handoffs.md), [citation integrity](../engineering-research-copilot/references/core-citation-integrity.md), and [paper calibration](../engineering-research-copilot/references/core-paper-calibration.md).

In a generated host projection, read the linked copies inside this Skill. In the canonical source tree, the links resolve to the umbrella sibling. Do not reconstruct or weaken the shared rules.

## Separate four operations

1. Translate the research brief into concepts, synonyms, exclusions, source boundaries, dates, and evidence roles.
2. Discover candidate records from appropriate scholarly sources. Label them `discovered` and do not cite them as verified.
3. Verify identity through an authoritative registry, official repository, PubMed, or publisher landing record. Compare title, ordered authors, identifier, work type, venue, dates, and version relation.
4. Inspect content at metadata, abstract, or full-text level. Record the inspected source and a resolvable anchor.

Keep two internal modes isolated. `discovery_mode` may return candidate pointers and search limitations but no verified citation. `verification_mode` starts from named candidates and returns identity/content records but does not silently broaden the search. If activation tests show either mode repeatedly triggers for the other, or they require different provider permissions, split them into separate discovery and source-verification Skills while preserving the shared evidence schema.

Do not infer a DOI, author, title, journal status, preprint-publication relation, or alternate identifier. Keep conflicting or unresolved records separate and blocked.

## Search for decisions, not volume

Assign every query an evidence purpose: target-problem existence, method evidence, transfer bridge, counterevidence, limitation, benchmark/data, or safety/standards. State the database/site, query, date, filters, and known coverage limits. Treat citation counts and popularity only as discovery or influence signals, never truth or applicability verdicts.

Prefer primary method papers, official standards or registries, and direct target-domain evidence. Use reviews to map the field and trace claims to primary sources. Permit verified preprints for method or exploration evidence but never as sole support for a main direction or safety conclusion.

## Return a verification ledger

For every retained record show:

- stable candidate ID and exact checked metadata;
- canonical identifier and URL, or an explicit absence/unresolved state;
- identity status, checked source, and verification time;
- content level and inspection anchor;
- what the source supports, contradicts, limits, and does not establish;
- recommendation eligibility and blocking reasons.

Deduplicate with decisive identifiers first. Treat normalized title plus first author only as a manual-review trigger. Preserve separate preprint and journal records until an authoritative relation is established.

## Stop honestly

Return `evidence_incomplete` when authoritative identity or required content cannot be checked. A search snippet, abstract aggregator, local schema fixture, or remembered citation cannot close the gap. Do not pad a portfolio with weak or conflicted records.

## Hand off

Pass verified records, discovery limitations, blocked candidates, counterevidence, content anchors, and current evidence level. Pass no drafting, route, plotting, or execution permission.
