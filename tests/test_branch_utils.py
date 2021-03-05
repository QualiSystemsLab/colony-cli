import unittest
from unittest.mock import MagicMock, patch

from colony import branch_utils
from colony.branch_utils import UNCOMMITTED_BRANCH_NAME


class TestStashLogicFunctions(unittest.TestCase):
    def setUp(self):
        self.switch = branch_utils.switch_to_temp_branch
        self.revert = branch_utils.revert_from_temp_branch

    @patch.object(branch_utils, "stash_local_changes_and_preserve_uncommitted_code")
    @patch.object(branch_utils, "create_local_branch")
    @patch.object(branch_utils, "create_remote_branch")
    def test_switch_to_temp_branch(self, mock3, mock2, mock1):
        # Arrange:
        mock_repo = MagicMock()
        defined_branch_in_file = MagicMock()
        # Act:
        uncommitted_branch_name = self.switch(mock_repo, defined_branch_in_file)
        # Assert:
        mock1.assert_called_once_with(mock_repo)
        mock2.assert_called_once_with(mock_repo, uncommitted_branch_name)
        mock3.assert_called_once_with(mock_repo, uncommitted_branch_name)
        self.assertTrue(uncommitted_branch_name.startswith(UNCOMMITTED_BRANCH_NAME))

    @patch.object(branch_utils, "checkout_remote_branch")
    @patch.object(branch_utils, "delete_temp_branch")
    @patch.object(branch_utils, "revert_from_uncommitted_code")
    def test_revert_from_temp_branch(self, mock3, mock2, mock1):
        # Arrange:
        mock_repo = MagicMock()
        temp_branch = "temp_branch"
        active_branch = "active_branch"
        # Act:
        self.revert(mock_repo, temp_branch, active_branch)
        # Assert:
        mock1.assert_called_once_with(
            mock_repo,
            active_branch,
        )
        mock2.assert_called_once_with(mock_repo, temp_branch)
        mock3.assert_called_once_with(mock_repo)
