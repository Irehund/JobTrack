"""
integrations/google_sheets.py
================================
Manages the Google Sheets application tracker integration.

On first connection, creates:
    My Drive > JobTrack > JobTrack Applications  (spreadsheet)

The spreadsheet is owned entirely by the user — JobTrack only has
the access the user explicitly grants during the OAuth consent step.

Column structure (base columns, always present):
    A: Company
    B: Job Title
    C: Location
    D: Provider
    E: Job URL
    F: Date Applied
    G: Status

Timeline columns (added automatically when status advances):
    H+: e.g. "Phone Screen Date", "Interview Date", etc.
"""

import os
from pathlib import Path
from typing import Optional

import gspread
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

DRIVE_FOLDER_NAME = "JobTrack"
SPREADSHEET_NAME = "JobTrack Applications"

# Scopes needed — Drive for folder creation, Sheets for read/write
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

BASE_COLUMNS = [
    "Company", "Job Title", "Location", "Provider",
    "Job URL", "Date Applied", "Status"
]


class GoogleSheetsTracker:
    """Manages creating, reading, and writing the job application tracker sheet."""

    def __init__(self, token_path: str):
        """
        Args:
            token_path: Path to the OAuth token JSON file.
                        Stored in AppData — never in the project directory.
        """
        self.token_path = token_path
        self._client: Optional[gspread.Client] = None
        self._worksheet: Optional[gspread.Worksheet] = None

    def authenticate(self, credentials_json: str) -> bool:
        """
        Run the OAuth2 flow. Opens a browser window for the user to grant access.
        Saves the resulting token to self.token_path for future sessions.

        Args:
            credentials_json: Path to the OAuth client secrets JSON from Google Cloud Console.

        Returns:
            True if authentication succeeded.
        """
        # TODO: Implement OAuth2 flow using InstalledAppFlow
        # 1. Run flow.run_local_server(port=0)
        # 2. Save credentials to self.token_path
        # 3. Initialize self._client = gspread.authorize(creds)
        raise NotImplementedError

    def is_authenticated(self) -> bool:
        """Return True if a valid token exists and has not expired."""
        # TODO: Check if token_path exists and credentials are valid/refreshable
        raise NotImplementedError

    def get_or_create_spreadsheet(self) -> gspread.Spreadsheet:
        """
        Find or create the JobTrack spreadsheet in the user's Drive.
        Creates the 'JobTrack' folder first if needed.

        Returns:
            The gspread Spreadsheet object.
        """
        # TODO:
        # 1. Search Drive for a folder named DRIVE_FOLDER_NAME
        # 2. Create it if not found
        # 3. Search folder for a sheet named SPREADSHEET_NAME
        # 4. Create it with BASE_COLUMNS header row if not found
        # 5. Return the spreadsheet object
        raise NotImplementedError

    def append_application(self, job_data: dict) -> None:
        """
        Add a new row to the tracker when the user marks a job as applied.

        Args:
            job_data: Dict with keys matching BASE_COLUMNS
        """
        # TODO: Append a row to self._worksheet in BASE_COLUMNS order
        raise NotImplementedError

    def update_status(self, row_index: int, status: str, timestamp: str) -> None:
        """
        Update the Status cell for a row and write a timestamp to the
        appropriate timeline column, creating it if it doesn't exist yet.

        Args:
            row_index: 1-based row number in the spreadsheet
            status:    New status string, e.g. "Phone Screen"
            timestamp: ISO format timestamp string
        """
        # TODO: Update Status column, then call _ensure_timeline_column()
        raise NotImplementedError

    def _ensure_timeline_column(self, status: str) -> int:
        """
        Find or create a column for the given status's timestamp.
        Column name format: "<Status> Date", e.g. "Phone Screen Date"

        Returns:
            The 1-based column index of the timeline column.
        """
        # TODO: Check header row for existing column, append if missing
        raise NotImplementedError

    def get_all_applications(self) -> list[dict]:
        """
        Return all rows from the tracker as a list of dicts.
        Used to populate the Tracker panel on app launch.
        """
        # TODO: Read all rows, map to dicts using header row as keys
        raise NotImplementedError
