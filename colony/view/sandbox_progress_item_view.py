from colorama import Back, Fore

from colony.model.sandbox import Sandbox

STATUS_BACK_COLOR_CODE = {"Pending": Back.LIGHTBLACK_EX, "InProgress": Back.YELLOW, "Done": Back.GREEN}


class SandboxProgressItemView(object):
    def __init__(self, progress_item: Sandbox.SandboxProgressItem):
        self.progress_item = progress_item

    def _in_progress_color(self, status):
        if self.progress_item.failed:
            return Fore.RED
        if self.progress_item.succeeded:
            return Fore.GREEN
        else:
            return self._get_contrast_color(status)

    def _get_contrast_color(self, status):
        if STATUS_BACK_COLOR_CODE.get(status, Back.RESET) == Back.YELLOW:
            return Fore.BLACK
        else:
            return Fore.RESET

    def render(self):
        status = self.progress_item.status
        return (
            f"{STATUS_BACK_COLOR_CODE.get(status, Back.RESET)}{self._in_progress_color(status)}"
            f"{self.progress_item.name} "
            f"{self.progress_item.succeeded + self.progress_item.failed}{self._get_contrast_color(status)}/"
            f"{self.progress_item.total}{Fore.RESET}{Back.RESET} "
        )
