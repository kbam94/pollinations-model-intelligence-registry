import json
import tempfile
import unittest
from pathlib import Path

import catalog


class CatalogDiffTests(unittest.TestCase):
    def test_detects_added_removed_changed_and_unchanged_models(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "catalog.sqlite3"
            source = Path(tmp) / "snapshots.jsonl"
            rows = [
                {"model_id": "provider/changed", "snapshot_at": "2026-11-10", "paid_only": False,
                 "input_price": "0", "output_price": "0", "context_window": 8192,
                 "supports_tools": False, "provider": "provider", "source": "fixture"},
                {"model_id": "provider/removed", "snapshot_at": "2026-11-10", "paid_only": False},
                {"model_id": "provider/steady", "snapshot_at": "2026-11-10", "paid_only": False},
                {"model_id": "provider/changed", "snapshot_at": "2026-11-11", "paid_only": True,
                 "input_price": "0.1", "output_price": "0.2", "context_window": 16384,
                 "supports_tools": True, "provider": "provider", "source": "fixture"},
                {"model_id": "provider/steady", "snapshot_at": "2026-11-11", "paid_only": False},
                {"model_id": "provider/added", "snapshot_at": "2026-11-11", "paid_only": False}
            ]
            source.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
            catalog.import_jsonl(source, db)
            report = catalog.compare_snapshots(db)
            self.assertEqual(report["from_snapshot"], "2026-11-10")
            self.assertEqual(report["to_snapshot"], "2026-11-11")
            self.assertEqual([r["model_id"] for r in report["added"]], ["provider/added"])
            self.assertEqual([r["model_id"] for r in report["removed"]], ["provider/removed"])
            self.assertEqual([r["model_id"] for r in report["changed"]], ["provider/changed"])
            self.assertEqual(report["unchanged"], ["provider/steady"])
            self.assertEqual(set(report["changed"][0]["fields"]), {
                "paid_only", "input_price", "output_price", "context_window", "supports_tools"
            })

    def test_requires_two_snapshots_for_automatic_comparison(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "catalog.sqlite3"
            source = Path(tmp) / "one.jsonl"
            source.write_text(json.dumps({
                "model_id": "provider/model", "snapshot_at": "2026-11-11"
            }) + "\n", encoding="utf-8")
            catalog.import_jsonl(source, db)
            report = catalog.compare_snapshots(db)
            self.assertIn("two distinct", report["error"])

    def test_missing_database_is_not_created_by_diff(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "missing.sqlite3"
            report = catalog.compare_snapshots(db)
            self.assertIn("does not exist", report["error"])
            self.assertFalse(db.exists())

    def test_explicit_snapshot_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "catalog.sqlite3"
            source = Path(tmp) / "snapshots.jsonl"
            rows = [
                {"model_id": "provider/model", "snapshot_at": "2026-11-09", "context_window": 4096},
                {"model_id": "provider/model", "snapshot_at": "2026-11-10", "context_window": 8192},
                {"model_id": "provider/model", "snapshot_at": "2026-11-11", "context_window": 16384}
            ]
            source.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
            catalog.import_jsonl(source, db)
            report = catalog.compare_snapshots(db, "2026-11-09", "2026-11-10")
            self.assertEqual(report["changed"][0]["fields"]["context_window"],
                             {"before": 4096, "after": 8192})


if __name__ == "__main__":
    unittest.main()
