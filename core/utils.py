"""
core/utils.py
==============
Shared utility functions used throughout JobTrack.
No UI imports. No external API calls.
"""

import logging
import logging.handlers
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def setup_logging(log_level: int = logging.INFO) -> logging.Logger:
    """
    Configure and return the root JobTrack logger.
    Writes to both console and a rotating log file in the AppData directory.
    Safe to call multiple times — handlers are only added once.
    """
    logger = logging.getLogger("jobtrack")

    if logger.handlers:
        return logger  # Already configured

    logger.setLevel(log_level)
    formatter = logging.Formatter(
        "%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    # File handler — rotating, max 1MB, keep 3 backups
    try:
        from core.config_manager import get_config_dir
        log_path = get_config_dir() / "jobtrack.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_path, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception:
        pass  # If we can't write logs, keep console handler and continue

    return logger


def haversine_distance(
    lat1: float, lon1: float,
    lat2: float, lon2: float,
) -> float:
    """
    Calculate the great-circle distance between two points on Earth.
    Returns distance in miles.
    """
    import math
    R = 3958.8
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


def format_salary(
    salary_min: Optional[float],
    salary_max: Optional[float],
    interval: str = "annual",
    currency: str = "USD",
) -> str:
    """
    Format a salary range as a human-readable string.

    Examples:
        format_salary(80000, 100000)          -> "$80,000 – $100,000 / year"
        format_salary(25, 30, "hourly")       -> "$25 – $30 / hour"
        format_salary(90000, None)            -> "$90,000+ / year"
        format_salary(None, None)             -> "Salary not listed"
    """
    symbol = "$" if currency == "USD" else currency + " "
    period = "/ year" if interval == "annual" else "/ hour"

    def _fmt(n: float) -> str:
        if interval == "annual":
            return f"{symbol}{n:,.0f}"
        return f"{symbol}{n:,.2f}".rstrip("0").rstrip(".")

    if salary_min is None and salary_max is None:
        return "Salary not listed"
    if salary_min is not None and salary_max is not None:
        return f"{_fmt(salary_min)} – {_fmt(salary_max)} {period}"
    if salary_min is not None:
        return f"{_fmt(salary_min)}+ {period}"
    return f"Up to {_fmt(salary_max)} {period}"


def truncate(text: str, max_length: int = 200) -> str:
    """Truncate text to max_length characters, appending '...' if cut."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3].rstrip() + "..."


def days_ago(dt: datetime) -> str:
    """
    Return a human-readable relative time string.

    Examples:
        "Today", "Yesterday", "3 days ago", "2 weeks ago", "1 month ago"
    """
    now = datetime.now(timezone.utc)
    # Make dt timezone-aware if it isn't already
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    delta = now - dt
    days = delta.days

    if days < 0:
        return "Just posted"
    if days == 0:
        return "Today"
    if days == 1:
        return "Yesterday"
    if days < 7:
        return f"{days} days ago"
    if days < 14:
        return "1 week ago"
    if days < 30:
        return f"{days // 7} weeks ago"
    if days < 60:
        return "1 month ago"
    return f"{days // 30} months ago"


def normalize_state(state_input: str) -> str:
    """
    Normalize a US state to its two-letter abbreviation.
    Accepts full names ("Texas") or abbreviations ("tx" -> "TX").
    Returns empty string if not recognized.
    """
    _STATES = {
        "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
        "california": "CA", "colorado": "CO", "connecticut": "CT", "delaware": "DE",
        "florida": "FL", "georgia": "GA", "hawaii": "HI", "idaho": "ID",
        "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS",
        "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
        "massachusetts": "MA", "michigan": "MI", "minnesota": "MN", "mississippi": "MS",
        "missouri": "MO", "montana": "MT", "nebraska": "NE", "nevada": "NV",
        "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM", "new york": "NY",
        "north carolina": "NC", "north dakota": "ND", "ohio": "OH", "oklahoma": "OK",
        "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC",
        "south dakota": "SD", "tennessee": "TN", "texas": "TX", "utah": "UT",
        "vermont": "VT", "virginia": "VA", "washington": "WA", "west virginia": "WV",
        "wisconsin": "WI", "wyoming": "WY", "district of columbia": "DC",
    }
    cleaned = state_input.strip().lower()
    # Check full name first
    if cleaned in _STATES:
        return _STATES[cleaned]
    # Check if it's already a valid abbreviation
    upper = cleaned.upper()
    if upper in _STATES.values():
        return upper
    return ""


def parse_iso_date(date_str: str) -> Optional[datetime]:
    """
    Safely parse an ISO 8601 date string, returning None on failure.
    Handles both date-only ("2026-02-19") and full datetime strings.
    """
    if not date_str:
        return None
    # Strip trailing Z and replace with +00:00 for Python < 3.11 compat
    date_str = date_str.strip().rstrip("Z")
    formats = [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str[:len(fmt) + 5], fmt)
        except ValueError:
            continue
    return None
