"""
core/config_manager.py
=======================
Loads and saves user configuration from/to a JSON file stored in the
platform-appropriate AppData directory. Handles default values and
version migrations so the app doesn't break when new settings are added.

Config file location:
    Windows: %APPDATA%/JobTrack/config.json
    macOS:   ~/Library/Application Support/JobTrack/config.json

Sensitive values (API keys) are NOT stored here —
they are stored via core/keyring_manager.py instead.
"""

import copy
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
    config_path = get_config_path()

    if not config_path.exists():
        return copy.deepcopy(DEFAULTS)

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            on_disk = json.load(f)
    except (json.JSONDecodeError, OSError):
        # Corrupted or unreadable config — return defaults.
        # The next save() call will overwrite with clean defaults.
        return copy.deepcopy(DEFAULTS)

    # Merge on-disk values into defaults so any new keys are filled in
    merged = _deep_merge(copy.deepcopy(DEFAULTS), on_disk)

    # Apply any version migrations
    merged = _migrate(merged)

    return merged


def save(config: dict[str, Any]) -> None:
    """
    Save config dict to disk as pretty-printed JSON.
    Writes atomically: to a .tmp file first, then renames, so a crash
    mid-write can never corrupt the config file.

    Raises:
        OSError: If the file cannot be written.
    """
    config_path = get_config_path()
    tmp_path = config_path.with_suffix(".tmp")

    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        # Atomic rename
        try:
            tmp_path.replace(config_path)
        except OSError:
            # Fallback for older Windows versions
            if config_path.exists():
                config_path.unlink()
            tmp_path.rename(config_path)
    except OSError:
        if tmp_path.exists():
            tmp_path.unlink()
        raise


def reset() -> dict[str, Any]:
    """
    Delete config.json and return a fresh copy of DEFAULTS.
    Used by 'Reset to Defaults' in Preferences.
    """
    config_path = get_config_path()
    if config_path.exists():
        config_path.unlink()
    return copy.deepcopy(DEFAULTS)


def _deep_merge(base: dict, override: dict) -> dict:
    """
    Recursively merge override into base.
    - Keys in override overwrite keys in base at the same level.
    - Nested dicts are merged recursively rather than replaced wholesale.
    - Keys in base that are absent from override are preserved as-is.

    Example:
        base     = {"a": 1, "b": {"x": 10, "y": 20}}
        override = {"b": {"x": 99}, "c": 3}
        result   = {"a": 1, "b": {"x": 99, "y": 20}, "c": 3}
    """
    result = copy.deepcopy(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def _migrate(config: dict[str, Any]) -> dict[str, Any]:
    """
    Apply any necessary migrations when the config_version on disk
    is older than the current CONFIG_VERSION.

    Each migration step updates the version number after applying changes
    so they are idempotent and never applied twice.
    """
    version = config.get("config_version", 0)

    # Future migrations go here as CONFIG_VERSION increments:
    # if version < 2:
    #     config.setdefault("new_section", {"new_key": "default_value"})
    #     config["config_version"] = 2
    #     version = 2

    config["config_version"] = CONFIG_VERSION
    return config
