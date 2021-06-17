import os
import shutil
import tempfile
import unittest

from git import Repo, Actor

from colony.exceptions import BadBlueprintRepo
from colony.utils import BlueprintRepo


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

    def test_raise_on_repo_without_blueprints_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            Repo.init(temp_dir)
            self.assertRaises(BadBlueprintRepo, BlueprintRepo, temp_dir)

    def test_raise_on_repo_without_remotes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            Repo.init(temp_dir)
            os.mkdir(f"{temp_dir}/blueprints")
            self.assertRaises(BadBlueprintRepo, BlueprintRepo, temp_dir)

    def test_has_remote_branch(self):
        self.assertTrue(self.bp_repo.current_branch_exists_on_remote())

    def test_no_branch_on_remote(self):
        local_branch = "my_super_branch"
        new_branch = self.bp_repo.create_head(local_branch)
        assert self.bp_repo.active_branch != new_branch
        new_branch.checkout()
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
