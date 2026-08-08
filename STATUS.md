# Project Status

## Active milestone

`M4 — Cross-engineering forward evaluation`

Active revision: `M4.1 PREPARATION_ONLY`

Historical r5 evidence HEAD: `1b696bce53ee0a11163bfe4f91a9a49ab3af6f49`

Gate 3 accepted evidence baseline HEAD: `ea8a7bbb8b365aded89f9ddb5c784f6e95a51d3d`

Gate 3 accepted evidence baseline exact-HEAD CI: `PASSED` (GitHub Actions run `31192712555`)

Status: `M3_CLOSED; M4_0_PRE_DISPATCH_FAILED_PRESERVED; M4_1_PREPARATION_ONLY; M4_FRESH_RESULTS_NOT_RUN`

Historical r5 status: `BLOCKED_NOT_ACCEPTED`

Historical accepted fresh cases: `F01, F03, F04, F05`

Historical failed fresh case: `F02`

r5.2-f02 replacement: `F02 ACCEPTED; SELECTED_FOR_AGGREGATE`

Selected aggregate revisions: `F01=r5; F02=r5.2-f02; F03=r5; F04=r5; F05=r5`

Selected aggregate counters: `tasks=5; finalizations=5; composer=4; validator=5; accepted=5; failed=0; retry=0`

Preserved historical-attempt counters: `tasks=7; finalizations=7; composer=6; validator=5; accepted=5; failed=2; retry=0`

Excluded immutable F02 attempts: `r5 processing_failed; r5.1-f02 terminal_not_accepted`

Aggregate candidate exact-HEAD CI: `PASSED` on HEAD `3be04218b038bac7a55da10a553a5ce05be4652c` (GitHub Actions run `31233356741`)

Historical immutable-r5 exact-HEAD CI: `FAILED` (GitHub Actions run `31096079186`)

M3: `CLOSED`

M4: `M4_1_PREPARATION_ONLY`

M4 fresh tasks authorized: `false; M4.0 authorization consumed and terminal; M4.1 authorization not issued`

M4 preparation protocol: `COMPLETE; OFFLINE_ONLY`

M4 preparation manifest: `evals/m4/preparation-manifest.json`

M4 preparation matrix: `12 cases; 5 arms; 60 planned tasks; 6 domain batches`

M4 preparation counters: `authorized=0; contexts=0; dispatched=0; finalizations=0; results=0; judge_scores=0; retries=0; repairs=0; unauthorized_side_effects=0`

M4 result state: `NOT_RUN`

M4 preparation local gates: `PASSED; focused=27/27; full=606/606; preparation_audit=PASSED; results_audit=NOT_RUN`

M4 Gate IV independent review: `PASSED; findings=0`

M4 Gate IV preparation baseline: `c56c3c1ab384f65e51a70e9582672c6320d19121` (GitHub Actions run `31237480839`; `success`)

M4 Gate IV authorization artifact: `evals/m4/authorization/execution-authorization.json`

M4 Gate IV execution control: `evals/m4/authorization/execution-control.json`

M4 Gate IV model binding: `gpt-5.6-sol; reasoning_effort=max; configured defaults must match`

M4 Gate IV authorized roster: `60 task IDs; 60 fresh contexts maximum; 60 independent finalizations maximum; 6 domain batches; 1 attempt/task`

M4 Gate IV authorization token: `sha256:09c940955104f2ae9278b55d155bc43a47d43a0eb9e80e4f90d7425eb3c0e292`

M4 Gate IV authorization token status: `CONSUMED; claim_count=1; terminal for M4.0`

M4 Gate IV launch claim: `PRESENT; claim_id=507b5fef-c05f-4ede-ad06-b6694203cfe1; sha256=5690177383c44a30e808533ebdfe0b504c6da2abf8e61a1d0303d4c439c3ecec`

M4 Gate IV observed counters: `create_thread_calls=0; contexts=0; dispatched=0; finalizations=0; results=0; retries=0; repairs=0; followups=0; judge_scores=0; unauthorized_side_effects=0`

M4 Gate IV authorization local gates before claim: `PASSED; focused=42/42; full=618/618; authorization_audit=READY_UNCONSUMED; configured_default_check=MATCHED; results_audit=NOT_RUN`

M4 Gate IV judge and later gates: `judge_execution=false; blind_mapping_access=false; aggregation=false; closure=false`

M4 separate fresh-execution authorization: `CONSUMED; SAME_REVISION_CONTINUATION_FORBIDDEN`

M4.0 pre-dispatch failure: `PRESERVED; failed_stage=frozen_request_bundle_hash_verification; batch=M4-BATCH-NUC; task_id=null; System.Convert.ToHexString unavailable on PowerShell 5.1 / CLR 4.0`

M4.0 failure evidence: `evals/m4/execution/m4.0/pre-dispatch-failure.json; sha256=8ef9487ce617aeafefc6d665a981581ffc046b541cf426f22d434be689f007ff`

M4.0 fresh result state: `NOT_RUN; result_roots=0; results_manifest=ABSENT`

M4.0 terminal local gate: `PASSED; focused=8/8; execution_audit=PRE_DISPATCH_FAILED_PRESERVED; first exact-HEAD CI=FAILED on c5c25c5a4e8439bf3b54e16e6e65237911ed99b4 (GitHub Actions run 31244970922; Linux single-branch authorization ref lookup); compatibility-fix exact-HEAD CI=PASSED on f48ab8d7e835e9a57e65b75458faa786d696316d (GitHub Actions run 31246286753)`

M4.1 successor state: `PREPARATION_ONLY; OFFLINE_ONLY`

M4.1 predecessor terminal baseline: `f48ab8d7e835e9a57e65b75458faa786d696316d` (GitHub Actions run `31246286753`; `success`)

M4.1 preparation manifest: `evals/m4/revisions/m4.1/preparation-manifest.json`

M4.1 preparation matrix: `12 cases; 5 arms; 60 planned tasks; 6 domain batches`

M4.1 task identity state: `60 new task IDs; 0 reused; blind IDs=M4-J061..M4-J120; 6 new batch IDs`

M4.1 fresh execution authorized: `false; separate Gate IV review and authorization required after green preparation exact-HEAD CI`

M4.1 preparation counters: `authorized=0; contexts=0; dispatched=0; finalizations=0; results=0; judge_scores=0; retries=0; repairs=0; unauthorized_side_effects=0`

M4.1 result state: `NOT_RUN; launch_claim=ABSENT; result_roots=0; results_manifest=ABSENT`

M4.1 preparation local gates: `PASSED; focused=12/12; combined=62/62; full=638/638; preparation_audit=PREPARED_NOT_AUTHORIZED; PowerShell 5.1 self-test=PASSED; request_bindings=60/60; Skill validator=PASSED; workflow_yaml=VALID`

M4.1 preparation exact-HEAD CI: `NOT_RUN; this preparation commit does not pre-claim success`

M4.1 authorization and fresh execution: `NOT_STARTED`

r5.1 CI and acceptance hardening implementation: `COMPLETE`

