import logging

from docopt import DocoptExit

from colony.constants import ColonyConfigKeys
from colony.exceptions import ConfigError
from colony.models.connection import ColonyConnection
from colony.parsers.global_input_parser import GlobalInputParser
from colony.services.config import ColonyConfigProvider

logger = logging.getLogger(__name__)


class ColonyConnectionProvider:
    def __init__(self, args_parser: GlobalInputParser):
        self._args_parser = args_parser

    def get_connection(self) -> ColonyConnection:
        # first try to get them as options or from env variable
        token = self._args_parser.token
        space = self._args_parser.space
        account = self._args_parser.account

        # then try to load them from file
        if not all([token, space]):
            logger.debug("Couldn't fetch token/space neither from command line nor environment variables")
            profile = self._args_parser.profile
            config_file = self._args_parser.get_config_path()
            logger.debug("Trying to obtain unset values from configuration file")
            try:
                colony_conn = ColonyConfigProvider(config_file).load_connection(profile)
                token = token or colony_conn[ColonyConfigKeys.TOKEN]
                space = space or colony_conn[ColonyConfigKeys.SPACE]
                if ColonyConfigKeys.ACCOUNT in colony_conn:
                    account = colony_conn[ColonyConfigKeys.ACCOUNT]
            except ConfigError as e:
                raise DocoptExit(f"Unable to read Colony credentials. Reason: {e}")

        return ColonyConnection(token=token, space=space, account=account)
