"""
db/jobs_repo.py
================
Repository layer for reading and writing job applications to the local
SQLite database. All database operations go through this module.

Uses db/database.py for connection management.
All timestamps stored as ISO 8601 strings in UTC.
"""

import logging
from datetime import datetime, timezone
from typing import Optional
from db.database import get_connection

logger = logging.getLogger("jobtrack.db.repo")

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
    conn = get_connection()
    try:
        now = _now_iso()
        cursor = conn.execute(
            """
            INSERT INTO applications
                (job_id, provider, company, title, location, job_url,
                 date_applied, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job_data.get("job_id", ""),
                job_data.get("provider", ""),
                job_data.get("company", ""),
                job_data.get("title", ""),
                job_data.get("location", ""),
                job_data.get("job_url", ""),
                job_data.get("date_applied", now),
                job_data.get("status", "Applied"),
                now,
                now,
            ),
        )
        conn.commit()
        new_id = cursor.lastrowid
        logger.info(f"Added application #{new_id}: {job_data.get('title')} at {job_data.get('company')}")
        return new_id
    finally:
        conn.close()


def update_status(application_id: int, new_status: str) -> None:
    """
    Update the status for an application.
    If new_status is in TIMESTAMPED_STATUSES, automatically records
    a timeline event with the current timestamp.

    Args:
        application_id: The application's integer ID
        new_status:     New status string from ALL_STATUSES
    """
    conn = get_connection()
    try:
        now = _now_iso()
        conn.execute(
            "UPDATE applications SET status = ?, updated_at = ? WHERE id = ?",
            (new_status, now, application_id),
        )
        if new_status in TIMESTAMPED_STATUSES:
            conn.execute(
                """
                INSERT INTO timeline_events (application_id, status, event_timestamp, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (application_id, new_status, now, now),
            )
        conn.commit()
        logger.info(f"Application #{application_id} status updated to '{new_status}'")
    finally:
        conn.close()


def get_all_applications() -> list[dict]:
    """
    Return all applications as a list of dicts, each with their
    timeline events embedded as a nested list.
    Used to populate the Tracker panel.
    """
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT * FROM applications
            ORDER BY date_applied DESC
            """
        ).fetchall()

        results = []
        for row in rows:
            app = dict(row)
            # Attach timeline events for this application
            events = conn.execute(
                """
                SELECT status, event_timestamp
                FROM timeline_events
                WHERE application_id = ?
                ORDER BY event_timestamp ASC
                """,
                (app["id"],),
            ).fetchall()
            app["timeline"] = [dict(e) for e in events]
            results.append(app)
        return results
    finally:
        conn.close()


def get_application(application_id: int) -> Optional[dict]:
    """Return a single application by ID, or None if not found."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM applications WHERE id = ?",
            (application_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_timeline(application_id: int) -> list[dict]:
    """
    Return all timeline events for an application in chronological order.

    Returns:
        List of dicts with keys: status, event_timestamp
    """
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT status, event_timestamp
            FROM timeline_events
            WHERE application_id = ?
            ORDER BY event_timestamp ASC
            """,
            (application_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def delete_application(application_id: int) -> None:
    """Delete an application and its timeline events (CASCADE handles events)."""
    conn = get_connection()
    try:
        conn.execute("DELETE FROM applications WHERE id = ?", (application_id,))
        conn.commit()
        logger.info(f"Deleted application #{application_id}")
    finally:
        conn.close()


def get_stats() -> dict:
    """
    Return summary statistics for the dashboard panel.

    Returns:
        Dict with keys: total, by_status (dict of status -> count)
    """
    conn = get_connection()
    try:
        total = conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
        status_rows = conn.execute(
            "SELECT status, COUNT(*) as count FROM applications GROUP BY status"
        ).fetchall()
        by_status = {r["status"]: r["count"] for r in status_rows}
        return {"total": total, "by_status": by_status}
    finally:
        conn.close()


def _now_iso() -> str:
    """Return the current UTC time as an ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()
