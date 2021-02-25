import logging
import os

import tabulate
from docopt import DocoptExit

from colony.blueprints import BlueprintsManager
from colony.commands.base import BaseCommand
from colony.exceptions import BadBlueprintRepo
from colony.utils import (
    UNCOMMITTED_BRANCH_NAME,
    BlueprintRepo,
    get_blueprint_working_branch,
    revert_from_temp_branch,
    switch_to_temp_branch,
)

logger = logging.getLogger(__name__)


class BlueprintsCommand(BaseCommand):
    """
    usage:
        colony (bp | blueprint) validate <name> [options]
        colony (bp | blueprint) [--help]

    options:
       -b --branch <branch>     Specify the name of remote git branch. If not provided, we will try to automatically
                                detect the current working branch if the command is used in a git enabled folder.

       -c --commit <commitId>   Specify commit ID. It's required to validate a blueprint from an historic commit.
                                Must be used together with the branch option. If not specified then the latest commit
                                will be used.

       -r, --remote             Work with remote branch (default is local branch)

       -h --help                Show this message
    """

    RESOURCE_MANAGER = BlueprintsManager

    def get_actions_table(self) -> dict:
        return {"validate": self.do_validate}

    def do_validate(self):
        name = self.args.get("<name>")
        branch = self.args.get("--branch")
        commit = self.args.get("--commit")
        remote = self.args.get("--remote")

        if commit and branch is None:
            raise DocoptExit("Since commit is specified, branch is required")

        temp_working_branch = ""
        repo = BlueprintRepo(os.getcwd())
        if branch:
            working_branch = branch
        else:
            # Try to detect branch from current git-enabled folder
            logger.debug("Branch hasn't been specified. Trying to identify branch from current working directory")
            try:
                # todo get flag for stash mode
                working_branch = get_blueprint_working_branch(repo, blueprint_name=name)
                self.message(f"Automatically detected current working branch: {working_branch}")
                if not remote:
                    temp_working_branch = working_branch
                    try:
                        temp_working_branch = switch_to_temp_branch(repo, working_branch)
                    except Exception as e:
                        logger.error(f"Was not able to create temp branch for validation - {str(e)}")

            except BadBlueprintRepo as e:
                working_branch = None
                logger.warning(
                    f"No branch has been specified and it could not be identified from the working directory; "
                    f"reason: {e}. A branch of the Blueprints Repository attached to Colony Space will be used"
                )

        try:
            if temp_working_branch:
                self.message(f"Validating using temp branch: {temp_working_branch}")
                bp = self.manager.validate(blueprint=name, branch=temp_working_branch, commit=commit)
            else:
                self.message(f"Validating using remote branch: {working_branch}")
                bp = self.manager.validate(blueprint=name, branch=working_branch, commit=commit)

        except Exception as e:
            logger.exception(e, exc_info=False)
            bp = None
            self.die()

        errors = getattr(bp, "errors")

        if temp_working_branch.startswith(UNCOMMITTED_BRANCH_NAME):
            revert_from_temp_branch(repo, temp_working_branch, working_branch)

        if errors:
            # We don't need error code
            err_table = [{"message": err["message"], "name": err["name"]} for err in errors]

            logger.error("Validation failed")
            self.die(tabulate.tabulate(err_table, headers="keys"))

        else:
            self.success("Valid")
