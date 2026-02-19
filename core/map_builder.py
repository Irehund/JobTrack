"""
core/map_builder.py
====================
Builds an interactive Folium map from a list of JobListing objects.
Called only when the user opens the Map View panel.

Commute times are calculated only for the jobs the user explicitly
selects — never for the full result set. Results are cached to avoid
redundant API calls.

Pin color coding by commute time:
    Green  = under 30 minutes
    Yellow = 30 to 60 minutes
    Red    = over 60 minutes
    Gray   = commute not yet calculated
"""

import folium
from typing import Optional
from core.job_model import JobListing


def build_map(
    listings: list[JobListing],
    home_lat: float,
    home_lon: float,
    output_path: str,
) -> str:
    """
    Generate an interactive HTML map centered on the user's home location.
    Each job is shown as a pin with a popup containing job title, company,
    and commute time if calculated.

    Args:
        listings:    List of JobListing objects to plot
        home_lat:    User's home latitude
        home_lon:    User's home longitude
        output_path: File path to write the HTML map to

    Returns:
        The output_path where the HTML map was written.
    """
    # TODO: Implement map build
    # 1. Create folium.Map centered on (home_lat, home_lon) with zoom ~10
    # 2. Add a home marker (house icon, blue) at (home_lat, home_lon)
    # 3. For each listing with latitude/longitude:
    #    - Determine pin color via _commute_color(listing.commute_minutes)
    #    - Add folium.CircleMarker or Marker with popup showing job details
    # 4. Add a legend explaining the color coding
    # 5. Save map to output_path and return it
    raise NotImplementedError


def _commute_color(commute_minutes: Optional[int]) -> str:
    """
    Return a color string for a map pin based on commute time.

    Args:
        commute_minutes: Drive time in minutes, or None if not calculated.

    Returns:
        "green" | "orange" | "red" | "gray"
    """
    if commute_minutes is None:
        return "gray"
    if commute_minutes < 30:
        return "green"
    if commute_minutes <= 60:
        return "orange"
    return "red"


def _build_popup_html(listing: JobListing) -> str:
    """
    Build the HTML string shown in the map popup for a given listing.
    Includes: job title, company, location, commute time, apply link.
    """
    # TODO: Build a clean HTML snippet for the folium popup
    raise NotImplementedError
