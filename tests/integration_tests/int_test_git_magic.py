import unittest
from unittest.mock import MagicMock, patch


class GitMagicTests(unittest.TestCase):

    def setUp(self) -> None:
        # setup testing env
        # -> copy base_repo to temp folder
        # -> do git init on temp folder
        # -> set working directory to temp folder
        # -> git remote => mock/patch => git pull, git push, remote sync test (mock here or on class level)
        #                             => colony API calls
        pass

    def tearDown(self) -> None:
        # delete temp folder
        pass

    def test_blueprint_validate_when_uncommited_changes(self):

        # manipulate files/git state to set up current test case

        # act
        # method_under_test()

        return