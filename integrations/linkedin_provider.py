"""
integrations/linkedin_provider.py
==================================
LinkedIn Jobs API integration — opt-in provider.

Developer portal: https://www.linkedin.com/developers/

Note: LinkedIn API access requires a developer application
and may require business verification for job search endpoints.

UI Note: The wizard shows a dedicated reminder screen for LinkedIn
users to update their profile before searching.
"""

from core.job_model import JobListing
from integrations.base_provider import BaseProvider, ProviderError


class LinkedinProvider(BaseProvider):
    """Fetches job listings from the LinkedIn Jobs API."""

    PROVIDER_ID = "linkedin"
    DISPLAY_NAME = "LinkedIn"
    REQUIRES_API_KEY = True
    IS_FREE = False

    BASE_URL = "https://api.linkedin.com/v2/jobSearch"

    def search(
        self,
        keywords: list[str],
        location: str,
        radius_miles: int,
        max_results: int = 50,
    ) -> list[JobListing]:
        """
        Search linkedin for jobs matching keywords near location.

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
        Make a minimal linkedin API call to verify the key is active.

        TODO: Implement key validation
        - Use a lightweight endpoint or a minimal search query
        - Return (True, "Connected") on success
        - Return (False, "<error description>") on auth failure
        """
        raise NotImplementedError

    def _normalize(self, raw: dict) -> JobListing:
        """
        Convert a raw linkedin API response item into a JobListing.

        TODO: Map linkedin-specific field names to JobListing fields.
        Refer to the linkedin API docs for the response schema.
        Set provider="linkedin" and build job_id as "linkedin_<source_id>".
        Store the original raw dict in JobListing.raw for debugging.
        """
        raise NotImplementedError
