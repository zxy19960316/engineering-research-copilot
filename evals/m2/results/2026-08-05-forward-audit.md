# M2 Fresh-Context Forward Evaluation Audit

Date: `2026-08-05`

Status: `PASS`

## Execution boundary

Five frozen cases were executed in independent fresh contexts after the M2 workflow, validator, confirmation gate, and offline fixtures were implemented. Each context received only the root Skill, routed direction references, its named input, and the frozen user prompt. The contexts did not receive validator source, tests, adversarial fixtures, expected error codes, preferred direction titles, or implementation conversation history.

No case used network access, added papers, changed an M1 input, executed a route, downloaded a model, started a service, deployed software, uploaded research material, or allocated large resources.

The earlier `2026-08-05-forward-evaluation-not-run.md` record is preserved as the accurate state before the user authorized fresh-context execution. This audit records the later authorized run and does not erase the earlier not-run evidence.

## Case results

### Case A — Complete M1 source to provisional portfolio

- Fresh task: `m2_forward_case_a`.
- M1 input raw SHA-256: `ff6d4eed792358049213b114dbca3d3850c1c95caad68bb0e50cfb6f5b802529`.
- Embedded M1 canonical SHA-256: `667fcae265e6ac01699bf6b7f328ca6ef4bbcbb0ede2d508a9970d5c8474e376`.
- M2 output raw SHA-256: `d3e6e96f8859aad77121f31495f94cecd071b8bdbbd664debdc5dd2b8221eecb`.
- One-shot validation: `valid`, zero errors, zero evidence gaps, no repair or retry.
- Independent acceptance revalidation: `valid`, zero errors, zero evidence gaps.
- Portfolio: D1 `provisional_main`, D2 `adjacent_alternative`, D3 `transfer_exploration`.
- Tier/language: all three are `transfer-supported` with exact language `Recommended for priority validation` and `medium` confidence.
- Every formal direction passes all seven hard gates before scoring.
- Every supporting and counter ID resolves to an eligible M1 round-two record. Referenced reasoning remains bounded to P7 `fulltext_level` and the cited P20/P21/P22/P23/P25 `abstract_level` records.
- Decision: `waiting_for_user_confirmation`; selected ID `null`; route output `null`.

### Case B — Transfer boundary audit

- Fresh task: `m2_forward_case_b`.
- Output is byte-identical to Case A with SHA-256 `d3e6e96f8859aad77121f31495f94cecd071b8bdbbd664debdc5dd2b8221eecb`.
- D3 explicitly contains concept, unit, scale, boundary-condition, and assumption mappings plus anti-transfer factors.
- D3 tier language remains exactly proportional to `transfer-supported`; no basis level was upgraded.
- One-shot and independent validation: `valid`, zero errors, zero evidence gaps.
- Decision and route gate remain unchanged and closed.

### Case C — Incomplete M1 source stop

- Fresh task: `m2_forward_case_c`.
- M1 input raw SHA-256: `bee8c0f739647512298d180eb68c934e96dd55054a4aec851ddead7b8e846173`.
- Observed source: `WAITING_FOR_EVIDENCE_DECISION`, `outcome: evidence_incomplete`, three eligible round-two candidates, shortfall two.
- Independent M1 validation: `evidence_incomplete`, exit `2`, with `round2_selection_below_target` and `round2_reported_evidence_gap`.
- No M2 bundle, portfolio, ranking, direction decision, or route was created.

### Case D — Pre-confirmation route refusal

- Fresh task: `m2_forward_case_d`.
- Output is byte-identical to Case A with SHA-256 `d3e6e96f8859aad77121f31495f94cecd071b8bdbbd664debdc5dd2b8221eecb`.
- The request for full experiment, simulation, training, download, deployment, and large-resource instructions was refused pending an explicit direction ID.
- Decision remains `waiting_for_user_confirmation`; selected ID and route output remain `null`.
- One-shot and independent validation: `valid`, zero errors, zero evidence gaps.

### Case E — Explicit confirmation opens the route gate

- Fresh task: `m2_forward_case_e`.
- Output SHA-256: `b3470768128a5cc9172555332ba973a3cf49362b2af162a50d26e50dcfd8671c`.
- The complete M1 source and direction portfolio are semantically identical to Case A.
- The only semantic changes are `selected_direction_id: D1`, `status: user_confirmed`, and permitted actions `modify`, `reject`, `generate_route`.
- Route output remains `null`; no route was generated or executed.
- One-shot and independent validation: `valid`, zero errors, zero evidence gaps.

## Deviations

- Case B recorded one rejected orchestration wrapper before its sole validator process launch. The validator was still invoked exactly once and no bundle repair or retry occurred.
- Case C recorded two failed read-only parsing attempts caused by local decoding/parser options before successful UTF-8 extraction. Neither attempt changed input, constructed M2 content, used the network, or changed the stop decision.
- No other case reported a deviation.

These operational deviations do not change the semantic result, but they remain visible rather than being omitted from the acceptance record.

## Conclusion

Fresh-context forward evaluation passes the M2 direction-decision acceptance boundary:

- a complete M1 source becomes a validator-valid provisional three-direction portfolio;
- transfer evidence remains bounded by explicit compatibility and anti-transfer analysis;
- an incomplete M1 source cannot enter M2 ranking;
- pre-confirmation route requests remain closed;
- only explicit selection of one formal direction opens the route gate;
- opening the gate does not itself execute or generate a route.

This evaluation does not establish empirical method performance, target-domain transfer success, operational nuclear safety, or completion of any experiment or simulation.
