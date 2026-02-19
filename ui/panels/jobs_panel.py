"""
panels/jobs_panel.py
======================
Scrollable job results list with filter toolbar.
Each result is a JobCard component.
'Mark Applied' on each card adds to tracker.
"""

import customtkinter as ctk


class JobsPanel(ctk.CTkFrame):
    """See module docstring above."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._build()

    def _build(self) -> None:
        """Build widgets. TODO: Implement."""
        raise NotImplementedError
