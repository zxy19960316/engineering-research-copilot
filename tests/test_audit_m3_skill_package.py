from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
M3_EVAL_DIR = REPO_ROOT / "evals" / "m3"
sys.path.insert(0, str(M3_EVAL_DIR))

from audit_skill_package import audit_package, main  # noqa: E402


class M3SkillPackageAuditTests(unittest.TestCase):
    def _write(self, path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")

    def _make_package(self, root: Path, skill_body: str | None = None) -> Path:
        package = root / "engineering-research-copilot"
        body = skill_body or (
            "---\n"
            "name: engineering-research-copilot\n"
            "description: \"test package\"\n"
            "---\n\n"
            "[Reference](references/reference.md)\n"
        )
        self._write(package / "SKILL.md", body)
        self._write(package / "references" / "reference.md", "# Reference\n")
        return package

    def test_current_package_is_valid(self):
        package = REPO_ROOT / "skills" / "engineering-research-copilot"
        result = audit_package(package)
        self.assertEqual("valid", result["status"])
        self.assertEqual([], result["errors"])
        self.assertEqual(13, result["reference_count"])
        self.assertEqual(13, result["direct_link_count"])

    def test_filename_substring_is_not_a_markdown_direct_link(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            package = self._make_package(
                Path(temp_dir),
                "---\n"
                "name: engineering-research-copilot\n"
                "description: \"test package\"\n"
                "---\n\n"
                "Fake mention: references/reference.md\n",
            )
            result = audit_package(package)
        self.assertIn("unlinked_reference", result["errors"])

    def test_dangling_and_unlinked_direct_links_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            package = self._make_package(
                Path(temp_dir),
                "---\n"
                "name: engineering-research-copilot\n"
                "description: \"test package\"\n"
                "---\n\n"
                "[Missing](references/missing.md)\n",
            )
            result = audit_package(package)
        self.assertIn("dangling_reference_link", result["errors"])
        self.assertIn("unlinked_reference", result["errors"])

    def test_duplicate_direct_link_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            package = self._make_package(
                Path(temp_dir),
                "---\n"
                "name: engineering-research-copilot\n"
                "description: \"test package\"\n"
                "---\n\n"
                "[One](references/reference.md)\n"
                "[Again](references/reference.md)\n",
            )
            result = audit_package(package)
        self.assertIn("duplicate_reference_link", result["errors"])

    def test_nested_reference_markdown_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            package = self._make_package(Path(temp_dir))
            self._write(
                package / "references" / "nested" / "deep.md",
                "# Nested\n",
            )
            result = audit_package(package)
        self.assertIn("nested_reference_markdown", result["errors"])

    def test_forbidden_file_and_marker_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            package = self._make_package(Path(temp_dir))
            self._write(package / "README.md", "# Forbidden\n")
            self._write(
                package / "references" / "reference.md",
                "# Reference\n\nTODO replace this marker.\n",
            )
            result = audit_package(package)
        self.assertIn("forbidden_package_file", result["errors"])
        self.assertIn("unresolved_package_marker", result["errors"])

    def test_cli_emits_compact_closed_json_and_exit_codes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            package = self._make_package(Path(temp_dir))
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = main([str(package)])
            line = output.getvalue()
            result = json.loads(line)
            self.assertEqual(0, exit_code)
            self.assertEqual(
                {
                    "direct_link_count",
                    "errors",
                    "reference_count",
                    "skill_lines",
                    "status",
                },
                set(result),
            )
            self.assertNotIn(": ", line)
            self.assertTrue(line.endswith("\n"))

            self._write(package / "README.md", "# Forbidden\n")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                exit_code = main([str(package)])
            self.assertEqual(1, exit_code)
            self.assertEqual("invalid", json.loads(output.getvalue())["status"])


if __name__ == "__main__":
    unittest.main()
