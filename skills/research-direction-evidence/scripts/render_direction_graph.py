"""Validate and render deterministic offline research-direction graphs."""

from __future__ import annotations

import argparse
import copy
import html
import json
import math
import textwrap
from collections import defaultdict
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "direction-graph.v1"
RELEVANCE_BASIS = "current_brief_fit"
TOP_LEVEL_FIELDS = {
    "schema_version",
    "graph_id",
    "title",
    "relevance_basis",
    "root_id",
    "nodes",
    "edges",
}
NODE_FIELDS = {
    "id",
    "node_type",
    "portfolio_role",
    "label",
    "summary",
    "parent_id",
    "relevance",
    "evidence_basis",
    "verification_status",
    "status",
    "source_refs",
    "details",
}
EDGE_FIELDS = {
    "id",
    "source",
    "target",
    "relation",
    "strength",
    "basis",
    "evidence_basis",
    "label",
}
NODE_TYPES = {
    "research_problem",
    "direction",
    "claim",
    "evidence",
    "user_material",
    "risk",
    "unknown",
    "minimum_test",
    "constraint",
    "data",
}
PORTFOLIO_ROLES = {
    "root_problem",
    "provisional_main",
    "adjacent_alternative",
    "transfer_exploration",
    "high_risk",
    "not_applicable",
}
EVIDENCE_BASES = {
    "user_material",
    "metadata_level",
    "abstract_level",
    "fulltext_level",
    "analysis_only",
    "not_applicable",
}
VERIFICATION_STATUSES = {
    "user_provided",
    "verified_identity",
    "derived",
    "unverified",
    "conflicted",
    "not_applicable",
}
NODE_STATUSES = {"admissible", "hypothesis", "unresolved", "blocked", "rejected"}
RELATIONS = {
    "contains",
    "supports",
    "contradicts",
    "tensions",
    "transfers",
    "constrains",
    "tests",
    "depends_on",
    "derives_from",
    "uses_data",
}
EDGE_BASES = {"explicit", "inferred", "transfer_hypothesis"}
EXTERNAL_CONTENT_BASES = {"metadata_level", "abstract_level", "fulltext_level"}

NODE_COLORS = {
    "research_problem": "#1F4E6B",
    "direction": "#2F6B8A",
    "claim": "#4D7C8A",
    "evidence": "#3F7D57",
    "user_material": "#597A9B",
    "risk": "#9B4A47",
    "unknown": "#777777",
    "minimum_test": "#6B5A9A",
    "constraint": "#9A6A2F",
    "data": "#397A78",
}
EVIDENCE_STROKES = {
    "user_material": "#79B8E8",
    "metadata_level": "#A9A9A9",
    "abstract_level": "#F2C14E",
    "fulltext_level": "#55C271",
    "analysis_only": "#B58BE2",
    "not_applicable": "#D8D8D8",
}
RELATION_COLORS = {
    "contains": "#8B98A3",
    "supports": "#3C9D5D",
    "contradicts": "#D64F4F",
    "tensions": "#D8872F",
    "transfers": "#8A63C7",
    "constrains": "#B07A35",
    "tests": "#397FC0",
    "depends_on": "#667788",
    "derives_from": "#6E8797",
    "uses_data": "#287E7B",
}


def _is_nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_unit_number(value: Any) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value) and 0 <= value <= 1


