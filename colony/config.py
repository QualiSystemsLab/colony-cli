import logging
import os
from configparser import ConfigParser, ParsingError

import colony.exceptions

logger = logging.getLogger(__name__)


class ColonyConnection(object):
    def __init__(self, space: str, token: str):
        self.space = space
        self.token = token


class ColonyConfigProvider(object):
    default_config_path = "~/.colony/config"

    def __init__(self, filename: str = None):
        config_path = filename or self.default_config_path

        path = os.path.expandvars(config_path)
        path = os.path.expanduser(path)

        if not os.path.isfile(path):
            raise colony.exceptions.ConfigError("Config file doesn't exist")

        else:
            self.config_path = path

            try:
                conf = ConfigParser()
                conf.read(self.config_path)
                self.config_obj = conf

            except ParsingError as e:
                raise colony.exceptions.ConfigError(f"Wrong format of config file. Details {e}")

    def load_connection(self, profile_name: str = None):
        profile = profile_name or "default"
        config = self._parse_config()

        if profile not in config:
            raise colony.exceptions.ConfigError("Provided profile does not exist in config file")

        return ColonyConnection(**config[profile])

    def _parse_config(self) -> dict:
        config = {}
        for section in self.config_obj.sections():
            config[section] = dict(self.config_obj.items(section))

        return config

    def save_profile(self, profile_name, token, space):
        pass
