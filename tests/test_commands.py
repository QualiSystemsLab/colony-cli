import unittest
from unittest import mock

from docopt import DocoptExit

from colony.commands.base import BaseCommand
from colony.commands.bp import BlueprintsCommand
from colony.commands.sb import SandboxesCommand
from colony.commands.configure import ConfigureCommand


class TestBaseCommand(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
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
        colony (bp | blueprint) validate <name> [options]
        colony (bp | blueprint) [--help]"""

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
        colony (sb | sandbox) start <blueprint_name> [options]
        colony (sb | sandbox) status <sandbox_id>
        colony (sb | sandbox) end <sandbox_id>
        colony (sb | sandbox) list [--filter={all|my|auto}] [--show-ended] [--count=<N>]
        colony (sb | sandbox) [--help]"""

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
        colony (configure) set
        colony (configure) list
        colony (configure) [--help]"""

        with self.assertRaises(DocoptExit) as ctx:
            _ = ConfigureCommand(command_args=[])

        self.assertEqual(expected_usage, str(ctx.exception))

    def test_actions_table(self):
        args = "configure list".split()
        command = ConfigureCommand(command_args=args)
        expected_actions = ["set", "list"]
        for action in command.get_actions_table():
            self.assertIn(action, expected_actions)
