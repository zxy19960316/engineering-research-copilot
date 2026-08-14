from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = REPO_ROOT / "skills"
EXPECTED_SKILLS = {
    "engineering-research-copilot",
    "research-direction-evidence",
    "research-literature-evidence",
    "research-method-transfer",
    "research-manuscript",
    "research-cross-review",
    "research-data-comparison",
    "research-evidence-adversary",
    "research-figure-workflow",
}
FOCUSED_SKILLS = EXPECTED_SKILLS - {"engineering-research-copilot"}
SHARED_GOVERNANCE_LINK = (
    "../engineering-research-copilot/references/core-research-governance.md"
)
SHARED_HANDOFF_LINK = (
    "../engineering-research-copilot/references/core-skill-handoffs.md"
)
REPORT_HASHES = {
    "2026-08-14-scientific-figure-workflow-survey.md": (
        "4fcbc1169613ade1d065008a284419cee9caa5c2831a7c400c781cc717885bea"
    ),
    "2026-08-14-research-skill-ecosystem-survey.md": (
        "3b484ed3494ea55cabc61992060048bf748ab051411a46e2fca363854d9aa207"
    ),
    "2026-08-14-agent-host-compatibility-survey.md": (
        "57778b596dcbc4ef22827ff48a8e463a6498f5601c74fe1038d74ed74c9be470"
    ),
}


def _frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    _, raw, _ = text.split("---", 2)
    return yaml.safe_load(raw)


