import logging
from collections import OrderedDict

import tabulate
from docopt import DocoptExit

from colony.blueprints import BlueprintsManager
from colony.branch_utils import create_and_handle_temp_branch_if_required, revert_and_delete_temp_branch, \
    check_repo_and_return_working_branch, get_and_check_folder_based_repo, count_stashed_items
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
        items_in_stash_before_temp_branch_check = count_stashed_items(repo)
        if branch:
            working_branch = branch
            temp_working_branch = None
        else:
            working_branch = check_repo_and_return_working_branch(blueprint_name)
            temp_working_branch = create_and_handle_temp_branch_if_required(blueprint_name, working_branch)
            if not temp_working_branch:
                self.error("Unable to validate Blueprint")
                return False
        stashed_flag = count_stashed_items(repo) > items_in_stash_before_temp_branch_check

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
