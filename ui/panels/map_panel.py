"""
panels/map_panel.py
=====================
Interactive map view. All filtered jobs shown as pins.
User selects jobs for commute calculation (batch).
Pin colors: green <30min, orange 30-60min, red >60min, gray=unknown.
"""

import customtkinter as ctk


class MapPanel(ctk.CTkFrame):
    """See module docstring above."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._build()

    def _build(self) -> None:
        """Build widgets. TODO: Implement."""
        raise NotImplementedError
