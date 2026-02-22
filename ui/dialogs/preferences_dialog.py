"""
ui/dialogs/preferences_dialog.py
==================================
Full preferences editor. Tabbed layout:
    Location | Job Search | Providers & Keys | Tracker | Appearance

All changes saved atomically on 'Save' click.
Changes are not applied until Save is clicked — Cancel discards everything.
"""

import copy
import threading
import customtkinter as ctk
from core import config_manager, keyring_manager
from core.utils import normalize_state


APP_VERSION = "1.0.0"


class PreferencesDialog(ctk.CTkToplevel):
    """Tabbed preferences editor launched from the sidebar."""

    def __init__(self, parent, config: dict, on_save=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.title("Preferences")
        self.geometry("680x560")
        self.resizable(False, False)
        self.grab_set()   # Modal

        # Work on a deep copy so Cancel truly discards
        self._config   = copy.deepcopy(config)
        self._on_save  = on_save
        self._widgets  = {}   # named widget refs for reading values on Save

        self._build()
        self._center_on_parent(parent)

    def _center_on_parent(self, parent):
        self.update_idletasks()
        px = parent.winfo_rootx() + parent.winfo_width()  // 2
        py = parent.winfo_rooty() + parent.winfo_height() // 2
        w, h = 680, 560
        self.geometry(f"{w}x{h}+{px - w//2}+{py - h//2}")

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)
        self.grid_columnconfigure(0, weight=1)

        tabs = ctk.CTkTabview(self, anchor="nw")
        tabs.grid(row=0, column=0, sticky="nsew", padx=16, pady=(16, 8))

        for name in ["Location", "Job Search", "Providers & Keys", "Tracker", "Appearance"]:
            tabs.add(name)

        self._build_location_tab(tabs.tab("Location"))
        self._build_search_tab(tabs.tab("Job Search"))
        self._build_providers_tab(tabs.tab("Providers & Keys"))
        self._build_tracker_tab(tabs.tab("Tracker"))
        self._build_appearance_tab(tabs.tab("Appearance"))

        # ── Save / Cancel buttons ─────────────────────────────────────────────
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 16))

        ctk.CTkButton(btn_row, text="Cancel", width=100,
                      fg_color=("gray75", "gray35"),
                      command=self.destroy).pack(side="right", padx=(8, 0))
        ctk.CTkButton(btn_row, text="Save", width=100,
                      command=self._save).pack(side="right")

        self._status = ctk.CTkLabel(btn_row, text="", font=ctk.CTkFont(size=12),
                                    text_color="gray")
        self._status.pack(side="left")

    # ── Location tab ──────────────────────────────────────────────────────────

    def _build_location_tab(self, frame):
        frame.grid_columnconfigure(1, weight=1)
        loc = self._config.get("location", {})

        row = 0
        for label, key, placeholder in [
            ("City",      "city",  "e.g. Forney"),
            ("State",     "state", "e.g. TX"),
            ("Zip Code",  "zip",   "e.g. 75126"),
        ]:
            ctk.CTkLabel(frame, text=label, anchor="w").grid(
                row=row, column=0, sticky="w", padx=(12,8), pady=8)
            entry = ctk.CTkEntry(frame, placeholder_text=placeholder)
            entry.grid(row=row, column=1, sticky="ew", padx=(0,12), pady=8)
            entry.insert(0, loc.get(key, ""))
            self._widgets[f"loc_{key}"] = entry
            row += 1

        # Radius slider
        ctk.CTkLabel(frame, text="Search Radius", anchor="w").grid(
            row=row, column=0, sticky="w", padx=(12,8), pady=8)

        radius_frame = ctk.CTkFrame(frame, fg_color="transparent")
        radius_frame.grid(row=row, column=1, sticky="ew", padx=(0,12), pady=8)

        radius_var = ctk.IntVar(value=self._config.get("search_radius_miles", 50))
        self._widgets["radius_var"] = radius_var

        radius_label = ctk.CTkLabel(radius_frame, text=f"{radius_var.get()} miles",
                                    width=72, anchor="w")
        radius_label.pack(side="right")

        SNAPS = [10, 25, 50, 75, 100]

        def _on_slide(val):
            snapped = min(SNAPS, key=lambda s: abs(s - int(val)))
            radius_var.set(snapped)
            radius_label.configure(text=f"{snapped} miles")

        slider = ctk.CTkSlider(radius_frame, from_=10, to=100,
                               variable=radius_var, command=_on_slide)
        slider.pack(side="left", fill="x", expand=True)

    # ── Job Search tab ────────────────────────────────────────────────────────

    def _build_search_tab(self, frame):
        frame.grid_columnconfigure(1, weight=1)
        prefs = self._config.get("job_preferences", {})

        # Keywords
        ctk.CTkLabel(frame, text="Keywords", anchor="w").grid(
            row=0, column=0, sticky="w", padx=(12,8), pady=8)
        kw_entry = ctk.CTkEntry(frame, placeholder_text="SOC Analyst, Security Analyst, ...")
        kw_entry.grid(row=0, column=1, sticky="ew", padx=(0,12), pady=8)
        kw_entry.insert(0, ", ".join(prefs.get("keywords", [])))
        self._widgets["keywords"] = kw_entry

        ctk.CTkLabel(frame, text="Work Type", anchor="w").grid(
            row=1, column=0, sticky="w", padx=(12,8), pady=8)
        work_var = ctk.StringVar(value=prefs.get("work_type", "any").capitalize())
        self._widgets["work_type"] = work_var
        ctk.CTkSegmentedButton(
            frame, values=["Any", "Remote", "Hybrid", "Onsite"],
            variable=work_var,
        ).grid(row=1, column=1, sticky="w", padx=(0,12), pady=8)

        ctk.CTkLabel(frame, text="Experience Level", anchor="w").grid(
            row=2, column=0, sticky="w", padx=(12,8), pady=8)
        exp_var = ctk.StringVar(value=prefs.get("experience_level", "any").capitalize())
        self._widgets["experience_level"] = exp_var
        ctk.CTkSegmentedButton(
            frame, values=["Any", "Entry", "Mid", "Senior"],
            variable=exp_var,
        ).grid(row=2, column=1, sticky="w", padx=(0,12), pady=8)

    # ── Providers & Keys tab ──────────────────────────────────────────────────

    def _build_providers_tab(self, frame):
        frame.grid_columnconfigure(0, weight=1)

        providers = [
            ("usajobs",       "USAJobs (always on)",   True,  ["usajobs", "usajobs_email"]),
            ("indeed",        "Indeed",                False, ["indeed"]),
            ("linkedin",      "LinkedIn",              False, ["linkedin"]),
            ("glassdoor",     "Glassdoor",             False, ["glassdoor"]),
            ("adzuna",        "Adzuna",                False, ["adzuna"]),
            ("anthropic",     "Claude AI Assistant",   False, ["anthropic"]),
            ("openrouteservice","OpenRouteService (maps)",False,["openrouteservice"]),
        ]

        scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)

        prov_cfg = self._config.get("providers", {})

        for i, (pid, label, always_on, key_names) in enumerate(providers):
            card = ctk.CTkFrame(scroll, fg_color=("gray88", "gray18"), corner_radius=8)
            card.grid(row=i, column=0, sticky="ew", pady=4, padx=4)
            card.grid_columnconfigure(0, weight=1)

            header = ctk.CTkFrame(card, fg_color="transparent")
            header.grid(row=0, column=0, sticky="ew", padx=12, pady=(10,4))

            enabled_var = ctk.BooleanVar(value=always_on or
                                          prov_cfg.get(pid, {}).get("enabled", False))
            self._widgets[f"enabled_{pid}"] = enabled_var

            cb = ctk.CTkCheckBox(header, text=label, variable=enabled_var,
                                 state="disabled" if always_on else "normal")
            cb.pack(side="left")

            # Key entry fields
            for key_name in key_names:
                is_email = "email" in key_name
                row_frame = ctk.CTkFrame(card, fg_color="transparent")
                row_frame.grid(sticky="ew", padx=12, pady=2)
                row_frame.grid_columnconfigure(1, weight=1)

                ph = "Email address" if is_email else f"{key_name.replace('_',' ').title()} API key"
                ctk.CTkLabel(row_frame, text=ph, width=160, anchor="w",
                             font=ctk.CTkFont(size=12), text_color="gray").grid(
                    row=0, column=0, sticky="w")

                entry = ctk.CTkEntry(row_frame, show="" if is_email else "•",
                                     placeholder_text="not set")
                entry.grid(row=0, column=1, sticky="ew", padx=(8,0))

                existing = keyring_manager.get_key(key_name) or ""
                if existing:
                    entry.insert(0, existing)
                self._widgets[f"key_{key_name}"] = entry

            ctk.CTkFrame(card, height=1, fg_color=("gray80","gray30")).grid(
                sticky="ew", padx=12, pady=(6,0))

    # ── Tracker tab ───────────────────────────────────────────────────────────

    def _build_tracker_tab(self, frame):
        frame.grid_columnconfigure(0, weight=1)
        mode = self._config.get("tracker", {}).get("mode", "local")

        ctk.CTkLabel(frame, text="Application Tracker Storage",
                     font=ctk.CTkFont(size=14, weight="bold"), anchor="w").grid(
            row=0, column=0, sticky="w", padx=12, pady=(16,8))

        mode_var = ctk.StringVar(value=mode)
        self._widgets["tracker_mode"] = mode_var

        options = [
            ("local",  "🖥️  Local Only",    "Saved on this computer only. Works offline."),
            ("google", "☁️  Google Sheets", "Synced to your Google Drive. Accessible anywhere."),
            ("both",   "🔄  Both",          "Local + Google Sheets. Local is the backup."),
        ]
        for i, (val, label, desc) in enumerate(options, 1):
            rb = ctk.CTkRadioButton(frame, text=label, variable=mode_var, value=val)
            rb.grid(row=i, column=0, sticky="w", padx=24, pady=(4,0))
            ctk.CTkLabel(frame, text=desc, font=ctk.CTkFont(size=11),
                         text_color="gray", anchor="w").grid(
                row=i, column=1, sticky="w", padx=8)

        # Google auth section
        ctk.CTkFrame(frame, height=1, fg_color=("gray80","gray30")).grid(
            row=5, column=0, columnspan=2, sticky="ew", padx=12, pady=12)

        self._google_status = ctk.CTkLabel(
            frame, text=self._google_auth_status(),
            font=ctk.CTkFont(size=12), text_color="gray", anchor="w")
        self._google_status.grid(row=6, column=0, sticky="w", padx=12)

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.grid(row=7, column=0, sticky="w", padx=12, pady=8)

        ctk.CTkButton(btn_frame, text="Connect Google Account",
                      width=200, command=self._connect_google).pack(side="left", padx=(0,8))
        ctk.CTkButton(btn_frame, text="Disconnect",
                      width=100, fg_color=("gray75","gray35"),
                      command=self._disconnect_google).pack(side="left")

    def _google_auth_status(self) -> str:
        token_path = str(config_manager.get_config_dir() / "google_token.json")
        import os
        return ("✅  Connected to Google" if os.path.exists(token_path)
                else "⚠️  Not connected to Google")

    def _connect_google(self):
        self._google_status.configure(text="⟳  Opening browser for Google sign-in...")
        def _run():
            try:
                from integrations.google_sheets import GoogleSheetsTracker
                token_path = str(config_manager.get_config_dir() / "google_token.json")
                creds_path = str(config_manager.get_config_dir() / "google_credentials.json")
                tracker = GoogleSheetsTracker(token_path=token_path)
                tracker.authenticate(creds_path)
                self._google_status.configure(text="✅  Connected to Google")
            except FileNotFoundError:
                self._google_status.configure(
                    text="⚠️  credentials.json not found.\n"
                         "Download from Google Cloud Console → APIs & Services → Credentials.")
            except Exception as e:
                self._google_status.configure(text=f"⚠️  Connection failed: {str(e)[:80]}")
        threading.Thread(target=_run, daemon=True).start()

    def _disconnect_google(self):
        try:
            from integrations.google_sheets import GoogleSheetsTracker
            token_path = str(config_manager.get_config_dir() / "google_token.json")
            GoogleSheetsTracker(token_path=token_path).revoke()
            self._google_status.configure(text="⚠️  Not connected to Google")
        except Exception as e:
            self._google_status.configure(text=f"Error: {e}")

    # ── Appearance tab ────────────────────────────────────────────────────────

    def _build_appearance_tab(self, frame):
        frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(frame, text="Theme", anchor="w").grid(
            row=0, column=0, sticky="w", padx=(12,8), pady=16)

        theme_var = ctk.StringVar(value=self._config.get("theme", "system").capitalize())
        self._widgets["theme"] = theme_var

        ctk.CTkSegmentedButton(
            frame, values=["Light", "Dark", "System"], variable=theme_var,
            command=lambda v: ctk.set_appearance_mode(v.lower()),
        ).grid(row=0, column=1, sticky="w", padx=(0,12), pady=16)

        ctk.CTkFrame(frame, height=1, fg_color=("gray80","gray30")).grid(
            row=1, column=0, columnspan=2, sticky="ew", padx=12)

        ctk.CTkLabel(frame, text="Reset",
                     font=ctk.CTkFont(size=13, weight="bold"), anchor="w").grid(
            row=2, column=0, sticky="w", padx=(12,8), pady=(16,4))

        ctk.CTkLabel(
            frame,
            text="Reset all settings to defaults and re-run the setup wizard.\n"
                 "Your tracked applications will not be deleted.",
            font=ctk.CTkFont(size=12), text_color="gray", anchor="w", justify="left",
        ).grid(row=3, column=0, columnspan=2, sticky="w", padx=12)

        ctk.CTkButton(
            frame, text="Reset to Defaults", width=160,
            fg_color="#d32f2f", hover_color="#b71c1c",
            command=self._reset_to_defaults,
        ).grid(row=4, column=0, sticky="w", padx=12, pady=12)

        # App version
        ctk.CTkLabel(
            frame, text=f"JobTrack v{APP_VERSION}",
            font=ctk.CTkFont(size=11), text_color="gray",
        ).grid(row=10, column=0, columnspan=2, sticky="sw", padx=12, pady=12)

    def _reset_to_defaults(self):
        """Confirm then wipe config and restart wizard."""
        dialog = ctk.CTkInputDialog(
            text="Type RESET to confirm. This will re-run the setup wizard.\n"
                 "(Your tracked applications will not be deleted.)",
            title="Confirm Reset")
        val = dialog.get_input()
        if val and val.strip().upper() == "RESET":
            config_manager.reset()
            self.destroy()
            # Restart wizard by setting setup_complete=False and relaunching
            fresh = config_manager.load()
            fresh["setup_complete"] = False
            config_manager.save(fresh)
            self._status.configure(text="Reset complete — restart JobTrack to run setup.")

    # ── Save ──────────────────────────────────────────────────────────────────

    def _save(self):
        """Read all widget values back into config and persist."""
        # ── Location ──────────────────────────────────────────────────────────
        loc = self._config.setdefault("location", {})
        loc["city"]  = self._widgets["loc_city"].get().strip()
        loc["state"] = normalize_state(self._widgets["loc_state"].get().strip())
        loc["zip"]   = self._widgets["loc_zip"].get().strip()
        self._config["search_radius_miles"] = self._widgets["radius_var"].get()

        # ── Job search ────────────────────────────────────────────────────────
        prefs = self._config.setdefault("job_preferences", {})
        raw_kw = self._widgets["keywords"].get()
        prefs["keywords"] = [k.strip() for k in raw_kw.split(",") if k.strip()]
        prefs["work_type"]        = self._widgets["work_type"].get().lower()
        prefs["experience_level"] = self._widgets["experience_level"].get().lower()

        # ── Providers (enabled flags) ─────────────────────────────────────────
        prov_cfg = self._config.setdefault("providers", {})
        for pid in ["indeed", "linkedin", "glassdoor", "adzuna"]:
            prov_cfg.setdefault(pid, {})["enabled"] = \
                self._widgets[f"enabled_{pid}"].get()

        # ── API keys (keyring) ────────────────────────────────────────────────
        key_fields = ["usajobs", "usajobs_email", "indeed", "linkedin",
                      "glassdoor", "adzuna", "anthropic", "openrouteservice"]
        for key_name in key_fields:
            val = self._widgets[f"key_{key_name}"].get().strip()
            if val:
                keyring_manager.save_key(key_name, val)

        # ── Tracker ───────────────────────────────────────────────────────────
        self._config.setdefault("tracker", {})["mode"] = \
            self._widgets["tracker_mode"].get()

        # ── Appearance ────────────────────────────────────────────────────────
        theme = self._widgets["theme"].get().lower()
        self._config["theme"] = theme
        ctk.set_appearance_mode(theme)

        # ── Persist ───────────────────────────────────────────────────────────
        config_manager.save(self._config)
        self._status.configure(text="✅  Saved")

        if self._on_save:
            self._on_save(self._config)

        self.after(800, self.destroy)
