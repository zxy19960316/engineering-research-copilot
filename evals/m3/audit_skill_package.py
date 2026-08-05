#!/usr/bin/env python3
"""Audit the installable Skill package with a deterministic closed result."""

from __future__ import annotations

import json
import os
import re
import stat
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
MARKDOWN_LINK = re.compile(r"\[[^\]\r\n]+\]\(([^)\r\n]+)\)")
DIRECT_REFERENCE_TARGET = re.compile(r"references/[^/\\]+\.md")
FENCE_OPEN = re.compile(r"^ {0,3}(`{3,}|~{3,})[^\r\n]*$")
HTML_COMMENT = re.compile(r"<!--.*?(?:-->|\Z)", re.DOTALL)
REPARSE_POINT = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


def _mask_span(characters: list[str], start: int, end: int) -> None:
    for index in range(start, end):
        if characters[index] not in {"\r", "\n"}:
            characters[index] = " "


def _mask_fenced_code(text: str) -> str:
    characters = list(text)
    offset = 0
    fence_character: str | None = None
    fence_length = 0
    for line in text.splitlines(keepends=True):
        content = line.rstrip("\r\n")
        if fence_character is None:
            opened = FENCE_OPEN.fullmatch(content)
            if opened is not None:
                marker = opened.group(1)
                fence_character = marker[0]
                fence_length = len(marker)
                _mask_span(characters, offset, offset + len(line))
        else:
            _mask_span(characters, offset, offset + len(line))
            closing = re.fullmatch(
                rf" {{0,3}}{re.escape(fence_character)}"
                rf"{{{fence_length},}}[ \t]*",
                content,
            )
            if closing is not None:
                fence_character = None
                fence_length = 0
        offset += len(line)
    return "".join(characters)


def _mask_html_comments(text: str) -> str:
    characters = list(text)
    for match in HTML_COMMENT.finditer(text):
        _mask_span(characters, match.start(), match.end())
    return "".join(characters)


def _mask_inline_code(text: str) -> str:
    characters = list(text)
    index = 0
    while index < len(text):
        if text[index] != "`":
            index += 1
            continue
        run_end = index
        while run_end < len(text) and text[run_end] == "`":
            run_end += 1
        marker = text[index:run_end]
        search_from = run_end
        closing_start = -1
        while True:
            candidate = text.find(marker, search_from)
            if candidate < 0:
                break
            before_is_tick = candidate > 0 and text[candidate - 1] == "`"
            after = candidate + len(marker)
            after_is_tick = after < len(text) and text[after] == "`"
            if not before_is_tick and not after_is_tick:
                closing_start = candidate
                break
            search_from = candidate + 1
        if closing_start < 0:
            index = run_end
            continue
        closing_end = closing_start + len(marker)
        _mask_span(characters, index, closing_end)
        index = closing_end
    return "".join(characters)


def _escaped_at(text: str, index: int) -> bool:
    backslashes = 0
    cursor = index - 1
    while cursor >= 0 and text[cursor] == "\\":
        backslashes += 1
        cursor -= 1
    return backslashes % 2 == 1


def _rendered_markdown_targets(text: str) -> list[str]:
    visible = _mask_inline_code(_mask_html_comments(_mask_fenced_code(text)))
    targets = []
    for match in MARKDOWN_LINK.finditer(visible):
        opening_bracket = match.start()
        if _escaped_at(visible, opening_bracket):
            continue
        if (
            opening_bracket > 0
            and visible[opening_bracket - 1] == "!"
            and not _escaped_at(visible, opening_bracket - 1)
        ):
            continue
        targets.append(match.group(1))
    return targets


def _regular_unlinked_readable_file(path: Path) -> bool:
    try:
        metadata = os.lstat(path)
    except OSError:
        return False
    attributes = getattr(metadata, "st_file_attributes", 0)
    if (
        stat.S_ISLNK(metadata.st_mode)
        or attributes & REPARSE_POINT
        or not stat.S_ISREG(metadata.st_mode)
    ):
        return False
    try:
        with path.open("rb") as handle:
            handle.read(1)
    except OSError:
        return False
    return True


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
        top_level_entries = sorted(references_root.glob("*.md"))
        top_level_references = [
            path
            for path in top_level_entries
            if _regular_unlinked_readable_file(path)
        ]
        if len(top_level_references) != len(top_level_entries):
            errors.append("invalid_top_level_reference")
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
        for target in _rendered_markdown_targets(skill_text)
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
        if path.suffix not in AUDITED_SUFFIXES:
            continue
        if not _regular_unlinked_readable_file(path):
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
