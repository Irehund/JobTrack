"""
dialogs/about_dialog.py
=========================
About dialog: version, credits, GitHub link, privacy statement, MIT license.
"""

import customtkinter as ctk


class AboutDialog(ctk.CTkToplevel):
    """See module docstring above."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._build()

    def _build(self) -> None:
        """Build widgets. TODO: Implement."""
        raise NotImplementedError
