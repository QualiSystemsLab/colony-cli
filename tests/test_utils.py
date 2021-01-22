import unittest
from colony import utils


class TestParseParamString(unittest.TestCase):
    def setUp(self):
        self.parse_fun = utils.parse_comma_separated_string

    def test_is_result_dict(self):
        line = None
        result = self.parse_fun(line)
        self.assertIsInstance(result, dict)

    def test_return_empty_dict(self):
        line = None
        result = self.parse_fun(line)
        self.assertDictEqual(result, {})

    def test_trailing_spaces(self):
        line = " key1 =val1,key2 = val2"
        expected = {"key1": "val1", "key2": "val2"}
        result = self.parse_fun(line)
        self.assertDictEqual(result, expected)

    def test_raise_exception_on_space_del(self):
        line = "key1=val1 key2=val2"
        with self.assertRaises(ValueError):
            self.parse_fun(line)

    def test_raise_exception_on_colon(self):
        line = "key1:val1, key2:val2"
        with self.assertRaises(ValueError):
            self.parse_fun(line)


if __name__ == '__main__':
    unittest.main()