r5.1 implementation exact-HEAD CI: `PASSED` on HEAD `18e48e38e44b0f0e18e323246496e0919d36fcdc` (GitHub Actions run `31105995299`)

r5.1 first closure-evidence exact-HEAD CI: `FAILED` on HEAD `92517be9b936b299f1cd1fa04bee120ef4760323` (GitHub Actions run `31107751125`)

r5.1 corrected closure-evidence exact-HEAD CI: `PASSED` on HEAD `c5ca408beedf2c3f20160fb1d06293336eacd725` (GitHub Actions run `31108332769`)

r5.1-f02 replacement one-shot fresh execution: `TERMINAL_NOT_ACCEPTED`

r5.1-f02 preparation implementation HEAD: `df327ec4a1faf5b0b5a5f10804ee33efab24accf`

r5.1-f02 preparation exact-HEAD CI: `PASSED` on HEAD `bbf54721b090d9d91b269d88e31919ae00fb0a39` (GitHub Actions run `31115643290`)

r5.1-f02 one-shot fresh-context authorization: `PASSED; CONSUMED`

r5.1-f02 authorization-readiness implementation: `COMPLETE`

r5.1-f02 authorization-readiness implementation HEAD: `7df109e120f0769e8d5b8dddac50666fb8859bc9`

r5.1-f02 authorization-readiness local gates: `PASSED`

r5.1-f02 authorization-readiness exact-HEAD CI: `PASSED` on HEAD `dae68ebd0d876a4aa2258f12a4a7ad8b4948e5ea` (GitHub Actions run `31144763405`)

r5.1-f02 one-shot execution-authorization implementation: `COMPLETE`

r5.1-f02 one-shot execution-authorization implementation HEAD: `69c2e1cbad792a97467bdd2f3f05fc56b4499bc9`

r5.1-f02 one-shot execution-authorization local gates: `PASSED`

r5.1-f02 one-shot execution-authorization exact-HEAD CI: `PASSED` on HEAD `85ce824c55a3a40f3f05153a57edb809dc68eee6` (GitHub Actions run `31162936407`)

r5.1-f02 fresh-context execution: `NOT_ACCEPTED` (`processing_failed`; `payload_invalid_json`)

r5.1-f02 execution counters: `tasks=1; finalizations=1; composer=1; validator=0; retry=0`

r5.1-f02 retry: `FORBIDDEN`

r5.1-f02 replacement task budget: `CONSUMED`

r5.1-f02 authorization token: `CONSUMED / TERMINAL`

r5.1-f02 aggregate role: `EXCLUDED_IMMUTABLE_FAILED_ATTEMPT`

Gate 1 root-cause and protocol preparation: `COMPLETE`

Gate 1 implementation HEAD: `86a24a4d1895a565ce54ce087627e32ebbb4c30f`

Gate 1 primary root cause: `authorization_not_visible_in_consumed_turn`

Gate 1 consumed-turn authorization visibility: `ABSENT`

Gate 1 external authorization: `PRESENT; NOT_MODEL_VISIBLE_IN_CONSUMED_TURN`

Gate 1 late authorization: `POST_TERMINAL_OBSERVATION_ONLY`

Gate 1 offline parser replay: `1; payload_invalid_json; model_calls=0; writes=0; retries=0`

Gate 2: `COMPLETE; EXACT_HEAD_CI_PASSED`

Gate 2 implementation HEAD: `1b6583b694c0d2263bcf7e12bf62b4a5e6567a47`

Gate 2 delivery HEAD: `05e64d9678f9755126b1c1a0bfa4835bd8296e08`

Gate 2 exact-HEAD CI: `PASSED` (GitHub Actions run `31184790162`)

Gate 2 local gates: `PASSED; focused=32/32; full=518/518`

Gate 2 output mode: `strict_text_json_fail_closed; capability recheck required before Gate 3`

Gate 2 prompt contradiction lint: `PASSED`

Gate 2 new fresh-run authorization: `false`

Gate 3 one-shot authorization: `CONSUMED; EXACT_HEAD_CI_PASSED`

Gate 3 authorization implementation HEAD: `765b99afe2b9b0968fbbcbff1f24dd6119fa1da1`

Gate 3 corrected authorization delivery HEAD: `0a6bb7876148a8990934c88cd0fe11aebc0cad7d`

Gate 3 authorization exact-HEAD CI: `PASSED` (GitHub Actions run `31189442896`)

Gate 3 first authorization exact-HEAD CI: `FAILED` on HEAD `eb154888cdb43b62ce039b06e9e5dc0027885be2` (GitHub Actions run `31188398030`; stale Gate 2 status assertion and platform-dependent Gate 2 worktree-byte comparison)

Gate 3 authorization receipt SHA-256: `84a684c6a5b12ad207f41fea04dfe26bb88d4c2cb233e774ff36fef110e62604`

Gate 3 execution-control SHA-256: `98c418aaebea54e148894ab86f791cd060d57cc1ef2ab262bf432d0747b3904e`

Gate 3 terminal evidence exact-HEAD CI: `PASSED` on HEAD `461e833d7ee2bdd3314aa261194963c4497577c7` (GitHub Actions run `31192483833`)

r5.2-f02 fresh execution: `ACCEPTED; TERMINAL`

r5.2-f02 task ID: `019fdcb5-14e4-7462-be4f-379b72171a4d`

r5.2-f02 finalization ID: `019fdcb5-1932-7182-a682-ea8bbd4703ab`

r5.2-f02 raw final: `14532 bytes; sha256=a8ec9c94fe5b55555dd1907e770054aacb5d396d050175b18d0f8d435c97eac7`

r5.2-f02 result root: `TERMINAL; entries=13; logical_artifacts=12; allowlist_match=true`

r5.2-f02 counters: `tasks=1; finalizations=1; composer=1; validator=1; retry=0`

r5.2-f02 retry: `FORBIDDEN`

Gate 4: `COMPLETE; CROSS_REVISION_AGGREGATE_ACCEPTED; EXACT_HEAD_CI_PASSED`

M3 final validation: `PASSED; AGGREGATE_CANDIDATE_EXACT_HEAD_CI_PASSED`

M3 closure: `CLOSED; CLOSURE_AUDIT_PASSED; DELIVERY_EXACT_HEAD_CI_PASSED`

M3 closure delivery HEAD: `716c11b9154a1ff3b866b7f64d39b1c6a9039e54`

M3 closure delivery exact-HEAD CI: `PASSED` (GitHub Actions run `31233977467`)

Gate 4 selects the immutable accepted r5 evidence for F01, F03, F04, and F05 together with the separately accepted r5.2-f02 F02 evidence. The historical r5 F02 `processing_failed` result and the 216-byte r5.1-f02 `terminal_not_accepted` result remain excluded immutable attempts; neither is relabeled, repaired, retried, or deleted. Aggregate candidate HEAD `3be04218b038bac7a55da10a553a5ce05be4652c` passed exact-HEAD run `31233356741`, and the successor closure manifest binds that green candidate and passes the read-only closure audit. M3 is `CLOSED`; closure delivery HEAD `716c11b9154a1ff3b866b7f64d39b1c6a9039e54` passed exact-HEAD run `31233977467`. M4 is active only for offline preparation, and fresh M4 tasks remain unauthorized.

