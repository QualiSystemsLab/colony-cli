import emoji
from colorama import Fore, Style

from colony.model.sandbox import Sandbox


class ApplicationShortcutView(object):
    def __init__(self, app: Sandbox.Application, shortcut: str):
        self.app = app
        self.shortcut = shortcut

    def render(self) -> str:
        return (
            f"{emoji.emojize(':globe_with_meridians:', use_aliases=True)} "
            f"{Fore.BLUE}{self.shortcut}{Fore.RESET} {Style.DIM}[{self.app.name}]{Style.RESET_ALL}"
        )
