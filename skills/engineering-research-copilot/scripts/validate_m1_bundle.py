#!/usr/bin/env python3
"""Validate one saved M1 calibration bundle without network access."""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from render_m1_map import render_mermaid, render_text_fallback


SCHEMA_VERSION = "m1.2"
TERMINAL_STATES = {"WAITING_FOR_EVIDENCE_DECISION", "M1_COMPLETE"}
OUTCOMES = {"evidence_incomplete", "complete"}
ROOT_REQUIRED_FIELDS = {
    "schema_version",
    "terminal_state",
    "stopped_after_round",
    "outcome",
    "round1",
}
ROOT_OPTIONAL_FIELDS = {"fixture_mode", "evidence_class", "feedback_delta", "round2"}
ROOT_EVIDENCE_FIELDS = {
    "proves",
    "does_not_prove",
    "fixture_duplicate_doi_tokens",
}
BASIS_RANK = {"metadata_level": 0, "abstract_level": 1, "fulltext_level": 2}
BLOCKED_STATES = {"partial", "conflicted", "not_found", "manual_needed"}
ELIGIBLE_STATES = {
    "verified_primary",
    "verified_registry",
    "verified_preprint",
}
REAL_STATES = ELIGIBLE_STATES | BLOCKED_STATES
STATUS_RANK = {
    "verified_primary": 4,
    "verified_registry": 3,
    "verified_preprint": 2,
    "fixture_only": 2,
    "partial": 1,
    "conflicted": 0,
    "not_found": 0,
    "manual_needed": 0,
}
DISPOSITIONS = {"retained", "replaced", "downgraded", "removed"}
CAUSE_TYPES = {"feedback_delta", "new_evidence"}
EVIDENCE_ROLES = [
    "direct_problem",
    "method",
    "transfer_bridge",
    "counter_limitation",
]
BASIS_LEVELS = ["metadata_level", "abstract_level", "fulltext_level"]
EDGE_RELATIONS = {
    "same_problem",
    "shared_method",
    "transfer_bridge",
    "claim_support",
    "claim_tension",
    "same_data_or_benchmark",
}
PAPER_MAP_FIELDS = {
    "round",
    "node_size_basis",
    "legend",
    "nodes",
    "edges",
    "text_fallback",
    "mermaid",
}
PAPER_NODE_FIELDS = {
    "id",
    "node_type",
    "fit_score",
    "evidence_role",
    "verification_status",
    "basis_level",
    "short_note",
}
CLUSTER_NODE_FIELDS = {"id", "node_type", "basis_level", "short_note"}
EDGE_FIELDS = {
    "source",
    "target",
    "relation",
    "strength",
    "confidence",
    "basis_level",
    "note",
}
SOURCE_TYPES = {"doi_registry", "official_repository", "pubmed", "publisher_landing"}
SOURCE_RESULTS = {"match", "conflict", "not_found", "unavailable"}
ELIGIBLE_TITLE_MATCHES = {"exact", "normalized"}
ELIGIBLE_AUTHOR_MATCHES = {"exact", "compatible"}
ROUND_ONE_ROLE_COUNTS = {
    "direct_problem": 3,
    "method": 2,
    "transfer_bridge": 2,
    "counter_limitation": 1,
}
FEEDBACK_FIELDS = {
    "from_brief_version",
    "to_brief_version",
    "inherited",
    "rejected",
    "reset",
    "added",
    "allocation",
    "query_changes",
}
FEEDBACK_ITEM_FIELDS = {
    "inherited": {"object_id", "value"},
    "rejected": {"object_id", "value", "reason"},
    "reset": {"object_id", "previous_value", "reason"},
    "added": {"object_id", "value", "reason"},
}
RESEARCH_BRIEF_FIELDS = {
    "brief_version",
    "branch_id",
    "engineering_object",
    "target_problem",
    "target_metric",
    "available_data",
    "resources",
    "time_budget",
    "preferred_routes",
    "excluded_routes",
    "hard_constraints",
    "soft_preferences",
    "open_questions",
    "evidence_needs",
}
RESEARCH_BRIEF_TEXT_FIELDS = {
    "engineering_object",
    "target_problem",
    "target_metric",
    "time_budget",
}
RESEARCH_BRIEF_LIST_FIELDS = {
    "available_data",
    "resources",
    "preferred_routes",
    "excluded_routes",
    "hard_constraints",
    "soft_preferences",
    "open_questions",
    "evidence_needs",
}
SEARCH_PLAN_FIELDS = {
    "round",
    "brief_version",
    "branch_id",
    "time_boundary",
    "language_boundary",
    "source_boundary",
    "queries",
    "limitations",
}
SEARCH_PLAN_LIST_FIELDS = {
    "time_boundary",
    "language_boundary",
    "source_boundary",
    "limitations",
}
QUERY_FIELDS = {
    "query_id",
    "purpose",
    "query_text",
    "expected_evidence_role",
    "inclusion_terms",
    "exclusion_terms",
}
QUERY_PURPOSES = {
    "direct_problem",
    "method",
    "transfer_bridge",
    "counter_limitation",
}
_DOI_PREFIX = re.compile(
    r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", re.IGNORECASE
)
_PATH_TOKEN = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)|\[(\d+)\]")
_NEW_EVIDENCE_REF = re.compile(
    r"^round2\.candidate_pool\[\d+\]\.verified_record"
    r"\.verification\.checked_sources\[\d+\]$"
)
_FEEDBACK_CAUSE_REF = re.compile(
    r"^feedback_delta\.(?:rejected|reset|added)\[\d+\]$"
)
_QUERY_MATERIAL_REF = re.compile(
    r"^feedback_delta\.(?:rejected|reset|added)\[\d+\]$"
)
_MISSING = object()


def normalize_doi(value: str | None) -> str | None:
    """Normalize a supplied DOI without repairing or inferring it."""

    if value is None or not isinstance(value, str):
        return None
    normalized = value.strip()
    normalized = _DOI_PREFIX.sub("", normalized, count=1)
    normalized = normalized.strip().rstrip(".,;:)]}>").strip()
    return normalized.lower() or None


def normalize_alternate_id(value: Any) -> tuple[str, str] | None:
    """Return one closed, case-insensitive official alternate-ID key."""

    if not isinstance(value, dict) or set(value) != {"authority", "value"}:
        return None
    authority = value.get("authority")
    identifier = value.get("value")
    if not _nonempty_text(authority) or not _nonempty_text(identifier):
        return None
    return authority.strip().casefold(), identifier.strip().casefold()


def normalize_title_first_author(record: dict) -> tuple[str, str] | None:
    """Return the weak title/first-author review key without inferring identity."""

    title = record.get("title")
    authors = record.get("authors")
    if not _nonempty_text(title) or not isinstance(authors, list) or not authors:
        return None
    if not _nonempty_text(authors[0]):
        return None
    normalized_title = " ".join(title.split()).casefold()
    normalized_author = " ".join(authors[0].split()).casefold()
    return normalized_title, normalized_author


