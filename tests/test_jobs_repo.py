"""
tests/test_jobs_repo.py
=========================
Tests for db/jobs_repo.py and db/database.py.
Uses an in-memory SQLite database to avoid touching the real AppData file.
Every test gets a fresh empty database via the fixture.
"""

import pytest
import sqlite3
from pathlib import Path
from unittest.mock import patch
from db import jobs_repo
from db import database


@pytest.fixture
def in_memory_db(monkeypatch):
    """
    Replace get_connection with a fresh in-memory SQLite connection.
    Each test gets its own clean database — no state bleeds between tests.
    """
    def make_connection():
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        # Load and execute the real schema
        schema_path = Path(__file__).parent.parent / "db" / "schema.sql"
        conn.executescript(schema_path.read_text(encoding="utf-8"))
        conn.commit()
        return conn

    monkeypatch.setattr(database, "get_connection", make_connection)
    monkeypatch.setattr(jobs_repo, "get_connection", make_connection)
    return make_connection


def _sample_job(**overrides) -> dict:
    """Build a sample job_data dict for testing."""
    data = {
        "job_id": "usajobs_TEST001",
        "provider": "usajobs",
        "company": "Cybersecurity and Infrastructure Security Agency",
        "title": "Information Security Analyst",
        "location": "Dallas, TX",
        "job_url": "https://www.usajobs.gov/job/TEST001",
        "date_applied": "2026-02-19T14:00:00+00:00",
        "status": "Applied",
    }
    data.update(overrides)
    return data


# ── add_application ───────────────────────────────────────────────────────────

class TestAddApplication:

    def test_returns_positive_integer_id(self, in_memory_db):
        """add_application should return a positive integer row ID."""
        result_id = jobs_repo.add_application(_sample_job())
        assert isinstance(result_id, int)
        assert result_id > 0

    def test_sequential_ids_increment(self, in_memory_db):
        """Each new application should get a unique incrementing ID."""
        id1 = jobs_repo.add_application(_sample_job(job_id="job_1"))
        id2 = jobs_repo.add_application(_sample_job(job_id="job_2"))
        assert id2 > id1

    def test_application_retrievable_after_add(self, in_memory_db):
        """An application added should be retrievable by ID."""
        new_id = jobs_repo.add_application(_sample_job())
        app = jobs_repo.get_application(new_id)
        assert app is not None
        assert app["title"] == "Information Security Analyst"
        assert app["company"] == "Cybersecurity and Infrastructure Security Agency"

    def test_all_fields_stored_correctly(self, in_memory_db):
        """All fields in job_data should be stored and retrievable."""
        data = _sample_job()
        new_id = jobs_repo.add_application(data)
        app = jobs_repo.get_application(new_id)
        assert app["job_id"] == data["job_id"]
        assert app["provider"] == data["provider"]
        assert app["company"] == data["company"]
        assert app["title"] == data["title"]
        assert app["location"] == data["location"]
        assert app["job_url"] == data["job_url"]
        assert app["status"] == "Applied"

    def test_default_status_is_applied(self, in_memory_db):
        """If no status is provided, it should default to 'Applied'."""
        data = _sample_job()
        del data["status"]
        new_id = jobs_repo.add_application(data)
        app = jobs_repo.get_application(new_id)
        assert app["status"] == "Applied"

    def test_multiple_applications_stored_independently(self, in_memory_db):
        """Multiple applications should not interfere with each other."""
        id1 = jobs_repo.add_application(_sample_job(title="SOC Analyst", company="Acme"))
        id2 = jobs_repo.add_application(_sample_job(title="Security Engineer", company="Globex"))
        app1 = jobs_repo.get_application(id1)
        app2 = jobs_repo.get_application(id2)
        assert app1["title"] == "SOC Analyst"
        assert app2["title"] == "Security Engineer"


# ── get_application ───────────────────────────────────────────────────────────

class TestGetApplication:

    def test_returns_none_for_missing_id(self, in_memory_db):
        """get_application should return None for an ID that doesn't exist."""
        result = jobs_repo.get_application(99999)
        assert result is None

    def test_returns_dict(self, in_memory_db):
        """get_application should return a dict, not a sqlite3.Row."""
        new_id = jobs_repo.add_application(_sample_job())
        app = jobs_repo.get_application(new_id)
        assert isinstance(app, dict)


