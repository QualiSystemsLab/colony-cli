import unittest

from colony.view.configure_list_view import ConfigureListView
from tests.helpers.builders import ConfigBuilder


class TestConfigureListView(unittest.TestCase):
    def test_render_empty_config(self):
        # act
        render_result = ConfigureListView(None).render()

        # arrange
        self.assertEqual(render_result, "Config file is empty. Use 'colony configure set' to configure Colony CLI.")

    def test_render_single_profile_with_account(self):
        # arrange
        config = ConfigBuilder().with_profile("default", "space1", "token1", "account1").build()
        expected_result = """Profile Name    Colony Account    Space Name    Token
--------------  ----------------  ------------  -------------
default         account1          space1        *********ken1"""

        # act
        render_result = ConfigureListView(config).render()

        # assert
        self.assertEqual(render_result, expected_result)

    def test_render_single_profile_no_account(self):
        # arrange
        config = ConfigBuilder().with_profile("default", "space1", "token1").build()
        expected_result = """Profile Name    Colony Account    Space Name    Token
--------------  ----------------  ------------  -------------
default                           space1        *********ken1"""

        # act
        render_result = ConfigureListView(config).render()

        # assert
        self.assertEqual(render_result, expected_result)

    def test_render_masks_token(self):
        # arrange
        token = "my_very_secure_token"
        config = ConfigBuilder().with_profile("default", "space1", token).build()

        # act
        render_result = ConfigureListView(config).render()

        # assert
        self.assertNotIn(token, render_result)

    def test_render_multiple_profiles(self):
        # arrange
        config = (
            ConfigBuilder()
            .with_profile("default", "space1", "token1")
            .with_profile("customer2", "space2", "token2", "account2")
            .build()
        )

        expected_result = """Profile Name    Colony Account    Space Name    Token
--------------  ----------------  ------------  -------------
default                           space1        *********ken1
customer2       account2          space2        *********ken2"""

        # act
        render_result = ConfigureListView(config).render()

        # assert
        self.assertEqual(render_result, expected_result)
