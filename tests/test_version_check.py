import unittest
from unittest.mock import Mock, patch

from colony.services.version import VersionCheckService


class VersionCheckServiceTests(unittest.TestCase):

    @patch('colony.services.version.requests')
    def test_no_newer_version(self, requests_mock):
        # arrange
        versions_checker = VersionCheckService("1.0.0")
        versions_checker._show_new_version_message = Mock()
        requests_mock.get.return_value = Mock(json=Mock(return_value={"a": "b"}))

        # act
        versions_checker.check_for_new_version_safely()

        # assert
        versions_checker._show_new_version_message.assert_not_called()

    def _get_