class _Result:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.evidence_gaps: list[str] = []

    def error(self, code: str) -> None:
        if code not in self.errors:
            self.errors.append(code)

    def gap(self, code: str) -> None:
        if code not in self.evidence_gaps:
            self.evidence_gaps.append(code)

    def closed(self) -> dict:
        if self.errors:
            status = "invalid"
        elif self.evidence_gaps:
            status = "evidence_incomplete"
        else:
            status = "valid"
        return {
            "status": status,
            "errors": self.errors,
            "evidence_gaps": self.evidence_gaps,
        }


def _as_list(value: Any, result: _Result, error: str) -> list:
    if isinstance(value, list):
        return value
    result.error(error)
    return []


def _nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _valid_checked_at(value: Any) -> bool:
    if not _nonempty_text(value):
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def _checked_source_is_valid(source: Any) -> bool:
    return (
        isinstance(source, dict)
        and set(source) == {"source_type", "canonical_record", "checked_at", "result"}
        and isinstance(source.get("source_type"), str)
        and source.get("source_type") in SOURCE_TYPES
        and isinstance(source.get("result"), str)
        and source.get("result") in SOURCE_RESULTS
        and _nonempty_text(source.get("canonical_record"))
        and _valid_checked_at(source.get("checked_at"))
    )


def _verified_provenance_is_closed(verification: dict) -> bool:
    sources = verification.get("checked_sources")
    return (
        verification.get("status") in ELIGIBLE_STATES
        and verification.get("title_match") in ELIGIBLE_TITLE_MATCHES
        and verification.get("author_match") in ELIGIBLE_AUTHOR_MATCHES
        and verification.get("version_relation")
        in {"same_work", "preprint_of", "distinct"}
        and isinstance(sources, list)
        and bool(sources)
        and all(_checked_source_is_valid(source) for source in sources)
        and any(source.get("result") == "match" for source in sources)
        and not any(source.get("result") in {"conflict", "not_found"} for source in sources)
    )


def _valid_blocking_reasons(value: Any, require_nonempty: bool) -> bool:
    if not isinstance(value, list) or any(
        not _nonempty_text(item) for item in value
    ):
        return False
    return bool(value) if require_nonempty else not value


def _production_eligibility_is_valid(verification: dict) -> bool:
    blocking = verification.get("blocking_reasons")
    return (
        _verified_provenance_is_closed(verification)
        and verification.get("recommendation_eligible") is True
        and _valid_blocking_reasons(blocking, require_nonempty=False)
    )


def _candidate_counts_as_verified(candidate: dict, fixture_mode: bool) -> bool:
    verified = candidate.get("verified_record")
    verification = verified.get("verification") if isinstance(verified, dict) else None
    if not isinstance(verification, dict):
        return False
    if fixture_mode:
        return (
            candidate.get("verification_status") == "fixture_only"
            and verification.get("status") == "fixture_only"
        )
    blocking = verification.get("blocking_reasons")
    eligible = verification.get("recommendation_eligible")
    return (
        candidate.get("verification_status") == verification.get("status")
        and candidate.get("recommendation_eligible") is eligible
        and _verified_provenance_is_closed(verification)
        and (
            (eligible is True and _valid_blocking_reasons(blocking, False))
            or (eligible is False and _valid_blocking_reasons(blocking, True))
        )
    )


def _validate_candidate(
    candidate: Any,
    fixture_mode: bool,
    result: _Result,
) -> tuple[str | None, dict | None]:
    if not isinstance(candidate, dict):
        result.error("invalid_candidate_record")
        return None, None

    candidate_id = candidate.get("candidate_id")
    if not _nonempty_text(candidate_id):
        result.error("invalid_candidate_id")
        return None, candidate

    status = candidate.get("verification_status")
    eligible = candidate.get("recommendation_eligible")
    basis = candidate.get("basis_level")
    evidence_roles = candidate.get("evidence_roles")
    selection_role = candidate.get("selection_role")
    verified = candidate.get("verified_record")
    if not isinstance(eligible, bool):
        result.error("invalid_recommendation_eligibility")
    if basis not in BASIS_RANK:
        result.error("invalid_basis_level")
    if (
        not isinstance(evidence_roles, list)
        or not evidence_roles
        or any(role not in EVIDENCE_ROLES for role in evidence_roles)
    ):
        result.error("invalid_evidence_roles")
    if (
        not isinstance(selection_role, str)
        or selection_role not in EVIDENCE_ROLES
        or not isinstance(evidence_roles, list)
        or selection_role not in evidence_roles
    ):
        result.error("invalid_selection_role")
    if not isinstance(verified, dict):
        result.error("missing_verified_record")
        verified = {}

    verification = verified.get("verification")
    if not isinstance(verification, dict):
        result.error("missing_verification_object")
        verification = {}

    if verified.get("paper_id") != candidate_id:
        result.error("candidate_record_id_mismatch")
    if verification.get("status") != status:
        result.error("candidate_verification_status_mismatch")
    if verification.get("recommendation_eligible") is not eligible:
        result.error("candidate_eligibility_mismatch")
    if verified.get("basis_level") != basis:
        result.error("candidate_basis_mismatch")

    doi = verified.get("doi")
    alternate_id = verified.get("alternate_id")
    authors = verified.get("authors")
    if doi is not None and not isinstance(doi, str):
        result.error("invalid_doi_type")
    if alternate_id is not None and not isinstance(alternate_id, dict):
        result.error("invalid_alternate_id")
    elif isinstance(alternate_id, dict) and (
        set(alternate_id) != {"authority", "value"}
        or
        not _nonempty_text(alternate_id.get("authority"))
        or not _nonempty_text(alternate_id.get("value"))
    ):
        result.error("invalid_alternate_id")
    if not _nonempty_text(verified.get("title")):
        result.error("invalid_verified_title")
    if (
        not isinstance(authors, list)
        or not authors
        or any(not _nonempty_text(author) for author in authors)
    ):
        result.error("invalid_verified_authors")

    is_fixture_id = candidate_id.startswith("fixture:")
    if fixture_mode:
        if not is_fixture_id or status != "fixture_only":
            result.error("fixture_claims_real_verification")
        if any(
            verified.get(field) not in (None, "")
            for field in ("doi", "alternate_id", "canonical_url")
        ):
            result.error("fixture_citation_identifier_present")
        if verification.get("checked_sources") not in ([], None):
            result.error("fixture_claims_real_verification")
    else:
        if is_fixture_id or status == "fixture_only":
            result.error("fixture_record_in_production")
        if status not in REAL_STATES:
            result.error("invalid_verification_status")
        checked_sources = verification.get("checked_sources")
        if status in ELIGIBLE_STATES and (
            not isinstance(checked_sources, list) or not checked_sources
        ):
            result.error("missing_current_checked_sources")
        if isinstance(checked_sources, list):
            if any(not _checked_source_is_valid(source) for source in checked_sources):
                result.error("invalid_checked_source")
        elif checked_sources is not None:
            result.error("invalid_checked_source")
        if eligible is True and not _production_eligibility_is_valid(verification):
            result.error("production_record_not_eligible")
        if status in ELIGIBLE_STATES and not _verified_provenance_is_closed(
            verification
        ):
            result.error("verified_record_identity_not_closed")

    if status in BLOCKED_STATES and eligible is True:
        result.error("blocked_record_marked_eligible")
    if (
        status in ELIGIBLE_STATES
        and eligible is False
        and not _valid_blocking_reasons(
            verification.get("blocking_reasons"), require_nonempty=True
        )
    ):
        result.error("verified_record_ineligible_without_reason")
    return candidate_id, candidate


