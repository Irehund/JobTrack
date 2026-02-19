"""
components/theme_toggle.py
============================
Three-way theme toggle: Light / Dark / System.
Applies immediately. Saves to config.json.
"""

import customtkinter as ctk


class ThemeToggle(ctk.CTkSegmentedButton):
    """See module docstring above."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._build()

    def _build(self) -> None:
        """Build widgets. TODO: Implement."""
        raise NotImplementedError
