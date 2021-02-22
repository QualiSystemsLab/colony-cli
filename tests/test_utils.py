import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, call

from git import Actor, Repo

from colony import utils
from colony.exceptions import BadBlueprintRepo
from colony.utils import BlueprintRepo, UNCOMMITTED_BRANCH_NAME


class TestParseParamString(unittest.TestCase):
    def setUp(self):
        self.parse_fun = utils.parse_comma_separated_string

    def test_is_result_dict(self):
        line = None
        result = self.parse_fun(line)
        self.assertIsInstance(result, dict)

    def test_return_empty_dict(self):
        line = None
        result = self.parse_fun(line)
        self.assertDictEqual(result, {})

    def test_trailing_spaces(self):
        line = " key1 =val1,key2 = val2"
        expected = {"key1": "val1", "key2": "val2"}
        result = self.parse_fun(line)
        self.assertDictEqual(result, expected)

    def test_raise_exception_on_space_del(self):
        line = "key1=val1 key2=val2"
        with self.assertRaises(ValueError):
            self.parse_fun(line)

    def test_raise_exception_on_colon(self):
        line = "key1:val1, key2:val2"
        with self.assertRaises(ValueError):
            self.parse_fun(line)


class TestBlueprintRepo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super(TestBlueprintRepo, cls).setUpClass()
        cls.git_repo_url = "https://github.com/QualiSystemsLab/colony-demo-space.git"

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        Repo.clone_from(self.git_repo_url, self.test_dir)
        self.bp_repo = BlueprintRepo(self.test_dir)

    def test_blueprint_repo_has_blueprints(self):
        bp_list = self.bp_repo.blueprints
        self.assertTrue(len(bp_list))

    def test_has_non_existing_blueprint(self):
        fake_bp = "MyTestBp"
        self.assertFalse(self.bp_repo.repo_has_blueprint(fake_bp))

    def test_has_blueprint(self):
        bp_name = "promotions-manager-all-aws"
        self.assertTrue(self.bp_repo.repo_has_blueprint(bp_name))

    def test_create_repo_from_non_git_dir(self):
        with tempfile.TemporaryDirectory() as wrong_dir:
            self.assertRaises(BadBlueprintRepo, BlueprintRepo, wrong_dir)

    def test_raise_on_bare_repo(self):
        with tempfile.TemporaryDirectory() as wrong_dir:
            Repo.init(wrong_dir, bare=True)
            self.assertRaises(BadBlueprintRepo, BlueprintRepo, wrong_dir)

    def test_has_remote_branch(self):
        self.assertTrue(self.bp_repo.current_branch_exists_on_remote())

    def test_no_branch_on_remote(self):
        local_branch = "my_super_branch"
        current = self.bp_repo.create_head(local_branch)
        current.checkout()
        self.assertFalse(self.bp_repo.current_branch_exists_on_remote())

    def test_is_synced(self):
        self.assertTrue(self.bp_repo.is_current_branch_synced())

    def test_repo_not_synced(self):
        index = self.bp_repo.index

        new_file_path = os.path.join(self.test_dir, "new-file-name")
        open(new_file_path, "w").close()
        index.add([new_file_path])

        author = Actor("An author", "author@example.com")
        committer = Actor("A committer", "committer@example.com")

        index.commit("my commit message", author=author, committer=committer)
        self.assertFalse(self.bp_repo.is_current_branch_synced())

    def tearDown(self):
        # Close the file, the directory will be removed after the test
        shutil.rmtree(self.test_dir)

class TestStashLogicFunctions(unittest.TestCase):
    def setUp(self):
        self.switch = utils.switch_to_temp_branch
        self.revert = utils.revert_from_temp_branch

    def test_switch_to_temp_branch(self):
        # Arrange:
        mock_repo = MagicMock()
        defined_branch_in_file = "abc"
        # Act:
        uncommitted_branch_name = self.switch(mock_repo,defined_branch_in_file)
        # Assert:
        mock_repo.git.stash.assert_has_calls([call('save'),call('apply')])
        mock_repo.git.checkout.assert_called_once()
        mock_repo.git.add.assert_called_once()
        mock_repo.git.commit.assert_called_once()
        mock_repo.git.push.assert_called_once_with("origin",uncommitted_branch_name)
        self.assertTrue(uncommitted_branch_name.startswith(UNCOMMITTED_BRANCH_NAME))

    def test_revert_from_temp_branch(self):
        # Arrange:
        mock_repo = MagicMock()
        temp_branch = "temp_branch"
        active_branch = "active_branch"
        # Act:
        self.revert(mock_repo,temp_branch,active_branch)
        # Assert:
        mock_repo.git.checkout.assert_called_once_with(active_branch)
        mock_repo.git.push.assert_called_once_with("origin", "--delete", temp_branch)
        mock_repo.delete_head.assert_called_once_with("-D", temp_branch)
        mock_repo.git.stash.assert_called_once_with('pop')

if __name__ == "__main__":
    unittest.main()
