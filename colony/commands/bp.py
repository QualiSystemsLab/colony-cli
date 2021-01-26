import logging
import os

import tabulate
from docopt import DocoptExit

from colony.blueprints import BlueprintsManager
from colony.commands.base import BaseCommand
from colony.exceptions import BadBlueprintRepo
from colony.utils import get_blueprint_working_branch

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

       -h --help                Show this message
    """

    RESOURCE_MANAGER = BlueprintsManager

    def get_actions_table(self) -> dict:
        return {"validate": self.do_validate}

    def do_validate(self):
        name = self.args.get("<name>")
        branch = self.args.get("--branch")
        commit = self.args.get("--commit")

        if commit and branch is None:
            raise DocoptExit("Since commit is specified, branch is required")

        if branch:
            working_branch = branch
        else:
            # Try to detect branch from current git-enabled folder
            logger.debug("Branch hasn't been specified. Trying to identify branch from current working directory")
            try:
                working_branch = get_blueprint_working_branch(os.getcwd(), blueprint_name=name)
                self.message(f"Automatically detected current working branch: {working_branch}")
            except BadBlueprintRepo as e:
                working_branch = None
                logger.warning(
                    f"No branch has been specified and it could not be identified from the working directory; "
                    f"reason: {e}. A branch of the Blueprints Repository attached to Colony Space will be used"
                )

        try:
            bp = self.manager.validate(blueprint=name, branch=working_branch, commit=commit)

        except Exception as e:
            logger.exception(e, exc_info=False)
            bp = None
            self.die()

        errors = getattr(bp, "errors")
        if errors:
            # We don't need error code
            err_table = [{"message": err["message"], "name": err["name"]} for err in errors]

            logger.error("Validation failed")
            self.die(tabulate.tabulate(err_table, headers="keys"))

        else:
            self.success("Valid")
