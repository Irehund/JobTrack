"""
core/commute_calculator.py
===========================
Calculates driving commute times from the user's home to job locations
using the OpenRouteService API (free tier available).

Called only from map_builder.py, only for jobs the user has explicitly
selected in the Map View. Never called on the full result set.

Results are cached in memory (per session) and persisted to the
commute_cache table in SQLite across sessions.

ORS Matrix API endpoint:
    POST https://api.openrouteservice.org/v2/matrix/driving-car
    Free tier: 40 requests/minute, 500/day, up to 50 destinations per call.
"""

import logging
import requests
from typing import Optional, Callable
from core.job_model import JobListing
from core import keyring_manager

logger = logging.getLogger("jobtrack.commute")

ORS_MATRIX_URL = "https://api.openrouteservice.org/v2/matrix/driving-car"
REQUEST_TIMEOUT = 15        # seconds
MAX_DESTINATIONS = 50       # ORS free tier limit per request

# In-memory cache: (home_lat, home_lon, job_lat, job_lon) -> minutes
_cache: dict[tuple, Optional[int]] = {}


def calculate_batch(
    home_lat: float,
    home_lon: float,
    listings: list[JobListing],
    progress_callback: Optional[Callable[[int, int], None]] = None,
) -> list[JobListing]:
    """
    Calculate commute times for a list of job listings.
    Results stored directly on each listing's commute_minutes field.

    Skips listings with no coordinates.
    Uses cached results where available.
    Batches uncached calls up to ORS's 50-destination limit.

    Args:
        home_lat:          User's home latitude
        home_lon:          User's home longitude
        listings:          JobListing objects to calculate commutes for
        progress_callback: Optional callable(completed, total) for progress bar

    Returns:
        The same listings list with commute_minutes populated where possible.
    """
    # Separate locatable from unlocatable listings
    locatable = [j for j in listings if j.latitude is not None and j.longitude is not None]
    total = len(locatable)

    if not locatable:
        logger.info("No listings with coordinates — skipping commute calculation.")
        return listings

    # Check cache first
    uncached: list[JobListing] = []
    completed = 0

    for listing in locatable:
        cache_key = (home_lat, home_lon, listing.latitude, listing.longitude)
        if cache_key in _cache:
            listing.commute_minutes = _cache[cache_key]
            completed += 1
            if progress_callback:
                progress_callback(completed, total)
        else:
            uncached.append(listing)

    logger.info(f"Commute cache: {completed} hits, {len(uncached)} uncached")

    if not uncached:
        return listings

    # Check DB cache for uncached listings
    uncached = _load_db_cache(home_lat, home_lon, uncached)
    still_uncached = [j for j in uncached if j.commute_minutes is None]

    if not still_uncached:
        return listings

    # Batch API calls — ORS allows up to 50 destinations per request
    for batch_start in range(0, len(still_uncached), MAX_DESTINATIONS):
        batch = still_uncached[batch_start:batch_start + MAX_DESTINATIONS]
        destinations = [(j.latitude, j.longitude) for j in batch]

        try:
            times = _call_api(home_lat, home_lon, destinations)

            for listing, minutes in zip(batch, times):
                listing.commute_minutes = minutes
                cache_key = (home_lat, home_lon, listing.latitude, listing.longitude)
                _cache[cache_key] = minutes
                completed += 1
                if progress_callback:
                    progress_callback(completed, total)

            # Persist to DB cache
            _save_db_cache(home_lat, home_lon, batch)

        except Exception as e:
            logger.error(f"Commute batch calculation failed: {e}")
            # Leave commute_minutes as None for this batch — not a fatal error

    return listings


def calculate_single(
    home_lat: float,
    home_lon: float,
    job_lat: float,
    job_lon: float,
) -> Optional[int]:
    """
    Get driving time in minutes from home to one job location.
    Returns None if the API call fails or coordinates are unreachable.
    Checks memory cache first.
    """
    cache_key = (home_lat, home_lon, job_lat, job_lon)
    if cache_key in _cache:
        return _cache[cache_key]

    try:
        times = _call_api(home_lat, home_lon, [(job_lat, job_lon)])
        result = times[0] if times else None
        _cache[cache_key] = result
        return result
    except Exception as e:
        logger.error(f"Single commute calculation failed: {e}")
        return None


