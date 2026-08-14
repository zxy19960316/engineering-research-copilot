from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock
import zipfile


REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALLER_PATH = REPO_ROOT / "install-skill.py"
SPEC = importlib.util.spec_from_file_location("install_skill", INSTALLER_PATH)
assert SPEC is not None and SPEC.loader is not None
INSTALLER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = INSTALLER
SPEC.loader.exec_module(INSTALLER)

EXPECTED_SKILLS = {
    "engineering-research-copilot",
    "research-cross-review",
    "research-data-comparison",
    "research-direction-evidence",
    "research-evidence-adversary",
    "research-figure-workflow",
    "research-literature-evidence",
    "research-manuscript",
    "research-method-transfer",
}
EXPECTED_HOSTS = {
    "codex",
    "claude-code",
    "opencode",
    "hermes",
    "openclaw",
    "github-copilot",
}
LEGACY_SOURCE_ONLY_PATHS = (
    "skills/engineering-research-copilot/scripts/compose_m3_bundle.py",
    "skills/engineering-research-copilot/scripts/render_m1_map.py",
    "skills/engineering-research-copilot/scripts/validate_m1_bundle.py",
    "skills/engineering-research-copilot/scripts/validate_m2_direction_bundle.py",
    "skills/engineering-research-copilot/scripts/validate_m3_method_bundle.py",
)


