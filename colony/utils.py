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
        return blueprint_name in list(self.blueprints.keys())

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
                return local_branch.commit.__eq__(remote.commit)
        return False

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

    def get_blueprint_default_inputs(self, blueprint_name):
        yaml_obj = self.get_blueprint_yaml(blueprint_name)
        inputs = yaml_obj.get("inputs", None)
        if not inputs:
            return {}
        else:
            res = {}
            for inp in inputs:
                for input_name, specs in inp.items():
                    if specs:
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


def get_working_branch() -> str:
    logger.debug("Branch hasn't been specified. " "Trying to identify branch from current working directory")
    branch = None

    try:
        repo = BlueprintRepo(os.getcwd())
        if repo.is_repo_detached():
            raise BadBlueprintRepo("Repo's HEAD is in detached state")

        branch = repo.active_branch.name
        logger.debug(f"Current working branch is '{branch}'")

        if repo.is_dirty():
            logger.warning("You have uncommitted changes")

        if not repo.current_branch_exists_on_remote():
            raise BadBlueprintRepo("Your current local branch doesn't exist on remote")

        if not repo.is_current_branch_synced():
            logger.warning("Your local branch is not synced with remote")

    except BadBlueprintRepo as e:
        logger.debug(f"Unable to recognize current directory as a proper colony blueprints git repo. " f"Details: {e}")
    finally:
        if not branch:
            logger.warning(
                "No branch has been specified and it couldn't be identified. "
                "Blueprint branch attached to Colony will be used. "
                "Use `--debug` flag to find details "
            )

    return branch


def parse_comma_separated_string(params_string: str = None) -> dict:
    res = {}

    if not params_string:
        return res

    key_vals = params_string.split(",")

    for item in key_vals:
        parts = item.split("=")
        key = parts[0].strip()
        val = parts[1].strip()
        res[key] = val

    return res
