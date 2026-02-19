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

        # Load config and apply theme before any widgets are created
        self.config = config_manager.load()
        self._apply_theme(self.config.get("theme", "system"))

        self.title(APP_NAME)
        self.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self._center_window(1200, 750)

        # Route to wizard or main window
        if not self.config.get("setup_complete", False):
            self._show_wizard()
        else:
            self._show_main_window()

    def _apply_theme(self, theme: str) -> None:
        """
        Apply the selected theme.
        theme: "light" | "dark" | "system"
        """
        # TODO: Call ctk.set_appearance_mode(theme)
        # CustomTkinter handles "system" automatically on Windows/macOS
        raise NotImplementedError

    def _show_wizard(self) -> None:
        """Load the first-run setup wizard as the app's content."""
        # TODO: Import and instantiate WizardController, add to self
        raise NotImplementedError

    def _show_main_window(self) -> None:
        """Load the main application window."""
        # TODO: Import and instantiate MainWindow, add to self
        raise NotImplementedError

    def on_wizard_complete(self, updated_config: dict) -> None:
        """
        Called by WizardController when setup finishes.
        Switches from the wizard to the main window.
        """
        # TODO: Save updated_config, destroy wizard, show main window
        raise NotImplementedError

    def _center_window(self, width: int, height: int) -> None:
        """Center the window on the primary screen."""
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - width) // 2
        y = (screen_h - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")
