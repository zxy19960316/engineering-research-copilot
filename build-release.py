#!/usr/bin/env python3
"""Build a deterministic clean release of the Research Workbench cluster."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
from typing import Any
import zipfile


MATRIX_FILENAME = "agent-hosts.json"
RELEASE_SCHEMA = "engineering-research-clean-release.v1"
REPORT_SCHEMA = "engineering-research-clean-release-report.v1"
MANIFEST_FILENAME = "release-manifest.json"
PAYLOAD_POLICY = "git-tracked-explicit-allowlist"
ROOT_FILES = (
    ".claude-plugin/plugin.json",
    ".codex-plugin/plugin.json",
    MATRIX_FILENAME,
    "README.md",
    "SKILL.md",
    "install-skill.py",
    "opencode.json",
)
SEMVER = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)


@dataclass(frozen=True)
class PayloadFile:
    path: str
    payload: bytes


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate or build the deterministic clean Engineering Research "
            "Workbench release archive."
        )
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Repository root (default: directory containing this script).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="ZIP path to create. Required unless --check is used.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate and report the payload without writing an archive.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing output archive after validation succeeds.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the result as JSON.",
    )
    args = parser.parse_args(argv)
    if args.check and args.output is not None:
        parser.error("--check and --output are mutually exclusive")
    if not args.check and args.output is None:
        parser.error("--output is required unless --check is used")
    if args.check and args.force:
        parser.error("--force has no effect with --check")
    return args


def _load_index_json(repository_root: Path, relative: str) -> dict[str, Any]:
    entries = _tracked_entries(repository_root, (relative,))
    if len(entries) != 1 or entries[0][0] != relative:
        raise ValueError(f"Missing tracked JSON file: {relative}")
    _path, mode, object_id = entries[0]
    if mode != "100644":
        raise ValueError(f"Tracked JSON file has an unsupported mode: {relative}")
    try:
        payload = _read_index_blob(repository_root, object_id).decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(f"Tracked JSON file is not UTF-8: {relative}") from error
    value = json.loads(payload)
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be an object: {relative}")
    return value


def load_matrix(repository_root: Path) -> dict[str, Any]:
    matrix = _load_index_json(repository_root, MATRIX_FILENAME)
    required = matrix.get("required_skills")
    if (
        not isinstance(required, list)
        or not required
        or not all(isinstance(name, str) and name for name in required)
        or len(required) != len(set(required))
    ):
        raise ValueError("Host matrix must declare unique required skill names")
    version = matrix.get("cluster_version")
    if not isinstance(version, str) or not SEMVER.fullmatch(version):
        raise ValueError(f"Cluster version must be strict semver: {version!r}")
    if not isinstance(matrix.get("cluster_name"), str) or not matrix["cluster_name"]:
        raise ValueError("Host matrix must declare cluster_name")
    source_only = matrix.get("source_only_paths")
    if (
        not isinstance(source_only, list)
        or not source_only
        or not all(isinstance(path, str) and path for path in source_only)
        or source_only != sorted(source_only)
        or len(source_only) != len(set(source_only))
    ):
        raise ValueError("Host matrix must declare sorted unique source_only_paths")
    required_skills = set(required)
    for relative in source_only:
        _validate_relative_path(relative)
        parts = PurePosixPath(relative).parts
        if (
            len(parts) < 4
            or parts[0] != "skills"
            or parts[1] not in required_skills
            or parts[-1] == "SKILL.md"
        ):
            raise ValueError(
                f"Source-only path must be a non-entrypoint Skill file: {relative}"
            )
    return matrix


def _tracked_entries(
    repository_root: Path, pathspecs: tuple[str, ...]
) -> list[tuple[str, str, str]]:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(repository_root),
            "ls-files",
            "--stage",
            "-z",
            "--",
            *pathspecs,
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    entries: list[tuple[str, str, str]] = []
    for raw_entry in result.stdout.split(b"\0"):
        if not raw_entry:
            continue
        try:
            metadata, raw_path = raw_entry.split(b"\t", 1)
            mode_raw, object_id_raw, stage_raw = metadata.split(b" ")
            mode = mode_raw.decode("ascii")
            object_id = object_id_raw.decode("ascii")
            stage = stage_raw.decode("ascii")
            path = raw_path.decode("utf-8")
        except (UnicodeDecodeError, ValueError) as error:
            raise ValueError("Git returned an invalid tracked path entry") from error
        if stage != "0":
            raise ValueError(f"Release payload contains an unmerged path: {path}")
        entries.append((path, mode, object_id))
    return sorted(entries)


def _read_index_blob(repository_root: Path, object_id: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(repository_root), "cat-file", "blob", object_id],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout


def _validate_relative_path(path: str) -> None:
    pure = PurePosixPath(path)
    if (
        not path
        or "\\" in path
        or pure.is_absolute()
        or any(part in {"", ".", ".."} for part in pure.parts)
        or pure.as_posix() != path
    ):
        raise ValueError(f"Payload path is not canonical and relative: {path!r}")


def _validate_manifest_versions(
    repository_root: Path, matrix: dict[str, Any]
) -> None:
    expected_name = matrix["cluster_name"]
    expected_version = matrix["cluster_version"]
    for relative in (
        ".codex-plugin/plugin.json",
        ".claude-plugin/plugin.json",
    ):
        manifest = _load_index_json(repository_root, relative)
        if manifest.get("name") != expected_name:
            raise ValueError(f"Plugin name mismatch: {relative}")
        if manifest.get("version") != expected_version:
            raise ValueError(f"Plugin version mismatch: {relative}")


def collect_payload(
    repository_root: Path, matrix: dict[str, Any]
) -> list[PayloadFile]:
    repository_root = repository_root.resolve()
    _validate_manifest_versions(repository_root, matrix)
    entries = _tracked_entries(repository_root, (*ROOT_FILES, "skills"))
    paths = [path for path, _mode, _object_id in entries]
    if len(paths) != len(set(paths)):
        raise ValueError("Git payload enumeration contains duplicate paths")

    missing_roots = sorted(set(ROOT_FILES) - set(paths))
    if missing_roots:
        raise ValueError(f"Release root files are not tracked: {missing_roots}")

    source_only_paths = set(matrix["source_only_paths"])
    missing_source_only = sorted(source_only_paths - set(paths))
    if missing_source_only:
        raise ValueError(
            f"Declared source-only files are not tracked: {missing_source_only}"
        )

    required_skills = set(matrix["required_skills"])
    observed_skills: set[str] = set()
    payload: list[PayloadFile] = []
    for relative, mode, object_id in entries:
        _validate_relative_path(relative)
        allowed = relative in ROOT_FILES
        if relative.startswith("skills/"):
            parts = PurePosixPath(relative).parts
            if len(parts) < 3:
                raise ValueError(f"Skill payload path is incomplete: {relative}")
            skill_name = parts[1]
            observed_skills.add(skill_name)
            allowed = skill_name in required_skills
        if not allowed:
            raise ValueError(f"Tracked path is outside the release allowlist: {relative}")
        if mode == "120000":
            raise ValueError(f"Release payload must not contain symlinks: {relative}")
        if mode not in {"100644", "100755"}:
            raise ValueError(f"Unsupported Git file mode {mode}: {relative}")

        if relative in source_only_paths:
            continue
        content = _read_index_blob(repository_root, object_id)
        if (
            relative == "SKILL.md" or relative.endswith("/SKILL.md")
        ) and content.startswith(b"\xef\xbb\xbf"):
            raise ValueError(f"Canonical SKILL.md contains a UTF-8 BOM: {relative}")
        payload.append(PayloadFile(relative, content))

    if observed_skills != required_skills:
        raise ValueError(
            "Release Skill set mismatch: expected "
            f"{sorted(required_skills)}, found {sorted(observed_skills)}"
        )
    for skill_name in required_skills:
        skill_file = f"skills/{skill_name}/SKILL.md"
        if skill_file not in paths:
            raise ValueError(f"Release Skill is missing SKILL.md: {skill_name}")
    return sorted(payload, key=lambda item: item.path)


def build_manifest(
    matrix: dict[str, Any], files: list[PayloadFile]
) -> dict[str, Any]:
    return {
        "schema_version": RELEASE_SCHEMA,
        "cluster_name": matrix["cluster_name"],
        "cluster_version": matrix["cluster_version"],
        "payload_policy": PAYLOAD_POLICY,
        "file_count": len(files),
        "files": [
            {
                "path": item.path,
                "sha256": hashlib.sha256(item.payload).hexdigest(),
                "size": len(item.payload),
            }
            for item in files
        ],
    }


def _json_bytes(value: dict[str, Any]) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _zip_mode(path: str) -> int:
    if path == "install-skill.py":
        return 0o755
    parts = PurePosixPath(path).parts
    if "scripts" in parts and path.endswith((".py", ".sh", ".ps1")):
        return 0o755
    return 0o644


def _write_entry(bundle: zipfile.ZipFile, item: PayloadFile) -> None:
    info = zipfile.ZipInfo(item.path, date_time=FIXED_ZIP_TIME)
    info.compress_type = zipfile.ZIP_STORED
    info.create_system = 3
    info.external_attr = ((0o100000 | _zip_mode(item.path)) & 0xFFFF) << 16
    bundle.writestr(info, item.payload)


def _validate_archive(path: Path, files: list[PayloadFile]) -> None:
    expected = {item.path: item.payload for item in files}
    with zipfile.ZipFile(path) as bundle:
        names = bundle.namelist()
        if names != sorted(expected):
            raise ValueError("Release archive member order is not canonical")
        if len(names) != len(set(names)):
            raise ValueError("Release archive contains duplicate members")
        for name, payload in expected.items():
            if bundle.read(name) != payload:
                raise ValueError(f"Release archive payload mismatch: {name}")


def write_archive(
    output: Path,
    files: list[PayloadFile],
    manifest_bytes: bytes,
    force: bool,
) -> str:
    output = output.expanduser().resolve()
    if output.exists() and not force:
        raise FileExistsError(f"Refusing to overwrite existing release: {output}")
    if output.exists() and not output.is_file():
        raise ValueError(f"Release output is not a file: {output}")

    archive_files = sorted(
        [*files, PayloadFile(MANIFEST_FILENAME, manifest_bytes)],
        key=lambda item: item.path,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=f".{output.name}.",
            suffix=".tmp",
            dir=output.parent,
            delete=False,
        ) as temporary:
            temporary_name = temporary.name
        temporary_path = Path(temporary_name)
        with zipfile.ZipFile(temporary_path, mode="w") as bundle:
            for item in archive_files:
                _write_entry(bundle, item)
        _validate_archive(temporary_path, archive_files)
        os.replace(temporary_path, output)
        temporary_name = None
    finally:
        if temporary_name is not None:
            Path(temporary_name).unlink(missing_ok=True)
    return hashlib.sha256(output.read_bytes()).hexdigest()


def make_report(
    matrix: dict[str, Any],
    files: list[PayloadFile],
    manifest_bytes: bytes,
    status: str,
    output: Path | None = None,
    archive_sha256: str | None = None,
) -> dict[str, Any]:
    report: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA,
        "status": status,
        "cluster_name": matrix["cluster_name"],
        "cluster_version": matrix["cluster_version"],
        "payload_policy": PAYLOAD_POLICY,
        "skill_count": len(matrix["required_skills"]),
        "file_count": len(files),
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "side_effects": [],
    }
    if output is not None:
        report["output"] = str(output.expanduser().resolve())
        report["archive_sha256"] = archive_sha256
        report["side_effects"] = [
            {"operation": "write_release_archive", "path": report["output"]}
        ]
    return report


def emit_report(report: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        return
    if report["status"] == "valid":
        print(
            f"Valid clean release payload {report['cluster_name']} "
            f"{report['cluster_version']} ({report['file_count']} files)"
        )
    else:
        print(
            f"Built {report['cluster_name']} {report['cluster_version']} "
            f"at {report['output']}"
        )
        print(f"SHA-256: {report['archive_sha256']}")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repository_root = args.source.expanduser().resolve()
    matrix = load_matrix(repository_root)
    files = collect_payload(repository_root, matrix)
    manifest_bytes = _json_bytes(build_manifest(matrix, files))
    if args.check:
        emit_report(
            make_report(matrix, files, manifest_bytes, "valid"), args.json
        )
        return 0

    archive_sha256 = write_archive(
        args.output, files, manifest_bytes, args.force
    )
    emit_report(
        make_report(
            matrix,
            files,
            manifest_bytes,
            "built",
            args.output,
            archive_sha256,
        ),
        args.json,
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        OSError,
        ValueError,
        json.JSONDecodeError,
        subprocess.CalledProcessError,
        zipfile.BadZipFile,
    ) as error:
        print(f"Release build failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
