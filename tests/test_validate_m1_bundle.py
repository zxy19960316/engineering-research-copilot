from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "skills" / "engineering-research-copilot" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from validate_m1_bundle import normalize_doi, validate_bundle  # noqa: E402


def _candidate(number: int) -> dict:
    candidate_id = f"fixture:P{number:02d}"
    roles = (
        ["direct_problem"]
        if number <= 3
        else ["method"]
        if number <= 5
        else ["transfer_bridge"]
        if number <= 7
        else ["counter_limitation"]
    )
    return {
        "candidate_id": candidate_id,
        "verification_status": "fixture_only",
        "recommendation_eligible": True,
        "evidence_roles": roles,
        "selection_role": roles[0],
        "basis_level": "abstract_level",
        "verified_record": {
            "paper_id": candidate_id,
            "title": f"Synthetic contract record {number:02d}",
            "authors": ["Fixture Author"],
            "year_online": None,
            "year_issue": None,
            "venue": "",
            "publication_type": "offline_contract_fixture",
            "doi": None,
            "canonical_url": "",
            "alternate_id": None,
            "verification": {
                "status": "fixture_only",
                "checked_sources": [],
                "title_match": "not_checked",
                "author_match": "not_checked",
                "version_relation": "same_work",
                "recommendation_eligible": True,
                "blocking_reasons": [],
            },
            "evidence_role": roles[0],
            "supports": "Offline structural validation only",
            "does_not_support": "Real citation existence or metadata accuracy",
            "basis_level": "abstract_level",
        },
    }


def _paper_map(round_number: int, selected_ids: list[str]) -> dict:
    nodes = []
    fallback = []
    for candidate_id in selected_ids:
        number = int(candidate_id.rsplit("P", 1)[1])
        candidate = _candidate(number)
        node = {
            "id": candidate_id,
            "node_type": "paper",
            "fit_score": 0.8,
            "evidence_role": candidate["evidence_roles"][0],
            "verification_status": "fixture_only",
            "basis_level": "abstract_level",
            "short_note": "Offline fixture node",
        }
        nodes.append(node)
        fallback.append(
            {
                "entry_type": "node",
                "id": candidate_id,
                "node_type": "paper",
                "evidence_role": node["evidence_role"],
                "verification_status": "fixture_only",
                "basis_level": "abstract_level",
                "text": f"{candidate_id}: Offline fixture node",
            }
        )
    return {
        "round": round_number,
        "node_size_basis": "user_fit",
        "legend": {
            "evidence_roles": [
                "direct_problem",
                "method",
                "transfer_bridge",
                "counter_limitation",
            ],
            "basis_levels": [
                "metadata_level",
                "abstract_level",
                "fulltext_level",
            ],
        },
        "nodes": nodes,
        "edges": [],
        "text_fallback": fallback,
    }


def _round_bundle(round_number: int, selected_ids: list[str]) -> dict:
    brief_version = round_number
    query_id = "Q-STABLE"
    query_text = (
        "public engineering simulation evidence"
        if round_number == 1
        else "public simulation evidence excluding proprietary data"
    )
    return {
        "schema_version": "m1.2",
        "round": round_number,
        "research_brief": {
            "brief_version": brief_version,
            "branch_id": "branch-a",
            "engineering_object": "fixture object",
            "target_problem": "fixture problem",
            "target_metric": "fixture metric",
            "available_data": ["public simulation"],
            "resources": ["offline fixtures"],
            "time_budget": "fixture only",
            "preferred_routes": [],
            "excluded_routes": ["proprietary data"] if round_number == 2 else [],
            "hard_constraints": [],
            "soft_preferences": [],
            "open_questions": [],
            "evidence_needs": [],
        },
        "search_plan": {
            "round": round_number,
            "brief_version": brief_version,
            "branch_id": "branch-a",
            "time_boundary": ["fixture only"],
            "language_boundary": ["English"],
            "source_boundary": ["offline_contract_fixture"],
            "queries": [
                {
                    "query_id": query_id,
                    "purpose": "direct_problem",
                    "query_text": query_text,
                    "expected_evidence_role": "direct_problem",
                    "inclusion_terms": ["public simulation"],
                    "exclusion_terms": ["proprietary data"] if round_number == 2 else [],
                }
            ],
            "limitations": ["No real scholarly lookup was performed"],
        },
        "candidate_pool": [_candidate(number) for number in range(1, 16)],
        "selected_ids": selected_ids,
        "paper_map": _paper_map(round_number, selected_ids),
        "evidence_gaps": [],
        "search_limitations": [],
    }


def _root_state(terminal_state: str, stopped_after_round: int, outcome: str) -> dict:
    return {
        "schema_version": "m1.2",
        "terminal_state": terminal_state,
        "stopped_after_round": stopped_after_round,
        "outcome": outcome,
        "fixture_mode": True,
        "evidence_class": "offline_contract_fixture",
    }


def make_complete_fixture_bundle() -> dict:
    round_one_ids = [f"fixture:P{number:02d}" for number in range(1, 9)]
    round_two_ids = [
        "fixture:P01",
        "fixture:P02",
        "fixture:P03",
        "fixture:P04",
        "fixture:P09",
        "fixture:P10",
    ]
    round_two = _round_bundle(2, round_two_ids)
    dispositions = []
    for number in range(1, 5):
        candidate_id = f"fixture:P{number:02d}"
        dispositions.append(
            {
                "round_one_id": candidate_id,
                "disposition": "retained",
                "round_two_id": candidate_id,
                "reason": "Remains relevant after the stated constraint change",
                "cause_type": "feedback_delta",
                "cause_ref": "feedback_delta.added[0]",
            }
        )
    dispositions.extend(
        [
            {
                "round_one_id": "fixture:P05",
                "disposition": "replaced",
                "round_two_id": "fixture:P09",
                "reason": "A better public-data fixture occupies this slot",
                "cause_type": "feedback_delta",
                "cause_ref": "feedback_delta.rejected[0]",
            },
            {
                "round_one_id": "fixture:P06",
                "disposition": "replaced",
                "round_two_id": "fixture:P10",
                "reason": "A better public-data fixture occupies this slot",
                "cause_type": "feedback_delta",
                "cause_ref": "feedback_delta.rejected[0]",
            },
            {
                "round_one_id": "fixture:P07",
                "disposition": "removed",
                "round_two_id": None,
                "reason": "The route conflicts with the new data constraint",
                "cause_type": "feedback_delta",
                "cause_ref": "feedback_delta.rejected[0]",
            },
            {
                "round_one_id": "fixture:P08",
                "disposition": "removed",
                "round_two_id": None,
                "reason": "The route conflicts with the new data constraint",
                "cause_type": "feedback_delta",
                "cause_ref": "feedback_delta.rejected[0]",
            },
        ]
    )
    round_two["round_one_dispositions"] = dispositions
    return {
        **_root_state("M1_COMPLETE", 2, "complete"),
        "round1": _round_bundle(1, round_one_ids),
        "feedback_delta": {
            "from_brief_version": 1,
            "to_brief_version": 2,
            "inherited": [],
            "rejected": [
                {
                    "object_id": "fixture:P07",
                    "value": "Route requiring proprietary data",
                    "reason": "Exclude routes requiring proprietary data",
                }
            ],
            "reset": [],
            "added": [
                {
                    "object_id": "public_simulation_preference",
                    "value": "Prefer public simulation evidence",
                    "reason": "Prefer public simulation evidence",
                }
            ],
            "allocation": {"exploit": 30, "explore": 70},
            "query_changes": [
                {
                    "query_id": "Q-STABLE",
                    "reason": "Exclude proprietary-data routes",
                    "cause_refs": [
                        "feedback_delta.rejected[0]",
                        "feedback_delta.added[0]",
                    ],
                    "before": "public engineering simulation evidence",
                    "after": "public simulation evidence excluding proprietary data",
                }
            ],
        },
        "round2": round_two,
    }


