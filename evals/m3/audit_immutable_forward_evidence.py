#!/usr/bin/env python3
"""Compare immutable r2/r3 filesystem bytes with their exact Git blobs."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


IMMUTABLE_ROOTS = (
    "evals/m3/forward-inputs-r2",
    "evals/m3/results/forward-r2",
    "evals/m3/forward-inputs-r3",
    "evals/m3/results/forward-r3",
)
IMMUTABLE_REPORTS = (
    "evals/m3/results/2026-08-05-forward-evaluation-r2.md",
    "evals/m3/results/2026-08-06-forward-evaluation-r3.md",
)


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _git_files(repo_root: Path, ref: str) -> list[str]:
    completed = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", ref, "--", *IMMUTABLE_ROOTS, *IMMUTABLE_REPORTS],
        cwd=repo_root,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return []
    return sorted(
        line
        for line in completed.stdout.decode("utf-8", errors="strict").splitlines()
        if line
    )


def _git_blob(repo_root: Path, ref: str, relative_path: str) -> tuple[bytes | None, str | None]:
    content = subprocess.run(
        ["git", "show", f"{ref}:{relative_path}"],
        cwd=repo_root,
        capture_output=True,
        check=False,
    )
    object_id = subprocess.run(
        ["git", "rev-parse", f"{ref}:{relative_path}"],
        cwd=repo_root,
        capture_output=True,
        check=False,
        text=True,
        encoding="ascii",
    )
    if content.returncode != 0 or object_id.returncode != 0:
        return None, None
    return content.stdout, object_id.stdout.strip()


def compare_file_bytes(path: Path, baseline: bytes, relative_path: str) -> dict[str, Any]:
    raw = path.read_bytes()
    return {
        "path": relative_path,
        "byte_length": len(raw),
        "filesystem_raw_sha256": _sha256(raw),
        "baseline_raw_sha256": _sha256(baseline),
        "bytes_equal": raw == baseline,
    }


def audit_repository(repo_root: Path, ref: str = "HEAD") -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    errors: list[str] = []
    paths = _git_files(repo_root, ref)
    if not paths:
        errors.append("immutable_git_file_list_unavailable")
    for relative_path in paths:
        path = repo_root / Path(relative_path)
        baseline, object_id = _git_blob(repo_root, ref, relative_path)
        if baseline is None:
            files.append(
                {
                    "path": relative_path,
                    "bytes_equal": False,
                    "filesystem_status": "not_checked",
                    "git_blob_status": "unavailable",
                }
            )
            errors.append(f"git_blob_unavailable:{relative_path}")
            continue
        if not path.is_file():
            files.append(
                {
                    "path": relative_path,
                    "bytes_equal": False,
                    "filesystem_status": "missing",
                    "git_blob_object_id": object_id,
                    "git_blob_raw_sha256": _sha256(baseline),
                }
            )
            errors.append(f"filesystem_file_missing:{relative_path}")
            continue
        raw = path.read_bytes()
        equal = raw == baseline
        files.append(
            {
                "path": relative_path,
                "byte_length": len(raw),
                "filesystem_raw_sha256": _sha256(raw),
                "git_blob_raw_sha256": _sha256(baseline),
                "git_blob_object_id": object_id,
                "bytes_equal": equal,
            }
        )
        if not equal:
            errors.append(f"filesystem_git_blob_mismatch:{relative_path}")
    return {
        "schema_version": "m3.1-forward-immutable-byte-audit-r4-v1",
        "baseline_ref": ref,
        "status": "valid" if not errors else "invalid",
        "files": files,
        "errors": sorted(set(errors)),
    }


def _write_new(path: Path, value: dict[str, Any]) -> bool:
    try:
        with path.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            handle.write("\n")
    except (FileExistsError, OSError):
        return False
    return True


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if len(arguments) != 1:
        return 2
    result = audit_repository(Path(__file__).resolve().parents[2])
    if not _write_new(Path(arguments[0]), result):
        return 2
    return 0 if result["status"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
