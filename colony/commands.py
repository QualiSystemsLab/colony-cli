from docopt import docopt
from colony.client import ColonyClient
from pprint import pprint

import colony.utils

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
        if "validate" in self.args:
            name = self.args.get('<name>')
            branch = self.args.get('<branch>')
            commit = self.args.get('<commitId>')

            if commit and branch is None:
                print("Since commit is specified, branch is required")
                return

            if not branch:
                # Try to identify working branch
                work_branch = colony.utils.get_blueprint_branch()
                if work_branch:
                    print(f"colony[WARN]: Since you haven't specified a branch, "
                          f"current work branch '{work_branch}' is used")
                    branch = work_branch
                else:
                    print("colony[WARN]: No branch has been specified and it couldn't be identified. "
                          "Using branch attached to Colony")

            try:
                bp = self.client.blueprints.validate(blueprint=name, branch=branch, commit=commit)
            except Exception as e:
                print(f"Unable to run command. Details {e}")
                return
            errors = bp.errors
            if errors:
                pprint(errors)

            else:
                print("Valid!")