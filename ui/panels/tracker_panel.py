"""
panels/tracker_panel.py
=========================
Application tracker table: Company, Title, Status, and timeline columns.
StatusDropdown auto-timestamps on contact events.
Timeline columns appear automatically as status advances.
"""

import customtkinter as ctk


class TrackerPanel(ctk.CTkFrame):
    """See module docstring above."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._build()

    def _build(self) -> None:
        """Build widgets. TODO: Implement."""
        raise NotImplementedError
