"""
ui/wizard/step_linkedin_reminder.py
=====================================
Step 3b: LinkedIn profile reminder — only shown if LinkedIn is enabled.
"""

import customtkinter as ctk
from ui.wizard.base_step import BaseStep


class StepLinkedinReminder(BaseStep):
    TITLE = "One Thing Before We Continue"
    SUBTITLE = "You've enabled LinkedIn job search — here's something important to know."

    def _build_content(self, frame):
        card = ctk.CTkFrame(frame, fg_color=("gray90", "gray20"), corner_radius=12)
        card.pack(fill="x", pady=(10, 0))

        ctk.CTkLabel(card, text="👔  Update Your LinkedIn Profile First",
                     font=ctk.CTkFont(size=16, weight="bold"), anchor="w",
                     ).pack(fill="x", padx=20, pady=(18, 8))

        ctk.CTkLabel(
            card,
            text="When you apply to a job through LinkedIn, employers can see your full LinkedIn profile — "
                 "not just your resume. Before you start searching, make sure your profile is:",
            font=ctk.CTkFont(size=13),
            text_color="gray",
            anchor="w",
            wraplength=660,
            justify="left",
        ).pack(fill="x", padx=20, pady=(0, 10))

        checklist = [
            "✓  Up to date with your most recent experience and skills",
            "✓  Has a professional profile photo",
            "✓  Includes a strong headline (not just your job title)",
            "✓  Your contact information is accurate",
            "✓  Set to 'Open to Work' if you want recruiters to find you",
        ]
        for item in checklist:
            ctk.CTkLabel(card, text=item, font=ctk.CTkFont(size=13),
                         anchor="w").pack(fill="x", padx=32, pady=2)

        ctk.CTkLabel(
            card,
            text="\nYou can update your profile at linkedin.com — it only takes a few minutes "
                 "and significantly increases your chances of hearing back.",
            font=ctk.CTkFont(size=12),
            text_color="gray",
            anchor="w",
            wraplength=660,
            justify="left",
        ).pack(fill="x", padx=20, pady=(4, 18))
