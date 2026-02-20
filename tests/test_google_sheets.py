"""
tests/test_google_sheets.py
=============================
Tests for integrations/google_sheets.py and sheets_sync_manager.py.
All Google API calls are mocked — no network, no credentials needed.
"""

import pytest
from unittest.mock import MagicMock, patch, call
from integrations.google_sheets import (
    GoogleSheetsTracker,
    BASE_COLUMNS,
    TIMELINE_STATUSES,
    SHEET_TAB_NAME,
    _col_letter,
)


# ── _col_letter ───────────────────────────────────────────────────────────────

class TestColLetter:

    def test_a_is_1(self):        assert _col_letter(1)  == "A"
    def test_g_is_7(self):        assert _col_letter(7)  == "G"
    def test_z_is_26(self):       assert _col_letter(26) == "Z"
    def test_aa_is_27(self):      assert _col_letter(27) == "AA"
    def test_az_is_52(self):      assert _col_letter(52) == "AZ"
    def test_ba_is_53(self):      assert _col_letter(53) == "BA"

    def test_sequence_is_correct(self):
        expected = ["A","B","C","D","E","F","G","H","I","J",
                    "K","L","M","N","O","P","Q","R","S","T",
                    "U","V","W","X","Y","Z","AA","AB"]
        assert [_col_letter(i) for i in range(1, 29)] == expected


# ── Constants ─────────────────────────────────────────────────────────────────

class TestConstants:

    def test_base_columns_correct_order(self):
        assert BASE_COLUMNS[0] == "Company"
        assert BASE_COLUMNS[1] == "Job Title"
        assert BASE_COLUMNS[6] == "Status"
        assert len(BASE_COLUMNS) == 7

    def test_timeline_statuses_nonempty(self):
        assert len(TIMELINE_STATUSES) > 0

    def test_phone_screen_is_timeline_status(self):
        assert "Phone Screen" in TIMELINE_STATUSES

    def test_offer_received_is_timeline_status(self):
        assert "Offer Received" in TIMELINE_STATUSES

    def test_applied_is_not_timeline_status(self):
        assert "Applied" not in TIMELINE_STATUSES

    def test_no_response_is_not_timeline_status(self):
        assert "No Response" not in TIMELINE_STATUSES


# ── GoogleSheetsTracker fixtures ──────────────────────────────────────────────

def _make_tracker(authenticated=True) -> GoogleSheetsTracker:
    """Return a tracker with a mocked gspread client."""
    tracker = GoogleSheetsTracker(token_path="/tmp/fake_token.json")
    if authenticated:
        tracker._client = MagicMock()
        mock_ws = MagicMock()
        mock_ws.row_values.return_value = BASE_COLUMNS[:]
        mock_ws.get_all_values.return_value = [BASE_COLUMNS] + [
            ["CISA","SOC Analyst","Dallas, TX","usajobs",
             "https://usajobs.gov/1","2026-02-01","Applied"]
        ]
        mock_ws.get_all_records.return_value = [
            {"Company":"CISA","Job Title":"SOC Analyst","Location":"Dallas, TX",
             "Provider":"usajobs","Job URL":"https://usajobs.gov/1",
             "Date Applied":"2026-02-01","Status":"Applied"}
        ]
        mock_ss = MagicMock()
        mock_ss.worksheet.return_value = mock_ws
        mock_ss.sheet1 = mock_ws
        mock_ss.id = "fake_spreadsheet_id"
        tracker._spreadsheet = mock_ss
        tracker._worksheet   = mock_ws
        tracker._headers     = BASE_COLUMNS[:]
    return tracker


# ── is_authenticated ──────────────────────────────────────────────────────────

