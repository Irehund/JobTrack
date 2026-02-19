"""
wizard/step_api_keys.py
=========================
Step 3: API key entry.
One section per enabled provider with a ScreenshotSlideshow
showing step-by-step how to get the key.
Live key validation before allowing user to proceed.
"""

import customtkinter as ctk


class StepApiKeys(ctk.CTkFrame):
    """See module docstring above."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._build()

    def _build(self) -> None:
        """Build widgets. TODO: Implement."""
        raise NotImplementedError
