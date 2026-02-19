"""
wizard/step_linkedin_reminder.py
==================================
Step 3b: LinkedIn profile reminder (shown only if LinkedIn enabled).
Reminds user to update their LinkedIn profile before searching,
as employers see it when the user applies.
"""

import customtkinter as ctk


class StepLinkedinReminder(ctk.CTkFrame):
    """See module docstring above."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._build()

    def _build(self) -> None:
        """Build widgets. TODO: Implement."""
        raise NotImplementedError
