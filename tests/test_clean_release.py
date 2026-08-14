from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
import zipfile


REPO_ROOT = Path(__file__).resolve().parents[1]
BUILD_SCRIPT = REPO_ROOT / "build-release.py"
EXPECTED_VERSION = "0.7.0"
EXPECTED_TOP_LEVEL = {
    ".claude-plugin",
    ".codex-plugin",
    "agent-hosts.json",
    "install-skill.py",
    "opencode.json",
    "release-manifest.json",
    "skills",
}
FORBIDDEN_PREFIXES = (
    ".github/",
    "docs/",
    "evals/",
    "tests/",
)
FORBIDDEN_ROOT_FILES = {
    ".gitattributes",
    ".gitignore",
    "AGENTS.md",
    "PROJECT_PLAN.md",
    "README.md",
    "STATUS.md",
    "build-release.py",
}
LEGACY_SOURCE_ONLY_PATHS = (
    "skills/engineering-research-copilot/scripts/compose_m3_bundle.py",
    "skills/engineering-research-copilot/scripts/render_m1_map.py",
    "skills/engineering-research-copilot/scripts/validate_m1_bundle.py",
    "skills/engineering-research-copilot/scripts/validate_m2_direction_bundle.py",
    "skills/engineering-research-copilot/scripts/validate_m3_method_bundle.py",
)
MILESTONE_TOKEN = re.compile(
    rb"(?<![A-Za-z0-9])M[1-4](?:\.[0-9]+)*(?![A-Za-z0-9])"
)


def run_builder(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            str(BUILD_SCRIPT),
            *arguments,
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def run_release_installer(
    extracted: Path, home_root: Path
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            str(extracted / "install-skill.py"),
            "--source",
            str(extracted),
            "--agent",
            "all",
            "--scope",
            "user",
            "--home-root",
            str(home_root),
            "--dry-run",
            "--json",
        ],
        cwd=extracted,
        text=True,
        capture_output=True,
        check=False,
    )


