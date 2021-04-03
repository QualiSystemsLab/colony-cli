import unittest

from colony.view.view_helper import mask_token


class TestViewHelper(unittest.TestCase):
    def test_token_masked_4_last_chars_displayed(self):
        # arrange
        token = "66977d3f306941b1bbac8f58219f3f6f"

        # act
        masked_token = mask_token(token)

        # assert
        self.assertEqual(masked_token, "*********3f6f")

    def test_mask_token_returns_empty_string_when_called_without_token(self):
        self.assertEqual(mask_token(""), "")
        self.assertEqual(mask_token(None), "")