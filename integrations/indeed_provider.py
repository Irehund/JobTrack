"""
integrations/indeed_provider.py
================================
Indeed API integration — opt-in provider.

Developer portal: https://developer.indeed.com/

Note: Indeed's Publisher API has limited availability.
Users may need to apply for access separately.
"""

from core.job_model import JobListing
from integrations.base_provider import BaseProvider, ProviderError


class IndeedProvider(BaseProvider):
    """Fetches job listings from the Indeed API."""

    PROVIDER_ID = "indeed"
    DISPLAY_NAME = "Indeed"
    REQUIRES_API_KEY = True
    IS_FREE = False

    BASE_URL = "https://api.indeed.com/ads/apisearch"

    def search(
        self,
        keywords: list[str],
        location: str,
        radius_miles: int,
        max_results: int = 50,
    ) -> list[JobListing]:
        """
        Search indeed for jobs matching keywords near location.

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
        Make a minimal indeed API call to verify the key is active.

        TODO: Implement key validation
        - Use a lightweight endpoint or a minimal search query
        - Return (True, "Connected") on success
        - Return (False, "<error description>") on auth failure
        """
        raise NotImplementedError

    def _normalize(self, raw: dict) -> JobListing:
        """
        Convert a raw indeed API response item into a JobListing.

        TODO: Map indeed-specific field names to JobListing fields.
        Refer to the indeed API docs for the response schema.
        Set provider="indeed" and build job_id as "indeed_<source_id>".
        Store the original raw dict in JobListing.raw for debugging.
        """
        raise NotImplementedError
