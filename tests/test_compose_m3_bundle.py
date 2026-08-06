from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
COMPOSER = (
    REPO_ROOT
    / "skills"
    / "engineering-research-copilot"
    / "scripts"
    / "compose_m3_bundle.py"
)
sys.path.insert(0, str(REPO_ROOT / "tests"))

from test_validate_m3_method_bundle import make_valid_m3_bundle  # noqa: E402


EXPECTED_FIELDS = {
    "schema_version",
    "source_m2_bundle",
    "source_m2_bundle_hash",
    "selected_direction_id",
    "selected_direction_hash",
    "coaching_mode",
    "method_cards",
    "domain_overlays",
}


def canonical_sha256(value: object) -> str:
    raw = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


class ComposeM3BundleTests(unittest.TestCase):
    def _write_json(self, path: Path, payload: object) -> None:
        path.write_text(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
            newline="\n",
        )

    def _inputs(self, root: Path) -> tuple[Path, Path, Path, dict, dict]:
        complete = make_valid_m3_bundle()
        m2 = complete["source_m2_bundle"]
        payload = {
            "coaching_mode": complete["coaching_mode"],
            "method_cards": complete["method_cards"],
            "domain_overlays": complete["domain_overlays"],
        }
        m2_path = root / "immutable-m2.json"
        payload_path = root / "model-payload.json"
        output_path = root / "m3-output.json"
        self._write_json(m2_path, m2)
        self._write_json(payload_path, payload)
        return m2_path, payload_path, output_path, m2, payload

    def _run(
        self,
        m2_path: Path,
        payload_path: Path,
        output_path: Path,
        *extra: str,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                "-X",
                "utf8",
                str(COMPOSER),
                str(m2_path),
                str(payload_path),
                str(output_path),
                *extra,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def test_composes_exact_eight_field_bundle_without_mutating_inputs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            m2_path, payload_path, output_path, m2, payload = self._inputs(root)
            m2_before = m2_path.read_bytes()
            payload_before = payload_path.read_bytes()

            completed = self._run(m2_path, payload_path, output_path)

            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            self.assertEqual(completed.stderr, "")
            output = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(set(output), EXPECTED_FIELDS)
            self.assertEqual(output["schema_version"], "m3.1")
            self.assertEqual(output["source_m2_bundle"], m2)
            self.assertIsNot(output["source_m2_bundle"], m2)
            self.assertEqual(output["coaching_mode"], payload["coaching_mode"])
            self.assertEqual(output["method_cards"], payload["method_cards"])
            self.assertEqual(output["domain_overlays"], payload["domain_overlays"])
            self.assertEqual(m2_path.read_bytes(), m2_before)
            self.assertEqual(payload_path.read_bytes(), payload_before)

    def test_recomputes_source_and_selected_direction_hashes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            m2_path, payload_path, output_path, m2, _ = self._inputs(root)

            completed = self._run(m2_path, payload_path, output_path)

            self.assertEqual(completed.returncode, 0, completed.stdout)
            output = json.loads(output_path.read_text(encoding="utf-8"))
            selected_id = m2["direction_decision"]["selected_direction_id"]
            selected = next(
                direction
                for direction in m2["direction_portfolio"]["directions"]
                if direction["direction_id"] == selected_id
            )
            self.assertEqual(output["source_m2_bundle_hash"], canonical_sha256(m2))
            self.assertEqual(output["selected_direction_id"], selected_id)
            self.assertEqual(output["selected_direction_hash"], canonical_sha256(selected))

    def test_receipt_records_raw_and_canonical_input_hashes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            m2_path, payload_path, output_path, m2, payload = self._inputs(root)

            completed = self._run(m2_path, payload_path, output_path)

            self.assertEqual(completed.returncode, 0, completed.stdout)
            self.assertEqual(completed.stdout.count("\n"), 1)
            receipt = json.loads(completed.stdout)
            self.assertEqual(receipt["status"], "composed")
            self.assertEqual(
                receipt["m2_raw_sha256"], hashlib.sha256(m2_path.read_bytes()).hexdigest()
            )
            self.assertEqual(receipt["m2_canonical_sha256"], canonical_sha256(m2))
            self.assertEqual(
                receipt["payload_raw_sha256"],
                hashlib.sha256(payload_path.read_bytes()).hexdigest(),
            )
            self.assertEqual(receipt["payload_canonical_sha256"], canonical_sha256(payload))
            self.assertEqual(
                receipt["output_raw_sha256"],
                hashlib.sha256(output_path.read_bytes()).hexdigest(),
            )

    def test_preserves_array_order_and_writes_utf8_without_bom(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            m2_path, payload_path, output_path, m2, payload = self._inputs(root)
            original_ids = [
                direction["direction_id"]
                for direction in m2["direction_portfolio"]["directions"]
            ]
            original_card_ids = [card["card_id"] for card in payload["method_cards"]]

            completed = self._run(m2_path, payload_path, output_path)

            self.assertEqual(completed.returncode, 0, completed.stdout)
            raw = output_path.read_bytes()
            self.assertFalse(raw.startswith(b"\xef\xbb\xbf"))
            self.assertEqual(raw.count(b"\n"), 1)
            output = json.loads(raw.decode("utf-8"))
            self.assertEqual(
                [
                    direction["direction_id"]
                    for direction in output["source_m2_bundle"]["direction_portfolio"][
                        "directions"
                    ]
                ],
                original_ids,
            )
            self.assertEqual(
                [card["card_id"] for card in output["method_cards"]],
                original_card_ids,
            )

    def test_rejects_unknown_payload_fields_without_writing_output(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            m2_path, payload_path, output_path, _, payload = self._inputs(root)
            payload["route_output"] = {"invented": True}
            self._write_json(payload_path, payload)

            completed = self._run(m2_path, payload_path, output_path)

            self.assertNotEqual(completed.returncode, 0)
            self.assertFalse(output_path.exists())
            self.assertEqual(json.loads(completed.stdout)["error"], "unknown_payload_fields")

    def test_does_not_fill_missing_method_card_fields(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            m2_path, payload_path, output_path, _, payload = self._inputs(root)
            payload["method_cards"][0].pop("failure_modes")
            payload_before = copy.deepcopy(payload)
            self._write_json(payload_path, payload)

            completed = self._run(m2_path, payload_path, output_path)

            self.assertNotEqual(completed.returncode, 0)
            self.assertFalse(output_path.exists())
            self.assertEqual(json.loads(payload_path.read_text(encoding="utf-8")), payload_before)
            receipt = json.loads(completed.stdout)
            self.assertEqual(receipt["error"], "payload_contract_invalid")
            self.assertEqual(receipt["contract_errors"][0]["path"], "method_cards[0]")

    def test_reports_metric_object_as_field_level_contract_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            m2_path, payload_path, output_path, _, payload = self._inputs(root)
            payload["method_cards"][0]["primary_metrics"] = [
                {"metric_id": "M1", "metric": "description", "unit": "fraction"}
            ]
            self._write_json(payload_path, payload)

            completed = self._run(m2_path, payload_path, output_path)

            self.assertNotEqual(completed.returncode, 0)
            self.assertFalse(output_path.exists())
            receipt = json.loads(completed.stdout)
            self.assertEqual(receipt["error"], "payload_contract_invalid")
            self.assertEqual(
                receipt["contract_errors"],
                [
                    {
                        "code": "primary_metrics_item_type",
                        "path": "method_cards[0].primary_metrics[0]",
                        "expected": "string metric_id",
                    }
                ],
            )

    def test_reports_route_incompatible_and_empty_cards_without_malformed_bundle(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            m2_path, payload_path, output_path, _, _ = self._inputs(root)
            self._write_json(
                payload_path,
                {
                    "coaching_mode": "route_incompatible",
                    "method_cards": [],
                    "domain_overlays": [],
                },
            )

            completed = self._run(m2_path, payload_path, output_path)

            self.assertNotEqual(completed.returncode, 0)
            self.assertFalse(output_path.exists())
            receipt = json.loads(completed.stdout)
            self.assertEqual(receipt["error"], "payload_contract_invalid")
            self.assertEqual(
                receipt["contract_errors"],
                [
                    {
                        "code": "coaching_mode_enum",
                        "path": "coaching_mode",
                        "expected": ["bounded", "route_specific"],
                    },
                    {
                        "code": "method_cards_min_items",
                        "path": "method_cards",
                        "expected": "at least one closed method card",
                    },
                ],
            )

    def test_rejects_invalid_m2_without_writing_output(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            m2_path, payload_path, output_path, _, _ = self._inputs(root)
            self._write_json(m2_path, {})

            completed = self._run(m2_path, payload_path, output_path)

            self.assertNotEqual(completed.returncode, 0)
            self.assertFalse(output_path.exists())
            self.assertEqual(json.loads(completed.stdout)["error"], "invalid_source_m2_bundle")

    def test_rejects_bom_and_non_object_inputs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            m2_path, payload_path, output_path, _, _ = self._inputs(root)
            payload_path.write_bytes(b"\xef\xbb\xbf{}")

            completed = self._run(m2_path, payload_path, output_path)

            self.assertNotEqual(completed.returncode, 0)
            self.assertFalse(output_path.exists())
            self.assertEqual(json.loads(completed.stdout)["error"], "payload_utf8_bom_forbidden")

            payload_path.write_text("[]\n", encoding="utf-8")
            completed = self._run(m2_path, payload_path, output_path)
            self.assertNotEqual(completed.returncode, 0)
            self.assertEqual(json.loads(completed.stdout)["error"], "payload_must_be_object")

    def test_refuses_to_overwrite_and_rejects_wrong_argument_count(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            m2_path, payload_path, output_path, _, _ = self._inputs(root)
            output_path.write_text("sentinel\n", encoding="utf-8")

            completed = self._run(m2_path, payload_path, output_path)

            self.assertNotEqual(completed.returncode, 0)
            self.assertEqual(output_path.read_text(encoding="utf-8"), "sentinel\n")
            self.assertEqual(json.loads(completed.stdout)["error"], "output_already_exists")

            completed = self._run(m2_path, payload_path, output_path, "extra")
            self.assertNotEqual(completed.returncode, 0)
            self.assertEqual(json.loads(completed.stdout)["error"], "expected_three_paths")


if __name__ == "__main__":
    unittest.main()
