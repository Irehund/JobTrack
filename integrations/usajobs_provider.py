"""
integrations/usajobs_provider.py
==================================
USAJobs.gov API integration — always-on provider.

Registration (free): https://developer.usajobs.gov/APIRequest/
API Docs:            https://developer.usajobs.gov/API-Reference/

Authentication uses two headers:
    Authorization-Key: <your api key>
    User-Agent:        <your registered email address>

Both stored in keyring: "usajobs" (key) and "usajobs_email" (email).
"""

import logging
from typing import Optional
import requests

from core.job_model import JobListing
from integrations.base_provider import BaseProvider, ProviderError

logger = logging.getLogger("jobtrack.usajobs")

_WORK_SCHEDULE_MAP = {
    "FullTime": "full_time", "PartTime": "part_time",
    "Shift": "full_time", "Intermittent": "contract",
    "Job Sharing": "part_time", "Multiple Schedules": "full_time",
}
_PAY_INTERVAL_MAP = {"PA": "annual", "PH": "hourly", "BW": "annual", "WC": "annual"}
_ENTRY_KEYWORDS = {"entry", "junior", "gs-01", "gs-02", "gs-03", "gs-04", "gs-05", "gs-06", "gs-07"}
_SENIOR_KEYWORDS = {"senior", "lead", "principal", "gs-13", "gs-14", "gs-15", "ses"}


