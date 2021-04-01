import os
import unittest
from unittest import mock
from unittest.mock import Mock

from colony.parsers.input_parser import GlobalInputParser


class TestGlobalInputParser(unittest.TestCase):
    def test_get_token_from_args(self):
        # arrange
        token_mock = Mock()
        args = {"--token": token_mock}
        input_parser = GlobalInputParser(args)

        # act
        token = input_parser.token

        # assert
        self.assertEqual(token, token_mock)

    @mock.patch.dict(os.environ, {"COLONY_TOKEN": "colony_token"})
    def test_get_token_from_env_var(self):
        # arrange
        args = {}
        input_parser = GlobalInputParser(args)

        # act
        token = input_parser.token

        # assert
        self.assertEqual(token, "colony_token")

    def test_get_token_returns_none_when_not_exist(self):
        # arrange
        args = {}
        input_parser = GlobalInputParser(args)

        # act
        token = input_parser.token

        # assert
        self.assertIsNone(token)

    def test_get_space_from_args(self):
        # arrange
        space_mock = Mock()
        args = {"--space": space_mock}
        input_parser = GlobalInputParser(args)

        # act
        space = input_parser.space

        # assert
        self.assertEqual(space, space_mock)

    @mock.patch.dict(os.environ, {"COLONY_SPACE": "colony_space"})
    def test_get_space_from_env_var(self):
        # arrange
        args = {}
        input_parser = GlobalInputParser(args)

        # act
        space = input_parser.space

        # assert
        self.assertEqual(space, "colony_space")

    def test_get_space_returns_none_when_not_exist(self):
        # arrange
        args = {}
        input_parser = GlobalInputParser(args)

        # act
        space = input_parser.space

        # assert
        self.assertIsNone(space)

    def test_get_account_from_args(self):
        # arrange
        account_mock = Mock()
        args = {"--account": account_mock}
        input_parser = GlobalInputParser(args)

        # act
        account = input_parser.account

        # assert
        self.assertEqual(account, account_mock)

    @mock.patch.dict(os.environ, {"COLONY_ACCOUNT": "colony_account"})
    def test_get_account_from_env_var(self):
        # arrange
        args = {}
        input_parser = GlobalInputParser(args)

        # act
        account = input_parser.account

        # assert
        self.assertEqual(account, "colony_account")

    def test_get_account_returns_none_when_not_exist(self):
        # arrange
        args = {}
        input_parser = GlobalInputParser(args)

        # act
        account = input_parser.account

        # assert
        self.assertIsNone(account)

    def test_get_profile_from_args(self):
        # arrange
        account_mock = Mock()
        args = {"--profile": account_mock}
        input_parser = GlobalInputParser(args)

        # act
        profile = input_parser.profile

        # assert
        self.assertEqual(profile, account_mock)

    def test_get_profile_returns_none_when_not_exist(self):
        # arrange
        args = {}
        input_parser = GlobalInputParser(args)

        # act
        profile = input_parser.profile

        # assert
        self.assertIsNone(profile)

    def test_get_debug_from_args(self):
        # arrange
        debug_mock = Mock()
        args = {"--debug": debug_mock}
        input_parser = GlobalInputParser(args)

        # act
        debug = input_parser.debug

        # assert
        self.assertEqual(debug, debug_mock)

    def test_get_debug_returns_none_when_not_exist(self):
        # arrange
        args = {}
        input_parser = GlobalInputParser(args)

        # act
        debug = input_parser.debug

        # assert
        self.assertIsNone(debug)

    def test_get_command_from_args(self):
        # arrange
        command_mock = Mock()
        args = {"<command>": command_mock}
        input_parser = GlobalInputParser(args)

        # act
        command = input_parser.command

        # assert
        self.assertEqual(command, command_mock)

    def test_get_command_returns_none_when_not_exist(self):
        # arrange
        args = {}
        input_parser = GlobalInputParser(args)

        # act
        command = input_parser.command

        # assert
        self.assertIsNone(command)

    def test_get_command_args_from_args(self):
        # arrange
        command_args_mock = Mock()
        args = {"<args>": command_args_mock}
        input_parser = GlobalInputParser(args)

        # act
        command_args = input_parser.command_args

        # assert
        self.assertEqual(command_args, command_args_mock)

    def test_get_command_args_returns_none_when_not_exist(self):
        # arrange
        args = {}
        input_parser = GlobalInputParser(args)

        # act
        command_args = input_parser.command_args

        # assert
        self.assertIsNone(command_args)

    @mock.patch.dict(os.environ, {"COLONY_CONFIG_PATH": "some_path"})
    def test_get_config_path_from_env_var(self):
        # arrange
        args = {}
        input_parser = GlobalInputParser(args)

        # act
        config_path = input_parser.get_config_path()

        # assert
        self.assertEqual(config_path, "some_path")

    def test_get_config_path_returns_none_when_not_exist(self):
        # arrange
        args = {}
        input_parser = GlobalInputParser(args)

        # act
        config_path = input_parser.get_config_path()

        # assert
        self.assertIsNone(config_path)