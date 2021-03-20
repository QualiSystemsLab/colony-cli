from colorama import Fore

from colony.model.sandbox import Sandbox
from colony.view.sandbox_progress_item_view import SandboxProgressItemView


class SandboxProgressItemsView(object):
    def __init__(self, progress_items: [Sandbox.SandboxProgressItem]):
        self.progress_items = progress_items

    def render(self) -> str:
        progress_statuses = [SandboxProgressItemView(item).render() for item in self.progress_items.values()]
        return f" {Fore.CYAN}|{Fore.RESET} ".join(progress_statuses)
