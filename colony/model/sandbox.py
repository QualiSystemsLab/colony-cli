from colony.base import Resource, ResourceManager


class Sandbox(Resource):
    class Service(object):
        def __init__(self, name: str, status: str):
            self.status = status
            self.name = name

    class Application(object):
        def __init__(self, name: str, status: str, shortcuts: [str]):
            self.status = status
            self.shortcuts = shortcuts
            self.name = name

    class SandboxProgressItem(object):
        @classmethod
        def json_deserialize(cls, name: str, json_obj: dict):
            return Sandbox.SandboxProgressItem(
                name=name,
                total=int(json_obj["total"]),
                succeeded=int(json_obj["succeeded"]),
                failed=int(json_obj["failed"]),
                status=json_obj["status"],
            )

        def __init__(self, name: str, total: int, succeeded: int, failed: int, status: str):
            self.name = name
            self.status = status
            self.failed = failed
            self.succeeded = succeeded
            self.total = total

    applications: [Application]
    services: [Service]
    sandbox_progress: {str, SandboxProgressItem}

    def __init__(self, manager: ResourceManager, sandbox_id: str, name: str, blueprint_name: str):
        super(Sandbox, self).__init__(manager)

        self.sandbox_id = sandbox_id
        self.name = name
        self.blueprint_name = blueprint_name
        self.applications = []
        self.services = []
        self.sandbox_progress = {}

    @classmethod
    def json_deserialize(cls, manager: ResourceManager, json_obj: dict):
        try:
            sb = Sandbox(manager, json_obj["id"], json_obj["name"], json_obj["blueprint_name"])
        except KeyError as e:
            raise NotImplementedError(f"unable to create object. Missing keys in Json. Details: {e}")

        for attr in ["description", "errors", "sandbox_status", "launching_progress"]:
            sb.__dict__[attr] = json_obj.get(attr, "")
        applications_json = json_obj.get("applications", [])
        for app_json in applications_json:
            app = Sandbox.Application(
                name=app_json.get("name"), status=app_json.get("status"), shortcuts=app_json.get("shortcuts", [])
            )
            sb.applications.append(app)

        services_json = json_obj.get("services", [])
        for service_json in services_json:
            service = Sandbox.Service(name=service_json.get("name"), status=service_json.get("status"))
            sb.services.append(service)

        launch_progress_json = json_obj.get("launching_progress", {})

        progress_steps = [
            "creating_infrastructure",
            "preparing_artifacts",
            "deploying_applications",
            "verifying_environment",
        ]

        if launch_progress_json:
            for step in progress_steps:
                sb.sandbox_progress[step] = Sandbox.SandboxProgressItem.json_deserialize(
                    step, launch_progress_json.get(step)
                )

        # TODO(ddovbii): set all needed attributes
        # sb.errors = json_obj.get("errors", [])
        # sb.description = json_obj.get("description", "")
        # sb.status = json_obj.get("sandbox_status", "")
        # sb.launching_progress = json_obj.get("launching_progress", {})
        # sb.__dict__ = json_obj.copy()
        return sb
