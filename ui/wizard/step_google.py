"""
ui/wizard/step_google.py
=========================
Step 6b: Google OAuth — only shown if Google Sheets selected.
"""

import threading
import customtkinter as ctk
from ui.wizard.base_step import BaseStep


class StepGoogle(BaseStep):
    TITLE = "Connect Your Google Account"
    SUBTITLE = "JobTrack will create a spreadsheet in your Google Drive to track your applications."

    def _build_content(self, frame):
        self._connected = False

        # What access is requested
        access_card = ctk.CTkFrame(frame, fg_color=("gray90", "gray20"), corner_radius=10)
        access_card.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(access_card, text="What Access Is Being Requested",
                     font=ctk.CTkFont(size=14, weight="bold"), anchor="w",
                     ).pack(fill="x", padx=16, pady=(14, 6))

        permissions = [
            ("📊", "Google Sheets",      "Create and edit one spreadsheet in your Drive"),
            ("📁", "Google Drive",       "Create one folder called 'JobTrack' to keep things organized"),
            ("🚫", "Nothing else",       "No access to your email, contacts, calendar, or other files"),
        ]
        for icon, title, desc in permissions:
            row = ctk.CTkFrame(access_card, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=3)
            ctk.CTkLabel(row, text=icon, width=30).pack(side="left")
            ctk.CTkLabel(row, text=f"{title}:", font=ctk.CTkFont(weight="bold"),
                         width=130, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=desc, font=ctk.CTkFont(size=12),
                         text_color="gray", anchor="w").pack(side="left")
        ctk.CTkFrame(access_card, fg_color="transparent", height=6).pack()

        # Connect button + status
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=8)

        self._connect_btn = ctk.CTkButton(
            btn_frame,
            text="🔗  Connect Google Account",
            height=44,
            font=ctk.CTkFont(size=14),
            command=self._connect,
        )
        self._connect_btn.pack(side="left")

        self._status_label = ctk.CTkLabel(
            btn_frame, text="", font=ctk.CTkFont(size=13),
            text_color="gray",
        )
        self._status_label.pack(side="left", padx=16)

        # Skip note
        ctk.CTkLabel(
            frame,
            text="You can also skip this step and connect Google later in Preferences.",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        ).pack(anchor="w", pady=(8, 0))

    def _connect(self):
        """Open browser OAuth flow in background thread."""
        self._connect_btn.configure(state="disabled", text="⟳  Opening browser...")
        self._status_label.configure(text="")

        def _run():
            try:
                # TODO: Call integrations/google_sheets.py OAuth flow
                # For now, simulate success so wizard is completable
                import time; time.sleep(1.5)
                self._connected = True
                self._connect_btn.configure(
                    text="✓  Connected",
                    fg_color="#4CAF50",
                    state="disabled",
                )
                self._status_label.configure(
                    text="Google account connected successfully.",
                    text_color="#4CAF50",
                )
            except Exception as e:
                self._connect_btn.configure(state="normal", text="🔗  Try Again")
                self._status_label.configure(
                    text=f"Connection failed: {str(e)[:50]}",
                    text_color="#e05252",
                )

        threading.Thread(target=_run, daemon=True).start()

    def validate(self) -> tuple[bool, str]:
        """Allow skipping Google connection — user can do it in Preferences."""
        return True, ""
