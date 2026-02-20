"""
ui/wizard/step_welcome.py
==========================
Step 1: Welcome screen with privacy statement.
"""

import customtkinter as ctk
from ui.wizard.base_step import BaseStep


class StepWelcome(BaseStep):
    TITLE = "Welcome to JobTrack"
    SUBTITLE = "Let's get you set up in just a few minutes."
    NEXT_LABEL = "Get Started →"
    SHOW_BACK = False

    def _build_content(self, frame):
        frame.grid_rowconfigure(0, weight=1)

        # Feature highlights
        features = [
            ("🔍", "Search multiple job boards", "USAJobs, Indeed, LinkedIn, Glassdoor, and Adzuna — all in one place."),
            ("🗺️", "See jobs on a map", "Visualize commute times before you apply."),
            ("📋", "Track your applications", "Never lose track of where you applied or what happened next."),
            ("🤖", "Built-in AI assistant", "Ask plain-English questions anytime while you search."),
        ]

        for icon, title, desc in features:
            row = ctk.CTkFrame(frame, fg_color=("gray90", "gray20"), corner_radius=10)
            row.pack(fill="x", pady=6)
            ctk.CTkLabel(row, text=icon, font=ctk.CTkFont(size=24), width=50).pack(side="left", padx=(16, 8), pady=12)
            text_frame = ctk.CTkFrame(row, fg_color="transparent")
            text_frame.pack(side="left", fill="x", expand=True, pady=12)
            ctk.CTkLabel(text_frame, text=title, font=ctk.CTkFont(size=14, weight="bold"), anchor="w").pack(fill="x")
            ctk.CTkLabel(text_frame, text=desc, font=ctk.CTkFont(size=12), text_color="gray", anchor="w").pack(fill="x")

        # Privacy box
        privacy = ctk.CTkFrame(frame, fg_color=("gray85", "gray25"), corner_radius=10)
        privacy.pack(fill="x", pady=(20, 0))
        ctk.CTkLabel(
            privacy,
            text="🔒  Your Privacy",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        ).pack(fill="x", padx=16, pady=(12, 4))
        ctk.CTkLabel(
            privacy,
            text="None of the information you enter is ever stored outside your own computer "
                 "or your own Google account. JobTrack never connects to any server we own. "
                 "The full source code is on GitHub so anyone can verify this.",
            font=ctk.CTkFont(size=12),
            text_color="gray",
            anchor="w",
            wraplength=680,
            justify="left",
        ).pack(fill="x", padx=16, pady=(0, 12))