def _candidate_index(
    round_bundle: dict,
    fixture_mode: bool,
    result: _Result,
) -> tuple[dict[str, dict], list[str], int]:
    candidates = _as_list(
        round_bundle.get("candidate_pool"), result, "invalid_candidate_pool"
    )
    index: dict[str, dict] = {}
    ordered_ids: list[str] = []
    verified_count = 0
    for candidate in candidates:
        candidate_id, record = _validate_candidate(candidate, fixture_mode, result)
        if candidate_id is None or record is None:
            continue
        ordered_ids.append(candidate_id)
        if candidate_id in index:
            result.error("duplicate_candidate_id")
        else:
            index[candidate_id] = record
            if _candidate_counts_as_verified(record, fixture_mode):
                verified_count += 1
    return index, ordered_ids, verified_count


def _validate_selection(
    round_bundle: dict,
    index: dict[str, dict],
    fixture_mode: bool,
    result: _Result,
) -> list[str]:
    selected = _as_list(
        round_bundle.get("selected_ids"), result, "invalid_selected_ids"
    )
    selected_ids: list[str] = []
    for selected_id in selected:
        if not _nonempty_text(selected_id):
            result.error("invalid_selected_id")
            continue
        selected_ids.append(selected_id)
    if len(set(selected_ids)) != len(selected_ids):
        result.error("duplicate_selected_id")

    for selected_id in selected_ids:
        candidate = index.get(selected_id)
        if candidate is None:
            result.error("unknown_selected_id")
            continue
        status = candidate.get("verification_status")
        eligible = candidate.get("recommendation_eligible") is True
        allowed = status == "fixture_only" if fixture_mode else status in ELIGIBLE_STATES
        if not eligible or not allowed or status in BLOCKED_STATES:
            result.error("selected_record_blocked")
    return selected_ids


def _validate_round_count(
    name: str,
    round_bundle: dict,
    verified_candidate_count: int,
    selected_count: int,
    result: _Result,
) -> None:
    reported_gaps = _as_list(
        round_bundle.get("evidence_gaps"), result, "invalid_evidence_gaps"
    )
    limitations = _as_list(
        round_bundle.get("search_limitations"),
        result,
        "invalid_search_limitations",
    )
    has_gap = bool(reported_gaps)

    if name == "round1":
        if verified_candidate_count < 15:
            if limitations:
                result.gap("round1_candidate_pool_below_target")
            else:
                result.error("eligible_candidate_count_without_limit")
        elif verified_candidate_count > 20:
            result.error("candidate_count_out_of_range")
        lower = upper = 8
    else:
        lower, upper = 5, 10

        request_present = "round_two_request" in round_bundle
        request = round_bundle.get("round_two_request")
        valid_request = (
            isinstance(request, dict)
            and set(request) == {"explicit_user_request", "requested_count"}
            and type(request.get("explicit_user_request")) is bool
            and type(request.get("requested_count")) is int
            and request.get("requested_count") == selected_count
        )
        if request_present and not valid_request:
            result.error("invalid_round_two_request")
        if 7 <= selected_count <= 10 and (
            not valid_request or request.get("explicit_user_request") is not True
        ):
            result.error("round_two_expansion_not_authorized")

    if selected_count < lower:
        if has_gap:
            result.gap(f"{name}_selection_below_target")
        else:
            result.error("selection_count_without_gap")
    elif selected_count > upper:
        result.error("selection_count_out_of_range")

    if has_gap:
        result.gap(f"{name}_reported_evidence_gap")


def _validate_round_one_roles(
    selected_ids: list[str],
    index: dict[str, dict],
    round_bundle: dict,
    result: _Result,
) -> None:
    roles = []
    for candidate_id in selected_ids:
        candidate = index.get(candidate_id)
        if isinstance(candidate, dict):
            role = candidate.get("selection_role")
            if isinstance(role, str):
                roles.append(role)
    counts = Counter(roles)
    target = Counter(ROUND_ONE_ROLE_COUNTS)
    if len(roles) != len(selected_ids) or len(selected_ids) > 8:
        result.error("round1_role_allocation_invalid")
        return
    if len(selected_ids) == 8:
        if counts != target:
            result.error("round1_role_allocation_invalid")
        return
    if any(counts[role] > limit for role, limit in ROUND_ONE_ROLE_COUNTS.items()):
        result.error("round1_role_allocation_invalid")
        return

    gaps = round_bundle.get("evidence_gaps")
    documented: dict[str, int] = {}
    if isinstance(gaps, list):
        for gap in gaps:
            if not isinstance(gap, dict):
                continue
            role = gap.get("role")
            missing_count = gap.get("missing_count")
            if role in ROUND_ONE_ROLE_COUNTS and type(missing_count) is int:
                documented[role] = documented.get(role, 0) + missing_count
    for role, limit in ROUND_ONE_ROLE_COUNTS.items():
        missing = limit - counts[role]
        if missing and documented.get(role) != missing:
            result.error("round1_role_gap_missing")


