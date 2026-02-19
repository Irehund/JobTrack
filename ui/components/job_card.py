"""
components/job_card.py
========================
Single job listing card: title, company, location, salary, badges.
Buttons: 'View Posting' (opens URL), 'Mark Applied'.
Compact and expanded view modes.
"""

import customtkinter as ctk


class JobCard(ctk.CTkFrame):
    """See module docstring above."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._build()

    def _build(self) -> None:
        """Build widgets. TODO: Implement."""
        raise NotImplementedError
