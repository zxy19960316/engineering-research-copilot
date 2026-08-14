from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Iterable


SOURCE_BASELINE_COMMIT = "eb0f2ebc3d0c0a02802ee1cc395c1e705f8ade42"
SOURCE_ROOT = Path("skills/engineering-research-copilot")
VARIANTS_ROOT = Path("evals/m4/variants")
MANIFEST_PATH = VARIANTS_ROOT / "variant-manifest.json"
ARM_IDS = ("N", "F", "A1", "A2", "A3")

REMOVED_CAPABILITIES = {
    "N": ["all_skill_instructions"],
    "F": [],
    "A1": ["citation_verification", "evidence_integrity"],
    "A2": ["direction_confirmation", "route_binding"],
    "A3": ["method_cards", "uncertainty", "stop_pivot", "safety_boundary"],
}

LABELS = {
    "N": "No-Skill control",
    "F": "Frozen full M3-closed Skill",
    "A1": "Citation-verification and evidence-integrity ablation",
    "A2": "Direction-confirmation and route-binding ablation",
    "A3": "Method-card, uncertainty, stop-pivot, and safety-boundary ablation",
}

DROPPED_SECTIONS: dict[str, dict[str, frozenset[str]]] = {
    "A2": {
        "SKILL.md": frozenset({"## Enforce the direction gate"}),
        "references/core-direction-decision.md": frozenset(
            {
                "## Contents",
                "## Require user confirmation",
                "## Validate post-confirmation route output",
            }
        ),
        "references/core-method-coaching.md": frozenset(
            {
                "## Contents",
                "## Follow the M3 state flow",
                "## Derive the trusted M2 context",
                "## Choose the coaching mode",
            }
        ),
    },
    "A3": {
        "SKILL.md": frozenset({"## Coach methods with bounded claims"}),
        "references/core-citation-integrity.md": frozenset(
            {"## Contents", "## Apply the preprint contract"}
        ),
        "references/core-direction-decision.md": frozenset(
            {
                "## Contents",
                "## Enforce preprint support policy",
                "## Define a minimum decisive test",
                "## Validate post-confirmation route output",
            }
        ),
    },
}

DROP_EXACT_LINES: dict[str, dict[str, frozenset[str]]] = {
    "A1": {
        "SKILL.md": frozenset(
            {
                "- Use only verified metadata in final citations; never guess identifiers.",
                "- State whether reasoning is metadata-, abstract-, or full-text-level.",
                "- Keep verified preprints out of sole support for main directions and safety-related conclusions.",
            }
        )
    },
    "A2": {
        "SKILL.md": frozenset(
            {
                "  -> user direction confirmation",
                "| Plan an experiment, simulation, or minimum decisive test | Use the direction-decision rules above; require `user_confirmed` direction status first |",
            }
        )
    },
    "A3": {
        "SKILL.md": frozenset(
            {
                "| Coach an engineering method | [Method coaching](references/core-method-coaching.md), then load only the applicable family: [Experiment, measurement, and UQ](references/method-experiment-measurement-uq.md), [Modeling, simulation, and VVUQ](references/method-modeling-simulation-vvuq.md), [Control, optimization, and identification](references/method-control-optimization-identification.md), [Signal processing and diagnostics](references/method-signal-diagnostics.md), [Data, machine learning, and hybrid methods](references/method-data-ml-hybrid.md), or [Reliability, safety, and risk](references/method-reliability-safety-risk.md); for nuclear engineering × ML, also apply the additive [Nuclear engineering × machine learning overlay](references/domain-nuclear-ml.md) |",
                "- uncertainty, sensitivity, and validity checks;",
                "- Go, Stop, and Pivot conditions;",
            }
        )
    },
}

EXACT_REPLACEMENTS: dict[str, dict[str, tuple[tuple[str, str], ...]]] = {
    "A1": {
        "SKILL.md": (
            ("verified DOI/author/title metadata, ", ""),
            ("verified literature", "literature"),
            (", [Citation integrity](references/core-citation-integrity.md)", ""),
            (" and, when papers are used, the citation-integrity rules above", ""),
            ("Apply Citation integrity to candidate admission and recommendation eligibility, ", ""),
        )
    },
    "A2": {
        "SKILL.md": (
            (
                "Load and apply Method coaching. Validate the confirmed M2 bundle before deriving claims, metrics, preconditions, conditions, resources, or sources. Keep coaching bounded when no route exists, and instantiate route-specific cards only from a compatible route. Treat domain-specific standards and safety judgments as specialist review boundaries.",
                "Load and apply Method coaching. Treat domain-specific standards and safety judgments as specialist review boundaries.",
            ),
        )
    },
    "A3": {
        "SKILL.md": (
            (
                " with numeric success, stop, and pivot thresholds for each formal direction",
                " for each formal direction",
            ),
        )
    },
}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git_bytes(repo_root: Path, *args: str) -> bytes:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        message = completed.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {message}")
    return completed.stdout


