"""
ui/panels/map_panel.py
=======================
Map panel — renders jobs as color-coded pins on a Folium map.
Commute times calculated on demand via OpenRouteService.
Map displayed in a system browser (via webbrowser module) since
CustomTkinter has no native WebView — Phase 9 approach.
"""

import os
import tempfile
import threading
import webbrowser
import customtkinter as ctk
from core.job_model import JobListing


class MapPanel(ctk.CTkFrame):
    """Displays job listings on an interactive Folium map."""

    def __init__(self, parent, config: dict, main_window, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.config = config
        self.main_window = main_window
        self._results: list[JobListing] = []
        self._map_path: str = ""
        self._build()

    def _build(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ── Toolbar ───────────────────────────────────────────────────────────
        toolbar = ctk.CTkFrame(self, fg_color=("gray90", "gray20"),
                               corner_radius=0, height=54)
        toolbar.grid(row=0, column=0, sticky="ew")
        toolbar.grid_propagate(False)
        toolbar.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(toolbar, text="🗺️  Map View",
                     font=ctk.CTkFont(size=15, weight="bold"),
                     ).grid(row=0, column=0, padx=16, pady=14, sticky="w")

        btn_frame = ctk.CTkFrame(toolbar, fg_color="transparent")
        btn_frame.grid(row=0, column=2, padx=12, pady=8)

        self._commute_btn = ctk.CTkButton(
            btn_frame,
            text="🚗  Calculate Commutes",
            width=190, height=34,
            command=self._calculate_commutes,
        )
        self._commute_btn.pack(side="left", padx=(0, 8))

        self._open_btn = ctk.CTkButton(
            btn_frame,
            text="🌐  Open Map in Browser",
            width=190, height=34,
            fg_color=("gray75", "gray35"),
            command=self._open_in_browser,
            state="disabled",
        )
        self._open_btn.pack(side="left")

        # ── Info panel ────────────────────────────────────────────────────────
        self._info_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._info_frame.grid(row=1, column=0, sticky="nsew")
        self._info_frame.grid_rowconfigure(0, weight=1)
        self._info_frame.grid_columnconfigure(0, weight=1)

        self._status_label = ctk.CTkLabel(
            self._info_frame,
            text="🗺️\n\nRun a search first, then open this panel\nto see jobs plotted on an interactive map.",
            font=ctk.CTkFont(size=14), text_color="gray", justify="center",
        )
        self._status_label.grid(row=0, column=0)

        # Stats card
        self._stats_frame = ctk.CTkFrame(self._info_frame,
                                         fg_color=("gray90", "gray20"),
                                         corner_radius=10)
        # Not shown until results are loaded

    def on_results_updated(self, results: list[JobListing]):
        """Called by main_window when a new search completes."""
        self._results = results
        locatable = sum(1 for j in results if j.latitude and j.longitude)
        with_commute = sum(1 for j in results if j.commute_minutes is not None)

        self._status_label.configure(
            text=f"📍  {len(results)} jobs loaded  •  {locatable} have map coordinates"
                 f"  •  {with_commute} commutes calculated\n\n"
                 "Click 'Calculate Commutes' to get drive times, then\n"
                 "'Open Map in Browser' to view the interactive map.",
        )
        # Re-enable open button if map already exists
        if self._map_path and os.path.exists(self._map_path):
            self._open_btn.configure(state="normal")

    def _calculate_commutes(self):
        """Run commute calculation in background thread."""
        if not self._results:
            self._status_label.configure(text="No results to calculate commutes for.\nRun a search first.")
            return

        loc = self.config.get("location", {})
        lat = loc.get("latitude")
        lon = loc.get("longitude")

        if not lat or not lon:
            self._status_label.configure(
                text="⚠️  Home coordinates not set.\n"
                     "Go to Preferences → Location and update your address.")
            return

        self._commute_btn.configure(state="disabled", text="⟳  Calculating...")
        self.main_window.show_progress("Calculating commute times...")

        def _run():
            try:
                from core.commute_calculator import calculate_batch

                locatable = [j for j in self._results
                             if j.latitude is not None and j.longitude is not None]

                def _progress(done, total):
                    self._status_label.configure(
                        text=f"⟳  Calculating commutes... {done}/{total}")

                calculate_batch(float(lat), float(lon), locatable, _progress)
                self._build_map(float(lat), float(lon))

            except Exception as e:
                self._status_label.configure(
                    text=f"⚠️  Commute calculation failed:\n{str(e)[:120]}\n\n"
                         "Check your OpenRouteService API key in Preferences.")
            finally:
                self._commute_btn.configure(state="normal", text="🚗  Calculate Commutes")
                self.main_window.hide_progress()

        threading.Thread(target=_run, daemon=True).start()

    def _build_map(self, home_lat: float, home_lon: float):
        """Generate the Folium HTML map and enable the Open in Browser button."""
        try:
            from core.map_builder import build_map

            # Write to a temp file that persists for the session
            if not self._map_path:
                tmp = tempfile.NamedTemporaryFile(
                    suffix=".html", delete=False, prefix="jobtrack_map_")
                self._map_path = tmp.name
                tmp.close()

            build_map(
                listings=self._results,
                home_lat=home_lat,
                home_lon=home_lon,
                output_path=self._map_path,
            )

            with_commute = sum(1 for j in self._results if j.commute_minutes is not None)
            locatable    = sum(1 for j in self._results if j.latitude and j.longitude)

            self._status_label.configure(
                text=f"✅  Map ready — {locatable} jobs plotted, "
                     f"{with_commute} with commute times.\n\n"
                     "Click 'Open Map in Browser' to view the interactive map.\n"
                     "Pins are color-coded: 🟢 <30 min  🟠 30–60 min  🔴 >60 min  ⚫ unknown",
            )
            self._open_btn.configure(state="normal")
            logger_msg = f"Map built: {self._map_path}"

        except Exception as e:
            self._status_label.configure(
                text=f"⚠️  Map generation failed:\n{str(e)[:120]}")

    def _open_in_browser(self):
        """Open the generated map HTML in the system's default browser."""
        if self._map_path and os.path.exists(self._map_path):
            webbrowser.open(f"file://{self._map_path}")
        else:
            self._status_label.configure(
                text="No map generated yet. Click 'Calculate Commutes' first.")
