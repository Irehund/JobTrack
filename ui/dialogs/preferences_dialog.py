"""
dialogs/preferences_dialog.py
===============================
Full preferences editor. Tabbed layout matching wizard steps:
Providers, Location, Job Prefs, Tracker, Appearance.
All changes saved on 'Save' click.
"""

import customtkinter as ctk


class PreferencesDialog(ctk.CTkToplevel):
    """See module docstring above."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._build()

    def _build(self) -> None:
        """Build widgets. TODO: Implement."""
        raise NotImplementedError
