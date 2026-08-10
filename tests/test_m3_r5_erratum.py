from __future__ import annotations

import hashlib
import json
import subprocess
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_HEAD = "1b696bce53ee0a11163bfe4f91a9a49ab3af6f49"
ERRATUM = REPO_ROOT / "evals" / "m3" / "results" / "diagnostics-r5.1" / "r5-acceptance-erratum.json"
OFFLINE_DIAGNOSTIC = REPO_ROOT / "evals" / "m3" / "results" / "diagnostics-r5.1" / "m3-f02.offline-diagnostic.json"
R5_1_TERMINAL = REPO_ROOT / "evals" / "m3" / "results" / "forward-r5.1-f02" / "terminal-manifest.json"
R5_2_TERMINAL = REPO_ROOT / "evals" / "m3" / "results" / "forward-r5.2-f02" / "terminal-manifest.json"
CLOSURE_MANIFEST = REPO_ROOT / "evals" / "m3" / "results" / "forward-r5.2-aggregate" / "m3-closure-manifest.json"
M4_2_AUTHORIZATION = REPO_ROOT / "evals" / "m4" / "authorization" / "m4.2" / "execution-authorization.json"
M4_2_CONTROL = REPO_ROOT / "evals" / "m4" / "authorization" / "m4.2" / "execution-control.json"