class ResearchSkillClusterTests(unittest.TestCase):
    def test_plugin_manifest_declares_the_exact_local_cluster(self):
        manifest = json.loads(
            (REPO_ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertEqual("engineering-research-workbench", manifest["name"])
        self.assertEqual("0.6.0", manifest["version"])
        self.assertEqual("./skills/", manifest["skills"])
        self.assertNotIn("apps", manifest)
        self.assertNotIn("mcpServers", manifest)
        self.assertNotIn("license", manifest)
        self.assertEqual(
            EXPECTED_SKILLS,
            {path.name for path in SKILLS_ROOT.iterdir() if path.is_dir()},
        )

    def test_every_skill_has_narrow_metadata_and_matching_default_prompt(self):
        for skill_name in sorted(EXPECTED_SKILLS):
            with self.subTest(skill=skill_name):
                skill_root = SKILLS_ROOT / skill_name
                skill_text = (skill_root / "SKILL.md").read_text(encoding="utf-8")
                metadata = _frontmatter(skill_root / "SKILL.md")
                agent = yaml.safe_load(
                    (skill_root / "agents" / "openai.yaml").read_text(
                        encoding="utf-8"
                    )
                )
                self.assertEqual(skill_name, metadata["name"])
                self.assertIn("Use", metadata["description"])
                self.assertIn("Do not use", metadata["description"])
                self.assertLess(len(skill_text.splitlines()), 500)
                self.assertIn(
                    f"${skill_name}", agent["interface"]["default_prompt"]
                )
                if skill_name in FOCUSED_SKILLS:
                    self.assertTrue(agent["policy"]["allow_implicit_invocation"])
                self.assertNotIn("dependencies", agent)

    def test_every_focused_skill_links_shared_contracts_directly(self):
        for skill_name in sorted(FOCUSED_SKILLS):
            with self.subTest(skill=skill_name):
                text = (SKILLS_ROOT / skill_name / "SKILL.md").read_text(
                    encoding="utf-8"
                )
                self.assertIn(f"]({SHARED_GOVERNANCE_LINK})", text)
                self.assertIn(f"]({SHARED_HANDOFF_LINK})", text)
                self.assertTrue(
                    (SKILLS_ROOT / skill_name / SHARED_GOVERNANCE_LINK).resolve().is_file()
                )
                self.assertTrue(
                    (SKILLS_ROOT / skill_name / SHARED_HANDOFF_LINK).resolve().is_file()
                )

    def test_shared_governance_covers_evidence_readiness_and_each_permission(self):
        text = (
            SKILLS_ROOT
            / "engineering-research-copilot"
            / "references"
            / "core-research-governance.md"
        ).read_text(encoding="utf-8")
        for token in (
            "source_class",
            "identity_status",
            "content_level",
            "claim_relation",
            "metadata_level",
            "abstract_level",
            "fulltext_level",
            "user_provided_content",
            "concept_sketch",
            "route_preparation",
            "executable_route",
            "source_file_write",
            "artifact_file_write",
            "download",
            "upload",
            "experiment",
            "simulation",
            "training",
            "publication",
            "external_communication",
            "Route generation is not execution authorization",
            "author's decision",
        ):
            self.assertIn(token, text)

    def test_handoff_never_strengthens_evidence_readiness_or_authority(self):
        text = (
            SKILLS_ROOT
            / "engineering-research-copilot"
            / "references"
            / "core-skill-handoffs.md"
        ).read_text(encoding="utf-8")
        for token in (
            "content_hash",
            "inspection_status",
            "inherited",
            "rejected",
            "reset",
            "added",
            "permission_ledger",
            "permitted_next_actions",
            "prohibited_next_actions",
            "without upgrading",
            "does not authorize",
        ):
            self.assertIn(token, text)

    def test_historical_static_paper_map_and_successor_direction_graph_are_separate(self):
        old_contract = (
            SKILLS_ROOT
            / "engineering-research-copilot"
            / "references"
            / "core-paper-map.md"
        ).read_text(encoding="utf-8")
        new_contract = (
            SKILLS_ROOT
            / "research-direction-evidence"
            / "references"
            / "direction-graph-contract.md"
        ).read_text(encoding="utf-8")
        self.assertIn("Do not create an interactive HTML application", old_contract)
        self.assertIn("direction-graph.v1", new_contract)
        self.assertIn("not a new evidence source", new_contract)

    def test_paired_first_release_skills_have_explicit_mode_split_triggers(self):
        expected_modes = {
            "research-literature-evidence": ("discovery_mode", "verification_mode"),
            "research-method-transfer": ("method_design_mode", "transfer_assessment_mode"),
            "research-manuscript": ("draft_mode", "polish_mode"),
        }
        for skill_name, modes in expected_modes.items():
            with self.subTest(skill=skill_name):
                text = (SKILLS_ROOT / skill_name / "SKILL.md").read_text(
                    encoding="utf-8"
                )
                for mode in modes:
                    self.assertIn(mode, text)
                self.assertIn("split", text.lower())

    def test_research_reports_are_bound_and_read_only(self):
        report_root = REPO_ROOT / "docs" / "research"
        for name, expected_hash in REPORT_HASHES.items():
            with self.subTest(report=name):
                path = report_root / name
                payload = path.read_bytes()
                self.assertEqual(expected_hash, hashlib.sha256(payload).hexdigest())
                text = payload.decode("utf-8")
                self.assertTrue("read-only" in text.lower() or "只读" in text)

    def test_successor_status_preserves_terminal_predecessor_boundary(self):
        current = (REPO_ROOT / "STATUS.md").read_text(encoding="utf-8").split(
            "## M3 checklist", 1
        )[0]
        self.assertIn("S1.1 — Portable Agent-host projections", current)
        self.assertIn("S1_FOUNDATION_IMPLEMENTED", current)
        self.assertIn("codex/research-skill-cluster-strengthening", current)
        self.assertIn("not a continuation, retry, repair, or relabeling of M4.2", current)
        self.assertIn("M4.2 GATE_B_STOPPED_PROTOCOL_OR_INFRASTRUCTURE_FAILURE", current)
        self.assertIn("authorization_token=CONSUMED", current)
        self.assertIn("continuation_forbidden=true", current)


if __name__ == "__main__":
    unittest.main()