class TestIsAuthenticated:

    def test_returns_true_with_client(self):
        t = _make_tracker(authenticated=True)
        assert t.is_authenticated() is True

    def test_returns_false_without_client(self):
        t = _make_tracker(authenticated=False)
        with patch.object(t, "load_saved_credentials", return_value=False):
            assert t.is_authenticated() is False

    def test_attempts_load_when_no_client(self):
        t = _make_tracker(authenticated=False)
        with patch.object(t, "load_saved_credentials", return_value=True) as mock_load:
            t.is_authenticated()
            mock_load.assert_called_once()


# ── append_application ────────────────────────────────────────────────────────

class TestAppendApplication:

    def test_appends_row_in_correct_column_order(self):
        t = _make_tracker()
        t._worksheet.get_all_values.return_value = [BASE_COLUMNS, ["row2"]]

        job_data = {
            "company":      "CISA",
            "title":        "SOC Analyst",
            "location":     "Dallas, TX",
            "provider":     "usajobs",
            "job_url":      "https://usajobs.gov/1",
            "date_applied": "2026-02-01T12:00:00",
            "status":       "Applied",
        }
        t.append_application(job_data)
        call_args = t._worksheet.append_row.call_args[0][0]
        assert call_args[0] == "CISA"
        assert call_args[1] == "SOC Analyst"
        assert call_args[6] == "Applied"

    def test_date_applied_truncated_to_date_only(self):
        t = _make_tracker()
        t._worksheet.get_all_values.return_value = [BASE_COLUMNS, ["r"]]
        t.append_application({"date_applied": "2026-02-01T14:30:00",
                               "company":"X","title":"Y","location":"Z",
                               "provider":"p","job_url":"u","status":"Applied"})
        row = t._worksheet.append_row.call_args[0][0]
        assert row[5] == "2026-02-01"   # No time component

    def test_returns_row_index(self):
        t = _make_tracker()
        # 1 header + 1 existing + 1 new = 3 rows total
        t._worksheet.get_all_values.return_value = [BASE_COLUMNS, ["r1"], ["r2"]]
        result = t.append_application({
            "company":"X","title":"Y","location":"Z",
            "provider":"p","job_url":"u","date_applied":"2026-01-01","status":"Applied"
        })
        assert result == 3

    def test_missing_fields_default_to_empty_string(self):
        t = _make_tracker()
        t._worksheet.get_all_values.return_value = [BASE_COLUMNS]
        t.append_application({})   # No fields at all — should not crash
        row = t._worksheet.append_row.call_args[0][0]
        assert row[0] == ""   # company defaults to ""


# ── update_status ─────────────────────────────────────────────────────────────

class TestUpdateStatus:

    def test_updates_status_cell(self):
        t = _make_tracker()
        t.update_status(3, "Applied", "2026-02-01T12:00:00")
        # Status is column 7 (G)
        calls = t._worksheet.update_cell.call_args_list
        status_call = [c for c in calls if c[0][1] == 7]
        assert len(status_call) >= 1
        assert status_call[0][0][2] == "Applied"

    def test_non_timeline_status_no_extra_column(self):
        """Applied and No Response should not add a timeline column."""
        t = _make_tracker()
        t.update_status(2, "Applied", "2026-02-01T12:00:00")
        # Only one update_cell call — the status column itself
        assert t._worksheet.update_cell.call_count == 1

    def test_timeline_status_writes_timestamp(self):
        """Phone Screen should update status AND write a timestamp column."""
        t = _make_tracker()
        t._worksheet.row_values.return_value = BASE_COLUMNS[:]
        t.update_status(3, "Phone Screen", "2026-02-15T09:30:00")
        # Should have called update_cell at least twice (status + timestamp)
        assert t._worksheet.update_cell.call_count >= 2

    def test_timestamp_truncated_to_seconds(self):
        """Timestamp stored in sheet should not have microseconds."""
        t = _make_tracker()
        t._worksheet.row_values.return_value = BASE_COLUMNS[:]
        t.update_status(2, "Phone Screen", "2026-02-15T09:30:00.123456")
        calls = t._worksheet.update_cell.call_args_list
        ts_calls = [c for c in calls if "2026" in str(c[0][2])]
        assert ts_calls[0][0][2] == "2026-02-15T09:30:00"


