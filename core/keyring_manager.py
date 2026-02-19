"""
core/keyring_manager.py
========================
Manages secure storage and retrieval of API keys using the OS-level
credential store via the keyring library.

On Windows this uses Windows Credential Manager.
On macOS this uses the macOS Keychain.

Keys are never written to config.json or any plain text file.
The user enters a key once and never needs to see it again.

Service naming convention:
    "JobTrack/<provider_name>"
    e.g. "JobTrack/indeed", "JobTrack/usajobs"
"""

import keyring
import keyring.errors
from typing import Optional

APP_NAME = "JobTrack"

# All provider keys we manage
PROVIDER_KEYS = [
    "usajobs",
    "indeed",
    "linkedin",
    "glassdoor",
    "adzuna",
    "anthropic",          # Claude AI assistant key
    "openrouteservice",   # Commute calculation key
]

# Minimum key lengths for basic format validation
_MIN_KEY_LENGTH = {
    "usajobs": 20,
    "indeed": 20,
    "linkedin": 20,
    "glassdoor": 20,
    "adzuna": 20,
    "anthropic": 30,      # Anthropic keys start with "sk-ant-"
    "openrouteservice": 20,
}

# Known key prefixes for providers that use them
_KEY_PREFIXES = {
    "anthropic": "sk-ant-",
}


def _service_name(provider: str) -> str:
    """Return the keyring service name for a given provider."""
    return f"{APP_NAME}/{provider}"


def save_key(provider: str, api_key: str) -> None:
    """
    Save an API key to the OS credential store.

    Args:
        provider: Provider name, e.g. "indeed"
        api_key:  The API key string to store securely

    Raises:
        keyring.errors.KeyringError: If the OS credential store is unavailable.
    """
    api_key = api_key.strip()
    keyring.set_password(_service_name(provider), provider, api_key)


def get_key(provider: str) -> Optional[str]:
    """
    Retrieve an API key from the OS credential store.

    Returns:
        The stored API key, or None if not set.
    """
    try:
        return keyring.get_password(_service_name(provider), provider)
    except keyring.errors.KeyringError:
        return None


def delete_key(provider: str) -> None:
    """
    Remove an API key from the OS credential store.
    Safe to call even if the key does not exist.
    """
    try:
        keyring.delete_password(_service_name(provider), provider)
    except keyring.errors.PasswordDeleteError:
        pass  # Key didn't exist — that's fine
    except keyring.errors.KeyringError:
        pass  # Credential store unavailable — silently ignore


def has_key(provider: str) -> bool:
    """Return True if a non-empty key is stored for the given provider."""
    key = get_key(provider)
    return key is not None and len(key.strip()) > 0


def validate_key_format(provider: str, api_key: str) -> tuple[bool, str]:
    """
    Perform basic format validation on an API key before saving it.
    Does NOT make a network call — just checks length, prefix, etc.
    Live validation against the actual API happens in the wizard's
    'Verify Key' button.

    Returns:
        (is_valid: bool, error_message: str)
        error_message is empty string if valid.
    """
    api_key = api_key.strip()

    if not api_key:
        return False, "Key cannot be empty."

    # Check minimum length
    min_len = _MIN_KEY_LENGTH.get(provider, 10)
    if len(api_key) < min_len:
        return False, f"Key looks too short (expected at least {min_len} characters)."

    # Check for spaces in the middle (common copy-paste mistake)
    if " " in api_key:
        return False, "Key should not contain spaces. Check for extra characters when copying."

    # Check known prefixes
    expected_prefix = _KEY_PREFIXES.get(provider)
    if expected_prefix and not api_key.startswith(expected_prefix):
        return False, f"This key doesn't look right — {provider.capitalize()} keys usually start with '{expected_prefix}'."

    return True, ""
