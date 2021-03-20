from colorama import Fore

from colony.model.sandbox import Sandbox
from colony.view.application_status_view import ApplicationStatusView
from colony.view.service_status_view import ServiceStatusView


class ApplicationsAndServicesStatusView(object):
    def __init__(self, applications: [Sandbox.Application], services: [Sandbox.Service]):
        self.services = services
        self.applications = applications

    def render(self) -> str:
        app_statuses = [ApplicationStatusView(app).render() for app in self.applications]
        service_statuses = [ServiceStatusView(service).render() for service in self.services]

        return f" {Fore.CYAN}|{Fore.RESET} ".join(app_statuses + service_statuses)
