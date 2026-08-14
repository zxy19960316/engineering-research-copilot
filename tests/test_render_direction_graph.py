from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "skills" / "research-direction-evidence"
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from render_direction_graph import (  # noqa: E402
    _node_area,
    main,
    render_html,
    render_text_fallback,
    validate_graph,
)


def _fixture() -> dict:
    return json.loads(
        (SKILL_ROOT / "assets" / "direction-graph-example.json").read_text(
            encoding="utf-8"
        )
    )


class DirectionGraphContractTests(unittest.TestCase):
    def test_fixture_is_valid(self):
        self.assertEqual([], validate_graph(_fixture()))

    def test_duplicate_or_orphan_graph_fails_closed(self):
        duplicate = _fixture()
        duplicate["nodes"].append(copy.deepcopy(duplicate["nodes"][0]))
        self.assertIn("duplicate_node_id", validate_graph(duplicate))

        orphan = _fixture()
        orphan["edges"][0]["target"] = "fixture:missing"
        self.assertIn("edge_0_endpoint_missing", validate_graph(orphan))

    def test_cycle_and_unrooted_hierarchy_are_rejected(self):
        graph = _fixture()
        graph["nodes"][1]["parent_id"] = "fixture:C1"
        graph["nodes"][5]["parent_id"] = "fixture:D1"
        errors = validate_graph(graph)
        self.assertTrue(any(error.startswith("hierarchy_cycle:") for error in errors))

    def test_boolean_and_out_of_range_relevance_are_rejected(self):
        graph = _fixture()
        graph["nodes"][0]["relevance"] = True
        self.assertIn("node_0_relevance_invalid", validate_graph(graph))
        graph["nodes"][0]["relevance"] = 1.01
        self.assertIn("node_0_relevance_invalid", validate_graph(graph))

    def test_external_evidence_requires_identity_and_source(self):
        graph = _fixture()
        evidence = graph["nodes"][6]
        evidence["node_type"] = "evidence"
        evidence["evidence_basis"] = "abstract_level"
        evidence["verification_status"] = "unverified"
        evidence["source_refs"] = []
        self.assertIn("node_6_external_evidence_unverified", validate_graph(graph))

    def test_conflicted_evidence_cannot_be_admissible(self):
        graph = _fixture()
        graph["nodes"][6]["verification_status"] = "conflicted"
        self.assertIn("node_6_conflicted_admissible", validate_graph(graph))


class DirectionGraphRendererTests(unittest.TestCase):
    def test_renderers_are_pure_and_deterministic(self):
        graph = _fixture()
        original = copy.deepcopy(graph)
        self.assertEqual(render_html(graph), render_html(graph))
        self.assertEqual(render_text_fallback(graph), render_text_fallback(graph))
        self.assertEqual(original, graph)

    def test_node_area_not_radius_is_linear_in_relevance(self):
        delta_low = _node_area(0.4) - _node_area(0.2)
        delta_high = _node_area(0.9) - _node_area(0.7)
        self.assertAlmostEqual(delta_low, delta_high)
        self.assertGreater(_node_area(0.9), _node_area(0.4))

    def test_html_is_self_contained_and_interactive(self):
        rendered = render_html(_fixture())
        for marker in (
            'id="search"',
            'id="type-filter"',
            'id="role-filter"',
            'id="evidence-filter"',
            'id="relation-filter"',
            'id="zoom-in"',
            'id="details"',
            'tabindex="0"',
            "pointerdown",
            "direction-graph.v1",
            "节点面积",
            "等价文本视图",
            'class="hierarchy-edge"',
        ):
            self.assertIn(marker, rendered)
        self.assertNotIn("<script src=", rendered)
        self.assertNotIn("<link ", rendered)
        self.assertNotIn("http://", rendered)
        self.assertNotIn("https://", rendered)

    def test_html_escapes_markup_and_inert_json(self):
        graph = _fixture()
        graph["nodes"][1]["label"] = '<img src=x onerror=alert(1)></script>'
        rendered = render_html(graph)
        self.assertNotIn("<img src=x", rendered)
        self.assertNotIn("</script></script>", rendered)
        self.assertIn("\\u003c", rendered)
        self.assertIn("&lt;img", rendered)

    def test_fallback_preserves_all_node_and_edge_facts(self):
        graph = _fixture()
        fallback = render_text_fallback(graph)
        for node in graph["nodes"]:
            self.assertIn(node["id"], fallback)
            self.assertIn(f'relevance={node["relevance"]:.3f}', fallback)
            self.assertIn(f'evidence={node["evidence_basis"]}', fallback)
        for edge in graph["edges"]:
            self.assertIn(edge["id"], fallback)
            self.assertIn(f'--{edge["relation"]}-->', fallback)

    def test_check_mode_performs_no_write(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            input_path = temp_root / "graph.json"
            input_path.write_text(json.dumps(_fixture()), encoding="utf-8")
            before = sorted(path.name for path in temp_root.iterdir())
            self.assertEqual(0, main([str(input_path), "--check"]))
            after = sorted(path.name for path in temp_root.iterdir())
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
