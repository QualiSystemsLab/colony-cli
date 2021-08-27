import os
import unittest
from configparser import ConfigParser
from unittest.mock import Mock, mock_open, patch

from colony.exceptions import ConfigError, ConfigFileMissingError
from colony.services.branding import Brand, Branding
from colony.services.config import ColonyConfigProvider


class TestConfigProvider(unittest.TestCase):
    def setUp(self) -> None:
        Branding.Brand = Brand.Torque
        test_config_file = os.path.abspath(os.path.expanduser(os.path.expandvars("tests/fixtures/test_config")))
        self.provider = ColonyConfigProvider(filename=test_config_file)

    def test_correct_default_path(self):
        self.assertEqual(ColonyConfigProvider().filename, "~/.torque/config")

    def test_filename_not_exist(self):
        wrong_file_name = "tests/fixtures/test_config_wrong"
        with self.assertRaises(ConfigFileMissingError):
            _ = ColonyConfigProvider(filename=wrong_file_name).load_connection()

    def test_raise_on_wrong_profile(self):
        wrong_profile = "fake_tester"
        with self.assertRaises(ConfigError):
            _ = self.provider.load_connection(wrong_profile)

    def test_correct_default_load(self):
        expected = ("test", "zzvvccbb")
        result = self.provider.load_connection()
        self.assertEqual(expected, (result["space"], result["token"]))

    def test_load_connection_return_type(self):
        self.assertIsInstance(self.provider.load_connection(), dict)

    def test_wrong_setting_file(self):
        filename = "tests/fixtures/wrong_config"
        with self.assertRaises(ConfigError):
            _ = ColonyConfigProvider(filename).load_connection()

    def test_wrong_settings(self):
        wrong_profile = "tester-2"
        with self.assertRaises(ConfigError):
            _ = self.provider.load_connection(wrong_profile)

    def test_token_and_space_must_appear_together(self):
        wrong_profile = "tester-3"
        with self.assertRaises(ConfigError):
            _ = self.provider.load_connection(wrong_profile)

    def test_account_is_accepted_as_config_setting(self):
        expected = ("trial", "abcd", "myaccount")
        result = self.provider.load_connection("tester-4")
        self.assertEqual(expected, (result["space"], result["token"], result["account"]))

    def test_load_all_profiles(self):
        # act
        result = self.provider.load_all()

        # assert
        self.assertEqual(len(result), 5)
        self.assertTrue("default" in result)
        for i in list(range(1, 5)):
            self.assertTrue(f"tester-{i}" in result)

    def test_save_profile_config_doesnt_exist(self):
        # arrange
        filename = "tests/fixtures/new_config"
        config_provider = ColonyConfigProvider(filename)
        config_provider._save_config_to_file = Mock()

        # act
        config_provider.save_profile("default", "token1", "space1", "account1")

        # assert
        config_provider._save_config_to_file.assert_called_once()
        self.assertIsInstance(config_provider.config_obj, ConfigParser)
        self.assertTrue(config_provider.config_obj.has_section("default"))
        self.assertEqual(config_provider.config_obj.get("default", "token"), "token1")
        self.assertEqual(config_provider.config_obj.get("default", "space"), "space1")
        self.assertEqual(config_provider.config_obj.get("default", "account"), "account1")

    def test_save_profile_without_account_config_doesnt_exist(self):
        # arrange
        filename = "test/fixtures/new_config"
        config_provider = ColonyConfigProvider(filename)
        config_provider._save_config_to_file = Mock()

        # act
        config_provider.save_profile("default", "token1", "space1")

        # assert
        config_provider._save_config_to_file.assert_called_once()
        self.assertIsNone(config_provider.config_obj.get("default", "account", fallback=None))

    def test_save_profile_existing_config_new_section(self):
        # arrange
        self.provider._save_config_to_file = Mock()

        # act
        self.provider.save_profile("new_profile", "token1", "space1", "account1")

        # assert
        self.provider._save_config_to_file.assert_called_once()
        self.assertIsInstance(self.provider.config_obj, ConfigParser)
        self.assertTrue(self.provider.config_obj.has_section("new_profile"))
        self.assertEqual(self.provider.config_obj.get("new_profile", "token"), "token1")
        self.assertEqual(self.provider.config_obj.get("new_profile", "space"), "space1")
        self.assertEqual(self.provider.config_obj.get("new_profile", "account"), "account1")

    def test_save_profile_existing_config_existing_section(self):
        # arrange
        self.provider._save_config_to_file = Mock()

        # act
        self.provider.save_profile("default", "token1", "space1", "account1")

        # assert
        self.provider._save_config_to_file.assert_called_once()
        self.assertIsInstance(self.provider.config_obj, ConfigParser)
        self.assertTrue(self.provider.config_obj.has_section("default"))
        self.assertEqual(self.provider.config_obj.get("default", "token"), "token1")
        self.assertEqual(self.provider.config_obj.get("default", "space"), "space1")
        self.assertEqual(self.provider.config_obj.get("default", "account"), "account1")

    def test_save_profile_save_error(self):
        self.provider._save_config_to_file = Mock(side_effect=IOError)

        with self.assertRaises(ConfigError):
            self.provider.save_profile("some_profile", "some_token", "some_space")

        self.provider._save_config_to_file.assert_called_once()

    def test_save_config_to_file(self):
        self.provider.config_obj = Mock()
        with patch("builtins.open", mock_open()) as open_mock:
            self.provider._save_config_to_file()
            self.provider.config_obj.write.assert_called_once_with(open_mock.return_value)

    def test_save_profile_bad_config_file(self):
        # arrange
        filename = "tests/fixtures/wrong_config"
        config_provider = ColonyConfigProvider(filename)
        config_provider._save_config_to_file = Mock()

        # act
        config_provider.save_profile("some_profile", "token1", "space1")

        # assert
        config_provider._save_config_to_file.assert_called_once()
        self.assertIsInstance(config_provider.config_obj, ConfigParser)
        self.assertTrue(config_provider.config_obj.has_section("some_profile"))
        self.assertEqual(config_provider.config_obj.get("some_profile", "token"), "token1")
        self.assertEqual(config_provider.config_obj.get("some_profile", "space"), "space1")

    def test_remove_profile(self):
        # arrange
        self.provider._save_config_to_file = Mock()

        # act
        self.provider.remove_profile("tester-1")

        # assert
        self.assertFalse(self.provider.config_obj.has_section("tester-1"))
        self.provider._save_config_to_file.assert_called_once()

    def test_remove_profile_unknown_profile(self):
        # arrange
        self.provider._save_config_to_file = Mock()

        # act
        self.provider.remove_profile("wrong_profile")

        # assert
        self.provider._save_config_to_file.assert_not_called()

    def test_remove_profile_raises_when_no_config_file(self):
        # arrange
        filename = "new_config"
        config_provider = ColonyConfigProvider(filename)
        config_provider._save_config_to_file = Mock()

        with self.assertRaises(ConfigFileMissingError):
            config_provider.remove_profile(Mock())

    def test_remove_profile_raises_config_error_on_save_error(self):
        # arrange
        self.provider._save_config_to_file = Mock(side_effect=ConfigError)

        with self.assertRaises(ConfigError):
            self.provider.remove_profile("default")
