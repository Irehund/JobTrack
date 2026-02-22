"""
ui/dialogs/retry_notification.py
==================================
Toast-style popup during API retry attempts.
Shows: "Retrying <Provider> — Attempt N of 3"
Auto-dismisses after 3s or when explicitly closed.
"""

import customtkinter as ctk


class RetryNotification(ctk.CTkToplevel):
    """
    Non-blocking toast notification shown when a provider is being retried.
    Positioned in the bottom-right of the screen.
    """

    AUTO_DISMISS_MS = 3000

    def __init__(self, parent, provider_name: str, attempt: int, max_attempts: int, **kwargs):
        super().__init__(parent, **kwargs)

        self.overrideredirect(True)    # No title bar
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.92)

        self._build(provider_name, attempt, max_attempts)
        self._position()

        # Auto-dismiss
        self.after(self.AUTO_DISMISS_MS, self.dismiss)

    def _build(self, provider: str, attempt: int, max_attempts: int):
        self.configure(fg_color=("gray20", "gray15"))

        frame = ctk.CTkFrame(self, fg_color=("gray25", "gray18"),
                             corner_radius=10, border_width=1,
                             border_color=("gray60", "gray40"))
        frame.pack(padx=2, pady=2)

        ctk.CTkLabel(
            frame,
            text=f"⟳  Retrying {provider}",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(padx=16, pady=(12, 2))

        ctk.CTkLabel(
            frame,
            text=f"Attempt {attempt} of {max_attempts}",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack(padx=16, pady=(0, 12))

    def _position(self):
        """Position in the bottom-right corner of the screen."""
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w  = self.winfo_reqwidth()
        h  = self.winfo_reqheight()
        x  = sw - w - 24
        y  = sh - h - 60   # Above taskbar
        self.geometry(f"+{x}+{y}")

    def dismiss(self):
        """Close the notification (called automatically or by parent)."""
        try:
            self.destroy()
        except Exception:
            pass   # Already destroyed


def show_retry_toast(parent, provider_name: str, attempt: int,
                     max_attempts: int) -> RetryNotification:
    """
    Convenience function — create and show a RetryNotification.

    Returns the notification widget so the caller can dismiss it early
    (e.g., when the retry succeeds).
    """
    return RetryNotification(parent, provider_name, attempt, max_attempts)
