# Shared Research Governance Contract

Apply this contract to every workflow in the Engineering Research Workbench plugin. Keep the user in control of material changes and keep every claim proportional to inspected evidence.

## Accept any honest entry point

Start from a vague idea, literature list, plan, result, outline, draft, reviewer comment, figure, table, or existing evidence package. Do not force the user to repeat earlier phases.

Create the smallest usable research-case envelope:

```yaml
case_id: ""
brief_version: 1
entry_type: "idea|literature|plan|result|outline|draft|review|figure|data|mixed"
research_problem: ""
intended_decision_or_output: ""
confirmed_constraints: []
soft_preferences: []
user_materials: []
open_questions: []
```

Ask only for missing information that can materially change the immediate output. Preserve uncertainty instead of filling a field by inference.

## Keep evidence dimensions separate

Represent each external or user-supplied evidence item with these independent dimensions:

```yaml
evidence_id: "E1"
source_class: "external_literature|user_material|tool_observation|authorized_execution_result"
identity_status: "discovered|identity_verified|conflicted|unresolved|not_applicable"
content_level: "none|metadata_level|abstract_level|fulltext_level|user_provided_content"
inspection_anchor: ""
claim_relation: "supports|contradicts|limits|motivates|does_not_establish"
supports: ""
does_not_support: ""
checked_at: null
gaps: []
```

- Treat discovery as a locator only. Never copy discovery metadata into a verified citation without an authoritative identity check.
- Treat identity verification and content inspection as different operations. A verified title, author list, DOI, or official identifier does not establish a substantive claim.
- Use `metadata_level` only for bibliographic or keyword-level reasoning, `abstract_level` only after inspecting a verified abstract, and `fulltext_level` only with a resolvable section, page, figure, table, or paragraph anchor.
- Label user materials `user_provided_content`. Analyze them as supplied, but do not call them externally verified or independently reproduced.
- Use `authorized_execution_result` only when the exact execution was separately authorized and an actual observation was captured. A plan, command, synthetic fixture, or expected result is not an execution result.
- Block `conflicted` and `unresolved` external identities from citations, recommendations, and safety conclusions.

Never invent or complete a citation, author, title, identifier, data value, sample size, experimental condition, analysis output, result, uncertainty, or conclusion. Mark the missing element as a gap.

## Build claims before prose or decisions

Use one claim-evidence ledger before drafting, recommending, or synthesizing:

```yaml
claim_id: "C1"
claim: ""
claim_type: "observation|comparison|mechanism|causal|transfer|limitation|recommendation"
status: "supported|contested|unsupported|hypothesis|not_tested"
supporting_evidence_ids: []
counter_evidence_ids: []
assumptions: []
scope: ""
falsifier: ""
allowed_language: ""
```

Require at least one inspected evidence item for `supported`. Keep a claim `contested` when admissible evidence conflicts. Use `hypothesis` or `not_tested` for transfer reasoning and planned tests until target-domain results exist. Do not turn the absence of found evidence into evidence of absence without an explicit, adequate search boundary.

## Return the real readiness level

Use exactly one readiness state:

- `concept_sketch`: return the problem framing, candidate claims or directions, evidence gaps, risks, and the next smallest information-gathering step. Do not create a detailed route.
- `route_preparation`: return a provisional direction portfolio, preconditions, decision metrics, and bounded minimum falsification tests. Do not create a detailed route until a formal direction is explicitly confirmed.
- `executable_route`: permit a detailed route only after the user explicitly confirms one formal direction and the evidence/data/resource preconditions are adequate.

Route generation is not execution authorization. A written route, executable-looking command, `READY`, or `user_confirmed` direction does not authorize an experiment, simulation, training run, download, upload, or other side effect.

## Maintain an operation-specific permission ledger

Default audits, inspections, comparisons, and reviews to read-only. Record permissions independently:

```yaml
permission_ledger:
  source_file_write: "not_authorized"
  artifact_file_write: "not_authorized"
  download: "not_authorized"
  upload: "not_authorized"
  experiment: "not_authorized"
  simulation: "not_authorized"
  training: "not_authorized"
  publication: "not_authorized"
  external_communication: "not_authorized"
authorization_provenance: []
```

Treat an authorization as scoped to its stated operation, target, and current request. File-write authority does not grant download or upload authority. Simulation authority does not grant training authority. Publication authority does not grant external correspondence authority. When scope is absent or ambiguous, keep the operation `not_authorized`.

## Preserve reviewer independence and author control

Freeze each reviewer or audit pass before cross-review synthesis. Do not delete minority findings merely because another pass disagrees. First show agreements, disagreements, evidence dependencies, and unresolved questions; then synthesize issue priority.

Distinguish independent agents from separated passes by one agent. Never label separated passes as independent agents. Treat every proposed substantive change to claims, methods, analyses, results, or conclusions as awaiting the author's decision. Do not modify a manuscript or data file during read-only review.

## Report limitations visibly

State the search boundary, evidence basis, inaccessible material, unresolved identity, analysis not run, and operations not authorized. A valid schema or synthetic fixture proves only the contract it checks; it never proves that a real citation, experiment, plot, or conclusion is correct.
