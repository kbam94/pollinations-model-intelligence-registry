import sqlite3
import tempfile
import unittest
from pathlib import Path

import compare


class CompareTests(unittest.TestCase):
    def row(self, outcome, error_code=None, latency=None, tokens=None):
        return {
            "requested_model": "provider/model-a",
            "actual_model": "provider/model-a-routed",
            "provider": "provider",
            "key_policy": "quest_only",
            "outcome": outcome,
            "prompt_tokens": None,
            "completion_tokens": None,
            "total_tokens": tokens,
            "latency_ms": latency,
            "error_code": error_code,
        }

    def test_aggregate_scored_rate_and_missing_metrics(self):
        rows = [
            self.row("pass", latency=100, tokens=20),
            self.row("quality_fail", latency=200, tokens=None),
            self.row("inconclusive"),
        ]
        item = compare.aggregate_history(rows)[0]
        self.assertEqual(item["attempts"], 3)
        self.assertEqual(item["evaluated"], 2)
        self.assertEqual(item["pass_rate"], 50.0)
        self.assertAlmostEqual(item["attempt_pass_rate"], 33.3, places=1)
        self.assertEqual(item["avg_latency_ms"], 150.0)
        self.assertEqual(item["avg_total_tokens"], 20)
        self.assertEqual(item["eligibility"], "QUEST TEST PASS RECORDED")
        self.assertEqual(item["evidence"], "VERY LIMITED")

    def test_paid_pollen_block_is_not_quest_eligible(self):
        row = self.row("error", error_code="paid_pollen_required")
        item = compare.aggregate_history([row])[0]
        self.assertEqual(item["eligibility"], "PAID POLLEN REQUIRED")
        self.assertIsNone(item["pass_rate"])
        self.assertEqual(item["paid_blocked"], 1)

    def test_read_history_uses_read_only_database(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "history.sqlite3"
            conn = sqlite3.connect(db)
            conn.execute("""CREATE TABLE model_tests (
                requested_model TEXT, actual_model TEXT, provider TEXT,
                key_policy TEXT, outcome TEXT, prompt_tokens INTEGER,
                completion_tokens INTEGER, total_tokens INTEGER,
                latency_ms REAL, error_code TEXT, tested_at TEXT
            )""")
            conn.execute(
                "INSERT INTO model_tests VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                ("m", "m-routed", "p", "quest_only", "pass", 1, 2, 3, 4.0, None, "2026-01-01")
            )
            conn.commit()
            conn.close()
            rows = compare.read_history(db)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["requested_model"], "m")

    def test_render_warns_about_small_samples_and_missing_data(self):
        item = compare.aggregate_history([self.row("pass")])[0]
        rendered = compare.render_history([item])
        self.assertIn("VERY LIMITED", rendered)
        self.assertIn("not recorded", rendered)
        self.assertIn("not a definitive leaderboard", rendered.lower())

    def test_benchmark_report_schema_matches_scorer(self):
        report = {
            "mode": "offline_scoring_no_api_calls",
            "response_records": 2,
            "summaries": [{
                "model": "m", "passed": 1, "tested": 2,
                "accuracy_percent": 50.0, "manual_reviews": 0,
                "categories": {"accuracy": {"passed": 1, "total": 2}}
            }],
            "results": []
        }
        rendered = compare.render_benchmark(report)
        self.assertIn("1/2 passed (50.0%)", rendered)
        self.assertIn("Accuracy", rendered)


if __name__ == "__main__":
    unittest.main()
