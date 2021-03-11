import datetime
import logging
import os
import random
import string
import time

from colony.commands.base import BaseCommand
from colony.constants import FINAL_SB_STATUSES, TIMEOUT, UNCOMMITTED_BRANCH_NAME
from colony.exceptions import BadBlueprintRepo
from colony.sandboxes import SandboxesManager
from colony.utils import BlueprintRepo

logging.getLogger("git").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def examine_blueprint_working_branch(repo: BlueprintRepo, blueprint_name: str):
    if repo.is_repo_detached():
        raise BadBlueprintRepo("Repo's HEAD is in detached state")

    if not repo.repo_has_blueprint(blueprint_name):
        logger.warning(f"Current repo does not contain a definition for the blueprint '{blueprint_name}'.")

    if repo.is_dirty():
        logger.warning("You have uncommitted changes")

    if not repo.current_branch_exists_on_remote():
        logger.warning("Your current local branch doesn't exist on remote")
        # raise BadBlueprintRepo("Your current local branch doesn't exist on remote")

    if not repo.is_current_branch_synced():
        logger.warning("Your local branch is not synced with remote")
    return


def get_blueprint_working_branch(repo: BlueprintRepo) -> str:

    branch = repo.active_branch.name
    logger.debug(f"Current working branch is '{branch}'")

    return branch


def set_blueprint_working_temp_branch(repo: BlueprintRepo, defined_branch_in_file: str) -> str:
    temp_branch = defined_branch_in_file

    try:
        temp_branch = switch_to_temp_branch(repo, defined_branch_in_file)
    except Exception as e:
        logger.error(f"Was not able to create temp branch for validation - {str(e)}")

    return temp_branch


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
            examine_blueprint_working_branch(repo, blueprint_name=blueprint_name)
            working_branch = get_blueprint_working_branch(repo)
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
                    f"Using temp branch: {temp_working_branch} "
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
    logger.debug(f"[GIT] Push (origin) {uncommitted_branch_name}")
    repo.git.push("origin", uncommitted_branch_name)


def create_local_branch(repo, uncommitted_branch_name):
    logger.debug("[GIT] Checkout (-b) {uncommitted_branch_name}")
    repo.git.checkout("-b", uncommitted_branch_name)
    logger.debug("[GIT] Add (.)")
    repo.git.add(".")
    logger.debug("[GIT] Commit")
    repo.git.commit("-m", "Uncommitted temp branch - temp commit for validation")


def stash_local_changes_and_preserve_uncommitted_code(repo):
    logger.debug("[GIT] Stash(SAVE --include-untracked)")
    repo.git.stash("save", "--include-untracked")
    # id = id_unparsed.split(": ")[1].split(" U")[0]
    logger.debug("[GIT] Stash(APPLY)")
    repo.git.stash("apply")


def revert_from_temp_branch(repo: BlueprintRepo, active_branch) -> None:
    try:
        checkout_remote_branch(repo, active_branch)
        revert_from_uncommitted_code(repo)
    except Exception as e:
        raise e


def revert_from_uncommitted_code(repo):
    logger.debug("[GIT] Stash(POP)")
    repo.git.stash("pop")


def delete_temp_branch(repo, temp_branch):
    try:
        logger.debug(f"[GIT] Deleting remote branch {temp_branch}")
        repo.git.push("origin", "--delete", temp_branch)
        logger.debug(f"[GIT] Deleting local branch {temp_branch}")
        repo.delete_head("-D", temp_branch)
    except Exception as e:
        raise e


def wait_and_then_delete_branch(sb_manager: SandboxesManager, sandbox_id, repo, temp_branch):
    if not temp_branch:
        return
    start_time = datetime.datetime.now()
    sandbox = sb_manager.get(sandbox_id)
    status = getattr(sandbox, "sandbox_status")
    progress = getattr(sandbox, "launching_progress")
    prep_art_status = progress.get("preparing_artifacts").get("status")
    logger.debug("Waiting for sandbox (id={}) to prepare artifacts (before deleting temp branch)...".format(sandbox_id))

    while (datetime.datetime.now() - start_time).seconds < TIMEOUT * 60:

        if status in FINAL_SB_STATUSES or (status == "Launching" and prep_art_status != "Pending"):
            delete_temp_branch(repo, temp_branch)
            break
        else:
            time.sleep(3)
            logger.debug(
                f"Still waiting for sandbox (id={sandbox_id}) to prepare artifacts..."
                f"[{datetime.datetime.now() - start_time} sec]"
            )
            sandbox = sb_manager.get(sandbox_id)
            status = getattr(sandbox, "sandbox_status")
            progress = getattr(sandbox, "launching_progress")
            prep_art_status = progress.get("preparing_artifacts").get("status")


def checkout_remote_branch(repo, active_branch):
    logger.debug(f"[GIT] Checking out {active_branch}")
    repo.git.checkout(active_branch)
