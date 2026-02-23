"""
ui/wizard/step_tracker.py
==========================
Step 6: Application tracker storage selection.
"""
import customtkinter as ctk
from ui.wizard.base_step import BaseStep

TRACKER_OPTIONS = [
    {
        "value": "local",
        "title": "Local File  (Recommended)",
        "desc":  "Saved only on this computer. No account needed. Works offline. "
                 "Your data never leaves your machine.",
    },
    {
        "value": "google",
        "title": "Google Sheets",
        "desc":  "Synced to a spreadsheet in your Google Drive. "
                 "Access your tracker from any device. "
                 "Requires additional setup — see the note below.",
    },
    {
        "value": "both",
        "title": "Both  (Local + Google Sheets)",
        "desc":  "Saves locally and syncs to Google Sheets. "
                 "Local file acts as a backup if Google is unavailable. "
                 "Requires additional setup — see the note below.",
    },
]

GOOGLE_WARNING = (
    "Google Sheets requires a one-time setup before it will work:\n\n"
    "1. Create a free Google Cloud project at console.cloud.google.com\n"
    "2. Enable the Google Sheets API and Google Drive API\n"
    "3. Create OAuth 2.0 credentials and download google_credentials.json\n"
    "4. Place google_credentials.json in your JobTrack AppData folder\n\n"
    "A full step-by-step guide is available at:\n"
    "github.com/Irehund/JobTrack/wiki/Google-Sheets-Setup\n\n"
    "If you skip this now, you can switch to Google Sheets later in Preferences "
    "once the setup is complete. Local File works immediately with no setup."
)


class StepTracker(BaseStep):
    TITLE = "How Would You Like to Track Your Applications?"
    SUBTITLE = "Choose where JobTrack saves the jobs you apply to."

    def _build_content(self, frame):
        current = self.config.get("tracker", {}).get("mode", "local")
        self._tracker_var = ctk.StringVar(value=current)

        for option in TRACKER_OPTIONS:
            self._build_option_card(frame, option)

        # Warning card — shown when Google Sheets or Both is selected
        self._warning_card = ctk.CTkFrame(
            frame, fg_color=("#fff3cd", "#3a3000"), corner_radius=10)
        self._warning_card.pack(fill="x", pady=(8, 0))

        ctk.CTkLabel(
            self._warning_card,
            text="Additional Setup Required for Google Sheets",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        ).pack(fill="x", padx=16, pady=(14, 4))

        ctk.CTkLabel(
            self._warning_card,
            text=GOOGLE_WARNING,
            font=ctk.CTkFont(size=12),
            text_color="gray",
            anchor="w",
            wraplength=600,
            justify="left",
        ).pack(fill="x", padx=16, pady=(0, 14))

        # Show or hide warning based on current selection
        self._update_warning()

    def _build_option_card(self, parent, option: dict):
        card = ctk.CTkFrame(parent, fg_color=("gray90", "gray20"), corner_radius=10)
        card.pack(fill="x", pady=6)
        card.grid_columnconfigure(1, weight=1)

        rb = ctk.CTkRadioButton(
            card, text="",
            variable=self._tracker_var,
            value=option["value"],
            command=self._on_change,
        )
        rb.grid(row=0, column=0, rowspan=2, padx=(16, 4), pady=16)

        ctk.CTkLabel(
            card, text=option["title"],
            font=ctk.CTkFont(size=14, weight="bold"), anchor="w",
        ).grid(row=0, column=1, sticky="w", padx=4, pady=(16, 2))

        ctk.CTkLabel(
            card, text=option["desc"],
            font=ctk.CTkFont(size=12), text_color="gray",
            anchor="w", wraplength=580, justify="left",
        ).grid(row=1, column=1, sticky="w", padx=4, pady=(0, 16))

    def _on_change(self):
        mode = self._tracker_var.get()
        if "tracker" not in self.config:
            self.config["tracker"] = {}
        self.config["tracker"]["mode"] = mode
        self._update_warning()

    def _update_warning(self):
        """Show warning card only when a Google option is selected."""
        if self._tracker_var.get() in ("google", "both"):
            self._warning_card.pack(fill="x", pady=(8, 0))
        else:
            self._warning_card.pack_forget()

    def on_exit(self):
        self._on_change()
