#!/usr/bin/env python3
"""Contract tests for the immutable F04-D01 confirmation successor."""

from __future__ import annotations

import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = Path(__file__).with_name("confirm_f04_d01.py")
DRAFT = ROOT / "evals" / "f04-upstream" / "m2" / "f04-m2-direction-bundle.json"
EXPECTED_PRECONFIRMATION_HASH = (
    "884e80387776ecdf3963a3db79c1bec3eb8fe48f65f17c0fc8852d61b54f8678"
)
EXPECTED_DIRECTION_HASH = (
    "1f81072903df3afa27d49bd06c17209141014ac8ea5026973a8bc7bd8e69b310"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("confirm_f04_d01", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("confirmation_module_spec_unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ConfirmF04D01Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()
        cls.draft = json.loads(DRAFT.read_text(encoding="utf-8"))

    def test_builds_exact_route_free_confirmation_successor(self) -> None:
        original = copy.deepcopy(self.draft)

        confirmed, event = self.module.build_confirmed(self.draft)

        self.assertEqual(
            confirmed["direction_decision"]["selected_direction_id"], "F04-D01"
        )
        self.assertEqual(confirmed["direction_decision"]["status"], "user_confirmed")
        self.assertEqual(
            confirmed["direction_decision"]["permitted_next_actions"],
            ["modify", "reject", "generate_route"],
        )
        self.assertEqual(event["actor_role"], "user")
        self.assertEqual(event["selected_direction_id"], "F04-D01")
        self.assertEqual(
            event["source_message_id"],
            "codex-task:019fd4f7-e1c4-7fd1-9799-786f62fda8e6:item-46",
        )
        self.assertEqual(
            event["source_message_excerpt"], "Confirm F04 direction F04-D01"
        )
        self.assertEqual(event["previous_bundle_hash"], EXPECTED_PRECONFIRMATION_HASH)
        self.assertIsNone(confirmed["route_output"])
        self.assertEqual(self.draft, original)

    def test_rejects_changed_preconfirmation_bundle(self) -> None:
        changed = copy.deepcopy(self.draft)
        changed["portfolio_status"] = "changed"

        with self.assertRaisesRegex(ValueError, "preconfirmation_bundle_hash_mismatch"):
            self.module.build_confirmed(changed)

    def test_rejects_non_null_route(self) -> None:
        changed = copy.deepcopy(self.draft)
        changed["route_output"] = {}

        with self.assertRaisesRegex(ValueError, "draft_route_output_must_be_null"):
            self.module.build_confirmed(changed)

    def test_rejects_missing_selected_direction(self) -> None:
        changed = copy.deepcopy(self.draft)
        changed["direction_portfolio"]["directions"] = [
            direction
            for direction in changed["direction_portfolio"]["directions"]
            if direction["direction_id"] != "F04-D01"
        ]

        with self.assertRaisesRegex(ValueError, "selected_direction_missing"):
            self.module.build_confirmed(changed)

    def test_rejects_changed_selected_direction_excerpt(self) -> None:
        changed = copy.deepcopy(self.draft)
        direction = next(
            direction
            for direction in changed["direction_portfolio"]["directions"]
            if direction["direction_id"] == "F04-D01"
        )
        direction["title"] += " changed"

        with self.assertRaisesRegex(ValueError, "selected_direction_hash_mismatch"):
            self.module.build_confirmed(changed)

    def test_expected_hash_constants_match_source_artifact(self) -> None:
        self.assertEqual(
            self.module.canonical_sha256(self.draft), EXPECTED_PRECONFIRMATION_HASH
        )
        direction = next(
            direction
            for direction in self.draft["direction_portfolio"]["directions"]
            if direction["direction_id"] == "F04-D01"
        )
        self.assertEqual(
            self.module.canonical_sha256(direction), EXPECTED_DIRECTION_HASH
        )


if __name__ == "__main__":
    unittest.main()
