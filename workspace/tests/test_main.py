import unittest
import sys
import io
from unittest import mock
from src.main import *

class TestArithmeticFunctions(unittest.TestCase):
    def test_add(self):
        self.assertEqual(add(2, 3), 5)
        self.assertAlmostEqual(add(2.5, 3.1), 5.6)

    def test_sub(self):
        self.assertEqual(sub(5, 3), 2)
        self.assertAlmostEqual(sub(5.5, 2.2), 3.3)

    def test_mul(self):
        self.assertEqual(mul(4, 2), 8)
        self.assertAlmostEqual(mul(1.5, 2), 3.0)

    def test_div(self):
        self.assertEqual(div(10, 2), 5)
        self.assertAlmostEqual(div(7, 2), 3.5)

    def test_div_zero(self):
        with self.assertRaises(ZeroDivisionError):
            div(5, 0)

class TestParseInput(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(parse_input("   "), ("", []))

    def test_single_command(self):
        self.assertEqual(parse_input("HELP"), ("help", []))

    def test_command_with_args(self):
        self.assertEqual(parse_input("Add  2   3"), ("add", ["2", "3"]))

    def test_case_insensitivity(self):
        self.assertEqual(parse_input("QuIt"), ("quit", []))

class TestPrintFunctions(unittest.TestCase):
    def test_print_help(self):
        captured = io.StringIO()
        with mock.patch('sys.stdout', new=captured):
            print_help()
        output = captured.getvalue()
        self.assertIn("Available commands:", output)
        self.assertIn("add a b", output)

    def test_print_error(self):
        captured = io.StringIO()
        with mock.patch('sys.stdout', new=captured):
            print_error("Something went wrong")
        self.assertEqual(captured.getvalue().strip(), "Error: Something went wrong")

class TestExecuteCommand(unittest.TestCase):
    def setUp(self):
        self.stdout_patcher = mock.patch('sys.stdout', new_callable=io.StringIO)
        self.mock_stdout = self.stdout_patcher.start()
        self.addCleanup(self.stdout_patcher.stop)

    def test_help_command(self):
        execute_command('help', [])
        self.assertIn("Available commands:", self.mock_stdout.getvalue())

    def test_unknown_command(self):
        execute_command('foobar', [])
        self.assertIn("Error: Unknown command", self.mock_stdout.getvalue())

    def test_missing_arguments(self):
        execute_command('add', ['1'])
        self.assertIn("Error: Expected two arguments", self.mock_stdout.getvalue())

    def test_non_numeric_arguments(self):
        execute_command('sub', ['a', 'b'])
        self.assertIn("Error: Non-numeric argument", self.mock_stdout.getvalue())

    def test_division_by_zero(self):
        execute_command('div', ['10', '0'])
        self.assertIn("Error: Division by zero", self.mock_stdout.getvalue())

    def test_successful_add(self):
        execute_command('add', ['2', '3'])
        self.assertIn("5.0", self.mock_stdout.getvalue())

    def test_successful_sub(self):
        execute_command('-', ['5', '2'])
        self.assertIn("3.0", self.mock_stdout.getvalue())

    def test_successful_mul(self):
        execute_command('*', ['4', '2.5'])
        self.assertIn("10.0", self.mock_stdout.getvalue())

    def test_successful_div(self):
        execute_command('/', ['9', '3'])
        self.assertIn("3.0", self.mock_stdout.getvalue())

    def test_quit_command_exits(self):
        with mock.patch('sys.exit', side_effect=SystemExit) as mock_exit:
            with self.assertRaises(SystemExit):
                execute_command('quit', [])
            mock_exit.assert_called_once_with(0)
            self.assertIn("Good‑bye!", self.mock_stdout.getvalue())

    def test_exit_alias(self):
        with mock.patch('sys.exit', side_effect=SystemExit):
            with self.assertRaises(SystemExit):
                execute_command('q', [])

if __name__ == '__main__':
    unittest.main()