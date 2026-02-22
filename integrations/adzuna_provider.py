"""
integrations/adzuna_provider.py
================================
Adzuna API integration — opt-in provider. Free tier available.

Registration: https://developer.adzuna.com/
API Docs:     https://api.adzuna.com/docs/

Authentication: app_id + app_key passed as query params.
Store combined as "app_id:app_key" in keyring under "adzuna".
Free tier: 250 requests/month, 50 results per call.
"""

import logging
import requests
from datetime import datetime

from core.job_model import JobListing
from integrations.base_provider import BaseProvider, ProviderError

logger = logging.getLogger("jobtrack.adzuna")

BASE_URL        = "https://api.adzuna.com/v1/api/jobs/us/search/1"
VALIDATE_URL    = "https://api.adzuna.com/v1/api/jobs/us/search/1"
REQUEST_TIMEOUT = 15


class AdzunaProvider(BaseProvider):
    """
    Fetches job listings from the Adzuna API.

    The api_key stored in keyring should be "app_id:app_key" format,
    e.g. "a1b2c3d4:e5f6g7h8i9j0k1l2".
    """

    PROVIDER_ID  = "adzuna"
    DISPLAY_NAME = "Adzuna"
    REQUIRES_API_KEY = True
    IS_FREE      = True

    def _parse_creds(self) -> tuple:
        """Split "app_id:app_key" into (app_id, app_key)."""
        if ":" in self.api_key:
            parts = self.api_key.split(":", 1)
            return parts[0].strip(), parts[1].strip()
        return self.api_key, self.api_key   # Fallback — will likely 401

    def search(
        self,
        keywords: list,
        location: str,
        radius_miles: int,
        max_results: int = 50,
    ) -> list:
        app_id, app_key = self._parse_creds()
        keyword_str = " ".join(keywords) if keywords else "analyst"
        city = location.split(",")[0].strip()

        params = {
            "app_id":       app_id,
            "app_key":      app_key,
            "results_per_page": min(max_results, 50),
            "what":         keyword_str,
            "where":        city,
            "distance":     radius_miles,
            "sort_by":      "date",
            "full_time":    1,
            "content-type": "application/json",
        }

        try:
            response = requests.get(BASE_URL, params=params, timeout=REQUEST_TIMEOUT)
        except requests.RequestException as e:
            raise ProviderError(self.PROVIDER_ID, f"Network error: {e}")

        if response.status_code == 401:
            raise ProviderError(self.PROVIDER_ID, "Invalid Adzuna app_id or app_key.", 401)
        if response.status_code == 429:
            raise ProviderError(self.PROVIDER_ID, "Rate limit reached.", 429)
        if not response.ok:
            raise ProviderError(self.PROVIDER_ID, f"HTTP {response.status_code}",
                                response.status_code)

        data    = response.json()
        results_raw = data.get("results", [])
        logger.info(f"Adzuna: {len(results_raw)} raw results")

        results = []
        for item in results_raw[:max_results]:
            try:
                results.append(self._normalize(item))
            except Exception as e:
                logger.warning(f"Adzuna: skipping result — {e}")
        return results

    def validate_key(self) -> tuple:
        app_id, app_key = self._parse_creds()
        try:
            r = requests.get(
                VALIDATE_URL,
                params={"app_id": app_id, "app_key": app_key,
                        "results_per_page": 1, "what": "analyst"},
                timeout=REQUEST_TIMEOUT,
            )
            if r.status_code == 401: return (False, "Invalid Adzuna credentials.")
            if r.ok:                 return (True,  "Connected to Adzuna.")
            return (False, f"HTTP {r.status_code}")
        except requests.RequestException as e:
            return (False, f"Network error: {e}")

    def _normalize(self, raw: dict) -> JobListing:
        job_id   = f"adzuna_{raw.get('id', '')}"
        title    = raw.get("title", "")
        company  = raw.get("company", {}).get("display_name", "")
        loc_data = raw.get("location", {})
        loc_areas = loc_data.get("area", [])
        city     = loc_areas[-1] if len(loc_areas) >= 1 else ""
        state    = loc_areas[-2] if len(loc_areas) >= 2 else ""
        location = loc_data.get("display_name", f"{city}, {state}".strip(", "))
        url      = raw.get("redirect_url", "")
        desc     = raw.get("description", "")

        # Salary
        sal_min  = raw.get("salary_min")
        sal_max  = raw.get("salary_max")
        interval = "annual"   # Adzuna always returns annual

        # Date
        created  = raw.get("created", "")
        date_posted = None
        if created:
            try:
                date_posted = datetime.fromisoformat(created.replace("Z", "+00:00"))
            except ValueError:
                pass

        # Experience from title
        title_lower = title.lower()
        exp = ("senior" if any(k in title_lower for k in ("senior","sr.","lead","principal"))
               else "entry" if any(k in title_lower for k in ("junior","jr.","entry","associate","i ","level i"))
               else "mid" if any(k in title_lower for k in ("mid","ii","iii","level ii"))
               else "")

        # Remote detection from category/description
        category = raw.get("category", {}).get("label", "").lower()
        is_remote = "remote" in category or "remote" in desc.lower()[:200]

        return JobListing(
            job_id=job_id, provider="adzuna",
            title=title, company=company, location=location,
            city=city, state=state, url=url,
            description=desc[:2000], is_remote=is_remote, is_hybrid=False,
            salary_min=float(sal_min) if sal_min else None,
            salary_max=float(sal_max) if sal_max else None,
            salary_interval=interval, date_posted=date_posted,
            experience_level=exp, raw=raw,
        )