def make_round_one_incomplete_bundle() -> dict:
    bundle = _root_state("WAITING_FOR_EVIDENCE_DECISION", 1, "evidence_incomplete")
    round_one = _round_bundle(1, ["fixture:P01", "fixture:P02", "fixture:P03"])
    round_one["candidate_pool"] = round_one["candidate_pool"][:10]
    round_one["paper_map"] = _paper_map(1, round_one["selected_ids"])
    round_one["evidence_gaps"] = [
        {"role": "direct_problem", "missing_count": 2},
        {"role": "method", "missing_count": 2},
        {"role": "transfer_bridge", "missing_count": 2},
        {"role": "counter_limitation", "missing_count": 1},
    ]
    round_one["search_limitations"] = [
        "Only ten eligible fixture records were available"
    ]
    bundle["round1"] = round_one
    return bundle


def make_round_two_incomplete_bundle() -> dict:
    bundle = make_complete_fixture_bundle()
    bundle.update(
        {
            "terminal_state": "WAITING_FOR_EVIDENCE_DECISION",
            "stopped_after_round": 2,
            "outcome": "evidence_incomplete",
        }
    )
    selected = ["fixture:P01", "fixture:P02", "fixture:P03"]
    bundle["round2"]["selected_ids"] = selected
    bundle["round2"]["paper_map"] = _paper_map(2, selected)
    bundle["round2"]["evidence_gaps"] = [
        "Two additional eligible papers are missing"
    ]
    for entry in bundle["round2"]["round_one_dispositions"]:
        if entry["round_one_id"] in selected:
            entry.update(
                {"disposition": "retained", "round_two_id": entry["round_one_id"]}
            )
        else:
            entry.update({"disposition": "removed", "round_two_id": None})
    return bundle


def run_cli_bundle(bundle: dict) -> subprocess.CompletedProcess[str]:
    script = SCRIPTS_DIR / "validate_m1_bundle.py"
    with tempfile.TemporaryDirectory() as directory:
        fixture_path = Path(directory) / "bundle.json"
        fixture_path.write_text(json.dumps(bundle), encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(script), str(fixture_path)],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )


def set_expanded_round_two_selection(bundle: dict, count: int) -> None:
    if count <= 10:
        selected_ids = [
            "fixture:P01",
            "fixture:P02",
            "fixture:P03",
            "fixture:P04",
            *[f"fixture:P{number:02d}" for number in range(9, 9 + count - 4)],
        ]
        dispositions = bundle["round2"]["round_one_dispositions"]
        for offset, entry in enumerate(dispositions[4:], start=9):
            entry["disposition"] = "replaced"
            entry["round_two_id"] = f"fixture:P{offset:02d}"
            entry["reason"] = "A preferred public-data fixture occupies this slot"
    else:
        selected_ids = [f"fixture:P{number:02d}" for number in range(1, count + 1)]
        dispositions = bundle["round2"]["round_one_dispositions"]
        for number, entry in enumerate(dispositions, start=1):
            candidate_id = f"fixture:P{number:02d}"
            entry["disposition"] = "retained"
            entry["round_two_id"] = candidate_id
            entry["reason"] = "Remains relevant after the stated constraint change"
            entry["cause_type"] = "feedback_delta"
            entry["cause_ref"] = "feedback_delta.added[0]"
    bundle["round2"]["selected_ids"] = selected_ids
    bundle["round2"]["paper_map"] = _paper_map(2, selected_ids)


def make_structurally_valid_production_bundle() -> dict:
    bundle = json.loads(
        json.dumps(make_complete_fixture_bundle()).replace("fixture:P", "contract:P")
    )
    bundle["fixture_mode"] = False
    for round_name in ("round1", "round2"):
        for candidate in bundle[round_name]["candidate_pool"]:
            candidate["verification_status"] = "verified_registry"
            verified_record = candidate["verified_record"]
            verified_record["alternate_id"] = {
                "authority": "contract",
                "value": candidate["candidate_id"],
            }
            verification = verified_record["verification"]
            verification["status"] = "verified_registry"
            verification["title_match"] = "exact"
            verification["author_match"] = "exact"
            verification["checked_sources"] = [
                {
                    "source_type": "doi_registry",
                    "canonical_record": (
                        "contract:doi_registry:" + candidate["candidate_id"]
                    ),
                    "checked_at": "2026-08-04T12:00:00+08:00",
                    "result": "match",
                }
            ]
        for node in bundle[round_name]["paper_map"]["nodes"]:
            if node["node_type"] == "paper":
                node["verification_status"] = "verified_registry"
        for entry in bundle[round_name]["paper_map"]["text_fallback"]:
            if entry["entry_type"] == "node" and entry["node_type"] == "paper":
                entry["verification_status"] = "verified_registry"
    return bundle


def malformed_bundle_cases() -> list[tuple[str, object]]:
    cases: list[tuple[str, object]] = [
        ("root_list", []),
        ("root_string", "not an object"),
        ("root_number", 7),
        ("root_null", None),
    ]

    edge_source = make_complete_fixture_bundle()
    edge_source["round1"]["paper_map"]["edges"] = [
        {
            "source": ["fixture:P01"],
            "target": "fixture:P02",
            "relation": "claim_support",
            "basis_level": "abstract_level",
        }
    ]
    cases.append(("edge_source_list", edge_source))

    non_string_doi = make_complete_fixture_bundle()
    non_string_doi["round1"]["candidate_pool"][0]["verified_record"]["doi"] = [
        "not-a-string"
    ]
    cases.append(("doi_list", non_string_doi))

    query_before = make_complete_fixture_bundle()
    query_before["feedback_delta"]["query_changes"][0]["before"] = ["bad"]
    cases.append(("query_before_list", query_before))

    disposition_type = make_complete_fixture_bundle()
    disposition_type["round2"]["round_one_dispositions"][0]["disposition"] = [
        "retained"
    ]
    cases.append(("disposition_list", disposition_type))

    node_id = make_complete_fixture_bundle()
    node_id["round1"]["paper_map"]["nodes"][0]["id"] = {"bad": "shape"}
    cases.append(("node_id_object", node_id))

    checked_sources = make_structurally_valid_production_bundle()
    checked_sources["round1"]["candidate_pool"][0]["verified_record"][
        "verification"
    ]["checked_sources"] = {"bad": "shape"}
    cases.append(("checked_sources_object", checked_sources))
    return cases


