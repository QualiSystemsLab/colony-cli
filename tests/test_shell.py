import unittest

from docopt import DocoptExit, docopt

from colony import shell


class MainShellTest(unittest.TestCase):
    def setUp(self) -> None:
        self.main_doc = shell.__doc__
        self.base_usage = """Usage: colony [--space=<space>] [--token=<token>] [--profile=<profile>] [--help] [--debug]
              <command> [<args>...]"""

    def test_show_base_usage_line(self):
        with self.assertRaises(DocoptExit) as ctx:
            docopt(doc=self.main_doc)

        self.assertEqual(self.base_usage, str(ctx.exception))

    def test_help_needed_with_command(self):
        user_input = ["sb", "--help"]
        args = docopt(doc=self.main_doc, options_first=True, argv=user_input)
        self.assertTrue(shell.is_help_needed(args))

    def test_validate_both_profile_and_creds(self):
        expected = "If --profile is set, neither --space or --token must be provided!\n" + self.base_usage

        user_input = ["--token", "abc", "--profile", "tester", "sb"]
        args = docopt(doc=self.main_doc, options_first=True, argv=user_input)
        with self.assertRaises(DocoptExit) as ctx:
            shell.validate_connection_params(args)
        self.assertEqual(expected, str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
