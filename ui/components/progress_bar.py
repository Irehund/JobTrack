"""
components/progress_bar.py
============================
Persistent progress bar in the main window bottom bar.
Hidden when idle. Shows percent + current operation label.
Briefly shows 'Complete' before hiding.
"""

import customtkinter as ctk


class ProgressBar(ctk.CTkFrame):
    """See module docstring above."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._build()

    def _build(self) -> None:
        """Build widgets. TODO: Implement."""
        raise NotImplementedError
