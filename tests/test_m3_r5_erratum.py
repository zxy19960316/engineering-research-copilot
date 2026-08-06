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

    def test_status_top_reports_current_r5_blocked_state(self):
        text = (REPO_ROOT / "STATUS.md").read_text(encoding="utf-8")
        current = text.split("## M3 checklist", 1)[0]

        self.assertIn("Active revision: `M3.1.1 r5`", current)
        self.assertIn(f"Evidence HEAD: `{EVIDENCE_HEAD}`", current)
        self.assertIn("Status: `BLOCKED_NOT_ACCEPTED`", current)
        self.assertIn("Accepted fresh cases: `F01, F03, F04, F05`", current)
        self.assertIn("Failed fresh case: `F02`", current)
        self.assertIn("Exact-HEAD CI: `FAILED`", current)
        self.assertIn("M3: `IN_PROGRESS`", current)
        self.assertIn("M4: `NOT_STARTED`", current)
        self.assertNotIn("READY_FOR_AUTHORIZED_R5_FRESH_CONTEXTS", current)


if __name__ == "__main__":
    unittest.main()
