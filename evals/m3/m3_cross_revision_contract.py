#!/usr/bin/env python3
"""Strict, read-only primitives for the M3 cross-revision evidence aggregate."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]

R5_HEAD = "1b696bce53ee0a11163bfe4f91a9a49ab3af6f49"
R5_1_HEAD = "fb5eec44bbf86446cf12bda2bddc76fcb07a7e69"
R5_2_ARTIFACT_HEAD = "13dd2f485a32b30e60f7b962cd784cc8bdfe2521"
GATE3_HEAD = "ea8a7bbb8b365aded89f9ddb5c784f6e95a51d3d"

SELECTED_REVISIONS = {
    "m3-f01": "r5",
    "m3-f02": "r5.2-f02",
    "m3-f03": "r5",
    "m3-f04": "r5",
    "m3-f05": "r5",
}
COUNTER_KEYS = ("tasks", "finalizations", "composer", "validator", "accepted", "failed", "retry")
SELECTED_COUNTERS = {
    "tasks": 5,
    "finalizations": 5,
    "composer": 4,
    "validator": 5,
    "accepted": 5,
    "failed": 0,
    "retry": 0,
}
HISTORICAL_COUNTERS = {
    "tasks": 7,
    "finalizations": 7,
    "composer": 6,
    "validator": 5,
    "accepted": 5,
    "failed": 2,
    "retry": 0,
}

ARTIFACT_REF_KEYS = {
    "path",
    "source_head",
    "git_blob_oid",
    "byte_length",
    "raw_sha256",
    "json_status",
}
JSON_ARTIFACT_REF_KEYS = ARTIFACT_REF_KEYS | {"canonical_sha256"}
_HEX_40 = re.compile(r"[0-9a-f]{40}\Z")
_HEX_64 = re.compile(r"[0-9a-f]{64}\Z")
_ARTIFACT_CACHE: dict[tuple[str, str, str], dict[str, Any]] = {}


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _reject_duplicate_pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in items:
        if key in value:
            raise ValueError(f"duplicate_key:{key}")
        value[key] = item
    return value


def _reject_constant(token: str) -> Any:
    raise ValueError(f"nonfinite_number:{token}")


def parse_strict_object(raw: bytes) -> dict[str, Any]:
    """Parse exactly one UTF-8 JSON object with closed lexical hazards."""

    if raw.startswith(b"\xef\xbb\xbf"):
        raise ValueError("utf8_bom_forbidden")
    try:
        text = raw.decode("utf-8", errors="strict")
        value = json.loads(
            text,
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=_reject_constant,
        )
    except UnicodeError as exc:
        raise ValueError("invalid_utf8") from exc
    except json.JSONDecodeError as exc:
        raise ValueError("invalid_json") from exc
    if not isinstance(value, dict):
        raise ValueError("object_required")
    return value


def load_strict_object(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ValueError("file_unavailable") from exc
    return parse_strict_object(raw)


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return _sha256(canonical_bytes(value))


def _relative_git_path(path: str) -> str:
    if not isinstance(path, str) or not path or "\\" in path or ":" in path:
        raise ValueError("git_path_invalid")
    candidate = PurePosixPath(path)
    if candidate.is_absolute() or any(part in {"", ".", ".."} for part in candidate.parts):
        raise ValueError("git_path_invalid")
    normalized = candidate.as_posix()
    if normalized != path:
        raise ValueError("git_path_invalid")
    return normalized


def _git(repo_root: Path, arguments: list[str], *, text: bool) -> subprocess.CompletedProcess[Any]:
    try:
        return subprocess.run(
            ["git", *arguments],
            cwd=repo_root,
            capture_output=True,
            check=False,
            text=text,
            encoding="utf-8" if text else None,
        )
    except OSError as exc:
        raise ValueError("git_unavailable") from exc


def git_artifact(repo_root: Path, head: str, path: str) -> dict[str, Any]:
    """Return the exact Git-object identity for a historical artifact."""

    relative = _relative_git_path(path)
    if not isinstance(head, str) or _HEX_40.fullmatch(head) is None:
        raise ValueError("source_head_invalid")
    cache_key = (str(repo_root.resolve()), head, relative)
    cached = _ARTIFACT_CACHE.get(cache_key)
    if cached is not None:
        return dict(cached)
    commit = _git(repo_root, ["cat-file", "-e", f"{head}^{{commit}}"], text=False)
    if commit.returncode != 0:
        raise ValueError("source_head_unavailable")
    ancestor = _git(repo_root, ["merge-base", "--is-ancestor", head, "HEAD"], text=False)
    if ancestor.returncode != 0:
        raise ValueError("source_head_not_ancestor")
    resolved = _git(repo_root, ["rev-parse", f"{head}:{relative}"], text=True)
    oid = resolved.stdout.strip() if resolved.returncode == 0 else ""
    if _HEX_40.fullmatch(oid) is None:
        raise ValueError("git_blob_unavailable")
    kind = _git(repo_root, ["cat-file", "-t", oid], text=True)
    if kind.returncode != 0 or kind.stdout.strip() != "blob":
        raise ValueError("git_object_not_blob")
    blob = _git(repo_root, ["cat-file", "blob", oid], text=False)
    if blob.returncode != 0:
        raise ValueError("git_blob_unavailable")
    raw = bytes(blob.stdout)
    result: dict[str, Any] = {
        "path": relative,
        "source_head": head,
        "git_blob_oid": oid,
        "byte_length": len(raw),
        "raw_sha256": _sha256(raw),
    }
    try:
        value = parse_strict_object(raw)
    except ValueError:
        result["json_status"] = "not_applicable"
    else:
        result["json_status"] = "valid"
        result["canonical_sha256"] = canonical_sha256(value)
    _ARTIFACT_CACHE[cache_key] = dict(result)
    return dict(result)


def validate_artifact_ref(
    ref: object,
    *,
    repo_root: Path,
    expected_head: str,
    allowed_prefixes: tuple[str, ...],
    json_required: bool,
) -> list[str]:
    """Validate one closed artifact reference against an exact historical blob."""

    errors: list[str] = []
    if not isinstance(ref, dict):
        return ["artifact_ref_object_required"]
    expected_keys = JSON_ARTIFACT_REF_KEYS if json_required else ARTIFACT_REF_KEYS
    if set(ref) != expected_keys:
        errors.append("artifact_ref_keys_invalid")
    raw_path = ref.get("path")
    try:
        path = _relative_git_path(raw_path)
    except (TypeError, ValueError):
        errors.append("artifact_ref_path_invalid")
        path = None
    if path is not None and not any(
        path == prefix.rstrip("/") or path.startswith(prefix.rstrip("/") + "/")
        for prefix in allowed_prefixes
    ):
        errors.append("artifact_ref_path_not_allowed")
    if ref.get("source_head") != expected_head:
        errors.append("artifact_ref_source_head_mismatch")
    if path is None or errors:
        return sorted(set(errors))
    try:
        actual = git_artifact(repo_root, expected_head, path)
    except ValueError:
        return sorted(set([*errors, "artifact_ref_unavailable"]))
    if json_required and actual.get("json_status") != "valid":
        errors.append("artifact_ref_json_required")
    for key in expected_keys:
        if ref.get(key) != actual.get(key):
            errors.append(f"artifact_ref_{key}_mismatch")
    if not isinstance(ref.get("git_blob_oid"), str) or _HEX_40.fullmatch(ref["git_blob_oid"]) is None:
        errors.append("artifact_ref_git_blob_oid_invalid")
    if not isinstance(ref.get("raw_sha256"), str) or _HEX_64.fullmatch(ref["raw_sha256"]) is None:
        errors.append("artifact_ref_raw_sha256_invalid")
    if json_required and (
        not isinstance(ref.get("canonical_sha256"), str)
        or _HEX_64.fullmatch(ref["canonical_sha256"]) is None
    ):
        errors.append("artifact_ref_canonical_sha256_invalid")
    return sorted(set(errors))


def validate_exact_keys(value: object, expected: set[str], code: str) -> list[str]:
    if not isinstance(value, dict):
        return [f"{code}_object_required"]
    return [] if set(value) == expected else [f"{code}_keys_invalid"]
