import unittest

from colony.client import ColonyClient
from colony.sandboxes import SandboxesManager


class TestSandboxes(unittest.TestCase):
    def setUp(self) -> None:
        self.client_with_account = ColonyClient(account="my_account", space="my_space")
        self.sandboxes = SandboxesManager(self.client_with_account)

    def test_ui_link_is_properly_generated(self):
        self.assertEqual(
            self.sandboxes.get_sandbox_ui_link("blah"),
            "https://my_account.cloudshellcolony.com/my_space/sandboxes/blah",
        )

    def test_sandbox_url_properly_generated(self):
        self.assertEqual(
            self.sandboxes.get_sandbox_url("blah"),
            "https://my_account.cloudshellcolony.com/api/spaces/my_space/sandboxes/blah",
        )


if __name__ == "__main__":
    unittest.main()
