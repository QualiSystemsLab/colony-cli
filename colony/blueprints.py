from .base import Resource, ResourceManager


class Blueprint(Resource):
    def __init__(self, manager: ResourceManager, name: str, url: str):
        super(Blueprint, self).__init__(manager)

        self.name = name
        self.url = url

    @classmethod
    def json_deserialize(cls, manager: ResourceManager, json_obj: dict):
        try:
            bp = Blueprint(manager, json_obj["blueprint_name"], json_obj["url"])
        except KeyError as e:
            raise NotImplementedError(f"unable to create object. Missing keys in Json. Details: {e}")

        # TODO(ddovbii): set all needed attributes
        bp.errors = json_obj.get("errors", [])
        bp.description = json_obj.get("description", "")
        return bp


class BlueprintsManager(ResourceManager):
    resource_obj = Blueprint

    def get(self, blueprint_name: str) -> Blueprint:
        url = f"catalog/{blueprint_name}"
        bp_json = self._get(url)

        return Blueprint.json_deserialize(self, bp_json)

    def list(self):
        url = "blueprints"
        result_json = self._list(path=url)
        return [self.resource_obj.json_deserialize(self, obj) for obj in result_json]

    def validate(self, blueprint: str, env_type: str = "sandbox", branch: str = None, commit: str = None) -> Blueprint:
        url = "validations/blueprints"
        params = {"blueprint_name": blueprint, "type": env_type}

        if commit and branch in (None, ""):
            raise ValueError("Since commit is specified, branch is required")

        if branch:
            params["source"] = {
                "branch": branch,
            }
            params["source"]["commit"] = commit or ""

        result_json = self._post(url, params)
        result_bp = Blueprint.json_deserialize(self, result_json)
        return result_bp
