"""
ui/main_window.py
==================
Main application shell shown after setup is complete.
Contains:
    - Left sidebar with navigation buttons
    - Content area that swaps panels based on navigation
    - Persistent progress bar at the bottom (hidden when idle)
    - Status bar with last-searched timestamp and privacy indicator
"""

import customtkinter as ctk


class MainWindow(ctk.CTkFrame):
    """
    Main window shell. Instantiated by ui/app.py after setup completes.

    Layout:
        ┌─────────────┬──────────────────────────────────┐
        │             │                                  │
        │   Sidebar   │       Content Panel Area         │
        │   Nav       │                                  │
        │             │                                  │
        ├─────────────┴──────────────────────────────────┤
        │  Privacy indicator  │  Progress Bar  │ Status  │
        └────────────────────────────────────────────────┘
    """

    # Navigation items: (label, panel_class_name, icon_name)
    NAV_ITEMS = [
        ("Dashboard",   "DashboardPanel",   "home"),
        ("Job Results", "JobsPanel",        "search"),
        ("Map View",    "MapPanel",         "map"),
        ("Tracker",     "TrackerPanel",     "clipboard"),
        ("Assistant",   "AssistantPanel",   "chat"),
    ]

    def __init__(self, parent, config: dict, **kwargs):
        super().__init__(parent, **kwargs)
        self.config = config
        self._active_panel = None
        self._panels: dict = {}

        self._build_layout()
        self._build_sidebar()
        self._build_bottom_bar()
        self.navigate_to("Dashboard")

    def _build_layout(self) -> None:
        """Create the top-level grid: sidebar left, content right, bottom bar."""
        # TODO: Configure grid rows/columns, create sidebar frame and content frame
        raise NotImplementedError

    def _build_sidebar(self) -> None:
        """Build the navigation sidebar with app logo and nav buttons."""
        # TODO: Add app name label, nav buttons for each NAV_ITEM
        # Add Settings gear and About buttons at the bottom of the sidebar
        raise NotImplementedError

    def _build_bottom_bar(self) -> None:
        """
        Build the persistent bottom status/progress bar.
        Contains:
            - Privacy lock icon + "Your data stays on your computer" label (left)
            - Progress bar (center, hidden when idle)
            - Last searched timestamp (right)
        """
        # TODO: Create bottom frame with three sections
        # Import and embed the ProgressBar component
        raise NotImplementedError

    def navigate_to(self, panel_name: str) -> None:
        """
        Switch the content area to the named panel.
        Lazily instantiates panels on first visit.
        """
        # TODO: Hide current panel, show or create named panel
        raise NotImplementedError

    def show_progress(self, percent: float, label: str = "") -> None:
        """
        Update the bottom progress bar.
        percent=0 hides the bar. percent=100 briefly shows then hides.
        """
        # TODO: Delegate to the ProgressBar component
        raise NotImplementedError

    def open_preferences(self) -> None:
        """Open the Preferences dialog as a modal window."""
        # TODO: Import and instantiate PreferencesDialog
        raise NotImplementedError
