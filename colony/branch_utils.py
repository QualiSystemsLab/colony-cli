import datetime
import logging
import os
import random
import string
import time

from yaspin import yaspin

from colony.commands.base import BaseCommand
from colony.constants import FINAL_SB_STATUSES, TIMEOUT, UNCOMMITTED_BRANCH_NAME
from colony.exceptions import BadBlueprintRepo
from colony.sandboxes import SandboxesManager
from colony.utils import BlueprintRepo

logging.getLogger("git").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def examine_blueprint_working_branch(repo: BlueprintRepo, blueprint_name: str) -> None:
    if repo.is_repo_detached():
        raise BadBlueprintRepo("Repo's HEAD is in detached state")

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
    return


def get_blueprint_working_branch(repo: BlueprintRepo) -> str:
    branch = repo.active_branch.name
    logger.debug(f"Current working branch is '{branch}'")

    return branch


def figure_out_branches(user_defined_branch: str, blueprint_name: str):
    temp_working_branch = ""
    repo = None
    stashed_flag = False
    success = True
    if user_defined_branch:
        working_branch = user_defined_branch
    else:
        # Try to detect branch from current git-enabled folder
        logger.debug("Branch hasn't been specified. Trying to identify branch from current working directory")
        try:
            repo = BlueprintRepo(os.getcwd())
            examine_blueprint_working_branch(repo, blueprint_name=blueprint_name)
            working_branch = get_blueprint_working_branch(repo)
            BaseCommand.fyi_info(f"Automatically detected current working branch: {working_branch}")

        except Exception as e:
            working_branch = None
            logger.error(f"Branch could not be identified/used from the working directory; reason: {e}.")
            success = False

        # Checking if:
        # 1) User has specified not use local (specified a branch)
        # 2) User is in an actual git dir (working_branch)
        # 3) There is even a need to create a temp branch for out-of-sync reasons:
        #   either repo.is_dirty() (changes have not been committed locally)
        #   or not repo.is_current_branch_synced() (changes committed locally but not pushed to remote)
        if not user_defined_branch and working_branch and not repo.is_current_state_synced_with_remote():
            try:
                temp_working_branch, stashed_flag = switch_to_temp_branch(repo, working_branch)
                BaseCommand.info(
                    "Using your local blueprint changes (including uncommitted changes and/or untracked files)"
                )
                logger.debug(
                    f"Using temp branch: {temp_working_branch} "
                    f"(This shall include any uncommitted changes but and/or untracked files)"
                )
            except Exception as e:
                logger.error(f"Was not able push your latest changes to temp branch for validation. Reason: {str(e)}")
                success = False

    return repo, working_branch, temp_working_branch, stashed_flag, success


def switch_to_temp_branch(repo: BlueprintRepo, defined_branch_in_file: str):
    stashed_flag = False
    created_remote_flag = False
    created_local_temp_branch = False
    random_suffix = "".join(random.choice(string.ascii_lowercase) for i in range(10))
    uncommitted_branch_name = UNCOMMITTED_BRANCH_NAME + defined_branch_in_file + "-" + random_suffix
    try:
        # todo return id and use it for revert_from_temp_branch
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
        if created_local_temp_branch:
            if created_remote_flag:
                revert_and_delete_temp_branch(repo, defined_branch_in_file, uncommitted_branch_name, stashed_flag)
            else:
                revert_from_temp_branch(repo, defined_branch_in_file, stashed_flag)
        raise

    return uncommitted_branch_name, stashed_flag


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


def stash_local_changes(repo: BlueprintRepo):
    logger.debug("[GIT] Stash(Push --include-untracked)")
    repo.git.stash("push", "--include-untracked")


def preserve_uncommitted_code(repo: BlueprintRepo) -> None:
    logger.debug("[GIT] Stash(APPLY)")
    repo.git.stash("apply")


def revert_from_temp_branch(repo: BlueprintRepo, active_branch: str, stashed_flag: bool) -> None:
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


def delete_temp_branch(repo: BlueprintRepo, temp_branch: str) -> None:
    try:
        delete_temp_local_branch(repo, temp_branch)
        delete_temp_remote_branch(repo, temp_branch)
    except Exception as e:
        raise e


def delete_temp_local_branch(repo: BlueprintRepo, temp_branch: str) -> None:
    logger.debug(f"[GIT] Deleting local branch {temp_branch}")
    repo.delete_head("-D", temp_branch)
    # local_branches_names = [h.name for h in repo.heads]


def delete_temp_remote_branch(repo: BlueprintRepo, temp_branch: str) -> None:
    logger.debug(f"[GIT] Deleting remote branch {temp_branch}")
    repo.git.push("origin", "--delete", temp_branch)
    # remote_branches_names = [h.name for h in repo.remote().refs]


def wait_and_delete_temp_branch(
    sb_manager: SandboxesManager, sandbox_id: str, repo: BlueprintRepo, temp_branch: str, blueprint_name: str
) -> None:
    try:
        k8s_blueprint = is_k8s_blueprint(blueprint_name, repo)
        start_time = datetime.datetime.now()
        sandbox = sb_manager.get(sandbox_id)
        status = getattr(sandbox, "sandbox_status")
        progress = getattr(sandbox, "launching_progress")
        prep_art_status = progress.get("preparing_artifacts").get("status")
        deploy_app_status = progress.get("deploying_applications").get("status")
        logger.debug(
            "Waiting for sandbox (id={}) to be provisioned (before deleting temp branch)...".format(sandbox_id)
        )

        BaseCommand.info("Waiting for the Sandbox to start with local changes. This may take some time.")
        BaseCommand.fyi_info("Canceling or exiting before the process completes may cause the sandbox to fail")

        with yaspin(text="Starting...", color="yellow") as spinner:
            while (datetime.datetime.now() - start_time).seconds < TIMEOUT * 60:
                if (
                    status in FINAL_SB_STATUSES
                    or prep_art_status != "Pending"
                    and not k8s_blueprint
                    or k8s_blueprint
                    and deploy_app_status != "Pending"
                ):
                    spinner.green.ok("✔")
                    delete_temp_branch(repo, temp_branch)
                    break

                time.sleep(10)
                spinner.text = f"[{int((datetime.datetime.now() - start_time).total_seconds())} sec]"
                sandbox = sb_manager.get(sandbox_id)
                status = getattr(sandbox, "sandbox_status")
                progress = getattr(sandbox, "launching_progress")
                prep_art_status = progress.get("preparing_artifacts").get("status")
                deploy_app_status = progress.get("deploying_applications").get("status")
    except Exception as e:
        logger.error(f"There was an issue with waiting for sandbox deployment -> {str(e)}")
        delete_temp_branch(repo, temp_branch)


def is_k8s_blueprint(blueprint_name, repo) -> bool:
    k8s_sandbox_flag = False
    yaml_obj = repo.get_blueprint_yaml(blueprint_name)
    for cloud in yaml_obj["clouds"]:
        if "/" in cloud:
            k8s_sandbox_flag = True
    return k8s_sandbox_flag


def checkout_remote_branch(repo: BlueprintRepo, active_branch: str):
    logger.debug(f"[GIT] Checking out {active_branch}")
    repo.git.checkout(active_branch)


def revert_and_delete_temp_branch(
    repo: BlueprintRepo, working_branch: str, temp_working_branch: str, stashed_flag: bool
) -> None:
    if temp_working_branch.startswith(UNCOMMITTED_BRANCH_NAME):
        revert_from_temp_branch(repo, working_branch, stashed_flag)
        delete_temp_branch(repo, temp_working_branch)
