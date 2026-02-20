"""
ui/components/status_dropdown.py
==================================
Status dropdown for the Tracker panel.
Auto-records timestamps when a TIMESTAMPED_STATUS is selected.
"""

import customtkinter as ctk
from db.jobs_repo import ALL_STATUSES, update_status


class StatusDropdown(ctk.CTkOptionMenu):
    """Dropdown that auto-saves status changes to the database."""

    def __init__(self, parent, application_id: int,
                 current_status: str, on_change=None, **kwargs):
        self._app_id = application_id
        self._on_change = on_change

        super().__init__(
            parent,
            values=ALL_STATUSES,
            command=self._on_select,
            width=150,
            **kwargs,
        )
        self.set(current_status)

    def _on_select(self, new_status: str):
        try:
            update_status(self._app_id, new_status)
        except Exception as e:
            print(f"StatusDropdown: Failed to update status — {e}")
        if self._on_change:
            self._on_change()
