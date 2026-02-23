"""
integrations/indeed_provider.py
================================
Indeed API integration — opt-in provider.

Indeed's "Publisher API" is legacy/restricted. The modern path is their
Indeed Hiring Platform / Job Posting API. For search, Indeed exposes a
RapidAPI-hosted endpoint that many developers use.

We implement against the JSearch API (RapidAPI) which aggregates Indeed
+ other boards, using the Indeed-specific endpoint when possible.

API used: RapidAPI JSearch (returns Indeed results)
Endpoint: https://jsearch.p.rapidapi.com/search
Key:      RapidAPI key stored in keyring as "indeed"
"""

import logging
import requests
from datetime import datetime, timezone
from typing import Optional

from core.job_model import JobListing
from integrations.base_provider import BaseProvider, ProviderError

logger = logging.getLogger("jobtrack.indeed")

BASE_URL      = "https://jsearch.p.rapidapi.com/search"
RAPIDAPI_HOST = "jsearch.p.rapidapi.com"
REQUEST_TIMEOUT = 15


def _safe_str(value, default="") -> str:
    """Return a string from value, falling back to default if None."""
    if value is None:
        return default
    return str(value).strip()


class IndeedProvider(BaseProvider):
    """Fetches job listings from Indeed via the JSearch RapidAPI."""

    PROVIDER_ID  = "indeed"
    DISPLAY_NAME = "Indeed"
    REQUIRES_API_KEY = True
    IS_FREE      = False   # RapidAPI free tier: 500 req/month

    def search(
        self,
        keywords: list,
        location: str,
        radius_miles: int,
        max_results: int = 50,
    ) -> list:
        keyword_str = " ".join(keywords) if keywords else "analyst"

        params = {
            "query":            f"{keyword_str} {location}",
            "page":             "1",
            "num_pages":        "1",
            "date_posted":      "month",
            "employment_types": "FULLTIME,CONTRACTOR",
        }

        headers = {
            "X-RapidAPI-Key":  self.api_key,
            "X-RapidAPI-Host": RAPIDAPI_HOST,
        }

        try:
            response = requests.get(
                BASE_URL, headers=headers, params=params,
                timeout=REQUEST_TIMEOUT)
        except requests.RequestException as e:
            raise ProviderError(self.PROVIDER_ID, f"Network error: {e}")

        if response.status_code == 401:
            raise ProviderError(self.PROVIDER_ID, "Invalid RapidAPI key.", 401)
        if response.status_code == 403:
            raise ProviderError(self.PROVIDER_ID, "Not subscribed to JSearch API on RapidAPI.", 403)
        if response.status_code == 429:
            raise ProviderError(self.PROVIDER_ID, "Rate limit reached.", 429)
        if not response.ok:
            raise ProviderError(
                self.PROVIDER_ID, f"HTTP {response.status_code}", response.status_code)

        data = response.json()
        jobs = data.get("data", [])
        logger.info(f"Indeed: received {len(jobs)} raw results")

        results = []
        for item in jobs[:max_results]:
            try:
                results.append(self._normalize(item))
            except Exception as e:
                logger.warning(f"Indeed: skipping malformed result — {e}")
        return results

    def validate_key(self) -> tuple:
        try:
            headers = {
                "X-RapidAPI-Key":  self.api_key,
                "X-RapidAPI-Host": RAPIDAPI_HOST,
            }
            response = requests.get(
                BASE_URL,
                headers=headers,
                params={"query": "analyst", "page": "1", "num_pages": "1"},
                timeout=REQUEST_TIMEOUT,
            )
            if response.status_code == 401:
                return False, "Invalid RapidAPI key (401)."
            if response.status_code == 403:
                return False, "Not subscribed to JSearch on RapidAPI. Visit rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch to subscribe."
            if response.status_code == 429:
                return True, "Key valid — rate limited (429). Try later."
            if response.ok:
                return True, "Connected to Indeed via RapidAPI."
            return False, f"Unexpected status {response.status_code}"
        except requests.RequestException as e:
            return False, f"Network error: {e}"

    def _normalize(self, raw: dict) -> JobListing:
        job_id  = f"indeed_{_safe_str(raw.get('job_id') or raw.get('job_apply_link', ''))[:40]}"
        title   = _safe_str(raw.get("job_title"))
        company = _safe_str(raw.get("employer_name"))
        city    = _safe_str(raw.get("job_city"))
        state   = _safe_str(raw.get("job_state"))
        location = f"{city}, {state}".strip(", ") if city or state else _safe_str(raw.get("job_country"))
        url     = _safe_str(raw.get("job_apply_link") or raw.get("job_google_link"))
        desc    = _safe_str(raw.get("job_description"))
        is_remote = bool(raw.get("job_is_remote", False))

        # Salary
        salary_min = raw.get("job_min_salary")
        salary_max = raw.get("job_max_salary")
        sal_period = _safe_str(raw.get("job_salary_period")).lower()
        interval   = "annual" if "year" in sal_period or "annual" in sal_period else \
                     "hourly" if "hour" in sal_period else ""

        # Date
        posted_str  = _safe_str(raw.get("job_posted_at_datetime_utc"))
        date_posted = None
        if posted_str:
            try:
                date_posted = datetime.fromisoformat(posted_str.replace("Z", "+00:00"))
            except ValueError:
                pass

        # Experience level from title
        title_lower = title.lower()
        if any(k in title_lower for k in ("senior", "sr.", "lead", "principal")):
            exp = "senior"
        elif any(k in title_lower for k in ("junior", "jr.", "entry", "associate", "i ")):
            exp = "entry"
        elif "mid" in title_lower or "ii" in title_lower:
            exp = "mid"
        else:
            exp = ""

        return JobListing(
            job_id=job_id, provider="indeed",
            title=title, company=company, location=location,
            city=city, state=state, url=url,
            description=desc[:2000],
            is_remote=is_remote, is_hybrid=False,
            salary_min=float(salary_min) if salary_min else None,
            salary_max=float(salary_max) if salary_max else None,
            salary_interval=interval,
            date_posted=date_posted,
            experience_level=exp,
            raw=raw,
        )
