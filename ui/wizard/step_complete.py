"""
ui/wizard/step_complete.py
===========================
Step 7: Setup complete — summary and launch button.
"""

import customtkinter as ctk
from ui.wizard.base_step import BaseStep
from core.utils import format_salary


class StepComplete(BaseStep):
    TITLE = "You're All Set!"
    SUBTITLE = "Here's a summary of your setup. Everything can be changed later in Preferences."
    NEXT_LABEL = "🚀  Start Searching"

    def _build_content(self, frame):
        self._summary_frame = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        self._summary_frame.pack(fill="both", expand=True)

    def on_enter(self):
        """Rebuild the summary every time this step is shown."""
        super().on_enter()
        for w in self._summary_frame.winfo_children():
            w.destroy()
        self._build_summary()

    def _build_summary(self):
        f = self._summary_frame

        def section(title, items):
            card = ctk.CTkFrame(f, fg_color=("gray90", "gray20"), corner_radius=10)
            card.pack(fill="x", pady=5)
            ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=13, weight="bold"),
                         anchor="w").pack(fill="x", padx=16, pady=(12, 4))
            for label, value in items:
                row = ctk.CTkFrame(card, fg_color="transparent")
                row.pack(fill="x", padx=16, pady=2)
                ctk.CTkLabel(row, text=label, width=160, anchor="w",
                             text_color="gray", font=ctk.CTkFont(size=12)).pack(side="left")
                ctk.CTkLabel(row, text=str(value), anchor="w",
                             font=ctk.CTkFont(size=12)).pack(side="left")
            ctk.CTkFrame(card, fg_color="transparent", height=6).pack()

        # Location
        loc = self.config.get("location", {})
        city  = loc.get("city", "")
        state = loc.get("state", "")
        zip_  = loc.get("zip", "")
        loc_str = f"{city}, {state} {zip_}".strip().strip(",")
        section("📍  Location", [
            ("Home location",   loc_str or "Not set"),
            ("Search radius",   f"{self.config.get('search_radius_miles', 50)} miles"),
        ])

        # Providers
        providers = self.config.get("providers", {})
        enabled = [pid.capitalize() for pid, v in providers.items() if v.get("enabled")]
        section("🔍  Job Sources", [
            ("Searching",  ", ".join(enabled) if enabled else "USAJobs only"),
        ])

        # Preferences
        prefs = self.config.get("job_preferences", {})
        kw = ", ".join(prefs.get("keywords", [])) or "None (will show all jobs)"
        section("⚙️  Search Preferences", [
            ("Keywords",          kw),
            ("Work arrangement",  prefs.get("work_type", "any").capitalize()),
            ("Experience level",  prefs.get("experience_level", "any").capitalize()),
        ])

        # Tracker
        mode = self.config.get("tracker", {}).get("mode", "local")
        mode_labels = {"local": "Local file (on this computer)",
                       "google": "Google Sheets", "both": "Both (local + Google Sheets)"}
        section("📋  Application Tracker", [
            ("Storage",  mode_labels.get(mode, mode)),
        ])

    def validate(self) -> tuple[bool, str]:
        return True, ""

    def on_exit(self):
        self.controller.complete()
