from colorama import Fore

from colony.rendering.cli_renderer import BaseRenderer

SEPARATOR = f" {Fore.CYAN}|{Fore.RESET} "


class CompositeViewLayout:

    def __init__(self, renderer: BaseRenderer, item_views, width_buffer: int):
        self.width_buffer = width_buffer
        self.item_views = item_views
        self.renderer = renderer
        self.windows = []
        self.last_window_render = None
        self.calculate_display_windows()

    def num_windows(self):
        return len(self.windows)

    def calculate_display_windows(self):
        display_width, display_height = self.renderer.get_terminal_size()
        width = display_width - self.width_buffer
        window = []
        self.windows.append(window)
        size = 0
        for view in self.item_views:
            # Add the separator after first app only
            if size > 0:
                size += len(self.renderer.get_stripped_string(SEPARATOR))

            # Calculate length to get window
            app_text = self.renderer.get_stripped_string(view.render())
            size += len(app_text)
            if size >= width:
                window = []
                self.windows.append(window)
                size = 0
            window.append(view)

    def render_display_window(self, current_window: int) -> str:
        window = self.windows[current_window]
        item_renders = [item.render() for item in window]
        return SEPARATOR.join(item_renders)