def validate_graph(graph: Any) -> list[str]:
    """Return stable error codes for one closed direction-graph object."""

    errors: list[str] = []
    if not isinstance(graph, dict):
        return ["graph_not_object"]
    if set(graph) != TOP_LEVEL_FIELDS:
        errors.append("graph_fields_invalid")
    if graph.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version_invalid")
    if graph.get("relevance_basis") != RELEVANCE_BASIS:
        errors.append("relevance_basis_invalid")
    for field in ("graph_id", "title", "root_id"):
        if not _is_nonempty_text(graph.get(field)):
            errors.append(f"{field}_invalid")

    nodes = graph.get("nodes")
    edges = graph.get("edges")
    if not isinstance(nodes, list) or not nodes:
        errors.append("nodes_invalid")
        nodes = []
    if not isinstance(edges, list):
        errors.append("edges_invalid")
        edges = []

    node_by_id: dict[str, dict[str, Any]] = {}
    direction_roles: list[str] = []
    for index, node in enumerate(nodes):
        prefix = f"node_{index}"
        if not isinstance(node, dict):
            errors.append(f"{prefix}_not_object")
            continue
        if set(node) != NODE_FIELDS:
            errors.append(f"{prefix}_fields_invalid")
        node_id = node.get("id")
        if not _is_nonempty_text(node_id):
            errors.append(f"{prefix}_id_invalid")
        elif node_id in node_by_id:
            errors.append("duplicate_node_id")
        else:
            node_by_id[node_id] = node
        for field in ("label", "summary"):
            if not _is_nonempty_text(node.get(field)):
                errors.append(f"{prefix}_{field}_invalid")
        parent_id = node.get("parent_id")
        if parent_id is not None and not _is_nonempty_text(parent_id):
            errors.append(f"{prefix}_parent_id_invalid")
        if node.get("node_type") not in NODE_TYPES:
            errors.append(f"{prefix}_node_type_invalid")
        role = node.get("portfolio_role")
        if role not in PORTFOLIO_ROLES:
            errors.append(f"{prefix}_portfolio_role_invalid")
        elif node.get("node_type") == "research_problem" and role != "root_problem":
            errors.append(f"{prefix}_root_role_invalid")
        elif node.get("node_type") == "direction":
            if role not in {
                "provisional_main",
                "adjacent_alternative",
                "transfer_exploration",
                "high_risk",
            }:
                errors.append(f"{prefix}_direction_role_invalid")
            else:
                direction_roles.append(role)
        elif node.get("node_type") != "research_problem" and role != "not_applicable":
            errors.append(f"{prefix}_non_direction_role_invalid")
        if not _is_unit_number(node.get("relevance")):
            errors.append(f"{prefix}_relevance_invalid")
        if node.get("evidence_basis") not in EVIDENCE_BASES:
            errors.append(f"{prefix}_evidence_basis_invalid")
        if node.get("verification_status") not in VERIFICATION_STATUSES:
            errors.append(f"{prefix}_verification_status_invalid")
        if node.get("status") not in NODE_STATUSES:
            errors.append(f"{prefix}_status_invalid")
        for field in ("source_refs", "details"):
            values = node.get(field)
            if not isinstance(values, list) or not all(_is_nonempty_text(value) for value in values):
                errors.append(f"{prefix}_{field}_invalid")
        if (
            node.get("node_type") == "evidence"
            and node.get("evidence_basis") in EXTERNAL_CONTENT_BASES
            and (
                node.get("verification_status") != "verified_identity"
                or not node.get("source_refs")
            )
        ):
            errors.append(f"{prefix}_external_evidence_unverified")
        if node.get("verification_status") == "conflicted" and node.get("status") == "admissible":
            errors.append(f"{prefix}_conflicted_admissible")

    root_id = graph.get("root_id")
    root = node_by_id.get(root_id)
    if root is None:
        errors.append("root_missing")
    elif root.get("node_type") != "research_problem" or root.get("parent_id") is not None:
        errors.append("root_invalid")

    for formal_role in (
        "provisional_main",
        "adjacent_alternative",
        "transfer_exploration",
    ):
        if direction_roles.count(formal_role) != 1:
            errors.append(f"formal_direction_role_count_invalid:{formal_role}")
    if direction_roles.count("high_risk") > 2:
        errors.append("high_risk_direction_count_invalid")

    for node_id, node in node_by_id.items():
        if node_id == root_id:
            continue
        parent_id = node.get("parent_id")
        if parent_id not in node_by_id:
            errors.append(f"node_parent_missing:{node_id}")
            continue
        seen = {node_id}
        cursor = parent_id
        while cursor is not None and cursor in node_by_id:
            if cursor in seen:
                errors.append(f"hierarchy_cycle:{node_id}")
                break
            seen.add(cursor)
            cursor = node_by_id[cursor].get("parent_id")
        else:
            if cursor is not None:
                continue
            if root_id not in seen:
                errors.append(f"node_not_rooted:{node_id}")

    edge_ids: set[str] = set()
    for index, edge in enumerate(edges):
        prefix = f"edge_{index}"
        if not isinstance(edge, dict):
            errors.append(f"{prefix}_not_object")
            continue
        if set(edge) != EDGE_FIELDS:
            errors.append(f"{prefix}_fields_invalid")
        edge_id = edge.get("id")
        if not _is_nonempty_text(edge_id):
            errors.append(f"{prefix}_id_invalid")
        elif edge_id in edge_ids:
            errors.append("duplicate_edge_id")
        else:
            edge_ids.add(edge_id)
        source = edge.get("source")
        target = edge.get("target")
        if source not in node_by_id or target not in node_by_id:
            errors.append(f"{prefix}_endpoint_missing")
        elif source == target:
            errors.append(f"{prefix}_self_edge")
        if edge.get("relation") not in RELATIONS:
            errors.append(f"{prefix}_relation_invalid")
        if not _is_unit_number(edge.get("strength")):
            errors.append(f"{prefix}_strength_invalid")
        if edge.get("basis") not in EDGE_BASES:
            errors.append(f"{prefix}_basis_invalid")
        if edge.get("evidence_basis") not in EVIDENCE_BASES:
            errors.append(f"{prefix}_evidence_basis_invalid")
        if not _is_nonempty_text(edge.get("label")):
            errors.append(f"{prefix}_label_invalid")

    return sorted(set(errors))


