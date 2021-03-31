import tabulate

from colony.constants import ColonyConfigKeys
from colony.view.view_helper import mask_token


class ConfigureListView:
    def __init__(self, config: dict):
        self.config = config

    def render(self):
        if not self.config:
            return "Config file is empty. Use 'colony configure set' to configure Colony CLI."

        result_table = []
        for profile in self.config.keys():
            result_table.append(
                {
                    "Profile Name": profile,
                    "Colony Account": self.config[profile].get(ColonyConfigKeys.ACCOUNT, None),
                    "Space Name": self.config[profile].get(ColonyConfigKeys.SPACE, None),
                    "Token": mask_token(self.config[profile].get(ColonyConfigKeys.TOKEN, None))
                }
            )

        return tabulate.tabulate(result_table, headers="keys")


