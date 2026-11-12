import builtins
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import menu


class MenuTests(unittest.TestCase):
    def test_choose_number_accepts_valid_selection(self):
        with patch("builtins.input", side_effect=["abc", "9", "2"]):
            self.assertEqual(menu.choose_number("Pick", 3), 2)

    def test_choose_number_zero_returns_back(self):
        with patch("builtins.input", return_value="0"):
            self.assertIsNone(menu.choose_number("Pick", 3))

    def test_choose_file_path_refuses_existing_file_without_yes(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "existing.jsonl"
            target.write_text("keep", encoding="utf-8")
            with patch("builtins.input", side_effect=["", "no"]):
                self.assertIsNone(menu.choose_file_path("Output", target))
            self.assertEqual(target.read_text(encoding="utf-8"), "keep")

    def test_model_selection_source_is_live_runner_allowlist(self):
        import live_runner
        self.assertEqual(len(live_runner.ALLOWED_MODELS), 6)
        self.assertIn("openai/gpt-5-nano", live_runner.ALLOWED_MODELS)


if __name__ == "__main__":
    unittest.main()
