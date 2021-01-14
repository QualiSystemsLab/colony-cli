from urllib.parse import urljoin

from colony.client import ColonyClient

# TODO(ddovbii): Make classes abstract


class ResourceManager(object):
    resource_obj = None

    def __init__(self, client: ColonyClient):
        self.client = client
        self.endpoint = urljoin(self.client.base_url, f"spaces/{self.client.space}/")

    def _get(self, path: str, headers: dict = None):
        if headers is None:
            headers = {}

        url = urljoin(self.endpoint, path)

        result_json = self.client.request(url, "GET", headers)
        return result_json

    def _list(self, path: str, filter: dict = None):
        url = urljoin(self.endpoint, path)

        # TODO(ddovbii): add filter handling
        if filter is not None:
            pass

        result_json = self.client.request(url, "GET")

        return result_json

    def _post(self, path: str, params: dict = None, headers: dict = None):
        if headers is None:
            headers = {}

        if params is None:
            params = {}

        url = urljoin(self.endpoint, path)
        result_json = self.client.request(url, "POST", params, headers)
        return result_json


class Resource(object):
    def __init__(self, manager: ResourceManager):
        self.manager = manager

    @classmethod
    def json_deserialize(cls, manager: ResourceManager, json_obj: dict):
        pass
