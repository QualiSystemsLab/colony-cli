import os

from typing import List

from colony.exceptions import BadBlueprintRepo
from git import Repo, InvalidGitRepositoryError


class BlueprintRepo(Repo):
    bp_file_extensions = [".yaml", ".yml"]
    bp_dir = "blueprints"

    def __init__(self, path: str):
        try:
            super().__init__(path)
        except InvalidGitRepositoryError:
            raise BadBlueprintRepo("Not a git folder")
        if self.bare:
            raise BadBlueprintRepo("Cannot get working directory. Repo is bare")

        self.blueprints = self._fetch_blueprints_list()

    def repo_has_blueprint(self, blueprint_name) -> bool:
        """Check if repo contains provided blueprint"""
        return blueprint_name in self.blueprints

    def is_repo_detached(self):
        return self.head.is_detached

    def current_branch_exists_on_remote(self) -> bool:
        local_branch_name = self.active_branch.name
        remote_branches = self._get_remote_branches_names()

        return local_branch_name in remote_branches

    def is_current_branch_synced(self) -> bool:
        """Check if last commit in local and remote branch is the same"""
        local_branch = self.active_branch
        for remote in self.remote().refs:
            if local_branch.name == remote.remote_head:
                return local_branch.__eq__(remote.commit)

    def _fetch_blueprints_list(self) -> List[str]:
        bps = []
        work_dir = self.working_dir
        bp_dir = os.path.join(work_dir, self.bp_dir)

        if not os.path.exists(bp_dir):
            raise BadBlueprintRepo("Repo doesn't have 'blueprints' dir")

        for bp_file in os.listdir(bp_dir):
            blueprint, extension = os.path.splitext(bp_file)
            if extension in self.bp_file_extensions:
                bps.append(blueprint)

        return bps

    def _get_remote_branches_names(self):
        return [ref.remote_head for ref in self.remote().refs]



def get_blueprint_branch(path: str = None):
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

#
# path = "/mnt/c/Users/ddovbii/jenkins-colony"
#
# a = BlueprintRepo(path)
# print(a.current_branch_exists_on_remote())
#
# print(a.blueprints)
