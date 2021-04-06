from collections import OrderedDict

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
            item = OrderedDict()
            item["Profile Name"] = profile
            item["Colony Account"] = self.config[profile].get(ColonyConfigKeys.ACCOUNT, None)
            item["Space Name"] = self.config[profile].get(ColonyConfigKeys.SPACE, None)
            item["Token"] = mask_token(self.config[profile].get(ColonyConfigKeys.TOKEN, None))
            result_table.append(item)

        return tabulate.tabulate(result_table, headers="keys")