def _depths(graph: dict[str, Any]) -> dict[str, int]:
    node_by_id = {node["id"]: node for node in graph["nodes"]}
    depths: dict[str, int] = {}
    for node in graph["nodes"]:
        depth = 0
        cursor = node
        while cursor["parent_id"] is not None:
            depth += 1
            cursor = node_by_id[cursor["parent_id"]]
        depths[node["id"]] = depth
    return depths


def _node_area(relevance: float) -> float:
    """Map relevance linearly to rendered area, not radius."""

    return 1800.0 + relevance * 7200.0


def _node_radius(relevance: float) -> float:
    return math.sqrt(_node_area(relevance) / math.pi)


def _layout(graph: dict[str, Any]) -> tuple[dict[str, tuple[float, float]], float, float]:
    depths = _depths(graph)
    by_depth: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for node in graph["nodes"]:
        by_depth[depths[node["id"]]].append(node)
    max_depth = max(by_depth, default=0)
    max_count = max((len(nodes) for nodes in by_depth.values()), default=1)
    width = max(900.0, 260.0 + max_depth * 340.0)
    height = max(680.0, 180.0 + max_count * 150.0)
    positions: dict[str, tuple[float, float]] = {}
    for depth in range(max_depth + 1):
        nodes = by_depth.get(depth, [])
        if not nodes:
            continue
        x = 120.0 + depth * 340.0
        band = height / (len(nodes) + 1)
        for index, node in enumerate(nodes, start=1):
            positions[node["id"]] = (x, band * index)
    return positions, width, height


def _label_lines(label: str) -> list[str]:
    if " " in label.strip():
        lines = textwrap.wrap(label, width=18, break_long_words=True, break_on_hyphens=False)
    else:
        lines = textwrap.wrap(label, width=10, break_long_words=True, break_on_hyphens=False)
    return lines[:3] or [label]


