from colorama import Back, Style

from colony.model.sandbox import Sandbox

STATUS_COLOR_CODE = {"Pending": Back.LIGHTBLACK_EX, "Deploying": Back.YELLOW, "Error": Back.RED, "Setup": Back.YELLOW}


class ApplicationStatusView(object):
    def __init__(self, app):
        self.app = app

    @staticmethod
    def app_status_to_colored_string(status: str):
        return STATUS_COLOR_CODE.get(status, Back.GREEN) + status + Style.RESET_ALL

    def render(self) -> str:
        return f"{STATUS_COLOR_CODE.get(self.app.status, Back.GREEN)}{self.app.name}{Back.RESET}"