def _validate_map(
    name: str,
    round_number: int,
    round_bundle: dict,
    index: dict[str, dict],
    selected_ids: list[str],
    result: _Result,
) -> None:
    paper_map = round_bundle.get("paper_map")
    if not isinstance(paper_map, dict):
        result.error("invalid_paper_map")
        return
    if set(paper_map) != PAPER_MAP_FIELDS:
        result.error("paper_map_fields_invalid")
    if paper_map.get("round") != round_number:
        result.error("paper_map_round_mismatch")
    if paper_map.get("node_size_basis") != "user_fit":
        result.error("invalid_node_size_basis")

    legend = paper_map.get("legend")
    if not isinstance(legend, dict) or legend.get("evidence_roles") != EVIDENCE_ROLES or legend.get(
        "basis_levels"
    ) != BASIS_LEVELS:
        result.error("invalid_map_legend")

    nodes = _as_list(paper_map.get("nodes"), result, "invalid_map_nodes")
    node_index: dict[str, dict] = {}
    paper_node_ids: list[str] = []
    for node in nodes:
        if not isinstance(node, dict) or not _nonempty_text(node.get("id")):
            result.error("invalid_map_node")
            continue
        node_id = node["id"]
        if node_id in node_index:
            result.error("duplicate_map_node_id")
        else:
            node_index[node_id] = node
        node_type = node.get("node_type")
        expected_node_fields = (
            PAPER_NODE_FIELDS
            if node_type == "paper"
            else CLUSTER_NODE_FIELDS
            if node_type == "cluster"
            else None
        )
        if expected_node_fields is None or set(node) != expected_node_fields:
            result.error("invalid_map_node")
        if not _nonempty_text(node.get("short_note")):
            result.error("invalid_map_node")
        if node.get("basis_level") not in BASIS_RANK:
            result.error("invalid_basis_level")
        if node_type == "paper":
            fit_score = node.get("fit_score")
            if type(fit_score) not in {int, float} or not 0 <= fit_score <= 1:
                result.error("invalid_fit_score")
            paper_node_ids.append(node_id)
            candidate = index.get(node_id)
            if candidate is None:
                result.error("map_contains_unknown_paper")
                continue
            candidate_basis = candidate.get("basis_level")
            node_basis = node.get("basis_level")
            if (
                candidate_basis in BASIS_RANK
                and node_basis in BASIS_RANK
                and BASIS_RANK[node_basis] > BASIS_RANK[candidate_basis]
            ):
                result.error("map_basis_exceeds_source")
            if node.get("verification_status") != candidate.get("verification_status"):
                result.error("map_verification_status_mismatch")
            roles = candidate.get("evidence_roles")
            if not isinstance(roles, list) or node.get("evidence_role") not in roles:
                result.error("map_evidence_role_mismatch")

    if Counter(paper_node_ids) != Counter(selected_ids):
        result.error("map_nodes_do_not_match_selection")

    edges = _as_list(paper_map.get("edges"), result, "invalid_map_edges")
    edge_keys: list[tuple[Any, Any, Any]] = []
    for edge in edges:
        if not isinstance(edge, dict):
            result.error("invalid_map_edge")
            continue
        if set(edge) != EDGE_FIELDS:
            result.error("invalid_map_edge")
        source = edge.get("source")
        target = edge.get("target")
        relation = edge.get("relation")
        if not all(_nonempty_text(value) for value in (source, target, relation)):
            result.error("invalid_map_edge")
            continue
        edge_keys.append((source, target, relation))
        if source not in node_index or target not in node_index:
            result.error("edge_endpoint_missing")
        if relation not in EDGE_RELATIONS:
            result.error("invalid_edge_relation")
        if not all(
            _nonempty_text(edge.get(field))
            for field in ("strength", "confidence", "note")
        ):
            result.error("invalid_map_edge")
        edge_basis = edge.get("basis_level")
        if edge_basis not in BASIS_RANK:
            result.error("invalid_basis_level")
            continue
        paper_endpoints = [
            endpoint
            for endpoint in (source, target)
            if endpoint in index and node_index.get(endpoint, {}).get("node_type") == "paper"
        ]
        if not paper_endpoints:
            result.error("edge_without_paper_support")
        for endpoint in paper_endpoints:
            source_basis = index[endpoint].get("basis_level")
            if (
                source_basis in BASIS_RANK
                and BASIS_RANK[edge_basis] > BASIS_RANK[source_basis]
            ):
                result.error("edge_basis_exceeds_source")
    if len(set(edge_keys)) != len(edge_keys):
        result.error("duplicate_map_edge")

    fallback = _as_list(paper_map.get("text_fallback"), result, "missing_text_fallback")
    fallback_nodes: dict[str, list[dict]] = {}
    fallback_edges: dict[tuple[Any, Any, Any], list[dict]] = {}
    for entry in fallback:
        if not isinstance(entry, dict):
            result.error("invalid_text_fallback")
            continue
        if entry.get("entry_type") == "node":
            entry_id = entry.get("id")
            if not _nonempty_text(entry_id):
                result.error("invalid_text_fallback")
                continue
            fallback_nodes.setdefault(entry_id, []).append(entry)
        elif entry.get("entry_type") == "edge":
            values = (entry.get("source"), entry.get("target"), entry.get("relation"))
            if not all(_nonempty_text(value) for value in values):
                result.error("invalid_text_fallback")
                continue
            key = values
            fallback_edges.setdefault(key, []).append(entry)
        else:
            result.error("invalid_text_fallback")

    if set(fallback_nodes) != set(node_index) or any(
        len(entries) != 1 for entries in fallback_nodes.values()
    ):
        result.error("map_fallback_node_mismatch")
    if set(fallback_edges) != set(edge_keys) or any(
        len(entries) != 1 for entries in fallback_edges.values()
    ):
        result.error("map_fallback_edge_mismatch")

    for node_id, node in node_index.items():
        entries = fallback_nodes.get(node_id, [])
        if len(entries) != 1:
            continue
        entry = entries[0]
        fields = ["node_type", "basis_level"]
        if node.get("node_type") == "paper":
            fields.extend(["evidence_role", "verification_status"])
        if any(entry.get(field) != node.get(field) for field in fields):
            result.error("map_fallback_node_mismatch")
    for edge in edges:
        if not isinstance(edge, dict):
            continue
        key = (edge.get("source"), edge.get("target"), edge.get("relation"))
        entries = fallback_edges.get(key, [])
        if len(entries) == 1 and entries[0].get("basis_level") != edge.get("basis_level"):
            result.error("map_fallback_edge_mismatch")

    try:
        expected_fallback = render_text_fallback(paper_map)
        expected_mermaid = render_mermaid(paper_map)
    except (KeyError, TypeError):
        expected_fallback = _MISSING
        expected_mermaid = _MISSING
    if paper_map.get("text_fallback") != expected_fallback:
        result.error("map_fallback_not_deterministic")
    if paper_map.get("mermaid") != expected_mermaid:
        result.error("map_mermaid_not_deterministic")


def _value_at_ref(bundle: dict, reference: str) -> Any:
    if not isinstance(reference, str):
        return _MISSING
    position = 0
    current: Any = bundle
    for match in _PATH_TOKEN.finditer(reference):
        if match.start() != position and not (
            reference[position : match.start()] == "." and match.group(1)
        ):
            return _MISSING
        position = match.end()
        key, index = match.groups()
        if key is not None:
            if not isinstance(current, dict) or key not in current:
                return _MISSING
            current = current[key]
        else:
            numeric_index = int(index)
            if not isinstance(current, list) or numeric_index >= len(current):
                return _MISSING
            current = current[numeric_index]
    return current if position == len(reference) else _MISSING


def _resolve_ref(bundle: dict, reference: str) -> bool:
    return _value_at_ref(bundle, reference) is not _MISSING


