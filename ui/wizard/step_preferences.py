"""
wizard/step_preferences.py
============================
Step 5: Job search preferences.
Job title keyword tags. Work type: Remote/Hybrid/On-site/Any.
Experience level: Entry/Mid/Senior/Any.
"""

import customtkinter as ctk


class StepPreferences(ctk.CTkFrame):
    """See module docstring above."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._build()

    def _build(self) -> None:
        """Build widgets. TODO: Implement."""
        raise NotImplementedError
