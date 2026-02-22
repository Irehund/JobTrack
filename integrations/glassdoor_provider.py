"""
integrations/glassdoor_provider.py
====================================
Glassdoor job search integration — opt-in provider.

Glassdoor's public API was deprecated in 2024 for most uses.
We route through the JSearch RapidAPI endpoint (same infrastructure as
Indeed/LinkedIn providers) filtering for Glassdoor-sourced listings.

API: RapidAPI JSearch
Key: stored in keyring as "glassdoor"
"""

import logging
import requests
from datetime import datetime

from core.job_model import JobListing
from integrations.base_provider import BaseProvider, ProviderError

logger = logging.getLogger("jobtrack.glassdoor")

BASE_URL      = "https://jsearch.p.rapidapi.com/search"
RAPIDAPI_HOST = "jsearch.p.rapidapi.com"
REQUEST_TIMEOUT = 15


class GlassdoorProvider(BaseProvider):
    """Fetches job listings sourced via Glassdoor through JSearch RapidAPI."""

    PROVIDER_ID  = "glassdoor"
    DISPLAY_NAME = "Glassdoor"
    REQUIRES_API_KEY = True
    IS_FREE      = False

    def search(
        self,
        keywords: list,
        location: str,
        radius_miles: int,
        max_results: int = 50,
    ) -> list:
        keyword_str = " ".join(keywords) if keywords else "analyst"
        headers = {"X-RapidAPI-Key": self.api_key, "X-RapidAPI-Host": RAPIDAPI_HOST}
        params  = {
            "query":       f"{keyword_str} {location}",
            "page":        "1",
            "num_pages":   "1",
            "date_posted": "month",
        }

        try:
            response = requests.get(BASE_URL, headers=headers, params=params,
                                    timeout=REQUEST_TIMEOUT)
        except requests.RequestException as e:
            raise ProviderError(self.PROVIDER_ID, f"Network error: {e}")

        if response.status_code == 401:
            raise ProviderError(self.PROVIDER_ID, "Invalid RapidAPI key.", 401)
        if response.status_code == 429:
            raise ProviderError(self.PROVIDER_ID, "Rate limit reached.", 429)
        if not response.ok:
            raise ProviderError(self.PROVIDER_ID, f"HTTP {response.status_code}",
                                response.status_code)

        data = response.json()
        jobs = [j for j in data.get("data", [])
                if "glassdoor" in j.get("job_apply_link", "").lower()
                or "glassdoor" in j.get("job_publisher", "").lower()]
        if not jobs:
            jobs = data.get("data", [])

        logger.info(f"Glassdoor: {len(jobs)} results")
        results = []
        for item in jobs[:max_results]:
            try:
                results.append(self._normalize(item))
            except Exception as e:
                logger.warning(f"Glassdoor: skipping — {e}")
        return results

    def validate_key(self) -> tuple:
        try:
            headers = {"X-RapidAPI-Key": self.api_key, "X-RapidAPI-Host": RAPIDAPI_HOST}
            r = requests.get(BASE_URL, headers=headers,
                             params={"query":"analyst","page":"1","num_pages":"1"},
                             timeout=REQUEST_TIMEOUT)
            if r.status_code == 401: return (False, "Invalid key.")
            if r.ok:                 return (True,  "Connected to Glassdoor via RapidAPI.")
            return (False, f"HTTP {r.status_code}")
        except requests.RequestException as e:
            return (False, f"Network error: {e}")

    def _normalize(self, raw: dict) -> JobListing:
        job_id   = f"glassdoor_{raw.get('job_id','')[:40]}"
        title    = raw.get("job_title", "")
        company  = raw.get("employer_name", "")
        city     = raw.get("job_city", "")
        state    = raw.get("job_state", "")
        location = f"{city}, {state}".strip(", ")
        url      = raw.get("job_apply_link") or raw.get("job_google_link", "")
        desc     = raw.get("job_description", "")
        is_remote = bool(raw.get("job_is_remote", False))

        sal_min    = raw.get("job_min_salary")
        sal_max    = raw.get("job_max_salary")
        sal_period = raw.get("job_salary_period", "").lower()
        interval   = "annual" if "year" in sal_period or "annual" in sal_period else \
                     "hourly" if "hour" in sal_period else ""

        date_posted = None
        posted_str  = raw.get("job_posted_at_datetime_utc", "")
        if posted_str:
            try:
                date_posted = datetime.fromisoformat(posted_str.replace("Z", "+00:00"))
            except ValueError:
                pass

        title_lower = title.lower()
        exp = ("senior" if any(k in title_lower for k in ("senior","sr.","lead","principal"))
               else "entry" if any(k in title_lower for k in ("junior","jr.","entry","associate"))
               else "")

        return JobListing(
            job_id=job_id, provider="glassdoor",
            title=title, company=company, location=location,
            city=city, state=state, url=url,
            description=desc[:2000], is_remote=is_remote, is_hybrid=False,
            salary_min=float(sal_min) if sal_min else None,
            salary_max=float(sal_max) if sal_max else None,
            salary_interval=interval, date_posted=date_posted,
            experience_level=exp, raw=raw,
        )
