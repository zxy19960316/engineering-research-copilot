#!/usr/bin/env python3
"""Audit the installable Skill package with a deterministic closed result."""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path


M3_DIR = Path(__file__).resolve().parent
REPO_ROOT = M3_DIR.parents[1]
DEFAULT_PACKAGE_ROOT = REPO_ROOT / "skills" / "engineering-research-copilot"
FORBIDDEN_NAMES = {"README.md", "CHANGELOG.md", "INSTALLATION_GUIDE.md"}
MARKERS = (
    "TO" + "DO",
    "T" + "BD",
    "[" + "TO" + "DO" + "]",
    "PLACE" + "HOLDER",
)
AUDITED_SUFFIXES = {".md", ".py", ".yaml", ".yml"}
MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]\r\n]+\]\(([^)\r\n]+)\)")
DIRECT_REFERENCE_TARGET = re.compile(r"references/[^/\\]+\.md")


def _result(
    errors: list[str],
    *,
    skill_lines: int,
    reference_count: int,
    direct_link_count: int,
) -> dict[str, object]:
    closed_errors = sorted(set(errors))
    return {
        "status": "valid" if not closed_errors else "invalid",
        "errors": closed_errors,
        "skill_lines": skill_lines,
        "reference_count": reference_count,
        "direct_link_count": direct_link_count,
    }


def audit_package(package_root: Path) -> dict[str, object]:
    """Return one closed audit result without modifying the package."""

    root = Path(package_root)
    skill_path = root / "SKILL.md"
    references_root = root / "references"
    errors: list[str] = []

    try:
        skill_text = skill_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        skill_text = ""
        errors.append("invalid_skill_file")
    skill_lines = len(skill_text.splitlines())
    if skill_lines >= 500:
        errors.append("skill_line_limit_exceeded")

    lines = skill_text.splitlines()
    if not lines or lines[0] != "---":
        errors.append("invalid_skill_frontmatter")
        frontmatter: list[str] = []
    else:
        try:
            close_index = lines.index("---", 1)
        except ValueError:
            errors.append("invalid_skill_frontmatter")
            frontmatter = []
        else:
            frontmatter = lines[1:close_index]
    names = [line for line in frontmatter if line.startswith("name:")]
    descriptions = [line for line in frontmatter if line.startswith("description:")]
    if names != ["name: engineering-research-copilot"]:
        errors.append("invalid_skill_name")
    if len(descriptions) != 1 or not descriptions[0].partition(":")[2].strip():
        errors.append("invalid_skill_description")

    try:
        top_level_references = sorted(references_root.glob("*.md"))
        nested_references = sorted(
            path
            for path in references_root.rglob("*.md")
            if path.parent != references_root
        )
    except OSError:
        top_level_references = []
        nested_references = []
        errors.append("invalid_references_directory")
    if not top_level_references:
        errors.append("missing_top_level_references")
    if nested_references:
        errors.append("nested_reference_markdown")

    expected_targets = {
        f"references/{path.name}" for path in top_level_references
    }
    reference_like_targets = [
        target
        for target in MARKDOWN_LINK.findall(skill_text)
        if target.startswith("references/")
    ]
    invalid_targets = [
        target
        for target in reference_like_targets
        if DIRECT_REFERENCE_TARGET.fullmatch(target) is None
    ]
    if invalid_targets:
        errors.append("invalid_reference_link")
    direct_targets = [
        target
        for target in reference_like_targets
        if DIRECT_REFERENCE_TARGET.fullmatch(target) is not None
    ]
    if any(count > 1 for count in Counter(direct_targets).values()):
        errors.append("duplicate_reference_link")
    linked_targets = set(direct_targets)
    if linked_targets - expected_targets:
        errors.append("dangling_reference_link")
    if expected_targets - linked_targets:
        errors.append("unlinked_reference")

    try:
        package_entries = list(root.rglob("*"))
    except OSError:
        package_entries = []
        errors.append("invalid_package_tree")
    if any(path.name in FORBIDDEN_NAMES for path in package_entries):
        errors.append("forbidden_package_file")
    marker_found = False
    for path in package_entries:
        if not path.is_file() or path.suffix not in AUDITED_SUFFIXES:
            continue
        try:
            body = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            errors.append("invalid_package_file")
            continue
        if any(marker in body for marker in MARKERS):
            marker_found = True
    if marker_found:
        errors.append("unresolved_package_marker")

    return _result(
        errors,
        skill_lines=skill_lines,
        reference_count=len(top_level_references),
        direct_link_count=len(direct_targets),
    )


def _emit(result: dict[str, object]) -> None:
    print(
        json.dumps(
            result,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        )
    )


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) > 1:
        result = _result(
            ["unexpected_arguments"],
            skill_lines=0,
            reference_count=0,
            direct_link_count=0,
        )
    else:
        root = DEFAULT_PACKAGE_ROOT if not arguments else Path(arguments[0])
        result = audit_package(root)
    _emit(result)
    return 0 if result["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
