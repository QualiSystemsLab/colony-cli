import unittest
import colony

class TestSum(unittest.TestCase):

    def test_sum(self):
        self.assertEqual(colony.main(), "Hello", "Should be Hello")

if __name__ == '__main__':
    unittest.main()