def render_text_fallback(graph: dict[str, Any]) -> str:
    """Render all structured facts in source order."""

    errors = validate_graph(graph)
    if errors:
        raise ValueError("invalid direction graph: " + ",".join(errors))
    lines = [
        graph["title"],
        f'graph_id={graph["graph_id"]}; relevance_basis={graph["relevance_basis"]}; root_id={graph["root_id"]}',
        "NODES",
    ]
    for node in graph["nodes"]:
        refs = ",".join(node["source_refs"]) if node["source_refs"] else "none"
        details = " | ".join(node["details"]) if node["details"] else "none"
        parent = node["parent_id"] if node["parent_id"] is not None else "none"
        lines.append(
            f'{node["id"]} | parent={parent} | type={node["node_type"]} | '
            f'role={node["portfolio_role"]} | '
            f'relevance={node["relevance"]:.3f} | evidence={node["evidence_basis"]} | '
            f'verification={node["verification_status"]} | status={node["status"]} | '
            f'label={node["label"]} | summary={node["summary"]} | refs={refs} | details={details}'
        )
    lines.append("EDGES")
    for edge in graph["edges"]:
        lines.append(
            f'{edge["id"]} | {edge["source"]} --{edge["relation"]}--> {edge["target"]} | '
            f'strength={edge["strength"]:.3f} | basis={edge["basis"]} | '
            f'evidence={edge["evidence_basis"]} | label={edge["label"]}'
        )
    return "\n".join(lines) + "\n"


