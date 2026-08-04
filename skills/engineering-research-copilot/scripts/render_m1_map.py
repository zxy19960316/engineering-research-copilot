"""Pure deterministic renderers for one structured M1 paper map."""

from __future__ import annotations

from typing import Any


def render_text_fallback(paper_map: dict[str, Any]) -> list[dict[str, Any]]:
    """Render nodes then edges without sorting or mutating the structured map."""

    output: list[dict[str, Any]] = []
    for node in paper_map["nodes"]:
        entry = {key: node[key] for key in ("id", "node_type", "basis_level")}
        entry["entry_type"] = "node"
        if node["node_type"] == "paper":
            entry.update(
                {
                    "evidence_role": node["evidence_role"],
                    "verification_status": node["verification_status"],
                }
            )
        entry["text"] = f'{node["id"]}: {node["short_note"]}'
        output.append(entry)

    for edge in paper_map["edges"]:
        output.append(
            {
                "entry_type": "edge",
                "source": edge["source"],
                "target": edge["target"],
                "relation": edge["relation"],
                "basis_level": edge["basis_level"],
                "text": (
                    f'{edge["source"]} --{edge["relation"]}--> '
                    f'{edge["target"]}: {edge["note"]}'
                ),
            }
        )
    return output


def _escape_label(value: Any) -> str:
    """Escape characters that can alter a Mermaid quoted label."""

    text = str(value)
    replacements = (
        ("&", "&amp;"),
        ("\\", "&#92;"),
        ('"', "&quot;"),
        ("\r", "&#13;"),
        ("\n", "&#10;"),
        ("[", "&#91;"),
        ("]", "&#93;"),
        ("|", "&#124;"),
    )
    for source, target in replacements:
        text = text.replace(source, target)
    return text


def render_mermaid(paper_map: dict[str, Any]) -> str:
    """Render one deterministic Mermaid flowchart from nodes and edges only."""

    lines = ["flowchart TD"]
    node_aliases: dict[str, str] = {}
    for position, node in enumerate(paper_map["nodes"]):
        alias = f"n{position}"
        node_aliases[node["id"]] = alias
        parts = [
            f'id={node["id"]}',
            f'type={node["node_type"]}',
            f'basis={node["basis_level"]}',
        ]
        if node["node_type"] == "paper":
            parts.extend(
                [
                    f'role={node["evidence_role"]}',
                    f'status={node["verification_status"]}',
                    f'fit={node["fit_score"]}',
                ]
            )
        parts.append(f'note={node["short_note"]}')
        label = _escape_label("; ".join(parts))
        lines.append(f'  {alias}["{label}"]')

    for edge in paper_map["edges"]:
        parts = [
            f'relation={edge["relation"]}',
            f'basis={edge["basis_level"]}',
            f'strength={edge["strength"]}',
            f'confidence={edge["confidence"]}',
            f'note={edge["note"]}',
        ]
        label = _escape_label("; ".join(parts))
        lines.append(
            f'  {node_aliases[edge["source"]]} -- "{label}" --> '
            f'{node_aliases[edge["target"]]}'
        )
    return "\n".join(lines)