Before route-specific method-card instantiation, M3.1.1 must validate the complete M2.1.1 bundle, require `user_confirmed`, recompute the selected-direction binding, reject every non-empty `approved_constraint_changes` list with `unsupported_approved_constraint_change_provenance`, and rederive claim metrics, claim-specific preconditions, resource ceilings, actual Go/Stop/Pivot coverage, safety-source eligibility, and method-card internal bindings from upstream structures.

## M3 checklist

- [x] Existing M3.1 implementation, references, 57 focused validator tests, 16 offline cases, local validation record, and package audit are preserved as historical evidence.
- [x] M3.1.1 branch `codex/m3.1.1-acceptance-hardening` created directly from exact input HEAD `b0a1b9e41e85a1b57c80a8b571bac9ca01c88778` with a clean worktree.
- [x] M3.1.1 acceptance plan created outside the installable Skill.
- [x] Safety-source, non-negative-resource, and method-card claim/metric binding gates implemented; focused validator suite passes 62/62.
- [x] Twenty deterministic M3 adversarial cases regenerated and replayed byte-stably.
- [x] Independent M2 input preparation preserved in the r2 worktree: F01/F02/F03/F05 M2-valid artifacts; F04 explicit NOT_RUN with its non-nuclear prerequisite gap.
- [x] R2 inputs, prompts, outputs, validation receipts, and context records frozen by raw SHA-256 and Git blob identity in `evals/m3/results/forward-r3/r2-freeze-diagnostic.json`; F01 JSON syntax coordinates and F05 missing-output evidence remain explicit.
- [x] R3 deterministic artifact composer, case-level eligibility auditor, expected-blocked F03 forward outcome, and exact one-shot outcome evidence runner implemented red-first; the full suite passes 314/314.
- [x] R3 F01/F02/F03 and revised route-specific F05 inputs are eligible; F05 reuses the route-compatible F02 lineage and the old route-free r2 F05 remains ineligible for the revised case.
- [x] Independent non-nuclear F04 upstream lineage reaches new M1_COMPLETE, valid provisional M2.1.1, explicit user confirmation, independent acceptance, and eligible case status before any new fresh-context run.
- [x] R3 consumed its five authorized fresh contexts exactly once without repair or retry; F05 was accepted and F01/F02/F03/F04 remain invalid. Those outcomes remain historical evidence and are not being retried.
- [x] Fresh-worktree r4 byte gate passes at 66/66 immutable filesystem/Git-blob comparisons with zero mismatches; successor receipt `evals/m3/results/forward-r4/r2-r3-byte-preservation-fresh-worktree.json` preserves the result and the prior blocked receipt remains unchanged.
- [x] R4 inputs, five eligibility receipts, closed contract, five prompts, case specification, and acceptance manifest are frozen with exact raw/canonical hashes, `prompts_frozen=true`, `fresh_contexts_consumed=0`, and no future result/receipt paths.
- [x] Complete local r4 preparation gates pass at HEAD `fca83eecf4737a00f37a129d31a1822344b2eac0`: focused 29/29, full 334/334, unchanged M1/M2/M3 replays, package audit, and Skill validation. This is local structural evidence only; no exact-HEAD remote CI or closure CI is claimed.
- [ ] Five genuinely fresh-context r4 forward evaluations completed with accepted validator results. The first coordinator consumption, F03, stopped with `consumed_with_callback_failure`; no remaining case was dispatched, composed, or validated after that failure.
- [x] F03 one-shot evidence and the dispatcher callback failure are preserved at `evals/m3/results/forward-r4/m3-f03.outcome.json`, `m3-f03.validation.json`, and `m3-f03.dispatch-callback-failure.json`; no repair or retry was performed and all later r4 acceptance/closure gates remain `NOT_RUN`.
- [x] r5.1 CI/acceptance hardening implementation HEAD `18e48e38e44b0f0e18e323246496e0919d36fcdc` passed exact-HEAD GitHub Actions run `31105995299`; validate, Ubuntu historical audit, and Windows historical audit all completed successfully with no skipped project gates. This closes only r5.1 hardening and leaves r5 blocked.
- [x] r5.1 closure-evidence exact-HEAD CI. First closure record HEAD `92517be9b936b299f1cd1fa04bee120ef4760323` failed run `31107751125`; corrected closure HEAD `c5ca408beedf2c3f20160fb1d06293336eacd725` passed run `31108332769` with validate and both cross-platform jobs successful.
- [x] r5.1-f02 offline replacement preparation freezes a new F02 input binding, authority-explicit prompt and contract, one-case manifest, all-zero counters, and a zero-artifact result root without changing frozen r5 evidence.
- [x] Generic route-specific method-card regression rejects drift in authoritative `metric_id`, `criterion_type`, `value`, or `unit`; the existing strict condition-object equality remains the enforcement mechanism.
- [x] Local r5.1-f02 preparation gates pass at implementation HEAD `df327ec4a1faf5b0b5a5f10804ee33efab24accf`: 395 tests, unchanged replays, empty M2/M3 regeneration diffs, package and Skill audits, expected r5 blocked-state audit, and the new read-only preparation audit.
- [x] r5.1-f02 preparation exact-HEAD remote CI passed on HEAD `bbf54721b090d9d91b269d88e31919ae00fb0a39` in GitHub Actions run `31115643290`; validate, immutable-evidence preflight, Ubuntu historical audit, and Windows historical audit all succeeded.
- [x] Authorization readiness adds operator drift to the generic route-card regression and verifies route-specific nuclear-overlay authority drift for metric, operator, value, and unit without changing the validator.
- [x] The dedicated r5.1-f02 authorization auditor binds preparation HEAD `bbf54721b090d9d91b269d88e31919ae00fb0a39`, evidence HEAD `1b696bce53ee0a11163bfe4f91a9a49ab3af6f49`, source/prompt/contract/receipt identities, the base-contract path/OID/raw/canonical tuple, zero counters, canonical future paths, and an empty result root.
- [x] The narrow readiness dispatcher is limited to `m3-f02` / `r5.1-f02` and invokes no callback even after a valid readiness preflight because no fresh authorization receipt exists.
- [x] Local authorization-readiness gates pass at implementation HEAD `7df109e120f0769e8d5b8dddac50666fb8859bc9`: 418 tests, 22 focused authorization/dispatcher tests, unchanged replays, empty M2/M3 regeneration diffs, package and Skill audits, and zero immutable-r5 diff.
- [x] Authorization-readiness exact-HEAD remote CI passed on HEAD `dae68ebd0d876a4aa2258f12a4a7ad8b4948e5ea` in GitHub Actions run `31144763405`; validate and both cross-platform historical-audit jobs succeeded.
- [x] A successor execution-authorization receipt binds the readiness HEAD/run, predecessor manifest identity, preparation/source/input/prompt/contracts/receipts/policy/route authority, one-task maxima, no-retry/no-repair rules, and a zero-artifact result root without changing the frozen readiness evidence.
- [x] The separate once dispatcher uses an exclusive launch-attempt claim and immutable launch receipt; temporary-directory tests prove at-most-one callback, immutable first task binding, terminal callback failure, historical-task rejection, exact raw-final preservation, and no second finalization or overwrite.
- [x] Local one-shot execution-authorization gates pass at implementation HEAD `69c2e1cbad792a97467bdd2f3f05fc56b4499bc9`: 440 tests, 22 focused tests, unchanged replays, empty M2/M3 regeneration diffs, package and Skill audits, preparation/readiness/execution audits, zero immutable-r5 diff, zero replacement artifacts, zero historical retries, and zero fresh callbacks.
- [x] One-shot execution-authorization exact-HEAD remote CI passed on HEAD `85ce824c55a3a40f3f05153a57edb809dc68eee6` in GitHub Actions run `31162936407`.
- [x] One new r5.1-f02 fresh-context task was launched and finalized exactly once. The preserved non-JSON final failed composition with `payload_invalid_json`; composer invocation count is one, validator invocation count is zero, accepted is false, and retry is forbidden.
- [x] The terminal manifest and read-only terminal auditor freeze the consumed task, finalization, malformed payload, composer failure, transaction, predecessor authorization, prompt/input/contracts, and unchanged historical r5 tree. Current CI uses the terminal gate; predecessor preparation/readiness auditors retain their historical semantics.
- [x] Gate 1 separates and hash-binds the frozen repository prompt, the consumed-turn model-visible message envelope, and the external user authorization. It confirms `authorization_not_visible_in_consumed_turn` with direct evidence and classifies all 216 raw bytes as non-JSON authorization-deferral prose.
- [x] Gate 1 performs exactly one offline replay through the existing composer loader, reproducing `payload_invalid_json` at line 1, column 1, byte offset 0 with zero model calls, writes, or retries. The late authorized turn remains post-terminal observation only.
- [x] Gate 2 locally freezes the contradiction-free r5.2-f02 prompt, hash-bound input and authorization-receipt schema, strict JSON boundary, raw-response observation schema, nine synthetic regression cases, read-only preparation auditor, and callback-free dispatcher. The logical result root contains only an empty `.gitkeep`; no authorization receipt instance, task, finalization, composer call, validator call, or retry exists. Exact-HEAD remote CI remains pending at this record commit.
- [x] Gate 3 authorization baseline HEAD `0a6bb7876148a8990934c88cd0fe11aebc0cad7d` passed exact-HEAD GitHub Actions run `31189442896` before the exclusive launch claim was consumed.
- [x] Gate 3 created exactly one new r5.2-f02 task and consumed exactly one finalization. The 14,532-byte raw final is frozen before parsing with SHA-256 `a8ec9c94fe5b55555dd1907e770054aacb5d396d050175b18d0f8d435c97eac7`; composer and validator counts are one, retry is zero, and the result is accepted.
- [x] The r5.2-f02 terminal manifest and independent production replay auditor report `accepted`, exact `1/1/1/1/0` counters, an exact result-root allowlist, no unexpected artifacts or side effects, unchanged historical r5 and r5.1 evidence, and `Gate 4 = NOT_STARTED`.
- [x] Gate 4 preserves that terminal manifest as a historical snapshot and selects exactly F01/F03/F04/F05 from immutable r5 plus F02 from immutable r5.2-f02; r5 and r5.1-f02 F02 remain excluded failed attempts.
- [x] The local cross-revision aggregate audit accepts selected counters `5/5/4/5/5/0/0` and separately preserves historical-attempt counters `7/7/6/5/5/2/0`, with zero retries and no M4 authority.
- [x] Aggregate candidate HEAD `3be04218b038bac7a55da10a553a5ce05be4652c` passed exact-HEAD GitHub Actions run `31233356741`; validate, Ubuntu, and Windows jobs all succeeded.
- [x] The successor closure manifest binds the green candidate and its aggregate manifest, aggregate audit, and final-validation Git blobs; the read-only closure audit reports `closed`, M3 is `CLOSED`, and M4 remains `NOT_STARTED`.
- [ ] The closure delivery HEAD must pass its own exact-HEAD remote CI; no follow-up commit is used solely to record that external run.

