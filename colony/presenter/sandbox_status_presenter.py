import threading
import time

from halo import cursor

from colony.model.sandbox import Sandbox
from colony.rendering.cli_renderer import BaseRenderer
from colony.view.application_shortcut_view import ApplicationShortcutView
from colony.view.application_status_view import ApplicationStatusView
from colony.view.composite_view_layout import CompositeViewLayout
from colony.view.sandbox_progress_item_view import SandboxProgressItemView
from colony.view.status_spinner_view import StatusSpinnerView


class SandboxStatusPresenter:
    WINDOW_TRANSITION_DELAY = 10
    REFRESH_DATA_INTERVAL = 5
    DEFAULT_TIMEOUT = 30

    def __init__(self, sandbox: Sandbox, renderer: BaseRenderer):
        self.renderer = renderer
        self.sandbox = sandbox
        self.active = True
        self.ui_loop = threading.Thread(target=self._ui_loop, daemon=True)
        self.last_window_transition = None
        self.start_time = None
        self.timeout = SandboxStatusPresenter.DEFAULT_TIMEOUT
        self.sandbox_refreshed = False
        self.width, _ = self.renderer.get_terminal_size()

    def _time_to_transition_window(self, ):
        if not self.last_window_transition:
            return True

        return time.time() - self.last_window_transition > SandboxStatusPresenter.WINDOW_TRANSITION_DELAY

    def _ui_loop(self):

        windows_index = -1
        spinner_switch = False
        view_line = None
        current_section = 0
        displayed_shortcuts = []

        while (time.time() - self.start_time) < self.timeout * 60 and self.active:

            cursor.hide()
            time.sleep(0.5)

            self._clear_on_resize()

            if self.sandbox_refreshed:
                app_view_items = [ApplicationStatusView(app) for app in self.sandbox.applications]
                services_view_items = [ApplicationStatusView(service) for service in self.sandbox.services]
                progress_view_items = [SandboxProgressItemView(progress_item) for progress_item in
                                       self.sandbox.sandbox_progress.values()]
                components_view = app_view_items + services_view_items

                app_and_services_section_view = CompositeViewLayout(item_views=components_view, renderer=self.renderer,
                                                                    width_buffer=len(components_view))

                sandbox_progress_section_view = CompositeViewLayout(item_views=progress_view_items,
                                                                    renderer=self.renderer,
                                                                    width_buffer=len(progress_view_items))
                self.sandbox_refreshed = False

            apps_with_shortcuts = [app for app in self.sandbox.applications if app.shortcuts]
            for app in apps_with_shortcuts:
                for shortcut in app.shortcuts:
                    if shortcut not in displayed_shortcuts:
                        shortcut_text = (ApplicationShortcutView(app, shortcut).render())
                        displayed_shortcuts.append(shortcut)
                        self.renderer.clear_current_line()
                        self.renderer.render_to_current_line(shortcut_text)
                        self.renderer.render_new_line("")

            if not view_line or self._time_to_transition_window():
                windows_index += 1
                self.renderer.clear_current_line()

                if current_section == 0:
                    if windows_index >= sandbox_progress_section_view.num_windows():
                        windows_index = 0
                        current_section = 1
                        view_line = app_and_services_section_view.render_display_window(windows_index)

                    else:
                        view_line = sandbox_progress_section_view.render_display_window(windows_index)

                if current_section == 1:
                    if windows_index >= app_and_services_section_view.num_windows():
                        windows_index = 0
                        current_section = 0
                        view_line = sandbox_progress_section_view.render_display_window(windows_index)

                    else:
                        view_line = app_and_services_section_view.render_display_window(windows_index)

                combined_index = current_section * sandbox_progress_section_view.num_windows() + windows_index
                combined_windows = \
                    app_and_services_section_view.num_windows() + sandbox_progress_section_view.num_windows()
                self.last_window_transition = time.time()

            spinner = StatusSpinnerView(items_count=combined_windows, position=combined_index,
                                        blink=spinner_switch).render()

            spinner_width = len(self.renderer.get_stripped_string(spinner))
            view_width = len(self.renderer.get_stripped_string(view_line))
            width, height = self.renderer.get_terminal_size()
            pad = " " * (width - view_width - spinner_width - 1)
            spinner_switch = not spinner_switch

            full_line = f"{view_line}{pad}{spinner}"
            self.renderer.render_to_current_line(full_line)

    def _clear_on_resize(self):
        width, _ = self.renderer.get_terminal_size()
        if width != self.width:
            self.renderer.clear()
            self.renderer.restore_from_buffer()

    def stop_showing_status(self):
        self.active = False
        self.ui_loop.join()

    def update_sandbox(self, sandbox: Sandbox):
        self.sandbox = sandbox
        self.sandbox_refreshed = True

    def start_showing_status(self, timeout: int):
        self.start_time = time.time()
        self.sandbox_refreshed = True
        self.timeout = timeout
        self.active = True
        self.ui_loop.start()