class CleanReleaseTests(unittest.TestCase):
    maxDiff = None

    def test_cluster_version_is_bound_to_0_7_0_everywhere(self) -> None:
        matrix = json.loads(
            (REPO_ROOT / "agent-hosts.json").read_text(encoding="utf-8")
        )
        codex = json.loads(
            (REPO_ROOT / ".codex-plugin" / "plugin.json").read_text(
                encoding="utf-8"
            )
        )
        claude = json.loads(
            (REPO_ROOT / ".claude-plugin" / "plugin.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(EXPECTED_VERSION, matrix["cluster_version"])
        self.assertEqual(EXPECTED_VERSION, codex["version"])
        self.assertEqual(EXPECTED_VERSION, claude["version"])
        self.assertEqual(
            list(LEGACY_SOURCE_ONLY_PATHS), matrix["source_only_paths"]
        )
        for relative in LEGACY_SOURCE_ONLY_PATHS:
            self.assertTrue((REPO_ROOT / relative).is_file(), relative)

    def test_check_mode_is_read_only_and_reports_exact_policy(self) -> None:
        before = sorted(path.name for path in REPO_ROOT.iterdir())
        result = run_builder("--check", "--json")
        after = sorted(path.name for path in REPO_ROOT.iterdir())
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(before, after)
        report = json.loads(result.stdout)
        self.assertEqual("valid", report["status"])
        self.assertEqual(EXPECTED_VERSION, report["cluster_version"])
        self.assertEqual("git-tracked-explicit-allowlist", report["payload_policy"])
        self.assertEqual(9, report["skill_count"])
        self.assertGreater(report["file_count"], 9)
        self.assertEqual([], report["side_effects"])

    def test_archive_is_byte_deterministic_and_contains_only_release_files(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = root / "first.zip"
            second = root / "second.zip"
            first_result = run_builder("--output", str(first), "--json")
            second_result = run_builder("--output", str(second), "--json")
            self.assertEqual(0, first_result.returncode, first_result.stderr)
            self.assertEqual(0, second_result.returncode, second_result.stderr)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            first_report = json.loads(first_result.stdout)
            self.assertEqual(
                hashlib.sha256(first.read_bytes()).hexdigest(),
                first_report["archive_sha256"],
            )

            with zipfile.ZipFile(first) as bundle:
                names = bundle.namelist()
                self.assertEqual(sorted(names), names)
                self.assertEqual(len(names), len(set(names)))
                self.assertTrue(all(not name.endswith("/") for name in names))
                for entry in bundle.infolist():
                    self.assertEqual((1980, 1, 1, 0, 0, 0), entry.date_time)
                    self.assertEqual(zipfile.ZIP_STORED, entry.compress_type)

            top_level = {name.split("/", 1)[0] for name in names}
            self.assertEqual(EXPECTED_TOP_LEVEL, top_level)
            self.assertFalse(
                any(name.startswith(FORBIDDEN_PREFIXES) for name in names)
            )
            self.assertTrue(FORBIDDEN_ROOT_FILES.isdisjoint(names))
            self.assertTrue(set(LEGACY_SOURCE_ONLY_PATHS).isdisjoint(names))

            milestone_hits = []
            with zipfile.ZipFile(first) as bundle:
                for name in names:
                    if name.startswith("skills/") and name.endswith((".md", ".py")):
                        if MILESTONE_TOKEN.search(bundle.read(name)):
                            milestone_hits.append(name)
            self.assertEqual([], milestone_hits)

    def test_release_manifest_binds_every_payload_byte(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            archive = Path(temporary) / "release.zip"
            result = run_builder("--output", str(archive))
            self.assertEqual(0, result.returncode, result.stderr)
            with zipfile.ZipFile(archive) as bundle:
                names = bundle.namelist()
                manifest = json.loads(
                    bundle.read("release-manifest.json").decode("utf-8")
                )
                self.assertEqual(
                    "engineering-research-clean-release.v1",
                    manifest["schema_version"],
                )
                self.assertEqual(EXPECTED_VERSION, manifest["cluster_version"])
                self.assertEqual(
                    "git-tracked-explicit-allowlist",
                    manifest["payload_policy"],
                )
                paths = [entry["path"] for entry in manifest["files"]]
                self.assertEqual(sorted(paths), paths)
                self.assertEqual(len(paths), manifest["file_count"])
                self.assertEqual(
                    sorted(name for name in names if name != "release-manifest.json"),
                    paths,
                )
                for entry in manifest["files"]:
                    payload = bundle.read(entry["path"])
                    self.assertEqual(len(payload), entry["size"])
                    self.assertEqual(
                        hashlib.sha256(payload).hexdigest(), entry["sha256"]
                    )

    def test_extracted_release_is_installable_without_development_tree(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "release.zip"
            result = run_builder("--output", str(archive))
            self.assertEqual(0, result.returncode, result.stderr)
            extracted = root / "release"
            extracted.mkdir()
            with zipfile.ZipFile(archive) as bundle:
                bundle.extractall(extracted)

            install = run_release_installer(extracted, root / "home")
            self.assertEqual(0, install.returncode, install.stderr)
            report = json.loads(install.stdout)
            self.assertEqual("planned", report["status"])
            self.assertEqual(EXPECTED_VERSION, report["cluster_version"])
            self.assertEqual(9, len(report["skills"]))
            self.assertFalse((extracted / "evals").exists())
            self.assertFalse((extracted / "tests").exists())
            self.assertFalse((extracted / "docs").exists())

    def test_installer_rejects_modified_missing_and_extra_release_files(
        self,
    ) -> None:
        mutations = ("modified", "missing", "extra")
        for mutation in mutations:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                archive = root / "release.zip"
                result = run_builder("--output", str(archive))
                self.assertEqual(0, result.returncode, result.stderr)
                extracted = root / "release"
                extracted.mkdir()
                with zipfile.ZipFile(archive) as bundle:
                    bundle.extractall(extracted)

                skill = (
                    extracted
                    / "skills"
                    / "engineering-research-copilot"
                    / "SKILL.md"
                )
                if mutation == "modified":
                    skill.write_bytes(skill.read_bytes() + b"\n")
                elif mutation == "missing":
                    skill.unlink()
                else:
                    (extracted / "unexpected.txt").write_text(
                        "unexpected\n", encoding="utf-8", newline="\n"
                    )

                install = run_release_installer(extracted, root / "home")
                self.assertEqual(1, install.returncode)
                self.assertIn("release manifest", install.stderr.lower())
                self.assertFalse((root / "home").exists())

    def test_builder_refuses_to_overwrite_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            archive = Path(temporary) / "release.zip"
            archive.write_bytes(b"preserve-me")
            refused = run_builder("--output", str(archive))
            self.assertEqual(1, refused.returncode)
            self.assertEqual(b"preserve-me", archive.read_bytes())
            replaced = run_builder("--output", str(archive), "--force")
            self.assertEqual(0, replaced.returncode, replaced.stderr)
            self.assertTrue(zipfile.is_zipfile(archive))


if __name__ == "__main__":
    unittest.main()
