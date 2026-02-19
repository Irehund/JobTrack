"""
tests/test_jobs_repo.py
=========================
Tests for db/jobs_repo.py.
Uses an in-memory SQLite database to avoid touching the real AppData file.
"""
import pytest
from unittest.mock import patch
from db import jobs_repo, database


@pytest.fixture
def in_memory_db(monkeypatch):
    """Replace get_connection with an in-memory SQLite connection."""
    import sqlite3
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    # TODO: Initialize schema on the in-memory connection
    monkeypatch.setattr(database, "get_connection", lambda: conn)
    return conn


def test_add_application_returns_id(in_memory_db):
    """Adding an application should return a positive integer ID."""
    # TODO: Call jobs_repo.add_application() with sample data, assert id > 0
    raise NotImplementedError


def test_update_status_records_timeline_event(in_memory_db):
    """Updating to a TIMESTAMPED_STATUS should create a timeline_events row."""
    # TODO: Add application, update to "Phone Screen", query timeline_events
    # Assert one row exists with status="Phone Screen"
    raise NotImplementedError


def test_non_timestamped_status_creates_no_event(in_memory_db):
    """Updating to "No Response" should NOT create a timeline event."""
    # TODO: Add application, update to "No Response", assert no timeline row
    raise NotImplementedError
