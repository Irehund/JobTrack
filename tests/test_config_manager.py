"""
tests/test_config_manager.py
==============================
Tests for core/config_manager.py.
Covers: load defaults, save/reload, deep merge, version migration,
atomic write safety, and corrupted file recovery.
"""

import copy
import json
import pytest
from pathlib import Path
from core import config_manager


@pytest.fixture
def tmp_config(tmp_path, monkeypatch):
    """Redirect config path to a temp directory for each test."""
    config_file = tmp_path / "config.json"
    monkeypatch.setattr(config_manager, "get_config_path", lambda: config_file)
    monkeypatch.setattr(config_manager, "get_config_dir", lambda: tmp_path)
    return config_file


# ── load() ────────────────────────────────────────────────────────────────────

def test_load_returns_defaults_when_no_file(tmp_config):
    """Loading with no config.json should return a copy of DEFAULTS."""
    result = config_manager.load()
    assert result["setup_complete"] == False
    assert result["theme"] == "system"
    assert result["providers"]["usajobs"]["enabled"] == True


def test_load_returns_deep_copy_of_defaults(tmp_config):
    """Mutating the returned config should not affect DEFAULTS."""
    result = config_manager.load()
    result["theme"] = "dark"
    assert config_manager.DEFAULTS["theme"] == "system"


def test_load_fills_missing_keys_from_defaults(tmp_config):
    """A partial config on disk should be merged with DEFAULTS for missing keys."""
    partial = {"theme": "dark", "setup_complete": True}
    tmp_config.write_text(json.dumps(partial), encoding="utf-8")

    result = config_manager.load()
    assert result["theme"] == "dark"                         # from disk
    assert result["setup_complete"] == True                  # from disk
    assert result["search_radius_miles"] == 50               # from defaults
    assert "location" in result                              # nested default preserved
    assert result["location"]["zip"] == ""                   # nested default preserved


def test_load_recovers_from_corrupted_json(tmp_config):
    """A corrupted config.json should silently return defaults."""
    tmp_config.write_text("{ this is not : valid json !!!", encoding="utf-8")
    result = config_manager.load()
    assert result == config_manager.load()  # Matches defaults


def test_load_preserves_nested_user_values(tmp_config):
    """Nested values set by the user should survive a load/merge cycle."""
    user_config = {
        "location": {
            "zip": "75126",
            "city": "Forney",
            "state": "TX",
            "latitude": 32.74,
            "longitude": -96.46,
        }
    }
    tmp_config.write_text(json.dumps(user_config), encoding="utf-8")
    result = config_manager.load()
    assert result["location"]["zip"] == "75126"
    assert result["location"]["city"] == "Forney"
    assert result["location"]["latitude"] == 32.74


# ── save() ────────────────────────────────────────────────────────────────────

def test_save_creates_file(tmp_config):
    """save() should create config.json if it doesn't exist."""
    config = config_manager.load()
    config_manager.save(config)
    assert tmp_config.exists()


def test_save_and_reload_round_trip(tmp_config):
    """Saving then loading should return identical data."""
    config = config_manager.load()
    config["theme"] = "dark"
    config["setup_complete"] = True
    config["location"]["zip"] = "75126"
    config["job_preferences"]["keywords"] = ["SOC Analyst", "Security Analyst"]

    config_manager.save(config)
    reloaded = config_manager.load()

    assert reloaded["theme"] == "dark"
    assert reloaded["setup_complete"] == True
    assert reloaded["location"]["zip"] == "75126"
    assert reloaded["job_preferences"]["keywords"] == ["SOC Analyst", "Security Analyst"]


def test_save_writes_valid_json(tmp_config):
    """The saved file should be parseable JSON."""
    config_manager.save(config_manager.load())
    content = tmp_config.read_text(encoding="utf-8")
    parsed = json.loads(content)   # raises if invalid
    assert isinstance(parsed, dict)


def test_save_no_tmp_file_left_behind(tmp_config):
    """After a successful save, no .tmp file should remain."""
    config_manager.save(config_manager.load())
    tmp_file = tmp_config.with_suffix(".tmp")
    assert not tmp_file.exists()


# ── reset() ───────────────────────────────────────────────────────────────────

def test_reset_deletes_config_file(tmp_config):
    """reset() should delete the config file if it exists."""
    config_manager.save(config_manager.load())
    assert tmp_config.exists()
    config_manager.reset()
    assert not tmp_config.exists()


def test_reset_returns_defaults(tmp_config):
    """reset() should return a fresh copy of DEFAULTS."""
    config = config_manager.load()
    config["theme"] = "dark"
    config_manager.save(config)

    result = config_manager.reset()
    assert result["theme"] == "system"
    assert result["setup_complete"] == False


def test_reset_safe_when_no_file_exists(tmp_config):
    """reset() should not raise if config.json doesn't exist."""
    assert not tmp_config.exists()
    result = config_manager.reset()
    assert result == config_manager.DEFAULTS


# ── _deep_merge() ─────────────────────────────────────────────────────────────

def test_deep_merge_simple_override():
    base = {"a": 1, "b": 2}
    override = {"b": 99, "c": 3}
    result = config_manager._deep_merge(base, override)
    assert result == {"a": 1, "b": 99, "c": 3}


def test_deep_merge_nested_dict_merged_not_replaced():
    base = {"nested": {"x": 10, "y": 20}}
    override = {"nested": {"x": 99}}
    result = config_manager._deep_merge(base, override)
    assert result["nested"]["x"] == 99   # overridden
    assert result["nested"]["y"] == 20   # preserved from base


def test_deep_merge_does_not_mutate_inputs():
    base = {"a": {"x": 1}}
    override = {"a": {"x": 99}}
    original_base = copy.deepcopy(base)
    config_manager._deep_merge(base, override)
    assert base == original_base


def test_deep_merge_override_replaces_non_dict_with_dict():
    """If base has a scalar and override has a dict for same key, override wins."""
    base = {"key": "string_value"}
    override = {"key": {"nested": True}}
    result = config_manager._deep_merge(base, override)
    assert result["key"] == {"nested": True}


# ── _migrate() ────────────────────────────────────────────────────────────────

def test_migrate_sets_current_version():
    """Migration should always set config_version to CONFIG_VERSION."""
    old_config = {"config_version": 0, "theme": "light"}
    result = config_manager._migrate(old_config)
    assert result["config_version"] == config_manager.CONFIG_VERSION


def test_migrate_preserves_existing_values():
    """Migration should not wipe user data."""
    config = config_manager.load()
    config["theme"] = "dark"
    config["config_version"] = 0
    result = config_manager._migrate(config)
    assert result["theme"] == "dark"


def test_migrate_handles_missing_version_key():
    """Config with no version key should migrate safely."""
    config = {"theme": "light"}
    result = config_manager._migrate(config)
    assert result["config_version"] == config_manager.CONFIG_VERSION

