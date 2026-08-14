from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "skills" / "research-figure-workflow"
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from select_figure_recipe import (  # noqa: E402
    REQUIRED_FAMILIES,
    load_assets,
    main,
    select_recipe,
    validate_assets,
    validate_brief,
)


ASSET_PATH = SKILL_ROOT / "assets" / "figure-recipes.json"


def _assets() -> dict:
    return load_assets(ASSET_PATH)


def _brief(claim_type: str = "agreement") -> dict:
    return {
        "schema_version": "figure-brief.v1",
        "brief_id": "fixture:figure-brief",
        "claim_type": claim_type,
        "outcome": "Synthetic outcome",
        "unit_of_observation": "Synthetic subject",
        "columns": ["fixture:a", "fixture:b"],
        "units": {"fixture:a": "synthetic unit", "fixture:b": "synthetic unit"},
        "pairing_or_hierarchy": "Paired synthetic observations",
        "missingness": "No missing values in the contract fixture",
        "split": "Untouched synthetic evaluation split",
        "uncertainty": "Synthetic 95% interval with method to be specified by the recipe",
        "time_or_censoring": "Synthetic time origin, event, and censoring definition",
        "design_or_seed_alignment": "Aligned synthetic seeds, folds, and evaluation rows",
        "transform_and_missingness": "No transform; missing values remain explicitly missing",
        "edge_semantics_and_layout_seed": "Synthetic association edges; fixed seed 0",
        "coordinates_and_scale": "Synthetic monotonic grid, shared coordinates and color scale",
        "acceptable_difference": "Externally supplied synthetic tolerance",
        "class_prevalence": "Synthetic positive fraction fixed before evaluation",
        "residual_definition": "Observed minus fitted on the synthetic evaluation split",
        "interaction_needed": False,
        "target_journal": None,
        "backend": "unselected",
        "execution_authorized": False,
    }


class FigureRecipeAssetTests(unittest.TestCase):
    def test_asset_is_closed_and_covers_all_families(self):
        assets = _assets()
        self.assertEqual([], validate_assets(assets))
        self.assertEqual(REQUIRED_FAMILIES, {recipe["family"] for recipe in assets["recipes"]})
        self.assertEqual(11, len(assets["recipes"]))

    def test_asset_forbids_paper_images_network_and_popularity_scoring(self):
        policy = _assets()["asset_policy"]
        self.assertTrue(policy["static_is_authoritative"])
        self.assertFalse(policy["paper_images_bundled"])
        self.assertFalse(policy["network_required"])
        self.assertFalse(policy["citation_or_star_scoring_allowed"])

    def test_every_source_has_https_provenance_and_license_note(self):
        for source in _assets()["sources"]:
            self.assertTrue(source["url"].startswith("https://"))
            self.assertTrue(source["license_note"].strip())
            self.assertEqual("2026-08-14", source["checked_at"])

    def test_unknown_adjacency_and_source_fail_closed(self):
        assets = _assets()
        assets["recipes"][0]["adjacent_recipe_ids"] = ["missing-recipe.v1"]
        self.assertIn("adjacent_recipe_unknown:regression-diagnostics.v1", validate_assets(assets))

        assets = _assets()
        assets["recipes"][0]["source_ids"] = ["missing-source"]
        self.assertIn("recipe_0_source_id_unknown", validate_assets(assets))


class FigureRecipeSelectionTests(unittest.TestCase):
    def test_brief_schema_is_closed(self):
        brief = _brief()
        self.assertEqual([], validate_brief(brief))
        brief["invented_result"] = 1
        self.assertIn("brief_fields_invalid", validate_brief(brief))

    def test_tracked_brief_example_selects_agreement_without_execution(self):
        brief = json.loads(
            (SKILL_ROOT / "assets" / "figure-brief-example.json").read_text(
                encoding="utf-8"
            )
        )
        result = select_recipe(_assets(), brief)
        self.assertEqual("recipe_ready", result["status"])
        self.assertEqual("agreement-concordance.v1", result["recipe_id"])
        self.assertFalse(result["execution_authorized"])
        self.assertEqual([], result["side_effects"])

    def test_selection_is_deterministic_and_read_only(self):
        assets = _assets()
        brief = _brief("agreement")
        original_assets = copy.deepcopy(assets)
        original_brief = copy.deepcopy(brief)
        first = select_recipe(assets, brief)
        second = select_recipe(assets, brief)
        self.assertEqual(first, second)
        self.assertEqual("recipe_ready", first["status"])
        self.assertEqual("agreement-concordance.v1", first["recipe_id"])
        self.assertEqual([], first["side_effects"])
        self.assertFalse(first["execution_authorized"])
        self.assertEqual(original_assets, assets)
        self.assertEqual(original_brief, brief)

    def test_missing_design_field_returns_needs_information(self):
        brief = _brief("agreement")
        brief["acceptable_difference"] = None
        brief["pairing_or_hierarchy"] = None
        result = select_recipe(_assets(), brief)
        self.assertEqual("needs_information", result["status"])
        self.assertEqual("concept_sketch", result["readiness"])
        self.assertEqual(["acceptable_difference", "pairing_or_hierarchy"], result["missing_fields"])
        self.assertEqual("provide_missing_fields", result["next_action"])

    def test_execution_authority_still_requires_backend(self):
        brief = _brief("field")
        brief["execution_authorized"] = True
        result = select_recipe(_assets(), brief)
        self.assertEqual("needs_information", result["status"])
        self.assertIn("backend", result["missing_fields"])
        self.assertIn("simulation", result["does_not_authorize"])

        brief["backend"] = "python"
        result = select_recipe(_assets(), brief)
        self.assertEqual("recipe_ready", result["status"])
        self.assertEqual("verify_scoped_write_authorization_then_execute_selected_backend", result["next_action"])
        self.assertEqual([], result["side_effects"])

    def test_target_journal_and_unneeded_interaction_are_warnings(self):
        brief = _brief("regression")
        brief["target_journal"] = "Synthetic journal profile"
        brief["interaction_needed"] = True
        result = select_recipe(_assets(), brief)
        self.assertIn("target_journal_profile_requires_current_primary_verification", result["warnings"])
        self.assertIn("interaction_not_recommended_by_primary_recipe", result["warnings"])

    def test_validation_cli_performs_no_write(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            copied_asset = temp_root / "recipes.json"
            copied_asset.write_text(ASSET_PATH.read_text(encoding="utf-8"), encoding="utf-8")
            before = sorted(path.name for path in temp_root.iterdir())
            self.assertEqual(0, main(["--assets", str(copied_asset), "--validate-assets"]))
            after = sorted(path.name for path in temp_root.iterdir())
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
