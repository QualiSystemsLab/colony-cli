import os

from git import Repo, InvalidGitRepositoryError

def get_blueprint_branch(path:str = None):
    if path is None:
        path = os.getcwd()
    try:
        repo = Repo(path)
    except InvalidGitRepositoryError:
        return None

    if repo.head.is_detached:
        return None

    local_branch = repo.active_branch.name
    remote_branches = [ref.remote_head for ref in repo.remote().refs]

    if local_branch in remote_branches:
        return local_branch
    else:
        return None
