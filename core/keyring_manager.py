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


def _service_name(provider: str) -> str:
    """Return the keyring service name for a given provider."""
    return f"{APP_NAME}/{provider}"


def save_key(provider: str, api_key: str) -> None:
    """
    Save an API key to the OS credential store.

    Args:
        provider: Provider name, e.g. "indeed"
        api_key:  The API key string to store securely
    """
    # TODO: Call keyring.set_password(_service_name(provider), provider, api_key)
    raise NotImplementedError


def get_key(provider: str) -> Optional[str]:
    """
    Retrieve an API key from the OS credential store.

    Returns:
        The stored API key, or None if not set.
    """
    # TODO: Call keyring.get_password(_service_name(provider), provider)
    raise NotImplementedError


def delete_key(provider: str) -> None:
    """
    Remove an API key from the OS credential store.
    Safe to call even if the key does not exist.
    """
    # TODO: Call keyring.delete_password with error handling for missing keys
    raise NotImplementedError


def has_key(provider: str) -> bool:
    """Return True if a key is stored for the given provider."""
    # TODO: Return True if get_key(provider) is not None
    raise NotImplementedError


def validate_key_format(provider: str, api_key: str) -> tuple[bool, str]:
    """
    Perform basic format validation on an API key before saving it.
    Does NOT make a network call — just checks length, prefix, etc.

    Returns:
        (is_valid: bool, error_message: str)
        error_message is empty string if valid.
    """
    # TODO: Add provider-specific format checks
    # e.g. USAJobs keys are typically 32-char hex strings
    # Return (False, "Key appears too short") for obvious mistakes
    raise NotImplementedError
