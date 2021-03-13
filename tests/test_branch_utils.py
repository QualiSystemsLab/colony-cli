import unittest
from unittest.mock import MagicMock, patch

from colony import branch_utils
from colony.constants import UNCOMMITTED_BRANCH_NAME


class TestStashLogicFunctions(unittest.TestCase):
    def setUp(self):
        self.switch = branch_utils.switch_to_temp_branch
        self.revert = branch_utils.revert_from_temp_branch

    @patch.object(branch_utils, "create_remote_branch")
    @patch.object(branch_utils, "commit_to_local_branch")
    @patch.object(branch_utils, "preserve_uncommitted_code")
    @patch.object(branch_utils, "create_local_branch")
    @patch.object(branch_utils, "stash_local_changes")
    def test_switch_to_temp_branch_dirtyrepo(self, mock5, mock4, mock3, mock2, mock1):
        # Arrange:
        mock_repo = MagicMock()
        mock_repo.is_dirty = MagicMock(return_value=True)
        defined_branch_in_file = MagicMock()
        # Act:
        uncommitted_branch_name = self.switch(mock_repo, defined_branch_in_file)
        # Assert:
        mock1.assert_called_once_with(mock_repo, uncommitted_branch_name)
        mock2.assert_called_once_with(mock_repo)
        mock3.assert_called_once_with(mock_repo)
        mock4.assert_called_once_with(mock_repo, uncommitted_branch_name)
        mock5.assert_called_once_with(mock_repo)
        self.assertTrue(uncommitted_branch_name.startswith(UNCOMMITTED_BRANCH_NAME))

    @patch.object(branch_utils, "create_remote_branch")
    @patch.object(branch_utils, "commit_to_local_branch")
    @patch.object(branch_utils, "preserve_uncommitted_code")
    @patch.object(branch_utils, "create_local_branch")
    @patch.object(branch_utils, "stash_local_changes")
    def test_switch_to_temp_branch_cleanrepo(self, mock5, mock4, mock3, mock2, mock1):
        # Arrange:
        mock_repo = MagicMock()
        mock_repo.is_dirty = MagicMock(return_value=False)
        mock_repo.untracked_files = False
        defined_branch_in_file = MagicMock()
        # Act:
        uncommitted_branch_name = self.switch(mock_repo, defined_branch_in_file)
        # Assert:
        mock1.assert_called_once_with(mock_repo, uncommitted_branch_name)
        mock2.assert_called_once_with(mock_repo)
        mock3.assert_not_called()
        mock4.assert_called_once_with(mock_repo, uncommitted_branch_name)
        mock5.assert_not_called()
        self.assertTrue(uncommitted_branch_name.startswith(UNCOMMITTED_BRANCH_NAME))

    @patch.object(branch_utils, "checkout_remote_branch")
    @patch.object(branch_utils, "revert_from_uncommitted_code")
    def test_revert_from_temp_branch(self, mock2, mock1):
        # Arrange:
        mock_repo = MagicMock()
        active_branch = "active_branch"
        # Act:
        self.revert(mock_repo, active_branch)
        # Assert:
        mock1.assert_called_once_with(
            mock_repo,
            active_branch,
        )
        mock2.assert_called_once_with(mock_repo)
