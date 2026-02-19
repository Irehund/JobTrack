"""
integrations/glassdoor_provider.py
===================================
Glassdoor API integration — opt-in provider.

Developer portal: https://www.glassdoor.com/developer/index.htm
"""

from core.job_model import JobListing
from integrations.base_provider import BaseProvider, ProviderError


class GlassdoorProvider(BaseProvider):
    """Fetches job listings from the Glassdoor API."""

    PROVIDER_ID = "glassdoor"
    DISPLAY_NAME = "Glassdoor"
    REQUIRES_API_KEY = True
    IS_FREE = False

    BASE_URL = "https://api.glassdoor.com/api/api.htm"

    def search(
        self,
        keywords: list[str],
        location: str,
        radius_miles: int,
        max_results: int = 50,
    ) -> list[JobListing]:
        """
        Search glassdoor for jobs matching keywords near location.

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
        Make a minimal glassdoor API call to verify the key is active.

        TODO: Implement key validation
        - Use a lightweight endpoint or a minimal search query
        - Return (True, "Connected") on success
        - Return (False, "<error description>") on auth failure
        """
        raise NotImplementedError

    def _normalize(self, raw: dict) -> JobListing:
        """
        Convert a raw glassdoor API response item into a JobListing.

        TODO: Map glassdoor-specific field names to JobListing fields.
        Refer to the glassdoor API docs for the response schema.
        Set provider="glassdoor" and build job_id as "glassdoor_<source_id>".
        Store the original raw dict in JobListing.raw for debugging.
        """
        raise NotImplementedError
