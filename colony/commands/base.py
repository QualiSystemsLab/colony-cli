import sys

from docopt import DocoptExit, docopt

from colony.base import ResourceManager
from colony.client import ColonyClient
from colony.config import ColonyConnection


class BaseCommand(object):
    """
    usage: colony
    """

    RESOURCE_MANAGER = ResourceManager

    def __init__(self, command_args: list, connection: ColonyConnection = None):
        if connection:
            self.client = ColonyClient(space=connection.space, token=connection.token)
            self.manager = self.RESOURCE_MANAGER(client=self.client)
        else:
            self.client = None
            self.manager = None

        self.args = docopt(self.__doc__, argv=command_args)

    def execute(self):
        """Finds a subcommand passed to with command in
        object actions table and executes mapped method"""

        args = self.args

        actions_table = self.get_actions_table()

        for action in actions_table:
            if args.get(action, False):
                # call action
                actions_table[action]()
                break

        # if subcommand was specified without args (actions), just show usage
        raise DocoptExit

    def get_actions_table(self) -> dict:
        return {}

    @staticmethod
    def success(message: str = ""):
        if message:
            sys.stdout.write(message)
            sys.stdout.write("\n")
        sys.exit()

    @staticmethod
    def die(message: str = ""):
        if message:
            sys.stderr.write(message)
            sys.stderr.write("\n")
        sys.exit(1)

    @staticmethod
    def message(message: str = ""):
        sys.stdout.write(message)
        sys.stdout.write("\n")
