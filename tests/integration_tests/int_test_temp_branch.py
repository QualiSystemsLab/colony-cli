import logging
import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from git import Repo

from colony import branch_utils, shell
from colony.constants import UNCOMMITTED_BRANCH_NAME
from tests.helpers.repo_utils import (
    achieve_dirty_and_untracked_repo,
    add_untracked,
    create_clean_repo,
    make_repo_dirty,
    readonly_handler,
)

logging.getLogger("git").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


class GitMagicTests(unittest.TestCase):
    def setUp(self) -> None:
        self._repo = None
        self._cwd = os.getcwd()
        # setup testing env

        dst = tempfile.mkdtemp()
        print(f"Temp repo dir = {dst}")
        # -> set working directory to temp folder
        os.chdir(f"{dst}")
        os.mkdir("blueprints")

        # -> do git init on temp folder
        self._repo = create_clean_repo()

    def tearDown(self) -> None:
        # delete temp folder
        os.chdir(self._cwd)
        shutil.rmtree(self._repo.working_dir, onerror=readonly_handler)

    @patch("colony.utils.BlueprintRepo.is_current_branch_synced")
    @patch.object(branch_utils, "create_remote_branch")
    @patch("colony.blueprints.BlueprintsManager.validate")
    @patch.object(branch_utils, "delete_temp_remote_branch")
    @patch("pkg_resources.get_distribution")
    @patch("colony.shell.BootstrapHelper.get_connection_params")
    @patch("colony.branch_utils.debug_output_about_repo_examination")
    @patch("colony.shell.exit")
    def test_blueprint_validate_uncommitted_untracked(self, exit, ex, get_c, get_d, del_t, bp_validate, create_r, is_c):
        # Arrange
        bp_validate.return_value = Mock(errors="")

        current_branch = self._repo.active_branch.name

        achieve_dirty_and_untracked_repo(self._repo)

        # is_current_branch_synced.return_value = False
        for current_branch_sync_state in [True, False]:
            is_c.return_value = current_branch_sync_state

            # Act
            sys.argv[1:] = ["--debug", "bp", "validate", "test2"]
            shell.main()

            # Assert
            self._assert_untracked_reverted_with_untracked(1)
            self._assert_dirty_state_reverted_dirty()
            self._assert_branch_states_reverted(current_branch)

    @patch("colony.utils.BlueprintRepo.is_current_branch_synced")
    @patch.object(branch_utils, "create_remote_branch")
    @patch("colony.blueprints.BlueprintsManager.validate")
    @patch.object(branch_utils, "delete_temp_remote_branch")
    @patch("pkg_resources.get_distribution")
    @patch("colony.shell.BootstrapHelper.get_connection_params")
    @patch("colony.branch_utils.debug_output_about_repo_examination")
    @patch("colony.shell.exit")
    def test_blueprint_validate_uncommitted(self, exit, examination, get_c, get_d, del_t, bp_validate, create_r, is_c):
        # Arrange
        bp_validate.return_value = Mock(errors="")

        current_branch = self._repo.active_branch.name

        make_repo_dirty(self._repo)

        # is_current_branch_synced.return_value = False
        for current_branch_sync_state in [True, False]:
            is_c.return_value = current_branch_sync_state

            # Act
            sys.argv[1:] = ["--debug", "bp", "validate", "test2"]
            shell.main()

            # Assert
            self._assert_untracked_reverted_without_untracked()
            self._assert_dirty_state_reverted_dirty()
            self._assert_branch_states_reverted(current_branch)

    @patch("colony.utils.BlueprintRepo.is_current_branch_synced")
    @patch.object(branch_utils, "create_remote_branch")
    @patch("colony.blueprints.BlueprintsManager.validate")
    @patch.object(branch_utils, "delete_temp_remote_branch")
    @patch("pkg_resources.get_distribution")
    @patch("colony.shell.BootstrapHelper.get_connection_params")
    @patch("colony.branch_utils.debug_output_about_repo_examination")
    @patch("colony.shell.exit")
    def test_blueprint_validate_committed_untracked(self, exit, exam, get_c, get_d, del_t, bp_validate, create_r, is_c):
        # Arrange
        bp_validate.return_value = Mock(errors="")

        current_branch = self._repo.active_branch.name

        add_untracked(self._repo)

        # is_current_branch_synced.return_value = False
        for current_branch_sync_state in [True, False]:
            is_c.return_value = current_branch_sync_state

            # Act
            sys.argv[1:] = ["--debug", "bp", "validate", "test2"]
            shell.main()

            # Assert
            self._assert_untracked_reverted_with_untracked(1)
            self._assert_dirty_state_reverted_clean()
            self._assert_branch_states_reverted(current_branch)

    @patch("colony.utils.BlueprintRepo.is_current_branch_synced")
    @patch.object(branch_utils, "create_remote_branch")
    @patch("colony.blueprints.BlueprintsManager.validate")
    @patch.object(branch_utils, "delete_temp_remote_branch")
    @patch("pkg_resources.get_distribution")
    @patch("colony.shell.BootstrapHelper.get_connection_params")
    @patch("colony.branch_utils.debug_output_about_repo_examination")
    @patch("colony.shell.exit")
    def test_blueprint_validate_committed(self, exit, exam, get_c, get_d, del_t, bp_validate, create_r, is_c):
        # Arrange
        bp_validate.return_value = Mock(errors="")

        current_branch = self._repo.active_branch.name

        # is_current_branch_synced.return_value = False
        for current_branch_sync_state in [True, False]:
            is_c.return_value = current_branch_sync_state

            # Act
            sys.argv[1:] = ["--debug", "bp", "validate", "test2"]
            shell.main()

            # Assert
            self._assert_untracked_reverted_without_untracked()
            self._assert_dirty_state_reverted_clean()
            self._assert_branch_states_reverted(current_branch)

    def _assert_dirty_state_reverted_dirty(self) -> None:
        changed_files_list = self._repo.git.diff("HEAD", name_only=True).split("\n")
        self.assertEqual(len(changed_files_list), 1)
        self.assertEqual(changed_files_list[0], "dirty.txt")

    def _assert_dirty_state_reverted_clean(self) -> None:
        changed_files_list = self._repo.git.diff("HEAD", name_only=True).split("\n")
        self.assertEqual(len(changed_files_list), 1)
        self.assertEqual(changed_files_list[0], "")

    def _assert_untracked_reverted_with_untracked(self, num_of_untracked) -> None:
        self.assertEqual(len(self._repo.untracked_files), num_of_untracked)
        self.assertTrue(self._repo.untracked_files[0], "untracked.txt")

    def _assert_untracked_reverted_without_untracked(self) -> None:
        self.assertEqual(len(self._repo.untracked_files), 0)

    def _assert_branch_states_reverted(self, current_branch: Repo) -> None:
        # Check local temp branch was deleted
        for branch in self._repo.branches:
            self.assertFalse(branch.name.startswith(UNCOMMITTED_BRANCH_NAME))
        # Check branch reverted to original
        self.assertEqual(self._repo.active_branch.name, current_branch)