def _tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class AgentHostProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        package = INSTALLER.package_from_path(REPO_ROOT)
        assert package is not None
        cls.package = package

    def test_matrix_and_native_manifests_bind_one_cluster_version(self):
        matrix = self.package.matrix
        self.assertEqual(
            "engineering-research-agent-hosts.v1", matrix["schema_version"]
        )
        self.assertEqual("0.7.0", matrix["cluster_version"])
        self.assertEqual(EXPECTED_SKILLS, set(matrix["required_skills"]))
        self.assertEqual(EXPECTED_HOSTS, set(matrix["hosts"]))

        for relative in (
            ".codex-plugin/plugin.json",
            ".claude-plugin/plugin.json",
        ):
            with self.subTest(manifest=relative):
                manifest = json.loads(
                    (REPO_ROOT / relative).read_text(encoding="utf-8")
                )
                self.assertEqual(matrix["cluster_name"], manifest["name"])
                self.assertEqual(matrix["cluster_version"], manifest["version"])

        opencode = json.loads((REPO_ROOT / "opencode.json").read_text(encoding="utf-8"))
        self.assertEqual("https://opencode.ai/config.json", opencode["$schema"])
        self.assertEqual(["./skills"], opencode["skills"]["paths"])

    def test_source_cluster_is_portable_without_host_frontmatter_rewrites(self):
        INSTALLER.validate_package(self.package)
        allowed = set(self.package.matrix["portable_frontmatter_keys"])
        for skill_name in sorted(EXPECTED_SKILLS):
            with self.subTest(skill=skill_name):
                values, keys = INSTALLER._frontmatter(
                    REPO_ROOT / "skills" / skill_name / "SKILL.md"
                )
                self.assertEqual(skill_name, values["name"])
                self.assertTrue(values["description"])
                self.assertLessEqual(keys, allowed)
                self.assertNotIn("disable-model-invocation", keys)
                self.assertNotIn("user-invocable", keys)

    def test_user_projection_uses_each_host_documented_native_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            agents = INSTALLER.normalize_agents(self.package.matrix, ["all"])
            projections = INSTALLER.build_projections(
                self.package.matrix,
                agents,
                "user",
                base / "home",
                base / "project",
            )
            observed = {
                host: projection.root
                for projection in projections
                for host in projection.hosts
            }
            expected = {
                "codex": base / "home" / ".agents" / "skills",
                "claude-code": base / "home" / ".claude" / "skills",
                "opencode": base / "home" / ".config" / "opencode" / "skills",
                "hermes": base / "home" / ".hermes" / "skills",
                "openclaw": base / "home" / ".openclaw" / "skills",
                "github-copilot": base / "home" / ".copilot" / "skills",
            }
            self.assertEqual(
                {host: path.resolve() for host, path in expected.items()}, observed
            )

    def test_project_projection_deduplicates_shared_agents_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            agents = INSTALLER.normalize_agents(
                self.package.matrix,
                ["codex", "claude-code", "opencode", "openclaw", "github-copilot"],
            )
            projections = INSTALLER.build_projections(
                self.package.matrix,
                agents,
                "project",
                base / "home",
                base / "project",
            )
            by_root = {str(item.root): item.hosts for item in projections}
            shared = str((base / "project" / ".agents" / "skills").resolve())
            self.assertEqual(("codex", "openclaw"), by_root[shared])
            self.assertEqual(4, len(projections))

    def test_documented_host_environment_overrides_are_respected(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            projections = INSTALLER.build_projections(
                self.package.matrix,
                ["opencode", "hermes", "openclaw"],
                "user",
                base / "home",
                base / "project",
                {
                    "OPENCODE_CONFIG_DIR": str(base / "oc-config"),
                    "HERMES_HOME": str(base / "hermes-home"),
                    "OPENCLAW_STATE_DIR": str(base / "claw-state"),
                },
            )
            observed = {
                host: projection.root
                for projection in projections
                for host in projection.hosts
            }
            self.assertEqual((base / "oc-config" / "skills").resolve(), observed["opencode"])
            self.assertEqual(
                (base / "hermes-home" / "skills").resolve(), observed["hermes"]
            )
            self.assertEqual((base / "claw-state" / "skills").resolve(), observed["openclaw"])

    def test_hermes_project_scope_fails_closed_before_writing(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            project = base / "project"
            with self.assertRaisesRegex(ValueError, "external_dirs"):
                INSTALLER.build_projections(
                    self.package.matrix,
                    ["hermes"],
                    "project",
                    base / "home",
                    project,
                )
            self.assertFalse(project.exists())

    def test_dry_run_reports_exact_plan_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            stream = io.StringIO()
            argv = [
                "--source",
                str(REPO_ROOT),
                "--agent",
                "codex",
                "--agent",
                "claude-code",
                "--scope",
                "user",
                "--home-root",
                str(base / "home"),
                "--dry-run",
                "--json",
            ]
            with contextlib.redirect_stdout(stream):
                self.assertEqual(0, INSTALLER.main(argv))
            report = json.loads(stream.getvalue())
            self.assertEqual("planned", report["status"])
            self.assertEqual(INSTALLER.PROJECTION_SCHEMA, report["projection_schema"])
            self.assertTrue(report["self_contained"])
            self.assertEqual(EXPECTED_SKILLS, set(report["skills"]))
            self.assertEqual(2, len(report["projections"]))
            self.assertFalse((base / "home").exists())

    def test_user_install_generates_self_contained_auditable_projections(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            stream = io.StringIO()
            argv = [
                "--source",
                str(REPO_ROOT),
                "--agent",
                "all",
                "--scope",
                "user",
                "--home-root",
                str(base / "home"),
                "--json",
            ]
            with contextlib.redirect_stdout(stream):
                self.assertEqual(0, INSTALLER.main(argv))
            report = json.loads(stream.getvalue())
            self.assertEqual("installed", report["status"])
            self.assertEqual(INSTALLER.PROJECTION_SCHEMA, report["projection_schema"])
            self.assertTrue(report["self_contained"])
            self.assertEqual(6, len(report["projections"]))

            for projection in report["projections"]:
                root = Path(projection["root"])
                self.assertEqual(
                    EXPECTED_SKILLS,
                    {
                        path.name
                        for path in root.iterdir()
                        if path.is_dir() and not path.name.startswith(".")
                    },
                )
                for skill_name in EXPECTED_SKILLS:
                    with self.subTest(hosts=projection["hosts"], skill=skill_name):
                        source_root = REPO_ROOT / "skills" / skill_name
                        skill_root = root / skill_name
                        projected_skill = skill_root / "SKILL.md"
                        manifest_path = (
                            skill_root
                            / "references"
                            / "shared"
                            / "projection-manifest.json"
                        )
                        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                        self.assertEqual(INSTALLER.PROJECTION_SCHEMA, manifest["schema_version"])
                        self.assertEqual(skill_name, manifest["skill_name"])
                        self.assertEqual(projection["hosts"], manifest["hosts"])
                        self.assertEqual([], manifest["permission_changes"])
                        expected_omissions = [
                            relative
                            for relative in LEGACY_SOURCE_ONLY_PATHS
                            if relative.startswith(f"skills/{skill_name}/")
                        ]
                        self.assertEqual(
                            expected_omissions,
                            manifest["source_only_omissions"],
                        )
                        for relative in expected_omissions:
                            local = relative.removeprefix(f"skills/{skill_name}/")
                            self.assertFalse((skill_root / local).exists())
                        self.assertEqual(
                            _file_digest(source_root / "SKILL.md"),
                            manifest["source_skill_md_sha256"],
                        )
                        self.assertEqual(
                            _file_digest(projected_skill),
                            manifest["projected_skill_md_sha256"],
                        )
                        self.assertNotIn(
                            b"../engineering-research-copilot/references/",
                            projected_skill.read_bytes(),
                        )
                        for reference in manifest["references"]:
                            source_reference = REPO_ROOT / reference["source"]
                            projected_reference = skill_root / reference["projected"]
                            self.assertEqual(
                                _file_digest(source_reference), reference["source_sha256"]
                            )
                            self.assertEqual(
                                _file_digest(projected_reference),
                                reference["projected_sha256"],
                            )

                        if "hermes" in projection["hosts"]:
                            values, _ = INSTALLER._frontmatter(projected_skill)
                            expected = self.package.matrix["hosts"]["hermes"][
                                "description_overrides"
                            ][skill_name]
                            self.assertEqual(expected, values["description"])
                            self.assertLessEqual(len(values["description"]), 60)
                            self.assertEqual(1, len(manifest["frontmatter_changes"]))
                        else:
                            self.assertEqual([], manifest["frontmatter_changes"])

    def test_projection_is_deterministic_for_the_same_host(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            roots = []
            for name in ("first", "second"):
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(
                        0,
                        INSTALLER.main(
                            [
                                "--source",
                                str(REPO_ROOT),
                                "--agent",
                                "claude-code",
                                "--home-root",
                                str(base / name),
                            ]
                        ),
                    )
                roots.append(base / name / ".claude" / "skills")
            for skill_name in EXPECTED_SKILLS:
                self.assertEqual(
                    _tree_digest(roots[0] / skill_name),
                    _tree_digest(roots[1] / skill_name),
                )

    def test_preexisting_copy_blocks_every_projection_before_any_write(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            existing = (
                base
                / "home"
                / ".claude"
                / "skills"
                / "engineering-research-copilot"
            )
            existing.mkdir(parents=True)
            sentinel = existing / "sentinel.txt"
            sentinel.write_text("keep", encoding="utf-8")

            argv = [
                "--source",
                str(REPO_ROOT),
                "--agent",
                "codex",
                "--agent",
                "claude-code",
                "--home-root",
                str(base / "home"),
            ]
            with self.assertRaises(FileExistsError):
                INSTALLER.main(argv)
            self.assertEqual("keep", sentinel.read_text(encoding="utf-8"))
            self.assertFalse((base / "home" / ".agents").exists())

    def test_explicit_upgrade_replaces_old_cluster_without_source_mutation(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            common = [
                "--source",
                str(REPO_ROOT),
                "--agent",
                "claude-code",
                "--home-root",
                str(base / "home"),
            ]
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(0, INSTALLER.main(common))
            root = base / "home" / ".claude" / "skills"
            expected_digests = {
                skill_name: _tree_digest(root / skill_name)
                for skill_name in EXPECTED_SKILLS
            }
            stale = root / "research-direction-evidence" / "stale.txt"
            stale.write_text("old", encoding="utf-8")

            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(0, INSTALLER.main([*common, "--upgrade"]))
            self.assertFalse(stale.exists())
            for skill_name in EXPECTED_SKILLS:
                self.assertEqual(
                    expected_digests[skill_name],
                    _tree_digest(root / skill_name),
                )
            leftovers = [
                path.name
                for path in root.iterdir()
                if path.name.startswith(".engineering-research-workbench.")
            ]
            self.assertEqual([], leftovers)

    def test_staging_failure_leaves_no_partial_skill_or_hidden_stage(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            projection = INSTALLER.Projection(
                root=base / "target", hosts=("codex",)
            )
            original = INSTALLER._project_skill
            calls = 0

            def fail_second(package, skill_name, destination, hosts) -> None:
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("injected copy failure")
                original(package, skill_name, destination, hosts)

            with mock.patch.object(INSTALLER, "_project_skill", side_effect=fail_second):
                with self.assertRaisesRegex(OSError, "injected copy failure"):
                    INSTALLER.stage_projections(self.package, [projection])
            self.assertFalse((base / "target").exists())

    def test_activation_failure_restores_every_preexisting_projection(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            projections = [
                INSTALLER.Projection(base / "codex", ("codex",)),
                INSTALLER.Projection(base / "claude", ("claude-code",)),
            ]
            for projection in projections:
                old = projection.root / "engineering-research-copilot"
                old.mkdir(parents=True)
                (old / "sentinel.txt").write_text(
                    projection.hosts[0], encoding="utf-8"
                )

            states = INSTALLER.stage_projections(self.package, projections)
            first_skill = self.package.matrix["required_skills"][0]
            shutil.rmtree(states[1].stage_root / first_skill)
            with self.assertRaises(FileNotFoundError):
                INSTALLER.apply_staged(self.package, states)

            for projection in projections:
                self.assertEqual(
                    projection.hosts[0],
                    (
                        projection.root
                        / "engineering-research-copilot"
                        / "sentinel.txt"
                    ).read_text(encoding="utf-8"),
                )
                self.assertEqual(
                    {"engineering-research-copilot"},
                    {path.name for path in projection.root.iterdir()},
                )

    def test_safe_extract_rejects_parent_traversal(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            archive = base / "unsafe.zip"
            with zipfile.ZipFile(archive, "w") as bundle:
                bundle.writestr("../escaped.txt", "no")
            destination = base / "extract"
            destination.mkdir()
            with self.assertRaisesRegex(ValueError, "unsafe path"):
                INSTALLER.safe_extract(archive, destination)
            self.assertFalse((base / "escaped.txt").exists())

    def test_installed_focused_skills_keep_resolvable_shared_contracts(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            with contextlib.redirect_stdout(io.StringIO()):
                INSTALLER.main(
                    [
                        "--source",
                        str(REPO_ROOT),
                        "--agent",
                        "openclaw",
                        "--home-root",
                        str(base / "home"),
                    ]
                )
            root = base / "home" / ".openclaw" / "skills"
            for skill_name in EXPECTED_SKILLS - {"engineering-research-copilot"}:
                with self.subTest(skill=skill_name):
                    skill_root = root / skill_name
                    skill_text = (skill_root / "SKILL.md").read_text(encoding="utf-8")
                    self.assertIn("generated host projection", skill_text)
                    self.assertNotIn("../engineering-research-copilot/", skill_text)
                    manifest = json.loads(
                        (
                            skill_root
                            / "references"
                            / "shared"
                            / "projection-manifest.json"
                        ).read_text(encoding="utf-8")
                    )
                    self.assertGreaterEqual(len(manifest["references"]), 2)
                    for reference in manifest["references"]:
                        path = skill_root / reference["projected"]
                        self.assertTrue(path.is_file())
                        self.assertEqual(
                            reference["source_sha256"], _file_digest(path)
                        )


if __name__ == "__main__":
    unittest.main()
