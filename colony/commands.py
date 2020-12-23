import os

from docopt import docopt, DocoptExit
from colony.client import ColonyClient

from colony.utils import BlueprintRepo, BadBlueprintRepo
import logging

logger = logging.getLogger(__name__)


class BaseCommand(object):
    """Base class for parsed docopt command"""

    def __init__(self, client: ColonyClient, command_args):
        self.client = client
        self.args = docopt(self.__doc__, argv=command_args)

    def execute(self):
        pass


class BlueprintsCommand(BaseCommand):
    """
    usage:
        colony bp list
        colony bp validate <name> [-b --branch <branch>]
        colony blueprints validate <name> [--help] [-b --branch <branch>] [-c --commit <commitId>]

    options:
       -b --branch      Specify the name of remote git branch
       -c --commit      Specify commit ID. It's required if
       -h --help        Show this message
    """

    def execute(self):
        if self.args['list']:
            bps = self.client.blueprints.list()
            template = "{0:65}|{1:50}"
            print(template.format("Blueprint", "Url"))

            for bp in bps:
                print(template.format(bp.name, bp.url))
        if self.args['validate']:
            name = self.args.get('<name>')
            branch = self.args.get('<branch>')
            commit = self.args.get('<commitId>')

            # TODO: it should be possible to handle it by docopt initially
            if commit and branch is None:
                raise DocoptExit("Since commit is specified, branch is required")

            if not branch:
                logger.warning("Branch hasn't been specified. "
                             "Trying to identify branch from current working directory")

                try:
                    repo = BlueprintRepo(os.getcwd())
                    local_branch = repo.active_branch.name
                    logger.debug(f"Current working branch is '{local_branch}' ")

                    if repo.is_dirty():
                        logger.warning("You have uncommitted changes")

                    if repo.is_repo_detached():
                        raise BadBlueprintRepo("Repo's HEAD is in detached state")

                    if repo.current_branch_exists_on_remote():
                        branch = local_branch
                    else:
                        logger.warning("Your current local branch doesn't exist on remote")

                    if not repo.is_current_branch_synced():
                        logger.warning("Your local branch is not synced with remote")

                except BadBlueprintRepo as e:
                    logger.warning(f"Bad colony repo. Details: {e}")

                finally:
                    if not branch:
                        logger.warning("No branch has been specified and it couldn't be identified. "
                                       "Blueprint branch attached to Colony will be used")

                # work_branch = colony.utils.get_blueprint_branch()
                # if work_branch:
                #
                #     logger.warning(f"Since you haven't specified a branch, "
                #           f"current work branch '{work_branch}' is used")
                #     branch = work_branch
                # else:
                #     logger.warning("No branch has been specified and it couldn't be identified. "
                #           "Using branch attached to Colony")

            try:
                bp = self.client.blueprints.validate(blueprint=name, branch=branch, commit=commit)
            except Exception as e:
                logger.exception(e, exc_info=True)
                return
            errors = bp.errors
            if errors:
                template = "{0:35}|{1:85}|{2:30}"
                print(template.format("Code", "Message", "Name"))

                for er in errors:
                    print(template.format(er['code'], er['message'], er['name']))

            else:
                print("Valid!")