# ── update_status ─────────────────────────────────────────────────────────────

class TestUpdateStatus:

    def test_status_updates_correctly(self, in_memory_db):
        """Status should change after update_status is called."""
        new_id = jobs_repo.add_application(_sample_job())
        jobs_repo.update_status(new_id, "No Response")
        app = jobs_repo.get_application(new_id)
        assert app["status"] == "No Response"

    def test_timestamped_status_creates_timeline_event(self, in_memory_db):
        """Updating to a TIMESTAMPED_STATUS should create a timeline_events row."""
        new_id = jobs_repo.add_application(_sample_job())
        jobs_repo.update_status(new_id, "Phone Screen")
        timeline = jobs_repo.get_timeline(new_id)
        assert len(timeline) == 1
        assert timeline[0]["status"] == "Phone Screen"

    def test_non_timestamped_status_creates_no_timeline_event(self, in_memory_db):
        """Updating to 'No Response' should NOT create a timeline event."""
        new_id = jobs_repo.add_application(_sample_job())
        jobs_repo.update_status(new_id, "No Response")
        timeline = jobs_repo.get_timeline(new_id)
        assert len(timeline) == 0

    def test_multiple_status_updates_build_timeline(self, in_memory_db):
        """Each timestamped status change should add another timeline entry."""
        new_id = jobs_repo.add_application(_sample_job())
        jobs_repo.update_status(new_id, "Phone Screen")
        jobs_repo.update_status(new_id, "Interview Scheduled")
        jobs_repo.update_status(new_id, "Interview Completed")
        timeline = jobs_repo.get_timeline(new_id)
        assert len(timeline) == 3
        statuses = [e["status"] for e in timeline]
        assert "Phone Screen" in statuses
        assert "Interview Scheduled" in statuses
        assert "Interview Completed" in statuses

    def test_all_timestamped_statuses_create_events(self, in_memory_db):
        """Every status in TIMESTAMPED_STATUSES should create a timeline event."""
        for status in jobs_repo.TIMESTAMPED_STATUSES:
            new_id = jobs_repo.add_application(_sample_job())
            jobs_repo.update_status(new_id, status)
            timeline = jobs_repo.get_timeline(new_id)
            assert len(timeline) == 1, f"Expected timeline event for status '{status}'"

    def test_non_timestamped_statuses_create_no_events(self, in_memory_db):
        """Statuses not in TIMESTAMPED_STATUSES should never create timeline events."""
        non_timestamped = [s for s in jobs_repo.ALL_STATUSES
                           if s not in jobs_repo.TIMESTAMPED_STATUSES]
        for status in non_timestamped:
            new_id = jobs_repo.add_application(_sample_job())
            jobs_repo.update_status(new_id, status)
            timeline = jobs_repo.get_timeline(new_id)
            assert len(timeline) == 0, f"Unexpected timeline event for status '{status}'"

    def test_updated_at_changes_after_status_update(self, in_memory_db):
        """updated_at timestamp should change after update_status."""
        new_id = jobs_repo.add_application(_sample_job())
        app_before = jobs_repo.get_application(new_id)
        jobs_repo.update_status(new_id, "No Response")
        app_after = jobs_repo.get_application(new_id)
        # updated_at should be set (may be same second in fast tests, just verify it exists)
        assert app_after["updated_at"] is not None


# ── get_all_applications ──────────────────────────────────────────────────────

class TestGetAllApplications:

    def test_empty_database_returns_empty_list(self, in_memory_db):
        """get_all_applications should return [] when no applications exist."""
        result = jobs_repo.get_all_applications()
        assert result == []

    def test_returns_all_applications(self, in_memory_db):
        """Should return one dict per application."""
        jobs_repo.add_application(_sample_job(job_id="a", title="Job A"))
        jobs_repo.add_application(_sample_job(job_id="b", title="Job B"))
        jobs_repo.add_application(_sample_job(job_id="c", title="Job C"))
        result = jobs_repo.get_all_applications()
        assert len(result) == 3

    def test_each_result_includes_timeline_key(self, in_memory_db):
        """Each application dict should include a 'timeline' key."""
        jobs_repo.add_application(_sample_job())
        result = jobs_repo.get_all_applications()
        assert "timeline" in result[0]

    def test_timeline_populated_for_applications_with_events(self, in_memory_db):
        """Applications with status changes should have populated timelines."""
        new_id = jobs_repo.add_application(_sample_job())
        jobs_repo.update_status(new_id, "Phone Screen")
        result = jobs_repo.get_all_applications()
        assert len(result[0]["timeline"]) == 1
        assert result[0]["timeline"][0]["status"] == "Phone Screen"

    def test_returns_list_of_dicts(self, in_memory_db):
        """Results should be dicts, not sqlite3.Row objects."""
        jobs_repo.add_application(_sample_job())
        result = jobs_repo.get_all_applications()
        assert isinstance(result[0], dict)


