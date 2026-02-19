"""
db/database.py
===============
Manages the local SQLite database used for the application tracker.
Creates the database file in the platform AppData directory on first run.
Handles schema migrations automatically on version upgrades.

Database location:
    Windows: %APPDATA%\JobTrack\jobtrack.db
    macOS:   ~/Library/Application Support/JobTrack/jobtrack.db

The database file is the user's data — it stays on their machine.
It is excluded from git via .gitignore.
"""

import sqlite3
import logging
from pathlib import Path
from core.config_manager import get_config_dir

logger = logging.getLogger("jobtrack.db")

DB_FILENAME = "jobtrack.db"
SCHEMA_VERSION = 1


def get_db_path() -> Path:
    """Return the full path to the SQLite database file."""
    return get_config_dir() / DB_FILENAME


def get_connection() -> sqlite3.Connection:
    """
    Open and return a connection to the JobTrack database.
    Creates the database and runs initial schema if it doesn't exist.
    Sets row_factory to sqlite3.Row for dict-like row access.
    """
    db_path = get_db_path()
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")  # Better concurrent read performance
    _initialize(conn)
    _migrate(conn)
    return conn


def _initialize(conn: sqlite3.Connection) -> None:
    """
    Create all tables if they don't already exist.
    Reads schema from db/schema.sql.
    """
    schema_path = Path(__file__).parent / "schema.sql"
    try:
        sql = schema_path.read_text(encoding="utf-8")
        conn.executescript(sql)
        conn.commit()
    except Exception as e:
        logger.error(f"Failed to initialize database schema: {e}")
        raise


def _migrate(conn: sqlite3.Connection) -> None:
    """
    Apply schema migrations based on the stored schema_version.
    Add migration blocks here as SCHEMA_VERSION increments.
    """
    try:
        row = conn.execute("SELECT value FROM metadata WHERE key = 'schema_version'").fetchone()
        current_version = int(row["value"]) if row else 0
    except Exception:
        current_version = 0

    if current_version >= SCHEMA_VERSION:
        return  # Already up to date

    # Future migrations go here:
    # if current_version < 2:
    #     conn.execute("ALTER TABLE applications ADD COLUMN notes TEXT DEFAULT ''")
    #     conn.execute("UPDATE metadata SET value = '2' WHERE key = 'schema_version'")
    #     conn.commit()
    #     current_version = 2

    logger.debug(f"Database schema is current at version {SCHEMA_VERSION}")


def close(conn: sqlite3.Connection) -> None:
    """Safely close a database connection."""
    try:
        conn.close()
    except Exception:
        pass
