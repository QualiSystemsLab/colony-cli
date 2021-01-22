import unittest

from colony.client import ColonyClient


class TestClient(unittest.TestCase):
    def setUp(self) -> None:
        self.client = ColonyClient()

    def test_default_api_path(self):
        client = ColonyClient()
        expected = "https://cloudshellcolony.com/api/"
        self.assertEqual(client.base_url, expected)

    def test_request_wrong_method(self):
        endpoint = 'blueprints/'
        with self.assertRaises(ValueError):
            self.client.request(endpoint=endpoint, method="UPDATE")


if __name__ == '__main__':
    unittest.main()
