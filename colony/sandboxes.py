from urllib.parse import urlparse

from .base import ResourceManager
from .model.sandbox import Sandbox


class SandboxesManager(ResourceManager):
    resource_obj = Sandbox
    SANDBOXES_PATH = "sandbox"
    SPECIFIC_SANDBOX_PATH = "sandboxes"

    def get_sandbox_url(self, sandbox_id: str) -> str:
        return self._get_full_url(f"{self.SPECIFIC_SANDBOX_PATH}/{sandbox_id}")

    def get_sandbox_ui_link(self, sandbox_id: str) -> str:
        url = urlparse(self.get_sandbox_url(sandbox_id))
        space = url.path.split("/")[3]
        if self.client.account:
            ui_url = f"https://{url.hostname}/{space}/{self.SPECIFIC_SANDBOX_PATH}/{sandbox_id}"
        else:
            ui_url = f"https://[YOUR_ACCOUNT].{url.hostname}/{space}/{self.SPECIFIC_SANDBOX_PATH}/{sandbox_id}"

        return ui_url

    def get(self, sandbox_id: str) -> Sandbox:
        url = f"{self.SANDBOXES_PATH}/{sandbox_id}"
        sb_json = self._get(url)

        return self.resource_obj.json_deserialize(self, sb_json)

    def list(self, count: int = 25, filter_opt: str = "my", sandbox_name: str = ""):

        filter_params = {"count": count, "filter": filter_opt, "sandbox_name": sandbox_name}
        list_json = self._list(path=self.SANDBOXES_PATH, filter_params=filter_params)

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
        url = f"{self.SANDBOXES_PATH}/{sandbox_id}"

        try:
            self.get(sandbox_id)

        except Exception as e:
            raise NotImplementedError(f"Unable to end sandbox with ID: {sandbox_id}. Details: {e}")

        self._delete(url)
