"""
integrations/adzuna_provider.py
================================
Adzuna API integration — opt-in provider.

Registration (free tier available): https://developer.adzuna.com/
API Docs: https://api.adzuna.com/docs/
"""

from core.job_model import JobListing
from integrations.base_provider import BaseProvider, ProviderError


class AdzunaProvider(BaseProvider):
    """Fetches job listings from the Adzuna API."""

    PROVIDER_ID = "adzuna"
    DISPLAY_NAME = "Adzuna"
    REQUIRES_API_KEY = True
    IS_FREE = True

    BASE_URL = "https://api.adzuna.com/v1/api/jobs"

    def search(
        self,
        keywords: list[str],
        location: str,
        radius_miles: int,
        max_results: int = 50,
    ) -> list[JobListing]:
        """
        Search adzuna for jobs matching keywords near location.

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
        Make a minimal adzuna API call to verify the key is active.

        TODO: Implement key validation
        - Use a lightweight endpoint or a minimal search query
        - Return (True, "Connected") on success
        - Return (False, "<error description>") on auth failure
        """
        raise NotImplementedError

    def _normalize(self, raw: dict) -> JobListing:
        """
        Convert a raw adzuna API response item into a JobListing.

        TODO: Map adzuna-specific field names to JobListing fields.
        Refer to the adzuna API docs for the response schema.
        Set provider="adzuna" and build job_id as "adzuna_<source_id>".
        Store the original raw dict in JobListing.raw for debugging.
        """
        raise NotImplementedError