## M3.1.1 r5 historical preparation and terminal result

Historical preparation status: `READY_FOR_AUTHORIZED_R5_FRESH_CONTEXTS`

Terminal status: `BLOCKED_NOT_ACCEPTED`

The independent r5 dispatcher-receipt and five-task contract repair was structurally ready on branch `codex/m3.1.1-r5-dispatch-contract-repair`. The required starting HEAD was `66c1da40afe8e03ae9e3a6ab8ab3e9ad06423b14`; the readiness validation snapshot before authorization was `2d5c67780d711b5cbcb5dbac06e7f532cd9ca184`. Before authorization, all five r5 source cases were eligible, the closed future-path contract and batch preflight passed with zero side effects, prompts and contracts were hash-frozen, and every task, finalization, processing, invocation, acceptance, and transaction-failure counter was zero. The pre-authorization preparation manifest remains unchanged at `evals/m3/results/forward-r5/acceptance-manifest.json`. See `evals/m3/results/2026-08-06-m3.1.1-r5-preparation-validation.md`.

This readiness status is preparation evidence only. After the separately authorized one-shot r5 consumption, the r5 terminal status is recorded below as `BLOCKED_NOT_ACCEPTED`; M3 remains `IN_PROGRESS`; M4 and M5 remain `NOT_STARTED`. The following M3 local-result section preserves the historical r4 `BLOCKED_NOT_ACCEPTED` state and is not reinterpreted as r5 evidence.

Authorized r5 consumption observed exactly five finalizations and made exactly five dispatcher callbacks. F01, F03, F04, and F05 reached `processed_accepted`; F02 preserved a `processing_failed` transaction after its only composer invocation returned `composer_invocation_failed`. The derived counters are `tasks_launched=5`, `task_finalizations_observed=5`, `dispatcher_cases_preflighted=5`, `dispatcher_cases_processed=4`, `composer_invocations=4`, `validator_invocations=4`, `accepted_cases=4`, and `transaction_failures=1`. The acceptance audit returned `blocked_not_accepted`; later acceptance/closure gates are `NOT_RUN`. Full evidence is in `evals/m3/results/forward-r5/acceptance-manifest-consumed.json` and `evals/m3/results/2026-08-06-m3.1.1-r5-forward-consumption-validation.md`.

## M3.1.1 r5.1 CI and acceptance hardening closure

Status: `IMPLEMENTATION_COMPLETE; FIRST_CLOSURE_RECORD_CI_FAILED; CORRECTED_CLOSURE_RECORD_PENDING_EXACT_HEAD_CI`

