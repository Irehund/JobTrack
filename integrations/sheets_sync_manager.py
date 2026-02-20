"""
integrations/sheets_sync_manager.py
=====================================
Bridges the local SQLite tracker (jobs_repo) with Google Sheets.

Sync rules:
    - SQLite is always the source of truth.
    - When a new application is added locally, it gets pushed to Sheets.
    - When a status changes locally, the Sheets row is updated.
    - The sheets_sync table maps application_id → sheets_row_number.
    - If Google Sheets is unavailable, operations degrade silently —
      the local tracker always works regardless.
"""

import logging
from typing import Optional
from core import config_manager
from db import jobs_repo
from integrations.google_sheets import GoogleSheetsTracker

logger = logging.getLogger("jobtrack.sheets_sync")


def get_tracker():
    """
    Return a GoogleSheetsTracker if Google sync is enabled and authenticated.
    Returns None if sync is disabled or not authenticated.
    """
    cfg = config_manager.load()
    mode = cfg.get("tracker", {}).get("mode", "local")
    if mode not in ("google", "both"):
        return None

    from core import config_manager as cm
    token_path = str(cm.get_config_dir() / "google_token.json")

    tracker = GoogleSheetsTracker(token_path=token_path)
    if not tracker.is_authenticated():
        logger.warning("Google sync enabled but not authenticated.")
        return None

    return tracker


def push_new_application(application_id: int) -> bool:
    """
    Push a newly added local application to Google Sheets.
    Records the sheets row number in the sheets_sync table.

    Returns:
        True if successfully synced, False if sync skipped/failed.
    """
    tracker = get_tracker()
    if tracker is None:
        return False

    try:
        app = jobs_repo.get_application(application_id)
        if not app:
            logger.warning(f"push_new_application: no app with id {application_id}")
            return False

        tracker.get_or_create_spreadsheet()
        sheets_row = tracker.append_application(app)

        # Record the mapping
        _save_sync_row(application_id, sheets_row,
                       tracker._spreadsheet.id if tracker._spreadsheet else "")
        logger.info(f"Pushed application {application_id} → Sheets row {sheets_row}")
        return True

    except Exception as e:
        logger.error(f"push_new_application failed: {e}")
        return False


def push_status_update(application_id: int, new_status: str, timestamp: str) -> bool:
    """
    Update the status of an existing application in Google Sheets.

    Returns:
        True if successfully synced, False if sync skipped/failed.
    """
    tracker = get_tracker()
    if tracker is None:
        return False

    try:
        sheets_row = _get_sync_row(application_id)
        if sheets_row is None:
            # Application not in Sheets yet — push it now
            return push_new_application(application_id)

        tracker.get_or_create_spreadsheet()
        tracker.update_status(sheets_row, new_status, timestamp)
        _touch_sync_row(application_id)
        logger.info(f"Updated Sheets row {sheets_row} → {new_status}")
        return True

    except Exception as e:
        logger.error(f"push_status_update failed: {e}")
        return False


def full_sync() -> dict:
    """
    Push all local applications to Google Sheets.
    Used for the initial sync after OAuth or after being offline.

    Returns:
        {"appended": int, "updated": int, "skipped": int, "failed": int}
    """
    tracker = get_tracker()
    if tracker is None:
        return {"appended": 0, "updated": 0, "skipped": 0, "failed": 0}

    try:
        tracker.get_or_create_spreadsheet()
        applications = jobs_repo.get_all_applications()
        stats = tracker.sync_from_local(applications)
        stats.setdefault("failed", 0)
        logger.info(f"full_sync complete: {stats}")
        return stats
    except Exception as e:
        logger.error(f"full_sync failed: {e}")
        return {"appended": 0, "updated": 0, "skipped": 0, "failed": 1}


# ── Local sync table helpers ──────────────────────────────────────────────────

def _save_sync_row(application_id: int, sheets_row: int, spreadsheet_id: str) -> None:
    """Upsert a row into the sheets_sync table."""
    try:
        from db.database import get_connection
        conn = get_connection()
        conn.execute(
            """INSERT OR REPLACE INTO sheets_sync
               (application_id, sheets_row, spreadsheet_id, last_synced_at)
               VALUES (?, ?, ?, datetime('now'))""",
            (application_id, sheets_row, spreadsheet_id),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"_save_sync_row failed: {e}")


def _get_sync_row(application_id: int) -> Optional[int]:
    """Return the sheets_row for an application_id, or None if not synced."""
    try:
        from db.database import get_connection
        conn = get_connection()
        row = conn.execute(
            "SELECT sheets_row FROM sheets_sync WHERE application_id = ?",
            (application_id,),
        ).fetchone()
        conn.close()
        return row["sheets_row"] if row else None
    except Exception as e:
        logger.warning(f"_get_sync_row failed: {e}")
        return None


def _touch_sync_row(application_id: int) -> None:
    """Update last_synced_at for an application."""
    try:
        from db.database import get_connection
        conn = get_connection()
        conn.execute(
            "UPDATE sheets_sync SET last_synced_at = datetime('now') WHERE application_id = ?",
            (application_id,),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"_touch_sync_row failed: {e}")
