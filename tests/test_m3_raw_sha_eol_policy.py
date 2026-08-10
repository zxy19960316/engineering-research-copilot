from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = REPO_ROOT / "evals/m3/forward-inputs-r5.1-f02/manifest.json"
DIAGNOSTICS_RELATIVE = "evals/m3/results/diagnostics-r5.1"


class M3RawShaEolPolicyTests(unittest.TestCase):
    def _attributes(self, relative: str) -> dict[str, str]:
        raw = subprocess.run(
            ["git", "check-attr", "-z", "text", "eol", "--", relative],
            cwd=REPO_ROOT,
            capture_output=True,
            check=True,
        ).stdout
        fields = raw.decode("utf-8").rstrip("\0").split("\0")
        return {
            fields[index + 1]: fields[index + 2]
            for index in range(0, len(fields), 3)
        }

    def _assert_lf_blob_match(self, relative: str) -> None:
        self.assertEqual(
            self._attributes(relative), {"text": "set", "eol": "lf"}
        )
        worktree = (REPO_ROOT / relative).read_bytes()
        blob = subprocess.run(
            ["git", "show", f"HEAD:{relative}"],
            cwd=REPO_ROOT,
            capture_output=True,
            check=True,
        ).stdout
        self.assertEqual(worktree, blob)

    def _bindings(self) -> list[dict[str, str]]:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        bindings = [
            manifest[key]
            for key in ("input_binding", "prompt", "contract", "supersession_policy")
        ]
        input_binding = json.loads(
            (REPO_ROOT / manifest["input_binding"]["path"]).read_text(
                encoding="utf-8"
            )
        )
        bindings.extend(
            input_binding[key]
            for key in ("source_input", "m2_validation", "eligibility")
        )
        return bindings

    def test_all_r5_1_preparation_worktree_raw_sha_bindings_use_lf(self) -> None:
        bindings = self._bindings()
        paths = [binding["path"] for binding in bindings]
        self.assertEqual(len(paths), 7)
        self.assertEqual(len(set(paths)), 7)
        for relative in paths:
            with self.subTest(path=relative):
                self._assert_lf_blob_match(relative)

    def test_raw_locked_diagnostics_root_materializes_from_exact_blobs(self) -> None:
        raw = subprocess.run(
            ["git", "ls-files", "-z", "--", DIAGNOSTICS_RELATIVE],
            cwd=REPO_ROOT,
            capture_output=True,
            check=True,
        ).stdout
        paths = raw.decode("utf-8").rstrip("\0").split("\0")
        self.assertGreaterEqual(len(paths), 2)
        for relative in paths:
            with self.subTest(path=relative):
                self._assert_lf_blob_match(relative)


if __name__ == "__main__":
    unittest.main()
