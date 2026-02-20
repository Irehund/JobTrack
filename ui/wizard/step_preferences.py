"""
ui/wizard/step_preferences.py
================================
Step 5: Job search preferences — keywords, work type, experience level.
"""

import customtkinter as ctk
from ui.wizard.base_step import BaseStep


class StepPreferences(BaseStep):
    TITLE = "What Kind of Jobs Are You Looking For?"
    SUBTITLE = "These filters will be applied to every search. You can change them anytime in Preferences."

    def _build_content(self, frame):
        frame.grid_columnconfigure(0, weight=1)

        # ── Keywords ──────────────────────────────────────────────────────────
        kw_card = ctk.CTkFrame(frame, fg_color=("gray90", "gray20"), corner_radius=10)
        kw_card.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(kw_card, text="Job Title Keywords",
                     font=ctk.CTkFont(size=14, weight="bold"), anchor="w",
                     ).pack(fill="x", padx=16, pady=(14, 4))
        ctk.CTkLabel(kw_card,
                     text="Enter job titles or keywords to search for. Separate multiple entries with commas.",
                     font=ctk.CTkFont(size=12), text_color="gray", anchor="w",
                     ).pack(fill="x", padx=16, pady=(0, 8))

        existing_kw = ", ".join(self.config.get("job_preferences", {}).get("keywords", []))
        self._keywords_entry = ctk.CTkEntry(
            kw_card,
            placeholder_text="e.g. SOC Analyst, Security Analyst, Intelligence Analyst",
            height=36,
        )
        self._keywords_entry.pack(fill="x", padx=16, pady=(0, 14))
        if existing_kw:
            self._keywords_entry.insert(0, existing_kw)

        # ── Work type ─────────────────────────────────────────────────────────
        wt_card = ctk.CTkFrame(frame, fg_color=("gray90", "gray20"), corner_radius=10)
        wt_card.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(wt_card, text="Work Arrangement",
                     font=ctk.CTkFont(size=14, weight="bold"), anchor="w",
                     ).pack(fill="x", padx=16, pady=(14, 8))

        self._work_type_var = ctk.StringVar(
            value=self.config.get("job_preferences", {}).get("work_type", "any")
        )
        work_options = [
            ("any",    "Any",       "Show all listings regardless of work arrangement"),
            ("remote", "Remote",    "Only show fully remote positions"),
            ("hybrid", "Hybrid",    "Only show hybrid (some in-office) positions"),
            ("onsite", "On-site",   "Only show fully in-office positions"),
        ]
        btn_frame = ctk.CTkFrame(wt_card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=16, pady=(0, 14))
        for value, label, tooltip in work_options:
            rb = ctk.CTkRadioButton(btn_frame, text=label,
                                    variable=self._work_type_var, value=value)
            rb.pack(side="left", padx=12)

        # ── Experience level ──────────────────────────────────────────────────
        exp_card = ctk.CTkFrame(frame, fg_color=("gray90", "gray20"), corner_radius=10)
        exp_card.pack(fill="x")

        ctk.CTkLabel(exp_card, text="Experience Level",
                     font=ctk.CTkFont(size=14, weight="bold"), anchor="w",
                     ).pack(fill="x", padx=16, pady=(14, 8))

        self._exp_var = ctk.StringVar(
            value=self.config.get("job_preferences", {}).get("experience_level", "any")
        )
        exp_options = [
            ("any",    "Any"),
            ("entry",  "Entry Level"),
            ("mid",    "Mid Level"),
            ("senior", "Senior"),
        ]
        exp_frame = ctk.CTkFrame(exp_card, fg_color="transparent")
        exp_frame.pack(fill="x", padx=16, pady=(0, 14))
        for value, label in exp_options:
            rb = ctk.CTkRadioButton(exp_frame, text=label,
                                    variable=self._exp_var, value=value)
            rb.pack(side="left", padx=12)

    def on_exit(self):
        raw_keywords = self._keywords_entry.get().strip()
        keywords = [k.strip() for k in raw_keywords.split(",") if k.strip()] if raw_keywords else []

        if "job_preferences" not in self.config:
            self.config["job_preferences"] = {}

        self.config["job_preferences"]["keywords"]         = keywords
        self.config["job_preferences"]["work_type"]        = self._work_type_var.get()
        self.config["job_preferences"]["experience_level"] = self._exp_var.get()