class M3R5ErratumTests(unittest.TestCase):
    def _blob(self, path: str) -> tuple[str, str]:
        raw = subprocess.run(
            ["git", "show", f"{EVIDENCE_HEAD}:{path}"],
            cwd=REPO_ROOT,
            capture_output=True,
            check=True,
        ).stdout
        oid = subprocess.run(
            ["git", "rev-parse", f"{EVIDENCE_HEAD}:{path}"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        ).stdout.strip()
        return oid, hashlib.sha256(raw).hexdigest()

    def test_erratum_binds_immutable_r5_evidence_without_rewriting_it(self):
        erratum = json.loads(ERRATUM.read_text(encoding="utf-8"))

        self.assertTrue(erratum["supersedes_notes_only"])
        self.assertTrue(erratum["preserves_historical_evidence"])
        self.assertEqual(erratum["status"], "BLOCKED_NOT_ACCEPTED")
        self.assertEqual(erratum["m3_status"], "IN_PROGRESS")
        self.assertEqual(erratum["m4_status"], "NOT_STARTED")
        self.assertEqual(
            set(erratum["accepted_fresh_cases"]),
            {"m3-f01", "m3-f03", "m3-f04", "m3-f05"},
        )
        self.assertEqual(erratum["failed_fresh_case"]["case_id"], "m3-f02")

        references = [erratum["historical_consumed_manifest"]]
        for case in erratum["accepted_fresh_cases"].values():
            references.extend(
                {"path": value[0], "git_blob_oid": value[1], "raw_sha256": value[2]}
                for value in case.values()
            )
        failed = erratum["failed_fresh_case"]
        references.extend(
            {"path": failed[key][0], "git_blob_oid": failed[key][1], "raw_sha256": failed[key][2]}
            for key in ("transaction", "composer_receipt", "model_final")
        )
        for reference in references:
            oid, raw_sha256 = self._blob(reference["path"])
            self.assertEqual(reference["git_blob_oid"], oid)
            self.assertEqual(reference["raw_sha256"], raw_sha256)

        diff = subprocess.run(
            ["git", "diff", EVIDENCE_HEAD, "--", "evals/m3/results/forward-r5"],
            cwd=REPO_ROOT,
            capture_output=True,
            check=True,
        ).stdout
        self.assertEqual(diff, b"")

    def test_replace_f02_only_policy_is_frozen_but_not_authorized_to_run(self):
        erratum = json.loads(ERRATUM.read_text(encoding="utf-8"))
        policy = erratum["supersession_policy"]

        self.assertEqual(policy["policy"], "replace_f02_only")
        self.assertTrue(policy["frozen"])
        self.assertEqual(
            policy["reusable_immutable_cases"],
            ["m3-f01", "m3-f03", "m3-f04", "m3-f05"],
        )
        self.assertEqual(policy["replacement_case"], "m3-f02")
        self.assertEqual(policy["replacement_revision"], "r5.1-f02")
        self.assertEqual(
            policy["replacement_result_root"],
            "evals/m3/results/forward-r5.1-f02",
        )
        self.assertTrue(policy["same_task_retry_forbidden"])
        self.assertTrue(policy["same_output_path_retry_forbidden"])
        self.assertTrue(policy["cross_revision_aggregate_requires_hash_bound_cross_validation"])
        self.assertFalse(policy["new_fresh_run_authorized"])

        diagnostic = json.loads(OFFLINE_DIAGNOSTIC.read_text(encoding="utf-8"))
        self.assertEqual(diagnostic["evidence_class"], "offline_diagnostic")
        self.assertEqual(diagnostic["retry_count"], 0)
        self.assertFalse(diagnostic["composed_output_created"])

    def test_status_top_preserves_terminal_history_during_m4_2_one_shot_authorization(self):
        text = (REPO_ROOT / "STATUS.md").read_text(encoding="utf-8")
        current = text.split("## M3 checklist", 1)[0]
        issued = M4_2_AUTHORIZATION.exists() and M4_2_CONTROL.exists()

        if issued:
            self.assertIn(
                "Active revision: `M4.2 ONE_SHOT_AUTHORIZATION; "
                "M4_2_AUTHORIZED_UNCONSUMED_NOT_CLAIMED_NOT_EXECUTED; "
                "decision=APPROVE_M4_2_SEPARATE_ONE_SHOT_CLAIM_AND_EXECUTION_"
                "WORK_PACKAGE_ONLY; fresh_execution_authorized=true`",
                current,
            )
        else:
            self.assertIn(
                "Active revision: `M4.2 ONE_SHOT_AUTHORIZATION_CANDIDATE; "
                "M4_2_ONE_SHOT_AUTHORIZATION_CANDIDATE_READY_NOT_ISSUED; "
                "decision=PENDING_CANDIDATE_EXACT_HEAD_PUSH_AND_PR_CI; "
                "fresh_execution_authorized=false`",
                current,
            )
        self.assertIn(f"Historical r5 evidence HEAD: `{EVIDENCE_HEAD}`", current)
        self.assertIn(
            "Gate 3 accepted evidence baseline HEAD: "
            "`ea8a7bbb8b365aded89f9ddb5c784f6e95a51d3d`",
            current,
        )
        self.assertIn(
            "Gate 3 accepted evidence baseline exact-HEAD CI: `PASSED` "
            "(GitHub Actions run `31192712555`)",
            current,
        )
        for preserved_status in (
            "M3_CLOSED",
            "M4_0_PRE_DISPATCH_FAILED_PRESERVED",
            "M4_1_STOPPED_PROTOCOL_FAILURE_PRESERVED",
            "M4_1_AUTHORIZATION_CONSUMED",
            "M4_1_TASKS_NOT_DISPATCHED",
            "M4_2_PREPARED_NOT_AUTHORIZED",
            "M4_2_WINDOWS_LIFECYCLE_REPAIR_ACCEPTED",
            "M4_2_GATE_IV_A_REVIEW_PASSED_NOT_AUTHORIZED",
            "M4_2_GATE_IV_B_PROTOCOL_PROOF_PASSED_NOT_AUTHORIZED",
            "M4_2_AUTHORIZATION_PREPARATION_PASSED_NOT_AUTHORIZED",
            "M4_FRESH_RESULTS_NOT_RUN",
        ):
            self.assertIn(preserved_status, current)
        self.assertIn("Historical r5 status: `BLOCKED_NOT_ACCEPTED`", current)
        self.assertIn("Historical accepted fresh cases: `F01, F03, F04, F05`", current)
        self.assertIn("Historical failed fresh case: `F02`", current)
        self.assertIn(
            "r5.2-f02 replacement: `F02 ACCEPTED; SELECTED_FOR_AGGREGATE`",
            current,
        )
        self.assertIn(
            "Selected aggregate revisions: "
            "`F01=r5; F02=r5.2-f02; F03=r5; F04=r5; F05=r5`",
            current,
        )
        self.assertIn(
            "Selected aggregate counters: "
            "`tasks=5; finalizations=5; composer=4; validator=5; "
            "accepted=5; failed=0; retry=0`",
            current,
        )
        self.assertIn(
            "Preserved historical-attempt counters: "
            "`tasks=7; finalizations=7; composer=6; validator=5; "
            "accepted=5; failed=2; retry=0`",
            current,
        )
        self.assertIn(
            "Aggregate candidate exact-HEAD CI: `PASSED` on HEAD "
            "`3be04218b038bac7a55da10a553a5ce05be4652c` "
            "(GitHub Actions run `31233356741`)",
            current,
        )
        self.assertIn("Historical immutable-r5 exact-HEAD CI: `FAILED`", current)
        self.assertIn("M3: `CLOSED`", current)
        self.assertIn("M4.1 continuation or rerun is forbidden", current)
        self.assertIn(
            "M4 Gate IV authorization token status: `CONSUMED; claim_count=1; "
            "terminal for M4.0`",
            current,
        )
        self.assertIn(
            "M4.0 fresh result state: `NOT_RUN; result_roots=0; "
            "results_manifest=ABSENT`",
            current,
        )
        self.assertIn(
            "compatibility-fix exact-HEAD CI=PASSED on "
            "f48ab8d7e835e9a57e65b75458faa786d696316d "
            "(GitHub Actions run 31246286753)",
            current,
        )
        self.assertIn(
            "M4.1 current terminal state: "
            "`M4_1_STOPPED_PROTOCOL_FAILURE_PRESERVED; "
            "M4_1_AUTHORIZATION_CONSUMED; M4_1_TASKS_NOT_DISPATCHED; "
            "M4_2_REQUIRED`",
            current,
        )
        self.assertIn(
            "M4.1 launch claim: `PRESENT; "
            "claim_id=32e0df57-a8d2-5c19-9ffc-da69997686e8; "
            "sha256=c16a2e53aa2e9215e2325464d547356afdb73897bfc7d29605e0105b9987b3c6; "
            "claimed_at_utc=2026-08-08T14:28:37Z; claim_count=1`",
            current,
        )
        self.assertIn(
            "M4.1 execution terminal: `PRESENT; "
            "terminal_state=STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE; "
            "sha256=7305d71ba94cd209f5bb0cb2c977db3bb157d95b907f8f59df9133c192f4d66e; "
            "recorded_at_utc=2026-08-08T14:28:37Z`",
            current,
        )
        self.assertIn(
            "M4.1 consumed-state exact-HEAD CI: `FAILED` on HEAD "
            "`80b54697c3e27a5dad0a24d5318ce26c8fe46141` "
            "(GitHub Actions run `31262297707`",
            current,
        )
        self.assertIn("M4.2 state: `M4_2_PREPARED_NOT_AUTHORIZED", current)
        self.assertIn(
            "M4.2 Gate IV-A r1 terminal evidence: "
            "`head=ac6cc70714a90f73b4de09eaf0e521e699296890; "
            "tree=3ee67b0c5ffa53fc2676381e9ab9b79499e2cf6e; "
            "pull_request=4; "
            "artifact=evals/m4/authorization/m4.2/gate-iv-a-review.json; "
            "artifact_blob=9af5710dfba68ee5038f0c9e832591181d41835e; "
            "artifact_sha256=cd68d10a140606d4f7dd0ee6d09ebe49c1b4566aa54345cfe91728eaac06b373; "
            "findings=3; reviewer_side_effects=[]; decision=BLOCKED; "
            "status=BLOCKED; immutable=true`",
            current,
        )
        self.assertIn(
            "M4.2 Windows lifecycle repair exact HEAD: "
            "`44d1004da1cbb2681ee0d423d1748f98fbaa13e4; "
            "tree=9845b1a05e23fa84e55ad20399ec1b86bc861e44; "
            "parent=941602180c75c4ae16edfc927f6c39b8420fb45c; "
            "pull_request=5`",
            current,
        )
        self.assertIn(
            "M4.2 Windows lifecycle repair push exact-HEAD CI: `ALL_GREEN; "
            "run=31354780589; "
            "head=44d1004da1cbb2681ee0d423d1748f98fbaa13e4; jobs=7/7; "
            "raw_log_bytes=685943; "
            "raw_log_sha256=6b8bd910c89b5f17510c542f3a2418e20ded2c547d5cef69ff78aa32f78be29d; "
            "markers=FAIL:0,FAILED (:0,Traceback:0,##[error]:0`",
            current,
        )
        self.assertIn(
            "M4.2 Windows lifecycle repair PR exact-HEAD CI: `ALL_GREEN; "
            "run=31354802277; "
            "head=44d1004da1cbb2681ee0d423d1748f98fbaa13e4; jobs=7/7; "
            "raw_log_bytes=695517; "
            "raw_log_sha256=5f63879f748cecfc0ca8ddc4ac3b9686fb83aa1fd5683468f22b2e88b0a5a7f2; "
            "markers=FAIL:0,FAILED (:0,Traceback:0,##[error]:0`",
            current,
        )
        self.assertIn(
            "M4.2 Gate IV-A r2 reviewed repair: "
            "`head=44d1004da1cbb2681ee0d423d1748f98fbaa13e4; "
            "tree=9845b1a05e23fa84e55ad20399ec1b86bc861e44; "
            ".gitattributes=REVIEWED; repair_artifacts=REVIEWED`",
            current,
        )
        self.assertIn(
            "M4.2 Gate IV-A r2 artifact: "
            "`evals/m4/authorization/m4.2/gate-iv-a-review-r2.json; "
            "findings=[]; reviewer_side_effects=[]; "
            "decision=APPROVE_M4_2_GATE_IV_B_PROTOCOL_PROOF_ONLY; "
            "status=M4_2_GATE_IV_A_REVIEW_PASSED_NOT_AUTHORIZED`",
            current,
        )
        self.assertIn(
            "M4.2 Gate IV-A r2 delivery: `VERIFIED_TRUE_GREEN; "
            "accepted_review_head=caf2f579556d6df0dff88af246e51ed3ae6438b9; "
            "push_run=31359218501; push_jobs=9/9; "
            "push_raw_log_bytes=1217964; "
            "push_raw_log_sha256=933554d4e16e839f6f8de3cc7ed52ae7a4abf7e894458a699d869b8621985a60; "
            "pull_request_run=31359221182; pull_request_jobs=9/9; "
            "pull_request_raw_log_bytes=1231978; "
            "pull_request_raw_log_sha256=0efaf0ba5135fea86f4c0d32788c02e5b2555c392802ee3fe11f59daaf65ae0d; "
            "markers=FAIL:0,FAILED (:0,Traceback:0,##[error]:0`",
            current,
        )
        self.assertIn(
            "M4.2 Gate IV-A r2 review evidence: `PASSED_NOT_AUTHORIZED; "
            "reviewed_repair_head=44d1004da1cbb2681ee0d423d1748f98fbaa13e4; "
            "focused_review=30/30; Windows_current_lifecycle=634/634; "
            "Linux_current_lifecycle=634/634; repaired_baseline=21/21; "
            "request_bindings=60/60; Windows_PowerShell_5_1=60/60; "
            "GitHub_Ubuntu_PowerShell_7=60/60; "
            "M4.1_terminal=M4_1_STOPPED_PROTOCOL_FAILURE_PRESERVED; "
            "results=NOT_RUN; forbidden_path_count=0; findings=[]; "
            "reviewer_side_effects=[]; read_only=true; repeatable=true`",
            current,
        )
        self.assertIn(
            "M4.2 Gate IV-A r2 closure exact-HEAD CI: `PASSED; "
            "closure_head=988b4332504549df2038f51532175effd696a445; "
            "push_run=31359667359; pull_request_run=31359670122; "
            "both_success=true`",
            current,
        )
        self.assertIn(
            "M4.2 Gate IV-B proof baseline: "
            "`head=988b4332504549df2038f51532175effd696a445; "
            "tree=38b1aeacd54b5e5a9ac115be1816206a7a3f8a4f; "
            "r2_artifact_blob=734918bd5de16ea6f7595e206c3cd313ba041fa7; "
            "r2_decision=APPROVE_M4_2_GATE_IV_B_PROTOCOL_PROOF_ONLY`",
            current,
        )
        self.assertIn(
            "M4.2 Gate IV-B first B3 CI evidence: `PRESERVED_NOT_ACCEPTED; "
            "head=cf1dbc0c60a3dc5424fdf88da9e4deaa5a8bd1de; "
            "push_run=31369859743; pull_request_run=31369911612; "
            "Gate_IV_B_Ubuntu_and_Windows_jobs=PASSED; "
            "Windows_r2_lifecycle=FAILED; "
            "failed_test=tests.test_replay_m2_offline_results."
            "M2OfflineResultsReplayTests.test_fixture_builder_is_byte_deterministic; "
            "root_cause=isolated_r2_worktree_forced_LF_while_Windows_builder_"
            "materialized_CRLF; no authorization or execution side effect`",
            current,
        )
        self.assertIn(
            "M4.2 Gate IV-B B3 CI repair: "
            "`head=249e28d07d5e52cd9cec9b7e110f6159e6046222; "
            "parent=cf1dbc0c60a3dc5424fdf88da9e4deaa5a8bd1de; "
            "scope=.github/workflows/m1-validation.yml,"
            "tests/test_m4_2_gate_iv_b_protocol_proof.py; "
            "r2_worktree_inherits_runner_platform_EOL; "
            "M4 byte-sensitive paths remain LF-pinned by .gitattributes; "
            "no test weakened`",
            current,
        )
        self.assertIn(
            "M4.2 Gate IV-B delivery: `VERIFIED_TRUE_GREEN; "
            "accepted_proof_head=249e28d07d5e52cd9cec9b7e110f6159e6046222; "
            "push_run=31370941146; push_jobs=11/11; "
            "push_raw_log_bytes=1362037; "
            "push_raw_log_sha256=5a0984715457dbdea9217a57239eedac707fb6407e2cb274f61afebdbe5338bd; "
            "pull_request_run=31370945548; pull_request_jobs=11/11; "
            "pull_request_raw_log_bytes=1378502; "
            "pull_request_raw_log_sha256=6e483e7d9a897cb8dfc2254b1217089ad2213f30d8f9bc3ecfbbd05124faa471; "
            "markers=FAIL:0,FAILED (:0,Traceback:0,##[error]:0`",
            current,
        )
        self.assertIn(
            "M4.2 Gate IV-B decision: "
            "`APPROVE_M4_2_AUTHORIZATION_PREPARATION_ONLY; "
            "status=M4_2_GATE_IV_B_PROTOCOL_PROOF_PASSED_NOT_AUTHORIZED; "
            "this is not execution authorization`",
            current,
        )
        self.assertIn(
            "M4.2 Gate IV-B negative authority: "
            "`authorization_artifact=ABSENT; execution_control=ABSENT; "
            "authorization_token=NOT_ISSUED; launch_claim=ABSENT; "
            "result_root=ABSENT; authorized_tasks=0; created_contexts=0; "
            "dispatched_tasks=0; finalizations=0; results_observed=0; "
            "judge_scores=0; retries=0; repairs=0; raw_model_finals=0; "
            "aggregation_calls=0; acceptance_claims=0; "
            "unauthorized_side_effects=0`",
            current,
        )
        self.assertIn(
            "M4.2 authorization-preparation artifact: "
            "`evals/m4/authorization/m4.2/authorization-preparation.json; "
            "preparation_kind=AUTHORIZATION_SCHEMA_AND_PROJECTION_ONLY; "
            "status=M4_2_AUTHORIZATION_PREPARATION_PASSED_NOT_AUTHORIZED`",
            current,
        )
        self.assertIn(
            "M4.2 authorization-preparation superseded local closure attempt: "
            "`PRESERVED_NOT_PUSHED; "
            "closure_head=a3a2b14526358f8b359cc6c4b442884f0b851269; "
            "failed_test=tests.test_m4_2_authorization_preparation."
            "M42AuthorizationPreparationMutationTests."
            "test_rejects_final_state_without_valid_candidate_delivery; "
            "cause=final_values_reassigned_to_already_final_artifact_without_mutation; "
            "restore_head=86b5afc1631fb8c80ab753832abcfbb375c4366b; "
            "repaired_candidate_head=44e6cd611ce67f362015c431d3c1d6ba069ad345; "
            "no authorization or execution side effect`",
            current,
        )
        self.assertIn(
            "M4.2 authorization-preparation local gates: `PASSED; "
            "focused=48/48; current_lifecycle=682/682; "
            "exact_Gate_IV_B_replay=27/27; "
            "local_Windows_PowerShell_5_1=60/60; audit_results=NOT_RUN; "
            "preparation_auditor=BYTE_IDENTICAL_TWICE; "
            "Gate_IV_B_auditor=BYTE_IDENTICAL_TWICE; "
            "forbidden_path_count=0; working_tree=clean`",
            current,
        )
        self.assertIn(
            "M4.2 authorization-preparation delivery: `VERIFIED_TRUE_GREEN; "
            "accepted_candidate_head=44e6cd611ce67f362015c431d3c1d6ba069ad345; "
            "push_run=31379784953; push_jobs=13/13; "
            "push_raw_log_bytes=2026196; "
            "push_raw_log_sha256=4753351484c5f58defaf681b8568b768f07025f01394a2a6ed817b69212b7d51; "
            "pull_request_run=31379789763; pull_request_jobs=13/13; "
            "pull_request_raw_log_bytes=2045877; "
            "pull_request_raw_log_sha256=f1ad38ee2316c0147a5ee742bf634697457aa25cb9f7ff8f06522ba35bf80449; "
            "markers=FAIL:0,FAILED (:0,Traceback:0,##[error]:0`",
            current,
        )
        self.assertIn(
            "M4.2 authorization-preparation decision: "
            "`APPROVE_M4_2_SEPARATE_AUTHORIZATION_WORK_PACKAGE_ONLY; "
            "status=M4_2_AUTHORIZATION_PREPARATION_PASSED_NOT_AUTHORIZED; "
            "this is not execution authorization`",
            current,
        )
        self.assertIn(
            "M4.2 authorization-preparation negative authority: "
            "`authorization artifact=ABSENT; execution control=ABSENT; "
            "authorization token=NOT_ISSUED; claim=ABSENT; "
            "execution_root=ABSENT; result_root=ABSENT; authorized_tasks=0; "
            "created_contexts=0; dispatched_tasks=0; finalizations=0; "
            "results_observed=0; judge_scores=0; retries=0; repairs=0; "
            "raw_model_finals=0; aggregation_calls=0; acceptance_claims=0; "
            "unauthorized_side_effects=0`",
            current,
        )
        false_green_runs = {
            "31311637459": (
                "be6039e7d2a682b2e001ee12dff5c1db5743b2ed",
                "93240229660",
            ),
            "31313212880": (
                "dffccf5d2fecc295e3efc7d7368b36b7ff1bf6b7",
                "93244187473",
            ),
        }
        for run_id, (head, windows_job) in false_green_runs.items():
            with self.subTest(run_id=run_id):
                matching_lines = [
                    line for line in current.splitlines() if run_id in line
                ]
                self.assertEqual(len(matching_lines), 1)
                record = matching_lines[0]
                self.assertIn(head, record)
                self.assertIn(f"windows_job={windows_job}", record)
                self.assertIn(
                    "GITHUB_CONCLUSION_SUCCESS_BUT_WINDOWS_TEST_FAILED", record
                )
                self.assertIn("NOT_ACCEPTED", record)
                self.assertIn("FALSE_GREEN", record)
                self.assertIn(
                    "failed_test=tests.test_m4_2_preparation."
                    "M42PreparationAuditTests."
                    "test_rejects_raw_bound_input_eol_drift",
                    record,
                )
                self.assertNotIn("exact-HEAD CI: `PASSED`", record)
        self.assertNotIn("M4.2 preparation exact-HEAD CI: `PASSED`", current)
        self.assertIn(
            "M4.2 accepted exact-HEAD CI: `TRUE_GREEN_IMPLEMENTATION; "
            "CI_INTEGRITY_REPAIR_CLOSED; "
            "head=242490a5d0d4e9bc52f21263d8d6780830ab1c8f; "
            "run=31316090614; event=push; validate_job=93251454657; "
            "ubuntu_m4_2_job=93251454695; windows_m4_2_job=93251454692; "
            "all_jobs=7/7; all_raw_logs_verified=true; windows_unittest=OK; "
            "errors=[]; forbidden_path_count=0; side_effects=[]; "
            "PowerShell_5_1_request_bindings=60/60`",
            current,
        )
        self.assertIn(
            "M4.2 companion PR exact-HEAD CI: `TRUE_GREEN_IMPLEMENTATION; "
            "head=242490a5d0d4e9bc52f21263d8d6780830ab1c8f; "
            "run=31316093185; event=pull_request; "
            "validate_job=93251461042; ubuntu_m4_2_job=93251461072; "
            "windows_m4_2_job=93251461064; all_jobs=7/7; "
            "all_raw_logs_verified=true`",
            current,
        )
        self.assertNotIn("CI_INTEGRITY_REPAIR_REQUIRED", current)
        self.assertNotIn("branch remains local and unpushed", current)
        self.assertIn(
            "M4.2 predecessor closure baseline: "
            "`e6ae2be7695ce1d2613dcd39e379ff458c1b60fe` "
            "(GitHub Actions run `31301984766`; `success`)",
            current,
        )
        self.assertIn(
            "M4.2 source preparation: "
            "`evals/m4/revisions/m4.1/preparation-manifest.json; "
            "sha256=d66ad9d513d8e64307f9a1553242d9b7d840ea5432d084b06d86707c1b4c2b61; "
            "source_exact_head=fedc5cdeebd7a2943afeb6767d39841305c55444; "
            "source_ci_run=31248424046`",
            current,
        )
        self.assertIn(
            "M4.2 task identity state: `60 new task IDs; 0 reused; "
            "blind IDs=M4-J121..M4-J180; 6 new batch IDs; "
            "direct_lineage=M4.1; root_lineage=M4.0`",
            current,
        )
        self.assertIn(
            "M4.2 authority state: `fresh_execution=false; tasks=false; "
            "result_writes=false; retry=false; repair=false; "
            "authorization_artifact=null; "
            "model_binding_status=UNBOUND_UNTIL_SEPARATE_AUTHORIZATION`",
            current,
        )
        self.assertIn(
            "M4.2 preparation counters: `authorized_tasks=0; "
            "created_contexts=0; dispatched_tasks=0; finalizations=0; "
            "results_observed=0; judge_scores=0; retries=0; repairs=0; "
            "unauthorized_side_effects=0`",
            current,
        )
        self.assertIn(
            "M4.2 absent artifacts: `M4.1 result_root=ABSENT; "
            "M4.2 authorization=ABSENT; execution=ABSENT; "
            "result_root=ABSENT; results_manifest=ABSENT`",
            current,
        )
        self.assertIn(
            "M4.2 later gates: `Gate IV-A r1=BLOCKED_PRESERVED; "
            "Windows_lifecycle_repair=ACCEPTED; "
            "Gate IV-A r2=PASSED_NOT_AUTHORIZED; "
            "Gate IV-B protocol proof=PASSED_NOT_AUTHORIZED; "
            "authorization preparation=PASSED_NOT_AUTHORIZED; "
            "separate one-shot authorization=PERMITTED_NOT_STARTED; "
            "authorization=ABSENT; execution=ABSENT; claim=ABSENT; "
            "tasks=0; results=0; "
            "judge=NOT_RUN; aggregation=NOT_RUN; closure=NOT_RUN; "
            "M5=NOT_STARTED`",
            current,
        )
        self.assertIn(
            "M4.1 predecessor terminal baseline: "
            "`f48ab8d7e835e9a57e65b75458faa786d696316d` "
            "(GitHub Actions run `31246286753`; `success`)",
            current,
        )
        self.assertIn(
            "M4.1 task identity state: `60 new task IDs; 0 reused; "
            "blind IDs=M4-J061..M4-J120; 6 new batch IDs`",
            current,
        )
        self.assertIn(
            "M4.1 historical one-shot authorization: `CONSUMED by the sole claim; "
            "no authority remains for continuation or rerun`",
            current,
        )
        self.assertIn(
            "M4.1 historical pre-claim preparation counters: `authorized=0; "
            "contexts=0; "
            "dispatched=0; finalizations=0; results=0; judge_scores=0; "
            "retries=0; repairs=0; unauthorized_side_effects=0`",
            current,
        )
        self.assertIn(
            "M4.1 result state: `NOT_RUN; launch_claim=PRESENT_AND_CONSUMED; "
            "execution_terminal=PRESENT; result_roots=0; results_manifest=ABSENT`",
            current,
        )
        self.assertIn(
            "M4.1 preparation exact-HEAD CI: `PASSED` on HEAD "
            "`fedc5cdeebd7a2943afeb6767d39841305c55444` "
            "(GitHub Actions run `31248424046`; validate job `93080747550` "
            "success; ubuntu job `93080747506` success; windows job "
            "`93080747504` success)",
            current,
        )
        self.assertIn(
            "M4.1 Gate IV independent review: `PASSED; findings=0; "
            "decision=AUTHORIZE_M4_1_GATE_IV_ONE_SHOT_MATRIX`",
            current,
        )
        self.assertIn(
            "M4.1 Gate IV authorization token status: "
            "`CONSUMED; claim_count=1; SAME_REVISION_CONTINUATION_FORBIDDEN`",
            current,
        )
        self.assertRegex(
            current,
            r"M4\.1 terminal-closure CI transition: `old consumed-state exact-HEAD "
            r"run 31262297707 preserved as FAILED; lifecycle-aware replacement "
            r"run (?:PENDING|[0-9]+ PASSED)`",
        )
        self.assertIn(
            "M4.1 authorization and fresh execution: `AUTHORIZATION_CONSUMED; "
            "STOPPED_BEFORE_DISPATCH; launch_claim=PRESENT; terminal=PRESENT; "
            "result_roots=0; results_manifest=ABSENT`",
            current,
        )
        self.assertIn(
            "M4.1 Gate IV-A execution-protocol exact-HEAD CI: `PASSED` on HEAD "
            "`bb1b8a5e4bab46d625c637d564d8132dc69a21ab` "
            "(GitHub Actions run `31255966197`; validate job `93099235968` "
            "success; ubuntu job `93099235987` success; windows job "
            "`93099235994` success)",
            current,
        )
        self.assertIn(
            "M4.1 historical Gate IV-B readiness audit: "
            "`READY_FOR_ATOMIC_CLAIM; "
            "focused=18/18; combined=67/67; full=693/693; "
            "protocol_review=PASSED; "
            "authorization_audit=READY_UNCONSUMED; "
            "execution_audit=READY_UNCLAIMED; writer_check=DETERMINISTIC at "
            "c370a3ce21661f0dbf2cdd153b8761d8fce71f9b`",
            current,
        )
        self.assertIn(
            "M4.1 historical Gate IV-B zero state: "
            "`authorization token=UNCONSUMED; "
            "launch claim=ABSENT; terminal=ABSENT; platform observations=ABSENT; "
            "result root=ABSENT; results manifest=ABSENT; tasks=0; "
            "finalizations=0 at "
            "c370a3ce21661f0dbf2cdd153b8761d8fce71f9b`",
            current,
        )
        self.assertIn("r5.1-f02 retry: `FORBIDDEN`", current)
        self.assertIn("Gate 2: `COMPLETE; EXACT_HEAD_CI_PASSED`", current)
        self.assertIn("Gate 2 new fresh-run authorization: `false`", current)
        self.assertIn(
            "Gate 3 one-shot authorization: `CONSUMED; EXACT_HEAD_CI_PASSED`",
            current,
        )
        self.assertIn("r5.2-f02 fresh execution: `ACCEPTED; TERMINAL`", current)
        self.assertIn(
            "r5.2-f02 counters: `tasks=1; finalizations=1; composer=1; validator=1; retry=0`",
            current,
        )
        self.assertIn(
            "Gate 4: `COMPLETE; CROSS_REVISION_AGGREGATE_ACCEPTED; "
            "EXACT_HEAD_CI_PASSED`",
            current,
        )
        self.assertIn(
            "M3 final validation: `PASSED; "
            "AGGREGATE_CANDIDATE_EXACT_HEAD_CI_PASSED`",
            current,
        )
        self.assertIn(
            "M3 closure: `CLOSED; CLOSURE_AUDIT_PASSED; "
            "DELIVERY_EXACT_HEAD_CI_PASSED`",
            current,
        )
        self.assertIn("r5.1-f02 replacement task budget: `CONSUMED`", current)
        self.assertIn(
            "r5.1-f02 authorization token: `CONSUMED / TERMINAL`", current
        )
        self.assertNotIn("READY_FOR_AUTHORIZED_R5_FRESH_CONTEXTS", current)
        self.assertIn(
            "- M4: `M4.0 PRE_DISPATCH_FAILED_PRESERVED; "
            "M4.1 STOPPED_PROTOCOL_FAILURE_PRESERVED; "
            "M4.1 AUTHORIZATION_CONSUMED; M4.1 TASKS_NOT_DISPATCHED; "
            "M4.2 PREPARED_NOT_AUTHORIZED; "
            "M4.2 WINDOWS_LIFECYCLE_REPAIR_ACCEPTED; "
            "M4.2 GATE_IV_A_REVIEW_PASSED_NOT_AUTHORIZED; "
            "FRESH_RESULTS_NOT_RUN`",
            text,
        )
        self.assertIn(
            "- Active local branch: "
            "`codex/m4-cross-engineering-forward-evaluation-m4.2-gate-iv-a-r2`",
            text,
        )
        self.assertNotIn("GATE_IV_B_LAUNCH_READINESS_LOCAL_READY", text)
        if issued:
            self.assertIn(
                "M4_2_AUTHORIZED_UNCONSUMED_NOT_CLAIMED_NOT_EXECUTED", current
            )
            self.assertIn("claim_count=0", current)
        else:
            self.assertIn(
                "M4_2_ONE_SHOT_AUTHORIZATION_CANDIDATE_READY_NOT_ISSUED", current
            )
            self.assertNotIn(
                "M4_2_AUTHORIZED_UNCONSUMED_NOT_CLAIMED_NOT_EXECUTED", current
            )

        r5_1_terminal = json.loads(R5_1_TERMINAL.read_text(encoding="utf-8"))
        self.assertEqual(r5_1_terminal["status"], "terminal_not_accepted")
        self.assertFalse(r5_1_terminal["accepted"])
        self.assertFalse(r5_1_terminal["cross_revision_aggregation_authorized"])
        self.assertEqual(r5_1_terminal["m3_status"], "IN_PROGRESS")
        self.assertEqual(r5_1_terminal["m4_status"], "NOT_STARTED")

        r5_2_terminal = json.loads(R5_2_TERMINAL.read_text(encoding="utf-8"))
        self.assertEqual(r5_2_terminal["status"], "accepted")
        self.assertTrue(r5_2_terminal["accepted"])
        self.assertEqual(r5_2_terminal["gate_state"]["gate_4"], "NOT_STARTED")
        self.assertEqual(r5_2_terminal["gate_state"]["m3_closure"], "NOT_RUN")
        self.assertEqual(r5_2_terminal["gate_state"]["m4"], "NOT_STARTED")

        closure = json.loads(CLOSURE_MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(closure["milestone"], "M3")
        self.assertEqual(closure["status"], "CLOSED")
        self.assertEqual(closure["m4_status"], "NOT_STARTED")
        self.assertFalse(closure["scope_limits"]["m4_started"])


if __name__ == "__main__":
    unittest.main()
