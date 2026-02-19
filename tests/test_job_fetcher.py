"""
tests/test_job_fetcher.py
===========================
Tests for core/job_fetcher.py.
Uses mocked provider responses to test deduplication and retry logic.
"""
import pytest
from unittest.mock import MagicMock, patch
from core import job_fetcher
from core.job_model import JobListing


def test_deduplication_removes_same_job_from_two_providers():
    """The same job appearing in two provider results should produce one listing."""
    # TODO: Create two JobListing objects with same dedup_key(), call _deduplicate()
    # Assert result has length 1
    raise NotImplementedError


def test_retry_logic_calls_provider_up_to_max_retries(monkeypatch):
    """A failing provider should be retried MAX_RETRIES times then skipped."""
    # TODO: Mock a provider that always raises ProviderError
    # Run fetch_jobs(), assert provider was called exactly MAX_RETRIES times
    raise NotImplementedError


def test_one_failing_provider_doesnt_stop_others(monkeypatch):
    """If one provider fails all retries, other providers still return results."""
    # TODO: Mock one failing provider and one successful provider
    # Assert results from the successful provider are returned
    raise NotImplementedError