Implementation HEAD `18e48e38e44b0f0e18e323246496e0919d36fcdc` passed exact-HEAD GitHub Actions run `31105995299`. The `validate` job and both Ubuntu and Windows historical-audit jobs concluded `success`; every project validation step executed successfully. The full local suite passed 388 tests, M1/M2/M3 replays matched their frozen expectations, both fixture-regeneration diffs were empty, the package and standard Skill audits passed, and the expected r5 blocked-state audit remained valid. The frozen r5 result tree has zero diff from evidence HEAD `1b696bce53ee0a11163bfe4f91a9a49ab3af6f49`.

The first closure-evidence record HEAD `92517be9b936b299f1cd1fa04bee120ef4760323` failed exact-HEAD run `31107751125`: both cross-platform historical-audit jobs succeeded, but `test_status_top_reports_current_r5_blocked_state` rejected replacement of the preserved r5 `Exact-HEAD CI: FAILED` field, and all later validate steps were skipped. This correction restores that r5 field and records the successful r5.1 implementation CI separately. It does not relabel F02, accept r5, or close M3. The corrected closure-evidence commit cannot truthfully embed or pre-claim its own SHA or exact-HEAD CI; that successor gate remains `NOT_RUN` until push and is reported externally afterward. See `evals/m3/results/2026-08-06-m3.1.1-r5.1-ci-closure-validation.md`.

## M3.1.1 r5.1-f02 replacement preparation

Status: `LOCAL_READY_AWAITING_FRESH_AUTHORIZATION`

The replacement preparation is isolated under `evals/m3/forward-inputs-r5.1-f02/` and reserves `evals/m3/results/forward-r5.1-f02/`. Its input binding pins the existing eligible route-compatible F02 input by raw, canonical, and Git-blob identity, and separately pins the canonical stop/pivot authority derived from `route_output`. The prompt and output contract require exact inheritance of `criterion_type`, `metric_id`, `operator`, `value`, and `unit`; they forbid synthesis, normalization, conversion, or rounding of authoritative conditions.

The preparation manifest keeps every task, finalization, processing, composer, validator, acceptance, and failure counter at zero. `new_fresh_run_authorized` is false, `reserved_task_id` is null, and the new result root contains no result or receipt artifact. The auditor verifies the frozen `replace_f02_only` erratum, rejects reuse of the historical F02 task or result root, binds the four reusable r5 accepted cases to evidence HEAD `1b696bce53ee0a11163bfe4f91a9a49ab3af6f49`, and requires the entire historical `forward-r5` tree to remain unchanged.

Local structural validation passed at implementation HEAD `df327ec4a1faf5b0b5a5f10804ee33efab24accf`; remote exact-HEAD CI, fresh-context launch, one-shot finalization, composition, consumption, cross-revision aggregation, M3 closure, and M4 remain `NOT_RUN`. See `evals/m3/results/2026-08-06-m3.1.1-r5.1-f02-preparation-validation.md`.

## M3.1.1 r5.1-f02 authorization readiness

Status: `READY_FOR_FRESH_AUTHORIZATION`

The independent authorization manifest remains a readiness receipt, not an execution authorization: `new_fresh_run_authorized=false` and `reserved_task_id=null`. The read-only auditor verifies every frozen preparation and historical identity from the declared Git heads, including the replacement contract's complete base-contract dependency tuple. It rejects any preparation/evidence head drift, source or route-authority drift, prompt/contract/receipt drift, historical task or root reuse, nonzero counter, unsafe future path, result artifact, or historical r5 tree change.

The historical narrow dispatcher exposes no execution path. A valid readiness audit still returns `callback_invocations=0` with `fresh_run_not_authorized`; no task is created or reserved and no final is consumed. Local validation passed at implementation HEAD `7df109e120f0769e8d5b8dddac50666fb8859bc9`, and exact-HEAD CI passed on readiness HEAD `dae68ebd0d876a4aa2258f12a4a7ad8b4948e5ea` in GitHub Actions run `31144763405`. See `evals/m3/results/2026-08-07-m3.1.1-r5.1-f02-authorization-readiness-validation.md`.

## M3.1.1 r5.1-f02 one-shot execution authorization

Authorization status: `CONSUMED`

The successor `execution-authorization.json` does not modify or reinterpret the frozen readiness manifest. It binds readiness HEAD `dae68ebd0d876a4aa2258f12a4a7ad8b4948e5ea`, successful run `31144763405`, preparation baseline `bbf54721b090d9d91b269d88e31919ae00fb0a39`, historical evidence HEAD `1b696bce53ee0a11163bfe4f91a9a49ab3af6f49`, and every source, prompt, contract, receipt, policy, and route-authority identity. Its scope is exactly one new `m3-f02` / `r5.1-f02` fresh task, with one finalization, one composer invocation, one validator invocation, and no retry, repair, second finalization, historical reuse, aggregate acceptance, M3 closure, or M4 authority.

Before consumption, the read-only execution auditor reported `ready_for_one_shot_fresh_execution` with all counters zero, result artifact count zero, historical F02 retry count zero, callback invocations zero, and no side effects. The authorization baseline was finalized at exact HEAD `85ce824c55a3a40f3f05153a57edb809dc68eee6`, which passed GitHub Actions run `31162936407`. See `evals/m3/results/2026-08-07-m3.1.1-r5.1-f02-one-shot-execution-authorization-validation.md`.

## M3.1.1 r5.1-f02 one-shot fresh execution

Status: `TERMINAL_NOT_ACCEPTED`

The one-shot dispatcher bound fresh task `019fdb7c-1728-7a92-b6cf-b0eb631a18b8` with launch count one, callback invocation count one, and no historical task reuse. The only finalization preserved 216 raw bytes with SHA-256 `75b4f9f5f4e2459b2886c0a9654c8cc1bda4015c525869cd154a302a2bc0589a`. The existing composer was invoked once and rejected the non-JSON payload as `payload_invalid_json`; validator invocation count remained zero. The transaction state is `processing_failed`, accepted is false, and retry is forbidden. See `evals/m3/results/2026-08-07-m3.1.1-r5.1-f02-one-shot-execution-validation.md`.

M3 remains `IN_PROGRESS`, historical r5 remains `BLOCKED_NOT_ACCEPTED`, fresh F02 is `NOT_ACCEPTED`, cross-revision aggregate acceptance remains `NOT_RUN`, M3 closure remains `NOT_RUN`, and M4 remains `NOT_STARTED`.

The r5.1-f02 replacement task budget is `CONSUMED`, retry is `FORBIDDEN`, and the one-shot authorization token is `CONSUMED / TERMINAL`. No second task or second finalization is authorized. The terminal closure does not accept F02, aggregate r5 and r5.1 evidence, close M3, or start M4.

## M3.1.1 r5.2-f02 Gate 1 root-cause and protocol preparation

Status: `COMPLETE; GATE_2_LOCAL_COMPLETE`

The read-only, hash-bound report at `evals/m3/results/diagnostics-r5.2-f02/root-cause-report.json` distinguishes three contexts that the failed one-shot workflow had treated as interchangeable: the frozen repository prompt, the messages actually visible to the consumed fresh-model turn, and the external user authorization. The external workflow authorization was present before child creation, but it was not included in the consumed turn. The unchanged frozen prompt instead described a future task and instructed the model not to execute without separate authorization. The complete first final followed that instruction and returned 216 bytes of non-JSON authorization-deferral prose.

