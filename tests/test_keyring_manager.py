"""
tests/test_keyring_manager.py
================================
Tests for core/keyring_manager.py.
Uses monkeypatching to avoid touching the real OS credential store.
"""
import pytest
from unittest.mock import patch, MagicMock
from core import keyring_manager


def test_save_and_get_key(monkeypatch):
    """Saved key should be retrievable."""
    store = {}
    monkeypatch.setattr("keyring.set_password", lambda s, u, p: store.update({s: p}))
    monkeypatch.setattr("keyring.get_password", lambda s, u: store.get(s))
    # TODO: Call save_key and get_key, assert values match
    raise NotImplementedError


def test_has_key_returns_false_when_not_set(monkeypatch):
    monkeypatch.setattr("keyring.get_password", lambda s, u: None)
    # TODO: Assert has_key returns False
    raise NotImplementedError