def _validate_research_brief(value: Any, result: _Result) -> dict:
    if not isinstance(value, dict):
        result.error("invalid_research_brief")
        return {}
    if set(value) != RESEARCH_BRIEF_FIELDS:
        result.error("research_brief_fields_invalid")

    brief_version = value.get("brief_version")
    if type(brief_version) is not int or brief_version <= 0:
        result.error("invalid_brief_version")
    if not _nonempty_text(value.get("branch_id")):
        result.error("invalid_brief_branch_id")
    for field in RESEARCH_BRIEF_TEXT_FIELDS:
        if not _nonempty_text(value.get(field)):
            result.error("research_brief_text_invalid")
    for field in RESEARCH_BRIEF_LIST_FIELDS:
        if not isinstance(value.get(field), list):
            result.error("research_brief_list_invalid")
    return value


def _validate_search_plan(
    value: Any,
    expected_round: int,
    brief: dict,
    result: _Result,
) -> dict:
    if not isinstance(value, dict):
        result.error("invalid_search_plan")
        return {}
    if set(value) != SEARCH_PLAN_FIELDS:
        result.error("search_plan_fields_invalid")

    plan_round = value.get("round")
    if type(plan_round) is not int or plan_round != expected_round:
        result.error("search_plan_round_mismatch")
    plan_version = value.get("brief_version")
    if type(plan_version) is not int or plan_version <= 0:
        result.error("invalid_search_plan_brief_version")
    if plan_version != brief.get("brief_version"):
        result.error("search_plan_brief_version_mismatch")
    branch_id = value.get("branch_id")
    if not _nonempty_text(branch_id):
        result.error("invalid_search_plan_branch_id")
    if branch_id != brief.get("branch_id"):
        result.error("search_plan_branch_mismatch")
    for field in SEARCH_PLAN_LIST_FIELDS:
        if not isinstance(value.get(field), list):
            result.error("search_plan_boundary_invalid")

    queries = value.get("queries")
    if not isinstance(queries, list):
        result.error("invalid_search_plan_queries")
        return value
    query_ids: list[str] = []
    for query in queries:
        if not isinstance(query, dict) or set(query) != QUERY_FIELDS:
            result.error("query_fields_invalid")
            continue
        query_id = query.get("query_id")
        if not _nonempty_text(query_id):
            result.error("invalid_query_id")
        else:
            query_ids.append(query_id)
        if not _nonempty_text(query.get("query_text")):
            result.error("invalid_query_text")
        purpose = query.get("purpose")
        if not isinstance(purpose, str) or purpose not in QUERY_PURPOSES:
            result.error("invalid_query_purpose")
        if query.get("expected_evidence_role") not in EVIDENCE_ROLES:
            result.error("invalid_query_evidence_role")
        if not isinstance(query.get("inclusion_terms"), list) or not isinstance(
            query.get("exclusion_terms"), list
        ):
            result.error("invalid_query_terms")
    if len(query_ids) != len(set(query_ids)):
        result.error("duplicate_query_id")
    return value


def _validate_feedback_items(feedback: dict, result: _Result) -> None:
    for kind, expected in FEEDBACK_ITEM_FIELDS.items():
        items = _as_list(feedback.get(kind), result, f"invalid_feedback_{kind}")
        for item in items:
            if not isinstance(item, dict) or set(item) != expected:
                result.error(f"feedback_{kind}_fields_invalid")
                continue
            if any(not _nonempty_text(item[field]) for field in expected):
                result.error(f"feedback_{kind}_value_invalid")


def _validate_feedback(bundle: dict, result: _Result) -> None:
    feedback = bundle.get("feedback_delta")
    if not isinstance(feedback, dict):
        result.error("invalid_feedback_delta")
        return
    if set(feedback) != FEEDBACK_FIELDS:
        result.error("feedback_delta_fields_invalid")
    _validate_feedback_items(feedback, result)

    from_version = feedback.get("from_brief_version")
    to_version = feedback.get("to_brief_version")
    if (
        isinstance(from_version, bool)
        or isinstance(to_version, bool)
        or not isinstance(from_version, int)
        or not isinstance(to_version, int)
        or to_version <= from_version
    ):
        result.error("invalid_feedback_brief_versions")

    rejected = _as_list(feedback.get("rejected"), result, "invalid_feedback_rejected")
    reset = _as_list(feedback.get("reset"), result, "invalid_feedback_reset")
    added = _as_list(feedback.get("added"), result, "invalid_feedback_added")
    _as_list(feedback.get("inherited"), result, "invalid_feedback_inherited")
    allocation = feedback.get("allocation")
    if not isinstance(allocation, dict) or set(allocation) != {"exploit", "explore"}:
        result.error("invalid_feedback_allocation")
    else:
        exploit = allocation.get("exploit")
        explore = allocation.get("explore")
        if (
            isinstance(exploit, bool)
            or isinstance(explore, bool)
            or not isinstance(exploit, int)
            or not isinstance(explore, int)
            or exploit < 0
            or explore < 0
            or exploit + explore != 100
        ):
            result.error("invalid_feedback_allocation")

    query_changes = _as_list(
        feedback.get("query_changes"), result, "invalid_feedback_query_changes"
    )
    if (rejected or reset or added) and not query_changes:
        result.error("feedback_not_applied_to_query")

    round_one = bundle.get("round1")
    round_two = bundle.get("round2")
    plan_one = round_one.get("search_plan") if isinstance(round_one, dict) else None
    plan_two = round_two.get("search_plan") if isinstance(round_two, dict) else None
    queries_one = plan_one.get("queries") if isinstance(plan_one, dict) else []
    queries_two = plan_two.get("queries") if isinstance(plan_two, dict) else []
    if not isinstance(queries_one, list):
        result.error("invalid_round_brief_or_plan")
        queries_one = []
    if not isinstance(queries_two, list):
        result.error("invalid_round_brief_or_plan")
        queries_two = []

    covered_material_refs: set[str] = set()
    for change in query_changes:
        if not isinstance(change, dict):
            result.error("invalid_feedback_query_change")
            continue
        if set(change) != {"query_id", "reason", "cause_refs", "before", "after"}:
            result.error("invalid_feedback_query_change")
        if not _nonempty_text(change.get("reason")):
            result.error("feedback_query_change_reason_missing")
        cause_refs = change.get("cause_refs")
        if not isinstance(cause_refs, list) or not cause_refs:
            result.error("invalid_feedback_query_cause_refs")
        else:
            for cause_ref in cause_refs:
                if (
                    not _nonempty_text(cause_ref)
                    or not _QUERY_MATERIAL_REF.fullmatch(cause_ref)
                    or not _resolve_ref(bundle, cause_ref)
                ):
                    result.error("invalid_feedback_query_cause_refs")
                else:
                    covered_material_refs.add(cause_ref)
        before = change.get("before")
        after = change.get("after")
        query_id = change.get("query_id")
        if (
            not isinstance(before, str)
            or not isinstance(after, str)
            or not _nonempty_text(query_id)
            or not (before.strip() or after.strip())
        ):
            result.error("invalid_feedback_query_change")
            continue

        matching_one = [
            query
            for query in queries_one
            if isinstance(query, dict) and query.get("query_id") == query_id
        ]
        matching_two = [
            query
            for query in queries_two
            if isinstance(query, dict) and query.get("query_id") == query_id
        ]
        if before and (
            len(matching_one) != 1
            or matching_one[0].get("query_text") != before
        ):
            result.error("feedback_before_query_id_mismatch")
            result.error("feedback_before_not_in_round1")
        if before and after and before == after:
            result.error("feedback_query_change_noop")
        if after:
            if len(matching_two) != 1 or matching_two[0].get("query_text") != after:
                result.error("feedback_after_query_id_mismatch")
                result.error("feedback_after_not_in_round2")
                result.error("feedback_query_change_not_implemented")
        if not before:
            if matching_one:
                result.error("feedback_query_addition_not_explicit")
        elif not after:
            if not matching_one or matching_two:
                result.error("feedback_query_removal_not_explicit")

    expected_material_refs: set[str] = set()
    for field, items in (("rejected", rejected), ("reset", reset), ("added", added)):
        for index, item in enumerate(items):
            expected_material_refs.add(f"feedback_delta.{field}[{index}]")
            if not isinstance(item, dict) or not _nonempty_text(item.get("reason")):
                result.error("feedback_material_reason_missing")
                if field == "rejected":
                    result.error("feedback_rejection_reason_missing")
    if not expected_material_refs.issubset(covered_material_refs):
        result.error("feedback_material_cause_untracked")

    if isinstance(round_one, dict) and isinstance(round_two, dict):
        brief_one = round_one.get("research_brief")
        brief_two = round_two.get("research_brief")
        if not all(isinstance(item, dict) for item in (brief_one, brief_two, plan_one, plan_two)):
            result.error("invalid_round_brief_or_plan")
        else:
            if (
                brief_one.get("brief_version") != from_version
                or plan_one.get("brief_version") != from_version
                or brief_two.get("brief_version") != to_version
                or plan_two.get("brief_version") != to_version
            ):
                result.error("feedback_brief_version_mismatch")
            if plan_one.get("round") != 1 or plan_two.get("round") != 2:
                result.error("search_plan_round_mismatch")
            branches = [
                brief_one.get("branch_id"),
                brief_two.get("branch_id"),
                plan_one.get("branch_id"),
                plan_two.get("branch_id"),
            ]
            if not all(_nonempty_text(branch) for branch in branches) or len(
                set(branches)
            ) != 1:
                result.error("cross_round_branch_mismatch")


