import unittest
from unittest import mock
from unittest.mock import Mock, patch

from docopt import DocoptExit

from colony.commands.base import BaseCommand
from colony.commands.bp import BlueprintsCommand
from colony.commands.configure import ConfigureCommand
from colony.commands.sb import SandboxesCommand
from colony.exceptions import ConfigFileMissingError
from colony.services.branding import Brand, Branding


class TestBaseCommand(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        Branding.Brand = Brand.Torque
        cls.connection = mock.Mock()
        cls.connection.space = "test_space"
        cls.connection.token = "test_token"

        cls.manager = mock.Mock()

    def setUp(self) -> None:
        self.command = BaseCommand([], self.connection)

    def test_initialize_with_connection(self):
        self.assertIsNotNone(self.command.client)
        self.assertIsNotNone(self.command.manager)
        self.assertFalse(self.command.get_actions_table())

    def test_initialize_without_connection(self):
        command = BaseCommand([])
        self.assertIsNone(command.client)
        self.assertIsNone(command.manager)

    def test_execute_raises_error(self):
        self.assertRaises(DocoptExit, self.command.execute)


class TestBlueprintCommand(unittest.TestCase):
    def test_base_help_usage_line(self):
        expected_usage = """usage:
        torque (bp | blueprint) validate <name> [options]
        torque (bp | blueprint) [--help]"""

        with self.assertRaises(DocoptExit) as ctx:
            _ = BlueprintsCommand(command_args=[])

        self.assertEqual(expected_usage, str(ctx.exception))

    def test_actions_table(self):
        args = "bp validate test".split()
        command = BlueprintsCommand(command_args=args)

        for action in ["validate"]:
            self.assertIn(action, command.get_actions_table())

    def test_do_validate_commit_only(self):
        args = "bp validate test --commit abc123".split()
        command = BlueprintsCommand(command_args=args)
        self.assertRaises(DocoptExit, command.do_validate)


class TestSandboxCommand(unittest.TestCase):
    def test_base_help_usage_line(self):
        expected_usage = """usage:
        torque (sb | sandbox) start <blueprint_name> [options]
        torque (sb | sandbox) status <sandbox_id>
        torque (sb | sandbox) end <sandbox_id>
        torque (sb | sandbox) list [--filter={all|my|auto}] [--show-ended] [--count=<N>]
        torque (sb | sandbox) [--help]"""

        with self.assertRaises(DocoptExit) as ctx:
            _ = SandboxesCommand(command_args=[])

        self.assertEqual(expected_usage, str(ctx.exception))

    def test_actions_table(self):
        args = "sb start test".split()
        command = SandboxesCommand(command_args=args)
        expected_actions = ["start", "end", "status", "list"]
        for action in command.get_actions_table():
            self.assertIn(action, expected_actions)

    def validate_command_input(self, input_line: str, func: str) -> None:
        args = input_line.split()
        command = SandboxesCommand(command_args=args)
        self.assertRaises(DocoptExit, getattr(command, func))

    def test_start_negative_timeout(self):
        line = "sb start test --wait -10"
        func = "do_start"
        self.validate_command_input(line, func)

    def test_start_negative_duration(self):
        line = "sb start test --duration -10"
        func = "do_start"
        self.validate_command_input(line, func)

    def test_start_not_number_duration(self):
        line = "sb start test --duration abc"
        func = "do_start"
        self.validate_command_input(line, func)

    def test_start_not_number_timeout(self):
        line = "sb start test --wait abc"
        func = "do_start"
        self.validate_command_input(line, func)

    def test_start_commit_without_branch(self):
        line = "sb start test --commit abc"
        func = "do_start"
        self.validate_command_input(line, func)


class TestConfigureCommand(unittest.TestCase):
    def test_base_help_usage_line(self):
        expected_usage = """usage:
        torque configure set
        torque configure list
        torque configure remove <profile>
        torque configure [--help|-h]"""

        with self.assertRaises(DocoptExit) as ctx:
            _ = ConfigureCommand(command_args=[])

        self.assertEqual(expected_usage, str(ctx.exception))

    def test_actions_table(self):
        args = "configure list".split()
        command = ConfigureCommand(command_args=args)
        expected_actions = ["set", "list", "remove"]
        for action in command.get_actions_table():
            self.assertIn(action, expected_actions)

    @patch("colony.commands.configure.ColonyConfigProvider")
    @patch("colony.commands.configure.GlobalInputParser")
    def test_configure_list(self, global_input_parser, config_provider):
        # arrange
        args = "configure list".split()
        command = ConfigureCommand(args)
        command.message = Mock()

        # act
        result = command.do_list()

        # assert
        self.assertTrue(result)
        command.message.assert_called_once()

    @patch("colony.commands.configure.ColonyConfigProvider")
    @patch("colony.commands.configure.GlobalInputParser")
    def test_configure_list_missing_config(self, global_input_parser, config_provider):
        # arrange
        config_provider.return_value.load_all.side_effect = ConfigFileMissingError()
        args = "configure list".split()
        command = ConfigureCommand(args)

        # act & assert
        with self.assertRaises(DocoptExit):
            command.do_list()

    @patch("colony.commands.configure.ConfigureListView")
    @patch("colony.commands.configure.ColonyConfigProvider")
    @patch("colony.commands.configure.GlobalInputParser")
    def test_configure_list_return_false_on_unexpected_error(self, global_input_parser, config_provider, list_view):
        # arrange
        args = "configure list".split()
        command = ConfigureCommand(args)
        list_view.return_value.render.side_effect = Exception("some error")

        # act
        result = command.do_list()

        # assert
        self.assertFalse(result)

    @patch("colony.commands.configure.ColonyConfigProvider")
    @patch("colony.commands.configure.GlobalInputParser")
    def test_configure_test(self, global_input_parser, config_provider):
        # arrange
        args = "configure remove profile_name".split()
        command = ConfigureCommand(args)

        # act
        result = command.do_remove()

        # assert
        self.assertTrue(result)
        config_provider.return_value.remove_profile.assert_called_once_with("profile_name")

    @patch("colony.commands.configure.ColonyConfigProvider")
    @patch("colony.commands.configure.GlobalInputParser")
    def test_configure_test_returns_false_delete_error(self, global_input_parser, config_provider):
        # arrange
        args = "configure remove profile_name".split()
        command = ConfigureCommand(args)
        config_provider.return_value.remove_profile.side_effect = ValueError()

        # act
        result = command.do_remove()

        # assert
        self.assertFalse(result)