def _safe_json_for_html(graph: dict[str, Any]) -> str:
    payload = json.dumps(graph, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return payload.replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")


def render_html(graph: dict[str, Any]) -> str:
    """Render a deterministic self-contained interactive HTML/SVG artifact."""

    errors = validate_graph(graph)
    if errors:
        raise ValueError("invalid direction graph: " + ",".join(errors))
    source = copy.deepcopy(graph)
    positions, width, height = _layout(source)
    hierarchy_markup: list[str] = []
    for node in source["nodes"]:
        if node["parent_id"] is None:
            continue
        x1, y1 = positions[node["parent_id"]]
        x2, y2 = positions[node["id"]]
        control = max(55.0, abs(x2 - x1) * 0.45)
        path = f"M {x1:.1f} {y1:.1f} C {x1 + control:.1f} {y1:.1f}, {x2 - control:.1f} {y2:.1f}, {x2:.1f} {y2:.1f}"
        hierarchy_markup.append(
            f'<path class="hierarchy-edge" data-source="{html.escape(node["parent_id"], quote=True)}" '
            f'data-target="{html.escape(node["id"], quote=True)}" d="{path}" />'
        )

    edge_markup: list[str] = []
    for edge in source["edges"]:
        x1, y1 = positions[edge["source"]]
        x2, y2 = positions[edge["target"]]
        control = max(55.0, abs(x2 - x1) * 0.45)
        path = f"M {x1:.1f} {y1:.1f} C {x1 + control:.1f} {y1:.1f}, {x2 - control:.1f} {y2:.1f}, {x2:.1f} {y2:.1f}"
        dash = ' stroke-dasharray="9 7"' if edge["basis"] in {"inferred", "transfer_hypothesis"} else ""
        label = html.escape(edge["label"], quote=True)
        aria = html.escape(
            f'{edge["source"]} {edge["relation"]} {edge["target"]}: {edge["label"]}',
            quote=True,
        )
        edge_markup.append(
            f'<path id="edge-{html.escape(edge["id"], quote=True)}" class="edge" '
            f'data-edge-id="{html.escape(edge["id"], quote=True)}" '
            f'data-source="{html.escape(edge["source"], quote=True)}" '
            f'data-target="{html.escape(edge["target"], quote=True)}" '
            f'data-relation="{edge["relation"]}" tabindex="0" role="button" '
            f'aria-label="{aria}" d="{path}" fill="none" '
            f'stroke="{RELATION_COLORS[edge["relation"]]}" '
            f'stroke-width="{1.0 + edge["strength"] * 5.0:.2f}"{dash} marker-end="url(#arrow)">'
            f'<title>{label}</title></path>'
        )

    node_markup: list[str] = []
    for node in source["nodes"]:
        x, y = positions[node["id"]]
        radius = _node_radius(node["relevance"])
        status_dash = ' stroke-dasharray="7 5"' if node["status"] in {"hypothesis", "unresolved", "blocked", "rejected"} else ""
        opacity = "0.55" if node["status"] in {"blocked", "rejected"} else "1"
        label = html.escape(node["label"])
        aria = html.escape(
            f'{node["label"]}; type {node["node_type"]}; relevance {node["relevance"]:.2f}; '
            f'evidence {node["evidence_basis"]}; status {node["status"]}',
            quote=True,
        )
        tspans: list[str] = []
        label_lines = _label_lines(node["label"])
        start = -((len(label_lines) - 1) * 8)
        for index, line in enumerate(label_lines):
            dy = start if index == 0 else 16
            tspans.append(f'<tspan x="{x:.1f}" dy="{dy}">{html.escape(line)}</tspan>')
        node_markup.append(
            f'<g id="node-{html.escape(node["id"], quote=True)}" class="node" '
            f'data-node-id="{html.escape(node["id"], quote=True)}" '
            f'data-node-type="{node["node_type"]}" data-role="{node["portfolio_role"]}" '
            f'data-evidence="{node["evidence_basis"]}" '
            f'data-status="{node["status"]}" tabindex="0" role="button" aria-label="{aria}" '
            f'transform="translate(0 0)" opacity="{opacity}">'
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius:.2f}" fill="{NODE_COLORS[node["node_type"]]}" '
            f'stroke="{EVIDENCE_STROKES[node["evidence_basis"]]}" stroke-width="5"{status_dash}>'
            f'<title>{label}</title></circle>'
            f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="middle" class="node-label">{"".join(tspans)}</text>'
            f'</g>'
        )

    type_options = "".join(
        f'<option value="{value}">{value}</option>' for value in sorted(NODE_TYPES)
    )
    evidence_options = "".join(
        f'<option value="{value}">{value}</option>' for value in sorted(EVIDENCE_BASES)
    )
    relation_options = "".join(
        f'<option value="{value}">{value}</option>' for value in sorted(RELATIONS)
    )
    role_options = "".join(
        f'<option value="{value}">{value}</option>' for value in sorted(PORTFOLIO_ROLES)
    )
    node_legend = "".join(
        f'<span><i style="background:{color}"></i>{node_type}</span>'
        for node_type, color in NODE_COLORS.items()
    )
    evidence_legend = "".join(
        f'<span><i class="ring" style="border-color:{color}"></i>{basis}</span>'
        for basis, color in EVIDENCE_STROKES.items()
    )
    relation_legend = "".join(
        f'<span><i class="line" style="background:{color}"></i>{relation}</span>'
        for relation, color in RELATION_COLORS.items()
    )
    fallback = html.escape(render_text_fallback(source))
    template = """<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
:root{color-scheme:light dark;--bg:#f4f6f8;--panel:#ffffff;--ink:#1a2730;--muted:#60717d;--border:#cad3da;--focus:#e08a26}
@media(prefers-color-scheme:dark){:root{--bg:#11181d;--panel:#182228;--ink:#edf4f7;--muted:#a8bac4;--border:#3b4c56}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif}
header{padding:18px 22px 10px}h1{font-size:1.4rem;margin:0 0 5px}.subtitle{color:var(--muted);margin:0}
.controls{display:flex;flex-wrap:wrap;gap:9px;padding:12px 22px}.controls label{display:flex;gap:5px;align-items:center}.controls input,.controls select,.controls button{font:inherit;border:1px solid var(--border);border-radius:7px;padding:7px 9px;background:var(--panel);color:var(--ink)}
.workspace{display:grid;grid-template-columns:minmax(0,1fr) 310px;gap:12px;padding:0 22px 16px}.graph-panel,.details,.legend,.fallback{background:var(--panel);border:1px solid var(--border);border-radius:10px}
.graph-panel{overflow:hidden;min-height:680px}.graph-panel svg{display:block;width:100%;height:70vh;min-height:680px;touch-action:none;cursor:grab}.graph-panel svg.panning{cursor:grabbing}
.details{padding:15px;overflow-wrap:anywhere}.details h2{font-size:1rem;margin:0 0 9px}.details dt{font-weight:650;margin-top:8px}.details dd{margin:2px 0;color:var(--muted);white-space:pre-wrap}
.hierarchy-edge{fill:none;stroke:#81909a;stroke-width:1.5;stroke-dasharray:3 6;opacity:.34;pointer-events:none}.edge{pointer-events:stroke;cursor:pointer;opacity:.83}.edge:hover,.edge:focus{opacity:1;filter:drop-shadow(0 0 3px currentColor);outline:none}.node{cursor:pointer}.node:hover circle,.node:focus circle{stroke:var(--focus);stroke-width:7;outline:none}.node-label{fill:#fff;font-weight:650;font-size:12px;pointer-events:none;text-shadow:0 1px 2px #000}.hidden{display:none}
.legend{margin:0 22px 16px;padding:12px 14px}.legend h2{font-size:1rem;margin:0 0 8px}.legend-row{display:flex;gap:11px;flex-wrap:wrap;margin:7px 0;color:var(--muted);font-size:.82rem}.legend span{display:inline-flex;align-items:center;gap:4px}.legend i{display:inline-block;width:14px;height:14px;border-radius:50%}.legend .ring{background:transparent;border:3px solid}.legend .line{height:4px;border-radius:0;width:22px}
.fallback{margin:0 22px 22px;padding:12px 14px}.fallback summary{cursor:pointer;font-weight:650}.fallback pre{white-space:pre-wrap;overflow-wrap:anywhere;color:var(--muted)}
@media(max-width:900px){.workspace{grid-template-columns:1fr}.details{min-height:220px}.graph-panel svg{height:62vh}}
@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;transition:none!important}}
</style>
</head>
<body>
<header><h1>__TITLE__</h1><p class="subtitle">节点面积＝当前研究简报相关度；证据层级、核验状态与关系强度使用独立视觉通道。</p></header>
<section class="controls" aria-label="图谱筛选与视图控制">
<label>搜索 <input id="search" type="search" placeholder="节点、摘要或来源"></label>
<label>节点 <select id="type-filter"><option value="all">全部</option>__TYPE_OPTIONS__</select></label>
<label>方向角色 <select id="role-filter"><option value="all">全部</option>__ROLE_OPTIONS__</select></label>
<label>证据 <select id="evidence-filter"><option value="all">全部</option>__EVIDENCE_OPTIONS__</select></label>
<label>关系 <select id="relation-filter"><option value="all">全部</option>__RELATION_OPTIONS__</select></label>
<button id="zoom-in" type="button" aria-label="放大">＋</button><button id="zoom-out" type="button" aria-label="缩小">－</button><button id="reset" type="button">重置视图</button>
</section>
<main class="workspace">
<section class="graph-panel" aria-label="交互式研究方向证据图">
<svg id="graph" viewBox="0 0 __WIDTH__ __HEIGHT__" role="img" aria-label="__ARIA_TITLE__">
<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto"><path d="M0,0 L0,6 L7,3 z" fill="context-stroke"></path></marker></defs>
<g id="viewport">__HIERARCHY____EDGES____NODES__</g>
</svg>
</section>
<aside class="details" id="details" aria-live="polite"><h2>节点或关系详情</h2><p>选择一个节点或边；筛选和选择只改变视图，不改变证据、方向状态或授权。</p></aside>
</main>
<section class="legend" aria-label="图例"><h2>图例</h2><div class="legend-row"><strong>节点类型</strong> __NODE_LEGEND__</div><div class="legend-row"><strong>证据层级</strong> __EVIDENCE_LEGEND__</div><div class="legend-row"><strong>关系</strong> __RELATION_LEGEND__</div><div class="legend-row">灰色点线＝布局层级（不表示支持关系）；其他虚线＝推断、迁移假设、未决或被阻断；边宽＝本图关系强度；节点大小不表示证据质量。</div></section>
<details class="fallback"><summary>等价文本视图</summary><pre>__FALLBACK__</pre></details>
<noscript><p class="fallback">JavaScript 已关闭；请使用上方等价文本视图。图谱数据仍保持只读。</p></noscript>
<script id="graph-data" type="application/json">__GRAPH_JSON__</script>
<script>
"use strict";
const source=JSON.parse(document.getElementById("graph-data").textContent);
const nodeById=new Map(source.nodes.map(n=>[n.id,n]));
const edgeById=new Map(source.edges.map(e=>[e.id,e]));
const svg=document.getElementById("graph"),viewport=document.getElementById("viewport"),details=document.getElementById("details");
const search=document.getElementById("search"),typeFilter=document.getElementById("type-filter"),roleFilter=document.getElementById("role-filter"),evidenceFilter=document.getElementById("evidence-filter"),relationFilter=document.getElementById("relation-filter");
let scale=1,tx=0,ty=0,dragging=false,lastX=0,lastY=0;
function updateTransform(){viewport.setAttribute("transform",`translate(${tx} ${ty}) scale(${scale})`)}
function field(label,value){const dt=document.createElement("dt"),dd=document.createElement("dd");dt.textContent=label;dd.textContent=Array.isArray(value)?(value.join("\n")||"none"):String(value??"none");return[dt,dd]}
function showRecord(kind,record){details.replaceChildren();const h=document.createElement("h2");h.textContent=kind==="node"?record.label:`${record.source} ${record.relation} ${record.target}`;const dl=document.createElement("dl");Object.entries(record).forEach(([k,v])=>{const pair=field(k,v);dl.append(pair[0],pair[1])});details.append(h,dl)}
function applyFilters(){const q=search.value.trim().toLocaleLowerCase();const visible=new Set();document.querySelectorAll(".node").forEach(el=>{const n=nodeById.get(el.dataset.nodeId);const hay=JSON.stringify(n).toLocaleLowerCase();const ok=(!q||hay.includes(q))&&(typeFilter.value==="all"||n.node_type===typeFilter.value)&&(roleFilter.value==="all"||n.portfolio_role===roleFilter.value)&&(evidenceFilter.value==="all"||n.evidence_basis===evidenceFilter.value);el.classList.toggle("hidden",!ok);if(ok)visible.add(n.id)});document.querySelectorAll(".edge").forEach(el=>{const e=edgeById.get(el.dataset.edgeId);const ok=visible.has(e.source)&&visible.has(e.target)&&(relationFilter.value==="all"||e.relation===relationFilter.value);el.classList.toggle("hidden",!ok)});document.querySelectorAll(".hierarchy-edge").forEach(el=>el.classList.toggle("hidden",!(visible.has(el.dataset.source)&&visible.has(el.dataset.target))))}
document.querySelectorAll(".node").forEach(el=>{const activate=()=>showRecord("node",nodeById.get(el.dataset.nodeId));el.addEventListener("click",activate);el.addEventListener("keydown",ev=>{if(ev.key==="Enter"||ev.key===" "){ev.preventDefault();activate()}})});
document.querySelectorAll(".edge").forEach(el=>{const activate=()=>showRecord("edge",edgeById.get(el.dataset.edgeId));el.addEventListener("click",activate);el.addEventListener("keydown",ev=>{if(ev.key==="Enter"||ev.key===" "){ev.preventDefault();activate()}})});
[search,typeFilter,roleFilter,evidenceFilter,relationFilter].forEach(el=>el.addEventListener("input",applyFilters));
function zoom(factor){scale=Math.min(3,Math.max(.35,scale*factor));updateTransform()}
document.getElementById("zoom-in").addEventListener("click",()=>zoom(1.2));document.getElementById("zoom-out").addEventListener("click",()=>zoom(1/1.2));
document.getElementById("reset").addEventListener("click",()=>{scale=1;tx=0;ty=0;search.value="";typeFilter.value="all";roleFilter.value="all";evidenceFilter.value="all";relationFilter.value="all";updateTransform();applyFilters()});
svg.addEventListener("wheel",ev=>{ev.preventDefault();zoom(ev.deltaY<0?1.1:1/1.1)},{passive:false});
svg.addEventListener("pointerdown",ev=>{dragging=true;lastX=ev.clientX;lastY=ev.clientY;svg.setPointerCapture(ev.pointerId);svg.classList.add("panning")});
svg.addEventListener("pointermove",ev=>{if(!dragging)return;tx+=(ev.clientX-lastX)/scale;ty+=(ev.clientY-lastY)/scale;lastX=ev.clientX;lastY=ev.clientY;updateTransform()});
function endDrag(){dragging=false;svg.classList.remove("panning")}svg.addEventListener("pointerup",endDrag);svg.addEventListener("pointercancel",endDrag);
</script>
</body>
</html>
"""
    replacements = {
        "__TITLE__": html.escape(source["title"]),
        "__ARIA_TITLE__": html.escape(source["title"], quote=True),
        "__TYPE_OPTIONS__": type_options,
        "__ROLE_OPTIONS__": role_options,
        "__EVIDENCE_OPTIONS__": evidence_options,
        "__RELATION_OPTIONS__": relation_options,
        "__WIDTH__": f"{width:.1f}",
        "__HEIGHT__": f"{height:.1f}",
        "__HIERARCHY__": "".join(hierarchy_markup),
        "__EDGES__": "".join(edge_markup),
        "__NODES__": "".join(node_markup),
        "__NODE_LEGEND__": node_legend,
        "__EVIDENCE_LEGEND__": evidence_legend,
        "__RELATION_LEGEND__": relation_legend,
        "__FALLBACK__": fallback,
        "__GRAPH_JSON__": _safe_json_for_html(source),
    }
    for marker, value in replacements.items():
        template = template.replace(marker, value)
    return template


