"""
wizard/step_welcome.py
========================
Step 1: Welcome screen.
Explains what JobTrack does and displays the full privacy statement:
'None of the information you enter is stored outside your own computer
or your own Google account. Source code is on GitHub for anyone to verify.'
"""

import customtkinter as ctk


class StepWelcome(ctk.CTkFrame):
    """See module docstring above."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._build()

    def _build(self) -> None:
        """Build widgets. TODO: Implement."""
        raise NotImplementedError
