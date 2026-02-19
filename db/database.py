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
from pathlib import Path
from core.config_manager import get_config_dir

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
    # TODO: Implement connection
    # 1. conn = sqlite3.connect(get_db_path())
    # 2. conn.row_factory = sqlite3.Row
    # 3. conn.execute("PRAGMA foreign_keys = ON")
    # 4. Call _initialize(conn) to create tables if needed
    # 5. Call _migrate(conn) to apply any pending migrations
    # 6. Return conn
    raise NotImplementedError


def _initialize(conn: sqlite3.Connection) -> None:
    """
    Create all tables if they don't already exist.
    Reads schema from db/schema.sql.
    """
    # TODO: Read schema.sql and execute it
    raise NotImplementedError


def _migrate(conn: sqlite3.Connection) -> None:
    """
    Apply schema migrations based on the stored schema_version.
    Add migration blocks here as SCHEMA_VERSION increments.
    """
    # TODO: Read schema_version from a metadata table
    # Apply migrations for each version below the current SCHEMA_VERSION
    raise NotImplementedError
