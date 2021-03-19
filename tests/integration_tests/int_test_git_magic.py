import os
import shutil
import sys
import tempfile
import unittest
import logging
import git
from unittest.mock import MagicMock, patch

from colony.utils import BlueprintRepo
from colony import shell

logging.getLogger("git").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


class GitMagicTests(unittest.TestCase):
    @property
    def repo(self):
        return self._repo

    @property
    def cwd(self):
        return self._cwd

    def setUp(self) -> None:
        self._repo = None
        self._cwd = os.getcwd()
        # setup testing env
        # -> copy base_repo to temp folder
        try:
            dst = tempfile.mkdtemp()
            # -> set working directory to temp folder
            os.chdir(f"{dst}")
            os.mkdir("blueprints")
            print(dst)
            # -> do git init on temp folder
            self._repo = git.Repo.init()
        except Exception as e:
            logger.warning(f"Was not able to create a temp local dir with repo. Reason: {str(e)}")

        # -> git remote => mock/patch => git pull, git push, remote sync test (mock here or on class level)
        #                             => colony API calls
        pass

    def tearDown(self) -> None:
        # delete temp folder
        try:
            os.chdir(self._cwd)
            shutil.rmtree(self._repo.working_dir)
        except Exception as e:
            logger.warning(f"Was not able to delete a temp local dir with repo. Reason: {str(e)}")
        pass

    def test_blueprint_validate_when_uncommitted_changes(self):
        # manipulate files/git state to set up current test case
        self._create_dirty_no_untracked()

        # act
        try:
            sys.argv[1:] = ['--debug', 'bp', 'validate', 'test2']
            shell.main()
        except Exception as e:
            print(str(e))
        # method_under_test()

        return

    def _create_dirty_and_untracked(self):
        try:
            self._create_dirty_no_untracked()
            self._add_untracked()
        except Exception as e:
            logger.warning(f"Was not able to create a dirty repo with untracked... Reason: {str(e)}")

    def _create_dirty_no_untracked(self):
        try:
            os.chdir(self._repo.working_dir)
            with open('test.txt', 'w') as fp:
                pass
            self.repo.git.add("test.txt")
        except Exception as e:
            logger.warning(f"Was not able to create a dirty repo ... Reason: {str(e)}")

    def _add_untracked(self):
        try:
            os.chdir(self._repo.working_dir)
            with open('untracked.txt', 'w') as fp:
                pass
        except Exception as e:
            logger.warning(f"Was not able to create an untracked file ... Reason: {str(e)}")
