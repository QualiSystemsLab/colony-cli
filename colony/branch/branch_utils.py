import logging
import os
import random
import string

from colony.commands.base import BaseCommand
from colony.constants import DONE_STATUS, UNCOMMITTED_BRANCH_NAME
from colony.exceptions import BadBlueprintRepo
from colony.sandboxes import Sandbox
from colony.utils import BlueprintRepo

logging.getLogger("git").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def debug_output_about_repo_examination(repo: BlueprintRepo, blueprint_name: str):
    if not repo.repo_has_blueprint(blueprint_name):
        logger.debug(f"Current repo does not contain a definition for the blueprint '{blueprint_name}'.")
    if repo.is_dirty():
        logger.debug("You have uncommitted changes")
    if repo.untracked_files:
        logger.debug(
            "Untracked files detected - only staged or committed files will be used when testing local changes"
        )
    if not repo.current_branch_exists_on_remote():
        logger.debug("Your current local branch doesn't exist on remote")
        # raise BadBlueprintRepo("Your current local branch doesn't exist on remote")
    if not repo.is_current_branch_synced():
        logger.debug("Your local branch is not synced with remote")


def check_repo_for_errors(repo: BlueprintRepo) -> None:
    if repo.is_repo_detached():
        logger.error("Repo's HEAD is in detached state")
        raise BadBlueprintRepo("Repo's HEAD is in detached state")


def get_blueprint_working_branch(repo: BlueprintRepo) -> str:
    working_branch = repo.active_branch.name
    BaseCommand.fyi_info(f"Automatically detected current working branch: {working_branch}")
    logger.debug(f"Current working branch is '{working_branch}'")

    return working_branch


def create_temp_branch_and_stash_if_needed(repo: BlueprintRepo, working_branch: str) -> str:
    temp_working_branch = ""
    # Checking if:
    # 1) User has specified not use local (specified a branch) (This func is only called if not specified)
    # 2) User is in an actual git dir (working_branch)
    # 3) There is even a need to create a temp branch for out-of-sync reasons:
    #   either repo.is_dirty() (changes have not been committed locally)
    #   or not repo.is_current_branch_synced() (changes committed locally but not pushed to remote)

    if working_branch and not repo.is_current_state_synced_with_remote():
        try:
            temp_working_branch = switch_to_temp_branch(repo, working_branch)
            BaseCommand.info(
                "Using your local blueprint changes (including uncommitted changes and/or untracked files)"
            )
            logger.debug(
                f"Using temp branch: {temp_working_branch} "
                f"(This shall include any uncommitted changes and/or untracked files)"
            )
        except Exception as e:
            logger.error(f"Was not able push your latest changes to temp branch for validation. Reason: {str(e)}")
    return temp_working_branch


def get_and_check_folder_based_repo(blueprint_name: str) -> BlueprintRepo:
    # Try to detect branch from current git-enabled folder
    logger.debug("Branch hasn't been specified. Trying to identify branch from current working directory")
    try:
        repo = BlueprintRepo(os.getcwd())
        check_repo_for_errors(repo)
        debug_output_about_repo_examination(repo, blueprint_name)
    except Exception as e:
        logger.error(f"Branch could not be identified/used from the working directory; reason: {e}.")
        raise
    return repo


def switch_to_temp_branch(repo: BlueprintRepo, defined_branch_in_file: str):
    stashed_flag = False
    created_remote_flag = False
    created_local_temp_branch = False
    random_suffix = "".join(random.choice(string.ascii_lowercase) for i in range(10))
    uncommitted_branch_name = UNCOMMITTED_BRANCH_NAME + defined_branch_in_file + "-" + random_suffix
    stashed_items_before = count_stashed_items(repo)
    try:
        if repo.is_dirty() or repo.untracked_files:
            create_gitkeep_in_branch()
            stash_local_changes(repo)
            stashed_flag = True
        created_local_temp_branch = create_local_temp_branch(repo, uncommitted_branch_name)
        if stashed_flag:
            preserve_uncommitted_code(repo)
            commit_to_local_temp_branch(repo)
        create_remote_branch(repo, uncommitted_branch_name)
        created_remote_flag = True
    except Exception as e:
        logger.debug(f"An issue while creating temp branch: {str(e)}")
        if not stashed_flag and (count_stashed_items(repo) > stashed_items_before):
            revert_from_uncommitted_code(repo)
        if created_local_temp_branch:
            revert_from_local_temp_branch(repo, defined_branch_in_file, stashed_flag)
            delete_temp_local_branch(repo, defined_branch_in_file)
        if created_remote_flag:
            delete_temp_remote_branch(repo, defined_branch_in_file)
        raise

    return uncommitted_branch_name


