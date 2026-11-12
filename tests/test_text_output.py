import tempfile
import unittest
from pathlib import Path
import benchmark
import live_runner
import registry

class PlainTextOutputTests(unittest.TestCase):
    def test_registry_summary_is_human_readable(self):
        sample=[{"requested_model":"demo/model","actual_model":"demo-v1","attempts":2,
                 "passes":1,"quality_fails":1,"errors":0,"inconclusive":0,"last_test":"today"}]
        rendered=registry.render_summary(sample)
        self.assertIn("POLLINATIONS MODEL REGISTRY",rendered)
        self.assertIn("demo/model",rendered)
        self.assertIn("Passed",rendered)

    def test_registry_history_is_human_readable(self):
        sample=[{"requested_model":"demo/model","outcome":"pass","tested_at":"today",
                 "actual_model":"demo-v1","provider":"Pollinations","http_status":200,
                 "key_policy":"quest_only","prompt_tokens":4,"completion_tokens":2,
                 "total_tokens":6,"latency_ms":12.5,"error_code":None,"notes":"ok"}]
        rendered=registry.render_tests(sample)
        self.assertIn("[PASS]",rendered)
        self.assertIn("Token usage",rendered)

    def test_benchmark_case_list_is_readable(self):
        cases=benchmark.load_cases(benchmark.DEFAULT_CASES)
        rendered=benchmark.render_cases(cases)
        self.assertIn("BENCHMARK CASES",rendered)
        self.assertIn("accuracy-001",rendered)

    def test_live_preview_is_readable(self):
        case=live_runner.get_case("accuracy-001")
        rendered=live_runner.render_preview("openai/gpt-5-nano",case)
        self.assertIn("PREVIEW ONLY",rendered)
        self.assertIn("What is 19 + 23?",rendered)

if __name__=="__main__":
    unittest.main(verbosity=2)
