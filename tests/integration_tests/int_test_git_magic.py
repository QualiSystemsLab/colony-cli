import logging
import os
import shutil
import stat
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

import git

from colony import branch_utils, shell
from colony.constants import UNCOMMITTED_BRANCH_NAME

logging.getLogger("git").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


class GitMagicTests(unittest.TestCase):
    def setUp(self) -> None:
        self._repo = None
        self._cwd = os.getcwd()
        # setup testing env
        # -> copy base_repo to temp folder

        dst = tempfile.mkdtemp()
        print(f"temp dir ={dst}")
        # -> set working directory to temp folder
        os.chdir(f"{dst}")
        os.mkdir("blueprints")

        # -> do git init on temp folder
        self._create_clean_repo()
        print("")

    def tearDown(self) -> None:
        # delete temp folder
        os.chdir(self._cwd)
        shutil.rmtree(self._repo.working_dir, onerror=readonly_handler)

    @patch("colony.utils.BlueprintRepo.is_current_state_synced_with_remote")
    @patch.object(branch_utils, "create_remote_branch")
    @patch("colony.blueprints.BlueprintsManager.validate")
    @patch.object(branch_utils, "delete_temp_remote_branch")
    @patch("pkg_resources.get_distribution")
    @patch("colony.shell.get_connection_params")
    @patch("colony.branch_utils.examine_blueprint_working_branch")
    def test_blueprint_validate_uncommitted_untracked(
        self,
        examine_blueprint_working_branch,
        get_connection_params,
        pkg_resources_get_distribution,
        delete_temp_remote_branch,
        bp_validate,
        create_remote_branch,
        is_current_state_synced_with_remote,
    ):
        # Arrange
        # need to be tested with True as well
        is_current_state_synced_with_remote.return_value = False
        bp_validate.return_value = Mock(errors="")
        current_branch = self._repo.active_branch.name

        # manipulate files/git state to set up current test case
        self._achieve_dirty_and_untracked_repo()

        # Act
        sys.argv[1:] = ["--debug", "bp", "validate", "test2"]
        shell.main()

        # Assert

        # Can`t check is_current_state_synced_with_remote as it is mocked

        # Check state is dirty+untracked
        # Check that the actual files are the reason for the state (dirty.txt untracked.txt)
        self.assertEqual(len(self._repo.untracked_files), 1)
        self.assertTrue(self._repo.untracked_files[0], "untracked.txt")
        changed_files_list = self._repo.git.diff("HEAD", name_only=True).split("\n")
        self.assertEqual(len(changed_files_list), 1)
        self.assertTrue(changed_files_list[0], "dirty.txt")

        # Check local temp branch was deleted
        for branch in self._repo.branches:
            self.assertFalse(branch.name.startswith(UNCOMMITTED_BRANCH_NAME))

        # Check branch reverted to original
        self.assertEqual(self._repo.active_branch.name, current_branch)

        return

    def _create_clean_repo(self):
        self._repo = git.Repo.init()
        self._repo.config_writer().set_value("user", "name", "test").release()
        self._repo.config_writer().set_value("user", "email", "test@test.io").release()
        with open("clean.txt", "w") as fp:
            fp.close()
            pass
        self._repo.git.add(".")
        self._repo.git.commit("-m", "Initial commit")

    def _achieve_dirty_and_untracked_repo(self):
        self._make_repo_dirty()
        self._add_untracked()

    def _make_repo_dirty(self):
        os.chdir(self._repo.working_dir)
        with open("dirty.txt", "w") as fp:
            fp.close()
            pass
        self._repo.git.add("dirty.txt")

    def _add_untracked(self):
        os.chdir(self._repo.working_dir)
        with open("untracked.txt", "w") as fp:
            fp.close()
            pass


def readonly_handler(func, path, execinfo):
    os.chmod(path, stat.S_IWRITE)
    func(path)