# ── _ensure_timeline_column ───────────────────────────────────────────────────

class TestEnsureTimelineColumn:

    def test_returns_existing_column_index(self):
        t = _make_tracker()
        headers = BASE_COLUMNS + ["Phone Screen Date"]
        t._worksheet.row_values.return_value = headers
        t._headers = headers
        idx = t._ensure_timeline_column("Phone Screen")
        assert idx == 8   # 7 base cols + 1 = col 8
        t._worksheet.update_cell.assert_not_called()

    def test_creates_new_column_if_missing(self):
        t = _make_tracker()
        t._worksheet.row_values.return_value = BASE_COLUMNS[:]
        t._headers = BASE_COLUMNS[:]
        idx = t._ensure_timeline_column("Phone Screen")
        assert idx == 8   # First timeline column
        t._worksheet.update_cell.assert_called_once_with(1, 8, "Phone Screen Date")

    def test_second_timeline_column_is_9(self):
        t = _make_tracker()
        headers = BASE_COLUMNS + ["Phone Screen Date"]
        t._worksheet.row_values.return_value = headers
        t._headers = headers
        idx = t._ensure_timeline_column("Interview Scheduled")
        assert idx == 9


# ── get_all_applications ──────────────────────────────────────────────────────

class TestGetAllApplications:

    def test_returns_list_of_dicts(self):
        t = _make_tracker()
        result = t.get_all_applications()
        assert isinstance(result, list)
        assert all(isinstance(r, dict) for r in result)

    def test_dict_keys_match_headers(self):
        t = _make_tracker()
        result = t.get_all_applications()
        if result:
            assert "Company" in result[0]
            assert "Status"  in result[0]

    def test_returns_correct_record(self):
        t = _make_tracker()
        result = t.get_all_applications()
        assert result[0]["Company"]   == "CISA"
        assert result[0]["Job Title"] == "SOC Analyst"


# ── sync_from_local ───────────────────────────────────────────────────────────

class TestSyncFromLocal:

    def test_skips_already_existing_by_url(self):
        t = _make_tracker()
        apps = [{"job_url": "https://usajobs.gov/1",  # already in sheet
                 "company":"CISA","title":"SOC Analyst","location":"Dallas",
                 "provider":"usajobs","date_applied":"2026-02-01","status":"Applied"}]
        stats = t.sync_from_local(apps)
        assert stats["skipped"] == 1
        assert stats["appended"] == 0

    def test_appends_new_applications(self):
        t = _make_tracker()
        t._worksheet.get_all_values.return_value = [BASE_COLUMNS, ["r"]]
        apps = [{"job_url": "https://usajobs.gov/NEW",
                 "company":"FBI","title":"Security Analyst","location":"DC",
                 "provider":"usajobs","date_applied":"2026-02-01","status":"Applied"}]
        with patch.object(t, "append_application", return_value=3) as mock_append:
            stats = t.sync_from_local(apps)
        assert stats["appended"] == 1
        mock_append.assert_called_once()

    def test_mixed_new_and_existing(self):
        t = _make_tracker()
        t._worksheet.get_all_values.return_value = [BASE_COLUMNS, ["r"]]
        apps = [
            {"job_url": "https://usajobs.gov/1",     # existing
             "company":"CISA","title":"SOC","location":"TX",
             "provider":"usajobs","date_applied":"2026-01-01","status":"Applied"},
            {"job_url": "https://usajobs.gov/NEW2",  # new
             "company":"NSA","title":"Intel Analyst","location":"MD",
             "provider":"usajobs","date_applied":"2026-01-15","status":"Applied"},
        ]
        with patch.object(t, "append_application", return_value=3):
            stats = t.sync_from_local(apps)
        assert stats["appended"] == 1
        assert stats["skipped"]  == 1


