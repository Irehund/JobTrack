"""
tests/test_config_manager.py
==============================
Tests for core/config_manager.py.
Covers: load defaults, save/reload, deep merge, version migration.
"""
import pytest
from core import config_manager


def test_load_returns_defaults_when_no_file(tmp_path, monkeypatch):
    """Loading with no config.json should return DEFAULTS."""
    monkeypatch.setattr(config_manager, "get_config_path", lambda: tmp_path / "config.json")
    # TODO: Call config_manager.load() and assert result matches DEFAULTS
    raise NotImplementedError


def test_save_and_reload(tmp_path, monkeypatch):
    """Saving then loading should return the same data."""
    monkeypatch.setattr(config_manager, "get_config_path", lambda: tmp_path / "config.json")
    # TODO: save a modified config, load it, assert values match
    raise NotImplementedError


def test_deep_merge_fills_missing_keys():
    """Deep merge should add missing keys from base without removing existing ones."""
    # TODO: Test _deep_merge with partial override dict
    raise NotImplementedError


def test_migration_adds_new_keys():
    """Migration should add keys introduced in newer config versions."""
    # TODO: Pass an old-version config dict to _migrate, assert new keys present
    raise NotImplementedError