def _normalize_identity_text(value: str) -> str:
    return " ".join(value.casefold().split())


def _compare_candidate_identity(first: dict, second: dict) -> str:
    """Compare two verified records using the strongest available identity key."""

    first_doi = normalize_doi(first.get("doi"))
    second_doi = normalize_doi(second.get("doi"))
    if first_doi is not None and second_doi is not None:
        return "duplicate" if first_doi == second_doi else "distinct"

    first_alternate = normalize_alternate_id(first.get("alternate_id"))
    second_alternate = normalize_alternate_id(second.get("alternate_id"))
    if first_alternate is not None and second_alternate is not None:
        return "duplicate" if first_alternate == second_alternate else "distinct"

    first_weak_key = normalize_title_first_author(first)
    second_weak_key = normalize_title_first_author(second)
    if first_weak_key is not None and first_weak_key == second_weak_key:
        return "manual_needed"
    return "distinct"


def _identity_metadata_compatible(first: dict, second: dict) -> bool:
    first_title_author = normalize_title_first_author(first)
    second_title_author = normalize_title_first_author(second)
    first_authors = first.get("authors")
    second_authors = second.get("authors")
    first_type = first.get("publication_type")
    second_type = second.get("publication_type")
    first_verification = first.get("verification")
    second_verification = second.get("verification")
    if (
        first_title_author is None
        or second_title_author is None
        or not isinstance(first_authors, list)
        or not isinstance(second_authors, list)
        or not all(_nonempty_text(author) for author in first_authors)
        or not all(_nonempty_text(author) for author in second_authors)
        or not _nonempty_text(first_type)
        or not _nonempty_text(second_type)
        or not isinstance(first_verification, dict)
        or not isinstance(second_verification, dict)
        or not _nonempty_text(first_verification.get("version_relation"))
        or not _nonempty_text(second_verification.get("version_relation"))
    ):
        return False
    return (
        first_title_author[0] == second_title_author[0]
        and tuple(_normalize_identity_text(author) for author in first_authors)
        == tuple(_normalize_identity_text(author) for author in second_authors)
        and _normalize_identity_text(first_type) == _normalize_identity_text(second_type)
        and first_verification.get("version_relation")
        == second_verification.get("version_relation")
    )


def _validate_within_round_identities(
    index: dict[str, dict], selected_ids: list[str], result: _Result
) -> None:
    candidate_ids = list(index)
    selected = set(selected_ids)
    for position, first_id in enumerate(candidate_ids):
        first_candidate = index[first_id]
        first_record = first_candidate.get("verified_record")
        if not isinstance(first_record, dict):
            continue
        for second_id in candidate_ids[position + 1 :]:
            second_candidate = index[second_id]
            second_record = second_candidate.get("verified_record")
            if not isinstance(second_record, dict):
                continue
            identity = _compare_candidate_identity(first_record, second_record)
            related_selected = bool({first_id, second_id} & selected)
            if identity == "duplicate":
                if _identity_metadata_compatible(first_record, second_record):
                    result.error("duplicate_candidate_identity")
                else:
                    result.error("candidate_identity_conflict")
                    if related_selected:
                        result.error("selected_record_blocked")
            elif identity == "manual_needed":
                result.error("candidate_identity_manual_review")
                if related_selected:
                    result.error("selected_record_blocked")


def _stable_candidate_identity(
    first_candidate: dict, second_candidate: dict, fixture_mode: bool
) -> str:
    first = first_candidate.get("verified_record")
    second = second_candidate.get("verified_record")
    if not isinstance(first, dict) or not isinstance(second, dict):
        return "unresolved"
    if not _identity_metadata_compatible(first, second):
        return "changed"

    first_doi = normalize_doi(first.get("doi"))
    second_doi = normalize_doi(second.get("doi"))
    first_alternate = normalize_alternate_id(first.get("alternate_id"))
    second_alternate = normalize_alternate_id(second.get("alternate_id"))

    if (first_alternate is None) != (second_alternate is None):
        return "changed"
    if (
        first_alternate is not None
        and second_alternate is not None
        and first_alternate != second_alternate
    ):
        return "changed"

    if first_doi is not None and second_doi is None:
        return "changed"
    if first_doi is None and second_doi is not None:
        if first_alternate is not None and first_alternate == second_alternate:
            return "same"
        return "unresolved"
    if first_doi is not None and second_doi is not None:
        return "same" if first_doi == second_doi else "changed"

    if first_alternate is not None:
        return "same"

    if fixture_mode and first_doi is None and second_doi is None:
        return "same"
    return "unresolved"


