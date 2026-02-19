"""
wizard/step_google.py
=======================
Step 6b: Google OAuth (shown only if Sheets or Both selected).
Explains what access is requested. Shows screenshot of consent screen.
'Connect Google Account' button opens browser OAuth flow.
"""

import customtkinter as ctk


class StepGoogle(ctk.CTkFrame):
    """See module docstring above."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._build()

    def _build(self) -> None:
        """Build widgets. TODO: Implement."""
        raise NotImplementedError
