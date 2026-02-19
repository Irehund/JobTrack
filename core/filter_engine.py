"""
core/filter_engine.py
======================
Applies the user's saved preferences to a list of JobListing objects.
Called after job_fetcher returns results to trim the list before display.

All filtering is done in-memory — no API calls.
"""

from core.job_model import JobListing


def apply_filters(
    listings: list[JobListing],
    config: dict,
) -> list[JobListing]:
    """
    Filter a list of job listings based on user preferences in config.

    Filters applied (in order):
        1. Distance / radius from home location
        2. Work type (remote / hybrid / onsite / any)
        3. Experience level (entry / mid / senior / any)
        4. Keyword matching against title and description

    Args:
        listings: Raw list from job_fetcher.fetch_jobs()
        config:   Loaded config dict from config_manager.load()

    Returns:
        Filtered list of JobListing objects.
    """
    # TODO: Apply each filter in sequence, returning the narrowed list
    raise NotImplementedError


def filter_by_radius(
    listings: list[JobListing],
    home_lat: float,
    home_lon: float,
    radius_miles: float,
) -> list[JobListing]:
    """Keep only listings within radius_miles of (home_lat, home_lon)."""
    # TODO: Call listing.is_within_radius() for each listing
    raise NotImplementedError


def filter_by_work_type(
    listings: list[JobListing],
    work_type: str,
) -> list[JobListing]:
    """
    Keep only listings matching the requested work type.
    work_type "any" returns all listings unchanged.
    """
    # TODO: Filter on listing.is_remote / is_hybrid based on work_type
    raise NotImplementedError


def filter_by_experience(
    listings: list[JobListing],
    experience_level: str,
) -> list[JobListing]:
    """
    Keep only listings matching the requested experience level.
    experience_level "any" returns all listings unchanged.
    """
    # TODO: Filter on listing.experience_level
    # Listings with unknown experience level ("") should pass through
    raise NotImplementedError


def filter_by_keywords(
    listings: list[JobListing],
    keywords: list[str],
) -> list[JobListing]:
    """
    Keep only listings where at least one keyword appears in the title
    or description (case-insensitive).
    If keywords list is empty, all listings pass through.
    """
    # TODO: For each listing, check if any keyword is in title.lower() or description.lower()
    raise NotImplementedError
