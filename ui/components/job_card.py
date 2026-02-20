"""
ui/components/job_card.py
==========================
Compact/expandable job listing card used in the Jobs panel.
"""

import webbrowser
import customtkinter as ctk
from core.job_model import JobListing
from core.utils import format_salary, days_ago


class JobCard(ctk.CTkFrame):
    """A single job listing displayed as an expandable card."""

    def __init__(self, parent, job: JobListing, main_window, **kwargs):
        super().__init__(parent, fg_color=("gray90", "gray20"),
                         corner_radius=10, **kwargs)
        self.job = job
        self.main_window = main_window
        self._expanded = False
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)

        # ── Compact view (always shown) ───────────────────────────────────────
        compact = ctk.CTkFrame(self, fg_color="transparent")
        compact.grid(row=0, column=0, sticky="ew", padx=14, pady=10)
        compact.grid_columnconfigure(1, weight=1)

        # Provider badge
        provider_colors = {
            "usajobs": "#1565C0", "indeed": "#2164F3",
            "linkedin": "#0077B5", "glassdoor": "#0CAA41",
            "adzuna": "#FF6B35",
        }
        badge_color = provider_colors.get(self.job.provider, "gray")
        ctk.CTkLabel(
            compact,
            text=self.job.provider.upper(),
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color="white",
            fg_color=badge_color,
            corner_radius=4,
            width=64, height=20,
        ).grid(row=0, column=0, rowspan=2, padx=(0, 12), sticky="n", pady=2)

        # Title and company
        ctk.CTkLabel(compact, text=self.job.title,
                     font=ctk.CTkFont(size=14, weight="bold"),
                     anchor="w").grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(compact,
                     text=f"{self.job.company}  •  {self.job.location}",
                     font=ctk.CTkFont(size=12), text_color="gray",
                     anchor="w").grid(row=1, column=1, sticky="w")

        # Right side — salary + date
        right = ctk.CTkFrame(compact, fg_color="transparent")
        right.grid(row=0, column=2, rowspan=2, padx=(12, 0), sticky="e")

        salary_str = format_salary(
            self.job.salary_min, self.job.salary_max,
            self.job.salary_interval,
        )
        ctk.CTkLabel(right, text=salary_str,
                     font=ctk.CTkFont(size=12, weight="bold"),
                     anchor="e").pack(anchor="e")

        date_str = days_ago(self.job.date_posted) if self.job.date_posted else ""
        tags = []
        if self.job.is_remote: tags.append("🌐 Remote")
        if self.job.is_hybrid: tags.append("🏢 Hybrid")
        tag_str = "  ".join(tags)
        ctk.CTkLabel(right,
                     text=f"{date_str}  {tag_str}".strip(),
                     font=ctk.CTkFont(size=11), text_color="gray",
                     anchor="e").pack(anchor="e")

        # Expand toggle
        self._expand_btn = ctk.CTkButton(
            compact, text="▼", width=28, height=28,
            fg_color="transparent",
            text_color=("gray40", "gray60"),
            hover_color=("gray80", "gray30"),
            command=self._toggle_expand,
        )
        self._expand_btn.grid(row=0, column=3, rowspan=2, padx=(8, 0))

        # ── Expanded view (hidden by default) ─────────────────────────────────
        self._detail_frame = ctk.CTkFrame(self, fg_color="transparent")
        # Not gridded until expanded

        if self.job.description:
            ctk.CTkLabel(
                self._detail_frame, text=self.job.description[:600],
                font=ctk.CTkFont(size=12), text_color="gray",
                wraplength=680, justify="left", anchor="w",
            ).pack(fill="x", padx=14, pady=(0, 8))

        btn_row = ctk.CTkFrame(self._detail_frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=14, pady=(0, 10))

        ctk.CTkButton(
            btn_row, text="🔗  View Full Posting",
            width=160, height=32,
            command=lambda: webbrowser.open(self.job.url) if self.job.url else None,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_row, text="✓  Mark as Applied",
            width=150, height=32,
            fg_color="#4CAF50", hover_color="#388E3C",
            command=self._mark_applied,
        ).pack(side="left")

    def _toggle_expand(self):
        self._expanded = not self._expanded
        if self._expanded:
            self._detail_frame.grid(row=1, column=0, sticky="ew")
            self._expand_btn.configure(text="▲")
        else:
            self._detail_frame.grid_remove()
            self._expand_btn.configure(text="▼")

    def _mark_applied(self):
        """Save this job to the applications tracker."""
        from db import jobs_repo
        from datetime import datetime, timezone
        try:
            jobs_repo.add_application({
                "job_id":       self.job.job_id,
                "provider":     self.job.provider,
                "company":      self.job.company,
                "title":        self.job.title,
                "location":     self.job.location,
                "job_url":      self.job.url,
                "date_applied": datetime.now(timezone.utc).isoformat(),
                "status":       "Applied",
            })
            # Visual confirmation
            self.configure(fg_color=("gray80", "gray15"))
            ctk.CTkLabel(self, text="✓ Added to Tracker",
                         text_color="#4CAF50",
                         font=ctk.CTkFont(size=12)).grid(row=2, column=0, pady=4)
        except Exception as e:
            print(f"Error saving application: {e}")
