from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "evals" / "m3"))

from audit_immutable_forward_evidence import (  # noqa: E402
    audit_repository,
    compare_file_bytes,
)


class AuditImmutableForwardEvidenceTests(unittest.TestCase):
    def test_untouched_r2_r3_git_blobs_are_preserved_in_a_fresh_lf_checkout(self):
        result = audit_repository(REPO_ROOT)
        self.assertEqual(result["status"], "valid")
        self.assertGreater(len(result["files"]), 0)
        self.assertTrue(
            all(
                item.get("git_blob_object_id")
                and item.get("git_blob_raw_sha256")
                for item in result["files"]
            )
        )
        self.assertTrue(all(item["bytes_equal"] for item in result["files"]))
        self.assertEqual(result["errors"], [])

    def test_one_byte_mutation_is_detected_without_touching_repository(self):
        source = REPO_ROOT / "evals" / "m3" / "forward-inputs-r2" / "m3-f03-approved-change.bundle.json"
        original = source.read_bytes()
        with tempfile.TemporaryDirectory(dir=REPO_ROOT) as temp_dir:
            mutated = Path(temp_dir) / "mutated.bin"
            mutated.write_bytes(original + b"x")
            comparison = compare_file_bytes(mutated, original, "temporary-copy")
        self.assertFalse(comparison["bytes_equal"])
        self.assertNotEqual(comparison["filesystem_raw_sha256"], comparison["baseline_raw_sha256"])


if __name__ == "__main__":
    unittest.main()
