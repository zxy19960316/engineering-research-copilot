from __future__ import annotations

import contextlib
import io
import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
M3_EVAL_DIR = REPO_ROOT / "evals" / "m3"
sys.path.insert(0, str(M3_EVAL_DIR))

import audit_skill_package  # noqa: E402
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

    def test_nonrendered_link_like_text_is_not_a_direct_link(self):
        cases = {
            "backtick_fence": (
                "```markdown\n[Reference](references/reference.md)\n```\n"
            ),
            "tilde_fence": (
                "~~~markdown\n[Reference](references/reference.md)\n~~~\n"
            ),
            "inline_code": "`[Reference](references/reference.md)`\n",
            "multiline_html_comment": (
                "<!--\n[Reference](references/reference.md)\n-->\n"
            ),
            "escaped_open_bracket": (
                "\\[Reference](references/reference.md)\n"
            ),
        }
        for name, link_like_text in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temp_dir:
                package = self._make_package(
                    Path(temp_dir),
                    "---\n"
                    "name: engineering-research-copilot\n"
                    "description: \"test package\"\n"
                    "---\n\n"
                    + link_like_text,
                )
                result = audit_package(package)
            self.assertEqual(0, result["direct_link_count"])
            self.assertIn("unlinked_reference", result["errors"])

    def test_four_space_indented_code_link_is_not_rendered(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            package = self._make_package(
                Path(temp_dir),
                "---\n"
                "name: engineering-research-copilot\n"
                "description: \"test package\"\n"
                "---\n\n"
                "    [Reference](references/reference.md)\n",
            )
            result = audit_package(package)
        self.assertEqual(0, result["direct_link_count"])
        self.assertIn("unlinked_reference", result["errors"])
        self.assertNotIn("dangling_reference_link", result["errors"])

        with tempfile.TemporaryDirectory() as temp_dir:
            package = self._make_package(
                Path(temp_dir),
                "---\n"
                "name: engineering-research-copilot\n"
                "description: \"test package\"\n"
                "---\n\n"
                "- Outer item\n"
                "  - [Reference](references/reference.md)\n",
            )
            nested_list_result = audit_package(package)
        self.assertEqual("valid", nested_list_result["status"])
        self.assertEqual(1, nested_list_result["direct_link_count"])

    def test_tab_indented_code_link_is_not_rendered(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            package = self._make_package(
                Path(temp_dir),
                "---\n"
                "name: engineering-research-copilot\n"
                "description: \"test package\"\n"
                "---\n\n"
                "\t[Reference](references/reference.md)\n",
            )
            result = audit_package(package)
        self.assertEqual(0, result["direct_link_count"])
        self.assertIn("unlinked_reference", result["errors"])
        self.assertNotIn("dangling_reference_link", result["errors"])

    def test_four_space_nested_list_link_after_blank_is_rendered(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            package = self._make_package(
                Path(temp_dir),
                "---\n"
                "name: engineering-research-copilot\n"
                "description: \"test package\"\n"
                "---\n\n"
                "- Outer\n\n"
                "    - [Reference](references/reference.md)\n",
            )
            result = audit_package(package)
        self.assertEqual("valid", result["status"])
        self.assertEqual(1, result["direct_link_count"])

    def test_six_space_code_inside_list_does_not_render_link(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            package = self._make_package(
                Path(temp_dir),
                "---\n"
                "name: engineering-research-copilot\n"
                "description: \"test package\"\n"
                "---\n\n"
                "- Outer\n\n"
                "      [Reference](references/reference.md)\n",
            )
            result = audit_package(package)
        self.assertEqual(0, result["direct_link_count"])
        self.assertIn("unlinked_reference", result["errors"])
        self.assertNotIn("dangling_reference_link", result["errors"])

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

    def test_directory_named_markdown_is_not_a_valid_reference(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            package = self._make_package(Path(temp_dir))
            reference = package / "references" / "reference.md"
            reference.unlink()
            reference.mkdir()
            result = audit_package(package)
        self.assertEqual(0, result["reference_count"])
        self.assertIn("invalid_top_level_reference", result["errors"])

    def _replace_with_symlink(self, link: Path, target: Path | str) -> None:
        link.unlink()
        try:
            os.symlink(target, link)
        except (NotImplementedError, OSError) as error:
            self.skipTest(f"symlink creation unavailable: {error}")

    def test_broken_symlink_is_not_a_valid_reference(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            package = self._make_package(Path(temp_dir))
            reference = package / "references" / "reference.md"
            self._replace_with_symlink(reference, "missing-target.md")
            result = audit_package(package)
        self.assertEqual(0, result["reference_count"])
        self.assertIn("invalid_top_level_reference", result["errors"])

    def test_file_symlink_is_not_a_valid_reference(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            package = self._make_package(temp_root)
            external = temp_root / "external.md"
            self._write(external, "# External\n")
            reference = package / "references" / "reference.md"
            self._replace_with_symlink(reference, external)
            result = audit_package(package)
        self.assertEqual(0, result["reference_count"])
        self.assertIn("invalid_top_level_reference", result["errors"])

    def test_windows_reparse_reference_is_not_valid(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            package = self._make_package(Path(temp_dir))
            reference = package / "references" / "reference.md"
            real_lstat = os.lstat

            def mark_reference(path):
                metadata = real_lstat(path)
                if Path(path) == reference:
                    return SimpleNamespace(
                        st_mode=metadata.st_mode,
                        st_file_attributes=(
                            getattr(metadata, "st_file_attributes", 0)
                            | getattr(
                                stat,
                                "FILE_ATTRIBUTE_REPARSE_POINT",
                                0x400,
                            )
                        ),
                    )
                return metadata

            with mock.patch.object(
                audit_skill_package.os,
                "lstat",
                side_effect=mark_reference,
            ):
                result = audit_package(package)
        self.assertEqual(0, result["reference_count"])
        self.assertIn("invalid_top_level_reference", result["errors"])

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
