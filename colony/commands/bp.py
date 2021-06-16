import logging
from collections import OrderedDict

import tabulate
from docopt import DocoptExit

from colony.blueprints import BlueprintsManager
from colony.branch_utils import figure_out_branches, revert_and_delete_temp_branch
from colony.commands.base import BaseCommand
from colony.parsers.command_input_validators import CommandInputValidator

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

    def do_validate(self) -> bool:
        blueprint_name = self.input_parser.blueprint_validate.blueprint_name
        branch = self.input_parser.blueprint_validate.branch
        commit = self.input_parser.blueprint_validate.commit

        CommandInputValidator.validate_commit_and_branch_specified(branch, commit)

        repo, working_branch, temp_working_branch, stashed_flag, success = figure_out_branches(branch, blueprint_name)

        if not success:
            self.error("Unable to validate Blueprint")
            return False

        validation_branch = temp_working_branch or working_branch

        try:
            bp = self.manager.validate(blueprint=blueprint_name, branch=validation_branch, commit=commit)

        except Exception as e:
            logger.exception(e, exc_info=False)
            bp = None
            return self.die()
        finally:
            revert_and_delete_temp_branch(repo, working_branch, temp_working_branch, stashed_flag)

        errors = getattr(bp, "errors")

        if errors:
            # We don't need error code
            err_table = [OrderedDict([("NAME", err["name"]), ("MESSAGE", err["message"])]) for err in errors]

            logger.error("Blueprint validation failed")
            return self.die(tabulate.tabulate(err_table, headers="keys"))

        else:
            return self.success("Blueprint is valid")
