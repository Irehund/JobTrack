"""
panels/dashboard_panel.py
===========================
Main dashboard: recent results summary, quick stats,
last-searched timestamp, and prominent 'Search Now' button.
"""

import customtkinter as ctk


class DashboardPanel(ctk.CTkFrame):
    """See module docstring above."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._build()

    def _build(self) -> None:
        """Build widgets. TODO: Implement."""
        raise NotImplementedError
