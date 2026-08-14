"""Validate the scientific-figure recipe asset and select a read-only workflow."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ASSET_SCHEMA = "figure-recipes.v1"
BRIEF_SCHEMA = "figure-brief.v1"
ASSET_FIELDS = {"schema_version", "asset_policy", "sources", "recipes"}
POLICY_FIELDS = {
    "static_is_authoritative",
    "paper_images_bundled",
    "network_required",
    "citation_or_star_scoring_allowed",
}
SOURCE_FIELDS = {
    "source_id",
    "title",
    "url",
    "evidence_level",
    "source_roles",
    "license_note",
    "checked_at",
}
RECIPE_FIELDS = {
    "recipe_id",
    "family",
    "claim_types",
    "decision_question",
    "admissible_claims",
    "prohibited_substitutions",
    "required_brief_fields",
    "required_data_fields",
    "preconditions",
    "minimum_views",
    "uncertainty_requirements",
    "fail_closed_conditions",
    "adversarial_checks",
    "accessibility_checks",
    "export_targets",
    "interaction_policy",
    "minimum_falsification_view",
    "adjacent_recipe_ids",
    "source_ids",
}
BRIEF_FIELDS = {
    "schema_version",
    "brief_id",
    "claim_type",
    "outcome",
    "unit_of_observation",
    "columns",
    "units",
    "pairing_or_hierarchy",
    "missingness",
    "split",
    "uncertainty",
    "time_or_censoring",
    "design_or_seed_alignment",
    "transform_and_missingness",
    "edge_semantics_and_layout_seed",
    "coordinates_and_scale",
    "acceptable_difference",
    "class_prevalence",
    "residual_definition",
    "interaction_needed",
    "target_journal",
    "backend",
    "execution_authorized",
}
REQUIRED_FAMILIES = {
    "regression_diagnostics",
    "agreement_concordance",
    "calibration_reliability",
    "uncertainty_interval",
    "distribution_estimation",
    "classification_curves",
    "survival_time_event",
    "sensitivity_ablation",
    "heatmap_multivariate",
    "network_relationships",
    "field_multiphysics",
}
CLAIM_TYPES = {
    "regression",
    "agreement",
    "calibration",
    "uncertainty",
    "distribution",
    "classification",
    "survival",
    "sensitivity",
    "ablation",
    "heatmap",
    "network",
    "field",
}
EVIDENCE_LEVELS = {
    "metadata_level",
    "abstract_level",
    "caption_context",
    "fulltext_or_official",
}
SOURCE_ROLES = {
    "method_support",
    "visual_precedent",
    "implementation",
    "journal_spec",
    "license",
}
INTERACTION_POLICIES = {
    "static_default",
    "optional_self_contained_with_static_equivalent",
}
EXPORT_TARGETS = {"svg", "pdf", "png", "tiff", "graphml", "self_contained_html"}
BACKENDS = {"unselected", "python", "r"}


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _text_list(value: Any, *, allow_empty: bool = False) -> bool:
    return (
        isinstance(value, list)
        and (allow_empty or bool(value))
        and all(_text(item) for item in value)
    )


def _https_url(value: Any) -> bool:
    if not _text(value):
        return False
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc)


def validate_assets(payload: Any) -> list[str]:
    """Return stable errors for the closed figure-recipes.v1 asset."""

    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["asset_not_object"]
    if set(payload) != ASSET_FIELDS:
        errors.append("asset_fields_invalid")
    if payload.get("schema_version") != ASSET_SCHEMA:
        errors.append("asset_schema_invalid")

    policy = payload.get("asset_policy")
    if not isinstance(policy, dict) or set(policy) != POLICY_FIELDS:
        errors.append("asset_policy_invalid")
    else:
        expected_policy = {
            "static_is_authoritative": True,
            "paper_images_bundled": False,
            "network_required": False,
            "citation_or_star_scoring_allowed": False,
        }
        if policy != expected_policy:
            errors.append("asset_policy_values_invalid")

    sources = payload.get("sources")
    if not isinstance(sources, list) or not sources:
        errors.append("sources_invalid")
        sources = []
    source_by_id: dict[str, dict[str, Any]] = {}
    for index, source in enumerate(sources):
        prefix = f"source_{index}"
        if not isinstance(source, dict):
            errors.append(f"{prefix}_not_object")
            continue
        if set(source) != SOURCE_FIELDS:
            errors.append(f"{prefix}_fields_invalid")
        source_id = source.get("source_id")
        if not _text(source_id):
            errors.append(f"{prefix}_id_invalid")
        elif source_id in source_by_id:
            errors.append("duplicate_source_id")
        else:
            source_by_id[source_id] = source
        if not _text(source.get("title")):
            errors.append(f"{prefix}_title_invalid")
        if not _https_url(source.get("url")):
            errors.append(f"{prefix}_url_invalid")
        if source.get("evidence_level") not in EVIDENCE_LEVELS:
            errors.append(f"{prefix}_evidence_level_invalid")
        roles = source.get("source_roles")
        if not _text_list(roles) or not set(roles).issubset(SOURCE_ROLES):
            errors.append(f"{prefix}_source_roles_invalid")
        if not _text(source.get("license_note")):
            errors.append(f"{prefix}_license_note_invalid")
        if source.get("checked_at") != "2026-08-14":
            errors.append(f"{prefix}_checked_at_invalid")

    recipes = payload.get("recipes")
    if not isinstance(recipes, list) or not recipes:
        errors.append("recipes_invalid")
        recipes = []
    recipe_by_id: dict[str, dict[str, Any]] = {}
    observed_families: set[str] = set()
    observed_claim_types: set[str] = set()
    list_fields = {
        "claim_types",
        "admissible_claims",
        "prohibited_substitutions",
        "required_brief_fields",
        "required_data_fields",
        "preconditions",
        "minimum_views",
        "uncertainty_requirements",
        "fail_closed_conditions",
        "adversarial_checks",
        "accessibility_checks",
        "export_targets",
        "source_ids",
    }
    for index, recipe in enumerate(recipes):
        prefix = f"recipe_{index}"
        if not isinstance(recipe, dict):
            errors.append(f"{prefix}_not_object")
            continue
        if set(recipe) != RECIPE_FIELDS:
            errors.append(f"{prefix}_fields_invalid")
        recipe_id = recipe.get("recipe_id")
        if not _text(recipe_id):
            errors.append(f"{prefix}_id_invalid")
        elif recipe_id in recipe_by_id:
            errors.append("duplicate_recipe_id")
        else:
            recipe_by_id[recipe_id] = recipe
        family = recipe.get("family")
        if family not in REQUIRED_FAMILIES:
            errors.append(f"{prefix}_family_invalid")
        elif family in observed_families:
            errors.append("duplicate_recipe_family")
        else:
            observed_families.add(family)
        for field in ("decision_question", "minimum_falsification_view"):
            if not _text(recipe.get(field)):
                errors.append(f"{prefix}_{field}_invalid")
        for field in list_fields:
            if not _text_list(recipe.get(field)):
                errors.append(f"{prefix}_{field}_invalid")
        adjacent = recipe.get("adjacent_recipe_ids")
        if not _text_list(adjacent, allow_empty=True):
            errors.append(f"{prefix}_adjacent_recipe_ids_invalid")
        claim_types = recipe.get("claim_types", [])
        if isinstance(claim_types, list):
            if not set(claim_types).issubset(CLAIM_TYPES):
                errors.append(f"{prefix}_claim_types_unknown")
            for claim_type in claim_types:
                if claim_type in observed_claim_types:
                    errors.append("duplicate_claim_type_owner")
                observed_claim_types.add(claim_type)
        required_fields = recipe.get("required_brief_fields", [])
        if isinstance(required_fields, list) and not set(required_fields).issubset(BRIEF_FIELDS):
            errors.append(f"{prefix}_required_brief_fields_unknown")
        targets = recipe.get("export_targets", [])
        if isinstance(targets, list) and not set(targets).issubset(EXPORT_TARGETS):
            errors.append(f"{prefix}_export_targets_invalid")
        if recipe.get("interaction_policy") not in INTERACTION_POLICIES:
            errors.append(f"{prefix}_interaction_policy_invalid")
        source_ids = recipe.get("source_ids", [])
        if isinstance(source_ids, list):
            if any(source_id not in source_by_id for source_id in source_ids):
                errors.append(f"{prefix}_source_id_unknown")
            roles = {
                role
                for source_id in source_ids
                if source_id in source_by_id
                for role in source_by_id[source_id]["source_roles"]
            }
            if not roles.intersection({"method_support", "implementation"}):
                errors.append(f"{prefix}_method_or_implementation_source_missing")

    if observed_families != REQUIRED_FAMILIES:
        errors.append("recipe_family_coverage_invalid")
    if observed_claim_types != CLAIM_TYPES:
        errors.append("claim_type_coverage_invalid")
    for recipe_id, recipe in recipe_by_id.items():
        for adjacent_id in recipe.get("adjacent_recipe_ids", []):
            if adjacent_id == recipe_id:
                errors.append(f"adjacent_recipe_self:{recipe_id}")
            elif adjacent_id not in recipe_by_id:
                errors.append(f"adjacent_recipe_unknown:{recipe_id}")

    return sorted(set(errors))


def validate_brief(brief: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(brief, dict):
        return ["brief_not_object"]
    if set(brief) != BRIEF_FIELDS:
        errors.append("brief_fields_invalid")
    if brief.get("schema_version") != BRIEF_SCHEMA:
        errors.append("brief_schema_invalid")
    if not _text(brief.get("brief_id")):
        errors.append("brief_id_invalid")
    if brief.get("claim_type") not in CLAIM_TYPES:
        errors.append("claim_type_invalid")
    for field in (
        "outcome",
        "unit_of_observation",
        "pairing_or_hierarchy",
        "missingness",
        "split",
        "uncertainty",
        "time_or_censoring",
        "design_or_seed_alignment",
        "transform_and_missingness",
        "edge_semantics_and_layout_seed",
        "coordinates_and_scale",
        "acceptable_difference",
        "class_prevalence",
        "residual_definition",
        "target_journal",
    ):
        value = brief.get(field)
        if value is not None and not _text(value):
            errors.append(f"brief_{field}_invalid")
    if not isinstance(brief.get("columns"), list) or not all(
        _text(column) for column in brief.get("columns", [])
    ):
        errors.append("brief_columns_invalid")
    units = brief.get("units")
    if not isinstance(units, dict) or not all(
        _text(key) and _text(value) for key, value in units.items()
    ):
        errors.append("brief_units_invalid")
    for field in ("interaction_needed", "execution_authorized"):
        if not isinstance(brief.get(field), bool):
            errors.append(f"brief_{field}_invalid")
    if brief.get("backend") not in BACKENDS:
        errors.append("brief_backend_invalid")
    return sorted(set(errors))


def _present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    if isinstance(value, bool):
        return True
    if isinstance(value, (int, float)):
        return not isinstance(value, bool) and math.isfinite(value)
    return False


def select_recipe(assets: Any, brief: Any) -> dict[str, Any]:
    """Select one recipe without reading data, plotting, or writing files."""

    asset_errors = validate_assets(assets)
    if asset_errors:
        return {"status": "invalid_assets", "errors": asset_errors, "side_effects": []}
    brief_errors = validate_brief(brief)
    if brief_errors:
        return {"status": "invalid_brief", "errors": brief_errors, "side_effects": []}

    recipe = next(
        recipe
        for recipe in assets["recipes"]
        if brief["claim_type"] in recipe["claim_types"]
    )
    missing = [
        field for field in recipe["required_brief_fields"] if not _present(brief[field])
    ]
    if brief["execution_authorized"] and brief["backend"] == "unselected":
        missing.append("backend")
    warnings: list[str] = []
    if brief["interaction_needed"] and recipe["interaction_policy"] == "static_default":
        warnings.append("interaction_not_recommended_by_primary_recipe")
    if not brief["execution_authorized"] and brief["backend"] != "unselected":
        warnings.append("backend_selected_without_execution_authority")
    if brief["target_journal"] is not None:
        warnings.append("target_journal_profile_requires_current_primary_verification")
    status = "needs_information" if missing else "recipe_ready"
    readiness = "concept_sketch" if missing else "route_preparation"
    return {
        "status": status,
        "brief_id": brief["brief_id"],
        "recipe_id": recipe["recipe_id"],
        "family": recipe["family"],
        "missing_fields": sorted(set(missing)),
        "warnings": warnings,
        "readiness": readiness,
        "execution_authorized": brief["execution_authorized"],
        "backend": brief["backend"],
        "adjacent_recipe_ids": recipe["adjacent_recipe_ids"],
        "minimum_falsification_view": recipe["minimum_falsification_view"],
        "minimum_views": recipe["minimum_views"],
        "fail_closed_conditions": recipe["fail_closed_conditions"],
        "source_ids": recipe["source_ids"],
        "next_action": (
            "provide_missing_fields"
            if missing
            else "verify_scoped_write_authorization_then_execute_selected_backend"
            if brief["execution_authorized"]
            else "review_recipe_and_request_scoped_figure_execution_if_desired"
        ),
        "does_not_authorize": [
            "data_modification",
            "download",
            "upload",
            "dependency_installation",
            "experiment",
            "simulation",
            "training",
            "publication",
            "external_communication",
        ],
        "side_effects": [],
    }


def load_assets(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    default_assets = Path(__file__).resolve().parents[1] / "assets" / "figure-recipes.json"
    parser = argparse.ArgumentParser(description="Validate or select a scientific figure recipe")
    parser.add_argument("--assets", type=Path, default=default_assets)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate-assets", action="store_true")
    mode.add_argument("--brief", type=Path)
    args = parser.parse_args(argv)
    try:
        assets = load_assets(args.assets)
    except (OSError, json.JSONDecodeError) as error:
        print(json.dumps({"status": "invalid_assets", "errors": [f"asset_unreadable:{type(error).__name__}"], "side_effects": []}, separators=(",", ":")))
        return 1
    if args.validate_assets:
        errors = validate_assets(assets)
        result = {
            "status": "valid" if not errors else "invalid_assets",
            "errors": errors,
            "recipe_count": len(assets.get("recipes", [])) if isinstance(assets, dict) else 0,
            "source_count": len(assets.get("sources", [])) if isinstance(assets, dict) else 0,
            "side_effects": [],
        }
    else:
        try:
            brief = json.loads(args.brief.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            print(json.dumps({"status": "invalid_brief", "errors": [f"brief_unreadable:{type(error).__name__}"], "side_effects": []}, separators=(",", ":")))
            return 1
        result = select_recipe(assets, brief)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0 if result["status"] in {"valid", "recipe_ready", "needs_information"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