The primary root cause is `authorization_not_visible_in_consumed_turn`. Output truncation, wrong consumed-message selection, Markdown or prefix/suffix corruption, and a composer-path defect are ruled out by the completed platform state, exact final/task-complete/model-final/payload byte equality, the post-terminal timing of the later authorized turn, and one offline replay of the existing composer loader. Provider `request_id` and `finish_reason` were not recorded and remain explicitly unavailable rather than inferred. The later authorized turn and its valid JSON are observation-only and do not repair, retry, or relabel r5.1-f02.

Local Gate 1 validation passed on implementation HEAD `86a24a4d1895a565ce54ce087627e32ebbb4c30f`: 17 focused tests, 486 full tests, a deep audit of the child rollout, source consumption prefix, and external authorization attachment, the existing terminal auditor, and the CI-state auditor. Historical `forward-r5` and `forward-r5.1-f02` diffs are empty. The immutable Gate 1 report retains its as-recorded `gate2=NOT_STARTED` and `r5_2_result_root=ABSENT` snapshot; the successor Gate 2 preparation now permits only the logical-empty result root marker and does not reinterpret the root-cause findings. See `evals/m3/results/2026-08-07-m3.1.1-r5.2-f02-root-cause-validation.md`.

## M3.1.1 r5.2-f02 Gate 2 execution protocol preparation

Status: `COMPLETE; EXACT_HEAD_CI_PASSED; FRESH_EXECUTION_NOT_RUN`

The model-facing prompt begins with `This is the authorized r5.2-f02 execution.` and `Execute the frozen task now.`; those lines are part of its frozen SHA-256 `815eae213701505755fb7edc4d64d16089bd4e14e14dc6ec1e16c787918ea1df`. Case-insensitive lint rejects `do not execute`, `future task`, and `without separate authorization`. The separate Gate 3 receipt schema binds that prompt hash, input-binding SHA-256 `3d90ed7f02a865eb3cab0fd8f70f0407ce5a80a93e500996686e2fad54c1709d`, `authorized=true`, and exactly one authorized task; no receipt instance or task ID exists in Gate 2.

GPT-5.6 Sol documents native Structured Outputs support, but the current `codex_app.create_thread` request surface exposes no response-format or JSON-Schema parameter. Gate 2 therefore freezes `strict_text_json_fail_closed`, no automatic repair, and a mandatory capability recheck before Gate 3. The text boundary requires one UTF-8 JSON object, first and last non-whitespace bytes `{` and `}`, no BOM, Markdown fence, surrounding prose, comments, duplicate keys, additional JSON values, or non-finite numbers. A separate pre-parser observation schema records raw bytes and SHA-256, byte count, model/task/request/finalization identities, finish reason, token counts, task timestamps, request-envelope hash, and model-visible-message hash; unexposed provider fields remain explicit `null` / `not_exposed` rather than inferred.

Local validation passed on implementation HEAD `1b6583b694c0d2263bcf7e12bf62b4a5e6567a47`: 32 focused Gate 2 tests, 49 combined Gate 1/Gate 2 tests, and 518 full tests; unchanged M1, M2, and M3 replays; empty M2/M3 fixture-regeneration diffs; valid package and standard Skill audits; valid r5 blocked-state, r5.1 terminal, Gate 1 root-cause, Gate 2 preparation, and callback-free dispatcher audits. Historical `forward-r5` and `forward-r5.1-f02` Git trees match their frozen evidence heads. `evals/m3/results/forward-r5.2-f02/` contains only an empty `.gitkeep`; task/finalization/composer/validator/retry counters remain `0/0/0/0/0`; `new_fresh_run_authorized=false`; fresh execution, cross-revision aggregation, M3 closure, and M4 remain `NOT_RUN`. Delivery HEAD `05e64d9678f9755126b1c1a0bfa4835bd8296e08` passed exact-HEAD GitHub Actions run `31184790162`. See `evals/m3/results/2026-08-07-m3.1.1-r5.2-f02-protocol-preparation-validation.md`.

## M3.1.1 r5.2-f02 Gate 3 one-shot fresh execution

Status: `COMPLETE; TERMINAL_ACCEPTED; TERMINAL_EVIDENCE_CI_PASSED`

The external authorization receipt is a separate closed five-field object with `revision=r5.2-f02`, `authorized=true`, the frozen prompt and input-binding SHA-256 values, and `authorized_task_count=1`. Its raw SHA-256 is `84a684c6a5b12ad207f41fea04dfe26bb88d4c2cb233e774ff36fef110e62604`. The execution-control record has raw SHA-256 `98c418aaebea54e148894ab86f791cd060d57cc1ef2ab262bf432d0747b3904e`; it binds Gate 2 delivery HEAD `05e64d9678f9755126b1c1a0bfa4835bd8296e08`, successful run `31184790162`, this branch, the worktree project target, the exact prompt as the sole initial user message, and one-task/one-finalization/one-composer/one-validator/no-retry limits.

The current `codex_app.create_thread` surface was rechecked and still exposes `model`, `prompt`, `target`, `thinking`, and `title`, with no response-format or JSON-Schema request field. The selected mode therefore remains `strict_text_json_fail_closed`. The frozen request projection omits `model` and `thinking`, has SHA-256 `8617b95e1560632285fd5b08dc114a16a37718f83e7769cc9ff00d79fa92ce1f`, and the initial-user-message projection has SHA-256 `fc3ca3d98bf96c9e3d389df38d49b35e00c636231b2aa47c9d00be72b28e6f49`.

Initial authorization delivery HEAD `eb154888cdb43b62ce039b06e9e5dc0027885be2` failed GitHub Actions run `31188398030` before execution. The failures were confined to a stale status test that still required the Gate 2 heading and an authorization audit that compared non-byte-sensitive Gate 2 source worktree bytes with Git blobs, which failed on Windows CRLF materialization. Fix HEAD `765b99afe2b9b0968fbbcbff1f24dd6119fa1da1` updates the status assertions to the Gate 3 `NOT_RUN/0` truth and compares Gate 2 committed Git blobs with Gate 2 committed Git blobs. No launch claim or task was created during the failed run or fix. Corrected authorization delivery HEAD `0a6bb7876148a8990934c88cd0fe11aebc0cad7d` passed GitHub Actions run `31189442896`; validate and both cross-platform jobs were green before execution began.

After that green gate, the exclusive launch claim created exactly one new task, `019fdcb5-14e4-7462-be4f-379b72171a4d`, with one completed turn/finalization, `019fdcb5-1932-7182-a682-ea8bbd4703ab`. No follow-up message, retry, second task, or second finalization was created. The tool-boundary final was frozen as 14,532 UTF-8 bytes with SHA-256 `a8ec9c94fe5b55555dd1907e770054aacb5d396d050175b18d0f8d435c97eac7` before the strict parser ran. Provider request ID, finish reason, input tokens, and output tokens were not exposed and are recorded as `null` / `not_exposed`, not inferred.

