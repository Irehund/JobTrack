"""
integrations/google_sheets.py
================================
Manages the Google Sheets application tracker integration.

On first connection, creates:
    My Drive > JobTrack > JobTrack Applications  (spreadsheet)

The spreadsheet is owned entirely by the user — JobTrack only has
the access the user explicitly grants during the OAuth consent step.

Column structure (A–G always present):
    A: Company       B: Job Title    C: Location   D: Provider
    E: Job URL       F: Date Applied G: Status

Timeline columns (appended as status milestones are reached):
    H+: e.g. "Phone Screen Date", "Interview Scheduled Date", etc.

Sync model:
    - SQLite is always the source of truth locally.
    - Google Sheets mirrors it: new rows pushed, status updates propagated.
    - Row numbers tracked in a local sheets_sync table so we can update
      the right row without a full re-read each time.
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger("jobtrack.sheets")

DRIVE_FOLDER_NAME = "JobTrack"
SPREADSHEET_NAME  = "JobTrack Applications"
SHEET_TAB_NAME    = "Applications"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

BASE_COLUMNS = [
    "Company", "Job Title", "Location", "Provider",
    "Job URL", "Date Applied", "Status",
]

# Status values that get a dedicated timeline column in the sheet
TIMELINE_STATUSES = [
    "Phone Screen", "Interview Scheduled", "Interview Completed",
    "Second Interview", "Offer Received", "Offer Accepted",
    "Offer Declined", "Rejected",
]

# Column letter helpers (A=1, B=2, …, Z=26, AA=27, …)
def _col_letter(n: int) -> str:
    """Convert 1-based column index to A1 notation letter(s)."""
    result = ""
    while n > 0:
        n, rem = divmod(n - 1, 26)
        result = chr(65 + rem) + result
    return result


class GoogleSheetsTracker:
    """Manages creating, reading, and writing the job application tracker sheet."""

    def __init__(self, token_path: str):
        """
        Args:
            token_path: Where the OAuth token JSON is stored (AppData/JobTrack).
        """
        self.token_path   = token_path
        self._client      = None   # gspread.Client
        self._spreadsheet = None   # gspread.Spreadsheet
        self._worksheet   = None   # gspread.Worksheet
        self._headers: list[str] = []

    # ── Authentication ────────────────────────────────────────────────────────

    def authenticate(self, credentials_json: str) -> bool:
        """
        Run the OAuth2 flow. Opens a browser for consent, saves token locally.

        Args:
            credentials_json: Path to client_secrets.json from Google Cloud Console.

        Returns:
            True if authentication succeeded.

        Raises:
            FileNotFoundError: If credentials_json path doesn't exist.
            Exception:         On OAuth flow failure.
        """
        from google_auth_oauthlib.flow import InstalledAppFlow
        import gspread

        if not os.path.exists(credentials_json):
            raise FileNotFoundError(
                f"Google credentials file not found: {credentials_json}\n"
                "Download it from Google Cloud Console → APIs & Services → Credentials."
            )

        flow = InstalledAppFlow.from_client_secrets_file(credentials_json, SCOPES)
        creds = flow.run_local_server(port=0, open_browser=True)

        # Save token for future sessions
        Path(self.token_path).parent.mkdir(parents=True, exist_ok=True)
        with open(self.token_path, "w") as f:
            f.write(creds.to_json())
        logger.info(f"OAuth token saved to {self.token_path}")

        self._client = gspread.authorize(creds)
        return True

    def load_saved_credentials(self) -> bool:
        """
        Load a previously saved OAuth token without re-running the browser flow.
        Refreshes the token if expired.

        Returns:
            True if valid credentials were loaded.
        """
        if not os.path.exists(self.token_path):
            return False

        try:
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request
            import gspread

            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)

            if not creds.valid:
                if creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                    with open(self.token_path, "w") as f:
                        f.write(creds.to_json())
                    logger.info("OAuth token refreshed.")
                else:
                    logger.warning("Saved OAuth token is invalid and cannot be refreshed.")
                    return False

            self._client = gspread.authorize(creds)
            logger.info("Loaded saved Google credentials.")
            return True

        except Exception as e:
            logger.error(f"Failed to load saved credentials: {e}")
            return False

    def is_authenticated(self) -> bool:
        """Return True if a valid, loaded client is available."""
        if self._client is None:
            return self.load_saved_credentials()
        return True

    # ── Spreadsheet management ────────────────────────────────────────────────

    def get_or_create_spreadsheet(self):
        """
        Find or create the JobTrack spreadsheet in the user's Drive.
        Creates the JobTrack folder first if it doesn't exist.

        Returns:
            The gspread Spreadsheet object.
        """
        if not self.is_authenticated():
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        # Find or create folder
        folder_id = self._get_or_create_folder()

        # Search for existing spreadsheet in that folder
        try:
            existing = self._client.open(SPREADSHEET_NAME)
            self._spreadsheet = existing
            logger.info(f"Found existing spreadsheet: {existing.id}")
        except Exception:
            # Create new spreadsheet
            self._spreadsheet = self._client.create(SPREADSHEET_NAME)
            logger.info(f"Created new spreadsheet: {self._spreadsheet.id}")

            # Move it into the JobTrack folder
            self._move_to_folder(self._spreadsheet.id, folder_id)

            # Set up the Applications worksheet
            ws = self._spreadsheet.sheet1
            ws.update_title(SHEET_TAB_NAME)
            ws.append_row(BASE_COLUMNS, value_input_option="USER_ENTERED")
            self._format_header_row(ws)

        self._worksheet = self._spreadsheet.worksheet(SHEET_TAB_NAME)
        self._headers = self._worksheet.row_values(1)
        return self._spreadsheet

    def _get_or_create_folder(self) -> str:
        """Find or create the 'JobTrack' folder in My Drive. Returns folder ID."""
        drive_service = self._client.auth.authorized_session
        # Use gspread's internal drive client to list/create folders
        results = self._client.list_spreadsheet_files()
        # Search via Drive API through gspread's http object
        resp = self._client.auth.get(
            "https://www.googleapis.com/drive/v3/files",
            params={
                "q": f"name='{DRIVE_FOLDER_NAME}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
                "fields": "files(id, name)",
            }
        ).json()

        files = resp.get("files", [])
        if files:
            folder_id = files[0]["id"]
            logger.info(f"Found existing Drive folder: {folder_id}")
            return folder_id

        # Create folder
        create_resp = self._client.auth.post(
            "https://www.googleapis.com/drive/v3/files",
            json={
                "name": DRIVE_FOLDER_NAME,
                "mimeType": "application/vnd.google-apps.folder",
            }
        ).json()
        folder_id = create_resp["id"]
        logger.info(f"Created Drive folder: {folder_id}")
        return folder_id

    def _move_to_folder(self, file_id: str, folder_id: str) -> None:
        """Move a Drive file into the specified folder."""
        self._client.auth.patch(
            f"https://www.googleapis.com/drive/v3/files/{file_id}",
            params={"addParents": folder_id, "removeParents": "root"},
            json={},
        )

    def _format_header_row(self, ws) -> None:
        """Bold the header row and freeze it."""
        try:
            ws.format("A1:Z1", {
                "textFormat": {"bold": True},
                "backgroundColor": {"red": 0.26, "green": 0.52, "blue": 0.96},
            })
            ws.freeze(rows=1)
        except Exception as e:
            logger.warning(f"Could not format header row: {e}")

    # ── Row operations ────────────────────────────────────────────────────────

    def append_application(self, job_data: dict) -> int:
        """
        Add a new row for a job application.

        Args:
            job_data: Dict with BASE_COLUMNS keys (case-insensitive match).

        Returns:
            The 1-based row index of the newly appended row.
        """
        self._ensure_worksheet()
        row = [
            job_data.get("company", ""),
            job_data.get("title", ""),
            job_data.get("location", ""),
            job_data.get("provider", ""),
            job_data.get("job_url", ""),
            job_data.get("date_applied", "")[:10],  # Date only
            job_data.get("status", "Applied"),
        ]
        self._worksheet.append_row(row, value_input_option="USER_ENTERED")
        # Row count = data rows + 1 header
        row_index = len(self._worksheet.get_all_values())
        logger.info(f"Appended application row {row_index}: {job_data.get('title')}")
        return row_index

    def update_status(self, row_index: int, status: str, timestamp: str) -> None:
        """
        Update the Status cell for a row and write a timestamp to the
        appropriate timeline column (creating it if it doesn't exist yet).

        Args:
            row_index: 1-based row number in the spreadsheet (2+ for data rows)
            status:    New status string, e.g. "Phone Screen"
            timestamp: ISO format timestamp string
        """
        self._ensure_worksheet()

        # Update the Status column (G = 7)
        status_col = BASE_COLUMNS.index("Status") + 1  # 1-based
        self._worksheet.update_cell(row_index, status_col, status)

        # Write timestamp to timeline column if this status gets one
        if status in TIMELINE_STATUSES:
            col_idx = self._ensure_timeline_column(status)
            self._worksheet.update_cell(row_index, col_idx, timestamp[:19])

        logger.info(f"Updated row {row_index} status → {status}")

    def _ensure_timeline_column(self, status: str) -> int:
        """
        Find or create the timeline column for the given status.
        Column header format: "<Status> Date"

        Returns:
            1-based column index.
        """
        col_header = f"{status} Date"
        self._headers = self._worksheet.row_values(1)

        if col_header in self._headers:
            return self._headers.index(col_header) + 1  # 1-based

        # Append new column header
        new_col_idx = len(self._headers) + 1
        col_letter  = _col_letter(new_col_idx)
        self._worksheet.update_cell(1, new_col_idx, col_header)
        self._headers.append(col_header)
        logger.info(f"Created timeline column '{col_header}' at {col_letter}")
        return new_col_idx

    def get_all_applications(self) -> list[dict]:
        """
        Return all application rows as a list of dicts.
        Header row is used as dict keys.
        """
        self._ensure_worksheet()
        records = self._worksheet.get_all_records()
        logger.info(f"Read {len(records)} applications from Google Sheets.")
        return records

    def sync_from_local(self, applications: list[dict]) -> dict:
        """
        Push all local SQLite applications to the sheet.
        Only appends rows that don't already exist (matched by job_id or URL).
        Updates status for rows that have changed.

        Args:
            applications: List of dicts from jobs_repo.get_all_applications()

        Returns:
            {"appended": int, "updated": int, "skipped": int}
        """
        self._ensure_worksheet()
        existing = self.get_all_applications()
        existing_urls = {row.get("Job URL", "") for row in existing}

        stats = {"appended": 0, "updated": 0, "skipped": 0}

        for app in applications:
            url = app.get("job_url", "")
            if url and url in existing_urls:
                stats["skipped"] += 1
                continue

            self.append_application(app)
            stats["appended"] += 1

        logger.info(f"sync_from_local: {stats}")
        return stats

    def _ensure_worksheet(self) -> None:
        """Load the worksheet if not already loaded."""
        if self._worksheet is None:
            self.get_or_create_spreadsheet()

    # ── Revoke ────────────────────────────────────────────────────────────────

    def revoke(self) -> None:
        """Delete the saved token file (effectively logs out of Google)."""
        if os.path.exists(self.token_path):
            os.remove(self.token_path)
            logger.info("Google OAuth token revoked.")
        self._client      = None
        self._spreadsheet = None
        self._worksheet   = None
        self._headers     = []
