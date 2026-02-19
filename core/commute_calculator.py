"""
core/commute_calculator.py
===========================
Calculates driving commute times from the user's home to job locations
using the OpenRouteService API (free tier available).

Called only from map_builder.py, only for jobs the user has explicitly
selected in the Map View. Never called on the full result set.

Results are cached in memory (per session) and optionally persisted to
a local cache file to avoid repeat API calls across sessions.
"""

from typing import Optional
from core.job_model import JobListing

# In-memory cache: (home_lat, home_lon, job_lat, job_lon) -> minutes
_cache: dict[tuple, Optional[int]] = {}


def calculate_batch(
    home_lat: float,
    home_lon: float,
    listings: list[JobListing],
    progress_callback=None,
) -> list[JobListing]:
    """
    Calculate commute times for a list of job listings and store the
    results on each listing's commute_minutes field.

    Skips listings with no coordinates.
    Uses cached results where available.

    Args:
        home_lat:          User's home latitude
        home_lon:          User's home longitude
        listings:          JobListing objects to calculate commutes for
        progress_callback: Optional callable(completed, total) for progress bar

    Returns:
        The same listings list with commute_minutes populated where possible.
    """
    # TODO: Implement batch commute calculation
    # 1. Filter to listings that have latitude and longitude
    # 2. Check _cache for each — skip API call if cached
    # 3. Call OpenRouteService Matrix API with uncached coordinates in one batch
    # 4. Store results in _cache and on each listing.commute_minutes
    # 5. Call progress_callback(i, total) after each result
    raise NotImplementedError


def calculate_single(
    home_lat: float,
    home_lon: float,
    job_lat: float,
    job_lon: float,
) -> Optional[int]:
    """
    Get driving time in minutes from home to one job location.
    Returns None if the API call fails or coordinates are unreachable.
    Checks cache first.
    """
    # TODO: Check _cache, then call _call_api() if not cached
    raise NotImplementedError


def _call_api(
    home_lat: float,
    home_lon: float,
    destinations: list[tuple[float, float]],
) -> list[Optional[int]]:
    """
    Call the OpenRouteService Matrix API.

    Args:
        home_lat/home_lon: Origin coordinates
        destinations:      List of (lat, lon) destination tuples

    Returns:
        List of drive times in minutes (same order as destinations).
        None for any destination the API could not route to.
    """
    # TODO: Implement OpenRouteService API call
    # Endpoint: https://api.openrouteservice.org/v2/matrix/driving-car
    # API key retrieved from keyring_manager.get_key("openrouteservice")
    raise NotImplementedError


def clear_cache() -> None:
    """Clear the in-memory commute cache (e.g., when home location changes)."""
    _cache.clear()
