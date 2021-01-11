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


def get_working_branch() -> str:
    logger.debug("Branch hasn't been specified. "
                 "Trying to identify branch from current working directory")
    branch = None

    try:
        repo = BlueprintRepo(os.getcwd())
        if repo.is_repo_detached():
            raise BadBlueprintRepo("Repo's HEAD is in detached state")

        branch = repo.active_branch.name
        logger.debug(f"Current working branch is '{branch}'")

        if repo.is_dirty():
            logger.warning("You have uncommitted changes")

        if not repo.current_branch_exists_on_remote():
            raise BadBlueprintRepo("Your current local branch doesn't exist on remote")

        if not repo.is_current_branch_synced():
            logger.warning("Your local branch is not synced with remote")

    except BadBlueprintRepo as e:
        logger.debug(f"Unable to recognize current directory as a proper colony blueprints git repo. "
                     f"Details: {e}")
    finally:
        if not branch:
            logger.warning("No branch has been specified and it couldn't be identified. "
                           "Blueprint branch attached to Colony will be used. "
                           "Use `--debug` flag to find details ")

    return branch


class BlueprintsCommand(BaseCommand):
    """
    usage:
        colony bp validate <name> [-b --branch <branch>]
        colony blueprint validate <name> [--help] [-b --branch <branch>] [-c --commit <commitId>]

    options:
       -b --branch      Specify the name of remote git branch
       -c --commit      Specify commit ID. It's required if
       -h --help        Show this message
    """

    def execute(self):
        # if self.args['list']:
        #     bps = self.client.blueprints.list()
        #     template = "{0:65}|{1:50}"
        #     print(template.format("Blueprint", "Url"))
        #
        #     for bp in bps:
        #         print(template.format(bp.name, bp.url))
        if self.args['validate']:
            name = self.args.get('<name>')
            branch = self.args.get('<branch>')
            commit = self.args.get('<commitId>')

            # TODO: it should be possible to handle it by docopt initially
            if commit and branch is None:
                raise DocoptExit("Since commit is specified, branch is required")

            working_branch = branch or get_working_branch()

            try:
                bp = self.client.blueprints.validate(blueprint=name, branch=working_branch, commit=commit)
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


def parse_comma_separated_string(params_string: str = None) -> dict:
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


class SandboxesCommand(BaseCommand):
    """
        usage:
            colony sb start <blueprint_name> [options]
            colony sb [--help]

        options:
           -h --help        Show this message
           -d, --duration <minutes>
           -n, --name <sandbox_name>
           -i, --inputs <input_params>
           -a, --artifacts <artifacts>
           -b, --branch <branch>
           -c, --commit <commitId>
        """
    def execute(self):
        if self.args["start"]:
            bp_name = self.args["<blueprint_name>"]

            branch = self.args.get('--branch')
            commit = self.args.get('--commit')
            name = self.args["--name"]

            if name is None:
                suffix = datetime.datetime.now().strftime("%b%d%Y-%H:%M:%S")
                name = f"{bp_name}-{suffix}"

            inputs = parse_comma_separated_string(self.args["--inputs"])
            artifacts = parse_comma_separated_string(self.args["--artifacts"])

            logger.debug("Trying to obtain default values for artifacts and inputs from local git blueprint repo")
            try:
                repo = BlueprintRepo(os.getcwd())
                if not repo.is_current_branch_synced():
                    logger.debug("Skipping obtaining values since local branch is not synced with remote")
                else:

                    for art_name, art_path in repo.get_blueprint_artifacts(bp_name).items():
                        if art_name not in artifacts and art_path is not None:
                            logger.debug(f"Artifact `{art_name}` has been set with default path `{art_path}`")
                            artifacts[art_name] = art_path

                    for input_name, input_value in repo.get_blueprint_default_inputs(bp_name).items():
                        if input_name not in inputs and input_value is not None:
                            logger.debug(f"Parameter `{input_name}` has been set with default value `{input_value}`")
                            inputs[input_name] = input_value

            except Exception as e:
                logger.debug(f"Unable to recognize current directory as a blueprint repo. Details: {e}")

            try:
                duration = int(self.args["--duration"] or 120)
                if duration <= 0:
                    raise DocoptExit("Duration must be positive")

            except ValueError:
                raise DocoptExit("Duration must be a number")

            # TODO: it should be possible to handle it by docopt initially
            if commit and branch is None:
                raise DocoptExit("Since commit is specified, branch is required")

            working_branch = branch or get_working_branch()

            try:
                sandbox_id = self.client.sandboxes.start(name, bp_name, duration, working_branch,
                                                         commit, artifacts, inputs)
            except Exception as e:
                logger.exception(e, exc_info=False)
                return

            print(sandbox_id)





