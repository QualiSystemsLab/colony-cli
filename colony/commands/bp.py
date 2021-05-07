import logging
from collections import OrderedDict

import tabulate
from docopt import DocoptExit

from colony.blueprints import BlueprintsManager
from colony.branch_utils import (
    count_stashed_items,
    create_and_handle_temp_branch_if_required,
    get_and_check_folder_based_repo,
    revert_and_delete_temp_branch, get_blueprint_working_branch, create_temp_branch_and_stash_if_needed,
)
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

    def do_validate(self) -> bool:
        blueprint_name = self.args.get("<name>")
        branch = self.args.get("--branch")
        commit = self.args.get("--commit")

        if commit and branch is None:
            raise DocoptExit("Since a commit was specified, a branch parameter is also required")

        repo = get_and_check_folder_based_repo(blueprint_name)
        items_in_stack_before_temp_branch_check = count_stashed_items(repo)
        if branch:
            working_branch = branch
            temp_working_branch = None
        else:
            working_branch = get_blueprint_working_branch(repo)
            temp_working_branch = create_temp_branch_and_stash_if_needed(repo, working_branch)
            if not temp_working_branch:
                return self.error("Unable to Validate BP")

        stashed_flag = items_in_stack_before_temp_branch_check < count_stashed_items(repo)

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
