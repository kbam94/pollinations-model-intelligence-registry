import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

import catalog


class CatalogTests(unittest.TestCase):
    def write_jsonl(self, path, rows):
        path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")

    def sample(self, model="provider/model-a", date="2026-11-11T10:00:00", **extra):
        row = {"model_id": model, "snapshot_at": date, "paid_only": False,
               "input_price": "0", "output_price": "0", "context_window": 8192,
               "supports_tools": True, "provider": "provider-x",
               "source": "local test fixture", "notes": None}
        row.update(extra)
        return row

    def test_import_is_idempotent_and_latest_snapshot_selected(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "catalog.jsonl"
            db = Path(tmp) / "catalog.sqlite3"
            self.write_jsonl(source, [
                self.sample(date="2026-11-10T10:00:00"),
                self.sample(date="2026-11-11T10:00:00", context_window=16384)
            ])
            first = catalog.import_jsonl(source, db)
            second = catalog.import_jsonl(source, db)
            self.assertEqual(first["inserted_records"], 2)
            self.assertEqual(second["inserted_records"], 0)
            latest = catalog.list_snapshots(db, latest=True)
            self.assertEqual(len(latest), 1)
            self.assertEqual(latest[0]["context_window"], 16384)

    def test_catalog_does_not_infer_quest_eligibility(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "catalog.jsonl"
            db = Path(tmp) / "catalog.sqlite3"
            self.write_jsonl(source, [self.sample()])
            catalog.import_jsonl(source, db)
            rendered = catalog.render(catalog.list_snapshots(db))
            self.assertIn("NOT ESTABLISHED BY CATALOG METADATA", rendered)
            self.assertIn("CATALOG DOES NOT MARK PAID-ONLY", rendered)

    def test_paid_only_true_is_reported_as_catalog_metadata_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "catalog.jsonl"
            db = Path(tmp) / "catalog.sqlite3"
            self.write_jsonl(source, [self.sample(paid_only=True)])
            catalog.import_jsonl(source, db)
            row = catalog.list_snapshots(db)[0]
            self.assertEqual(catalog.catalog_label(row), "CATALOG MARKED PAID-ONLY")

    def test_rejects_unknown_quest_eligibility_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "catalog.jsonl"
            self.write_jsonl(source, [self.sample(quest_eligible=True)])
            with self.assertRaisesRegex(ValueError, "unsupported fields"):
                catalog.import_jsonl(source, Path(tmp) / "catalog.sqlite3")

    def test_rejects_non_boolean_paid_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "catalog.jsonl"
            self.write_jsonl(source, [self.sample(paid_only="false")])
            with self.assertRaisesRegex(ValueError, "paid_only must be true"):
                catalog.import_jsonl(source, Path(tmp) / "catalog.sqlite3")

    def test_listing_missing_database_does_not_create_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "not-created.sqlite3"
            self.assertEqual(catalog.list_snapshots(db), [])
            self.assertFalse(db.exists())


if __name__ == "__main__":
    unittest.main()
