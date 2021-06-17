import sys

from colorama import Fore, Style
from docopt import DocoptExit, docopt

from colony.base import ResourceManager
from colony.client import ColonyClient
from colony.models.connection import ColonyConnection
from colony.parsers.command_input_parsers import CommandInputParser


class BaseCommand(object):
    """
    usage: colony
    """

    RESOURCE_MANAGER = ResourceManager

    def __init__(self, command_args: list, connection: ColonyConnection = None):
        if connection:
            self.client = ColonyClient(space=connection.space, token=connection.token, account=connection.account)
            self.manager = self.RESOURCE_MANAGER(client=self.client)
        else:
            self.client = None
            self.manager = None

        self.args = docopt(self.__doc__, argv=command_args)
        self.input_parser = CommandInputParser(self.args)

    def execute(self) -> bool:
        """Finds a subcommand passed to with command in
        object actions table and executes mapped method"""

        actions_table = self.get_actions_table()
        for action in actions_table:
            if self.args.get(action, False):
                # call action
                return actions_table[action]()

        # if subcommand was specified without args (actions), just show usage
        raise DocoptExit

    def get_actions_table(self) -> dict:
        return {}

    @staticmethod
    def styled_text(style, message: str = "", newline=True):
        if message:
            sys.stdout.write(style + message)
            sys.stdout.write(Style.RESET_ALL)
        if newline:
            sys.stdout.write("\n")

    @staticmethod
    def error(message: str = "") -> bool:
        BaseCommand.styled_text(Fore.RED, message)
        return False

    @staticmethod
    def success(message: str = "") -> bool:
        BaseCommand.styled_text(Fore.GREEN, message)
        return True

    @staticmethod
    def die(message: str = "") -> bool:
        if message:
            sys.stderr.write(message)
            sys.stderr.write("\n")
        return False

    @staticmethod
    # Unimportant info that can be de-emphasized
    def fyi_info(message: str = ""):
        BaseCommand.styled_text(Style.DIM, message)

    @staticmethod
    # Something active is being performed
    def action_announcement(message: str = ""):
        BaseCommand.styled_text(Fore.YELLOW, message)

    @staticmethod
    # Unimportant info that can be de-emphasized
    def info(message: str = ""):
        BaseCommand.styled_text(Fore.LIGHTBLUE_EX, message)

    @staticmethod
    # Unimportant info that can be de-emphasized
    def important_value(prefix_message: str = "", value: str = ""):
        if prefix_message:
            BaseCommand.styled_text(Style.DIM, prefix_message, False)
        BaseCommand.styled_text(Fore.CYAN, value)

    @staticmethod
    def message(message: str = ""):
        sys.stdout.write(message)
        sys.stdout.write("\n")

    @staticmethod
    def url(prefix_message, message: str = ""):
        if prefix_message:
            BaseCommand.styled_text(Style.DIM, prefix_message, False)
        BaseCommand.styled_text(Fore.BLUE, message)
