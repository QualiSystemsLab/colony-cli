import getpass
import logging

from docopt import DocoptExit

from colony.commands.base import BaseCommand
from colony.constants import ColonyConfigKeys
from colony.exceptions import ConfigFileMissingError
from colony.parsers.global_input_parser import GlobalInputParser
from colony.sandboxes import SandboxesManager
from colony.services.branding import Branding
from colony.services.config import ColonyConfigProvider
from colony.view.configure_list_view import ConfigureListView
from colony.view.view_helper import mask_token

logger = logging.getLogger(__name__)


class ConfigureCommand(BaseCommand):
    """
    usage:
        {command_name} configure set
        {command_name} configure list
        {command_name} configure remove <profile>
        {command_name} configure [--help|-h]

    options:
        -h --help                   Show this message
    """

    RESOURCE_MANAGER = SandboxesManager

    def get_actions_table(self) -> dict:
        return {"set": self.do_configure, "list": self.do_list, "remove": self.do_remove}

    def do_list(self):
        config = None
        try:
            config_file = GlobalInputParser.get_config_path()
            config = ColonyConfigProvider(config_file).load_all()
            result_table = ConfigureListView(config).render()

        except ConfigFileMissingError:
            raise DocoptExit(
                "Config file doesn't exist. Use '{command_name} configure set' "
                "to configure {product_name} CLI.".format(
                    command_name=Branding.command_name(), product_name=Branding.product_name()
                )
            )
        except Exception as e:
            logger.exception(e, exc_info=False)
            return self.die()

        self.message(result_table)
        return self.success()

    def do_remove(self):
        profile_to_remove = self.input_parser.configure_remove.profile
        if not profile_to_remove:
            raise DocoptExit("Please provide a profile name to remove")

        try:
            config_file = GlobalInputParser.get_config_path()
            config_provider = ColonyConfigProvider(config_file)
            config_provider.remove_profile(profile_to_remove)
        except Exception as e:
            logger.exception(e, exc_info=False)
            return self.die()

        return self.success()

    def do_configure(self):
        config_file = GlobalInputParser.get_config_path()
        config_provider = ColonyConfigProvider(config_file)
        config = {}
        try:
            config = config_provider.load_all()
        except Exception:
            pass

        # read profile
        profile = input("Profile Name [default]: ")
        profile = profile or "default"

        # if profile exists set current values from profile
        current_account = config.get(profile, {}).get(ColonyConfigKeys.ACCOUNT, "")
        current_space = config.get(profile, {}).get(ColonyConfigKeys.SPACE, "")
        current_token = config.get(profile, {}).get(ColonyConfigKeys.TOKEN, "")

        # read account
        account = input(f"{Branding.product_name()} Account (optional) [{current_account}]: ")
        account = account or current_account

        # read space name
        space = input(f"{Branding.product_name()} Space [{current_space}]: ")
        space = space or current_space
        if not space:
            return self.die("Space cannot be empty")

        # read token
        token = getpass.getpass(f"{Branding.product_name()} Token [{mask_token(current_token)}]: ")
        token = token or current_token
        if not token:
            return self.die("Token cannot be empty")

        # save user inputs
        config_provider.save_profile(profile, token, space, account)

        return self.success()