def _load_graph(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate and render direction-graph.v1")
    parser.add_argument("input", type=Path)
    parser.add_argument("--html", type=Path, dest="html_path")
    parser.add_argument("--text", type=Path, dest="text_path")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if not args.check and args.html_path is None and args.text_path is None:
        parser.error("choose --check, --html, or --text")
    try:
        graph = _load_graph(args.input)
    except (OSError, json.JSONDecodeError) as error:
        print(json.dumps({"status": "invalid", "errors": [f"input_unreadable:{type(error).__name__}"]}, separators=(",", ":")))
        return 1
    errors = validate_graph(graph)
    if errors:
        print(json.dumps({"status": "invalid", "errors": errors}, separators=(",", ":")))
        return 1
    if args.html_path is not None:
        args.html_path.parent.mkdir(parents=True, exist_ok=True)
        args.html_path.write_text(render_html(graph), encoding="utf-8", newline="\n")
    if args.text_path is not None:
        args.text_path.parent.mkdir(parents=True, exist_ok=True)
        args.text_path.write_text(render_text_fallback(graph), encoding="utf-8", newline="\n")
    print(
        json.dumps(
            {
                "status": "valid",
                "graph_id": graph["graph_id"],
                "node_count": len(graph["nodes"]),
                "edge_count": len(graph["edges"]),
                "writes": int(args.html_path is not None) + int(args.text_path is not None),
            },
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
