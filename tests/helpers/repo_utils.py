import os
import stat

from git import Repo


def create_clean_repo():
    repo = Repo.init()
    repo.create_remote("origin", "https://github.com/user/repo.git")
    repo.config_writer().set_value("user", "name", "test").release()
    repo.config_writer().set_value("user", "email", "test@test.io").release()
    with open("clean.txt", "w"):
        pass
    repo.git.add(".")
    repo.git.commit("-m", "Initial commit")
    return repo


def achieve_dirty_and_untracked_repo(repo):
    make_repo_dirty(repo)
    add_untracked(repo)


def make_repo_dirty(repo):
    os.chdir(repo.working_dir)
    with open("dirty.txt", "w"):
        pass
    repo.git.add("dirty.txt")


def add_untracked(repo):
    os.chdir(repo.working_dir)
    with open("untracked.txt", "w"):
        pass


def readonly_handler(func, path, execinfo):
    os.chmod(path, stat.S_IWRITE)
    func(path)