def _source_files(repo_root: Path) -> list[str]:
    output = _git_bytes(
        repo_root,
        "ls-tree",
        "-r",
        "--name-only",
        SOURCE_BASELINE_COMMIT,
        "--",
        SOURCE_ROOT.as_posix(),
    ).decode("utf-8")
    prefix = f"{SOURCE_ROOT.as_posix()}/"
    selected: list[str] = []
    for full_path in output.splitlines():
        if full_path == f"{SOURCE_ROOT.as_posix()}/SKILL.md":
            selected.append("SKILL.md")
        elif full_path.startswith(f"{prefix}references/") and full_path.endswith(".md"):
            selected.append(full_path.removeprefix(prefix))
    if "SKILL.md" not in selected or not any(path.startswith("references/") for path in selected):
        raise RuntimeError("frozen Skill instruction corpus is incomplete")
    return sorted(selected, key=lambda value: (value != "SKILL.md", value))


def _source_blob(repo_root: Path, relative_path: str) -> bytes:
    full_path = (SOURCE_ROOT / relative_path).as_posix()
    return _git_bytes(repo_root, "show", f"{SOURCE_BASELINE_COMMIT}:{full_path}")


def _decode_normalized(data: bytes, relative_path: str) -> str:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RuntimeError(f"source is not UTF-8: {relative_path}") from exc
    return text.replace("\r\n", "\n").replace("\r", "\n")


def drop_markdown_sections(text: str, headings: frozenset[str]) -> str:
    if not headings:
        return text.rstrip() + "\n"
    seen: set[str] = set()
    kept: list[str] = []
    skipping_level: int | None = None
    for line in text.splitlines():
        level = len(line) - len(line.lstrip("#")) if line.startswith("#") else 0
        if line in headings:
            seen.add(line)
            skipping_level = level
            continue
        if skipping_level is not None and level and level <= skipping_level:
            skipping_level = None
        if skipping_level is None:
            kept.append(line)
    missing = sorted(headings - seen)
    if missing:
        raise RuntimeError(f"missing frozen headings: {missing}")
    return "\n".join(kept).rstrip() + "\n"


def _drop_exact_lines(text: str, lines_to_drop: frozenset[str]) -> str:
    if not lines_to_drop:
        return text
    lines = text.splitlines()
    present = set(lines)
    missing = sorted(lines_to_drop - present)
    if missing:
        raise RuntimeError(f"missing frozen lines: {missing}")
    return "\n".join(line for line in lines if line not in lines_to_drop).rstrip() + "\n"


def _replace_exact(text: str, replacements: Iterable[tuple[str, str]]) -> str:
    updated = text
    for old, new in replacements:
        if old not in updated:
            raise RuntimeError(f"missing frozen replacement source: {old}")
        updated = updated.replace(old, new)
    return updated.rstrip() + "\n"


def _included_files(arm_id: str, source_files: list[str]) -> list[str]:
    if arm_id == "N":
        return []
    if arm_id == "A1":
        return [path for path in source_files if path != "references/core-citation-integrity.md"]
    if arm_id == "A3":
        return [
            path
            for path in source_files
            if path != "references/core-method-coaching.md"
            and path != "references/domain-nuclear-ml.md"
            and not path.startswith("references/method-")
        ]
    return list(source_files)


