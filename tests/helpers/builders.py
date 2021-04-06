from typing import Dict, List

from colony.constants import ColonyConfigKeys


class ReleaseInfoBuilder:
    def __init__(self, version: str):
        self._version = version
        self._release = {"yanked": False}

    def with_yanked(self, is_yanked: bool = False):
        self._release["yanked"] = is_yanked
        return self

    def build(self) -> Dict:
        return {self._version: [self._release]}


class PyPiProjectInfoBuilder:
    def __init__(self):
        self._project = {"info": {}, "releases": {}}
        self._releases: List[ReleaseInfoBuilder] = []

    def with_version(self, version: str):
        self._project["info"]["version"] = version
        return self

    def with_release(self, release: ReleaseInfoBuilder):
        self._releases.append(release)
        return self

    def build(self) -> Dict:
        for release in self._releases:
            self._project["releases"].update(release.build())
        return self._project


class ConfigBuilder:
    def __init__(self):
        self._config = {}

    def with_profile(self, profile_name, space, token, account=None):
        profile_dict = {ColonyConfigKeys.SPACE: space, ColonyConfigKeys.TOKEN: token}
        if account:
            profile_dict[ColonyConfigKeys.ACCOUNT] = account

        self._config[profile_name] = profile_dict

        return self

    def build(self) -> Dict:
        return self._config
