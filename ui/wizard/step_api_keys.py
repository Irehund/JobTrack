"""
ui/wizard/step_api_keys.py
===========================
Step 3: API key entry for each enabled provider.
Shows a screenshot slideshow per provider and validates the key live.
"""

import threading
import customtkinter as ctk
from ui.wizard.base_step import BaseStep
from core import keyring_manager

# Instructions for each provider — shown as text steps since screenshots
# are added to assets/wizard_screens/ separately
PROVIDER_INSTRUCTIONS = {
    "usajobs": {
        "name": "USAJobs",
        "steps": [
            "Go to developer.usajobs.gov/APIRequest",
            "Fill in your name, email, and intended use (e.g. 'Personal job search tool')",
            "Submit the form — your API key will be emailed within minutes",
            "Also note the email address you registered with — you'll need both",
            "Paste your API key and email address below",
        ],
        "fields": [
            {"key": "usajobs",       "label": "API Key",           "placeholder": "Paste your USAJobs API key here"},
            {"key": "usajobs_email", "label": "Registered Email",  "placeholder": "The email you used to register"},
        ],
    },
    "indeed": {
        "name": "Indeed",
        "steps": [
            "Go to developer.indeed.com and sign in",
            "Click 'My Apps' then 'Create new app'",
            "Fill in the app name and description",
            "Copy the Publisher ID from your app dashboard",
            "Paste it below",
        ],
        "fields": [
            {"key": "indeed", "label": "Publisher ID", "placeholder": "Paste your Indeed Publisher ID here"},
        ],
    },
    "linkedin": {
        "name": "LinkedIn",
        "steps": [
            "Go to linkedin.com/developers and sign in",
            "Click 'Create App' and fill in the required fields",
            "Under 'Auth', copy your Client ID and Client Secret",
            "Note: LinkedIn API access may require business verification",
            "Paste your Client ID below",
        ],
        "fields": [
            {"key": "linkedin", "label": "Client ID", "placeholder": "Paste your LinkedIn Client ID here"},
        ],
    },
    "glassdoor": {
        "name": "Glassdoor",
        "steps": [
            "Go to glassdoor.com/developer and sign in",
            "Request API access — approval may take a few days",
            "Once approved, copy your Partner ID and Key",
            "Paste your API key below",
        ],
        "fields": [
            {"key": "glassdoor", "label": "API Key", "placeholder": "Paste your Glassdoor API key here"},
        ],
    },
    "adzuna": {
        "name": "Adzuna",
        "steps": [
            "Go to developer.adzuna.com and create a free account",
            "Click 'Create new application'",
            "Copy your App ID and App Key from the dashboard",
            "Paste your App Key below",
        ],
        "fields": [
            {"key": "adzuna", "label": "App Key", "placeholder": "Paste your Adzuna App Key here"},
        ],
    },
    "anthropic": {
        "name": "Claude AI Assistant (Optional)",
        "steps": [
            "Go to console.anthropic.com and sign in or create a free account",
            "Click 'API Keys' in the left sidebar",
            "Click 'Create Key', give it a name like 'JobTrack'",
            "Copy the key — you won't be able to see it again after closing",
            "Paste it below. This enables the built-in AI assistant.",
        ],
        "fields": [
            {"key": "anthropic", "label": "API Key", "placeholder": "sk-ant-..."},
        ],
    },
}


