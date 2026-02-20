"""
ui/app.py
==========
Root CustomTkinter application class.
Initializes the theme, loads config, and decides whether to show
the setup wizard (first run) or the main window (returning user).
"""

import customtkinter as ctk
from core import config_manager

APP_NAME = "JobTrack"
APP_VERSION = "1.0.0"
WINDOW_MIN_WIDTH = 1100
WINDOW_MIN_HEIGHT = 700


class JobTrackApp(ctk.CTk):
    """Root application window."""

    def __init__(self):
        super().__init__()

        self.config = config_manager.load()
        self._apply_theme(self.config.get("theme", "system"))

        self.title(APP_NAME)
        self.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self._center_window(1200, 750)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        if not self.config.get("setup_complete", False):
            self._show_wizard()
        else:
            self._show_main_window()

    def _apply_theme(self, theme: str) -> None:
        valid = {"light", "dark", "system"}
        ctk.set_appearance_mode(theme if theme in valid else "system")
        ctk.set_default_color_theme("blue")

    def _show_wizard(self) -> None:
        from ui.wizard.wizard_controller import WizardController
        self._current_view = WizardController(
            self,
            config=self.config,
            on_complete=self.on_wizard_complete,
        )
        self._current_view.grid(row=0, column=0, sticky="nsew")

    def _show_main_window(self) -> None:
        from ui.main_window import MainWindow
        self._current_view = MainWindow(self, config=self.config)
        self._current_view.grid(row=0, column=0, sticky="nsew")

    def on_wizard_complete(self, updated_config: dict) -> None:
        """Called by WizardController when setup finishes."""
        self.config = updated_config
        config_manager.save(self.config)
        # Destroy wizard and launch main window
        self._current_view.destroy()
        self._show_main_window()

    def _center_window(self, width: int, height: int) -> None:
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - width) // 2
        y = (screen_h - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")
