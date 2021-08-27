import json
import unittest
from unittest import mock

from colony.blueprints import Blueprint
from colony.services.branding import Brand, Branding


class TestBlueprintJsonLoad(unittest.TestCase):
    def setUp(self) -> None:
        Branding.Brand = Brand.Torque
        manager = mock.Mock()
        bp_json_file = "tests/fixtures/test_bp.json"
        with open(bp_json_file) as f:
            json_obj = json.load(f)
            self.blueprint = Blueprint.json_deserialize(manager=manager, json_obj=json_obj)

    def test_has_errors_attr(self):
        self.assertTrue(hasattr(self.blueprint, "errors"))

    def test_has_desc_attr(self):
        self.assertTrue(hasattr(self.blueprint, "description"))

    def test_bp_has_correct_desc(self):
        expected = "A dev environment for both local and offshore teams"
        self.assertEqual(expected, self.blueprint.description)

    def test_bp_has_no_errors(self):
        self.assertFalse(self.blueprint.errors)


if __name__ == "__main__":
    unittest.main()
