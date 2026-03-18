import unittest
from unittest import mock
from src.main import *

class TestQuitListener(unittest.TestCase):
    def setUp(self):
        self.original_argv = sys.argv[:]

    def tearDown(self):
        sys.argv = self.original_argv

    def test_help_argument(self):
        sys.argv = ['quit_listener.py', '-h']
        with mock.patch('builtins.print') as mock_print:
            ret = main()
        self.assertEqual(ret, 0)
        mock_print.assert_any_call("Read lines from stdin until the word 'quit' is entered.\nUsage: quit_listener.py [-h|--help]")

    def test_quit_immediately(self):
        sys.argv = ['quit_listener.py']
        with mock.patch('builtins.input', side_effect=['quit']):
            with mock.patch('builtins.print') as mock_print:
                ret = main()
        self.assertEqual(ret, 0)
        # No "You typed" should be printed
        calls = [c.args[0] for c in mock_print.call_args_list]
        self.assertTrue(all("You typed:" not in arg for arg in calls))

    def test_typing_and_quit(self):
        sys.argv = ['quit_listener.py']
        inputs = ['hello world', 'quit']
        with mock.patch('builtins.input', side_effect=inputs):
            with mock.patch('builtins.print') as mock_print:
                ret = main()
        self.assertEqual(ret, 0)
        # Verify the echoed line appears
        mock_print.assert_any_call('You typed: hello world')

    def test_eof_handling(self):
        sys.argv = ['quit_listener.py']
        with mock.patch('builtins.input', side_effect=EOFError):
            with mock.patch('builtins.print') as mock_print:
                ret = main()
        self.assertEqual(ret, 0)
        # No error printed
        mock_print.assert_not_called()

    def test_unexpected_exception(self):
        sys.argv = ['quit_listener.py']
        # Force an unexpected exception inside the loop
        def raise_exc(_):
            raise RuntimeError('boom')
        with mock.patch('builtins.input', side_effect=raise_exc):
            with mock.patch('sys.stderr', new_callable=mock.Mock) as mock_stderr:
                ret = main()
        self.assertEqual(ret, 1)
        mock_stderr.write.assert_called()
        written = ''.join(call.args[0] for call in mock_stderr.write.call_args_list)
        self.assertIn('Error: boom', written)

if __name__ == '__main__':
    unittest.main()