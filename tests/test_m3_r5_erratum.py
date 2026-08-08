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

    def test_status_top_preserves_terminal_history_during_m4_1_launch_readiness(self):
        text = (REPO_ROOT / "STATUS.md").read_text(encoding="utf-8")
        current = text.split("## M3 checklist", 1)[0]

        self.assertIn(
            "Active revision: `M4.1 GATE_IV_B_LAUNCH_READINESS_LOCAL_READY`",
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
        self.assertIn(
            "Status: `M3_CLOSED; M4_0_PRE_DISPATCH_FAILED_PRESERVED; "
            "M4_1_GATE_IV_A_EXACT_HEAD_CI_PASSED; "
            "M4_1_GATE_IV_B_LAUNCH_READINESS_LOCAL_READY; "
            "M4_1_AUTHORIZATION_UNCONSUMED; M4_FRESH_RESULTS_NOT_RUN`",
            current,
        )
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
        self.assertIn(
            "M4: `M4_1_GATE_IV_B_LAUNCH_READINESS_LOCAL_READY; "
            "AUTHORIZATION_UNCONSUMED`",
            current,
        )
        self.assertIn(
            "M4 fresh tasks authorized: `true for M4.1 only; "
            "execution-protocol freeze precedes claim; M4.0 authorization consumed "
            "and terminal; M4.1 execution remains NOT_RUN`",
            current,
        )
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
            "M4.1 successor state: `GATE_IV_AUTHORIZED_UNCONSUMED; "
            "OFFLINE_PREPARATION_COMPLETE`",
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
            "M4.1 fresh execution authorized: `true; one-shot 60-task matrix only; "
            "launch claim absent; execution NOT_RUN`",
            current,
        )
        self.assertIn(
            "M4.1 preparation counters: `authorized=0; contexts=0; "
            "dispatched=0; finalizations=0; results=0; judge_scores=0; "
            "retries=0; repairs=0; unauthorized_side_effects=0`",
            current,
        )
        self.assertIn(
            "M4.1 result state: `NOT_RUN; launch_claim=ABSENT; "
            "result_roots=0; results_manifest=ABSENT`",
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
            "`AUTHORIZED_UNCONSUMED; claim_count=0`",
            current,
        )
        self.assertIn(
            "M4.1 Gate IV exact-HEAD CI: `NOT_RUN; this authorization "
            "commit does not pre-claim success`",
            current,
        )
        self.assertIn(
            "M4.1 authorization and fresh execution: `AUTHORIZED_UNCONSUMED; "
            "execution=NOT_RUN; launch_claim=ABSENT; result_roots=0; "
            "results_manifest=ABSENT`",
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
            "M4.1 Gate IV-B readiness audit: `READY_FOR_ATOMIC_CLAIM; "
            "focused=18/18; combined=67/67; full=693/693; "
            "protocol_review=PASSED; "
            "authorization_audit=READY_UNCONSUMED; "
            "execution_audit=READY_UNCLAIMED; writer_check=DETERMINISTIC`",
            current,
        )
        self.assertIn(
            "M4.1 Gate IV-B zero state: `authorization token=UNCONSUMED; "
            "launch claim=ABSENT; terminal=ABSENT; platform observations=ABSENT; "
            "result root=ABSENT; results manifest=ABSENT; tasks=0; "
            "finalizations=0`",
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
