"""
components/status_dropdown.py
===============================
Application status dropdown for Tracker panel.
Auto-records timestamp on TIMESTAMPED_STATUSES selections.
Triggers timeline column creation in db/jobs_repo.
"""

import customtkinter as ctk


class StatusDropdown(ctk.CTkOptionMenu):
    """See module docstring above."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._build()

    def _build(self) -> None:
        """Build widgets. TODO: Implement."""
        raise NotImplementedError
