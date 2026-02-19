"""
tests/test_keyring_manager.py
================================
Tests for core/keyring_manager.py.
Monkeypatches the keyring library to avoid touching the real OS
credential store during testing.
"""

import pytest
from unittest.mock import MagicMock, patch
from core import keyring_manager


@pytest.fixture
def mock_keyring(monkeypatch):
    """
    Replace keyring library calls with an in-memory dict store.
    Returns the store dict so tests can inspect it directly.
    """
    store = {}

    def fake_set(service, username, password):
        store[service] = password

    def fake_get(service, username):
        return store.get(service)

    def fake_delete(service, username):
        import keyring.errors
        if service not in store:
            raise keyring.errors.PasswordDeleteError("not found")
        del store[service]

    monkeypatch.setattr("keyring.set_password", fake_set)
    monkeypatch.setattr("keyring.get_password", fake_get)
    monkeypatch.setattr("keyring.delete_password", fake_delete)
    return store


# ── save_key / get_key ────────────────────────────────────────────────────────

def test_save_and_get_key(mock_keyring):
    """A key saved via save_key should be retrievable via get_key."""
    keyring_manager.save_key("indeed", "test-api-key-12345")
    result = keyring_manager.get_key("indeed")
    assert result == "test-api-key-12345"


def test_save_key_strips_whitespace(mock_keyring):
    """Keys with leading/trailing spaces should be stored trimmed."""
    keyring_manager.save_key("usajobs", "  abc123key  ")
    assert keyring_manager.get_key("usajobs") == "abc123key"


def test_get_key_returns_none_when_not_set(mock_keyring):
    """get_key should return None for a provider with no stored key."""
    result = keyring_manager.get_key("linkedin")
    assert result is None


def test_different_providers_stored_independently(mock_keyring):
    """Saving keys for two providers should not overwrite each other."""
    keyring_manager.save_key("indeed", "indeed-key-abc")
    keyring_manager.save_key("linkedin", "linkedin-key-xyz")
    assert keyring_manager.get_key("indeed") == "indeed-key-abc"
    assert keyring_manager.get_key("linkedin") == "linkedin-key-xyz"


# ── delete_key ────────────────────────────────────────────────────────────────

def test_delete_key_removes_stored_key(mock_keyring):
    """delete_key should remove the key so get_key returns None afterward."""
    keyring_manager.save_key("adzuna", "some-key")
    keyring_manager.delete_key("adzuna")
    assert keyring_manager.get_key("adzuna") is None


def test_delete_key_safe_when_key_not_set(mock_keyring):
    """delete_key should not raise if the key doesn't exist."""
    keyring_manager.delete_key("glassdoor")  # Should not raise


# ── has_key ───────────────────────────────────────────────────────────────────

def test_has_key_true_when_key_saved(mock_keyring):
    keyring_manager.save_key("anthropic", "sk-ant-testkey123456789")
    assert keyring_manager.has_key("anthropic") == True


def test_has_key_false_when_not_set(mock_keyring):
    assert keyring_manager.has_key("indeed") == False


def test_has_key_false_after_delete(mock_keyring):
    keyring_manager.save_key("usajobs", "some-key-value")
    keyring_manager.delete_key("usajobs")
    assert keyring_manager.has_key("usajobs") == False


# ── validate_key_format ───────────────────────────────────────────────────────

def test_validate_empty_key_fails():
    valid, msg = keyring_manager.validate_key_format("indeed", "")
    assert valid == False
    assert "empty" in msg.lower()


def test_validate_whitespace_only_fails():
    valid, msg = keyring_manager.validate_key_format("indeed", "   ")
    assert valid == False


def test_validate_too_short_fails():
    valid, msg = keyring_manager.validate_key_format("usajobs", "abc")
    assert valid == False
    assert "short" in msg.lower()


def test_validate_key_with_spaces_fails():
    valid, msg = keyring_manager.validate_key_format("indeed", "abc 123 def 456 ghi 789 jkl")
    assert valid == False
    assert "space" in msg.lower()


def test_validate_anthropic_wrong_prefix_fails():
    valid, msg = keyring_manager.validate_key_format("anthropic", "not-the-right-prefix-12345678")
    assert valid == False
    assert "sk-ant-" in msg


def test_validate_anthropic_correct_prefix_passes():
    valid, msg = keyring_manager.validate_key_format("anthropic", "sk-ant-validkeystring1234567890")
    assert valid == True
    assert msg == ""


def test_validate_reasonable_key_passes():
    valid, msg = keyring_manager.validate_key_format("indeed", "abcdef1234567890abcdef1234567890")
    assert valid == True
    assert msg == ""


def test_validate_service_name_format():
    """Verify the service name format used in keyring calls."""
    service = keyring_manager._service_name("indeed")
    assert service == "JobTrack/indeed"

    service = keyring_manager._service_name("anthropic")
    assert service == "JobTrack/anthropic"