class ValidateM1BundleTests(unittest.TestCase):
    def test_valid_complete_bundle_returns_valid(self):
        result = validate_bundle(make_complete_fixture_bundle())
        self.assertEqual(result, {"status": "valid", "errors": [], "evidence_gaps": []})

    def test_round_one_incomplete_bundle_is_valid_incomplete(self):
        bundle = make_round_one_incomplete_bundle()
        result = validate_bundle(bundle)
        self.assertEqual(result["status"], "evidence_incomplete")
        self.assertEqual(result["errors"], [])
        self.assertIn("round1_candidate_pool_below_target", result["evidence_gaps"])

    def test_round_one_incomplete_rejects_round_two(self):
        bundle = make_round_one_incomplete_bundle()
        bundle["round2"] = _round_bundle(2, [])
        self.assertIn(
            "round_two_fields_after_round_one_stop", validate_bundle(bundle)["errors"]
        )

    def test_round_one_incomplete_cannot_claim_m1_complete(self):
        bundle = make_round_one_incomplete_bundle()
        bundle["terminal_state"] = "M1_COMPLETE"
        self.assertIn("terminal_state_inconsistent", validate_bundle(bundle)["errors"])

    def test_round_two_incomplete_requires_feedback_delta(self):
        bundle = make_round_two_incomplete_bundle()
        del bundle["feedback_delta"]
        self.assertIn("missing_feedback_delta", validate_bundle(bundle)["errors"])

    def test_complete_bundle_requires_round_two_ready(self):
        bundle = make_complete_fixture_bundle()
        bundle["round2"]["selected_ids"] = bundle["round2"]["selected_ids"][:3]
        self.assertIn(
            "complete_terminal_state_without_ready_round_two",
            validate_bundle(bundle)["errors"],
        )

    def test_complete_round_one_cannot_claim_incomplete_without_gap(self):
        bundle = make_complete_fixture_bundle()
        bundle.update(
            {
                "terminal_state": "WAITING_FOR_EVIDENCE_DECISION",
                "stopped_after_round": 1,
                "outcome": "evidence_incomplete",
            }
        )
        del bundle["feedback_delta"]
        del bundle["round2"]
        result = validate_bundle(bundle)
        self.assertEqual(result["status"], "invalid")
        self.assertIn("evidence_incomplete_without_gap", result["errors"])
        completed = run_cli_bundle(bundle)
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(json.loads(completed.stdout), result)

    def test_complete_round_two_cannot_claim_incomplete_without_gap(self):
        bundle = make_complete_fixture_bundle()
        bundle.update(
            {
                "terminal_state": "WAITING_FOR_EVIDENCE_DECISION",
                "outcome": "evidence_incomplete",
            }
        )
        result = validate_bundle(bundle)
        self.assertEqual(result["status"], "invalid")
        self.assertIn("evidence_incomplete_without_gap", result["errors"])
        completed = run_cli_bundle(bundle)
        self.assertEqual(completed.returncode, 1)
        self.assertEqual(json.loads(completed.stdout), result)

    def test_authorized_eight_paper_round_two_returns_valid(self):
        bundle = make_complete_fixture_bundle()
        set_expanded_round_two_selection(bundle, 8)
        bundle["round2"]["round_two_request"] = {
            "explicit_user_request": True,
            "requested_count": 8,
        }
        self.assertEqual(validate_bundle(bundle)["status"], "valid")

    def test_eight_paper_round_two_requires_true_matching_authorization(self):
        cases = (
            (None, "missing"),
            ({"explicit_user_request": False, "requested_count": 8}, "false"),
            ({"explicit_user_request": True, "requested_count": 7}, "mismatch"),
        )
        for request, label in cases:
            with self.subTest(label=label):
                bundle = make_complete_fixture_bundle()
                set_expanded_round_two_selection(bundle, 8)
                if request is not None:
                    bundle["round2"]["round_two_request"] = request
                result = validate_bundle(bundle)
                self.assertEqual(result["status"], "invalid")
                self.assertIn("round_two_expansion_not_authorized", result["errors"])

    def test_more_than_ten_round_two_papers_is_invalid(self):
        bundle = make_complete_fixture_bundle()
        set_expanded_round_two_selection(bundle, 11)
        bundle["round2"]["round_two_request"] = {
            "explicit_user_request": True,
            "requested_count": 11,
        }
        result = validate_bundle(bundle)
        self.assertEqual(result["status"], "invalid")
        self.assertIn("selection_count_out_of_range", result["errors"])

    def test_malformed_json_shapes_fail_closed_without_exception(self):
        for label, bundle in malformed_bundle_cases():
            with self.subTest(label=label):
                result = validate_bundle(bundle)
                self.assertEqual(result["status"], "invalid")
                self.assertEqual(set(result), {"status", "errors", "evidence_gaps"})
                self.assertTrue(result["errors"])

    def test_round_two_request_is_closed_in_every_round_and_count(self):
        round_one_request = make_complete_fixture_bundle()
        round_one_request["round1"]["round_two_request"] = {
            "explicit_user_request": False,
            "requested_count": 8,
        }
        self.assertIn(
            "round_two_request_in_round_one",
            validate_bundle(round_one_request)["errors"],
        )

        default_with_request = make_complete_fixture_bundle()
        default_with_request["round2"]["round_two_request"] = {
            "explicit_user_request": False,
            "requested_count": 6,
        }
        self.assertEqual(validate_bundle(default_with_request)["status"], "valid")

        invalid_requests = (
            [False, 6],
            {"explicit_user_request": False, "requested_count": 6, "extra": 1},
            {"explicit_user_request": 1, "requested_count": 6},
            {"explicit_user_request": False, "requested_count": True},
            {"explicit_user_request": False, "requested_count": 5},
        )
        for request in invalid_requests:
            with self.subTest(request=request):
                bundle = make_complete_fixture_bundle()
                bundle["round2"]["round_two_request"] = request
                self.assertIn(
                    "invalid_round_two_request", validate_bundle(bundle)["errors"]
                )

    def test_production_eligibility_requires_closed_current_provenance(self):
        self.assertEqual(
            validate_bundle(make_structurally_valid_production_bundle())["status"],
            "valid",
        )
        cases = (
            ("title_match", "conflict", "production_record_not_eligible"),
            ("author_match", "conflict", "production_record_not_eligible"),
            ("blocking_reasons", ["unresolved"], "production_record_not_eligible"),
            ("checked_sources", [], "missing_current_checked_sources"),
        )
        for field, value, expected in cases:
            with self.subTest(field=field):
                bundle = make_structurally_valid_production_bundle()
                verification = bundle["round1"]["candidate_pool"][0][
                    "verified_record"
                ]["verification"]
                verification[field] = value
                self.assertIn(expected, validate_bundle(bundle)["errors"])

        source_fields = (
            ("source_type", "ordinary_web"),
            ("result", "maybe"),
            ("checked_at", "2026-08-04"),
            ("canonical_record", ""),
        )
        for field, value in source_fields:
            with self.subTest(source_field=field):
                bundle = make_structurally_valid_production_bundle()
                source = bundle["round1"]["candidate_pool"][0]["verified_record"][
                    "verification"
                ]["checked_sources"][0]
                source[field] = value
                self.assertIn("invalid_checked_source", validate_bundle(bundle)["errors"])

    def test_partial_does_not_count_or_enter_selection(self):
        pool = make_structurally_valid_production_bundle()
        candidate = pool["round1"]["candidate_pool"][14]
        candidate["verification_status"] = "partial"
        candidate["recommendation_eligible"] = False
        verification = candidate["verified_record"]["verification"]
        verification["status"] = "partial"
        verification["recommendation_eligible"] = False
        result = validate_bundle(pool)
        self.assertIn("eligible_candidate_count_without_limit", result["errors"])

        selected = make_structurally_valid_production_bundle()
        candidate = selected["round1"]["candidate_pool"][0]
        candidate["verification_status"] = "partial"
        candidate["recommendation_eligible"] = False
        verification = candidate["verified_record"]["verification"]
        verification["status"] = "partial"
        verification["recommendation_eligible"] = False
        result = validate_bundle(selected)
        self.assertIn("selected_record_blocked", result["errors"])

    def test_blocked_status_in_selection_returns_invalid(self):
        bundle = make_complete_fixture_bundle()
        candidate = bundle["round1"]["candidate_pool"][0]
        candidate["verification_status"] = "conflicted"
        candidate["recommendation_eligible"] = False
        candidate["verified_record"]["verification"]["status"] = "conflicted"
        candidate["verified_record"]["verification"]["recommendation_eligible"] = False
        result = validate_bundle(bundle)
        self.assertEqual(result["status"], "invalid")
        self.assertIn("selected_record_blocked", result["errors"])

    def test_duplicate_normalized_doi_returns_invalid(self):
        bundle = make_complete_fixture_bundle()
        bundle["fixture_duplicate_doi_tokens"] = ["doi:TEST/SHARED.", "test/shared"]
        result = validate_bundle(bundle)
        self.assertEqual(result["status"], "invalid")
        self.assertIn("duplicate_normalized_doi", result["errors"])

    def test_map_sized_by_citation_count_returns_invalid(self):
        bundle = make_complete_fixture_bundle()
        bundle["round1"]["paper_map"]["node_size_basis"] = "citation_count"
        result = validate_bundle(bundle)
        self.assertEqual(result["status"], "invalid")
        self.assertIn("invalid_node_size_basis", result["errors"])

    def test_feedback_reason_without_query_change_returns_invalid(self):
        bundle = make_complete_fixture_bundle()
        bundle["feedback_delta"]["query_changes"] = []
        result = validate_bundle(bundle)
        self.assertEqual(result["status"], "invalid")
        self.assertIn("feedback_not_applied_to_query", result["errors"])

    def test_added_requires_value_and_reason(self):
        for missing in ("value", "reason"):
            with self.subTest(missing=missing):
                bundle = make_complete_fixture_bundle()
                del bundle["feedback_delta"]["added"][0][missing]
                self.assertIn(
                    "feedback_added_fields_invalid", validate_bundle(bundle)["errors"]
                )

    def test_reset_requires_previous_value_and_reason(self):
        for missing in ("previous_value", "reason"):
            with self.subTest(missing=missing):
                bundle = make_complete_fixture_bundle()
                bundle["feedback_delta"]["reset"] = [
                    {
                        "object_id": "old-fit",
                        "previous_value": "title fit",
                        "reason": "insufficient",
                    }
                ]
                bundle["feedback_delta"]["query_changes"][0]["cause_refs"].append(
                    "feedback_delta.reset[0]"
                )
                del bundle["feedback_delta"]["reset"][0][missing]
                self.assertIn(
                    "feedback_reset_fields_invalid", validate_bundle(bundle)["errors"]
                )

    def test_rejected_requires_value_and_reason(self):
        for missing in ("value", "reason"):
            with self.subTest(missing=missing):
                bundle = make_complete_fixture_bundle()
                del bundle["feedback_delta"]["rejected"][0][missing]
                self.assertIn(
                    "feedback_rejected_fields_invalid", validate_bundle(bundle)["errors"]
                )

    def test_inherited_requires_object_id_and_value(self):
        bundle = make_complete_fixture_bundle()
        bundle["feedback_delta"]["inherited"] = [
            {"object_id": "public-data-only"}
        ]
        self.assertIn(
            "feedback_inherited_fields_invalid", validate_bundle(bundle)["errors"]
        )

    def test_feedback_item_unknown_fields_are_invalid(self):
        bundle = make_complete_fixture_bundle()
        bundle["feedback_delta"]["added"][0]["extra"] = "closed schema"
        self.assertIn(
            "feedback_added_fields_invalid", validate_bundle(bundle)["errors"]
        )

        examples = {
            "inherited": {"object_id": "stable", "value": "still applies"},
            "rejected": {
                "object_id": "rejected",
                "value": "old route",
                "reason": "not suitable",
            },
            "reset": {
                "object_id": "reset",
                "previous_value": "old assumption",
                "reason": "not supported",
            },
            "added": {
                "object_id": "added",
                "value": "new constraint",
                "reason": "user requested",
            },
        }
        for kind, item in examples.items():
            for field in item:
                with self.subTest(kind=kind, empty_field=field):
                    empty = make_complete_fixture_bundle()
                    empty_item = dict(item)
                    empty_item[field] = "  "
                    empty["feedback_delta"][kind] = [empty_item]
                    self.assertIn(
                        f"feedback_{kind}_value_invalid",
                        validate_bundle(empty)["errors"],
                    )

    def test_feedback_material_refs_resolve_after_schema_change(self):
        bundle = make_complete_fixture_bundle()
        result = validate_bundle(bundle)
        self.assertNotIn("feedback_material_cause_untracked", result["errors"])
        self.assertNotIn("feedback_query_cause_unresolved", result["errors"])

    def test_feedback_query_before_and_after_must_resolve_to_rounds(self):
        before = make_complete_fixture_bundle()
        before["feedback_delta"]["query_changes"][0]["before"] = "not in round one"
        self.assertIn("feedback_before_not_in_round1", validate_bundle(before)["errors"])

        after = make_complete_fixture_bundle()
        after["feedback_delta"]["query_changes"][0]["after"] = "not in round two"
        self.assertIn("feedback_after_not_in_round2", validate_bundle(after)["errors"])

    def test_query_cause_refs_are_closed_and_cover_every_material_item(self):
        reason = make_complete_fixture_bundle()
        reason["feedback_delta"]["added"][0]["reason"] = ""
        self.assertIn(
            "feedback_material_reason_missing", validate_bundle(reason)["errors"]
        )

        for cause_refs in ([], ["feedback_delta.inherited[0]"], ["feedback_delta.added[99]"]):
            with self.subTest(cause_refs=cause_refs):
                bundle = make_complete_fixture_bundle()
                bundle["feedback_delta"]["query_changes"][0]["cause_refs"] = cause_refs
                self.assertIn(
                    "invalid_feedback_query_cause_refs",
                    validate_bundle(bundle)["errors"],
                )

        uncovered = make_complete_fixture_bundle()
        uncovered["feedback_delta"]["query_changes"][0]["cause_refs"] = [
            "feedback_delta.rejected[0]"
        ]
        self.assertIn(
            "feedback_material_cause_untracked", validate_bundle(uncovered)["errors"]
        )

        inherited = make_complete_fixture_bundle()
        inherited["feedback_delta"]["inherited"] = [
            {"object_id": "stable_constraint", "reason": "Still applies"}
        ]
        inherited["feedback_delta"]["query_changes"][0]["cause_refs"].append(
            "feedback_delta.inherited[0]"
        )
        self.assertIn(
            "invalid_feedback_query_cause_refs", validate_bundle(inherited)["errors"]
        )

    def test_modified_query_before_and_after_cannot_be_equal(self):
        bundle = make_complete_fixture_bundle()
        unchanged = "public engineering simulation evidence"
        bundle["round2"]["search_plan"]["queries"][0]["query_text"] = unchanged
        bundle["feedback_delta"]["query_changes"][0]["after"] = unchanged
        result = validate_bundle(bundle)
        self.assertIn("feedback_query_change_noop", result["errors"])

    def test_feedback_before_must_match_same_query_id(self):
        bundle = make_complete_fixture_bundle()
        bundle["feedback_delta"]["query_changes"][0]["query_id"] = "Q1-R1"
        self.assertIn(
            "feedback_after_query_id_mismatch", validate_bundle(bundle)["errors"]
        )

    def test_duplicate_query_id_is_invalid(self):
        bundle = make_complete_fixture_bundle()
        query = json.loads(
            json.dumps(bundle["round2"]["search_plan"]["queries"][0])
        )
        bundle["round2"]["search_plan"]["queries"].append(query)
        self.assertIn("duplicate_query_id", validate_bundle(bundle)["errors"])

    def test_missing_query_text_is_invalid(self):
        bundle = make_complete_fixture_bundle()
        del bundle["round1"]["search_plan"]["queries"][0]["query_text"]
        self.assertIn("query_fields_invalid", validate_bundle(bundle)["errors"])

    def test_query_branch_id_mismatch_is_invalid(self):
        bundle = make_complete_fixture_bundle()
        bundle["round2"]["search_plan"]["branch_id"] = "branch-b"
        self.assertIn("search_plan_branch_mismatch", validate_bundle(bundle)["errors"])

    def test_brief_unknown_field_is_invalid(self):
        bundle = make_complete_fixture_bundle()
        bundle["round1"]["research_brief"]["extra"] = "closed schema"
        self.assertIn("research_brief_fields_invalid", validate_bundle(bundle)["errors"])

    def test_plan_missing_boundary_is_invalid(self):
        bundle = make_complete_fixture_bundle()
        del bundle["round1"]["search_plan"]["source_boundary"]
        self.assertIn("search_plan_fields_invalid", validate_bundle(bundle)["errors"])

    def test_boolean_brief_version_is_invalid(self):
        bundle = make_complete_fixture_bundle()
        bundle["round1"]["research_brief"]["brief_version"] = True
        self.assertIn("invalid_brief_version", validate_bundle(bundle)["errors"])

    def test_round_two_branch_id_mismatch_is_invalid(self):
        bundle = make_complete_fixture_bundle()
        bundle["round2"]["research_brief"]["branch_id"] = "branch-b"
        bundle["round2"]["search_plan"]["branch_id"] = "branch-b"
        self.assertIn("cross_round_branch_mismatch", validate_bundle(bundle)["errors"])

    def test_modified_query_uses_one_stable_id_in_both_rounds(self):
        bundle = make_complete_fixture_bundle()
        self.assertNotIn(
            "feedback_before_query_id_mismatch", validate_bundle(bundle)["errors"]
        )
        bundle["round2"]["search_plan"]["queries"][0]["query_id"] = "Q-NEW"
        self.assertIn(
            "feedback_after_query_id_mismatch", validate_bundle(bundle)["errors"]
        )

    def test_added_query_id_exists_only_in_round_two(self):
        bundle = make_complete_fixture_bundle()
        added_query = json.loads(
            json.dumps(bundle["round2"]["search_plan"]["queries"][0])
        )
        added_query["query_id"] = "Q-ADDED"
        added_query["query_text"] = "new public simulation branch"
        bundle["round2"]["search_plan"]["queries"].append(added_query)
        change = bundle["feedback_delta"]["query_changes"][0]
        change.update(
            {"query_id": "Q-ADDED", "before": "", "after": added_query["query_text"]}
        )
        added_errors = validate_bundle(bundle)["errors"]
        self.assertNotIn("feedback_query_addition_not_explicit", added_errors)
        self.assertNotIn("feedback_after_query_id_mismatch", added_errors)
        bundle["round1"]["search_plan"]["queries"].append(
            json.loads(json.dumps(added_query))
        )
        self.assertIn(
            "feedback_query_addition_not_explicit", validate_bundle(bundle)["errors"]
        )

    def test_removed_query_id_exists_only_in_round_one(self):
        bundle = make_complete_fixture_bundle()
        change = bundle["feedback_delta"]["query_changes"][0]
        change.update(
            {
                "query_id": "Q-STABLE",
                "before": "public engineering simulation evidence",
                "after": "",
            }
        )
        removed_query = bundle["round2"]["search_plan"]["queries"].pop()
        removed_errors = validate_bundle(bundle)["errors"]
        self.assertNotIn("feedback_query_removal_not_explicit", removed_errors)
        self.assertNotIn("feedback_before_query_id_mismatch", removed_errors)
        bundle["round2"]["search_plan"]["queries"].append(removed_query)
        self.assertIn(
            "feedback_query_removal_not_explicit", validate_bundle(bundle)["errors"]
        )

    def test_short_pool_with_visible_search_limit_returns_incomplete(self):
        bundle = make_complete_fixture_bundle()
        bundle.update(
            {
                "terminal_state": "WAITING_FOR_EVIDENCE_DECISION",
                "stopped_after_round": 1,
                "outcome": "evidence_incomplete",
            }
        )
        del bundle["feedback_delta"]
        del bundle["round2"]
        bundle["round1"]["candidate_pool"] = bundle["round1"]["candidate_pool"][:10]
        bundle["round1"]["search_limitations"] = [
            "Only ten eligible fixture records remained"
        ]
        result = validate_bundle(bundle)
        self.assertEqual(result["status"], "evidence_incomplete")
        self.assertIn("round1_candidate_pool_below_target", result["evidence_gaps"])

    def test_short_selection_without_gap_returns_invalid(self):
        bundle = make_complete_fixture_bundle()
        bundle["round1"]["selected_ids"] = bundle["round1"]["selected_ids"][:7]
        result = validate_bundle(bundle)
        self.assertEqual(result["status"], "invalid")
        self.assertIn("selection_count_without_gap", result["errors"])

    def test_short_round_one_allows_only_documented_role_subsets(self):
        bundle = make_complete_fixture_bundle()
        bundle.update(
            {
                "terminal_state": "WAITING_FOR_EVIDENCE_DECISION",
                "stopped_after_round": 1,
                "outcome": "evidence_incomplete",
            }
        )
        del bundle["feedback_delta"]
        del bundle["round2"]
        bundle["round1"]["selected_ids"] = bundle["round1"]["selected_ids"][:7]
        bundle["round1"]["paper_map"] = _paper_map(
            1, bundle["round1"]["selected_ids"]
        )
        bundle["round1"]["evidence_gaps"] = [
            {"role": "counter_limitation", "missing_count": 1}
        ]
        result = validate_bundle(bundle)
        self.assertEqual(result["status"], "evidence_incomplete")
        self.assertNotIn("round1_role_allocation_invalid", result["errors"])

        over_quota = make_complete_fixture_bundle()
        over_quota["round1"]["selected_ids"] = over_quota["round1"]["selected_ids"][:7]
        over_quota["round1"]["paper_map"] = _paper_map(
            1, over_quota["round1"]["selected_ids"]
        )
        over_quota["round1"]["evidence_gaps"] = [
            {"role": "direct_problem", "missing_count": 1}
        ]
        over_quota["round1"]["candidate_pool"][3]["selection_role"] = (
            "direct_problem"
        )
        over_quota["round1"]["candidate_pool"][3]["evidence_roles"].append(
            "direct_problem"
        )
        over_quota["round2"]["round_one_dispositions"] = over_quota["round2"][
            "round_one_dispositions"
        ][:7]
        self.assertIn(
            "round1_role_allocation_invalid", validate_bundle(over_quota)["errors"]
        )

    def test_abstract_edge_claiming_fulltext_returns_invalid(self):
        bundle = make_complete_fixture_bundle()
        bundle["round1"]["paper_map"]["edges"] = [
            {
                "source": "fixture:P01",
                "target": "fixture:P02",
                "relation": "claim_support",
                "basis_level": "fulltext_level",
            }
        ]
        result = validate_bundle(bundle)
        self.assertEqual(result["status"], "invalid")
        self.assertIn("edge_basis_exceeds_source", result["errors"])

    def test_unknown_and_duplicate_candidate_ids_are_invalid(self):
        duplicate = make_complete_fixture_bundle()
        duplicate["round1"]["candidate_pool"][1]["candidate_id"] = "fixture:P01"
        self.assertIn("duplicate_candidate_id", validate_bundle(duplicate)["errors"])

        unknown = make_complete_fixture_bundle()
        unknown["round2"]["selected_ids"][0] = "fixture:P99"
        self.assertIn("unknown_selected_id", validate_bundle(unknown)["errors"])

    def test_duplicate_alternate_id_is_invalid(self):
        bundle = make_structurally_valid_production_bundle()
        first, second = bundle["round1"]["candidate_pool"][:2]
        for candidate in (first, second):
            candidate["verified_record"]["doi"] = None
            candidate["verified_record"]["alternate_id"] = {
                "authority": "arxiv",
                "value": "2401.01234v2",
            }
        second["verified_record"]["title"] = first["verified_record"]["title"]
        second["verified_record"]["authors"] = first["verified_record"]["authors"]
        self.assertIn(
            "duplicate_candidate_identity", validate_bundle(bundle)["errors"]
        )

    def test_duplicate_arxiv_id_with_different_candidate_ids(self):
        bundle = make_structurally_valid_production_bundle()
        first, second = bundle["round1"]["candidate_pool"][:2]
        first["verified_record"]["doi"] = second["verified_record"]["doi"] = None
        first["verified_record"]["alternate_id"] = {
            "authority": "arxiv",
            "value": "2401.01234V2",
        }
        second["verified_record"]["alternate_id"] = {
            "authority": "ArXiv",
            "value": "2401.01234v2",
        }
        second["verified_record"]["title"] = first["verified_record"]["title"]
        second["verified_record"]["authors"] = first["verified_record"]["authors"]
        self.assertIn(
            "duplicate_candidate_identity", validate_bundle(bundle)["errors"]
        )

    def test_equal_alternate_id_conflicting_title_is_blocked(self):
        bundle = make_structurally_valid_production_bundle()
        first, second = bundle["round1"]["candidate_pool"][:2]
        first["verified_record"]["doi"] = second["verified_record"]["doi"] = None
        first["verified_record"]["alternate_id"] = second["verified_record"][
            "alternate_id"
        ] = {"authority": "arxiv", "value": "2401.01234v2"}
        second["verified_record"]["title"] = "A conflicting work identity"
        errors = validate_bundle(bundle)["errors"]
        self.assertIn("candidate_identity_conflict", errors)
        self.assertIn("selected_record_blocked", errors)

    def test_different_alternate_ids_do_not_fallback_to_title_merge(self):
        bundle = make_structurally_valid_production_bundle()
        first, second = bundle["round1"]["candidate_pool"][:2]
        first["verified_record"]["doi"] = second["verified_record"]["doi"] = None
        second["verified_record"]["title"] = first["verified_record"]["title"]
        second["verified_record"]["authors"] = first["verified_record"]["authors"]
        first["verified_record"]["alternate_id"] = {
            "authority": "arxiv",
            "value": "2401.00001",
        }
        second["verified_record"]["alternate_id"] = {
            "authority": "arxiv",
            "value": "2401.00002",
        }
        errors = validate_bundle(bundle)["errors"]
        self.assertNotIn("duplicate_candidate_identity", errors)
        self.assertNotIn("candidate_identity_manual_review", errors)

    def test_title_first_author_match_requires_manual_review(self):
        bundle = make_structurally_valid_production_bundle()
        first, second = bundle["round1"]["candidate_pool"][:2]
        first["verified_record"]["doi"] = second["verified_record"]["doi"] = None
        first["verified_record"]["alternate_id"] = second["verified_record"][
            "alternate_id"
        ] = None
        second["verified_record"]["title"] = first["verified_record"]["title"]
        second["verified_record"]["authors"] = first["verified_record"]["authors"]
        errors = validate_bundle(bundle)["errors"]
        self.assertIn("candidate_identity_manual_review", errors)
        self.assertIn("selected_record_blocked", errors)

    def test_same_doi_with_conflicting_metadata_is_conflicted(self):
        bundle = make_structurally_valid_production_bundle()
        first, second = bundle["round1"]["candidate_pool"][:2]
        first["verified_record"]["doi"] = second["verified_record"][
            "doi"
        ] = "same-contract-token"
        second["verified_record"]["title"] = "A conflicting DOI identity"
        self.assertIn("candidate_identity_conflict", validate_bundle(bundle)["errors"])

    def test_stable_candidate_alternate_id_cannot_change(self):
        bundle = make_structurally_valid_production_bundle()
        for round_name, value in (
            ("round1", "2401.00001"),
            ("round2", "2401.00002"),
        ):
            record = bundle[round_name]["candidate_pool"][0]["verified_record"]
            record["doi"] = None
            record["alternate_id"] = {"authority": "arxiv", "value": value}
        self.assertIn(
            "stable_candidate_identity_changed", validate_bundle(bundle)["errors"]
        )

    def test_unselected_duplicate_identity_is_still_invalid(self):
        bundle = make_structurally_valid_production_bundle()
        first, second = bundle["round1"]["candidate_pool"][8:10]
        for candidate in (first, second):
            record = candidate["verified_record"]
            record["doi"] = None
            record["alternate_id"] = {
                "authority": "contract",
                "value": "unselected-duplicate",
            }
        second["verified_record"]["title"] = first["verified_record"]["title"]
        second["verified_record"]["authors"] = first["verified_record"]["authors"]
        result = validate_bundle(bundle)
        self.assertEqual(result["status"], "invalid")
        self.assertIn("duplicate_candidate_identity", result["errors"])

    def test_different_dois_do_not_fallback_to_equal_alternate_id(self):
        bundle = make_structurally_valid_production_bundle()
        for round_name in ("round1", "round2"):
            first, second = bundle[round_name]["candidate_pool"][:2]
            first_record = first["verified_record"]
            second_record = second["verified_record"]
            first_record["doi"] = "contract-doi-one"
            second_record["doi"] = "contract-doi-two"
            first_record["alternate_id"] = second_record["alternate_id"] = {
                "authority": "arxiv",
                "value": "2401.01234v2",
            }
            second_record["title"] = first_record["title"]
            second_record["authors"] = first_record["authors"]
        errors = validate_bundle(bundle)["errors"]
        self.assertNotIn("duplicate_candidate_identity", errors)
        self.assertNotIn("candidate_identity_conflict", errors)
        self.assertNotIn("candidate_identity_manual_review", errors)

    def test_new_doi_requires_stable_alternate_identity(self):
        stable = make_structurally_valid_production_bundle()
        stable["round1"]["candidate_pool"][0]["verified_record"]["doi"] = None
        stable["round2"]["candidate_pool"][0]["verified_record"][
            "doi"
        ] = "new-contract-doi"
        self.assertNotIn(
            "stable_candidate_identity_unresolved", validate_bundle(stable)["errors"]
        )

        unresolved = make_structurally_valid_production_bundle()
        first = unresolved["round1"]["candidate_pool"][0]["verified_record"]
        second = unresolved["round2"]["candidate_pool"][0]["verified_record"]
        first["doi"] = None
        second["doi"] = "new-contract-doi"
        first["alternate_id"] = second["alternate_id"] = None
        self.assertIn(
            "stable_candidate_identity_unresolved",
            validate_bundle(unresolved)["errors"],
        )

    def test_stable_doi_rejects_removed_alternate_id(self):
        bundle = make_structurally_valid_production_bundle()
        first = bundle["round1"]["candidate_pool"][0]["verified_record"]
        second = bundle["round2"]["candidate_pool"][0]["verified_record"]
        first["doi"] = second["doi"] = "stable-contract-doi"
        second["alternate_id"] = None
        self.assertIn(
            "stable_candidate_identity_changed", validate_bundle(bundle)["errors"]
        )

    def test_stable_doi_rejects_added_alternate_id(self):
        bundle = make_structurally_valid_production_bundle()
        first = bundle["round1"]["candidate_pool"][0]["verified_record"]
        second = bundle["round2"]["candidate_pool"][0]["verified_record"]
        first["doi"] = second["doi"] = "stable-contract-doi"
        first["alternate_id"] = None
        self.assertIn(
            "stable_candidate_identity_changed", validate_bundle(bundle)["errors"]
        )

    def test_stable_alternate_id_rejects_removed_doi(self):
        bundle = make_structurally_valid_production_bundle()
        first = bundle["round1"]["candidate_pool"][0]["verified_record"]
        second = bundle["round2"]["candidate_pool"][0]["verified_record"]
        first["doi"] = "removed-contract-doi"
        second["doi"] = None
        self.assertEqual(first["alternate_id"], second["alternate_id"])
        self.assertIn(
            "stable_candidate_identity_changed", validate_bundle(bundle)["errors"]
        )

    def test_stable_id_preserves_work_identity_across_rounds(self):
        title = make_complete_fixture_bundle()
        title["round2"]["candidate_pool"][0]["verified_record"]["title"] = (
            "A different contract work"
        )
        self.assertIn("stable_candidate_identity_changed", validate_bundle(title)["errors"])

        alternate = make_complete_fixture_bundle()
        alternate["round1"]["candidate_pool"][0]["verified_record"]["alternate_id"] = {
            "authority": "repository",
            "value": "contract-one",
        }
        alternate["round2"]["candidate_pool"][0]["verified_record"]["alternate_id"] = {
            "authority": "repository",
            "value": "contract-two",
        }
        self.assertIn(
            "stable_candidate_identity_changed", validate_bundle(alternate)["errors"]
        )

        doi = make_structurally_valid_production_bundle()
        doi["round1"]["candidate_pool"][0]["verified_record"]["doi"] = "left-token"
        doi["round2"]["candidate_pool"][0]["verified_record"]["doi"] = "right-token"
        self.assertIn("stable_candidate_identity_changed", validate_bundle(doi)["errors"])

    def test_equal_doi_still_requires_consistent_identity_metadata(self):
        mutations = (
            ("title", "Different normalized title"),
            ("authors", ["Second Author", "First Author"]),
            ("publication_type", "different_work_type"),
        )
        for field, value in mutations:
            with self.subTest(field=field):
                bundle = make_structurally_valid_production_bundle()
                first = bundle["round1"]["candidate_pool"][0]["verified_record"]
                second = bundle["round2"]["candidate_pool"][0]["verified_record"]
                first["doi"] = "same-contract-token"
                second["doi"] = "doi:SAME-CONTRACT-TOKEN."
                second[field] = value
                self.assertIn(
                    "stable_candidate_identity_changed",
                    validate_bundle(bundle)["errors"],
                )

        version = make_structurally_valid_production_bundle()
        first = version["round1"]["candidate_pool"][0]["verified_record"]
        second = version["round2"]["candidate_pool"][0]["verified_record"]
        first["doi"] = second["doi"] = "same-contract-token"
        second["verification"]["version_relation"] = "distinct"
        self.assertIn(
            "stable_candidate_identity_changed", validate_bundle(version)["errors"]
        )

    def test_alternate_id_requires_exact_authority_and_value_keys(self):
        cases = (
            {"authority": "repository", "value": "contract-one", "extra": "bad"},
            {"authority": "repository"},
            "repository:contract-one",
        )
        for alternate_id in cases:
            with self.subTest(alternate_id=alternate_id):
                bundle = make_complete_fixture_bundle()
                bundle["round1"]["candidate_pool"][0]["verified_record"][
                    "alternate_id"
                ] = alternate_id
                self.assertIn("invalid_alternate_id", validate_bundle(bundle)["errors"])

    def test_round_one_selection_roles_are_exactly_three_two_two_one(self):
        bundle = make_complete_fixture_bundle()
        bundle["round1"]["candidate_pool"][0]["selection_role"] = "method"
        result = validate_bundle(bundle)
        self.assertIn("round1_role_allocation_invalid", result["errors"])

    def test_map_paper_nodes_must_match_selection(self):
        bundle = make_complete_fixture_bundle()
        bundle["round2"]["paper_map"]["nodes"].pop()
        result = validate_bundle(bundle)
        self.assertIn("map_nodes_do_not_match_selection", result["errors"])

    def test_fixture_records_are_rejected_outside_fixture_mode(self):
        bundle = make_complete_fixture_bundle()
        bundle["fixture_mode"] = False
        result = validate_bundle(bundle)
        self.assertIn("fixture_record_in_production", result["errors"])

    def test_fixture_duplicate_tokens_do_not_become_citation_records(self):
        bundle = make_complete_fixture_bundle()
        bundle["fixture_duplicate_doi_tokens"] = ["doi:10.1234/ONLY-ONE"]
        self.assertEqual(validate_bundle(bundle)["status"], "valid")

    def test_normalize_doi_strips_only_wrappers_whitespace_and_punctuation(self):
        self.assertEqual(normalize_doi(" https://doi.org/10.1000/ABC). "), "10.1000/abc")
        self.assertEqual(normalize_doi("doi:TEST/SHARED."), "test/shared")
        self.assertIsNone(normalize_doi(None))
        self.assertIsNone(normalize_doi("   "))

    def test_dispositions_cover_round_one_exactly_once(self):
        missing = make_complete_fixture_bundle()
        missing["round2"]["round_one_dispositions"].pop()
        self.assertIn("disposition_coverage_mismatch", validate_bundle(missing)["errors"])

        duplicate = make_complete_fixture_bundle()
        duplicate["round2"]["round_one_dispositions"][-1]["round_one_id"] = "fixture:P07"
        self.assertIn("duplicate_round_one_disposition", validate_bundle(duplicate)["errors"])

    def test_disposition_enum_reason_and_cause_are_closed(self):
        cases = (
            ("disposition", "promoted", "invalid_disposition"),
            ("reason", "", "disposition_reason_missing"),
            ("cause_type", "memory", "invalid_disposition_cause"),
            ("cause_ref", "feedback_delta.rejected[99]", "unresolved_disposition_cause_ref"),
        )
        for field, value, expected_error in cases:
            with self.subTest(field=field):
                bundle = make_complete_fixture_bundle()
                bundle["round2"]["round_one_dispositions"][0][field] = value
                self.assertIn(expected_error, validate_bundle(bundle)["errors"])

        inherited = make_complete_fixture_bundle()
        inherited["feedback_delta"]["inherited"] = [
            {"object_id": "stable_constraint", "value": "Still applies"}
        ]
        inherited["round2"]["round_one_dispositions"][0]["cause_ref"] = (
            "feedback_delta.inherited[0]"
        )
        self.assertIn(
            "unresolved_disposition_cause_ref",
            validate_bundle(inherited)["errors"],
        )

    def test_retained_removed_and_downgraded_consistency(self):
        retained = make_complete_fixture_bundle()
        retained["round2"]["round_one_dispositions"][0]["round_two_id"] = "fixture:P02"
        self.assertIn("retained_disposition_conflict", validate_bundle(retained)["errors"])

        removed = make_complete_fixture_bundle()
        removed["round2"]["round_one_dispositions"][6]["round_two_id"] = "fixture:P09"
        self.assertIn("removed_disposition_conflict", validate_bundle(removed)["errors"])

        downgraded = make_complete_fixture_bundle()
        entry = downgraded["round2"]["round_one_dispositions"][0]
        entry["disposition"] = "downgraded"
        entry["round_two_id"] = "fixture:P02"
        self.assertIn("downgraded_disposition_conflict", validate_bundle(downgraded)["errors"])

    def test_downgraded_requires_an_observable_reduction(self):
        unchanged = make_complete_fixture_bundle()
        entry = unchanged["round2"]["round_one_dispositions"][0]
        entry["disposition"] = "downgraded"
        self.assertIn(
            "downgraded_without_observable_change", validate_bundle(unchanged)["errors"]
        )

        reduced = make_complete_fixture_bundle()
        entry = reduced["round2"]["round_one_dispositions"][0]
        entry["disposition"] = "downgraded"
        candidate = reduced["round2"]["candidate_pool"][0]
        candidate["basis_level"] = "metadata_level"
        candidate["verified_record"]["basis_level"] = "metadata_level"
        node = reduced["round2"]["paper_map"]["nodes"][0]
        fallback = reduced["round2"]["paper_map"]["text_fallback"][0]
        node["basis_level"] = "metadata_level"
        fallback["basis_level"] = "metadata_level"
        self.assertEqual(validate_bundle(reduced)["status"], "valid")

    def test_new_evidence_cause_ref_must_target_checked_source(self):
        valid = make_structurally_valid_production_bundle()
        entry = valid["round2"]["round_one_dispositions"][0]
        entry["cause_type"] = "new_evidence"
        entry["cause_ref"] = (
            "round2.candidate_pool[0].verified_record.verification.checked_sources[0]"
        )
        self.assertEqual(validate_bundle(valid)["status"], "valid")

        vague = make_structurally_valid_production_bundle()
        entry = vague["round2"]["round_one_dispositions"][0]
        entry["cause_type"] = "new_evidence"
        entry["cause_ref"] = "round2.candidate_pool[0].verified_record"
        self.assertIn(
            "unresolved_disposition_cause_ref", validate_bundle(vague)["errors"]
        )

    def test_replacement_target_is_unique_and_nonconflicting(self):
        duplicate = make_complete_fixture_bundle()
        duplicate["round2"]["round_one_dispositions"][5]["round_two_id"] = "fixture:P09"
        self.assertIn("duplicate_replacement_target", validate_bundle(duplicate)["errors"])

        retained_conflict = make_complete_fixture_bundle()
        retained_conflict["round2"]["round_one_dispositions"][4]["round_two_id"] = "fixture:P01"
        self.assertIn("replacement_target_conflict", validate_bundle(retained_conflict)["errors"])

    def test_replacement_source_and_target_must_match_round_two_selection(self):
        source_selected = make_complete_fixture_bundle()
        source_selected["round2"]["selected_ids"][4] = "fixture:P05"
        source_selected["round2"]["paper_map"] = _paper_map(
            2, source_selected["round2"]["selected_ids"]
        )
        self.assertIn("replaced_disposition_conflict", validate_bundle(source_selected)["errors"])

        missing_target = make_complete_fixture_bundle()
        missing_target["round2"]["round_one_dispositions"][4]["round_two_id"] = None
        self.assertIn("replaced_disposition_conflict", validate_bundle(missing_target)["errors"])


