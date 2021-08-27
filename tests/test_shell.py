import unittest
from unittest.mock import Mock, patch

from docopt import DocoptExit, docopt

from colony import shell
from colony.parsers.global_input_parser import GlobalInputParser
from colony.services.branding import Brand, Branding
from colony.shell import BootstrapHelper


class MainShellTest(unittest.TestCase):
    def setUp(self) -> None:
        Branding.Brand = Brand.Torque
        self.main_doc = shell.__doc__
        self.base_usage = """Usage: {command_name} [--space=<space>] [--token=<token>] [--account=<account>] 
              [--profile=<profile>] [--help] [--debug]
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

    def test_help_needed_with_command_no_subcommand_args(self):
        user_input = ["sb"]
        args = docopt(doc=self.main_doc, options_first=True, argv=user_input)
        input_parser = GlobalInputParser(args)
        self.assertTrue(shell.BootstrapHelper.is_help_message_requested(input_parser))

    def test_help_not_needed_with_command(self):
        user_input = ["sb", "start", "some_blueprint"]
        args = docopt(doc=self.main_doc, options_first=True, argv=user_input)
        input_parser = GlobalInputParser(args)
        self.assertFalse(shell.BootstrapHelper.is_help_message_requested(input_parser))

    @patch("colony.shell.BootstrapHelper.should_get_connection_params")
    def test_get_connection_params_no_need_for_connection(self, should_get_connection_params_mock):
        # arrange
        input_parser = Mock()
        should_get_connection_params_mock.return_value = False

        # act
        conn = BootstrapHelper.get_connection_params(input_parser)

        # assert
        self.assertIsNone(conn)

    @patch("colony.shell.ColonyConnectionProvider")
    @patch("colony.shell.BootstrapHelper.should_get_connection_params")
    def test_get_connection_params_returns_connection(
        self, should_get_connection_params_mock, connection_provider_class_mock
    ):
        # arrange
        input_parser = Mock()

        # act
        conn = BootstrapHelper.get_connection_params(input_parser)

        # assert
        self.assertEqual(conn, connection_provider_class_mock.return_value.get_connection.return_value)

    def test_validate_command(self):
        # arrange
        expected_commands = ["bp", "blueprint", "sb", "sandbox", "configure"]

        # act - make sure all expected commands are valid
        for command in expected_commands:
            BootstrapHelper.validate_command(command)

        with self.assertRaises(DocoptExit):
            BootstrapHelper.validate_command(Mock())

    def test_is_config_mode_true(self):
        # arrange
        input_parser = Mock(command="configure")

        # act
        result = BootstrapHelper.is_config_mode(input_parser)

        # assert
        self.assertTrue(result)

    def test_is_config_mode_false(self):
        # arrange
        input_parser = Mock(command="blueprint")

        # act
        result = BootstrapHelper.is_config_mode(input_parser)

        # assert
        self.assertFalse(result)

    @patch("colony.shell.BootstrapHelper.is_config_mode")
    @patch("colony.shell.BootstrapHelper.is_help_message_requested")
    def test_should_get_connection_params_true(self, is_help_message_requested_mock, is_config_mode_mock):
        # arrange
        input_parser = Mock()
        is_help_message_requested_mock.return_value = False
        is_config_mode_mock.return_value = False

        # act
        result = BootstrapHelper.should_get_connection_params(input_parser)

        # assert
        self.assertTrue(result)

    @patch("colony.shell.BootstrapHelper.is_config_mode")
    @patch("colony.shell.BootstrapHelper.is_help_message_requested")
    def test_should_get_connection_params_false(self, is_help_message_requested_mock, is_config_mode_mock):
        # arrange 1
        input_parser = Mock()
        is_help_message_requested_mock.return_value = True
        is_config_mode_mock.return_value = True
        # act 1
        result = BootstrapHelper.should_get_connection_params(input_parser)
        # assert 1
        self.assertFalse(result)

        # arrange 2
        is_help_message_requested_mock.return_value = False
        # act 2
        result = BootstrapHelper.should_get_connection_params(input_parser)
        # assert 2
        self.assertFalse(result)

        # arrange 3
        is_help_message_requested_mock.return_value = True
        is_config_mode_mock.return_value = False
        # act 3
        result = BootstrapHelper.should_get_connection_params(input_parser)
        # assert 3
        self.assertFalse(result)
