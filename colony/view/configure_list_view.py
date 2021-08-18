from collections import OrderedDict

import tabulate
from colony.services.branding import Branding

from colony.constants import ColonyConfigKeys
from colony.view.view_helper import mask_token


class ConfigureListView:
    def __init__(self, config: dict):
        self.config = config

    def render(self):
        if not self.config:
            return f"Config file is empty. Use '{Branding.command_name()} configure set' " \
                   f"to configure {Branding.product_name()} CLI."

        result_table = []
        for profile in self.config.keys():
            item = OrderedDict()
            item["Profile Name"] = profile
            item[f"{Branding.product_name()} Account"] = self.config[profile].get(ColonyConfigKeys.ACCOUNT, None)
            item["Space Name"] = self.config[profile].get(ColonyConfigKeys.SPACE, None)
            item["Token"] = mask_token(self.config[profile].get(ColonyConfigKeys.TOKEN, None))
            result_table.append(item)

        return tabulate.tabulate(result_table, headers="keys")
