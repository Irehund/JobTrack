"""
wizard/step_complete.py
=========================
Step 7: Setup complete.
Summary of all settings entered.
'Start Searching' saves config and transitions to main window.
"""

import customtkinter as ctk


class StepComplete(ctk.CTkFrame):
    """See module docstring above."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._build()

    def _build(self) -> None:
        """Build widgets. TODO: Implement."""
        raise NotImplementedError