def create_gitkeep_in_branch() -> None:
    for currentpath, folders, files in os.walk(os.getcwd()):
        if ".git" not in currentpath and not files:
            with open(os.path.join(currentpath, ".colonygitkeep"), "w"):
                pass


def remove_gitkeep_in_branch() -> None:
    files_to_delete = []
    for currentpath, folders, files in os.walk(os.getcwd()):
        if (os.sep + ".git") not in currentpath and ".colonygitkeep" in files:
            files_to_delete.append(os.path.join(currentpath, ".colonygitkeep"))
    for file in files_to_delete:
        os.remove(file)


def create_remote_branch(repo: BlueprintRepo, uncommitted_branch_name: str) -> None:
    logger.debug(f"[GIT] Push (origin) {uncommitted_branch_name}")
    repo.git.push("origin", uncommitted_branch_name)


def create_local_temp_branch(repo: BlueprintRepo, uncommitted_branch_name: str) -> bool:
    logger.debug(f"[GIT] Checkout (-b) {uncommitted_branch_name}")
    repo.git.checkout("-b", uncommitted_branch_name)
    return True


def commit_to_local_temp_branch(repo: BlueprintRepo) -> None:
    logger.debug("[GIT] Add (.)")
    repo.git.add(".")
    logger.debug("[GIT] Commit")
    repo.git.commit("-m", "Uncommitted temp branch - temp commit for validation")


def count_stashed_items(repo: BlueprintRepo) -> int:
    if repo:
        logger.info("[GIT] Stash(list)")
        stash_list = repo.git.stash("list")
        return stash_list.count("stash@")
    else:
        return 0


def stash_local_changes(repo: BlueprintRepo):
    logger.debug("[GIT] Stash(Push --include-untracked)")
    repo.git.stash("push", "--include-untracked")


def preserve_uncommitted_code(repo: BlueprintRepo) -> None:
    logger.debug("[GIT] Stash(APPLY)")
    repo.git.stash("apply")


def revert_from_local_temp_branch(repo: BlueprintRepo, active_branch: str, stashed_flag: bool) -> None:
    try:
        checkout_remote_branch(repo, active_branch)
        if stashed_flag:
            revert_from_uncommitted_code(repo)
    except Exception as e:
        raise e


def revert_from_uncommitted_code(repo: BlueprintRepo) -> None:
    logger.debug("[GIT] Stash(POP)")
    repo.git.stash("pop", "--index")
    remove_gitkeep_in_branch()


def delete_temp_local_branch(repo: BlueprintRepo, temp_branch: str) -> None:
    logger.debug(f"[GIT] Deleting local branch {temp_branch}")
    repo.delete_head("-D", temp_branch)


def delete_temp_remote_branch(repo: BlueprintRepo, temp_branch: str) -> None:
    logger.debug(f"[GIT] Deleting remote branch {temp_branch}")
    repo.git.push("origin", "--delete", temp_branch)


def is_k8s_blueprint(blueprint_name: str, repo: BlueprintRepo) -> bool:
    k8s_sandbox_flag = False
    yaml_obj = repo.get_blueprint_yaml(blueprint_name)
    for cloud in yaml_obj["clouds"]:
        if "/" in cloud:
            k8s_sandbox_flag = True
    return k8s_sandbox_flag


def is_tf_blueprint(blueprint_name: str, repo: BlueprintRepo) -> bool:
    tf_sandbox_flag = False
    yaml_obj = repo.get_blueprint_yaml(blueprint_name)
    if "services" in yaml_obj.keys():
        if len(yaml_obj["services"]):
            tf_sandbox_flag = True
    return tf_sandbox_flag


def checkout_remote_branch(repo: BlueprintRepo, active_branch: str) -> None:
    logger.debug(f"[GIT] Checking out {active_branch}")
    repo.git.checkout(active_branch)


def can_temp_branch_be_deleted(sandbox: Sandbox) -> bool:
    progress = getattr(sandbox, "launching_progress")
    prep_artifacts_status = progress.get("preparing_artifacts").get("status")
    creating_infra_status = progress.get("creating_infrastructure").get("status")

    return prep_artifacts_status == DONE_STATUS and creating_infra_status == DONE_STATUS