def render_variants(repo_root: Path) -> tuple[dict[str, bytes], dict[str, bytes]]:
    source_files = _source_files(repo_root)
    source_blobs = {path: _source_blob(repo_root, path) for path in source_files}
    rendered: dict[str, bytes] = {}
    for arm_id in ("F", "A1", "A2", "A3"):
        parts = ["# Frozen Engineering Research Instructions\n"]
        for relative_path in _included_files(arm_id, source_files):
            text = _decode_normalized(source_blobs[relative_path], relative_path)
            text = drop_markdown_sections(
                text,
                DROPPED_SECTIONS.get(arm_id, {}).get(relative_path, frozenset()),
            )
            text = _drop_exact_lines(
                text,
                DROP_EXACT_LINES.get(arm_id, {}).get(relative_path, frozenset()),
            )
            text = _replace_exact(
                text,
                EXACT_REPLACEMENTS.get(arm_id, {}).get(relative_path, ()),
            )
            parts.append(
                f"\n<!-- source: {relative_path}; source_sha256: {_sha256(source_blobs[relative_path])} -->\n{text}"
            )
        rendered[arm_id] = "".join(parts).rstrip().encode("utf-8") + b"\n"
    return rendered, source_blobs


def build_manifest(
    repo_root: Path,
    rendered: dict[str, bytes],
    source_blobs: dict[str, bytes],
) -> dict[str, object]:
    source_files = list(source_blobs)
    source_tree_oid = _git_bytes(
        repo_root,
        "rev-parse",
        f"{SOURCE_BASELINE_COMMIT}:{SOURCE_ROOT.as_posix()}",
    ).decode("ascii").strip()
    arms: dict[str, object] = {}
    for arm_id in ARM_IDS:
        included = _included_files(arm_id, source_files)
        data = rendered.get(arm_id)
        arms[arm_id] = {
            "label": LABELS[arm_id],
            "instruction_path": (
                (VARIANTS_ROOT / arm_id / "instructions.md").as_posix()
                if data is not None
                else None
            ),
            "instruction_sha256": _sha256(data) if data is not None else None,
            "instruction_bytes": len(data) if data is not None else 0,
            "included_source_files": included,
            "excluded_source_files": sorted(set(source_files) - set(included)),
            "dropped_sections": {
                path: sorted(headings)
                for path, headings in DROPPED_SECTIONS.get(arm_id, {}).items()
            },
            "removed_capabilities": REMOVED_CAPABILITIES[arm_id],
        }
    return {
        "schema_version": "m4-variant-manifest-v1",
        "source_baseline_commit": SOURCE_BASELINE_COMMIT,
        "source_tree_git_oid": source_tree_oid,
        "source_root": SOURCE_ROOT.as_posix(),
        "source_files": {path: _sha256(data) for path, data in source_blobs.items()},
        "arms": arms,
    }


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def build_variants(repo_root: Path, *, write: bool = True) -> dict[str, object]:
    rendered, source_blobs = render_variants(repo_root)
    manifest = build_manifest(repo_root, rendered, source_blobs)
    if write:
        for arm_id, data in rendered.items():
            path = repo_root / VARIANTS_ROOT / arm_id / "instructions.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        manifest_path = repo_root / MANIFEST_PATH
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_bytes(_json_bytes(manifest))
    return manifest


def check_variants(repo_root: Path) -> dict[str, object]:
    rendered, source_blobs = render_variants(repo_root)
    manifest = build_manifest(repo_root, rendered, source_blobs)
    mismatches: list[str] = []
    for arm_id, expected in rendered.items():
        path = repo_root / VARIANTS_ROOT / arm_id / "instructions.md"
        if not path.is_file():
            mismatches.append(f"missing_instructions:{arm_id}")
        elif path.read_bytes() != expected:
            mismatches.append(f"instruction_bytes_mismatch:{arm_id}")
    no_skill_path = repo_root / VARIANTS_ROOT / "N" / "instructions.md"
    if no_skill_path.exists():
        mismatches.append("no_skill_instructions_must_be_absent")
    manifest_path = repo_root / MANIFEST_PATH
    if not manifest_path.is_file():
        mismatches.append("variant_manifest_missing")
    elif manifest_path.read_bytes() != _json_bytes(manifest):
        mismatches.append("variant_manifest_bytes_mismatch")
    return {
        "status": "valid" if not mismatches else "invalid",
        "mismatches": mismatches,
        "source_file_count": len(source_blobs),
        "rendered_arm_count": len(rendered),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[3]
    if args.check:
        result = check_variants(repo_root)
    else:
        manifest = build_variants(repo_root, write=True)
        result = {
            "status": "generated",
            "arm_count": len(manifest["arms"]),
            "source_file_count": len(manifest["source_files"]),
        }
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return 0 if result["status"] in {"generated", "valid"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
