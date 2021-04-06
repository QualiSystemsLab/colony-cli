import logging
import os
from configparser import ConfigParser, ParsingError

from colony.constants import ColonyConfigKeys
from colony.exceptions import ConfigError, ConfigFileMissingError

DEFAULT_CONFIG_PATH = "~/.colony/config"

logger = logging.getLogger(__name__)


class ColonyConfigProvider(object):
    def __init__(self, filename: str = ""):
        self.filename = filename or DEFAULT_CONFIG_PATH
        path = os.path.expandvars(self.filename)
        path = os.path.expanduser(path)
        self.config_path = path
        self.config_obj: ConfigParser = None

    def load_connection(self, profile_name: str = "") -> dict:
        self._validate_config_file_exists()

        self._load_config_from_path()

        config = self._parse_config()

        profile = profile_name or "default"
        self._validate_profile_exists_in_config(config, profile)

        if not all(k in config[profile] for k in (ColonyConfigKeys.TOKEN, ColonyConfigKeys.SPACE)):
            raise ConfigError(
                "Missing configuration settings. Profile must contain these settings: `token` and `space`"
            )

        return config[profile]

    def load_all(self) -> dict:
        self._validate_config_file_exists()
        self._load_config_from_path()
        config = self._parse_config()
        return config

    def save_profile(self, profile_name: str, token: str, space: str, account: str = ""):
        try:
            self._try_load_config()
            if not self.config_obj:
                self.config_obj = ConfigParser()
            if not self.config_obj.has_section(profile_name):
                self.config_obj.add_section(profile_name)

            self.config_obj.set(profile_name, ColonyConfigKeys.SPACE, space)
            self.config_obj.set(profile_name, ColonyConfigKeys.TOKEN, token)
            if account:
                self.config_obj.set(profile_name, ColonyConfigKeys.ACCOUNT, account)

            self._save_config_to_file()

        except Exception as exc:
            raise ConfigError(f"Error saving profile in config {self.config_path}. Error: f{str(exc)}")

    def remove_profile(self, profile_name):
        self._validate_config_file_exists()
        self._load_config_from_path()

        if self.config_obj.has_section(profile_name):
            self.config_obj.remove_section(profile_name)

            try:
                self._save_config_to_file()
            except Exception:
                raise ConfigError(f"Error saving config to file {self.config_path}")
        else:
            logger.debug("Nothing to remove. Provided profile does not exist in config file")

    def _save_config_to_file(self):
        with open(self.config_path, "w") as cfgfile:
            self.config_obj.write(cfgfile)

    def _validate_profile_exists_in_config(self, config, profile):
        if profile not in config:
            raise ConfigError("Provided profile does not exist in config file")

    def _load_config_from_path(self):
        try:
            conf = ConfigParser()
            conf.read(self.config_path)
            self.config_obj = conf

        except ParsingError as e:
            raise ConfigError(f"Wrong format of config file. Details {e}")

    def _try_load_config(self):
        try:
            self._load_config_from_path()
        except Exception:
            pass

    def _validate_config_file_exists(self):
        if not os.path.isfile(self.config_path):
            raise ConfigFileMissingError("Config file doesn't exist")

    def _parse_config(self) -> dict:
        config = {}
        for section in self.config_obj.sections():
            config[section] = dict(self.config_obj.items(section))

        return config
