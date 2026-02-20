"""
ui/panels/jobs_panel.py
========================
Job Results panel — scrollable list of JobListing cards with filter bar.
"""

import customtkinter as ctk
from core.job_model import JobListing


class JobsPanel(ctk.CTkFrame):
    """Scrollable list of job results with filter controls."""

    def __init__(self, parent, config: dict, main_window, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.config = config
        self.main_window = main_window
        self._all_results: list[JobListing] = []
        self._build()

    def _build(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ── Filter bar ────────────────────────────────────────────────────────
        filter_bar = ctk.CTkFrame(self, fg_color=("gray90", "gray20"), corner_radius=0, height=54)
        filter_bar.grid(row=0, column=0, sticky="ew")
        filter_bar.grid_propagate(False)

        ctk.CTkLabel(filter_bar, text="Filter:",
                     font=ctk.CTkFont(size=13)).pack(side="left", padx=(16, 4), pady=14)

        self._work_filter = ctk.CTkSegmentedButton(
            filter_bar,
            values=["All", "Remote", "Hybrid", "On-site"],
            command=self._apply_filters,
        )
        self._work_filter.set("All")
        self._work_filter.pack(side="left", padx=8, pady=10)

        self._exp_filter = ctk.CTkOptionMenu(
            filter_bar,
            values=["Any Level", "Entry", "Mid", "Senior"],
            command=self._apply_filters,
            width=120,
        )
        self._exp_filter.pack(side="left", padx=8, pady=10)

        self._result_count = ctk.CTkLabel(
            filter_bar, text="0 jobs found",
            font=ctk.CTkFont(size=12), text_color="gray")
        self._result_count.pack(side="right", padx=16)

        # ── Job card list ─────────────────────────────────────────────────────
        self._job_list = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._job_list.grid(row=1, column=0, sticky="nsew", padx=16, pady=12)
        self._job_list.grid_columnconfigure(0, weight=1)

        self._show_empty_state()

    def _show_empty_state(self):
        for w in self._job_list.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self._job_list,
            text="No results yet.\nGo to the Dashboard and click 'Search for Jobs Now' to get started.",
            font=ctk.CTkFont(size=14), text_color="gray",
            justify="center",
        ).grid(row=0, column=0, pady=80)

    def on_results_updated(self, results: list):
        """Called by main_window when a new search completes."""
        self._all_results = results
        self._apply_filters()

    def _apply_filters(self, *_):
        """Filter and re-render the job card list."""
        work = self._work_filter.get()
        exp  = self._exp_filter.get()

        filtered = self._all_results
        if work == "Remote":
            filtered = [j for j in filtered if j.is_remote]
        elif work == "Hybrid":
            filtered = [j for j in filtered if j.is_hybrid]
        elif work == "On-site":
            filtered = [j for j in filtered if not j.is_remote and not j.is_hybrid]

        exp_map = {"Entry": "entry", "Mid": "mid", "Senior": "senior"}
        if exp in exp_map:
            filtered = [j for j in filtered if j.experience_level == exp_map[exp]]

        self._render_results(filtered)
        self._result_count.configure(text=f"{len(filtered)} jobs found")

    def _render_results(self, jobs: list):
        for w in self._job_list.winfo_children():
            w.destroy()

        if not jobs:
            ctk.CTkLabel(
                self._job_list,
                text="No jobs match the current filters.",
                font=ctk.CTkFont(size=14), text_color="gray",
            ).grid(row=0, column=0, pady=40)
            return

        from ui.components.job_card import JobCard
        for i, job in enumerate(jobs):
            card = JobCard(self._job_list, job=job, main_window=self.main_window)
            card.grid(row=i, column=0, sticky="ew", pady=4, padx=4)
