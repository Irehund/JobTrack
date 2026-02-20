"""
ui/panels/dashboard_panel.py
==============================
Dashboard panel — the home screen.
Shows application stats, a Search Now button, and recent activity.
"""

import threading
import customtkinter as ctk
from db import jobs_repo


class DashboardPanel(ctk.CTkFrame):
    """Home screen shown after setup. Entry point for job searches."""

    def __init__(self, parent, config: dict, main_window, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.config = config
        self.main_window = main_window
        self._build()
        self.refresh_stats()

    def _build(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ── Header ────────────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=32, pady=(32, 0))

        loc = self.config.get("location", {})
        city  = loc.get("city", "")
        state = loc.get("state", "")
        radius = self.config.get("search_radius_miles", 50)
        loc_str = f"{city}, {state}" if city and state else "your area"

        ctk.CTkLabel(
            header, text="Good to see you!",
            font=ctk.CTkFont(size=28, weight="bold"), anchor="w",
        ).pack(fill="x")
        ctk.CTkLabel(
            header,
            text=f"Searching within {radius} miles of {loc_str}",
            font=ctk.CTkFont(size=14), text_color="gray", anchor="w",
        ).pack(fill="x", pady=(4, 0))

        # ── Search button ─────────────────────────────────────────────────────
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.grid(row=1, column=0, sticky="n", padx=32, pady=24)

        self._search_btn = ctk.CTkButton(
            search_frame,
            text="🔍  Search for Jobs Now",
            font=ctk.CTkFont(size=16),
            height=52,
            width=280,
            command=self._run_search,
        )
        self._search_btn.pack()

        kw = self.config.get("job_preferences", {}).get("keywords", [])
        kw_str = ", ".join(kw) if kw else "all cybersecurity jobs"
        ctk.CTkLabel(
            search_frame,
            text=f"Searching for: {kw_str}",
            font=ctk.CTkFont(size=12), text_color="gray",
        ).pack(pady=(8, 0))

        # ── Stats row ─────────────────────────────────────────────────────────
        self._stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._stats_frame.grid(row=2, column=0, sticky="ew", padx=32, pady=(0, 16))

        # ── Recent activity ───────────────────────────────────────────────────
        recent_card = ctk.CTkFrame(self, fg_color=("gray90", "gray20"), corner_radius=10)
        recent_card.grid(row=3, column=0, sticky="nsew", padx=32, pady=(0, 32))
        recent_card.grid_rowconfigure(1, weight=1)
        recent_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            recent_card, text="Recent Applications",
            font=ctk.CTkFont(size=15, weight="bold"), anchor="w",
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 8))

        self._recent_frame = ctk.CTkScrollableFrame(
            recent_card, fg_color="transparent", height=180)
        self._recent_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))
        self._recent_frame.grid_columnconfigure(0, weight=1)

    def refresh_stats(self):
        """Pull fresh stats from DB and update the stats row."""
        try:
            stats = jobs_repo.get_stats()
        except Exception:
            stats = {"total": 0, "by_status": {}}

        # Clear and rebuild stats row
        for w in self._stats_frame.winfo_children():
            w.destroy()

        stat_items = [
            ("Total Applied",    str(stats["total"])),
            ("Interviews",       str(stats["by_status"].get("Interview Scheduled", 0) +
                                     stats["by_status"].get("Interview Completed", 0))),
            ("Offers",           str(stats["by_status"].get("Offer Received", 0))),
            ("No Response",      str(stats["by_status"].get("No Response", 0))),
        ]

        for label, value in stat_items:
            card = ctk.CTkFrame(self._stats_frame,
                                fg_color=("gray90", "gray20"), corner_radius=10)
            card.pack(side="left", expand=True, fill="x", padx=6, pady=4)
            ctk.CTkLabel(card, text=value,
                         font=ctk.CTkFont(size=28, weight="bold")).pack(pady=(14, 2))
            ctk.CTkLabel(card, text=label,
                         font=ctk.CTkFont(size=12), text_color="gray").pack(pady=(0, 14))

        # Recent applications
        self._refresh_recent()

    def _refresh_recent(self):
        for w in self._recent_frame.winfo_children():
            w.destroy()
        try:
            apps = jobs_repo.get_all_applications()[:5]
        except Exception:
            apps = []

        if not apps:
            ctk.CTkLabel(
                self._recent_frame,
                text="No applications yet. Run a search and start applying!",
                text_color="gray", font=ctk.CTkFont(size=13),
            ).grid(row=0, column=0, pady=20)
            return

        for app in apps:
            row = ctk.CTkFrame(self._recent_frame, fg_color="transparent")
            row.grid(sticky="ew", pady=2)
            row.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(row, text=app["title"], anchor="w",
                         font=ctk.CTkFont(size=13, weight="bold"), width=220,
                         ).grid(row=0, column=0, sticky="w")
            ctk.CTkLabel(row, text=app["company"], anchor="w",
                         font=ctk.CTkFont(size=12), text_color="gray",
                         ).grid(row=0, column=1, sticky="w", padx=8)
            ctk.CTkLabel(row, text=app["status"], anchor="e",
                         font=ctk.CTkFont(size=12),
                         ).grid(row=0, column=2, sticky="e")

    def _run_search(self):
        """Kick off a job search in a background thread."""
        self._search_btn.configure(state="disabled", text="⟳  Searching...")
        self.main_window.show_progress("Searching for jobs...")

        def _search():
            try:
                from core.job_fetcher import fetch_all
                results = fetch_all(self.config)
                self.main_window.set_job_results(results)
                # Navigate to results panel
                self.main_window.navigate_to("JobsPanel")
            except Exception as e:
                print(f"Search error: {e}")
            finally:
                self._search_btn.configure(state="normal", text="🔍  Search for Jobs Now")
                self.main_window.hide_progress()
                self.refresh_stats()

        threading.Thread(target=_search, daemon=True).start()

    def on_results_updated(self, results: list):
        """Called by main_window when new results arrive."""
        self.refresh_stats()
