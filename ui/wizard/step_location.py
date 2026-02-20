"""
ui/wizard/step_location.py
===========================
Step 4: Home location entry and search radius slider.
"""

import customtkinter as ctk
from ui.wizard.base_step import BaseStep
from core.utils import normalize_state


class StepLocation(BaseStep):
    TITLE = "Where Are You Located?"
    SUBTITLE = "JobTrack will search for jobs near your home and calculate commute times."

    def _build_content(self, frame):
        frame.grid_columnconfigure(0, weight=1)

        # ── Location entry ────────────────────────────────────────────────────
        loc_card = ctk.CTkFrame(frame, fg_color=("gray90", "gray20"), corner_radius=10)
        loc_card.pack(fill="x", pady=(0, 16))
        loc_card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(loc_card, text="Your Location",
                     font=ctk.CTkFont(size=14, weight="bold"), anchor="w",
                     ).pack(fill="x", padx=16, pady=(14, 8))

        # Zip code
        zip_row = ctk.CTkFrame(loc_card, fg_color="transparent")
        zip_row.pack(fill="x", padx=16, pady=4)
        ctk.CTkLabel(zip_row, text="Zip Code", width=110, anchor="w").pack(side="left")
        self._zip_entry = ctk.CTkEntry(zip_row, placeholder_text="e.g. 75126", width=120)
        self._zip_entry.pack(side="left", padx=(8, 0))
        existing_zip = self.config.get("location", {}).get("zip", "")
        if existing_zip:
            self._zip_entry.insert(0, existing_zip)

        # City
        city_row = ctk.CTkFrame(loc_card, fg_color="transparent")
        city_row.pack(fill="x", padx=16, pady=4)
        ctk.CTkLabel(city_row, text="City", width=110, anchor="w").pack(side="left")
        self._city_entry = ctk.CTkEntry(city_row, placeholder_text="e.g. Forney")
        self._city_entry.pack(side="left", fill="x", expand=True, padx=(8, 0))
        existing_city = self.config.get("location", {}).get("city", "")
        if existing_city:
            self._city_entry.insert(0, existing_city)

        # State
        state_row = ctk.CTkFrame(loc_card, fg_color="transparent")
        state_row.pack(fill="x", padx=16, pady=(4, 14))
        ctk.CTkLabel(state_row, text="State", width=110, anchor="w").pack(side="left")
        self._state_entry = ctk.CTkEntry(state_row, placeholder_text="e.g. TX or Texas", width=160)
        self._state_entry.pack(side="left", padx=(8, 0))
        existing_state = self.config.get("location", {}).get("state", "")
        if existing_state:
            self._state_entry.insert(0, existing_state)

        # ── Radius slider ─────────────────────────────────────────────────────
        radius_card = ctk.CTkFrame(frame, fg_color=("gray90", "gray20"), corner_radius=10)
        radius_card.pack(fill="x")

        ctk.CTkLabel(radius_card, text="Search Radius",
                     font=ctk.CTkFont(size=14, weight="bold"), anchor="w",
                     ).pack(fill="x", padx=16, pady=(14, 4))

        ctk.CTkLabel(radius_card, text="How far are you willing to travel for work?",
                     font=ctk.CTkFont(size=12), text_color="gray", anchor="w",
                     ).pack(fill="x", padx=16, pady=(0, 8))

        self._radius_var = ctk.IntVar(value=self.config.get("search_radius_miles", 50))
        self._radius_label = ctk.CTkLabel(
            radius_card,
            text=f"{self._radius_var.get()} miles",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        self._radius_label.pack(pady=(4, 0))

        slider = ctk.CTkSlider(
            radius_card,
            from_=10, to=100,
            number_of_steps=4,   # 10, 32.5, 55, 77.5, 100 — we'll snap to nearest
            variable=self._radius_var,
            command=self._on_radius_change,
        )
        slider.pack(fill="x", padx=32, pady=8)

        # Tick labels
        tick_frame = ctk.CTkFrame(radius_card, fg_color="transparent")
        tick_frame.pack(fill="x", padx=28, pady=(0, 14))
        for val in ["10 mi", "25 mi", "50 mi", "75 mi", "100 mi"]:
            ctk.CTkLabel(tick_frame, text=val, font=ctk.CTkFont(size=11),
                         text_color="gray").pack(side="left", expand=True)

    def _on_radius_change(self, value):
        """Snap slider to nearest preset value."""
        presets = [10, 25, 50, 75, 100]
        snapped = min(presets, key=lambda x: abs(x - value))
        self._radius_var.set(snapped)
        self._radius_label.configure(text=f"{snapped} miles")

    def validate(self) -> tuple[bool, str]:
        city  = self._city_entry.get().strip()
        state = self._state_entry.get().strip()
        zip_  = self._zip_entry.get().strip()

        if not city and not zip_:
            return False, "Please enter at least a city name or zip code."
        if city and not state:
            return False, "Please enter your state (e.g. TX or Texas)."
        return True, ""

    def on_exit(self):
        state_raw = self._state_entry.get().strip()
        state_normalized = normalize_state(state_raw) or state_raw.upper()[:2]

        if "location" not in self.config:
            self.config["location"] = {}

        self.config["location"]["zip"]   = self._zip_entry.get().strip()
        self.config["location"]["city"]  = self._city_entry.get().strip()
        self.config["location"]["state"] = state_normalized
        self.config["search_radius_miles"] = self._radius_var.get()
