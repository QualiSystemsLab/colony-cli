import logging
from collections import OrderedDict

import tabulate
from docopt import DocoptExit

from colony.blueprints import BlueprintsManager
from colony.branch_utils import figure_out_branches, revert_and_delete_temp_branch
from colony.commands.base import BaseCommand

logger = logging.getLogger(__name__)


class BlueprintsCommand(BaseCommand):
    """
    usage:
        colony (bp | blueprint) validate <name> [options]
        colony (bp | blueprint) [--help]

    options:
       -b --branch <branch>     Specify the name of the remote git branch. If not provided, the CLI will attempt to
                                automatically detect the current working branch. The latest branch commit will be used
                                by default unless the commit parameter is also specified.

       -c --commit <commitId>   Specify the commit ID. This can be used to validate a blueprint from an historic commit.
                                This option can be used together with the branch parameter.

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
            raise DocoptExit("Since a commit was specified, a branch parameter is also required")

        repo, working_branch, temp_working_branch, stashed_flag, success = figure_out_branches(branch, blueprint_name)

        if not success:
            self.error("Unable to validate Blueprint")
            return

        validation_branch = temp_working_branch or working_branch

        try:
            bp = self.manager.validate(blueprint=blueprint_name, branch=validation_branch, commit=commit)

        except Exception as e:
            logger.exception(e, exc_info=False)
            bp = None
            self.die()
        finally:
            revert_and_delete_temp_branch(repo, working_branch, temp_working_branch, stashed_flag)

        errors = getattr(bp, "errors")

        if errors:
            # We don't need error code
            err_table = [OrderedDict([("NAME", err["name"]), ("MESSAGE", err["message"])]) for err in errors]

            logger.error("Blueprint validation failed")
            self.die(tabulate.tabulate(err_table, headers="keys"))

        else:
            self.success("Blueprint is valid")