def _validate_stable_identities(
    round_one_index: dict[str, dict],
    round_two_index: dict[str, dict],
    fixture_mode: bool,
    result: _Result,
) -> None:
    for candidate_id in set(round_one_index) & set(round_two_index):
        identity = _stable_candidate_identity(
            round_one_index[candidate_id],
            round_two_index[candidate_id],
            fixture_mode,
        )
        if identity == "changed":
            result.error("stable_candidate_identity_changed")
        elif identity == "unresolved":
            result.error("stable_candidate_identity_unresolved")


def _observable_downgrade(before: Any, after: Any) -> bool:
    if not isinstance(before, dict) or not isinstance(after, dict):
        return False
    if (
        before.get("recommendation_eligible") is True
        and after.get("recommendation_eligible") is False
    ):
        return True
    before_status = before.get("verification_status")
    after_status = after.get("verification_status")
    if (
        before_status in STATUS_RANK
        and after_status in STATUS_RANK
        and STATUS_RANK[after_status] < STATUS_RANK[before_status]
    ):
        return True
    before_basis = before.get("basis_level")
    after_basis = after.get("basis_level")
    if (
        before_basis in BASIS_RANK
        and after_basis in BASIS_RANK
        and BASIS_RANK[after_basis] < BASIS_RANK[before_basis]
    ):
        return True
    before_roles = before.get("evidence_roles")
    after_roles = after.get("evidence_roles")
    if isinstance(before_roles, list) and isinstance(after_roles, list):
        before_set = set(role for role in before_roles if isinstance(role, str))
        after_set = set(role for role in after_roles if isinstance(role, str))
        if after_set < before_set:
            return True
    return False


def _validate_dispositions(
    bundle: dict,
    round_one_selected: list[str],
    round_two_selected: list[str],
    round_one_index: dict[str, dict],
    round_two_index: dict[str, dict],
    result: _Result,
) -> None:
    round_two = bundle.get("round2")
    dispositions = _as_list(
        round_two.get("round_one_dispositions") if isinstance(round_two, dict) else None,
        result,
        "invalid_round_one_dispositions",
    )
    round_one_ids = [
        entry.get("round_one_id") if isinstance(entry, dict) else None
        for entry in dispositions
    ]
    counts = Counter(round_one_ids)
    if any(count > 1 for count in counts.values()):
        result.error("duplicate_round_one_disposition")
    if counts != Counter(round_one_selected):
        result.error("disposition_coverage_mismatch")

    selected_two = set(round_two_selected)
    replacement_targets: list[str] = []
    retained_or_downgraded_targets: set[str] = set()
    for entry in dispositions:
        if not isinstance(entry, dict):
            result.error("invalid_round_one_disposition")
            continue
        round_one_id = entry.get("round_one_id")
        disposition = entry.get("disposition")
        round_two_id = entry.get("round_two_id")
        if not isinstance(disposition, str) or disposition not in DISPOSITIONS:
            result.error("invalid_disposition")
        if not _nonempty_text(entry.get("reason")):
            result.error("disposition_reason_missing")

        cause_type = entry.get("cause_type")
        cause_ref = entry.get("cause_ref")
        if cause_type not in CAUSE_TYPES or not _nonempty_text(cause_ref):
            result.error("invalid_disposition_cause")
        elif cause_type == "feedback_delta":
            if not _FEEDBACK_CAUSE_REF.fullmatch(cause_ref) or not _resolve_ref(bundle, cause_ref):
                result.error("unresolved_disposition_cause_ref")
        elif not _NEW_EVIDENCE_REF.fullmatch(cause_ref) or not _resolve_ref(bundle, cause_ref):
            result.error("unresolved_disposition_cause_ref")
        else:
            source = _value_at_ref(bundle, cause_ref)
            if not _checked_source_is_valid(source):
                result.error("unresolved_disposition_cause_ref")

        if disposition == "retained":
            if round_two_id != round_one_id or round_one_id not in selected_two:
                result.error("retained_disposition_conflict")
            if isinstance(round_two_id, str):
                retained_or_downgraded_targets.add(round_two_id)
        elif disposition == "replaced":
            if (
                not _nonempty_text(round_two_id)
                or round_one_id in selected_two
                or round_two_id == round_one_id
                or round_two_id not in selected_two
                or round_two_id not in round_two_index
            ):
                result.error("replaced_disposition_conflict")
            if isinstance(round_two_id, str):
                replacement_targets.append(round_two_id)
        elif disposition == "downgraded":
            if round_two_id is None:
                if round_one_id in selected_two or round_one_id not in round_two_index:
                    result.error("downgraded_disposition_conflict")
            elif round_two_id != round_one_id or round_one_id not in selected_two:
                result.error("downgraded_disposition_conflict")
            else:
                candidate = round_two_index.get(round_one_id)
                if candidate is None or candidate.get("recommendation_eligible") is not True:
                    result.error("downgraded_disposition_conflict")
                retained_or_downgraded_targets.add(round_two_id)
            before = round_one_index.get(round_one_id)
            after = round_two_index.get(round_one_id)
            if not _observable_downgrade(before, after):
                result.error("downgraded_without_observable_change")
        elif disposition == "removed":
            if round_two_id is not None or round_one_id in selected_two:
                result.error("removed_disposition_conflict")

    if len(set(replacement_targets)) != len(replacement_targets):
        result.error("duplicate_replacement_target")
    if set(replacement_targets) & retained_or_downgraded_targets:
        result.error("replacement_target_conflict")


def _validate_duplicate_dois(
    bundle: dict,
    round_indexes: list[dict[str, dict]],
    result: _Result,
) -> None:
    doi_owners: dict[str, str] = {}
    candidate_dois: dict[str, str] = {}
    for index in round_indexes:
        for candidate_id, candidate in index.items():
            verified = candidate.get("verified_record")
            raw_doi = verified.get("doi") if isinstance(verified, dict) else None
            if raw_doi is not None and not isinstance(raw_doi, str):
                result.error("invalid_doi_type")
                continue
            doi = normalize_doi(raw_doi)
            if doi is None:
                continue
            previous_for_candidate = candidate_dois.get(candidate_id)
            if previous_for_candidate is not None and previous_for_candidate != doi:
                result.error("stable_candidate_doi_changed")
            candidate_dois[candidate_id] = doi
            previous_owner = doi_owners.get(doi)
            if previous_owner is not None and previous_owner != candidate_id:
                result.error("duplicate_normalized_doi")
            doi_owners[doi] = candidate_id

    fixture_tokens = bundle.get("fixture_duplicate_doi_tokens", [])
    if not isinstance(fixture_tokens, list):
        result.error("invalid_fixture_duplicate_doi_tokens")
        return
    normalized_tokens = [
        normalized
        for token in fixture_tokens
        if isinstance(token, str) and (normalized := normalize_doi(token)) is not None
    ]
    if len(normalized_tokens) != len(set(normalized_tokens)):
        result.error("duplicate_normalized_doi")


