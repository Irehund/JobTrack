"""
ui/components/progress_bar.py
==============================
Animated indeterminate progress bar with a label.
Shown in the bottom bar during searches and API calls.
"""

import customtkinter as ctk


class ProgressBar(ctk.CTkFrame):
    """Animated progress bar that shows during background operations."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self._running = False

        self._label = ctk.CTkLabel(
            self, text="", font=ctk.CTkFont(size=11), text_color="gray")
        self._label.grid(row=0, column=0, sticky="ew")

        self._bar = ctk.CTkProgressBar(self, mode="indeterminate", height=6)
        self._bar.grid(row=1, column=0, sticky="ew", pady=(2, 0))
        self._bar.grid_remove()   # Hidden until start() is called

    def start(self, message: str = "Working..."):
        """Show and animate the progress bar."""
        self._label.configure(text=message)
        self._bar.grid()
        self._bar.start()
        self._running = True

    def stop(self):
        """Hide the progress bar."""
        self._bar.stop()
        self._bar.grid_remove()
        self._label.configure(text="")
        self._running = False
