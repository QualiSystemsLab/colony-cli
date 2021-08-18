import os
import unittest
from unittest import mock

from colony.client import ColonyClient


class TestClient(unittest.TestCase):
    def setUp(self) -> None:
        self.client = ColonyClient()
        self.client_with_account = ColonyClient(account="my_account")

    def test_default_api_path(self):
        client = ColonyClient()
        expected = "https://cloudshellcolony.com/api/"
        self.assertEqual(client.base_url, expected)

    @mock.patch.dict(os.environ, {"CLI_CLIENT_QTORQUE": "1"})
    def test_default_api_path_qtorque(self):
        client = ColonyClient()
        expected = "https://qtorque.io/api/"
        self.assertEqual(client.base_url, expected)

    @mock.patch.dict(os.environ, {"CLI_CLIENT_ICOLONY": "true"})
    def test_default_api_path_icolony(self):
        client = ColonyClient()
        expected = "https://icolony.io/api/"
        self.assertEqual(client.base_url, expected)

    @mock.patch.dict(os.environ, {"CLI_CLIENT_QTORQUE": "1"})
    @mock.patch.dict(os.environ, {"CLI_CLIENT_ICOLONY": "true"})
    @mock.patch.dict(os.environ, {"COLONY_HOSTNAME": "example.com"})
    def test_default_api_path_custom_url(self):
        client = ColonyClient()
        expected = "https://example.com/api/"
        self.assertEqual(client.base_url, expected)

    def test_request_wrong_method(self):
        endpoint = "blueprints/"
        with self.assertRaises(ValueError):
            self.client.request(endpoint=endpoint, method="UPDATE")

    def test_if_account_provided_client_base_url_includes_it(self):
        self.assertEqual(self.client_with_account.base_url, "https://my_account.cloudshellcolony.com/api/")


if __name__ == "__main__":
    unittest.main()
