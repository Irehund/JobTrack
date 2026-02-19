"""
integrations/base_provider.py
================================
Abstract base class that every job provider module must implement.
Enforces a consistent interface so job_fetcher.py can call all
providers identically without knowing their internal details.

To add a new provider:
    1. Create integrations/myprovider_provider.py
    2. Subclass BaseProvider
    3. Implement all abstract methods
    4. Add to job_fetcher._get_enabled_providers()
    5. Add wizard screenshots to assets/wizard_screens/myprovider/
"""

from abc import ABC, abstractmethod
from core.job_model import JobListing


class BaseProvider(ABC):
    """Abstract base for all job board provider integrations."""

    # Must be set in each subclass — used for display names and config keys
    PROVIDER_ID: str = ""        # e.g. "indeed"
    DISPLAY_NAME: str = ""       # e.g. "Indeed"
    REQUIRES_API_KEY: bool = True
    IS_FREE: bool = False        # True if the free tier is sufficient for basic search

    def __init__(self, api_key: str):
        """
        Args:
            api_key: Retrieved from keyring_manager.get_key(PROVIDER_ID)
        """
        self.api_key = api_key

    @abstractmethod
    def search(
        self,
        keywords: list[str],
        location: str,
        radius_miles: int,
        max_results: int = 50,
    ) -> list[JobListing]:
        """
        Search for jobs and return a list of normalized JobListing objects.

        Args:
            keywords:     List of job title/keyword search terms
            location:     Location string, e.g. "Dallas, TX" or zip code
            radius_miles: Search radius from location
            max_results:  Maximum number of results to return

        Returns:
            List of JobListing objects. Empty list on no results.

        Raises:
            ProviderError: On API errors (rate limit, auth failure, etc.)
        """
        ...

    @abstractmethod
    def validate_key(self) -> tuple[bool, str]:
        """
        Make a minimal API call to verify the stored key is valid.
        Used during wizard setup to give immediate feedback.

        Returns:
            (is_valid: bool, message: str)
            message describes the error if is_valid is False.
        """
        ...

    def _normalize(self, raw: dict) -> JobListing:
        """
        Convert a raw API response dict into a JobListing.
        Implement in each subclass — schema varies by provider.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement _normalize()"
        )


class ProviderError(Exception):
    """
    Raised by provider.search() when an API call fails.
    job_fetcher.py catches this to trigger the retry logic.
    """
    def __init__(self, provider_id: str, message: str, status_code: int = 0):
        self.provider_id = provider_id
        self.status_code = status_code
        super().__init__(f"[{provider_id}] {message} (HTTP {status_code})")
