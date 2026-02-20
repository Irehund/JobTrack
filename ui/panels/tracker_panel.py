"""
ui/panels/tracker_panel.py
===========================
Application tracker panel — shows all applied jobs with status dropdowns
and a timeline view of each application's progress.
"""

import customtkinter as ctk
from db import jobs_repo


class TrackerPanel(ctk.CTkFrame):
    """Tracks job applications with status history."""

    def __init__(self, parent, config: dict, main_window, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.config = config
        self.main_window = main_window
        self._build()
        self.refresh()

    def _build(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Toolbar
        toolbar = ctk.CTkFrame(self, fg_color=("gray90", "gray20"),
                               corner_radius=0, height=54)
        toolbar.grid(row=0, column=0, sticky="ew")
        toolbar.grid_propagate(False)

        ctk.CTkLabel(toolbar, text="📋  Application Tracker",
                     font=ctk.CTkFont(size=15, weight="bold"),
                     ).pack(side="left", padx=16, pady=14)

        ctk.CTkButton(toolbar, text="↻  Refresh",
                      width=90, height=32, command=self.refresh,
                      ).pack(side="right", padx=8, pady=10)

        # Application list
        self._list = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._list.grid(row=1, column=0, sticky="nsew", padx=16, pady=12)
        self._list.grid_columnconfigure(0, weight=1)

    def refresh(self):
        """Reload all applications from DB."""
        for w in self._list.winfo_children():
            w.destroy()

        try:
            apps = jobs_repo.get_all_applications()
        except Exception:
            apps = []

        if not apps:
            ctk.CTkLabel(
                self._list,
                text="No applications tracked yet.\n"
                     "Find a job you like and click 'Mark as Applied' to start tracking.",
                font=ctk.CTkFont(size=14), text_color="gray", justify="center",
            ).grid(row=0, column=0, pady=60)
            return

        # Column headers
        header = ctk.CTkFrame(self._list, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        for i, (text, w) in enumerate([
            ("Job Title", 220), ("Company", 180), ("Location", 140), ("Status", 160), ("Applied", 100)
        ]):
            ctk.CTkLabel(header, text=text, width=w, anchor="w",
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color="gray").grid(row=0, column=i, padx=4)

        for i, app in enumerate(apps, 1):
            self._build_app_row(i, app)

    def _build_app_row(self, row_idx: int, app: dict):
        from ui.components.status_dropdown import StatusDropdown

        row = ctk.CTkFrame(self._list,
                           fg_color=("gray90", "gray20") if row_idx % 2 == 0 else "transparent",
                           corner_radius=6)
        row.grid(row=row_idx, column=0, sticky="ew", pady=2)

        ctk.CTkLabel(row, text=app["title"], width=220, anchor="w",
                     font=ctk.CTkFont(size=13)).grid(row=0, column=0, padx=4, pady=8)
        ctk.CTkLabel(row, text=app["company"], width=180, anchor="w",
                     font=ctk.CTkFont(size=12), text_color="gray",
                     ).grid(row=0, column=1, padx=4)
        ctk.CTkLabel(row, text=app.get("location",""), width=140, anchor="w",
                     font=ctk.CTkFont(size=12), text_color="gray",
                     ).grid(row=0, column=2, padx=4)

        # Status dropdown — auto-timestamps on change
        status_dd = StatusDropdown(
            row, application_id=app["id"],
            current_status=app["status"],
            on_change=lambda: self.refresh(),
        )
        status_dd.grid(row=0, column=3, padx=4)

        date_str = app.get("date_applied","")[:10] if app.get("date_applied") else ""
        ctk.CTkLabel(row, text=date_str, width=100, anchor="w",
                     font=ctk.CTkFont(size=12), text_color="gray",
                     ).grid(row=0, column=4, padx=4)

    def on_results_updated(self, results: list):
        pass  # Tracker doesn't need search results
