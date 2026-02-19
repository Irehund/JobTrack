"""
wizard/step_location.py
=========================
Step 4: Home location entry.
Zip code or city/state text entry.
Search radius slider: 10 / 25 / 50 / 100 miles.
"""

import customtkinter as ctk


class StepLocation(ctk.CTkFrame):
    """See module docstring above."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._build()

    def _build(self) -> None:
        """Build widgets. TODO: Implement."""
        raise NotImplementedError
