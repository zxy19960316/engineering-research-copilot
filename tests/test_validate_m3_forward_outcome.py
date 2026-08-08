from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "evals" / "m3"))
sys.path.insert(0, str(REPO_ROOT / "tests"))

from test_validate_m3_method_bundle import make_valid_m3_bundle  # noqa: E402
from validate_m3_forward_outcome import validate_forward_outcome  # noqa: E402


TERMINAL_CODE = "unsupported_approved_constraint_change_provenance"


def _f03_source() -> dict:
    return json.loads(
        (
            REPO_ROOT
            / "evals"
            / "m3"
            / "forward-inputs-r2"
            / "m3-f03-approved-change.bundle.json"
        ).read_text(encoding="utf-8")
    )


def _selected(source: dict) -> dict:
    selected_id = source["direction_decision"]["selected_direction_id"]
    return next(
        direction
        for direction in source["direction_portfolio"]["directions"]
        if direction["direction_id"] == selected_id
    )


def _blocked(source: dict) -> dict:
    return {
        "outcome_kind": "blocked",
        "terminal_code": TERMINAL_CODE,
        "original_resource_limits": copy.deepcopy(_selected(source)["resource_limits"]),
        "applied_constraint_changes": [],
    }


class ValidateM3ForwardOutcomeTests(unittest.TestCase):
    def assertInvalid(self, result: dict, code: str) -> None:  # noqa: N802
        self.assertEqual(result["status"], "invalid")
        self.assertIn(code, result["errors"])

    def test_non_f03_valid_bundle_is_accepted_through_method_validator(self):
        bundle = make_valid_m3_bundle()
        source = bundle["source_m2_bundle"]

        result = validate_forward_outcome(
            "m3-f01", source, {"outcome_kind": "bundle", "bundle": bundle}
        )

        self.assertEqual(result, {
            "case_id": "m3-f01",
            "status": "accepted",
            "outcome_kind": "bundle",
            "errors": [],
            "evidence_gaps": [],
            "method_bundle_validation": {
                "status": "valid",
                "errors": [],
                "evidence_gaps": [],
            },
        })

    def test_invalid_method_bundle_is_not_accepted(self):
        bundle = make_valid_m3_bundle()
        source = bundle["source_m2_bundle"]
        bundle["method_cards"] = []

        result = validate_forward_outcome(
            "m3-f01", source, {"outcome_kind": "bundle", "bundle": bundle}
        )

        self.assertInvalid(result, "method_bundle_not_valid")
        self.assertIn("empty_method_cards", result["method_bundle_validation"]["errors"])

    def test_bundle_must_embed_the_exact_supplied_m2_object(self):
        bundle = make_valid_m3_bundle()
        source = copy.deepcopy(bundle["source_m2_bundle"])
        source["fixture_mode"] = 1

        result = validate_forward_outcome(
            "m3-f01", source, {"outcome_kind": "bundle", "bundle": bundle}
        )

        self.assertInvalid(result, "outcome_source_m2_mismatch")

    def test_f03_exact_block_is_accepted_without_calling_it_a_bundle(self):
        source = _f03_source()

        result = validate_forward_outcome("m3-f03", source, _blocked(source))

        self.assertEqual(result, {
            "case_id": "m3-f03",
            "status": "accepted_expected_block",
            "outcome_kind": "blocked",
            "errors": [],
            "evidence_gaps": [],
            "method_bundle_validation": "not_applicable_expected_block",
        })

    def test_f03_requires_actual_nonempty_upstream_change(self):
        source = _f03_source()
        source["route_output"]["approved_constraint_changes"] = []

        result = validate_forward_outcome("m3-f03", source, _blocked(source))

        self.assertInvalid(result, "upstream_approved_constraint_changes_required")

    def test_f03_original_limits_are_type_strict(self):
        source = _f03_source()
        outcome = _blocked(source)
        outcome["original_resource_limits"][0]["value"] = float(
            outcome["original_resource_limits"][0]["value"]
        )

        result = validate_forward_outcome("m3-f03", source, outcome)

        self.assertInvalid(result, "original_resource_limits_mismatch")

    def test_f03_rejects_applied_change_card_overlay_or_extra_code(self):
        source = _f03_source()
        outcome = _blocked(source)
        outcome["applied_constraint_changes"] = [
            copy.deepcopy(source["route_output"]["approved_constraint_changes"][0])
        ]
        result = validate_forward_outcome("m3-f03", source, outcome)
        self.assertInvalid(result, "approved_constraint_change_applied")

        for forbidden in ("method_cards", "domain_overlays"):
            outcome = _blocked(source)
            outcome[forbidden] = []
            result = validate_forward_outcome("m3-f03", source, outcome)
            self.assertInvalid(result, "unknown_blocked_outcome_fields")

        outcome = _blocked(source)
        outcome["terminal_code"] = [TERMINAL_CODE, "extra"]
        result = validate_forward_outcome("m3-f03", source, outcome)
        self.assertInvalid(result, "unexpected_blocked_terminal_code")

    def test_f03_cannot_be_accepted_as_bundle_and_other_cases_cannot_block(self):
        source = _f03_source()
        result = validate_forward_outcome(
            "m3-f03",
            source,
            {"outcome_kind": "bundle", "bundle": make_valid_m3_bundle()},
        )
        self.assertInvalid(result, "f03_requires_blocked_outcome")

        result = validate_forward_outcome("m3-f02", source, _blocked(source))
        self.assertInvalid(result, "blocked_outcome_only_allowed_for_f03")


if __name__ == "__main__":
    unittest.main()