def _call_api(
    home_lat: float,
    home_lon: float,
    destinations: list[tuple[float, float]],
) -> list[Optional[int]]:
    """
    Call the OpenRouteService Matrix API to get driving durations.

    ORS coordinate format is [longitude, latitude] (note: lon first).

    Args:
        home_lat/home_lon: Origin coordinates
        destinations:      List of (lat, lon) destination tuples

    Returns:
        List of drive times in minutes (same order as destinations).
        None for any destination the API could not route to.

    Raises:
        requests.HTTPError:       On 4xx/5xx responses
        requests.ConnectionError: On network failure
        KeyError:                 If API key not set in keyring
    """
    api_key = keyring_manager.get_key("openrouteservice")
    if not api_key:
        raise ValueError("OpenRouteService API key not set. Add it in Preferences → API Keys.")

    # ORS uses [longitude, latitude] order
    origin = [home_lon, home_lat]
    dests  = [[lon, lat] for lat, lon in destinations]

    payload = {
        "locations": [origin] + dests,
        "metrics":   ["duration"],
        "units":     "mi",
    }

    headers = {
        "Authorization": api_key,
        "Content-Type":  "application/json",
        "Accept":        "application/json, application/geo+json",
    }

    response = requests.post(
        ORS_MATRIX_URL,
        json=payload,
        headers=headers,
        timeout=REQUEST_TIMEOUT,
    )

    if response.status_code == 401:
        raise requests.HTTPError("Invalid OpenRouteService API key (401). Update it in Preferences.")
    if response.status_code == 429:
        raise requests.HTTPError("OpenRouteService rate limit reached (429). Try again in a minute.")
    response.raise_for_status()

    data = response.json()

    # durations[0] is the row for the origin.
    # durations[0][1..n] are origin→destination times in seconds.
    durations_row = data["durations"][0]
    results = []
    for i in range(1, len(destinations) + 1):
        seconds = durations_row[i]
        if seconds is None:
            results.append(None)
        else:
            results.append(int(seconds / 60))  # Convert to minutes

    return results


def _load_db_cache(
    home_lat: float,
    home_lon: float,
    listings: list[JobListing],
) -> list[JobListing]:
    """
    Check the SQLite commute_cache table for any pre-computed times.
    Populates listing.commute_minutes where found.
    Returns the same list (modified in place).
    """
    try:
        from db.database import get_connection
        conn = get_connection()
        for listing in listings:
            if listing.latitude is None or listing.longitude is None:
                continue
            row = conn.execute(
                """SELECT commute_minutes FROM commute_cache
                   WHERE home_lat = ? AND home_lon = ?
                     AND job_lat  = ? AND job_lon  = ?""",
                (round(home_lat, 5), round(home_lon, 5),
                 round(listing.latitude, 5), round(listing.longitude, 5)),
            ).fetchone()
            if row:
                listing.commute_minutes = row["commute_minutes"]
                cache_key = (home_lat, home_lon, listing.latitude, listing.longitude)
                _cache[cache_key] = row["commute_minutes"]
        conn.close()
    except Exception as e:
        logger.warning(f"DB cache read failed (non-fatal): {e}")
    return listings


def _save_db_cache(
    home_lat: float,
    home_lon: float,
    listings: list[JobListing],
) -> None:
    """Persist computed commute times to the SQLite commute_cache table."""
    try:
        from db.database import get_connection
        conn = get_connection()
        for listing in listings:
            if listing.latitude is None or listing.commute_minutes is None:
                continue
            conn.execute(
                """INSERT OR REPLACE INTO commute_cache
                   (home_lat, home_lon, job_lat, job_lon, commute_minutes)
                   VALUES (?, ?, ?, ?, ?)""",
                (round(home_lat, 5), round(home_lon, 5),
                 round(listing.latitude, 5), round(listing.longitude, 5),
                 listing.commute_minutes),
            )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"DB cache write failed (non-fatal): {e}")


def clear_cache() -> None:
    """Clear the in-memory commute cache (call when home location changes)."""
    _cache.clear()
    logger.info("Commute cache cleared.")
