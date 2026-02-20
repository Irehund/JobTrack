"""
ui/wizard/step_providers.py
=============================
Step 2: Job provider selection.
USAJobs locked on. Others are opt-in checkboxes.
"""

import customtkinter as ctk
from ui.wizard.base_step import BaseStep


PROVIDERS = [
    {
        "id": "usajobs",
        "name": "USAJobs (Federal Government)",
        "desc": "The official US federal job board. Free, always on, no approval needed.",
        "locked": True,
        "free": True,
    },
    {
        "id": "indeed",
        "name": "Indeed",
        "desc": "One of the largest job boards. Requires a free Publisher API key.",
        "locked": False,
        "free": False,
    },
    {
        "id": "linkedin",
        "name": "LinkedIn",
        "desc": "Professional network job listings. Requires a developer application.",
        "locked": False,
        "free": False,
    },
    {
        "id": "glassdoor",
        "name": "Glassdoor",
        "desc": "Job listings with company reviews and salary data.",
        "locked": False,
        "free": False,
    },
    {
        "id": "adzuna",
        "name": "Adzuna",
        "desc": "Aggregates listings from across the web. Free tier available.",
        "locked": False,
        "free": True,
    },
]


class StepProviders(BaseStep):
    TITLE = "Choose Your Job Sources"
    SUBTITLE = "USAJobs is always included. Select any additional sources you'd like to search."

    def _build_content(self, frame):
        self._checkboxes: dict[str, ctk.BooleanVar] = {}

        for provider in PROVIDERS:
            pid = provider["id"]
            current = self.config.get("providers", {}).get(pid, {}).get("enabled", provider["locked"])

            row = ctk.CTkFrame(frame, fg_color=("gray90", "gray20"), corner_radius=10)
            row.pack(fill="x", pady=5)
            row.grid_columnconfigure(1, weight=1)

            if provider["locked"]:
                # Lock icon — always on
                ctk.CTkLabel(row, text="🔒", font=ctk.CTkFont(size=18), width=44).grid(
                    row=0, column=0, rowspan=2, padx=(14, 4), pady=12)
            else:
                var = ctk.BooleanVar(value=current)
                self._checkboxes[pid] = var
                cb = ctk.CTkCheckBox(row, text="", variable=var, width=44,
                                     command=self._on_toggle)
                cb.grid(row=0, column=0, rowspan=2, padx=(14, 4), pady=12)

            name_label = ctk.CTkLabel(
                row, text=provider["name"],
                font=ctk.CTkFont(size=14, weight="bold"), anchor="w")
            name_label.grid(row=0, column=1, sticky="w", padx=4, pady=(12, 0))

            desc_label = ctk.CTkLabel(
                row, text=provider["desc"],
                font=ctk.CTkFont(size=12), text_color="gray", anchor="w")
            desc_label.grid(row=1, column=1, sticky="w", padx=4, pady=(0, 12))

            badge_text = "✓ Free" if provider["free"] else "API Key Required"
            badge_color = "#4CAF50" if provider["free"] else "#FF9800"
            ctk.CTkLabel(row, text=badge_text, font=ctk.CTkFont(size=11),
                         text_color=badge_color).grid(row=0, column=2, padx=14, pady=12)

    def _on_toggle(self):
        """Save checkbox state to config immediately on toggle."""
        for pid, var in self._checkboxes.items():
            if "providers" not in self.config:
                self.config["providers"] = {}
            if pid not in self.config["providers"]:
                self.config["providers"][pid] = {}
            self.config["providers"][pid]["enabled"] = var.get()

    def on_exit(self):
        self._on_toggle()  # Ensure final state is saved
