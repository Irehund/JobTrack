"""
db/jobs_repo.py
================
Repository layer for reading and writing job applications to the local
SQLite database. All database operations go through this module.

Uses db/database.py for connection management.
All timestamps stored as ISO 8601 strings in UTC.
"""

from datetime import datetime, timezone
from typing import Optional
from db.database import get_connection

# Statuses that automatically record a timestamp when selected
TIMESTAMPED_STATUSES = {
    "Phone Screen",
    "Interview Scheduled",
    "Interview Completed",
    "Second Interview",
    "Offer Received",
    "Offer Accepted",
    "Offer Declined",
    "Rejected",
}

ALL_STATUSES = [
    "Applied",
    "No Response",
    "Phone Screen",
    "Interview Scheduled",
    "Interview Completed",
    "Second Interview",
    "Offer Received",
    "Offer Accepted",
    "Offer Declined",
    "Rejected",
    "Withdrawn",
]


def add_application(job_data: dict) -> int:
    """
    Insert a new application record when the user marks a job as applied.

    Args:
        job_data: Dict with keys: job_id, provider, company, title,
                  location, job_url, date_applied, status

    Returns:
        The new row's integer ID.
    """
    # TODO: INSERT into applications table, return lastrowid
    raise NotImplementedError


def update_status(application_id: int, new_status: str) -> None:
    """
    Update the status for an application.
    If new_status is in TIMESTAMPED_STATUSES, automatically records
    a timeline event with the current timestamp.

    Args:
        application_id: The application's integer ID
        new_status:     New status string from ALL_STATUSES
    """
    # TODO:
    # 1. UPDATE applications SET status=?, updated_at=? WHERE id=?
    # 2. If new_status in TIMESTAMPED_STATUSES:
    #    call _record_timeline_event(application_id, new_status)
    raise NotImplementedError


def get_all_applications() -> list[dict]:
    """
    Return all applications with their latest timeline events.
    Used to populate the Tracker panel.

    Returns:
        List of dicts with application fields plus any timeline timestamps.
    """
    # TODO: JOIN applications with timeline_events, return as list of dicts
    raise NotImplementedError


def get_application(application_id: int) -> Optional[dict]:
    """Return a single application by ID, or None if not found."""
    # TODO: SELECT from applications WHERE id=?
    raise NotImplementedError


def get_timeline(application_id: int) -> list[dict]:
    """
    Return all timeline events for an application in chronological order.

    Returns:
        List of dicts with keys: status, event_timestamp
    """
    # TODO: SELECT from timeline_events WHERE application_id=? ORDER BY event_timestamp ASC
    raise NotImplementedError


def delete_application(application_id: int) -> None:
    """Delete an application and its timeline events (CASCADE handles events)."""
    # TODO: DELETE FROM applications WHERE id=?
    raise NotImplementedError


def _record_timeline_event(application_id: int, status: str) -> None:
    """
    Insert a timeline event with the current UTC timestamp.
    Called internally by update_status().
    """
    # TODO: INSERT into timeline_events (application_id, status, event_timestamp)
    raise NotImplementedError


def _now_iso() -> str:
    """Return the current UTC time as an ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()
