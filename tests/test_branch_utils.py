import unittest
from datetime import datetime
from unittest.mock import patch, Mock

from colony import branch_utils
from colony.constants import UNCOMMITTED_BRANCH_NAME, FINAL_SB_STATUSES
from colony.exceptions import BadBlueprintRepo
from freezegun import freeze_time


class TestStashLogicFunctions(unittest.TestCase):
    def setUp(self):
        self.switch = branch_utils.switch_to_temp_branch
        self.revert = branch_utils.revert_from_temp_branch
        self.examine = branch_utils.examine_blueprint_working_branch
        self.wait_and_delete = branch_utils.wait_and_delete_temp_branch

    @patch.object(branch_utils, "create_remote_branch")
    @patch.object(branch_utils, "commit_to_local_temp_branch")
    @patch.object(branch_utils, "preserve_uncommitted_code")
    @patch.object(branch_utils, "create_local_temp_branch")
    @patch.object(branch_utils, "stash_local_changes")
    def test_switch_to_temp_branch_dirtyrepo(
        self,
        stash_local_changes,
        create_local_temp_branch,
        preserve_uncommitted_code,
        commit_to_local_temp_branch,
        create_remote_branch,
    ):
        # Arrange:
        mock_repo = Mock()
        mock_repo.is_dirty = Mock(return_value=True)
        defined_branch_in_file = "defined_branch_in_file"
        # Act:
        uncommitted_branch_name, flag = self.switch(mock_repo, defined_branch_in_file)
        # Assert:
        create_remote_branch.assert_called_once_with(mock_repo, uncommitted_branch_name)
        commit_to_local_temp_branch.assert_called_once_with(mock_repo)
        preserve_uncommitted_code.assert_called_once_with(mock_repo)
        create_local_temp_branch.assert_called_once_with(mock_repo, uncommitted_branch_name)
        stash_local_changes.assert_called_once_with(mock_repo)
        self.assertTrue(uncommitted_branch_name.startswith(UNCOMMITTED_BRANCH_NAME))

    @patch.object(branch_utils, "create_remote_branch")
    @patch.object(branch_utils, "commit_to_local_temp_branch")
    @patch.object(branch_utils, "preserve_uncommitted_code")
    @patch.object(branch_utils, "create_local_temp_branch")
    @patch.object(branch_utils, "stash_local_changes")
    def test_switch_to_temp_branch_cleanrepo(
        self,
        stash_local_changes,
        create_local_temp_branch,
        preserve_uncommitted_code,
        commit_to_local_temp_branch,
        create_remote_branch,
    ):
        # Arrange:
        mock_repo = Mock()
        mock_repo.is_dirty = Mock(return_value=False)
        mock_repo.untracked_files = True
        defined_branch_in_file = "defined_branch_in_file"
        # Act:
        uncommitted_branch_name, flag = self.switch(mock_repo, defined_branch_in_file)
        # Assert:
        create_remote_branch.assert_called_once_with(mock_repo, uncommitted_branch_name)
        commit_to_local_temp_branch.assert_called_once_with(mock_repo)
        preserve_uncommitted_code.assert_called_once_with(mock_repo)
        create_local_temp_branch.assert_called_once_with(mock_repo, uncommitted_branch_name)
        stash_local_changes.assert_called_once_with(mock_repo)
        self.assertTrue(uncommitted_branch_name.startswith(UNCOMMITTED_BRANCH_NAME))

    @patch.object(branch_utils, "checkout_remote_branch")
    @patch.object(branch_utils, "revert_from_uncommitted_code")
    def test_revert_from_temp_branch(self, revert_from_uncommitted_code, checkout_remote_branch):
        # Arrange:
        mock_repo = Mock()
        active_branch = "active_branch"
        # Act:
        self.revert(mock_repo, active_branch, True)
        # Assert:
        checkout_remote_branch.assert_called_once_with(
            mock_repo,
            active_branch,
        )
        revert_from_uncommitted_code.assert_called_once_with(mock_repo)


    def test_examine_blueprint_working_branch_detached(self):
        # Arrange:
        mock_repo = Mock()
        mock_blueprint = Mock()
        mock_repo.is_repo_detached = Mock(return_value=True)

        # Act & Assert:
        self.assertRaises(BadBlueprintRepo, self.examine, mock_repo, mock_blueprint)

    def test_examine_blueprint_working_branch_attached(self):
        # Arrange:
        mock_repo = Mock()
        mock_blueprint = Mock()
        mock_repo.is_repo_detached = Mock(return_value=False)

        # Act:
        self.examine(mock_repo, mock_blueprint)

        # Assert:
        mock_repo.is_dirty.assert_called_once()
        mock_repo.is_current_branch_exists_on_remote()
        mock_repo.is_current_branch_synced()

    @freeze_time(datetime.now())
    @patch.object(branch_utils, "is_k8s_blueprint")
    @patch.object(branch_utils, "can_temp_branch_be_deleted")
    @patch.object(branch_utils, "delete_temp_branch")
    def test_wait_and_delete_temp_branch_not_k8s(self, delete_temp_branch, can_temp, is_k8s_blueprint):
        # Arrange:
        mock_sb_manager = Mock()
        mock_sandbox_id = "mock_sandbox_id"
        mock_temp_branch = "mock_temp_branch"
        mock_blueprint_name = "mock_blueprint_name"

        is_k8s_blueprint = Mock(return_value=False)
        can_temp = Mock(return_value=False)

        # Act & assert:
        for final_stage in FINAL_SB_STATUSES:
            mock_repo = Mock(sandbox_status=final_stage)
            self.wait_and_delete(mock_sb_manager, mock_sandbox_id, mock_repo, mock_temp_branch, mock_blueprint_name)
            delete_temp_branch.assert_called_with(mock_repo, mock_temp_branch)
