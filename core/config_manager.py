"""
core/config_manager.py
=======================
Loads and saves user configuration from/to a JSON file stored in the
platform-appropriate AppData directory. Handles default values and
version migrations so the app doesn't break when new settings are added.

Config file location:
    Windows: %APPDATA%\JobTrack\config.json
    macOS:   ~/Library/Application Support/JobTrack/config.json

Sensitive values (API keys) are NOT stored here —
they are stored via core/keyring_manager.py instead.
"""

import json
import os
import platform
from pathlib import Path
from typing import Any

APP_NAME = "JobTrack"

# Increment this when new required keys are added to DEFAULTS
CONFIG_VERSION = 1

DEFAULTS: dict[str, Any] = {
    "config_version": CONFIG_VERSION,
    "setup_complete": False,
    "theme": "system",                  # "light" | "dark" | "system"
    "location": {
        "zip": "",
        "city": "",
        "state": "",
        "latitude": None,
        "longitude": None,
    },
    "search_radius_miles": 50,
    "job_preferences": {
        "keywords": [],                 # List of job title keywords
        "work_type": "any",             # "remote" | "hybrid" | "onsite" | "any"
        "experience_level": "any",      # "entry" | "mid" | "senior" | "any"
    },
    "providers": {
        "usajobs": {"enabled": True},   # Always on — cannot be disabled
        "indeed": {"enabled": False},
        "linkedin": {"enabled": False},
        "glassdoor": {"enabled": False},
        "adzuna": {"enabled": False},
    },
    "tracker": {
        "mode": "local",                # "local" | "google" | "both"
        "google_sheet_id": None,
        "google_sheet_name": "JobTrack Applications",
    },
    "search": {
        "auto_search_on_launch": True,
    },
}


def get_config_dir() -> Path:
    """Return the platform-appropriate directory for storing config.json."""
    system = platform.system()
    if system == "Windows":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif system == "Darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path.home() / ".config"
    config_dir = base / APP_NAME
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_config_path() -> Path:
    """Return the full path to config.json."""
    return get_config_dir() / "config.json"


def load() -> dict[str, Any]:
    """
    Load config from disk, merging with defaults for any missing keys.
    If config.json does not exist, returns a fresh copy of DEFAULTS.
    """
    # TODO: Implement load logic
    # 1. Read config.json if it exists
    # 2. Deep-merge with DEFAULTS so missing keys are filled in
    # 3. Run _migrate() to handle version upgrades
    # 4. Return the merged config dict
    raise NotImplementedError


def save(config: dict[str, Any]) -> None:
    """
    Save config dict to disk as pretty-printed JSON.
    Raises OSError if the file cannot be written.
    """
    # TODO: Implement save logic
    # 1. Serialize config to JSON with indent=2
    # 2. Write to get_config_path() atomically (write to .tmp then rename)
    raise NotImplementedError


def reset() -> dict[str, Any]:
    """
    Delete config.json and return a fresh copy of DEFAULTS.
    Used by 'Reset to Defaults' in Preferences.
    """
    # TODO: Delete config.json if it exists, return copy of DEFAULTS
    raise NotImplementedError


def _deep_merge(base: dict, override: dict) -> dict:
    """
    Recursively merge override into base.
    Keys in base that are missing from override are preserved.
    """
    # TODO: Implement recursive dict merge
    raise NotImplementedError


def _migrate(config: dict[str, Any]) -> dict[str, Any]:
    """
    Apply any necessary migrations when the config_version on disk
    is older than the current CONFIG_VERSION.
    Each migration step should be added as a versioned block here.
    """
    # TODO: Add migration steps as CONFIG_VERSION increments
    # Example structure:
    #   version = config.get("config_version", 0)
    #   if version < 2:
    #       config["new_key"] = "default_value"
    #       config["config_version"] = 2
    return config
