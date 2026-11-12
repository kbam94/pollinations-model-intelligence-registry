import json
import tempfile
import unittest
from pathlib import Path
import live_runner
import registry

class LiveRunnerSafetyTests(unittest.TestCase):
    def test_allowlist_contains_only_expected_quest_tested_models(self):
        self.assertIn("openai/gpt-5-nano", live_runner.ALLOWED_MODELS)
        self.assertNotIn("community/kbam666/gemma-agent-test", live_runner.ALLOWED_MODELS)

    def test_preview_is_explicitly_non_live(self):
        case = live_runner.get_case("accuracy-001")
        self.assertEqual(case["id"], "accuracy-001")
        self.assertEqual(live_runner.MAX_TOKENS, 128)

    def test_record_saves_metadata_without_response_body(self):
        record = {
            "test_id": "unit-live-record",
            "tested_at": "2026-11-11T00:00:00+00:00",
            "requested_model": "openai/gpt-5-nano",
            "actual_model": "gpt-5-nano",
            "provider": "Pollinations",
            "endpoint": "/v1/chat/completions",
            "key_policy": "quest_only",
            "http_status": 200,
            "outcome": "pass",
            "prompt_tokens": 10,
            "completion_tokens": 2,
            "total_tokens": 12,
            "latency_ms": 123.4,
            "error_code": None,
            "notes": "benchmark:exact_match",
        }
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "tests.sqlite3"
            result = live_runner.save_record(record, db)
            self.assertEqual(result["inserted_records"], 1)
            rows = registry.list_tests(db)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["key_policy"], "quest_only")
            self.assertNotIn("response", rows[0])
            self.assertNotIn("prompt", rows[0])

    def test_duplicate_record_is_ignored(self):
        record = {
            "test_id": "unit-live-duplicate",
            "tested_at": "2026-11-11T00:00:00+00:00",
            "requested_model": "openai/gpt-5-nano",
            "endpoint": "/v1/chat/completions",
            "key_policy": "quest_only",
            "outcome": "pass",
        }
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "tests.sqlite3"
            first = live_runner.save_record(record, db)
            second = live_runner.save_record(record, db)
            self.assertEqual(first["inserted_records"], 1)
            self.assertEqual(second["inserted_records"], 0)

if __name__ == "__main__":
    unittest.main(verbosity=2)
