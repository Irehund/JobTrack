"""
ui/main_window.py
==================
Main application shell shown after setup is complete.
Contains:
    - Left sidebar with navigation buttons
    - Content area that swaps panels based on navigation
    - Persistent progress bar at the bottom (hidden when idle)
    - Status bar with last-searched timestamp and privacy indicator

Layout:
    ┌─────────────┬──────────────────────────────────┐
    │             │                                  │
    │   Sidebar   │       Content Panel Area         │
    │   Nav       │                                  │
    │             │                                  │
    ├─────────────┴──────────────────────────────────┤
    │  🔒 Private  │  Progress Bar  │  Last searched  │
    └────────────────────────────────────────────────┘
"""

import customtkinter as ctk
from datetime import datetime


class MainWindow(ctk.CTkFrame):
    """
    Main window shell. Instantiated by ui/app.py after setup completes.
    All panels are lazily instantiated on first navigation.
    """

    NAV_ITEMS = [
        ("🏠  Dashboard",    "DashboardPanel",  "dashboard"),
        ("🔍  Job Results",  "JobsPanel",       "jobs"),
        ("🗺️  Map View",     "MapPanel",        "map"),
        ("📋  Tracker",      "TrackerPanel",    "tracker"),
        ("🤖  Assistant",    "AssistantPanel",  "assistant"),
    ]

    PANEL_MODULES = {
        "DashboardPanel": ("ui.panels.dashboard_panel", "DashboardPanel"),
        "JobsPanel":      ("ui.panels.jobs_panel",      "JobsPanel"),
        "MapPanel":       ("ui.panels.map_panel",       "MapPanel"),
        "TrackerPanel":   ("ui.panels.tracker_panel",   "TrackerPanel"),
        "AssistantPanel": ("ui.panels.assistant_panel", "AssistantPanel"),
    }

    def __init__(self, parent, config: dict, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.config = config
        self._active_panel_name: str = ""
        self._panels: dict = {}
        self._nav_buttons: dict = {}
        self._job_results: list = []         # Shared job results across panels
        self._last_search_time: str = "Never"

        self._build_layout()
        self._build_sidebar()
        self._build_bottom_bar()
        self.navigate_to("DashboardPanel")

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_layout(self) -> None:
        """Configure the top-level grid."""
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)   # Bottom bar — fixed height
        self.grid_columnconfigure(0, weight=0)  # Sidebar — fixed width
        self.grid_columnconfigure(1, weight=1)  # Content — expands

        # Sidebar container
        self._sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self._sidebar.grid(row=0, column=0, sticky="nsew")
        self._sidebar.grid_propagate(False)
        self._sidebar.grid_rowconfigure(5, weight=1)  # Spacer row

        # Content panel container
        self._content = ctk.CTkFrame(self, fg_color="transparent")
        self._content.grid(row=0, column=1, sticky="nsew")
        self._content.grid_rowconfigure(0, weight=1)
        self._content.grid_columnconfigure(0, weight=1)

    def _build_sidebar(self) -> None:
        """Build the navigation sidebar."""
        # ── App title ─────────────────────────────────────────────────────────
        ctk.CTkLabel(
            self._sidebar,
            text="JobTrack",
            font=ctk.CTkFont(size=20, weight="bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=16, pady=(24, 4))

        ctk.CTkLabel(
            self._sidebar,
            text="Job Search Manager",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="w",
        ).grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 16))

        # Divider
        ctk.CTkFrame(self._sidebar, height=1, fg_color=("gray80", "gray30")
                     ).grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 8))

        # ── Nav buttons ───────────────────────────────────────────────────────
        nav_frame = ctk.CTkFrame(self._sidebar, fg_color="transparent")
        nav_frame.grid(row=3, column=0, sticky="ew")
        self._sidebar.grid_columnconfigure(0, weight=1)

        for label, panel_class, _ in self.NAV_ITEMS:
            btn = ctk.CTkButton(
                nav_frame,
                text=label,
                anchor="w",
                height=40,
                corner_radius=8,
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray85", "gray25"),
                font=ctk.CTkFont(size=13),
                command=lambda pc=panel_class: self.navigate_to(pc),
            )
            btn.pack(fill="x", padx=8, pady=2)
            self._nav_buttons[panel_class] = btn

        # Spacer
        ctk.CTkFrame(self._sidebar, fg_color="transparent").grid(row=5, column=0, sticky="nsew")

        # ── Bottom sidebar buttons ─────────────────────────────────────────────
        bottom = ctk.CTkFrame(self._sidebar, fg_color="transparent")
        bottom.grid(row=6, column=0, sticky="ew", padx=8, pady=(0, 8))

        # Theme toggle
        from ui.components.theme_toggle import ThemeToggle
        ThemeToggle(bottom, config=self.config).pack(fill="x", pady=2)

        # Settings
        ctk.CTkButton(
            bottom,
            text="⚙️  Preferences",
            anchor="w",
            height=36,
            corner_radius=8,
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray85", "gray25"),
            font=ctk.CTkFont(size=12),
            command=self._open_preferences,
        ).pack(fill="x", pady=2)

        # About
        ctk.CTkButton(
            bottom,
            text="ℹ️  About",
            anchor="w",
            height=36,
            corner_radius=8,
            fg_color="transparent",
            text_color=("gray10", "gray90"),
            hover_color=("gray85", "gray25"),
            font=ctk.CTkFont(size=12),
            command=self._open_about,
        ).pack(fill="x", pady=2)

    def _build_bottom_bar(self) -> None:
        """Build the persistent bottom status/progress bar."""
        bar = ctk.CTkFrame(self, height=36, corner_radius=0,
                           fg_color=("gray85", "gray20"))
        bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        bar.grid_propagate(False)
        bar.grid_columnconfigure(1, weight=1)

        # Privacy indicator
        ctk.CTkLabel(
            bar,
            text="🔒 Your data stays on your computer",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).grid(row=0, column=0, padx=12, pady=8, sticky="w")

        # Progress bar (center) — hidden when not searching
        from ui.components.progress_bar import ProgressBar
        self._progress_bar = ProgressBar(bar)
        self._progress_bar.grid(row=0, column=1, padx=20, pady=6, sticky="ew")

        # Last searched timestamp
        self._status_var = ctk.StringVar(value="Last search: Never")
        ctk.CTkLabel(
            bar,
            textvariable=self._status_var,
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).grid(row=0, column=2, padx=12, pady=8, sticky="e")

    # ── Navigation ────────────────────────────────────────────────────────────

    def navigate_to(self, panel_class_name: str) -> None:
        """Switch the content area to the named panel."""
        # Hide all panels
        for widget in self._content.grid_slaves():
            widget.grid_remove()

        # Highlight active nav button
        for name, btn in self._nav_buttons.items():
            if name == panel_class_name:
                btn.configure(
                    fg_color=("gray75", "gray30"),
                    font=ctk.CTkFont(size=13, weight="bold"),
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    font=ctk.CTkFont(size=13),
                )

        # Lazily instantiate the panel
        if panel_class_name not in self._panels:
            mod_path, cls_name = self.PANEL_MODULES[panel_class_name]
            import importlib
            mod = importlib.import_module(mod_path)
            cls = getattr(mod, cls_name)
            panel = cls(self._content, config=self.config, main_window=self)
            panel.grid(row=0, column=0, sticky="nsew")
            self._panels[panel_class_name] = panel

        self._panels[panel_class_name].grid()
        self._active_panel_name = panel_class_name

    # ── Shared state ──────────────────────────────────────────────────────────

    def set_job_results(self, results: list) -> None:
        """
        Called by DashboardPanel after a search completes.
        Stores results and notifies other panels.
        """
        self._job_results = results
        self._last_search_time = datetime.now().strftime("%I:%M %p")
        self._status_var.set(f"Last search: {self._last_search_time}  •  {len(results)} jobs found")

        # Refresh jobs and map panels if already instantiated
        for name in ("JobsPanel", "MapPanel"):
            if name in self._panels:
                self._panels[name].on_results_updated(results)

    def get_job_results(self) -> list:
        return self._job_results

    def show_progress(self, message: str = "Searching...") -> None:
        """Show the animated progress bar with a message."""
        self._progress_bar.start(message)

    def hide_progress(self) -> None:
        """Hide the progress bar."""
        self._progress_bar.stop()

    # ── Dialogs ───────────────────────────────────────────────────────────────

    def _open_preferences(self) -> None:
        from ui.dialogs.preferences_dialog import PreferencesDialog
        PreferencesDialog(self, config=self.config, on_save=self._on_preferences_saved)

    def _open_about(self) -> None:
        from ui.dialogs.about_dialog import AboutDialog
        AboutDialog(self)

    def _on_preferences_saved(self, updated_config: dict) -> None:
        from core import config_manager
        self.config = updated_config
        config_manager.save(self.config)
