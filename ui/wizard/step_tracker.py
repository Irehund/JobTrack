"""
wizard/step_tracker.py
========================
Step 6: Tracker storage choice.
Radio buttons: Local File / Google Sheets / Both.
Each option has a plain-English description of what it means.
"""

import customtkinter as ctk


class StepTracker(ctk.CTkFrame):
    """See module docstring above."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._build()

    def _build(self) -> None:
        """Build widgets. TODO: Implement."""
        raise NotImplementedError