The strict parser accepted exactly one JSON object. The production composer and validator were each invoked once; the validator returned `valid` with no errors or evidence gaps, the transaction completed, and the terminal manifest records `accepted=true`. Final counters are `tasks/finalizations/composer/validator/retry=1/1/1/1/0`. The 13-entry result-root allowlist matches exactly, unexpected artifacts and side effects are empty, the fresh task worktree is clean, and historical `forward-r5` and `forward-r5.1-f02` diffs are empty. The independent terminal auditor reproduces the accepted composer/validator outcome without writing or retrying. Gate 4, cross-revision aggregation, M3 final validation, M3 closure, and M4 remain `NOT_STARTED`. See `evals/m3/results/2026-08-07-m3.1.1-r5.2-f02-one-shot-execution-validation.md`.

Terminal-evidence delivery HEAD `461e833d7ee2bdd3314aa261194963c4497577c7` passed GitHub Actions run `31192483833`. The validate job, Ubuntu historical-audit job, and Windows historical-audit job all completed successfully; the validate job explicitly ran the r5.2-f02 terminal auditor against the accepted evidence. This closes Gate 3 only and does not authorize Gate 4.

## Historical M3 local result before Gate 4

Historical status: `M3.1.1 R5_BLOCKED_NOT_ACCEPTED; R4_BLOCKED_NOT_ACCEPTED; R3_ACCEPTANCE_NOT_ACCEPTED; R2_ACCEPTANCE_BLOCKED`

Fresh-worktree r4 preparation was green at readiness HEAD `058b93d944d67b9e5c862ab5e1e74bb86d652512`. The immutable byte audit reported 66 files, zero filesystem/Git-blob mismatches, and zero errors; the r4 preparation auditor reported five eligible cases, `prompts_frozen=true`, `fresh_contexts_consumed=0`, and no future result or receipt paths. Focused r4 gates passed 29/29, the full unit suite passed 334/334 after the committed fixture LF materialization rule, M1 and M2 replays were valid, the M3 replay matched all 20 frozen cases, the package audit reported 99 Skill lines and 13 linked references with no errors, and the standard Skill validator reported `Skill is valid!`. Five fresh task worktrees were created from the frozen readiness state, but the first coordinator consumption (F03) ended as `consumed_with_callback_failure` after one accepted-expected-block outcome validation; its exact final and failure record are preserved. No remaining fresh case was dispatched or validated, no exact-HEAD remote CI is claimed, and no local closure gate ran. The terminal acceptance record is `evals/m3/results/forward-r4/acceptance-manifest.json`; the preparation record is `evals/m3/results/2026-08-06-m3.1.1-r4-preparation-validation-fresh-worktree.md`.

Historical M3.1 local implementation and validation passed on `2026-08-05`; the M3.1.1 local hardening and deterministic replay also pass. Input HEAD `02d791275e6a8da16655a57aec5188d606c49357` passed GitHub Actions run `31006161680`, which covered the then-current implementation, replay, and package gates. That run does not close the forward acceptance repair. R3 architecture HEAD `0ba619a107f6616083a9531c2770ea7e0908e2af` passed 314 unit tests, unchanged M1/M2/M3 replay, package audit, and the standard Skill validator; this is local structural evidence only. The r3 preparation manifest is `fresh_contexts_consumed_not_accepted`: F01-F05 were all eligible, their five immutable inputs and prompts were frozen by LF-preserved raw SHA-256, and all five authorized fresh contexts were consumed exactly once. F05 was accepted. F01 and F04 produced JSON payloads that the composer rejected as `malformed_m3_bundle`; F02 produced `route_incompatible` with empty cards and overlays and was rejected; F03 produced the expected blocked terminal code but its sole validator call used a nonexistent r3 source alias, so its preserved receipt is invalid. No failed r3 case was repaired or retried. F04-D01 remains backed by a new independent non-nuclear M1_COMPLETE lineage, a valid route-free M2.1.1 confirmation successor, and a distinct fresh-worktree review. The initial F04 review remains preserved as invalid because Windows CRLF checkout changed the filesystem raw hash; path-specific LF rules repaired byte materialization without modifying the F04 or frozen r2 Git blobs, and a new review at HEAD `738f337b2dd645fc5e0c8c159fd42d02b67defc5` passed M1, M2, byte, confirmation, and F04 eligibility gates. The historical blocked acceptance record is `evals/m3/results/2026-08-05-m3.1.1-final-validation.md`; the r2 records are `evals/m3/results/2026-08-05-forward-evaluation-r2.md` and `evals/m3/results/forward-r2/acceptance-manifest.json`. No stale claim that M3 closure candidate HEAD `b0a1b9e` passed Actions run `31000758678` is accepted here. The baseline M2.1.1 Actions run `30977286846` is not M3 implementation CI. R3 does not supersede r2 for acceptance; local closure gates, push, exact final closure CI, M4, and M5 were not run.

Neither the historical local result nor this acceptance revision claims a real experiment, simulation, training run, download, deployment, route execution, target-domain transfer result, operational readiness, or nuclear safety conclusion.

## M2 checklist

- [x] Accepted M2 input HEAD, clean worktree, and exact-HEAD Actions success confirmed.
- [x] M2.1.1 implementation plan created outside the installable Skill.
- [x] `m2.1.1` provenance and semantic gates specified red-first.
- [x] Confirmation and route provenance hash-bound.
- [x] Claim coverage, preprint support, and data-precondition policies enforced.
- [x] Direction axes derived and scorecard rationales hardened.
- [x] M2.1.1 adversarial fixtures generated and replayed deterministically.
- [x] Case A repaired and Case F audited without route execution.
- [x] Local validation and acceptance record pass; implementation HEAD `94a41f423d12630c1058451da2d84b278a5285cf` passed exact-HEAD GitHub Actions run `30977203464`.

### Accepted M2.1 baseline

- [x] M1.2 baseline confirmed complete and the M2 work branch confirmed clean.
- [x] M2 implementation plan created outside the installable Skill.
- [x] `m2.1` direction portfolio and source-evidence lineage contract frozen.
- [x] Hard-gate, evidence-tier, formal-position, axis-separation, scorecard, and decisive-test behavior specified red-first.
- [x] Offline M2 direction bundle validator implemented.
- [x] User confirmation gate enforced for detailed route content.
- [x] Adversarial fixtures and deterministic replay pass.
- [x] Fresh-context direction-decision forward evaluation passes or preserves honest incomplete/blocked evidence.
- [x] Standard Skill validation, full unit suite, package audit, and final M2 scope audit pass.

## M2 result

Status: `M2.1 COMPLETE; M2.1.1 COMPLETE`

