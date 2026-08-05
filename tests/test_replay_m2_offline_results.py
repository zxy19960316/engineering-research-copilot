from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
M2_EVAL_DIR = REPO_ROOT / "evals" / "m2"
_REPLAY_SPEC = importlib.util.spec_from_file_location(
    "m2_replay_offline_results",
    M2_EVAL_DIR / "replay_offline_results.py",
)
if _REPLAY_SPEC is None or _REPLAY_SPEC.loader is None:
    raise RuntimeError("Unable to load the M2 replay module")
_REPLAY_MODULE = importlib.util.module_from_spec(_REPLAY_SPEC)
_REPLAY_SPEC.loader.exec_module(_REPLAY_MODULE)
evaluate = _REPLAY_MODULE.evaluate


class M2OfflineResultsReplayTests(unittest.TestCase):
    def test_replay_matches_every_declared_fixture_and_frozen_record(self):
        manifest = M2_EVAL_DIR / "adversarial-cases.json"
        actual = evaluate(manifest)
        frozen = json.loads(
            (M2_EVAL_DIR / "offline-results.json").read_text(encoding="utf-8")
        )
        self.assertTrue(actual["all_matched"])
        self.assertEqual(actual, frozen)

    def test_replay_exposes_expected_status_mismatch(self):
        manifest = json.loads(
            (M2_EVAL_DIR / "adversarial-cases.json").read_text(encoding="utf-8")
        )
        changed = copy.deepcopy(manifest)
        changed["cases"][0]["expected_status"] = "invalid"
        with tempfile.TemporaryDirectory(dir=M2_EVAL_DIR) as directory:
            temp_root = Path(directory)
            temp_manifest = temp_root / "adversarial-cases.json"
            temp_fixture_dir = temp_root / "fixtures"
            temp_fixture_dir.mkdir()
            temp_manifest.write_text(json.dumps(changed), encoding="utf-8")
            for case in changed["cases"]:
                source = M2_EVAL_DIR / "fixtures" / case["fixture"]
                (temp_fixture_dir / case["fixture"]).write_bytes(source.read_bytes())
            result = evaluate(temp_manifest)
        self.assertFalse(result["all_matched"])
        self.assertFalse(result["cases"][0]["matched"])

    def test_fixture_builder_is_byte_deterministic(self):
        manifest = M2_EVAL_DIR / "adversarial-cases.json"
        fixture_dir = M2_EVAL_DIR / "fixtures"
        paths = [manifest, *sorted(fixture_dir.glob("*.json"))]
        before = {path.name: path.read_bytes() for path in paths}
        completed = subprocess.run(
            [sys.executable, "-X", "utf8", str(M2_EVAL_DIR / "build_fixtures.py")],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        after_paths = [manifest, *sorted(fixture_dir.glob("*.json"))]
        after = {path.name: path.read_bytes() for path in after_paths}
        self.assertEqual(after, before)
        self.assertEqual(len(after) - 1, 34)


if __name__ == "__main__":
    unittest.main()
