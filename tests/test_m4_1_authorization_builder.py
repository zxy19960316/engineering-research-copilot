from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
AUTHORIZATION_ROOT = REPO_ROOT / "evals" / "m4" / "authorization"
M4_1_ROOT = AUTHORIZATION_ROOT / "m4.1"
sys.path.insert(0, str(AUTHORIZATION_ROOT))

import build_m4_1_authorization as build  # noqa: E402


REVIEW_PATH = M4_1_ROOT / "gate-iv-review.json"
AUTHORIZATION_PATH = M4_1_ROOT / "execution-authorization.json"
CONTROL_PATH = M4_1_ROOT / "execution-control.json"


class M41AuthorizationBuilderContractTests(unittest.TestCase):
    def test_build_artifacts_excludes_independent_review_and_is_byte_stable(self) -> None:
        review_before = REVIEW_PATH.read_bytes()
        artifacts = build.build_artifacts(REPO_ROOT)
        self.assertEqual(set(artifacts), {AUTHORIZATION_PATH, CONTROL_PATH})
        self.assertEqual(artifacts[AUTHORIZATION_PATH], AUTHORIZATION_PATH.read_bytes())
        self.assertEqual(artifacts[CONTROL_PATH], CONTROL_PATH.read_bytes())
        self.assertEqual(REVIEW_PATH.read_bytes(), review_before)

    def test_schemas_are_closed_and_match_exact_root_fields(self) -> None:
        pairs = (
            (
                M4_1_ROOT / "execution-authorization.schema.json",
                build.AUTHORIZATION_KEYS,
            ),
            (
                M4_1_ROOT / "execution-control.schema.json",
                build.CONTROL_KEYS,
            ),
        )
        for path, expected_keys in pairs:
            schema = json.loads(path.read_text(encoding="utf-8"))
            self.assertFalse(schema["additionalProperties"])
            self.assertEqual(set(schema["required"]), expected_keys)
            self.assertEqual(set(schema["properties"]), expected_keys)

    def test_authorization_is_new_exact_and_unconsumed(self) -> None:
        authorization = json.loads(AUTHORIZATION_PATH.read_text(encoding="utf-8"))
        preparation = json.loads(build.PREPARATION_PATH.read_text(encoding="utf-8"))
        old = json.loads(build.M4_0_AUTHORIZATION_PATH.read_text(encoding="utf-8"))

        self.assertEqual(authorization["revision"], "M4.1")
        self.assertEqual(authorization["status"], "AUTHORIZED_UNCONSUMED")
        self.assertEqual(authorization["model_binding"]["exact_model_id"], "gpt-5.6-sol")
        self.assertEqual(authorization["model_binding"]["reasoning_effort"], "max")
        self.assertEqual(authorization["prelaunch_counters"], build.ZERO_COUNTERS)
        self.assertEqual(
            authorization["authority"]["authorized_task_ids"],
            [task["task_id"] for task in preparation["tasks"]],
        )
        self.assertEqual(authorization["authority"]["authorized_task_count"], 60)
        self.assertEqual(authorization["authority"]["authorized_batch_count"], 6)
        self.assertEqual(authorization["authority"]["fresh_contexts_authorized"], 60)
        self.assertEqual(
            authorization["authority"]["independent_finalizations_authorized"], 60
        )
        self.assertEqual(authorization["authority"]["attempts_per_task_id"], 1)
        for key in (
            "retry_authorized",
            "repair_authorized",
            "followup_message_authorized",
            "judge_execution_authorized",
            "blind_mapping_access_authorized",
            "aggregation_authorized",
            "threshold_claim_authorized",
            "closure_authorized",
        ):
            self.assertFalse(authorization["authority"][key])
        self.assertEqual(
            authorization["consumption"]["launch_claim_path"],
            "evals/m4/execution/m4.1/launch-claim.json",
        )
        self.assertEqual(authorization["consumption"]["claim_count"], 0)
        self.assertEqual(
            authorization["consumption"]["authorization_token_status"],
            "UNCONSUMED",
        )
        self.assertEqual(
            authorization["authorization_token"], build.authorization_token(authorization)
        )
        self.assertNotEqual(
            authorization["authorization_token"], old["authorization_token"]
        )

    def test_control_binds_helper_requests_and_exact_frozen_order(self) -> None:
        control = json.loads(CONTROL_PATH.read_text(encoding="utf-8"))
        preparation = json.loads(build.PREPARATION_PATH.read_text(encoding="utf-8"))

        self.assertEqual(control["revision"], "M4.1")
        self.assertEqual(control["status"], "READY_UNCONSUMED")
        self.assertEqual(control["execution_helper"]["path"], build.HELPER_RELATIVE)
        self.assertEqual(
            control["execution_helper"]["raw_sha256"],
            preparation["execution_helper"]["raw_sha256"],
        )
        self.assertEqual(
            [task["task_id"] for task in control["tasks"]],
            preparation["randomization"]["task_order"],
        )
        self.assertEqual(control["batch_order"], [
            batch["batch_id"] for batch in preparation["matrix"]["batches"]
        ])
        self.assertEqual(len(control["tasks"]), 60)
        for controlled, prepared in zip(control["tasks"], preparation["tasks"], strict=True):
            self.assertEqual(controlled["source_task_id"], prepared["source_task_id"])
            self.assertEqual(
                controlled["request_binding_sha256"],
                prepared["request_binding_sha256"],
            )
            self.assertEqual(controlled["attempt_limit"], 1)
            self.assertTrue(controlled["independent_finalization_required"])
            self.assertFalse(controlled["cross_task_result_visibility"])
            self.assertTrue(controlled["result_root"].startswith("evals/m4/results/m4.1/"))
        self.assertEqual(control["request_policy"]["model_field"], "OMITTED")
        self.assertEqual(control["request_policy"]["thinking_field"], "OMITTED")
        for key in (
            "retry",
            "repair",
            "followup_message",
            "cross_task_result_read",
            "judge_execution",
            "blind_mapping_access",
            "aggregation",
            "threshold_claim",
            "m4_closure",
        ):
            self.assertFalse(control["permissions"][key])

    def test_review_is_validated_but_never_generated(self) -> None:
        review = json.loads(REVIEW_PATH.read_text(encoding="utf-8"))
        preparation = json.loads(build.PREPARATION_PATH.read_text(encoding="utf-8"))
        build.validate_review(review, preparation)
        review["findings"] = [{"severity": "blocking"}]
        with self.assertRaisesRegex(ValueError, "review_findings_nonempty"):
            build.validate_review(review, preparation)

    def test_builder_source_has_no_task_launch_or_network_api(self) -> None:
        source = (AUTHORIZATION_ROOT / "build_m4_1_authorization.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("create_thread(", source)
        self.assertNotIn("urlopen(", source)
        self.assertNotIn("requests.", source)
        self.assertNotIn("build_review", source)


if __name__ == "__main__":
    unittest.main()