class UsajobsProvider(BaseProvider):
    """Fetches job listings from the USAJobs.gov API."""

    PROVIDER_ID  = "usajobs"
    DISPLAY_NAME = "USAJobs (Federal)"
    REQUIRES_API_KEY = True
    IS_FREE      = True
    BASE_URL     = "https://data.usajobs.gov/api/search"

    def __init__(self, api_key: str, user_email: str):
        super().__init__(api_key)
        self.user_email = user_email

    def _headers(self) -> dict:
        return {
            "Authorization-Key": self.api_key,
            "User-Agent": self.user_email,
            "Host": "data.usajobs.gov",
        }

    def search(
        self,
        keywords: list,
        location: str,
        radius_miles: int,
        max_results: int = 50,
    ) -> list:
        keyword_str = " ".join(keywords) if keywords else "analyst"
        params = {
            "Keyword": keyword_str,
            "LocationName": location,
            "Radius": str(radius_miles),
            "ResultsPerPage": str(min(max_results, 500)),
            "Fields": "min",
            "SortField": "OpenDate",
            "SortDirection": "Desc",
        }
        logger.debug(f"USAJobs search: keyword='{keyword_str}' location='{location}'")
        try:
            response = requests.get(self.BASE_URL, headers=self._headers(), params=params, timeout=15)
        except requests.RequestException as e:
            raise ProviderError(self.PROVIDER_ID, f"Network error: {e}")

        if response.status_code == 401:
            raise ProviderError(self.PROVIDER_ID, "Invalid API key or email.", 401)
        if response.status_code == 429:
            raise ProviderError(self.PROVIDER_ID, "Rate limit reached.", 429)
        if response.status_code != 200:
            raise ProviderError(self.PROVIDER_ID, "Unexpected response.", response.status_code)

        try:
            data = response.json()
        except ValueError as e:
            raise ProviderError(self.PROVIDER_ID, f"Invalid JSON: {e}")

        items = data.get("SearchResult", {}).get("SearchResultItems", [])
        logger.info(f"USAJobs: {len(items)} results for '{keyword_str}' near '{location}'")

        listings = []
        for item in items:
            try:
                listings.append(self._normalize(item))
            except Exception as e:
                logger.warning(f"USAJobs normalize error: {e}")
        return listings

    def validate_key(self) -> tuple:
        try:
            r = requests.get(
                self.BASE_URL,
                headers=self._headers(),
                params={"Keyword": "analyst", "ResultsPerPage": "1"},
                timeout=10,
            )
        except requests.RequestException as e:
            return False, f"Could not reach USAJobs — check your internet connection. ({e})"
        if r.status_code == 401:
            return False, "API key or email not recognized. Double-check your USAJobs developer portal credentials."
        if r.status_code == 200:
            return True, "Connected to USAJobs successfully."
        return False, f"Unexpected response (code {r.status_code}). Try again in a moment."

    def _normalize(self, raw: dict) -> JobListing:
        item = raw.get("MatchedObjectDescriptor", raw)

        source_id = item.get("PositionID", item.get("MatchedObjectId", "unknown"))
        job_id    = f"usajobs_{source_id}"
        title     = item.get("PositionTitle", "").strip()
        company   = item.get("OrganizationName", item.get("DepartmentName", "")).strip()

        locations = item.get("PositionLocation", [])
        primary   = locations[0] if locations else {}
        city      = primary.get("CityName", "").strip()
        state     = primary.get("CountrySubDivisionCode", "").strip()

        if city and state:
            location_str = f"{city}, {state}"
        elif city:
            location_str = city
        elif state:
            location_str = state
        else:
            location_str = primary.get("CountryCode", "US")

        if len(locations) > 1:
            location_str += f" (+{len(locations) - 1} locations)"

        try:
            latitude  = float(primary["Latitude"])  if primary.get("Latitude")  else None
            longitude = float(primary["Longitude"]) if primary.get("Longitude") else None
        except (TypeError, ValueError):
            latitude = longitude = None

        telework      = item.get("TeleworkSchedule", [{}])
        telework_code = telework[0].get("Code", "") if telework else ""
        title_lower   = title.lower()
        details       = item.get("UserArea", {}).get("Details", {})
        desc_lower    = details.get("JobSummary", "").lower()

        is_remote = "remote" in title_lower or "remote" in desc_lower or telework_code in ("01", "02")
        is_hybrid = "hybrid" in title_lower or "hybrid" in desc_lower or telework_code in ("03",)

        pay_range = item.get("PositionRemuneration", [{}])
        pay       = pay_range[0] if pay_range else {}
        try:
            salary_min = float(pay.get("MinimumRange", 0)) or None
            salary_max = float(pay.get("MaximumRange", 0)) or None
        except (TypeError, ValueError):
            salary_min = salary_max = None

        pay_code        = pay.get("RateIntervalCode", "PA")
        salary_interval = _PAY_INTERVAL_MAP.get(pay_code, "annual")
        if pay_code == "BW":
            if salary_min: salary_min *= 26
            if salary_max: salary_max *= 26

        schedule      = item.get("PositionSchedule", [{}])
        schedule_code = schedule[0].get("Code", "") if schedule else ""
        employment_type = _WORK_SCHEDULE_MAP.get(schedule_code, "full_time")

        grade_raw = item.get("JobGrade", [{}])
        grade_str = " ".join(f"gs-{g.get('Code','').lstrip('GS-').lstrip('gs-').zfill(2)}" for g in grade_raw).lower()
        combined  = f"{title_lower} {grade_str}"
        if any(kw in combined for kw in _SENIOR_KEYWORDS):
            experience_level = "senior"
        elif any(kw in combined for kw in _ENTRY_KEYWORDS):
            experience_level = "entry"
        else:
            experience_level = "mid"

        from core.utils import parse_iso_date
        date_posted  = parse_iso_date(item.get("PublicationStartDate", ""))
        closing_date = parse_iso_date(item.get("ApplicationCloseDate", ""))
        description  = details.get("JobSummary", "").strip()
        url          = item.get("PositionURI", "").strip()

        return JobListing(
            job_id=job_id, provider=self.PROVIDER_ID,
            title=title, company=company, location=location_str,
            city=city, state=state,
            latitude=latitude, longitude=longitude,
            is_remote=is_remote, is_hybrid=is_hybrid,
            url=url, description=description,
            date_posted=date_posted, closing_date=closing_date,
            salary_min=salary_min, salary_max=salary_max,
            salary_interval=salary_interval,
            employment_type=employment_type,
            experience_level=experience_level,
            raw=raw,
        )
