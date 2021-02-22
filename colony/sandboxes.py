from .base import Resource, ResourceManager


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

        for attr in ["description", "errors", "sandbox_status", "launching_progress"]:
            sb.__dict__[attr] = json_obj.get(attr, "")
        # TODO(ddovbii): set all needed attributes
        # sb.errors = json_obj.get("errors", [])
        # sb.description = json_obj.get("description", "")
        # sb.status = json_obj.get("sandbox_status", "")
        # sb.launching_progress = json_obj.get("launching_progress", {})
        # sb.__dict__ = json_obj.copy()

        return sb


class SandboxesManager(ResourceManager):
    resource_obj = Sandbox

    def get(self, sandbox_id: str) -> Sandbox:
        url = f"sandbox/{sandbox_id}"
        sb_json = self._get(url)

        return self.resource_obj.json_deserialize(self, sb_json)

    def list(self, count: int = 25, filter_opt: str = "my"):
        url = "sandbox"

        filter_params = {"count": count, "filter": filter_opt}
        list_json = self._list(path=url, filter_params=filter_params)

        return [self.resource_obj.json_deserialize(self, obj) for obj in list_json]

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
