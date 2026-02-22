"""
ui/wizard/step_linkedin_reminder.py
=====================================
Step 3b: LinkedIn coverage notice — only shown if LinkedIn is enabled.
Explains that LinkedIn jobs are covered by the RapidAPI key already
entered for Indeed. No additional setup required.
"""

import customtkinter as ctk
from ui.wizard.base_step import BaseStep


class StepLinkedinReminder(BaseStep):
    TITLE = "Good News About LinkedIn"
    SUBTITLE = "LinkedIn jobs are already covered — no extra setup needed."

    def _build_content(self, frame):
        card = ctk.CTkFrame(frame, fg_color=("gray90", "gray20"), corner_radius=12)
        card.pack(fill="x", pady=(10, 0))

        ctk.CTkLabel(
            card,
            text="LinkedIn is included with your RapidAPI key",
            font=ctk.CTkFont(size=16, weight="bold"),
            anchor="w",
        ).pack(fill="x", padx=20, pady=(18, 8))

        ctk.CTkLabel(
            card,
            text=(
                "JobTrack searches LinkedIn through the same RapidAPI key you entered "
                "for Indeed. There is no separate LinkedIn developer account or API key required.\n\n"
                "As long as your RapidAPI key is active, LinkedIn job listings will appear "
                "in your search results automatically alongside Indeed and Glassdoor."
            ),
            font=ctk.CTkFont(size=13),
            text_color="gray",
            anchor="w",
            wraplength=620,
            justify="left",
        ).pack(fill="x", padx=20, pady=(0, 16))

        # Profile tip card
        tip_card = ctk.CTkFrame(frame, fg_color=("gray90", "gray20"), corner_radius=12)
        tip_card.pack(fill="x", pady=(12, 0))

        ctk.CTkLabel(
            tip_card,
            text="One thing worth doing before you search",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w",
        ).pack(fill="x", padx=20, pady=(18, 8))

        ctk.CTkLabel(
            tip_card,
            text=(
                "When you apply to a job through LinkedIn, employers can see your full "
                "LinkedIn profile. Before you start searching, make sure your profile is "
                "up to date with your most recent experience and set to 'Open to Work' "
                "if you want recruiters to find you."
            ),
            font=ctk.CTkFont(size=13),
            text_color="gray",
            anchor="w",
            wraplength=620,
            justify="left",
        ).pack(fill="x", padx=20, pady=(0, 18))
