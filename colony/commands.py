from docopt import docopt
from colony.client import ColonyClient
from pprint import pprint

class BaseCommand(object):
    """Base class for parsed docopt command"""

    def __init__(self, client: ColonyClient, command_args):
        self.client = client
        self.args = docopt(self.__doc__, argv=command_args)
        print(self.args)


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