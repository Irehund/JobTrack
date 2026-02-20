"""
core/map_builder.py
====================
Builds an interactive Folium map from a list of JobListing objects.
Called only when the user opens the Map View panel.

Pin color coding by commute time:
    Green  = under 30 minutes
    Yellow/Orange = 30 to 60 minutes
    Red    = over 60 minutes
    Gray   = commute not yet calculated
"""

import logging
import folium
from typing import Optional
from core.job_model import JobListing
from core.utils import format_salary

logger = logging.getLogger("jobtrack.map")

# Tile provider — OpenStreetMap is free, no API key needed
TILE_PROVIDER  = "OpenStreetMap"
DEFAULT_ZOOM   = 10
HOME_ICON      = "home"
HOME_COLOR     = "blue"


def build_map(
    listings: list[JobListing],
    home_lat: float,
    home_lon: float,
    output_path: str,
) -> str:
    """
    Generate an interactive HTML map centered on the user's home location.

    Args:
        listings:    List of JobListing objects to plot
        home_lat:    User's home latitude
        home_lon:    User's home longitude
        output_path: File path to write the HTML map to

    Returns:
        The output_path where the HTML map was written.
    """
    fmap = folium.Map(
        location=[home_lat, home_lon],
        zoom_start=DEFAULT_ZOOM,
        tiles=TILE_PROVIDER,
    )

    # ── Home marker ───────────────────────────────────────────────────────────
    folium.Marker(
        location=[home_lat, home_lon],
        popup=folium.Popup("<b>🏠 Your Home</b>", max_width=160),
        tooltip="Home",
        icon=folium.Icon(color=HOME_COLOR, icon=HOME_ICON, prefix="fa"),
    ).add_to(fmap)

    # ── Job pins ──────────────────────────────────────────────────────────────
    plotted = 0
    skipped = 0

    for listing in listings:
        if listing.latitude is None or listing.longitude is None:
            skipped += 1
            continue

        color  = _commute_color(listing.commute_minutes)
        radius = 8 if listing.commute_minutes is not None else 6

        popup_html = _build_popup_html(listing)

        folium.CircleMarker(
            location=[listing.latitude, listing.longitude],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            tooltip=f"{listing.title} — {listing.company}",
            popup=folium.Popup(popup_html, max_width=320),
        ).add_to(fmap)

        plotted += 1

    logger.info(f"Map: {plotted} pins plotted, {skipped} listings had no coordinates")

    # ── Legend ────────────────────────────────────────────────────────────────
    _add_legend(fmap)

    fmap.save(output_path)
    logger.info(f"Map saved to {output_path}")
    return output_path


def _commute_color(commute_minutes: Optional[int]) -> str:
    """
    Return a color string for a map pin based on commute time.

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
    Includes: title, company, location, commute time, salary, apply link.
    """
    # Commute line
    if listing.commute_minutes is not None:
        hours, mins = divmod(listing.commute_minutes, 60)
        if hours > 0:
            commute_str = f"{hours}h {mins}min drive"
        else:
            commute_str = f"{mins} min drive"
        commute_color = _commute_color(listing.commute_minutes)
        commute_html = (
            f'<span style="color:{commute_color}; font-weight:bold;">'
            f'🚗 {commute_str}</span>'
        )
    else:
        commute_html = '<span style="color:gray;">🚗 Commute not calculated</span>'

    # Salary line
    salary_str = format_salary(listing.salary_min, listing.salary_max, listing.salary_interval)
    salary_html = f'<div style="color:#555;">💰 {salary_str}</div>'

    # Remote/hybrid badge
    badges = []
    if listing.is_remote:
        badges.append('<span style="background:#e8f5e9;color:#388e3c;padding:1px 6px;border-radius:3px;font-size:11px;">Remote</span>')
    elif listing.is_hybrid:
        badges.append('<span style="background:#fff8e1;color:#f57c00;padding:1px 6px;border-radius:3px;font-size:11px;">Hybrid</span>')
    badge_html = " ".join(badges)

    # Apply link
    if listing.url:
        link_html = (
            f'<div style="margin-top:8px;">'
            f'<a href="{listing.url}" target="_blank" '
            f'style="background:#1565C0;color:white;padding:4px 10px;'
            f'border-radius:4px;text-decoration:none;font-size:12px;">'
            f'View Posting →</a></div>'
        )
    else:
        link_html = ""

    html = f"""
    <div style="font-family:sans-serif;font-size:13px;min-width:240px;">
      <div style="font-weight:bold;font-size:14px;margin-bottom:4px;">{listing.title}</div>
      <div style="color:#444;margin-bottom:2px;">{listing.company}</div>
      <div style="color:#888;font-size:12px;margin-bottom:6px;">{listing.location}</div>
      {badge_html}
      <div style="margin-top:6px;">{commute_html}</div>
      {salary_html}
      {link_html}
    </div>
    """.strip()

    return html


def _add_legend(fmap: folium.Map) -> None:
    """Add a color legend to the bottom-right of the map."""
    legend_html = """
    <div style="
        position: fixed;
        bottom: 30px; right: 10px; z-index: 1000;
        background: white; padding: 10px 14px;
        border: 1px solid #ccc; border-radius: 6px;
        font-family: sans-serif; font-size: 12px;
        box-shadow: 2px 2px 6px rgba(0,0,0,0.15);
    ">
        <div style="font-weight:bold;margin-bottom:6px;">🚗 Commute Time</div>
        <div><span style="color:green;">●</span> Under 30 min</div>
        <div><span style="color:orange;">●</span> 30 – 60 min</div>
        <div><span style="color:red;">●</span> Over 60 min</div>
        <div><span style="color:gray;">●</span> Not calculated</div>
    </div>
    """
    fmap.get_root().html.add_child(folium.Element(legend_html))
