#!/usr/bin/env python3
"""Install Engineering Research Copilot with host-specific invocation policy."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import sys
import tempfile
from urllib.parse import quote
from urllib.request import Request, urlopen
import uuid
import zipfile


SKILL_NAME = "engineering-research-copilot"
REPOSITORY = "zxy19960316/engineering-research-copilot"
HOSTS = ("codex", "claude-code", "github-copilot")
HOST_FRONTMATTER = (
    'argument-hint: "[研究问题、材料或当前任务]"',
    "disable-model-invocation: true",
    "user-invocable: true",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install Engineering Research Copilot without enabling implicit invocation."
    )
    parser.add_argument(
        "--agent",
        action="append",
        choices=HOSTS,
        required=True,
        help="Target host. Repeat to install for more than one host.",
    )
    parser.add_argument(
        "--scope",
        choices=("user", "project"),
        default="user",
        help="Install for the current user or one project (default: user).",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root used with --scope project (default: current directory).",
    )
    parser.add_argument(
        "--source",
        type=Path,
        help="Local repository root or Skill folder. When set, do not use the network.",
    )
    parser.add_argument(
        "--ref",
        default="main",
        help="GitHub branch to download when no local source is available (default: main).",
    )
    return parser.parse_args()


def skill_from_path(path: Path) -> Path | None:
    resolved = path.expanduser().resolve()
    candidates = (
        resolved,
        resolved / "skills" / SKILL_NAME,
    )
    for candidate in candidates:
        if candidate.name == SKILL_NAME and (candidate / "SKILL.md").is_file():
            return candidate
    return None


def local_source(explicit_source: Path | None) -> Path | None:
    if explicit_source is not None:
        source = skill_from_path(explicit_source)
        if source is None:
            raise ValueError(
                f"--source must be the repository root or {SKILL_NAME} folder: "
                f"{explicit_source}"
            )
        return source

    script_name = globals().get("__file__")
    if script_name and script_name not in {"<stdin>", "-"}:
        source = skill_from_path(Path(script_name).resolve().parent)
        if source is not None:
            return source
    return None


def safe_extract(archive: Path, destination: Path) -> None:
    destination = destination.resolve()
    with zipfile.ZipFile(archive) as bundle:
        for member in bundle.infolist():
            member_path = (destination / member.filename).resolve()
            if os.path.commonpath((str(destination), str(member_path))) != str(destination):
                raise ValueError(f"Archive contains an unsafe path: {member.filename}")
        bundle.extractall(destination)


def download_source(ref: str, temporary_root: Path) -> Path:
    encoded_ref = quote(ref, safe="")
    url = (
        f"https://codeload.github.com/{REPOSITORY}/zip/refs/heads/{encoded_ref}"
    )
    archive = temporary_root / "source.zip"
    request = Request(url, headers={"User-Agent": f"{SKILL_NAME}-installer"})
    with urlopen(request, timeout=60) as response, archive.open("wb") as output:
        shutil.copyfileobj(response, output)

    extracted = temporary_root / "source"
    extracted.mkdir()
    safe_extract(archive, extracted)
    matches = list(extracted.glob(f"*/skills/{SKILL_NAME}/SKILL.md"))
    if len(matches) != 1:
        raise ValueError(
            f"Downloaded archive must contain exactly one {SKILL_NAME} Skill; "
            f"found {len(matches)}"
        )
    return matches[0].parent


def target_path(agent: str, scope: str, project_root: Path) -> Path:
    if scope == "user":
        roots = {
            "codex": Path.home() / ".agents" / "skills",
            "claude-code": Path.home() / ".claude" / "skills",
            "github-copilot": Path.home() / ".copilot" / "skills",
        }
    else:
        root = project_root.expanduser().resolve()
        roots = {
            "codex": root / ".agents" / "skills",
            "claude-code": root / ".claude" / "skills",
            "github-copilot": root / ".github" / "skills",
        }
    return roots[agent] / SKILL_NAME


def add_host_frontmatter(skill_file: Path) -> None:
    content = skill_file.read_text(encoding="utf-8")
    if not content.startswith("---\n"):
        raise ValueError(f"SKILL.md has no leading YAML frontmatter: {skill_file}")
    closing = content.find("\n---\n", 4)
    if closing < 0:
        raise ValueError(f"SKILL.md frontmatter is not closed: {skill_file}")

    frontmatter = content[4:closing]
    for field in HOST_FRONTMATTER:
        key = field.split(":", 1)[0]
        if any(line.startswith(f"{key}:") for line in frontmatter.splitlines()):
            raise ValueError(f"SKILL.md already defines host field {key}: {skill_file}")

    adapted = frontmatter.rstrip() + "\n" + "\n".join(HOST_FRONTMATTER)
    with skill_file.open("w", encoding="utf-8", newline="\n") as output:
        output.write("---\n" + adapted + content[closing:])


def install_one(source: Path, destination: Path, agent: str) -> None:
    if destination.exists():
        raise FileExistsError(
            f"Refusing to overwrite existing {agent} installation: {destination}"
        )

    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.parent / f".{SKILL_NAME}.install-{uuid.uuid4().hex}"
    try:
        shutil.copytree(
            source,
            staging,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"),
        )
        if agent in {"claude-code", "github-copilot"}:
            add_host_frontmatter(staging / "SKILL.md")
        elif "allow_implicit_invocation: false" not in (
            staging / "agents" / "openai.yaml"
        ).read_text(encoding="utf-8"):
            raise ValueError("Codex package does not disable implicit invocation")
        staging.replace(destination)
    except Exception:
        if staging.exists() and staging.name.startswith(f".{SKILL_NAME}.install-"):
            shutil.rmtree(staging)
        raise


def main() -> int:
    args = parse_args()
    agents = list(dict.fromkeys(args.agent))
    destinations = [
        (agent, target_path(agent, args.scope, args.project_root))
        for agent in agents
    ]
    existing = [(agent, path) for agent, path in destinations if path.exists()]
    if existing:
        details = "; ".join(f"{agent}={path}" for agent, path in existing)
        raise FileExistsError(f"Refusing to overwrite existing installation(s): {details}")

    source = local_source(args.source)
    if source is not None:
        for agent, destination in destinations:
            install_one(source, destination, agent)
            print(f"Installed {agent}: {destination}")
        return 0

    with tempfile.TemporaryDirectory(prefix=f"{SKILL_NAME}-") as temp:
        source = download_source(args.ref, Path(temp))
        for agent, destination in destinations:
            install_one(source, destination, agent)
            print(f"Installed {agent}: {destination}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        print(f"Installation failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
