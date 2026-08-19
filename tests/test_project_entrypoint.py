from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
PROJECT_SKILL = REPO_ROOT / "SKILL.md"
MATRIX = json.loads((REPO_ROOT / "agent-hosts.json").read_text(encoding="utf-8"))
LINK = re.compile(r"\((skills/[^)]+/SKILL\.md)\)")


class ProjectEntrypointTests(unittest.TestCase):
    def test_project_skill_delegates_only_to_the_canonical_umbrella(self) -> None:
        text = PROJECT_SKILL.read_text(encoding="utf-8")
        umbrella = "skills/engineering-research-copilot/SKILL.md"
        self.assertEqual({umbrella}, set(LINK.findall(text)))
        for skill_name in set(MATRIX["required_skills"]) - {
            "engineering-research-copilot"
        }:
            self.assertNotIn(f"skills/{skill_name}/SKILL.md", text)
        self.assertLess(len(text.splitlines()), 500)
        self.assertIn(
            "skills/engineering-research-copilot/references/core-research-governance.md",
            text,
        )
        self.assertIn(
            "skills/engineering-research-copilot/references/core-skill-handoffs.md",
            text,
        )

    def test_git_archive_policy_excludes_only_development_material(self) -> None:
        forbidden = [
            ".gitattributes",
            ".gitignore",
            ".github",
            ".github/workflows/m1-validation.yml",
            "AGENTS.md",
            "build-release.py",
            "docs",
            "docs/superpowers/plans/2026-08-14-clean-skill-distribution.md",
            "evals",
            "evals/m1/replay_offline_results.py",
            "PROJECT_PLAN.md",
            "STATUS.md",
            "tests",
            "tests/test_clean_release.py",
            *MATRIX["source_only_paths"],
        ]
        allowed = [
            "README.md",
            "SKILL.md",
            ".claude-plugin/plugin.json",
            ".codex-plugin/plugin.json",
            "agent-hosts.json",
            "install-skill.py",
            "opencode.json",
            "skills/engineering-research-copilot/SKILL.md",
            "skills/research-literature-evidence/SKILL.md",
        ]
        result = subprocess.run(
            [
                "git",
                "-C",
                str(REPO_ROOT),
                "check-attr",
                "export-ignore",
                "--",
                *forbidden,
                *allowed,
            ],
            check=True,
            text=True,
            capture_output=True,
        )
        observed = {}
        for line in result.stdout.splitlines():
            path, attribute, value = line.rsplit(": ", 2)
            self.assertEqual("export-ignore", attribute)
            observed[path] = value
        self.assertEqual(set(forbidden + allowed), set(observed))
        for path in forbidden:
            self.assertEqual("set", observed[path], path)
        for path in allowed:
            self.assertEqual("unspecified", observed[path], path)


if __name__ == "__main__":
    unittest.main()
