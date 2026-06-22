"""Unit tests for hekmo.cli using unittest and mocks.

These tests avoid real network/LLM calls and real terminal input by mocking
click.prompt and the shared Rich console.
"""

import unittest
from unittest.mock import patch, MagicMock

from hekmo import cli


class TestAsk(unittest.TestCase):
    """Tests for the ask() text-prompt helper."""

    @patch("hekmo.cli.click.prompt")
    def test_retries_when_required_and_empty(self, mock_prompt):
        """ask() should keep prompting if input is empty and the field is required."""
        mock_prompt.side_effect = ["", "", "pandas-dev"]
        result = cli.ask("Label")
        self.assertEqual(result, "pandas-dev")
        self.assertEqual(mock_prompt.call_count, 3)

    @patch("hekmo.cli.click.prompt")
    def test_returns_empty_string_when_not_required(self, mock_prompt):
        """ask() should allow empty input when required=False."""
        mock_prompt.return_value = ""
        result = cli.ask("Label", required=False)
        self.assertEqual(result, "")


class TestAskInt(unittest.TestCase):
    """Tests for the ask_int() integer-prompt helper."""

    @patch("hekmo.cli.click.prompt")
    def test_returns_int_on_valid_input(self, mock_prompt):
        """ask_int() should return the integer when given valid digits."""
        mock_prompt.return_value = "929"
        result = cli.ask_int("Issue Number")
        self.assertEqual(result, 929)

    @patch("hekmo.cli.click.prompt")
    def test_retries_on_invalid_then_succeeds(self, mock_prompt):
        """ask_int() should keep prompting until valid digits are entered."""
        mock_prompt.side_effect = ["abc", "-1", "42"]
        result = cli.ask_int("Issue Number")
        self.assertEqual(result, 42)
        self.assertEqual(mock_prompt.call_count, 3)


class TestAskTemplate(unittest.TestCase):
    """Tests for the ask_template() template-selection helper."""

    @patch("hekmo.cli.load_templates")
    @patch("hekmo.cli.click.prompt")
    def test_returns_selected_template_key(self, mock_prompt, mock_load_templates):
        """ask_template() should return the key of the chosen template."""
        mock_load_templates.return_value = {
            "default": {"sections": ["Status"]},
            "madr": {"sections": ["Status"]},
            "nygard": {"sections": ["Status"]},
        }
        mock_prompt.return_value = "2"
        result = cli.ask_template()
        self.assertEqual(result, "madr")

    @patch("hekmo.cli.load_templates")
    @patch("hekmo.cli.click.prompt")
    def test_retries_on_out_of_range_index(self, mock_prompt, mock_load_templates):
        """ask_template() should retry if the number is out of range."""
        mock_load_templates.return_value = {
            "default": {"sections": ["Status"]},
            "madr": {"sections": ["Status"]},
        }
        mock_prompt.side_effect = ["99", "1"]
        result = cli.ask_template()
        self.assertEqual(result, "default")
        self.assertEqual(mock_prompt.call_count, 2)

    @patch("hekmo.cli.load_templates")
    @patch("hekmo.cli.click.prompt")
    def test_retries_on_non_numeric_input(self, mock_prompt, mock_load_templates):
        """ask_template() should retry if input isn't numeric at all."""
        mock_load_templates.return_value = {
            "default": {"sections": ["Status"]},
        }
        mock_prompt.side_effect = ["abc", "1"]
        result = cli.ask_template()
        self.assertEqual(result, "default")
        self.assertEqual(mock_prompt.call_count, 2)


class TestMessageHelpers(unittest.TestCase):
    """Tests for step(), ok(), and fail() console-print helpers."""

    @patch("hekmo.cli.console")
    def test_step_prints_message(self, mock_console):
        """step() should print the message via console.print."""
        cli.step("Generating ADR")
        mock_console.print.assert_called_once()
        printed = mock_console.print.call_args[0][0]
        self.assertIn("Generating ADR", printed)

    @patch("hekmo.cli.console")
    def test_ok_prints_message(self, mock_console):
        """ok() should print the message via console.print."""
        cli.ok("ADR ready")
        mock_console.print.assert_called_once()
        printed = mock_console.print.call_args[0][0]
        self.assertIn("ADR ready", printed)

    @patch("hekmo.cli.console")
    def test_fail_prints_message(self, mock_console):
        """fail() should print the message via console.print."""
        cli.fail("Something broke")
        mock_console.print.assert_called_once()
        printed = mock_console.print.call_args[0][0]
        self.assertIn("Something broke", printed)


class TestSpinner(unittest.TestCase):
    """Tests for the spinner() progress-wrapper helper."""

    def test_spinner_returns_function_result(self):
        """spinner() should return whatever the wrapped function returns."""

        def dummy_fn(x, y):
            return x + y

        result = cli.spinner("loading...", dummy_fn, 2, 3)
        self.assertEqual(result, 5)

    def test_spinner_calls_function_with_args_and_kwargs(self):
        """spinner() should pass through positional and keyword arguments."""
        mock_fn = MagicMock(return_value="done")
        result = cli.spinner("loading...", mock_fn, "owner", "repo", issue_no=929)
        mock_fn.assert_called_once_with("owner", "repo", issue_no=929)
        self.assertEqual(result, "done")

    def test_spinner_propagates_exception(self):
        """If the wrapped function raises, spinner() should not swallow it."""

        def failing_fn():
            raise ValueError("boom")

        with self.assertRaises(ValueError):
            cli.spinner("loading...", failing_fn)


class TestPrintBanner(unittest.TestCase):
    """Tests for print_banner()."""

    @patch("hekmo.cli.console")
    def test_print_banner_calls_console_print(self, mock_console):
        """print_banner() should print multiple times without raising."""
        cli.print_banner()
        self.assertTrue(mock_console.print.called)
        self.assertGreaterEqual(mock_console.print.call_count, 3)


if __name__ == "__main__":
    unittest.main()
