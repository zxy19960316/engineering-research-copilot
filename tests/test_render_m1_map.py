from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "skills" / "engineering-research-copilot" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from render_m1_map import render_mermaid, render_text_fallback  # noqa: E402


def _map() -> dict:
    return {
        "nodes": [
            {
                "id": "fixture:P01",
                "node_type": "paper",
                "fit_score": 0.8,
                "evidence_role": "direct_problem",
                "verification_status": "fixture_only",
                "basis_level": "abstract_level",
                "short_note": "Offline fixture node",
            },
            {
                "id": "fixture:D01",
                "node_type": "cluster",
                "basis_level": "metadata_level",
                "short_note": "Public evidence cluster",
            },
        ],
        "edges": [
            {
                "source": "fixture:P01",
                "target": "fixture:D01",
                "relation": "claim_support",
                "strength": "medium",
                "confidence": "medium",
                "basis_level": "metadata_level",
                "note": "Supports the scoped claim",
            }
        ],
    }


class RenderM1MapTests(unittest.TestCase):
    def test_fallback_preserves_order_and_exact_node_fields(self):
        rendered = render_text_fallback(_map())
        self.assertEqual(
            rendered[0],
            {
                "id": "fixture:P01",
                "node_type": "paper",
                "basis_level": "abstract_level",
                "entry_type": "node",
                "evidence_role": "direct_problem",
                "verification_status": "fixture_only",
                "text": "fixture:P01: Offline fixture node",
            },
        )
        self.assertEqual(
            rendered[1],
            {
                "id": "fixture:D01",
                "node_type": "cluster",
                "basis_level": "metadata_level",
                "entry_type": "node",
                "text": "fixture:D01: Public evidence cluster",
            },
        )

    def test_fallback_edge_preserves_exact_fields_and_note(self):
        self.assertEqual(
            render_text_fallback(_map())[-1],
            {
                "entry_type": "edge",
                "source": "fixture:P01",
                "target": "fixture:D01",
                "relation": "claim_support",
                "basis_level": "metadata_level",
                "text": "fixture:P01 --claim_support--> fixture:D01: Supports the scoped claim",
            },
        )

    def test_renderers_are_pure_and_deterministic(self):
        paper_map = _map()
        original = copy.deepcopy(paper_map)
        self.assertEqual(render_text_fallback(paper_map), render_text_fallback(paper_map))
        self.assertEqual(render_mermaid(paper_map), render_mermaid(paper_map))
        self.assertEqual(paper_map, original)

    def test_renderers_read_only_nodes_and_edges(self):
        first = _map()
        second = copy.deepcopy(first)
        first.update({"round": 1, "legend": {"ignored": "first"}})
        second.update({"round": 2, "legend": {"ignored": "second"}})
        self.assertEqual(render_text_fallback(first), render_text_fallback(second))
        self.assertEqual(render_mermaid(first), render_mermaid(second))

    def test_mermaid_preserves_structured_order_and_visible_semantics(self):
        rendered = render_mermaid(_map())
        self.assertLess(rendered.index("fixture:P01"), rendered.index("fixture:D01"))
        for value in (
            "paper",
            "direct_problem",
            "fixture_only",
            "abstract_level",
            "0.8",
            "claim_support",
            "metadata_level",
        ):
            self.assertIn(value, rendered)

    def test_mermaid_escapes_unsafe_label_characters(self):
        paper_map = _map()
        paper_map["nodes"][0]["short_note"] = 'slash \\ quote " newline\n bracket [x] pipe |'
        rendered = render_mermaid(paper_map)
        self.assertEqual(rendered, render_mermaid(paper_map))
        self.assertNotIn("slash \\", rendered)
        self.assertNotIn('quote " newline', rendered)
        self.assertNotIn("\n bracket", rendered)
        self.assertNotIn("[x]", rendered)
        self.assertNotIn("pipe |", rendered)


if __name__ == "__main__":
    unittest.main()
