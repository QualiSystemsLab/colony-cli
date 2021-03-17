import os
import unittest

from colony.config import ColonyConfigProvider
from colony.exceptions import ConfigError


class TestConfigProvider(unittest.TestCase):
    def setUp(self) -> None:
        test_config_file = os.path.abspath(os.path.expanduser(os.path.expandvars("tests/fixtures/test_config")))
        self.provider = ColonyConfigProvider(filename=test_config_file)

    def test_correct_default_path(self):
        self.assertEqual(self.provider.default_config_path, "~/.colony/config")

    def test_filename_not_exist(self):
        wrong_file_name = "fixtures/test_config_wrong"
        with self.assertRaises(ConfigError):
            _ = ColonyConfigProvider(filename=wrong_file_name)

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
        filename = "fixtures/wrong_config"
        with self.assertRaises(ConfigError):
            _ = ColonyConfigProvider(filename=filename)

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


if __name__ == "__main__":
    unittest.main()
