import unittest

from colony.client import ColonyClient
from colony.services.branding import Brand, Branding


class TestClient(unittest.TestCase):
    def setUp(self) -> None:
        Branding.Brand = Brand.Torque
        self.client = ColonyClient()
        self.client_with_account = ColonyClient(account="my_account")

    def test_default_api_path(self):
        client = ColonyClient()
        expected = "https://qtorque.io/api/"
        self.assertEqual(client.base_url, expected)

    def test_request_wrong_method(self):
        endpoint = "blueprints/"
        with self.assertRaises(ValueError):
            self.client.request(endpoint=endpoint, method="UPDATE")

    def test_if_account_provided_client_base_url_includes_it(self):
        self.assertEqual(self.client_with_account.base_url, "https://my_account.qtorque.io/api/")


if __name__ == "__main__":
    unittest.main()
