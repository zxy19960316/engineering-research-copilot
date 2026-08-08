from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT = (
    REPO_ROOT
    / "evals"
    / "m3"
    / "forward-inputs-r4"
    / "m3-model-output-contract.schema.json"
)
sys.path.insert(0, str(REPO_ROOT / "skills" / "engineering-research-copilot" / "scripts"))

from compose_m3_bundle import validate_model_payload_contract  # noqa: E402


CARD_FIELDS = {
    "schema_version",
    "card_id",
    "method_family",
    "applicability",
    "assumptions",
    "minimum_resources",
    "inherited_constraints",
    "baselines",
    "controls",
    "procedure_outline",
    "primary_metrics",
    "uncertainty_handling",
    "validation_checks",
    "failure_modes",
    "stop_conditions",
    "pivot_conditions",
    "safety_boundaries",
    "source_ledger",
}


def valid_payload() -> dict:
    card = {
        "schema_version": "m3.1",
        "card_id": "card:test",
        "method_family": "data_ml_hybrid",
        "applicability": {
            "supported_claim_types": ["claim_type"],
            "required_inputs": ["input"],
            "incompatible_conditions": ["condition"],
        },
        "assumptions": ["assumption"],
        "minimum_resources": [
            {
                "resource": "GPU",
                "required_value": 1,
                "unit": "count",
                "source_constraint_id": "R1",
            }
        ],
        "inherited_constraints": [
            {
                "constraint_id": "R1",
                "resource": "GPU",
                "operator": "<=",
                "value": 1,
                "unit": "count",
            }
        ],
        "baselines": ["baseline"],
        "controls": ["control"],
        "procedure_outline": ["procedure"],
        "primary_metrics": ["M1"],
        "uncertainty_handling": ["uncertainty"],
        "validation_checks": ["check"],
        "failure_modes": ["failure"],
        "stop_conditions": [
            {
                "criterion_type": "stop",
                "metric_id": "M1",
                "operator": "<",
                "value": 0.1,
                "unit": "fraction",
            }
        ],
        "pivot_conditions": [
            {
                "criterion_type": "pivot",
                "metric_id": "M1",
                "operator": ">=",
                "value": 0.1,
                "unit": "fraction",
            }
        ],
        "safety_boundaries": ["boundary"],
        "source_ledger": [
            {
                "source_id": "source:1",
                "candidate_id": "candidate:1",
                "basis_level": "abstract",
                "support_types": ["method"],
                "supports": ["support"],
                "does_not_support": ["non-support"],
                "limitations": ["limitation"],
            }
        ],
    }
    assert set(card) == CARD_FIELDS
    return {
        "coaching_mode": "bounded",
        "method_cards": [card],
        "domain_overlays": [],
    }


class M3OutputContractTests(unittest.TestCase):
    def test_contract_is_closed_and_does_not_expose_case_results(self):
        schema = json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(
            set(schema["properties"]),
            {"coaching_mode", "method_cards", "domain_overlays"},
        )
        serialized = json.dumps(schema)
        self.assertNotIn("expected_status", serialized)
        self.assertNotIn("fixtures", serialized.lower())

    def test_closed_payload_is_accepted(self):
        self.assertEqual(validate_model_payload_contract(valid_payload()), [])

    def test_primary_metrics_are_metric_id_strings_not_metric_objects(self):
        payload = valid_payload()
        payload["method_cards"][0]["primary_metrics"] = [
            {"metric_id": "M1", "metric": "description", "unit": "fraction"}
        ]
        self.assertEqual(
            validate_model_payload_contract(payload),
            [
                {
                    "code": "primary_metrics_item_type",
                    "path": "method_cards[0].primary_metrics[0]",
                    "expected": "string metric_id",
                }
            ],
        )

    def test_route_incompatible_and_empty_cards_are_not_payload_contracts(self):
        payload = {
            "coaching_mode": "route_incompatible",
            "method_cards": [],
            "domain_overlays": [],
        }
        self.assertEqual(
            validate_model_payload_contract(payload),
            [
                {
                    "code": "coaching_mode_enum",
                    "path": "coaching_mode",
                    "expected": ["bounded", "route_specific"],
                },
                {
                    "code": "method_cards_min_items",
                    "path": "method_cards",
                    "expected": "at least one closed method card",
                },
            ],
        )

    def test_checker_does_not_mutate_payload(self):
        payload = valid_payload()
        before = copy.deepcopy(payload)
        validate_model_payload_contract(payload)
        self.assertEqual(payload, before)


if __name__ == "__main__":
    unittest.main()
