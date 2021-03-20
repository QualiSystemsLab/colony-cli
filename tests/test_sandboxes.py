import os
import unittest
from unittest.mock import MagicMock

import yaml
from requests import Response

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

    def test_it_should_parse_sandbox_services_and_applications(self):
        # Arrange
        get_sandbox_response = Response()
        get_sandbox_response.status_code = 200
        yaml_response_file = os.path.abspath(os.path.expanduser(os.path.expandvars("fixtures/sandbox.yaml")))
        with open(yaml_response_file) as file:
            sandbox_yaml = yaml.load(file, Loader=yaml.FullLoader)

        get_sandbox_response.json = MagicMock(return_value=sandbox_yaml)
        self.client_with_account.request = MagicMock(return_value=get_sandbox_response)

        # Act
        sandbox = self.sandboxes.get("fake_sandbox_id")

        # Assert
        self.assertEqual(len(sandbox.applications), 1)
        self.assertEqual(sandbox.applications[0].status, "Deploying")
        self.assertEqual(sandbox.applications[0].name, "java-spring-website")

        self.assertEqual(len(sandbox.applications[0].shortcuts), 1)

        self.assertEqual(len(sandbox.services), 1)
        self.assertEqual(sandbox.services[0].status, "Setup")
        self.assertEqual(sandbox.services[0].name, "rds-mysql-instance")


if __name__ == "__main__":
    unittest.main()
