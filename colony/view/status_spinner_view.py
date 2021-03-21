from colorama import Fore


class StatusSpinnerView:
    SELECTED_COLOR = Fore.GREEN

    def __init__(self, items_count: int, position: int, blink: bool):
        self.blink = blink
        self.position = position
        self.items_count = items_count

    def _regular_before_dots(self):
        if self.position > 0:
            return "." * self.position
        return ""

    def _regular_after_dots(self):
        if (self.position + 1) < self.items_count:
            return "." * (self.items_count - (self.position + 1))
        return ""

    def _selected_dot(self):
        if self.blink:
            return " "
        else:
            return StatusSpinnerView.SELECTED_COLOR + "." + Fore.RESET

    def render(self):
        return self._regular_before_dots() + self._selected_dot() + self._regular_after_dots()
