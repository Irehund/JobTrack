"""
ui/wizard/base_step.py
=======================
Base class for all wizard steps.
Provides the standard layout: title, subtitle, content area,
error label, and Back/Next navigation buttons.

Each step subclass only needs to implement:
    _build_content(self, frame) — add widgets to the content frame
    validate(self)              — return (bool, error_str)
"""

import customtkinter as ctk


def attach_context_menu(entry: ctk.CTkEntry):
    """
    Attach a right-click context menu (Cut / Copy / Paste / Select All)
    to a CTkEntry widget. CustomTkinter does not include this by default.

    Call this after creating any CTkEntry that users may want to
    right-click paste into.
    """
    menu = ctk.CTkBaseClass  # placeholder — we use tkinter Menu directly
    import tkinter as tk

    popup = tk.Menu(entry, tearoff=0)
    popup.add_command(label="Cut",        command=lambda: entry.event_generate("<<Cut>>"))
    popup.add_command(label="Copy",       command=lambda: entry.event_generate("<<Copy>>"))
    popup.add_command(label="Paste",      command=lambda: entry.event_generate("<<Paste>>"))
    popup.add_separator()
    popup.add_command(label="Select All", command=lambda: entry.event_generate("<<SelectAll>>"))

    def _show_menu(event):
        try:
            popup.tk_popup(event.x_root, event.y_root)
        finally:
            popup.grab_release()

    # Bind to the underlying tkinter widget inside CTkEntry
    entry._entry.bind("<Button-3>", _show_menu)


class BaseStep(ctk.CTkFrame):
    """Base wizard step with standard layout and navigation."""

    # Subclasses set these
    TITLE: str = ""
    SUBTITLE: str = ""
    NEXT_LABEL: str = "Continue →"
    SHOW_BACK: bool = True

    def __init__(self, parent, config: dict, controller, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.config = config
        self.controller = controller
        self._error_var = ctk.StringVar(value="")
        self._build()

    def _build(self):
        """Build the standard step layout."""
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ── Header ────────────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=60, pady=(40, 0))

        ctk.CTkLabel(
            header,
            text=self.TITLE,
            font=ctk.CTkFont(size=26, weight="bold"),
            anchor="w",
        ).pack(fill="x")

        if self.SUBTITLE:
            ctk.CTkLabel(
                header,
                text=self.SUBTITLE,
                font=ctk.CTkFont(size=14),
                text_color="gray",
                anchor="w",
                wraplength=700,
            ).pack(fill="x", pady=(6, 0))

        # ── Content area ──────────────────────────────────────────────────────
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=1, column=0, sticky="nsew", padx=60, pady=20)
        content.grid_columnconfigure(0, weight=1)
        self._build_content(content)

        # ── Error label ───────────────────────────────────────────────────────
        self._error_label = ctk.CTkLabel(
            self,
            textvariable=self._error_var,
            text_color="#e05252",
            font=ctk.CTkFont(size=13),
        )
        self._error_label.grid(row=2, column=0, pady=(0, 4))

        # ── Navigation buttons ────────────────────────────────────────────────
        nav = ctk.CTkFrame(self, fg_color="transparent")
        nav.grid(row=3, column=0, sticky="ew", padx=60, pady=(0, 30))

        if self.SHOW_BACK:
            ctk.CTkButton(
                nav,
                text="← Back",
                width=100,
                fg_color="transparent",
                border_width=1,
                command=self.controller.back,
            ).pack(side="left")

        ctk.CTkButton(
            nav,
            text=self.NEXT_LABEL,
            width=140,
            command=self.controller.next,
        ).pack(side="right")

    def _build_content(self, frame: ctk.CTkFrame):
        """Override in subclass to add content widgets."""
        pass

    def validate(self) -> tuple[bool, str]:
        """Override in subclass. Return (True, '') to allow advancing."""
        return True, ""

    def show_error(self, message: str):
        """Display an error message below the content area."""
        self._error_var.set(message)

    def clear_error(self):
        """Clear any displayed error message."""
        self._error_var.set("")

    def on_enter(self):
        """Called when this step becomes visible. Override if needed."""
        self.clear_error()

    def on_exit(self):
        """Called when leaving this step. Override if needed."""
        pass
