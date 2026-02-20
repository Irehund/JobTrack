"""
core/filter_engine.py
======================
Applies the user's saved preferences to a list of JobListing objects.
Called after job_fetcher returns results to trim the list before display.

All filtering is done in-memory — no API calls.

Filter pipeline (applied in order):
    1. Radius       — drop jobs too far from home (jobs with no coords pass through)
    2. Work type    — remote / hybrid / onsite / any
    3. Experience   — entry / mid / senior / any (unknown level always passes)
    4. Keywords     — title or description must contain at least one keyword
"""

import logging
from core.job_model import JobListing

logger = logging.getLogger("jobtrack.filter")


def apply_filters(
    listings: list[JobListing],
    config: dict,
) -> list[JobListing]:
    """
    Apply all user preference filters to a list of job listings.

    Args:
        listings: Raw list from job_fetcher.fetch_jobs()
        config:   Loaded config dict from config_manager.load()

    Returns:
        Filtered list of JobListing objects.
    """
    if not listings:
        return []

    original_count = len(listings)
    result = listings

    # ── 1. Radius filter ──────────────────────────────────────────────────────
    location = config.get("location", {})
    lat = location.get("latitude")
    lon = location.get("longitude")
    radius = config.get("search_radius_miles", 50)

    if lat is not None and lon is not None:
        result = filter_by_radius(result, float(lat), float(lon), float(radius))
        logger.debug(f"After radius filter ({radius} mi): {len(result)}/{original_count}")

    # ── 2. Work type filter ───────────────────────────────────────────────────
    prefs = config.get("job_preferences", {})
    work_type = prefs.get("work_type", "any")
    if work_type != "any":
        result = filter_by_work_type(result, work_type)
        logger.debug(f"After work_type filter ({work_type}): {len(result)}")

    # ── 3. Experience level filter ────────────────────────────────────────────
    experience = prefs.get("experience_level", "any")
    if experience != "any":
        result = filter_by_experience(result, experience)
        logger.debug(f"After experience filter ({experience}): {len(result)}")

    # ── 4. Keyword filter ─────────────────────────────────────────────────────
    keywords = prefs.get("keywords", [])
    if keywords:
        result = filter_by_keywords(result, keywords)
        logger.debug(f"After keyword filter: {len(result)}")

    logger.info(f"Filter pipeline: {original_count} → {len(result)} listings")
    return result


def filter_by_radius(
    listings: list[JobListing],
    home_lat: float,
    home_lon: float,
    radius_miles: float,
) -> list[JobListing]:
    """
    Keep only listings within radius_miles of (home_lat, home_lon).
    Listings with no coordinates always pass through — we never discard
    a job just because we couldn't geolocate it.
    """
    return [j for j in listings if j.is_within_radius(home_lat, home_lon, radius_miles)]


def filter_by_work_type(
    listings: list[JobListing],
    work_type: str,
) -> list[JobListing]:
    """
    Keep only listings matching the requested work arrangement.

    work_type values:
        "any"    — return all listings unchanged
        "remote" — only listings where is_remote is True
        "hybrid" — only listings where is_hybrid is True
        "onsite" — only listings where neither is_remote nor is_hybrid
    """
    if work_type == "any":
        return listings
    if work_type == "remote":
        return [j for j in listings if j.is_remote]
    if work_type == "hybrid":
        return [j for j in listings if j.is_hybrid]
    if work_type == "onsite":
        return [j for j in listings if not j.is_remote and not j.is_hybrid]
    # Unknown work_type value — pass all through
    return listings


def filter_by_experience(
    listings: list[JobListing],
    experience_level: str,
) -> list[JobListing]:
    """
    Keep only listings matching the requested experience level.

    experience_level values:
        "any"    — return all listings unchanged
        "entry"  — only listings where experience_level == "entry"
        "mid"    — only listings where experience_level == "mid"
        "senior" — only listings where experience_level == "senior"

    Listings with an empty/unknown experience_level always pass through
    so we don't accidentally hide jobs just because we couldn't classify them.
    """
    if experience_level == "any":
        return listings
    return [
        j for j in listings
        if j.experience_level == "" or j.experience_level == experience_level
    ]


def filter_by_keywords(
    listings: list[JobListing],
    keywords: list[str],
) -> list[JobListing]:
    """
    Keep only listings where at least one keyword appears in the title
    or description (case-insensitive, substring match).

    If keywords is empty, all listings pass through.

    Examples:
        keywords = ["SOC Analyst"]
        title    = "Junior SOC Analyst II"   → PASSES (substring match)
        title    = "Software Engineer"        → FAILS
    """
    if not keywords:
        return listings

    lower_keywords = [kw.lower().strip() for kw in keywords if kw.strip()]
    if not lower_keywords:
        return listings

    def _matches(job: JobListing) -> bool:
        haystack = f"{job.title} {job.description}".lower()
        return any(kw in haystack for kw in lower_keywords)

    return [j for j in listings if _matches(j)]