class StepApiKeys(BaseStep):
    TITLE = "Connect Your Job Sources"
    SUBTITLE = "Enter the API key for each source you selected. Your keys are stored securely on your computer."

    def _build_content(self, frame):
        self._entries: dict[str, ctk.CTkEntry] = {}
        self._status_labels: dict[str, ctk.CTkLabel] = {}

        # Always show USAJobs. Show others if enabled. Always show Anthropic.
        providers_to_show = ["usajobs"]
        for pid in ["indeed", "linkedin", "glassdoor", "adzuna"]:
            if self.config.get("providers", {}).get(pid, {}).get("enabled", False):
                providers_to_show.append(pid)
        providers_to_show.append("anthropic")

        scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        scroll.grid_columnconfigure(0, weight=1)

        for pid in providers_to_show:
            info = PROVIDER_INSTRUCTIONS.get(pid)
            if not info:
                continue
            self._build_provider_section(scroll, pid, info)

    def _build_provider_section(self, parent, pid: str, info: dict):
        """Build the UI section for one provider."""
        section = ctk.CTkFrame(parent, fg_color=("gray90", "gray20"), corner_radius=10)
        section.pack(fill="x", pady=8)

        # Provider name header
        ctk.CTkLabel(
            section,
            text=info["name"],
            font=ctk.CTkFont(size=15, weight="bold"),
            anchor="w",
        ).pack(fill="x", padx=16, pady=(14, 6))

        # Numbered steps
        for i, step_text in enumerate(info["steps"], 1):
            ctk.CTkLabel(
                section,
                text=f"  {i}.  {step_text}",
                font=ctk.CTkFont(size=12),
                text_color="gray",
                anchor="w",
            ).pack(fill="x", padx=16, pady=1)

        # Entry fields
        for field in info["fields"]:
            key = field["key"]
            row = ctk.CTkFrame(section, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=(10, 4))
            row.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(row, text=field["label"], width=130, anchor="w",
                         font=ctk.CTkFont(size=13)).grid(row=0, column=0, sticky="w")

            entry = ctk.CTkEntry(row, placeholder_text=field["placeholder"],
                                 show="•" if "key" in field["label"].lower() or "secret" in field["label"].lower() else "")
            entry.grid(row=0, column=1, sticky="ew", padx=(8, 8))
            self._entries[key] = entry

            # Pre-fill if already stored
            existing = keyring_manager.get_key(key)
            if existing:
                entry.insert(0, existing)

            status = ctk.CTkLabel(row, text="", width=80, font=ctk.CTkFont(size=12))
            status.grid(row=0, column=2)
            self._status_labels[key] = status

            verify_btn = ctk.CTkButton(
                section, text=f"Verify {info['name']} Key",
                width=160, height=30,
                command=lambda p=pid, i=info: self._verify_key(p, i),
            )
            verify_btn.pack(anchor="e", padx=16, pady=(4, 14))

    def _verify_key(self, pid: str, info: dict):
        """Run key validation in a background thread to keep UI responsive."""
        def _run():
            from integrations.usajobs_provider import UsajobsProvider
            from integrations.base_provider import ProviderError

            if pid == "usajobs":
                key   = self._entries.get("usajobs", None)
                email = self._entries.get("usajobs_email", None)
                if not key or not email:
                    return
                key_val   = key.get().strip()
                email_val = email.get().strip()
                if not key_val or not email_val:
                    self._set_status("usajobs", "⚠ Enter key + email", "orange")
                    return
                provider = UsajobsProvider(key_val, email_val)
                valid, msg = provider.validate_key()
            else:
                field_key = info["fields"][0]["key"]
                entry = self._entries.get(field_key)
                if not entry:
                    return
                key_val = entry.get().strip()
                fmt_ok, fmt_msg = keyring_manager.validate_key_format(field_key, key_val)
                if not fmt_ok:
                    self._set_status(field_key, f"⚠ {fmt_msg[:30]}", "orange")
                    return
                # For non-USAJobs providers, format check is all we do for now
                valid, msg = True, "Format looks good"

            color = "#4CAF50" if valid else "#e05252"
            symbol = "✓" if valid else "✗"
            self._set_status(info["fields"][0]["key"], f"{symbol} {msg[:25]}", color)

            if valid:
                # Save all fields for this provider to keyring
                for field in info["fields"]:
                    key_entry = self._entries.get(field["key"])
                    if key_entry:
                        keyring_manager.save_key(field["key"], key_entry.get().strip())

        threading.Thread(target=_run, daemon=True).start()
        # Show "Checking..." immediately
        for field in info["fields"]:
            self._set_status(field["key"], "⟳ Checking...", "gray")

    def _set_status(self, key: str, text: str, color: str):
        """Update a status label — safe to call from background thread."""
        label = self._status_labels.get(key)
        if label:
            label.configure(text=text, text_color=color)

    def validate(self) -> tuple[bool, str]:
        """USAJobs key and email are required. Others are optional."""
        usajobs_key   = self._entries.get("usajobs", None)
        usajobs_email = self._entries.get("usajobs_email", None)

        if usajobs_key and not usajobs_key.get().strip():
            return False, "USAJobs API key is required. It's free — see the steps above."
        if usajobs_email and not usajobs_email.get().strip():
            return False, "USAJobs registered email is required."
        return True, ""

    def on_exit(self):
        """Save all entered keys to keyring when leaving this step."""
        for key, entry in self._entries.items():
            val = entry.get().strip()
            if val:
                keyring_manager.save_key(key, val)
