import json
import unittest
from pathlib import Path
import benchmark

class BenchmarkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = benchmark.load_cases(benchmark.DEFAULT_CASES)

    def test_case_count_and_unique_ids(self):
        self.assertEqual(len(self.cases), 15)
        ids = [c['id'] for c in self.cases]
        self.assertEqual(len(ids), len(set(ids)))

    def test_each_fixture_expected_answer_passes(self):
        for case in self.cases:
            with self.subTest(case=case['id']):
                if case['type'] == 'json_object':
                    response = json.dumps(case['expected'])
                elif case['type'] == 'contains_all':
                    response = '\\n'.join(case['expected'])
                else:
                    response = str(case['expected'])
                passed, _ = benchmark.evaluate(case, response)
                self.assertTrue(passed)

    def test_exact_mismatch_fails(self):
        case = next(c for c in self.cases if c['id'] == 'accuracy-001')
        self.assertFalse(benchmark.evaluate(case, '43')[0])

    def test_invalid_json_fails(self):
        case = next(c for c in self.cases if c['id'] == 'json-001')
        self.assertFalse(benchmark.evaluate(case, '{bad json')[0])

    def test_missing_code_fragment_fails(self):
        case = next(c for c in self.cases if c['id'] == 'coding-001')
        self.assertFalse(benchmark.evaluate(case, 'def is_even(n):\\n    return True')[0])

if __name__ == '__main__':
    unittest.main(verbosity=2)