M2.1.1 local acceptance passed on `2026-08-05` from implementation HEAD `b66bb5122c11730377ee587d59df3717a37e90ba` with 163 unit tests, both unchanged M1 replays, 34/34 M2.1.1 adversarial cases, byte-stable fixture regeneration, the local standard Skill validator, a repository package audit, revised Case A, and independent Case F. The final implementation-and-evidence HEAD `94a41f423d12630c1058451da2d84b278a5285cf` passed exact-HEAD GitHub Actions run `30977203464`; M2.1.1 is complete and M3 remains `NOT_STARTED`. See `evals/m2/results/2026-08-05-m2.1.1-final-validation.md`.

Validated on `2026-08-05` from acceptance input HEAD `aec8531fa0565e87651b87761717158994afaec1` with:

- Python compilation: exit `0`;
- unit tests: 138 passed;
- M1 frozen replay and machine-artifact replay: valid with the preserved Case B `evidence_incomplete` outcome;
- M2 adversarial replay: 12/12 exact matches;
- standard Skill validator: exit `0`, `Skill is valid!`;
- package audit: 108-line root Skill, five linked references, zero missing or unlinked references, zero unresolved template markers;
- fresh-context Case A/B/D/E bundles: `valid`, zero errors and gaps;
- fresh-context Case C: correctly stopped at M1 `evidence_incomplete`, expected exit `2`;
- confirmation gate: pre-confirmation route refused; explicit D1 confirmation opened the gate without generating or executing a route;
- final record: `evals/m2/results/2026-08-05-m2.1-final-validation.md`.

The accepted M2 closure HEAD `f0a44890fb9e3244ad86fb60f01065715ddb4de0` later passed exact-HEAD GitHub Actions run `30972309423`, job `92199125940`. This supersedes the earlier pre-push remote-not-run state without erasing that historical sequence. M2 completion does not claim empirical transfer success, experiment or simulation performance, model training, download, deployment, operational nuclear safety, or M3 work.

## M1 acceptance baseline

Status: `COMPLETE`

Acceptance revision: `m1.2`

Validated by:

- clean local validation with 108 passing tests;
- successful first-round exact-HEAD GitHub Actions run `30965919907` on `2842b6bc99f48ea17561b67a97205e271a370e4d`;
- successful closure exact-HEAD GitHub Actions run `30966375373` on `37ac4617fa5c506f2d087628b61570cef9c4cdf9`;
- complete two-round machine-valid Case A;
- second-round `evidence_incomplete` machine-valid Case B;
- citation-conflict blocking gate Case C;
- DOI and alternate-ID identity tests;
- round-one and round-two terminal-state tests.

Acceptance evidence:

- pre-push executable-input HEAD: `e234e90364ace4aa203716575ab37a0130b4d322`;
- first remote-CI input HEAD: `2842b6bc99f48ea17561b67a97205e271a370e4d`;
- GitHub Actions workflow/job: `M1 Validation` run `30965919907`, job `92179712580`, conclusion `success`;
- closure commit: `37ac4617fa5c506f2d087628b61570cef9c4cdf9`;
- closure GitHub Actions workflow/job: `M1 Validation` run `30966375373`, job `92181118237`, conclusion `success`;
- Python compilation: exit `0`;
- unit tests: 108 passed;
- frozen fixture replay: `valid`, zero mismatches;
- machine artifacts: Case A `valid`, Case B `evidence_incomplete`, Case C blocking gate `valid`, zero mismatches;
- standard Skill validator: exit `0`, `Skill is valid!`;
- root Skill: 106 lines;
- closure record: `evals/m1/results/2026-08-04-m1.2-final-validation.md`.

Closure commit `37ac4617fa5c506f2d087628b61570cef9c4cdf9` was successfully validated by exact-HEAD `M1 Validation` run `30966375373`. This post-CI evidence-record commit cannot embed its own SHA or pre-claim its own final exact-HEAD run; root will push it and confirm that run externally. M1.2 completion does not claim that Case B became complete or that Case C's citation conflict was resolved.

## M1 checklist

- [x] M0 baseline confirmed clean at root commit `5a5bcba`.
- [x] M1 implementation plan created outside the installable Skill.
- [x] Local work branch created: `codex/m1-paper-calibration`.
- [x] Adaptive research brief and query-plan contract implemented.
- [x] Verified 15–20-paper candidate-pool workflow implemented.
- [x] Eight-paper round-one evidence map and equivalent text fallback implemented.
- [x] Visible feedback delta and changed second-round search plan implemented.
- [x] Five-to-six-paper round-two output and disposition log implemented, with an honest incomplete stop when fewer than five papers have sufficient evidence.
- [x] Offline validator and adversarial fixtures pass.
- [x] Fresh-context real-search forward tests pass with current authoritative citation checks.
- [x] Standard Skill validation and final M1 scope audit pass.

## M1 result

Status: `COMPLETE`

Validated on `2026-08-04` with:

- standard Skill validator: exit `0`, `Skill is valid!`;
- M1 validator tests: 38 passed;
- adversarial fixture replay: all five exit/status pairs matched the frozen record;
- packaging audit: 106-line root Skill, zero missing or unlinked references, zero unresolved template markers;
- fresh-context Case A: 18 verified/deduplicated round-two candidates and six default recommendations;
- fresh-context Case B: 16 verified/deduplicated candidates, only three with sufficient basis, correctly stopped as `evidence_incomplete` / `WAITING_FOR_EVIDENCE_DECISION`;
- fresh-context Case C: live citation conflict blocked with `recommendation_eligible: false`.

Evidence is recorded under `evals/m1/`, including preserved failed runs and independent audits. M1 completion means the paper-calibration workflow and its stop behavior passed; it does not claim that incomplete Case B evidence became complete, that any experiment or simulation was run, or that M2 began.

## M0 checklist

- [x] D-drive project root created.
- [x] Local Git repository initialized on `main`.
- [x] Standard Skill scaffold generated.
- [x] Repository governance and product specification reviewed.
- [x] Thin root router and four core protocol references completed.
- [x] Standard Skill validation passed in UTF-8 mode: `Skill is valid!`.
- [x] Root references, placeholder count, and Skill length checks passed.
- [x] Initialization baseline prepared for one local root commit.

## Later milestones

- M2: `M2.1 COMPLETE; M2.1.1 COMPLETE`
- M3: `CLOSED`
- M4: `M4.0 PRE_DISPATCH_FAILED_PRESERVED; M4.1 PREPARATION_ONLY; FRESH_TASKS_AUTHORIZED_FALSE`
- M5: `NOT_STARTED`

## External state

- Git remote: `https://github.com/zxy19960316/engineering-research-copilot.git`
- Active local branch: `codex/m4-cross-engineering-forward-evaluation-m4.1-preparation`
- External APIs/services configured: none
- RRC integration: not started
- Platform integration: not required for the local Skill competition track

## M0 result

Status: `COMPLETE`

Validated with:

```powershell
python -X utf8 C:\Users\94310\.codex\skills\.system\skill-creator\scripts\quick_validate.py D:\engineering-research-copilot\skills\engineering-research-copilot
```

The first validator attempt without UTF-8 mode did not reach Skill validation because the Windows GBK default could not decode Chinese trigger text. No Skill content was weakened; the same validator passed under Python UTF-8 mode.
