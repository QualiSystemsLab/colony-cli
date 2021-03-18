import unittest
from unittest.mock import MagicMock, patch

import requests
from requests import Response

from colony.client import ColonyClient
from colony.session import ColonySession


class TestClient(unittest.TestCase):
    def setUp(self) -> None:
        self.client = ColonyClient()
        self.client_with_account = ColonyClient(account="my_account")

    # How easy is it for this test to break if I change the implementation
    # The test should describe a behavior what its actually testing
    # Language  (should)
    # Define what is the the tested component
    def test_the_class_called_http_post_with_parameters_one(self):
        session = ColonySession()
        success = Response()
        success.status_code = 200
        success.json = MagicMock(return_value={"access_token": "blah"})

        session.post = MagicMock(return_value=success)

        email = "dummy_email@email.com"
        password = "pass"
        account = "dummy_account"
        self.client.login(account, email, password, session)
        session.post.assert_called_once_with(url=f"https://cloudshellcolony.com/api/accounts/{account}/login",
                                             json={"email": email, "password": password})

    def test_default_api_path(self):
        client = ColonyClient()
        expected = "https://cloudshellcolony.com/api/"
        self.assertEqual(client.base_url, expected)

    def test_request_wrong_method(self):
        endpoint = "blueprints/"
        with self.assertRaises(ValueError):
            self.client.request(endpoint=endpoint, method="UPDATE")

    def test_if_account_provided_client_base_url_includes_it(self):
        self.assertEqual(self.client_with_account.base_url, "https://my_account.cloudshellcolony.com/api/")


if __name__ == "__main__":
    unittest.main()
