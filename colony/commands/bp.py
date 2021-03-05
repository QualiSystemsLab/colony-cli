import logging

import tabulate
from docopt import DocoptExit

from colony.blueprints import BlueprintsManager
from colony.commands.base import BaseCommand
from colony.utils import UNCOMMITTED_BRANCH_NAME, figure_out_branches, revert_from_temp_branch

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
        blueprint_name = self.args.get("<name>")
        branch = self.args.get("--branch")
        commit = self.args.get("--commit")

        if commit and branch is None:
            raise DocoptExit("Since commit is specified, branch is required")

        repo, working_branch, temp_working_branch = figure_out_branches(branch, blueprint_name)

        validation_branch = temp_working_branch or working_branch

        try:
            bp = self.manager.validate(blueprint=blueprint_name, branch=validation_branch, commit=commit)

        except Exception as e:
            logger.exception(e, exc_info=False)
            bp = None
            self.die()
        finally:
            if temp_working_branch.startswith(UNCOMMITTED_BRANCH_NAME):
                revert_from_temp_branch(repo, temp_working_branch, working_branch)

        errors = getattr(bp, "errors")

        if errors:
            # We don't need error code
            err_table = [{"message": err["message"], "name": err["name"]} for err in errors]

            logger.error("Validation failed")
            self.die(tabulate.tabulate(err_table, headers="keys"))

        else:
            self.success("Valid")
