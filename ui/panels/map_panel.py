"""
ui/panels/map_panel.py
=======================
Map panel — shows jobs as pins on a Folium map rendered in a WebView.
Calculates commute times via OpenRouteService.
"""

import customtkinter as ctk


class MapPanel(ctk.CTkFrame):
    """Displays job listings on an interactive map."""

    def __init__(self, parent, config: dict, main_window, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.config = config
        self.main_window = main_window
        self._results = []
        self._build()

    def _build(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Toolbar
        toolbar = ctk.CTkFrame(self, fg_color=("gray90", "gray20"),
                               corner_radius=0, height=54)
        toolbar.grid(row=0, column=0, sticky="ew")
        toolbar.grid_propagate(False)

        ctk.CTkLabel(toolbar, text="🗺️  Map View",
                     font=ctk.CTkFont(size=15, weight="bold"),
                     ).pack(side="left", padx=16, pady=14)

        self._commute_btn = ctk.CTkButton(
            toolbar,
            text="Calculate Commute Times",
            width=200, height=32,
            command=self._calculate_commutes,
        )
        self._commute_btn.pack(side="right", padx=16, pady=10)

        # Map placeholder — will be replaced with actual WebView in Phase 9
        self._map_placeholder = ctk.CTkFrame(
            self, fg_color=("gray85", "gray25"), corner_radius=0)
        self._map_placeholder.grid(row=1, column=0, sticky="nsew")
        self._map_placeholder.grid_rowconfigure(0, weight=1)
        self._map_placeholder.grid_columnconfigure(0, weight=1)

        self._map_label = ctk.CTkLabel(
            self._map_placeholder,
            text="🗺️\n\nMap will appear here after your first search.\n"
                 "Jobs will be shown as color-coded pins\nbased on commute distance.",
            font=ctk.CTkFont(size=14), text_color="gray", justify="center",
        )
        self._map_label.grid(row=0, column=0)

    def on_results_updated(self, results: list):
        """Called when new search results are available."""
        self._results = results
        count = len([j for j in results if j.latitude and j.longitude])
        self._map_label.configure(
            text=f"🗺️\n\n{len(results)} jobs loaded • {count} have map coordinates\n\n"
                 "Full map rendering coming in Phase 9.\n"
                 "Click 'Calculate Commute Times' to compute drive times."
        )

    def _calculate_commutes(self):
        """Placeholder — Phase 9 will wire up OpenRouteService."""
        ctk.CTkLabel(
            self._map_placeholder,
            text="⟳  Commute calculation coming in Phase 9",
            font=ctk.CTkFont(size=13), text_color="gray",
        ).grid(row=1, column=0, pady=8)
