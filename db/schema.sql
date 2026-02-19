-- JobTrack Local Database Schema
-- Version 1
-- Executed by db/database.py on first run.

-- ── Metadata ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS metadata (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

INSERT OR IGNORE INTO metadata (key, value) VALUES ('schema_version', '1');

-- ── Applied Jobs ────────────────────────────────────────────────────────────
-- One row per job the user has marked as applied.
CREATE TABLE IF NOT EXISTS applications (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id          TEXT NOT NULL,          -- From JobListing.job_id
    provider        TEXT NOT NULL,
    company         TEXT NOT NULL,
    title           TEXT NOT NULL,
    location        TEXT NOT NULL,
    job_url         TEXT NOT NULL DEFAULT '',
    date_applied    TEXT NOT NULL,          -- ISO 8601: "2026-02-19T14:30:00"
    status          TEXT NOT NULL DEFAULT 'Applied',
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ── Application Timeline Events ──────────────────────────────────────────────
-- One row per status-change event for each application.
-- This is the source of truth for the timeline columns in the tracker view.
CREATE TABLE IF NOT EXISTS timeline_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id  INTEGER NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    status          TEXT NOT NULL,          -- e.g. "Phone Screen"
    event_timestamp TEXT NOT NULL,          -- ISO 8601 — auto-set by the app
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ── Commute Cache ────────────────────────────────────────────────────────────
-- Cached commute times to avoid repeat API calls.
CREATE TABLE IF NOT EXISTS commute_cache (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    home_lat        REAL NOT NULL,
    home_lon        REAL NOT NULL,
    job_lat         REAL NOT NULL,
    job_lon         REAL NOT NULL,
    commute_minutes INTEGER,                -- NULL if route could not be calculated
    cached_at       TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_commute_cache_coords
    ON commute_cache (home_lat, home_lon, job_lat, job_lon);

-- ── Indexes ──────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_applications_status
    ON applications (status);

CREATE INDEX IF NOT EXISTS idx_applications_date
    ON applications (date_applied DESC);

CREATE INDEX IF NOT EXISTS idx_timeline_application
    ON timeline_events (application_id);
