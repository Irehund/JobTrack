"""
core/utils.py
==============
Shared utility functions used throughout JobTrack.
No UI imports. No external API calls.
"""

import logging
import os
from datetime import datetime
from pathlib import Path


def setup_logging(log_level: int = logging.INFO) -> logging.Logger:
    """
    Configure and return the root JobTrack logger.
    Writes to both console and a rotating log file in AppData.
    """
    # TODO: Set up logging with a FileHandler (logs/jobtrack.log) and StreamHandler
    raise NotImplementedError


def haversine_distance(
    lat1: float, lon1: float,
    lat2: float, lon2: float,
) -> float:
    """
    Calculate the great-circle distance between two points on Earth.

    Returns:
        Distance in miles.
    """
    # TODO: Implement haversine formula
    raise NotImplementedError


def format_salary(
    salary_min: float | None,
    salary_max: float | None,
    interval: str = "annual",
    currency: str = "USD",
) -> str:
    """
    Format a salary range as a human-readable string.

    Examples:
        format_salary(80000, 100000)         -> "$80,000 – $100,000 / year"
        format_salary(25, 30, "hourly")      -> "$25 – $30 / hour"
        format_salary(None, None)            -> "Salary not listed"
    """
    # TODO: Handle all None combinations and format with locale-appropriate separators
    raise NotImplementedError


def truncate(text: str, max_length: int = 200) -> str:
    """Truncate text to max_length characters, appending '...' if cut."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3].rstrip() + "..."


def days_ago(dt: datetime) -> str:
    """
    Return a human-readable relative time string.

    Examples:
        "Today", "Yesterday", "3 days ago", "2 weeks ago"
    """
    # TODO: Compute delta between dt and datetime.now(), return friendly string
    raise NotImplementedError


def normalize_state(state_input: str) -> str:
    """
    Normalize a US state to its two-letter abbreviation.
    Accepts full names ("Texas") or abbreviations ("TX" -> "TX").
    Returns empty string if not recognized.
    """
    # TODO: Implement state name -> abbreviation lookup dict
    raise NotImplementedError
