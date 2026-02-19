"""
panels/assistant_panel.py
===========================
Claude AI assistant chat. Accessible from sidebar at any time.
Scrollable message history, text input, Send button.
Context updated to reflect current app state.
"""

import customtkinter as ctk


class AssistantPanel(ctk.CTkFrame):
    """See module docstring above."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._build()

    def _build(self) -> None:
        """Build widgets. TODO: Implement."""
        raise NotImplementedError
