from .base import Resource, ResourceManager
from .blueprints import BlueprintsManager


class Sandbox(Resource):
    def __init__(self, manager: ResourceManager, sandbox_id: str, name: str, blueprint_name: str):
        super(Sandbox, self).__init__(manager)

        self.sandbox_id = sandbox_id
        self.name = name
        self.blueprint_name = blueprint_name

    @classmethod
    def json_deserialize(cls, manager: ResourceManager, json_obj: dict):
        try:
            sb = Sandbox(manager, json_obj["id"], json_obj["name"], json_obj["blueprint_name"])
        except KeyError as e:
            raise NotImplementedError(f"unable to create object. Missing keys in Json. Details: {e}")

        # TODO(ddovbii): set all needed attributes
        # sb.errors = json_obj.get("errors", [])
        # sb.description = json_obj.get("description", "")
        # sb.status = json_obj.get("sandbox_status", "")
        # sb.launching_progress = json_obj.get("launching_progress", {})
        sb.__dict__ = json_obj.copy()

        return sb


class SandboxesManager(ResourceManager):
    resource_obj = Sandbox

    def get(self, sandbox_id: str) -> Sandbox:
        url = f"sandbox/{sandbox_id}"
        sb_json = self._get(url)

        return self.resource_obj.json_deserialize(self, sb_json)

    def start(
        self,
        sandbox_name: str,
        blueprint_name: str,
        duration: int = 120,
        branch: str = None,
        commit: str = None,
        artifacts: dict = None,
        inputs: dict = None,
    ) -> str:
        url = "sandbox"

        if commit and not branch:
            raise ValueError("Commit is passed without branch")

        bm = BlueprintsManager(self.client)

        try:
            bm.get(blueprint_name)
        except Exception as e:
            raise NotImplementedError(f"Unable to get blueprint with passed name {blueprint_name}. Details: {e}")

        iso_duration = f"PT{duration}M"

        params = {
            "sandbox_name": sandbox_name,
            "blueprint_name": blueprint_name,
            "duration": iso_duration,
            "inputs": inputs,
            "artifacts": artifacts,
        }

        if branch:
            params["source"] = {
                "branch": branch,
            }
            params["source"]["commit"] = commit or ""

        result_json = self._post(url, params)
        sandbox_id = result_json["id"]
        return sandbox_id

    def end(self, sandbox_id: str):
        url = f"sandbox/{sandbox_id}"

        try:
            self.get(sandbox_id)

        except Exception as e:
            raise NotImplementedError(f"Unable to end sandbox with ID: {sandbox_id}. Details: {e}")

        self._delete(url)
