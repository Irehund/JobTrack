"""
components/screenshot_slideshow.py
====================================
Step-by-step image viewer for wizard API guides.
Loads images from assets/wizard_screens/<provider>/.
Previous/Next navigation with caption text.
"""

import customtkinter as ctk


class ScreenshotSlideshow(ctk.CTkFrame):
    """See module docstring above."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._build()

    def _build(self) -> None:
        """Build widgets. TODO: Implement."""
        raise NotImplementedError