# ── revoke ────────────────────────────────────────────────────────────────────

class TestRevoke:

    def test_revoke_deletes_token_file(self, tmp_path):
        token = tmp_path / "token.json"
        token.write_text('{"token": "fake"}')
        t = GoogleSheetsTracker(token_path=str(token))
        t._client = MagicMock()
        t.revoke()
        assert not token.exists()

    def test_revoke_clears_client(self):
        t = _make_tracker()
        t.revoke()
        assert t._client      is None
        assert t._spreadsheet is None
        assert t._worksheet   is None
        assert t._headers     == []

    def test_revoke_safe_when_no_token(self, tmp_path):
        t = GoogleSheetsTracker(token_path=str(tmp_path / "nonexistent.json"))
        t.revoke()   # Should not raise


# ── sheets_sync_manager ───────────────────────────────────────────────────────

class TestSheetsSyncManager:

    def test_get_tracker_returns_none_when_local_mode(self):
        from integrations import sheets_sync_manager
        with patch("integrations.sheets_sync_manager.config_manager.load",
                   return_value={"tracker": {"mode": "local"}}):
            assert sheets_sync_manager.get_tracker() is None

    def test_get_tracker_returns_none_when_not_authenticated(self):
        from integrations import sheets_sync_manager
        with patch("integrations.sheets_sync_manager.config_manager.load",
                   return_value={"tracker": {"mode": "google"}}):
            with patch("integrations.sheets_sync_manager.GoogleSheetsTracker") as MockTracker:
                MockTracker.return_value.is_authenticated.return_value = False
                result = sheets_sync_manager.get_tracker()
                assert result is None

    def test_push_new_application_returns_false_without_tracker(self):
        from integrations import sheets_sync_manager
        with patch("integrations.sheets_sync_manager.get_tracker", return_value=None):
            assert sheets_sync_manager.push_new_application(1) is False

    def test_push_status_update_returns_false_without_tracker(self):
        from integrations import sheets_sync_manager
        with patch("integrations.sheets_sync_manager.get_tracker", return_value=None):
            result = sheets_sync_manager.push_status_update(1, "Applied", "2026-01-01")
            assert result is False

    def test_full_sync_returns_zeros_without_tracker(self):
        from integrations import sheets_sync_manager
        with patch("integrations.sheets_sync_manager.get_tracker", return_value=None):
            stats = sheets_sync_manager.full_sync()
            assert stats["appended"] == 0
            assert stats["failed"]   == 0

    def test_full_sync_calls_sync_from_local(self):
        from integrations import sheets_sync_manager
        mock_tracker = MagicMock()
        mock_tracker.sync_from_local.return_value = {"appended":2,"updated":0,"skipped":1}
        with patch("integrations.sheets_sync_manager.get_tracker", return_value=mock_tracker):
            with patch("integrations.sheets_sync_manager.jobs_repo.get_all_applications",
                       return_value=[{"id":1},{"id":2}]):
                stats = sheets_sync_manager.full_sync()
        mock_tracker.sync_from_local.assert_called_once()
        assert stats["appended"] == 2

    def test_push_new_application_calls_append(self):
        from integrations import sheets_sync_manager
        mock_tracker = MagicMock()
        mock_tracker.append_application.return_value = 3
        mock_tracker._spreadsheet.id = "ss_id"
        with patch("integrations.sheets_sync_manager.get_tracker", return_value=mock_tracker):
            with patch("integrations.sheets_sync_manager.jobs_repo.get_application",
                       return_value={"id":1,"company":"CISA","title":"SOC","location":"TX",
                                     "provider":"usajobs","job_url":"u","date_applied":"2026-01-01",
                                     "status":"Applied"}):
                with patch("integrations.sheets_sync_manager._save_sync_row"):
                    result = sheets_sync_manager.push_new_application(1)
        assert result is True
        mock_tracker.append_application.assert_called_once()
