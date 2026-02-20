"""
ui/components/theme_toggle.py
==============================
Light/Dark/System theme toggle button for the sidebar.
"""

import customtkinter as ctk
from core import config_manager


class ThemeToggle(ctk.CTkSegmentedButton):
    """Three-way toggle for app theme saved to config."""

    def __init__(self, parent, config: dict, **kwargs):
        self._config = config
        current = config.get("theme", "system").capitalize()

        super().__init__(
            parent,
            values=["Light", "Dark", "System"],
            command=self._on_change,
            height=32,
            **kwargs,
        )
        self.set(current)

    def _on_change(self, value: str):
        theme = value.lower()
        ctk.set_appearance_mode(theme)
        self._config["theme"] = theme
        config_manager.save(self._config)
