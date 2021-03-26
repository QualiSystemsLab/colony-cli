import logging
import traceback
from typing import Dict, List

import requests
import semantic_version

from colony.commands.base import BaseCommand

logger = logging.getLogger(__name__)


class VersionCheckService:
    def __init__(self, current_version):
        self.current_version = current_version

    def check_for_new_version_safely(self):
        try:
            # get latest version from pypi
            response = requests.get("https://pypi.org/pypi/colony-cli/json")
            pypi_project_info = response.json()
            latest_release_info = pypi_project_info["info"]
            latest_version = latest_release_info["version"]

            try:
                if semantic_version.Version(latest_version) > semantic_version.Version(self.current_version):
                    self._show_new_version_message(latest_version)
            except ValueError:
                # we will get ValueError here if its a pre-release version
                # in this case iterate all available releases to check latest version that is not pre-release
                latest_version = self._find_latest_release(pypi_project_info)

                if semantic_version.Version(latest_version) > semantic_version.Version(self.current_version):
                    # latest version is bigger then current version so print nice message to user
                    self._show_new_version_message(latest_version)

        except Exception:
            logger.debug("Error checking latest version")
            logger.debug(traceback.format_exc())

    def _find_latest_release(self, pypi_project_info: Dict) -> str:
        """ Find latest not pre-release version """
        releases_info_dict = pypi_project_info["releases"]
        latest_version = self.current_version

        for version in releases_info_dict.keys():
            release_info_array = releases_info_dict[version]

            if self._is_release_yanked(release_info_array):
                # yanked release, need to skip
                continue

            try:
                if semantic_version.Version(version) > semantic_version.Version(latest_version):
                    # current version in loop in bigger then latest_version
                    latest_version = version
            except ValueError:
                # we will get ValueError here if its a pre-release version
                pass

        return latest_version

    def _is_release_yanked(self, release_info_array: List[Dict]) -> bool:
        return all(list(map(lambda x: x["yanked"], release_info_array)))

    def _show_new_version_message(self, latest_version: str):
        # todo - add color to the this message
        message = f"""================================================================
New version available: {latest_version}
Run 'pip install --upgrade colony-cli' to get the latest version
================================================================
"""
        BaseCommand.message(message)
