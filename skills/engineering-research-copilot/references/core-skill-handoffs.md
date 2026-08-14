# Research Skill Handoff Contract

Use this contract when one focused Skill passes work to another. Keep the handoff small enough to inspect and complete enough to prevent evidence or permission drift.

## Produce one handoff envelope

```yaml
handoff_version: "research-handoff.v1"
case_id: ""
brief_version: 1
from_skill: ""
to_skill: ""
requested_next_action: ""
source_artifacts:
  - artifact_id: ""
    path_or_source: ""
    content_hash: null
    inspection_status: "not_inspected|partially_inspected|inspected"
claim_ids: []
evidence_ids: []
constraints:
  inherited: []
  rejected: []
  reset: []
  added: []
evidence_gaps: []
readiness: "concept_sketch|route_preparation|executable_route"
permission_ledger: {}
permitted_next_actions: []
prohibited_next_actions: []
```

Use a raw SHA-256 content hash for a local artifact when byte identity matters and its bytes were actually read. Leave the hash null and state the gap when the artifact was not available. Do not invent a path, source, anchor, or hash.

## Preserve state without strengthening it

- Keep claim, evidence, direction, and artifact IDs stable across handoffs.
- Copy the evidence basis, identity status, content level, gaps, readiness, and permissions without upgrading them.
- Show inherited, rejected, reset, and newly added constraints before a new search branch or substantive reframe.
- Carry counterevidence and minority review findings with the supporting evidence.
- If the receiving Skill needs stronger evidence or broader permission, stop at the current readiness level and request that exact input or authorization.

## Keep handoff and action separate

A handoff authorizes the receiving Skill to reason over the supplied state only. It does not authorize file writes, downloads, uploads, experiments, simulations, training, publication, external communication, or a detailed route. Use the shared permission ledger and direction gate for those operations.

## Close the handoff visibly

Return:

- what was accepted unchanged;
- what was rejected or could not be verified;
- what new state was derived and at which evidence level;
- unresolved gaps and disagreements;
- the current readiness;
- the next permitted action and every blocked action relevant to the request.