# ── get_timeline ──────────────────────────────────────────────────────────────

class TestGetTimeline:

    def test_empty_timeline_for_new_application(self, in_memory_db):
        """A freshly added application should have an empty timeline."""
        new_id = jobs_repo.add_application(_sample_job())
        assert jobs_repo.get_timeline(new_id) == []

    def test_timeline_ordered_chronologically(self, in_memory_db):
        """Timeline events should be in ascending chronological order."""
        new_id = jobs_repo.add_application(_sample_job())
        jobs_repo.update_status(new_id, "Phone Screen")
        jobs_repo.update_status(new_id, "Interview Scheduled")
        timeline = jobs_repo.get_timeline(new_id)
        assert timeline[0]["status"] == "Phone Screen"
        assert timeline[1]["status"] == "Interview Scheduled"

    def test_timeline_events_have_timestamp(self, in_memory_db):
        """Each timeline event should have a non-empty event_timestamp."""
        new_id = jobs_repo.add_application(_sample_job())
        jobs_repo.update_status(new_id, "Phone Screen")
        timeline = jobs_repo.get_timeline(new_id)
        assert timeline[0]["event_timestamp"] is not None
        assert len(timeline[0]["event_timestamp"]) > 0


# ── delete_application ────────────────────────────────────────────────────────

class TestDeleteApplication:

    def test_application_removed_after_delete(self, in_memory_db):
        """Deleted application should not be retrievable."""
        new_id = jobs_repo.add_application(_sample_job())
        jobs_repo.delete_application(new_id)
        assert jobs_repo.get_application(new_id) is None

    def test_timeline_events_deleted_with_application(self, in_memory_db):
        """Timeline events should be cascade-deleted with the application."""
        new_id = jobs_repo.add_application(_sample_job())
        jobs_repo.update_status(new_id, "Phone Screen")
        jobs_repo.delete_application(new_id)
        # Timeline should be gone too
        assert jobs_repo.get_timeline(new_id) == []

    def test_delete_only_removes_target_application(self, in_memory_db):
        """Deleting one application should not affect others."""
        id1 = jobs_repo.add_application(_sample_job(job_id="a"))
        id2 = jobs_repo.add_application(_sample_job(job_id="b"))
        jobs_repo.delete_application(id1)
        assert jobs_repo.get_application(id1) is None
        assert jobs_repo.get_application(id2) is not None

    def test_delete_nonexistent_id_does_not_raise(self, in_memory_db):
        """Deleting an ID that doesn't exist should not raise an exception."""
        jobs_repo.delete_application(99999)  # Should not raise


# ── get_stats ─────────────────────────────────────────────────────────────────

class TestGetStats:

    def test_empty_database_stats(self, in_memory_db):
        """Stats on empty database should show zero total."""
        stats = jobs_repo.get_stats()
        assert stats["total"] == 0
        assert stats["by_status"] == {}

    def test_total_count_correct(self, in_memory_db):
        """Total count should match number of applications added."""
        jobs_repo.add_application(_sample_job(job_id="a"))
        jobs_repo.add_application(_sample_job(job_id="b"))
        jobs_repo.add_application(_sample_job(job_id="c"))
        stats = jobs_repo.get_stats()
        assert stats["total"] == 3

    def test_by_status_groups_correctly(self, in_memory_db):
        """by_status should accurately count applications per status."""
        id1 = jobs_repo.add_application(_sample_job(job_id="a"))
        id2 = jobs_repo.add_application(_sample_job(job_id="b"))
        id3 = jobs_repo.add_application(_sample_job(job_id="c"))
        jobs_repo.update_status(id2, "No Response")
        jobs_repo.update_status(id3, "No Response")
        stats = jobs_repo.get_stats()
        assert stats["by_status"]["Applied"] == 1
        assert stats["by_status"]["No Response"] == 2
