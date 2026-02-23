"""
ui/dialogs/about_dialog.py
============================
About dialog: version, tagline, GitHub link, privacy statement, MIT license.
"""

import webbrowser
import customtkinter as ctk

APP_VERSION  = "1.0.4"
GITHUB_URL   = "https://github.com/Irehund/JobTracker"
LICENSE_TEXT = """\
MIT License

Copyright (c) 2026 JobTrack Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.\
"""


class AboutDialog(ctk.CTkToplevel):
    """About / credits dialog launched from the sidebar."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.title("About JobTrack")
        self.geometry("480x540")
        self.resizable(False, False)
        self.grab_set()
        self._build()
        self._center_on_parent(parent)

    def _center_on_parent(self, parent):
        self.update_idletasks()
        px = parent.winfo_rootx() + parent.winfo_width()  // 2
        py = parent.winfo_rooty() + parent.winfo_height() // 2
        self.geometry(f"480x540+{px - 240}+{py - 270}")

    def _build(self):
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ── Header ────────────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color=("gray88", "gray18"), corner_radius=0)
        header.grid(row=0, column=0, sticky="ew")

        ctk.CTkLabel(
            header, text="JobTrack",
            font=ctk.CTkFont(size=32, weight="bold"),
        ).pack(pady=(24, 4))

        ctk.CTkLabel(
            header,
            text=f"v{APP_VERSION}  •  Job Search Manager",
            font=ctk.CTkFont(size=13), text_color="gray",
        ).pack(pady=(0, 8))

        ctk.CTkLabel(
            header,
            text="Find, track, and land your next cybersecurity role.",
            font=ctk.CTkFont(size=12), text_color="gray",
        ).pack(pady=(0, 20))

        # ── Privacy statement ─────────────────────────────────────────────────
        privacy = ctk.CTkFrame(self, fg_color="transparent")
        privacy.grid(row=1, column=0, sticky="ew", padx=20, pady=12)

        ctk.CTkLabel(
            privacy,
            text="🔒  Privacy",
            font=ctk.CTkFont(size=13, weight="bold"), anchor="w",
        ).pack(fill="x")

        ctk.CTkLabel(
            privacy,
            text=(
                "JobTrack never collects your data. Everything you enter —\n"
                "your location, job preferences, API keys, and applications —\n"
                "stays on your computer or your own Google account.\n"
                "JobTrack connects only to the job board APIs you configure."
            ),
            font=ctk.CTkFont(size=12), text_color="gray",
            justify="left", anchor="w",
        ).pack(fill="x", pady=(4, 0))

        # ── License ───────────────────────────────────────────────────────────
        license_frame = ctk.CTkFrame(self, fg_color="transparent")
        license_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 4))
        license_frame.grid_rowconfigure(1, weight=1)
        license_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            license_frame,
            text="📄  License",
            font=ctk.CTkFont(size=13, weight="bold"), anchor="w",
        ).grid(row=0, column=0, sticky="w", pady=(0, 4))

        textbox = ctk.CTkTextbox(
            license_frame, font=ctk.CTkFont(size=10, family="Courier"),
            fg_color=("gray90", "gray15"), height=130,
        )
        textbox.grid(row=1, column=0, sticky="nsew")
        textbox.insert("1.0", LICENSE_TEXT)
        textbox.configure(state="disabled")

        # ── Footer buttons ────────────────────────────────────────────────────
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.grid(row=3, column=0, sticky="ew", padx=20, pady=12)

        ctk.CTkButton(
            footer,
            text="⭐  View on GitHub",
            width=160, height=36,
            command=lambda: webbrowser.open(GITHUB_URL),
        ).pack(side="left")

        ctk.CTkButton(
            footer,
            text="Close",
            width=80, height=36,
            fg_color=("gray75", "gray35"),
            command=self.destroy,
        ).pack(side="right")
