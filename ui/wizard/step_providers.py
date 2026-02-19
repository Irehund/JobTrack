"""
wizard/step_providers.py
==========================
Step 2: Job provider selection.
USAJobs shown locked-on (free, always available, no approval).
Indeed, LinkedIn, Glassdoor, Adzuna are opt-in checkboxes.
"""

import customtkinter as ctk


class StepProviders(ctk.CTkFrame):
    """See module docstring above."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._build()

    def _build(self) -> None:
        """Build widgets. TODO: Implement."""
        raise NotImplementedError
