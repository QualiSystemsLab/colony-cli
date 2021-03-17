import os
import shutil
import unittest
import logging
from unittest.mock import MagicMock, patch

logging.getLogger("git").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

class GitMagicTests(unittest.TestCase):

    def setUp(self) -> None:
        # setup testing env
        # -> copy base_repo to temp folder
        try:
            os.chdir(f"tests{os.sep}integration_tests")
            # os.mkdir("test_repo_temp")
            src = f"{os.getcwd()}{os.sep}test_repo_gold"
            dst = f"{os.getcwd()}{os.sep}test_repo_temp"
            shutil.copytree(src, dst)
        except Exception as e:
            logger.warning(f"Was not able to create create a temp local dir. Reason: {str(e)}")


        print(os.getcwd())
        # -> do git init on temp folder
        # -> set working directory to temp folder
        # -> git remote => mock/patch => git pull, git push, remote sync test (mock here or on class level)
        #                             => colony API calls
        pass

    def tearDown(self) -> None:
        # delete temp folder
        pass

    def test_blueprint_validate_when_uncommitted_changes(self):

        # manipulate files/git state to set up current test case

        # act
        # method_under_test()

        return