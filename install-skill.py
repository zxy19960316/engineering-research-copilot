#!/usr/bin/env python3
"""Install deterministic host projections of the Research Workbench cluster."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import sys
import tempfile
from typing import Any
from urllib.parse import quote
from urllib.request import Request, urlopen
import uuid
import zipfile


REPOSITORY = "zxy19960316/engineering-research-copilot"
MATRIX_FILENAME = "agent-hosts.json"
MATRIX_SCHEMA = "engineering-research-agent-hosts.v1"
REPORT_SCHEMA = "engineering-research-install-report.v1"
IGNORED_NAMES = ("__pycache__", "*.pyc", ".DS_Store")
TOP_LEVEL_KEY = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*):(?:\s|$)")
CROSS_REFERENCE = re.compile(
    rb"\.\./engineering-research-copilot/references/([a-z0-9-]+\.md)"
)
DESCRIPTION_LINE = re.compile(
    rb'(?m)^description:\s*"[^"\r\n]*"(?P<cr>\r?)$'
)
PROJECTION_SCHEMA = "engineering-research-skill-projection.v1"


@dataclass(frozen=True)
class Package:
    repository_root: Path
    skills_root: Path
    matrix: dict[str, Any]


@dataclass(frozen=True)
class Projection:
    root: Path
    hosts: tuple[str, ...]


@dataclass
class AppliedProjection:
    projection: Projection
    stage_root: Path
    root_existed: bool
    backup_root: Path | None
    installed: list[Path]
    backed_up: list[tuple[Path, Path]]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Install the complete Engineering Research Workbench Skill cluster "
            "as deterministic, self-contained host projections."
        )
    )
    parser.add_argument(
        "--agent",
        action="append",
        required=True,
        help=(
            "Target host. Repeat for several hosts, or use 'all'. Supported "
            "names are read from agent-hosts.json."
        ),
    )
    parser.add_argument(
        "--scope",
        choices=("user", "project"),
        default="user",
        help="Install for one user or one project (default: user).",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Project root used with --scope project (default: current directory).",
    )
    parser.add_argument(
        "--home-root",
        type=Path,
        help="Override the home root used for user projections (mainly for isolation/testing).",
    )
    parser.add_argument(
        "--source",
        type=Path,
        help="Local repository root. When provided, the installer performs no download.",
    )
    parser.add_argument(
        "--ref",
        default="main",
        help="GitHub branch to download when no local repository is available (default: main).",
    )
    parser.add_argument(
        "--upgrade",
        action="store_true",
        help="Replace existing copies of these nine Skills using rollback-capable staging.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate the source and print the exact projection plan without writing.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the install report as JSON.",
    )
    return parser.parse_args(argv)


def _load_matrix(repository_root: Path) -> dict[str, Any]:
    path = repository_root / MATRIX_FILENAME
    if not path.is_file():
        raise ValueError(f"Repository does not contain {MATRIX_FILENAME}: {repository_root}")
    matrix = json.loads(path.read_text(encoding="utf-8"))
    if matrix.get("schema_version") != MATRIX_SCHEMA:
        raise ValueError(
            f"Unsupported host matrix schema: {matrix.get('schema_version')!r}"
        )
    return matrix


def package_from_path(path: Path) -> Package | None:
    resolved = path.expanduser().resolve()
    candidates = [resolved]
    if resolved.name == "skills":
        candidates.append(resolved.parent)
    for repository_root in candidates:
        skills_root = repository_root / "skills"
        if (repository_root / MATRIX_FILENAME).is_file() and skills_root.is_dir():
            return Package(repository_root, skills_root, _load_matrix(repository_root))
    return None


def local_package(explicit_source: Path | None) -> Package | None:
    if explicit_source is not None:
        package = package_from_path(explicit_source)
        if package is None:
            raise ValueError(
                f"--source must be a repository root containing skills/ and "
                f"{MATRIX_FILENAME}: {explicit_source}"
            )
        return package

    script_name = globals().get("__file__")
    if script_name and script_name not in {"<stdin>", "-"}:
        package = package_from_path(Path(script_name).resolve().parent)
        if package is not None:
            return package
    return None


def safe_extract(archive: Path, destination: Path) -> None:
    destination = destination.resolve()
    with zipfile.ZipFile(archive) as bundle:
        for member in bundle.infolist():
            unix_mode = member.external_attr >> 16
            if stat.S_ISLNK(unix_mode):
                raise ValueError(f"Archive contains a symbolic link: {member.filename}")
            member_path = (destination / member.filename).resolve()
            try:
                common = os.path.commonpath((str(destination), str(member_path)))
            except ValueError as error:
                raise ValueError(
                    f"Archive contains an unsafe path: {member.filename}"
                ) from error
            if os.path.normcase(common) != os.path.normcase(str(destination)):
                raise ValueError(f"Archive contains an unsafe path: {member.filename}")
        bundle.extractall(destination)


def download_package(ref: str, temporary_root: Path) -> Package:
    encoded_ref = quote(ref, safe="")
    url = f"https://codeload.github.com/{REPOSITORY}/zip/refs/heads/{encoded_ref}"
    archive = temporary_root / "source.zip"
    request = Request(
        url,
        headers={"User-Agent": "engineering-research-workbench-installer"},
    )
    with urlopen(request, timeout=60) as response, archive.open("wb") as output:
        shutil.copyfileobj(response, output)

    extracted = temporary_root / "source"
    extracted.mkdir()
    safe_extract(archive, extracted)
    candidates = [path.parent for path in extracted.glob(f"*/{MATRIX_FILENAME}")]
    packages = [package_from_path(path) for path in candidates]
    matches = [package for package in packages if package is not None]
    if len(matches) != 1:
        raise ValueError(
            "Downloaded archive must contain exactly one compatible repository; "
            f"found {len(matches)}"
        )
    return matches[0]


def _frontmatter(path: Path) -> tuple[dict[str, str], set[str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        raise ValueError(f"SKILL.md has no leading YAML frontmatter: {path}")
    try:
        closing = lines.index("---", 1)
    except ValueError as error:
        raise ValueError(f"SKILL.md frontmatter is not closed: {path}") from error

    values: dict[str, str] = {}
    keys: set[str] = set()
    for line in lines[1:closing]:
        if line.startswith((" ", "\t")):
            continue
        match = TOP_LEVEL_KEY.match(line)
        if not match:
            continue
        key = match.group(1)
        keys.add(key)
        value = line.split(":", 1)[1].strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        values[key] = value
    return values, keys


def validate_package(package: Package) -> None:
    matrix = package.matrix
    required = matrix.get("required_skills")
    if not isinstance(required, list) or not required:
        raise ValueError("Host matrix must declare a non-empty required_skills list")
    if len(required) != len(set(required)):
        raise ValueError("Host matrix contains duplicate required skill names")

    actual = sorted(
        child.name
        for child in package.skills_root.iterdir()
        if child.is_dir() and (child / "SKILL.md").is_file()
    )
    if actual != sorted(required):
        raise ValueError(
            f"Skill cluster mismatch: expected {sorted(required)}, found {actual}"
        )

    allowed_keys = set(matrix.get("portable_frontmatter_keys", []))
    if not {"name", "description"}.issubset(allowed_keys):
        raise ValueError("portable_frontmatter_keys must include name and description")

    for skill_name in required:
        skill_file = package.skills_root / skill_name / "SKILL.md"
        values, keys = _frontmatter(skill_file)
        if values.get("name") != skill_name:
            raise ValueError(
                f"Skill name must match its directory: {skill_file}"
            )
        if not values.get("description"):
            raise ValueError(f"Skill description is empty: {skill_file}")
        unsupported = keys - allowed_keys
        if unsupported:
            raise ValueError(
                f"Non-portable top-level frontmatter in {skill_file}: "
                f"{sorted(unsupported)}"
            )

    shared_root = (
        package.skills_root / "engineering-research-copilot" / "references"
    )
    for name in ("core-research-governance.md", "core-skill-handoffs.md"):
        if not (shared_root / name).is_file():
            raise ValueError(f"Missing shared normative reference: {shared_root / name}")

    for skill_name in set(required) - {"engineering-research-copilot"}:
        skill_file = package.skills_root / skill_name / "SKILL.md"
        skill_text = skill_file.read_text(encoding="utf-8")
        for relative in (
            "../engineering-research-copilot/references/core-research-governance.md",
            "../engineering-research-copilot/references/core-skill-handoffs.md",
        ):
            if relative not in skill_text:
                raise ValueError(
                    f"Focused Skill does not link the shared contract {relative}: "
                    f"{skill_file}"
                )
        if "generated host projection" not in skill_text:
            raise ValueError(
                f"Focused Skill lacks projection-reference guidance: {skill_file}"
            )

    expected_version = matrix.get("cluster_version")
    for relative in (
        Path(".codex-plugin/plugin.json"),
        Path(".claude-plugin/plugin.json"),
    ):
        manifest_path = package.repository_root / relative
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("name") != matrix.get("cluster_name"):
            raise ValueError(f"Plugin name mismatch: {manifest_path}")
        if manifest.get("version") != expected_version:
            raise ValueError(f"Plugin version mismatch: {manifest_path}")

    opencode_path = package.repository_root / "opencode.json"
    opencode = json.loads(opencode_path.read_text(encoding="utf-8"))
    if opencode.get("$schema") != "https://opencode.ai/config.json":
        raise ValueError(f"OpenCode schema mismatch: {opencode_path}")
    if opencode.get("skills", {}).get("paths") != ["./skills"]:
        raise ValueError(f"OpenCode Skill path mismatch: {opencode_path}")

    hermes_overrides = matrix["hosts"]["hermes"].get("description_overrides")
    if not isinstance(hermes_overrides, dict) or set(hermes_overrides) != set(required):
        raise ValueError("Hermes description overrides must cover the exact Skill cluster")
    if len(set(hermes_overrides.values())) != len(required):
        raise ValueError("Hermes description overrides must be unique")
    for skill_name, description in hermes_overrides.items():
        if (
            not isinstance(description, str)
            or not description
            or len(description) > 60
            or "\n" in description
            or '"' in description
        ):
            raise ValueError(
                f"Hermes description override must be 1-60 safe characters: "
                f"{skill_name}"
            )


def normalize_agents(matrix: dict[str, Any], requested: list[str]) -> list[str]:
    host_order = matrix.get("host_order")
    hosts = matrix.get("hosts")
    if not isinstance(host_order, list) or not isinstance(hosts, dict):
        raise ValueError("Host matrix does not define host_order and hosts")
    if set(host_order) != set(hosts):
        raise ValueError("Host matrix host_order does not match hosts")

    expanded: list[str] = []
    for agent in requested:
        if agent == "all":
            expanded.extend(host_order)
        else:
            expanded.append(agent)
    agents = list(dict.fromkeys(expanded))
    unknown = sorted(set(agents) - set(hosts))
    if unknown:
        raise ValueError(
            f"Unknown agent host(s): {', '.join(unknown)}. Supported: "
            f"{', '.join(host_order)}, all"
        )
    return agents


def _root_from_template(template: str, home: Path, project: Path) -> Path:
    rendered = template.format(home=str(home), project=str(project))
    return Path(rendered).expanduser().resolve()


def build_projections(
    matrix: dict[str, Any],
    agents: list[str],
    scope: str,
    home_root: Path,
    project_root: Path,
    host_environment: dict[str, str] | None = None,
) -> list[Projection]:
    environment = host_environment or {}
    grouped: dict[str, tuple[Path, list[str]]] = {}
    for agent in agents:
        host = matrix["hosts"][agent]
        template = host.get(f"{scope}_root")
        if template is None:
            note = host.get(f"{scope}_scope_note", "No target root is documented.")
            raise ValueError(f"{agent} does not support --scope {scope}: {note}")
        root = _root_from_template(template, home_root, project_root)
        if scope == "user":
            for override in host.get("user_root_overrides", []):
                requested_platform = override.get("platform")
                current_platform = "windows" if os.name == "nt" else "posix"
                if requested_platform and requested_platform != current_platform:
                    continue
                value = environment.get(override["environment"])
                if value:
                    root = (Path(value).expanduser() / override["suffix"]).resolve()
                    break
        key = os.path.normcase(str(root))
        if key not in grouped:
            grouped[key] = (root, [])
        grouped[key][1].append(agent)
    return [
        Projection(root=root, hosts=tuple(hosts))
        for root, hosts in grouped.values()
    ]


def _is_same_or_child(path: Path, parent: Path) -> bool:
    try:
        common = os.path.commonpath((str(path.resolve()), str(parent.resolve())))
    except ValueError:
        return False
    return os.path.normcase(common) == os.path.normcase(str(parent.resolve()))


def preflight(
    package: Package, projections: list[Projection], upgrade: bool
) -> dict[str, list[str]]:
    required = package.matrix["required_skills"]
    existing_by_root: dict[str, list[str]] = {}
    for projection in projections:
        if _is_same_or_child(projection.root, package.skills_root):
            raise ValueError(
                f"Refusing to install into the source Skill tree: {projection.root}"
            )
        existing: list[str] = []
        for skill_name in required:
            destination = projection.root / skill_name
            if destination.exists():
                existing.append(skill_name)
        existing_by_root[str(projection.root)] = existing
        if existing and not upgrade:
            raise FileExistsError(
                f"Refusing to overwrite existing installation at {projection.root}: "
                f"{', '.join(existing)}. Re-run with --upgrade after reviewing it."
            )
    return existing_by_root


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _project_skill(
    package: Package,
    skill_name: str,
    destination: Path,
    hosts: tuple[str, ...],
) -> None:
    source = package.skills_root / skill_name
    shutil.copytree(
        source,
        destination,
        ignore=shutil.ignore_patterns(*IGNORED_NAMES),
    )

    source_skill_file = source / "SKILL.md"
    projected_skill_file = destination / "SKILL.md"
    source_skill_bytes = source_skill_file.read_bytes()
    if source_skill_bytes.startswith(b"\xef\xbb\xbf"):
        raise ValueError(f"Canonical SKILL.md must not contain a UTF-8 BOM: {source_skill_file}")
    projected_skill_bytes = source_skill_bytes

    reference_names = sorted(
        {match.decode("ascii") for match in CROSS_REFERENCE.findall(source_skill_bytes)}
    )
    shared_root = destination / "references" / "shared"
    if shared_root.exists():
        raise ValueError(f"Projection output path already exists in canonical Skill: {shared_root}")
    shared_root.mkdir(parents=True)

    references: list[dict[str, str]] = []
    rewrites: list[dict[str, str]] = []
    for reference_name in reference_names:
        source_reference = (
            package.skills_root
            / "engineering-research-copilot"
            / "references"
            / reference_name
        )
        if not source_reference.is_file():
            raise ValueError(
                f"Cross-sibling reference is missing from the canonical umbrella: "
                f"{source_reference}"
            )
        reference_bytes = source_reference.read_bytes()
        if reference_bytes.startswith(b"\xef\xbb\xbf"):
            raise ValueError(
                f"Canonical shared reference must not contain a UTF-8 BOM: "
                f"{source_reference}"
            )
        projected_reference = shared_root / reference_name
        projected_reference.write_bytes(reference_bytes)
        old = (
            f"../engineering-research-copilot/references/{reference_name}"
        ).encode("ascii")
        new = f"references/shared/{reference_name}".encode("ascii")
        projected_skill_bytes = projected_skill_bytes.replace(old, new)
        source_hash = _sha256(reference_bytes)
        references.append(
            {
                "source": (
                    f"skills/engineering-research-copilot/references/{reference_name}"
                ),
                "projected": f"references/shared/{reference_name}",
                "source_sha256": source_hash,
                "projected_sha256": source_hash,
            }
        )
        rewrites.append(
            {
                "from": old.decode("ascii"),
                "to": new.decode("ascii"),
            }
        )

    frontmatter_changes: list[dict[str, str]] = []
    if "hermes" in hosts:
        description = package.matrix["hosts"]["hermes"][
            "description_overrides"
        ][skill_name]
        matches = list(DESCRIPTION_LINE.finditer(projected_skill_bytes))
        if len(matches) != 1:
            raise ValueError(
                f"Hermes projection requires exactly one quoted description line: "
                f"{source_skill_file}"
            )
        match = matches[0]
        replacement = (
            f'description: "{description}"'.encode("utf-8")
            + match.group("cr")
        )
        projected_skill_bytes = (
            projected_skill_bytes[: match.start()]
            + replacement
            + projected_skill_bytes[match.end() :]
        )
        frontmatter_changes.append(
            {
                "field": "description",
                "reason": "Hermes prompt index is limited to 60 characters",
                "projected_value": description,
            }
        )

    if CROSS_REFERENCE.search(projected_skill_bytes):
        raise ValueError(
            f"Projection still contains a cross-sibling reference: {skill_name}"
        )
    projected_skill_file.write_bytes(projected_skill_bytes)

    manifest = {
        "schema_version": PROJECTION_SCHEMA,
        "cluster_name": package.matrix["cluster_name"],
        "cluster_version": package.matrix["cluster_version"],
        "skill_name": skill_name,
        "hosts": list(hosts),
        "canonical_skill_md": f"skills/{skill_name}/SKILL.md",
        "source_skill_md_sha256": _sha256(source_skill_bytes),
        "projected_skill_md_sha256": _sha256(projected_skill_bytes),
        "references": references,
        "rewrites": rewrites,
        "frontmatter_changes": frontmatter_changes,
        "permission_changes": [],
        "generated_files": [
            *[entry["projected"] for entry in references],
            "references/shared/projection-manifest.json",
        ],
    }
    manifest_path = shared_root / "projection-manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def stage_projections(
    package: Package, projections: list[Projection]
) -> list[AppliedProjection]:
    applied: list[AppliedProjection] = []
    try:
        for projection in projections:
            root_existed = projection.root.exists()
            projection.root.mkdir(parents=True, exist_ok=True)
            stage_root = projection.root / (
                f".{package.matrix['cluster_name']}.stage-{uuid.uuid4().hex}"
            )
            stage_root.mkdir()
            state = AppliedProjection(
                projection=projection,
                stage_root=stage_root,
                root_existed=root_existed,
                backup_root=None,
                installed=[],
                backed_up=[],
            )
            applied.append(state)
            for skill_name in package.matrix["required_skills"]:
                _project_skill(
                    package,
                    skill_name,
                    stage_root / skill_name,
                    projection.hosts,
                )
        return applied
    except Exception:
        for state in applied:
            if state.stage_root.exists():
                shutil.rmtree(state.stage_root)
            if (
                not state.root_existed
                and state.projection.root.exists()
                and not any(state.projection.root.iterdir())
            ):
                state.projection.root.rmdir()
        raise


def apply_staged(package: Package, states: list[AppliedProjection]) -> None:
    required = package.matrix["required_skills"]
    try:
        for state in states:
            existing = [
                state.projection.root / name
                for name in required
                if (state.projection.root / name).exists()
            ]
            if existing:
                state.backup_root = state.projection.root / (
                    f".{package.matrix['cluster_name']}.backup-{uuid.uuid4().hex}"
                )
                state.backup_root.mkdir()
                for destination in existing:
                    backup = state.backup_root / destination.name
                    destination.replace(backup)
                    state.backed_up.append((destination, backup))

            for skill_name in required:
                source = state.stage_root / skill_name
                destination = state.projection.root / skill_name
                source.replace(destination)
                state.installed.append(destination)
    except Exception:
        for state in reversed(states):
            for destination in reversed(state.installed):
                if destination.exists():
                    shutil.rmtree(destination)
            for destination, backup in reversed(state.backed_up):
                if backup.exists():
                    backup.replace(destination)
            if state.backup_root and state.backup_root.exists():
                shutil.rmtree(state.backup_root)
            if (
                not state.root_existed
                and state.projection.root.exists()
                and not any(state.projection.root.iterdir())
            ):
                state.projection.root.rmdir()
        raise
    finally:
        for state in states:
            if state.stage_root.exists():
                shutil.rmtree(state.stage_root)
            if (
                not state.root_existed
                and state.projection.root.exists()
                and not any(state.projection.root.iterdir())
            ):
                state.projection.root.rmdir()

    for state in states:
        if state.backup_root and state.backup_root.exists():
            shutil.rmtree(state.backup_root)


def make_report(
    package: Package,
    projections: list[Projection],
    existing: dict[str, list[str]],
    scope: str,
    status: str,
) -> dict[str, Any]:
    return {
        "schema_version": REPORT_SCHEMA,
        "status": status,
        "cluster_name": package.matrix["cluster_name"],
        "cluster_version": package.matrix["cluster_version"],
        "projection_schema": PROJECTION_SCHEMA,
        "self_contained": True,
        "scope": scope,
        "source": str(package.repository_root),
        "skills": package.matrix["required_skills"],
        "projections": [
            {
                "root": str(projection.root),
                "hosts": list(projection.hosts),
                "existing_skills": existing[str(projection.root)],
            }
            for projection in projections
        ],
    }


def emit_report(report: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        return
    verb = "Planned" if report["status"] == "planned" else "Installed"
    print(
        f"{verb} {report['cluster_name']} {report['cluster_version']} "
        f"({len(report['skills'])} Skills)"
    )
    for projection in report["projections"]:
        print(f"  {', '.join(projection['hosts'])}: {projection['root']}")


def execute(args: argparse.Namespace, package: Package) -> int:
    validate_package(package)
    agents = normalize_agents(package.matrix, args.agent)
    home_root = (
        args.home_root.expanduser().resolve()
        if args.home_root is not None
        else Path.home().resolve()
    )
    project_root = args.project_root.expanduser().resolve()
    projections = build_projections(
        package.matrix,
        agents,
        args.scope,
        home_root,
        project_root,
        os.environ if args.home_root is None else {},
    )
    existing = preflight(package, projections, args.upgrade)
    if args.dry_run:
        emit_report(
            make_report(package, projections, existing, args.scope, "planned"),
            args.json,
        )
        return 0

    states = stage_projections(package, projections)
    apply_staged(package, states)
    emit_report(
        make_report(package, projections, existing, args.scope, "installed"),
        args.json,
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    package = local_package(args.source)
    if package is not None:
        return execute(args, package)

    with tempfile.TemporaryDirectory(
        prefix="engineering-research-workbench-"
    ) as temporary:
        package = download_package(args.ref, Path(temporary))
        return execute(args, package)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError, zipfile.BadZipFile) as error:
        print(f"Installation failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
