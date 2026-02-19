"""
dialogs/retry_notification.py
===============================
Toast popup during API retry attempts.
Shows: 'Retrying <Provider> - Attempt N of 3'.
Auto-dismisses after 3s or on success.
"""

import customtkinter as ctk


class RetryNotification(ctk.CTkToplevel):
    """See module docstring above."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._build()

    def _build(self) -> None:
        """Build widgets. TODO: Implement."""
        raise NotImplementedError