def _validate_root_contract(
    bundle: dict, result: _Result
) -> tuple[int | None, str | None, str | None]:
    unknown = (
        set(bundle) - ROOT_REQUIRED_FIELDS - ROOT_OPTIONAL_FIELDS - ROOT_EVIDENCE_FIELDS
    )
    if unknown or not ROOT_REQUIRED_FIELDS.issubset(bundle):
        result.error("root_fields_invalid")
    if bundle.get("schema_version") != SCHEMA_VERSION:
        result.error("invalid_schema_version")

    stopped = bundle.get("stopped_after_round")
    terminal = bundle.get("terminal_state")
    outcome = bundle.get("outcome")
    if type(stopped) is not int or stopped not in {1, 2}:
        result.error("invalid_stopped_after_round")
    if terminal not in TERMINAL_STATES:
        result.error("invalid_terminal_state")
    if outcome not in OUTCOMES:
        result.error("invalid_outcome")
    return stopped if type(stopped) is int else None, terminal, outcome


def _validate_terminal_state_consistency(
    stopped: int | None,
    terminal: str | None,
    outcome: str | None,
    round_two_ready: bool,
    result: _Result,
) -> None:
    expected = {
        (1, "evidence_incomplete"): "WAITING_FOR_EVIDENCE_DECISION",
        (2, "evidence_incomplete"): "WAITING_FOR_EVIDENCE_DECISION",
        (2, "complete"): "M1_COMPLETE",
    }
    if expected.get((stopped, outcome)) != terminal:
        result.error("terminal_state_inconsistent")
    if terminal == "M1_COMPLETE" and not round_two_ready:
        result.error("complete_terminal_state_without_ready_round_two")


def _validate_round(
    name: str,
    number: int,
    bundle: dict,
    fixture_mode: bool,
    result: _Result,
) -> tuple[dict, dict[str, dict], list[str], int]:
    round_bundle = bundle.get(name)
    if not isinstance(round_bundle, dict):
        result.error(f"missing_{name}")
        round_bundle = {}
    if round_bundle.get("schema_version") != SCHEMA_VERSION:
        result.error("invalid_schema_version")
    if round_bundle.get("round") != number:
        result.error("round_number_mismatch")
    if name == "round1" and "round_two_request" in round_bundle:
        result.error("round_two_request_in_round_one")
    brief = _validate_research_brief(round_bundle.get("research_brief"), result)
    _validate_search_plan(round_bundle.get("search_plan"), number, brief, result)
    index, _ordered_ids, verified_count = _candidate_index(
        round_bundle, fixture_mode, result
    )
    selected_ids = _validate_selection(round_bundle, index, fixture_mode, result)
    _validate_within_round_identities(index, selected_ids, result)
    _validate_round_count(name, round_bundle, verified_count, len(selected_ids), result)
    if name == "round1":
        _validate_round_one_roles(selected_ids, index, round_bundle, result)
    _validate_map(name, number, round_bundle, index, selected_ids, result)
    return round_bundle, index, selected_ids, verified_count


def _validate_bundle(bundle: dict) -> dict:
    result = _Result()
    if not isinstance(bundle, dict):
        result.error("invalid_bundle")
        return result.closed()
    stopped, terminal, outcome = _validate_root_contract(bundle, result)

    raw_fixture_mode = bundle.get("fixture_mode", False)
    if not isinstance(raw_fixture_mode, bool):
        result.error("invalid_fixture_mode")
        fixture_mode = False
    else:
        fixture_mode = raw_fixture_mode
    if fixture_mode and bundle.get("evidence_class") != "offline_contract_fixture":
        result.error("invalid_fixture_evidence_class")

    round_one = _validate_round("round1", 1, bundle, fixture_mode, result)
    round_one_gaps = round_one[0].get("evidence_gaps")
    round_one_ready = (
        round_one[3] >= 15
        and len(round_one[2]) == 8
        and isinstance(round_one_gaps, list)
        and not round_one_gaps
    )
    round_two_ready = False

    if stopped == 1:
        if "feedback_delta" in bundle or "round2" in bundle:
            result.error("round_two_fields_after_round_one_stop")
        _validate_duplicate_dois(bundle, [round_one[1]], result)
    elif stopped == 2:
        if "feedback_delta" not in bundle:
            result.error("missing_feedback_delta")
        else:
            _validate_feedback(bundle, result)
        if "round2" not in bundle:
            result.error("missing_round2")
        round_two = _validate_round("round2", 2, bundle, fixture_mode, result)
        round_two_gaps = round_two[0].get("evidence_gaps")
        round_two_ready = (
            round_one_ready
            and 5 <= len(round_two[2]) <= 10
            and isinstance(round_two_gaps, list)
            and not round_two_gaps
        )
        _validate_duplicate_dois(bundle, [round_one[1], round_two[1]], result)
        _validate_stable_identities(
            round_one[1], round_two[1], fixture_mode, result
        )
        _validate_dispositions(
            bundle,
            round_one[2],
            round_two[2],
            round_one[1],
            round_two[1],
            result,
        )

    if outcome == "evidence_incomplete" and not result.evidence_gaps:
        result.error("evidence_incomplete_without_gap")
    _validate_terminal_state_consistency(
        stopped, terminal, outcome, round_two_ready, result
    )
    return result.closed()


def validate_bundle(bundle: dict) -> dict:
    """Return status, errors, and evidence_gaps without performing I/O."""

    try:
        return _validate_bundle(bundle)
    except Exception:
        return _closed_cli_error("malformed_bundle")


def _closed_cli_error(code: str) -> dict:
    return {"status": "invalid", "errors": [code], "evidence_gaps": []}


def main(argv: list[str] | None = None) -> int:
    """Read one JSON bundle, print one JSON result, and return 0, 1, or 2."""

    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) != 1:
        output = _closed_cli_error("expected_one_json_path")
    else:
        try:
            payload = json.loads(Path(arguments[0]).read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            output = _closed_cli_error("unreadable_or_invalid_json")
        else:
            output = validate_bundle(payload)
    print(json.dumps(output, ensure_ascii=False, separators=(",", ":")))
    return {"valid": 0, "invalid": 1, "evidence_incomplete": 2}[output["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
