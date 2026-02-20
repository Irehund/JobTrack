"""
ui/wizard/wizard_controller.py
================================
Manages wizard step flow — back/next navigation, step validation,
and partial progress saving if the user quits mid-wizard.
Runs exactly once; all settings editable in Preferences afterward.
"""

import customtkinter as ctk
from typing import Optional


STEPS = [
    "step_welcome",
    "step_providers",
    "step_api_keys",
    "step_linkedin_reminder",   # Only shown if LinkedIn enabled
    "step_location",
    "step_preferences",
    "step_tracker",
    "step_google",              # Only shown if Google Sheets selected
    "step_complete",
]


class WizardController(ctk.CTkFrame):
    """
    Root wizard frame. Manages step instantiation, navigation,
    and the progress indicator at the top.
    """

    def __init__(self, parent, config: dict, on_complete, **kwargs):
        """
        Args:
            parent:      Parent widget (the root app window)
            config:      In-progress config dict (modified as user fills in steps)
            on_complete: Callback called with final config when wizard finishes
        """
        super().__init__(parent, **kwargs)
        self.config = config
        self.on_complete = on_complete
        self._steps: dict = {}
        self._step_order: list[str] = []
        self._current_index: int = 0

        self.configure(fg_color="transparent")
        self._build()
        self._build_step_order()
        self._show_step(0)

    def _build(self):
        """Build the wizard shell — progress bar area + content area."""
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ── Progress dots at top ──────────────────────────────────────────────
        self._progress_frame = ctk.CTkFrame(self, fg_color="transparent", height=40)
        self._progress_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 0))

        # ── Content area — steps render here ─────────────────────────────────
        self._content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._content_frame.grid(row=1, column=0, sticky="nsew")
        self._content_frame.grid_rowconfigure(0, weight=1)
        self._content_frame.grid_columnconfigure(0, weight=1)

    def _build_step_order(self):
        """
        Build the active step list based on current config.
        LinkedIn reminder only appears if LinkedIn is enabled.
        Google step only appears if tracker mode includes sheets.
        """
        self._step_order = ["step_welcome", "step_providers", "step_api_keys"]

        if self.config.get("providers", {}).get("linkedin", {}).get("enabled", False):
            self._step_order.append("step_linkedin_reminder")

        self._step_order += ["step_location", "step_preferences", "step_tracker"]

        tracker_mode = self.config.get("tracker", {}).get("mode", "local")
        if tracker_mode in ("google", "both"):
            self._step_order.append("step_google")

        self._step_order.append("step_complete")
        self._update_progress_dots()

    def _get_step(self, step_name: str):
        """Lazily instantiate a step widget."""
        if step_name not in self._steps:
            # Import the step module dynamically
            module_map = {
                "step_welcome":            ("ui.wizard.step_welcome",           "StepWelcome"),
                "step_providers":          ("ui.wizard.step_providers",         "StepProviders"),
                "step_api_keys":           ("ui.wizard.step_api_keys",          "StepApiKeys"),
                "step_linkedin_reminder":  ("ui.wizard.step_linkedin_reminder", "StepLinkedinReminder"),
                "step_location":           ("ui.wizard.step_location",          "StepLocation"),
                "step_preferences":        ("ui.wizard.step_preferences",       "StepPreferences"),
                "step_tracker":            ("ui.wizard.step_tracker",           "StepTracker"),
                "step_google":             ("ui.wizard.step_google",            "StepGoogle"),
                "step_complete":           ("ui.wizard.step_complete",          "StepComplete"),
            }
            mod_path, class_name = module_map[step_name]
            import importlib
            mod = importlib.import_module(mod_path)
            cls = getattr(mod, class_name)
            self._steps[step_name] = cls(
                self._content_frame,
                config=self.config,
                controller=self,
            )
            self._steps[step_name].grid(row=0, column=0, sticky="nsew")
        return self._steps[step_name]

    def _show_step(self, index: int):
        """Display the step at the given index."""
        if index < 0 or index >= len(self._step_order):
            return

        # Hide all steps
        for widget in self._content_frame.grid_slaves():
            widget.grid_remove()

        self._current_index = index
        step_name = self._step_order[index]
        step = self._get_step(step_name)
        step.grid()
        step.on_enter()
        self._update_progress_dots()

    def next(self):
        """
        Called by each step's Next/Continue button.
        Validates the current step before advancing.
        """
        step_name = self._step_order[self._current_index]
        step = self._get_step(step_name)

        valid, error_msg = step.validate()
        if not valid:
            step.show_error(error_msg)
            return

        step.on_exit()

        # After providers step, rebuild order in case LinkedIn was toggled
        if step_name == "step_providers":
            self._build_step_order()
        # After tracker step, rebuild order in case Google was toggled
        elif step_name == "step_tracker":
            self._build_step_order()

        if self._current_index < len(self._step_order) - 1:
            self._show_step(self._current_index + 1)

    def back(self):
        """Called by each step's Back button."""
        if self._current_index > 0:
            step = self._get_step(self._step_order[self._current_index])
            step.on_exit()
            self._show_step(self._current_index - 1)

    def complete(self):
        """Called by StepComplete's 'Start Searching' button."""
        self.config["setup_complete"] = True
        self.on_complete(self.config)

    def _update_progress_dots(self):
        """Redraw the progress dot indicators at the top of the wizard."""
        for widget in self._progress_frame.winfo_children():
            widget.destroy()

        total = len(self._step_order)
        for i, _ in enumerate(self._step_order):
            if i == self._current_index:
                color = "#1f6aa5"   # Active — blue
                size = 12
            elif i < self._current_index:
                color = "#4CAF50"   # Completed — green
                size = 10
            else:
                color = "#555555"   # Upcoming — gray
                size = 10

            dot = ctk.CTkLabel(
                self._progress_frame,
                text="●",
                font=ctk.CTkFont(size=size),
                text_color=color,
            )
            dot.pack(side="left", padx=4)

    @property
    def current_step_name(self) -> str:
        return self._step_order[self._current_index]

    @property
    def is_first_step(self) -> bool:
        return self._current_index == 0

    @property
    def is_last_step(self) -> bool:
        return self._current_index == len(self._step_order) - 1
