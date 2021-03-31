class Unauthorized(Exception):
    pass


class ConfigError(Exception):
    pass


class ConfigFileMissingError(ConfigError):
    pass


class BadBlueprintRepo(Exception):
    pass
