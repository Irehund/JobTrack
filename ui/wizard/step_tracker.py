"""
ui/wizard/step_tracker.py
==========================
Step 6: Application tracker storage selection.
"""

import customtkinter as ctk
from ui.wizard.base_step import BaseStep


TRACKER_OPTIONS = [
    {
        "value": "local",
        "title": "Local File  (Recommended)",
        "desc":  "Saved only on this computer. No account needed. Works offline. "
                 "Your data never leaves your machine.",
        "icon":  "💾",
    },
    {
        "value": "google",
        "title": "Google Sheets",
        "desc":  "Synced to a spreadsheet in your Google Drive. "
                 "Access your tracker from any device. Requires a Gmail account.",
        "icon":  "📊",
    },
    {
        "value": "both",
        "title": "Both  (Local + Google Sheets)",
        "desc":  "Saves locally and syncs to Google Sheets. "
                 "Local file acts as a backup if Google is unavailable.",
        "icon":  "🔄",
    },
]


class StepTracker(BaseStep):
    TITLE = "How Would You Like to Track Your Applications?"
    SUBTITLE = "Choose where JobTrack saves the jobs you apply to."

    def _build_content(self, frame):
        current = self.config.get("tracker", {}).get("mode", "local")
        self._tracker_var = ctk.StringVar(value=current)

        for option in TRACKER_OPTIONS:
            self._build_option_card(frame, option)

    def _build_option_card(self, parent, option: dict):
        card = ctk.CTkFrame(parent, fg_color=("gray90", "gray20"), corner_radius=10)
        card.pack(fill="x", pady=6)
        card.grid_columnconfigure(1, weight=1)

        rb = ctk.CTkRadioButton(
            card, text="",
            variable=self._tracker_var,
            value=option["value"],
            command=self._on_change,
        )
        rb.grid(row=0, column=0, rowspan=2, padx=(16, 4), pady=16)

        ctk.CTkLabel(card, text=f"{option['icon']}  {option['title']}",
                     font=ctk.CTkFont(size=14, weight="bold"), anchor="w",
                     ).grid(row=0, column=1, sticky="w", padx=4, pady=(16, 2))

        ctk.CTkLabel(card, text=option["desc"],
                     font=ctk.CTkFont(size=12), text_color="gray",
                     anchor="w", wraplength=580, justify="left",
                     ).grid(row=1, column=1, sticky="w", padx=4, pady=(0, 16))

    def _on_change(self):
        mode = self._tracker_var.get()
        if "tracker" not in self.config:
            self.config["tracker"] = {}
        self.config["tracker"]["mode"] = mode

    def on_exit(self):
        self._on_change()
