import os

from docopt import docopt, DocoptExit
from colony.client import ColonyClient

from colony.utils import BlueprintRepo, BadBlueprintRepo
import logging
import datetime

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


class SandboxesCommand(BaseCommand):
    """
    usage:
        colony sb start <blueprint_name> [-n --name <sandbox_name>] [-d --duration <minutes>]
                                         [-i --inputs <input_params>] [-a --artifacts <artifacts>]
                                         [-b --branch <branch>] [-c --commit <commitId>]
    """

    def execute(self):
        if self.args["start"]:
            bp_name = self.args["<blueprint_name>"]
            branch = self.args.get('<branch>')
            commit = self.args.get('<commitId>')

            name = self.args["sandbox_name"]
            if name is None:
                suffix = datetime.datetime.now().timestamp()
                name = f"{bp_name}-{suffix}"

            inputs = self._parse_comma_separated_string(self.args["<inputs>"])
            artifacts = self._parse_comma_separated_string(self.args["<artifacts>"])

            try:
                duration = int(self.args["<duration>"])
                if duration <= 0:
                    raise DocoptExit("duration must be positive")

            except ValueError:
                raise DocoptExit("Duration must be a numner")


            # TODO: it should be possible to handle it by docopt initially
            if commit and branch is None:
                raise DocoptExit("Since commit is specified, branch is required")

            if not branch:
                logger.warning("Branch hasn't been specified. "
                             "Trying to identify branch from current working directory")

    def _parse_comma_separated_string(self, params_string: str = None) -> dict:
        res = {}

        if not params_string:
            return res

        key_vals = params_string.split(",")

        for item in key_vals:
            parts = item.split("=")
            key = parts[0].strip()
            val = parts[1].strip()
            res[key] = val

        return res


