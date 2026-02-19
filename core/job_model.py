"""
core/job_model.py
==================
Defines the JobListing dataclass — the common data schema used for
all job results regardless of which provider they came from.

Every provider module normalizes its raw API response into a JobListing
so the rest of the app never needs to know which provider a job came from.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class JobListing:
    """
    Normalized representation of a single job listing.

    Required fields must be populated by every provider.
    Optional fields are filled in when available.
    """

    # ── Required ──────────────────────────────────────────
    job_id: str               # Unique ID — use f"{provider}_{source_id}" to avoid collisions
    provider: str             # Source provider name: "usajobs", "indeed", etc.
    title: str                # Job title
    company: str              # Employer / organization name
    location: str             # Human-readable location string, e.g. "Dallas, TX"

    # ── Strongly Recommended ──────────────────────────────
    url: str = ""                          # Direct link to the full job posting
    description: str = ""                  # Full or truncated job description
    date_posted: Optional[datetime] = None # When the listing was posted
    closing_date: Optional[datetime] = None

    # ── Location Details ──────────────────────────────────
    city: str = ""
    state: str = ""
    zip_code: str = ""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_remote: bool = False
    is_hybrid: bool = False

    # ── Job Details ───────────────────────────────────────
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: str = "USD"
    salary_interval: str = ""             # "annual" | "hourly" | ""
    employment_type: str = ""             # "full_time" | "part_time" | "contract" | ""
    experience_level: str = ""            # "entry" | "mid" | "senior" | ""

    # ── Computed (filled in by core, not providers) ───────
    commute_minutes: Optional[int] = None  # Set by commute_calculator.py in map view
    distance_miles: Optional[float] = None # Straight-line distance from user's home

    # ── Internal ──────────────────────────────────────────
    raw: dict = field(default_factory=dict, repr=False)  # Original API response for debugging

    def dedup_key(self) -> str:
        """
        Returns a string used to detect duplicate listings across providers.
        Two listings with the same dedup_key are considered the same job.
        """
        # TODO: Return a normalized string combining title + company + city/state
        # Use lowercase and strip whitespace to catch minor formatting differences
        raise NotImplementedError

    def is_within_radius(self, home_lat: float, home_lon: float, radius_miles: float) -> bool:
        """
        Returns True if this job is within radius_miles of the given coordinates.
        Returns True if job coordinates are unknown (don't filter out unlocatable jobs).
        """
        # TODO: Implement haversine distance check
        # If self.latitude or self.longitude is None, return True
        raise NotImplementedError
