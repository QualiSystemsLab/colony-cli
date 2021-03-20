from colorama import Fore

from colony.model.sandbox import Sandbox
from colony.view.application_status_view import ApplicationStatusView


class ApplicationsStatusView(object):
    def __init__(self, applications: [Sandbox.Application]):
        self.applications = applications

    def render(self) -> str:
        app_statuses = [ApplicationStatusView(app).render() for app in self.applications]
        return f" {Fore.CYAN}|{Fore.RESET} ".join(app_statuses)