class ValidateM1BundleCliTests(unittest.TestCase):
    def test_cli_reads_one_utf8_json_and_emits_one_closed_json_result(self):
        script = SCRIPTS_DIR / "validate_m1_bundle.py"
        with tempfile.TemporaryDirectory() as directory:
            fixture_path = Path(directory) / "有效-fixture.json"
            fixture_path.write_text(
                json.dumps(make_complete_fixture_bundle(), ensure_ascii=False),
                encoding="utf-8",
            )
            completed = subprocess.run(
                [sys.executable, str(script), str(fixture_path)],
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(json.loads(completed.stdout)["status"], "valid")
        self.assertEqual(completed.stderr, "")
        self.assertEqual(len(completed.stdout.strip().splitlines()), 1)

    def test_cli_uses_closed_exit_codes_for_invalid_and_incomplete(self):
        script = SCRIPTS_DIR / "validate_m1_bundle.py"
        invalid = make_complete_fixture_bundle()
        invalid["schema_version"] = "m1.0"
        incomplete = make_complete_fixture_bundle()
        incomplete.update(
            {
                "terminal_state": "WAITING_FOR_EVIDENCE_DECISION",
                "stopped_after_round": 1,
                "outcome": "evidence_incomplete",
            }
        )
        del incomplete["feedback_delta"]
        del incomplete["round2"]
        incomplete["round1"]["candidate_pool"] = incomplete["round1"][
            "candidate_pool"
        ][:10]
        incomplete["round1"]["search_limitations"] = [
            "Only ten eligible fixture records remained"
        ]
        with tempfile.TemporaryDirectory() as directory:
            paths = []
            for name, bundle in (("invalid", invalid), ("incomplete", incomplete)):
                path = Path(directory) / f"{name}.json"
                path.write_text(json.dumps(bundle), encoding="utf-8")
                paths.append(path)
            completed = [
                subprocess.run(
                    [sys.executable, str(script), str(path)],
                    check=False,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                )
                for path in paths
            ]
        self.assertEqual([item.returncode for item in completed], [1, 2])
        self.assertEqual(
            [json.loads(item.stdout)["status"] for item in completed],
            ["invalid", "evidence_incomplete"],
        )

    def test_cli_closes_every_malformed_json_shape_without_traceback(self):
        script = SCRIPTS_DIR / "validate_m1_bundle.py"
        with tempfile.TemporaryDirectory() as directory:
            completed = []
            for label, bundle in malformed_bundle_cases():
                path = Path(directory) / f"{label}.json"
                path.write_text(json.dumps(bundle), encoding="utf-8")
                completed.append(
                    subprocess.run(
                        [sys.executable, str(script), str(path)],
                        check=False,
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                    )
                )
        for item in completed:
            self.assertEqual(item.returncode, 1)
            self.assertEqual(item.stderr, "")
            self.assertEqual(len(item.stdout.strip().splitlines()), 1)
            output = json.loads(item.stdout)
            self.assertEqual(output["status"], "invalid")
            self.assertEqual(set(output), {"status", "errors", "evidence_gaps"})


if __name__ == "__main__":
    unittest.main()
