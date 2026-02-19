"""
integrations/usajobs_provider.py
=================================
USAJobs.gov API integration — always-on provider.

Registration (free): https://developer.usajobs.gov/APIRequest/
API Docs: https://developer.usajobs.gov/API-Reference/

USAJobs is the official US federal government job board.
Free registration, no approval process, no usage fees.
"""

from core.job_model import JobListing
from integrations.base_provider import BaseProvider, ProviderError


class UsajobsProvider(BaseProvider):
    """Fetches job listings from the USAJobs.gov API."""

    PROVIDER_ID = "usajobs"
    DISPLAY_NAME = "USAJobs (Federal)"
    REQUIRES_API_KEY = True
    IS_FREE = True

    BASE_URL = "https://data.usajobs.gov/api/search"

    def search(
        self,
        keywords: list[str],
        location: str,
        radius_miles: int,
        max_results: int = 50,
    ) -> list[JobListing]:
        """
        Search usajobs for jobs matching keywords near location.

        TODO: Implement API call
        1. Build request parameters/headers using self.api_key
        2. GET self.BASE_URL with params
        3. Raise ProviderError on non-200 response
        4. Parse response JSON and call self._normalize() on each result
        5. Return list of JobListing objects
        """
        raise NotImplementedError

    def validate_key(self) -> tuple[bool, str]:
        """
        Make a minimal usajobs API call to verify the key is active.

        TODO: Implement key validation
        - Use a lightweight endpoint or a minimal search query
        - Return (True, "Connected") on success
        - Return (False, "<error description>") on auth failure
        """
        raise NotImplementedError

    def _normalize(self, raw: dict) -> JobListing:
        """
        Convert a raw usajobs API response item into a JobListing.

        TODO: Map usajobs-specific field names to JobListing fields.
        Refer to the usajobs API docs for the response schema.
        Set provider="usajobs" and build job_id as "usajobs_<source_id>".
        Store the original raw dict in JobListing.raw for debugging.
        """
        raise NotImplementedError
