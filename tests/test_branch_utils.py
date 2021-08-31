import unittest
from datetime import datetime
from unittest.mock import Mock, patch

import colony.commands.sb
import colony.services.waiter
from colony.branch import branch_utils
from colony.constants import DEFAULT_TIMEOUT, FINAL_SB_STATUSES, UNCOMMITTED_BRANCH_NAME
from colony.exceptions import BadBlueprintRepo


class TestStashLogicFunctions(unittest.TestCase):
    def setUp(self):
        self.switch = branch_utils.switch_to_temp_branch
        self.revert = branch_utils.revert_from_local_temp_branch
        self.check_repo_for_errors = branch_utils.check_repo_for_errors
        self.wait_before_delete = colony.services.waiter.Waiter.wait_for_sandbox_to_launch
        self.debug_output_about_repo_examination = branch_utils.debug_output_about_repo_examination

        self.initialize_mock_vars()

    def initialize_mock_vars(self):
        self.repo = Mock()
        self.sb_manager = Mock()
        self.sandbox = Mock()
        self.sb_manager.get.return_value = self.sandbox
        self.sandbox_id = Mock()
        self.temp_branch = "mock_temp_branch"
        self.blueprint_name = "mock_blueprint_name"

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
        self.repo = Mock()
        self.repo.is_dirty = Mock(return_value=True)
        defined_branch_in_file = "defined_branch_in_file"
        # Act:
        uncommitted_branch_name = self.switch(self.repo, defined_branch_in_file)
        # Assert:
        create_remote_branch.assert_called_once_with(self.repo, uncommitted_branch_name)
        commit_to_local_temp_branch.assert_called_once_with(self.repo)
        preserve_uncommitted_code.assert_called_once_with(self.repo)
        create_local_temp_branch.assert_called_once_with(self.repo, uncommitted_branch_name)
        stash_local_changes.assert_called_once_with(self.repo)
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
        self.repo = Mock()
        self.repo.is_dirty = Mock(return_value=False)
        self.repo.untracked_files = True
        defined_branch_in_file = "defined_branch_in_file"
        # Act:
        uncommitted_branch_name = self.switch(self.repo, defined_branch_in_file)
        # Assert:
        create_remote_branch.assert_called_once_with(self.repo, uncommitted_branch_name)
        commit_to_local_temp_branch.assert_called_once_with(self.repo)
        preserve_uncommitted_code.assert_called_once_with(self.repo)
        create_local_temp_branch.assert_called_once_with(self.repo, uncommitted_branch_name)
        stash_local_changes.assert_called_once_with(self.repo)
        self.assertTrue(uncommitted_branch_name.startswith(UNCOMMITTED_BRANCH_NAME))

    @patch.object(branch_utils, "checkout_remote_branch")
    @patch.object(branch_utils, "revert_from_uncommitted_code")
    def test_revert_from_temp_branch(self, revert_from_uncommitted_code, checkout_remote_branch):
        # Arrange:
        self.repo = Mock()
        active_branch = "active_branch"
        # Act:
        self.revert(self.repo, active_branch, True)
        # Assert:
        checkout_remote_branch.assert_called_once_with(
            self.repo,
            active_branch,
        )
        revert_from_uncommitted_code.assert_called_once_with(self.repo)

    def test_check_repo_for_errors(self):
        # Arrange:
        self.repo = Mock()
        self.repo.is_repo_detached = Mock(return_value=True)

        # Act & Assert:
        self.assertRaises(BadBlueprintRepo, self.check_repo_for_errors, self.repo)

    def test_debug_output_about_repo_examination(self):
        # Arrange:
        self.repo = Mock()
        mock_blueprint = Mock()
        self.repo.is_repo_detached = Mock(return_value=False)

        # Act:
        self.debug_output_about_repo_examination(self.repo, mock_blueprint)

        # Assert:
        self.repo.is_dirty.assert_called_once()
        self.repo.is_current_branch_exists_on_remote()
        self.repo.is_current_branch_synced()

    @patch("time.sleep", return_value=None)
    @patch("colony.branch.branch_utils.can_temp_branch_be_deleted")
    def test_wait_for_sandbox_to_launch_final_stage(self, can_temp, time_sleep):
        # Arrange:
        self.initialize_mock_vars()
        can_temp.return_value = False
        context_branch = Mock()

        # Act & assert:

        for final_stage in FINAL_SB_STATUSES:
            self.sandbox.sandbox_status = final_stage
            start_time = datetime.now()
            self.wait_before_delete(
                self.sb_manager,
                self.sandbox_id,
                DEFAULT_TIMEOUT,
                context_branch,
                False,
            )
            assert (datetime.now() - start_time).seconds < 1

    @patch("time.sleep", return_value=None)
    @patch("colony.branch.branch_utils.can_temp_branch_be_deleted")
    def test_wait_for_sandbox_to_launch_can_be_deleted(self, can_temp, time_sleep):
        # Arrange:
        self.initialize_mock_vars()
        mock_non_final_stage = "mock_non_final_stage"
        can_temp.return_value = True
        self.sandbox.sandbox_status = mock_non_final_stage
        context_branch = Mock()

        # Act:
        timeout_reached = self.wait_before_delete(
            self.sb_manager,
            self.sandbox_id,
            1,
            context_branch,
            False,
        )

        # Assert:
        self.assertFalse(timeout_reached)

    @patch("colony.services.waiter.DEFAULT_TIMEOUT", 0.01)
    @patch("time.sleep", return_value=None)
    @patch("colony.branch.branch_utils.can_temp_branch_be_deleted")
    def test_wait_before_temp_branch_delete_cannot_be_deleted(
        self,
        can_temp,
        time_sleep,
    ):
        # Arrange:

        self.initialize_mock_vars()
        mock_non_final_stage = "mock_non_final_stage"
        can_temp.return_value = False
        self.sandbox.sandbox_status = mock_non_final_stage
        context_branch = Mock()

        # Act:
        timeout_reached = self.wait_before_delete(
            self.sb_manager,
            self.sandbox_id,
            0,
            context_branch,
            False,
        )

        # Assert:
        self.assertTrue(timeout_reached)
