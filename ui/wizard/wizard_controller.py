"""
wizard/wizard_controller.py
=============================
Manages wizard step flow — back/next navigation, step validation,
and partial progress saving if the user quits mid-wizard.
Runs exactly once; all settings editable in Preferences afterward.
"""

import customtkinter as ctk


class WizardController(ctk.CTkFrame):
    """See module docstring above."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._build()

    def _build(self) -> None:
        """Build widgets. TODO: Implement."""
        raise NotImplementedError
