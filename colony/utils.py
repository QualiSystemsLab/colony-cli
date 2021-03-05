import logging
import os
import random
import string

import yaml
from git import InvalidGitRepositoryError, Repo

from colony.commands.base import BaseCommand
from colony.exceptions import BadBlueprintRepo

logging.getLogger("git").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

UNCOMMITTED_BRANCH_NAME = "tmp-colony-"


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


def get_blueprint_working_branch(repo: BlueprintRepo, blueprint_name: str) -> str:
    if repo.is_repo_detached():
        raise BadBlueprintRepo("Repo's HEAD is in detached state")

    branch = repo.active_branch.name

    if not repo.repo_has_blueprint(blueprint_name):
        logger.warning(f"Current repo does not contain a definition for the blueprint '{blueprint_name}'.")

    logger.debug(f"Current working branch is '{branch}'")

    if repo.is_dirty():
        logger.warning("You have uncommitted changes")

    if not repo.current_branch_exists_on_remote():
        logger.warning("Your current local branch doesn't exist on remote")
        # raise BadBlueprintRepo("Your current local branch doesn't exist on remote")

    if not repo.is_current_branch_synced():
        logger.warning("Your local branch is not synced with remote")

    return branch


def set_blueprint_working_temp_branch(repo: BlueprintRepo, defined_branch_in_file: str) -> str:
    temp_branch = defined_branch_in_file

    try:
        temp_branch = switch_to_temp_branch(repo, defined_branch_in_file)
    except Exception as e:
        logger.error(f"Was not able to create temp branch for validation - {str(e)}")

    return temp_branch


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


def figure_out_branches(user_defined_branch, blueprint_name):
    temp_working_branch = ""
    repo = None
    if user_defined_branch:
        working_branch = user_defined_branch
    else:
        # Try to detect branch from current git-enabled folder
        logger.debug("Branch hasn't been specified. Trying to identify branch from current working directory")
        try:
            repo = BlueprintRepo(os.getcwd())
            working_branch = get_blueprint_working_branch(repo, blueprint_name=blueprint_name)
            BaseCommand.message(f"Automatically detected current working branch: {working_branch}")

        except BadBlueprintRepo as e:
            working_branch = None
            logger.warning(
                f"Branch could not be identified/used from the working directory; "
                f"reason: {e}. A branch of the Blueprints Repository attached to Colony Space will be used"
            )

        # Checking if:
        # 1) User has specified not use local (specified a branch)
        # 2) User is in an actual git dir (working_branch)
        # 3) There is even a need to create a temp branch for out-of-sync reasons:
        #   either repo.is_dirty() (changes have not been committed locally)
        #   or not repo.is_current_branch_synced() (changes committed locally but not pushed to remote)
        if not user_defined_branch and working_branch and not repo.is_current_state_synced_with_remote():
            try:
                temp_working_branch = switch_to_temp_branch(repo, working_branch)
                BaseCommand.message(
                    f"Validating using temp branch: {temp_working_branch} "
                    f"(This shall include any uncommitted changes and untracked files)"
                )
            except Exception as e:
                logger.warning(f"Was not able push your latest changes to temp branch for validation. Reason: {str(e)}")
    return repo, working_branch, temp_working_branch


def switch_to_temp_branch(repo: BlueprintRepo, defined_branch_in_file: str) -> str:
    random_suffix = "".join(random.choice(string.ascii_lowercase) for i in range(10))
    uncommitted_branch_name = UNCOMMITTED_BRANCH_NAME + defined_branch_in_file + "-" + random_suffix
    try:
        # todo return id and use it for revert_from_temp_branch
        stash_local_changes_and_preserve_uncommitted_code(repo)
        create_local_branch(repo, uncommitted_branch_name)
        create_remote_branch(repo, uncommitted_branch_name)
    except Exception as e:
        raise e
    return uncommitted_branch_name


def create_remote_branch(repo, uncommitted_branch_name):
    repo.git.push("origin", uncommitted_branch_name)


def create_local_branch(repo, uncommitted_branch_name):
    repo.git.checkout("-b", uncommitted_branch_name)
    repo.git.add(".")
    repo.git.commit("-m", "Uncommitted temp branch - temp commit for validation")


def stash_local_changes_and_preserve_uncommitted_code(repo):
    repo.git.stash("save", "--include-untracked")
    # id = id_unparsed.split(": ")[1].split(" U")[0]
    repo.git.stash("apply")


def revert_from_temp_branch(repo: BlueprintRepo, temp_branch, active_branch) -> None:
    try:
        checkout_remote_branch(repo, active_branch)
        delete_temp_branch(
            repo,
            temp_branch,
        )
        revert_from_uncommitted_code(repo)
    except Exception as e:
        raise e


def revert_from_uncommitted_code(repo):
    repo.git.stash("pop")


def delete_temp_branch(repo, temp_branch):
    repo.git.push("origin", "--delete", temp_branch)
    repo.delete_head("-D", temp_branch)


def checkout_remote_branch(repo, active_branch):
    repo.git.checkout(active_branch)
