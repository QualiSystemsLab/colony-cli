import logging
import os

import yaml
from git import InvalidGitRepositoryError, Repo

from colony.exceptions import BadBlueprintRepo

logging.getLogger("git").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


class BlueprintRepo(Repo):
    bp_file_extensions = [".yaml", ".yml"]
    bp_dir = "blueprints"
    _active_branch = ""
    _temp_branch = ""

    def __init__(self, path: str):
        try:
            super().__init__(path, search_parent_directories=True)
        except InvalidGitRepositoryError:
            raise BadBlueprintRepo("Not a git folder")
        if self.bare:
            raise BadBlueprintRepo("Cannot get folder tree structure. Repo is bare")

        self.blueprints = self._fetch_blueprints_list()

    def repo_has_blueprint(self, blueprint_name) -> bool:
        """Check if repo contains provided blueprint"""
        return blueprint_name in list(self.blueprints.keys())

    def is_repo_detached(self):
        return self.head.is_detached

    def current_branch_exists_on_remote(self) -> bool:
        try:
            local_branch_name = self.active_branch.name
            remote_branches = self._get_remote_branches_names()
            return local_branch_name in remote_branches
        except Exception as e:
            logger.error(f"Failed to get remote branches names: {str(e)}")
            return False

    def is_current_branch_synced(self) -> bool:
        """Check if last commit in local and remote branch is the same"""
        local_branch = self.active_branch
        for remote in self.remote().refs:
            if local_branch.name == remote.remote_head:
                return local_branch.commit.__eq__(remote.commit)
        return False

    # (TODO:ddovbii): must be moved to separated class (BlueprintYamlHandler or smth)
    def get_blueprint_artifacts(self, blueprint_name: str) -> dict:
        yaml_obj = self.get_blueprint_yaml(blueprint_name)
        artifacts = yaml_obj.get("artifacts", None)

        if not artifacts:
            return {}

        else:
            res = {}
            for art in artifacts:
                for name, path in art.items():
                    if path:
                        res[name] = path
            return res

    # (TODO:ddovbii): must be moved to separated class (BlueprintYamlHandler or smth)
    def get_blueprint_default_inputs(self, blueprint_name):
        yaml_obj = self.get_blueprint_yaml(blueprint_name)
        inputs = yaml_obj.get("inputs", None)
        if not inputs:
            return {}
        else:
            res = {}
            for inp in inputs:
                for input_name, specs in inp.items():
                    if specs is not None:
                        if not isinstance(specs, dict):
                            res[input_name] = specs
                        else:
                            res[input_name] = specs.get("default_value", None)
            return res

    def get_blueprint_yaml(self, blueprint_name: str) -> dict:
        if not self.repo_has_blueprint(blueprint_name):
            raise BadBlueprintRepo(f"Blueprint Git repo does not contain blueprint {blueprint_name}")

        with open(self.blueprints[blueprint_name]) as bp_file:
            yaml_obj = yaml.full_load(bp_file)

        return yaml_obj

    def _fetch_blueprints_list(self) -> dict:
        bps = {}
        work_dir = self.working_dir
        bp_dir = os.path.join(work_dir, self.bp_dir)

        if not os.path.exists(bp_dir):
            raise BadBlueprintRepo("Repo doesn't have 'blueprints' dir")

        for bp_file in os.listdir(bp_dir):
            blueprint, extension = os.path.splitext(bp_file)
            if extension in self.bp_file_extensions:
                bps[blueprint] = os.path.abspath(os.path.join(bp_dir, bp_file))

        return bps

    def _get_remote_branches_names(self):
        return [ref.remote_head for ref in self.remote().refs]

    def get_active_branch(self) -> str:
        return self._active_branch

    def set_active_branch(self, branch_name: str) -> None:
        self._active_branch = branch_name
        return

    def get_temp_branch(self) -> str:
        return self._temp_branch

    def set_temp_branch(self, branch_name: str) -> None:
        self._temp_branch = branch_name
        return

    def is_current_state_synced_with_remote(self) -> bool:
        # is_dirty() -> means there is *uncommitted* delta for tracked files between local and remote
        # untracked_files -> means there is a delta which are the untracked files (uncommitted)
        # is_current_branch_synced() -> means thoug current state *committed* there is a delta between local and remote
        return not (self.is_dirty() or self.untracked_files or not self.is_current_branch_synced())


def parse_comma_separated_string(params_string: str = None) -> dict:
    res = {}

    if not params_string:
        return res

    key_values = params_string.split(",")

    for item in key_values:
        parts = item.split("=")
        if len(parts) != 2:
            raise ValueError("Line must be comma-separated list of key=values: key1=val1, key2=val2...")

        key = parts[0].strip()
        val = parts[1].strip()

        res[key] = val

    return res
