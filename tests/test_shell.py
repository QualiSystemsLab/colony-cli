import unittest

from docopt import DocoptExit, docopt

from colony import shell
from colony.parsers.input_parser import GlobalInputParser


class MainShellTest(unittest.TestCase):
    def setUp(self) -> None:
        self.main_doc = shell.__doc__
        self.base_usage = """Usage: colony [--space=<space>] [--token=<token>] [--account=<account>] [--profile=<profile>] [--help] [--debug]
              <command> [<args>...]"""

    def test_show_base_usage_line(self):
        with self.assertRaises(DocoptExit) as ctx:
            docopt(doc=self.main_doc)

        self.assertEqual(self.base_usage, str(ctx.exception))

    def test_help_needed_with_command(self):
        user_input = ["sb", "--help"]
        args = docopt(doc=self.main_doc, options_first=True, argv=user_input)
        input_parser = GlobalInputParser(args)
        self.assertTrue(shell.BootstrapHelper.is_help_message_requested(input_parser))
