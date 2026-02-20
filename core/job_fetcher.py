"""
core/job_fetcher.py
====================
Orchestrates job searches across all enabled provider modules.
Runs providers in parallel using threads to keep the UI responsive.
Deduplicates results using JobListing.dedup_key().
Reports progress back to the UI via a callback.

Error/retry behavior per provider:
    - Attempt 1: Run normally
    - Attempt 2+: On failure, notify UI and wait RETRY_DELAY_SECONDS
    - After MAX_RETRIES: Skip provider, continue with remaining
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Optional

from core.job_model import JobListing
from integrations.base_provider import BaseProvider, ProviderError

logger = logging.getLogger("jobtrack.fetcher")

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2


class FetchProgress:
    """
    Passed to the progress callback during a search.
    UI uses this to update the progress bar and status label.
    """

    def __init__(self, total_providers: int):
        self.total_providers = total_providers
        self.completed_providers = 0
        self.current_provider: str = ""
        self.retry_attempt: int = 0
        self.failed_providers: list = []
        self.total_results: int = 0

    @property
    def percent_complete(self) -> float:
        if self.total_providers == 0:
            return 100.0
        return (self.completed_providers / self.total_providers) * 100

    @property
    def status_message(self) -> str:
        if self.retry_attempt > 0:
            return f"Retrying {self.current_provider} — Attempt {self.retry_attempt} of {MAX_RETRIES}"
        if self.current_provider:
            return f"Searching {self.current_provider}..."
        return "Searching..."


ProgressCallback = Callable[[FetchProgress], None]


def fetch_jobs(
    config: dict,
    progress_callback: Optional[ProgressCallback] = None,
) -> list:
    """
    Run a job search across all enabled providers in parallel.

    Returns:
        Deduplicated list of JobListing objects sorted by date_posted desc.
    """
    providers = _get_enabled_providers(config)
    if not providers:
        logger.warning("fetch_jobs: No enabled providers found.")
        return []

    progress = FetchProgress(total_providers=len(providers))
    all_results = []

    prefs    = config.get("job_preferences", {})
    keywords = prefs.get("keywords", [])
    location = config.get("location", {})
    city     = location.get("city", "")
    state    = location.get("state", "")
    loc_str  = f"{city}, {state}".strip(", ") or location.get("zip", "Remote")
    radius   = config.get("search_radius_miles", 50)

    def _fetch_one(provider: BaseProvider) -> list:
        name = provider.DISPLAY_NAME
        last_error = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                progress.current_provider = name
                progress.retry_attempt = attempt if attempt > 1 else 0
                if progress_callback:
                    progress_callback(progress)

                results = provider.search(
                    keywords=keywords,
                    location=loc_str,
                    radius_miles=radius,
                )
                logger.info(f"{name}: {len(results)} results")
                return results

            except ProviderError as e:
                last_error = e
                if e.status_code in (401, 403):
                    logger.warning(f"{name}: Auth error, skipping retries")
                    break
                logger.warning(f"{name}: Attempt {attempt}/{MAX_RETRIES} — {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY_SECONDS)

            except Exception as e:
                last_error = e
                logger.warning(f"{name}: Attempt {attempt} error — {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY_SECONDS)

        logger.error(f"{name}: All attempts failed. Last: {last_error}")
        return []

    with ThreadPoolExecutor(max_workers=min(len(providers), 5)) as executor:
        future_to_provider = {executor.submit(_fetch_one, p): p for p in providers}
        for future in as_completed(future_to_provider):
            provider = future_to_provider[future]
            try:
                results = future.result()
                all_results.extend(results)
            except Exception as e:
                logger.error(f"{provider.DISPLAY_NAME}: Unhandled — {e}")
                progress.failed_providers.append(provider.DISPLAY_NAME)

            progress.completed_providers += 1
            progress.current_provider = provider.DISPLAY_NAME
            progress.retry_attempt = 0
            progress.total_results = len(all_results)
            if progress_callback:
                progress_callback(progress)

    deduped = _deduplicate(all_results)
    logger.info(f"fetch_jobs: {len(all_results)} raw → {len(deduped)} after dedup")

    deduped.sort(
        key=lambda j: j.date_posted.isoformat() if j.date_posted else "",
        reverse=True,
    )
    return deduped


def fetch_all(config: dict) -> list:
    """Alias for fetch_jobs with no progress callback. Used by UI panels."""
    return fetch_jobs(config)


def _deduplicate(listings: list) -> list:
    """
    Remove duplicate listings using JobListing.dedup_key().
    When duplicates exist, keep the listing with the highest quality score.
    """
    seen: dict = {}
    for listing in listings:
        key = listing.dedup_key()
        if key not in seen:
            seen[key] = listing
        elif _quality_score(listing) > _quality_score(seen[key]):
            seen[key] = listing
    return list(seen.values())


def _quality_score(listing) -> int:
    """
    Score a listing by data completeness for dedup preference.
    Description is worth the most — it's the richest signal of a complete record.
    A description alone (5 pts) beats both salary fields combined (2+2=4 pts).
    """
    score = 0
    if listing.description:              score += 5
    if listing.salary_min is not None:   score += 2
    if listing.salary_max is not None:   score += 2
    if listing.closing_date is not None: score += 1
    if listing.latitude is not None:     score += 1
    return score


def _get_enabled_providers(config: dict) -> list:
    """Instantiate and return all enabled provider objects."""
    from core import keyring_manager
    providers = []

    # USAJobs — always on
    try:
        from integrations.usajobs_provider import UsajobsProvider
        api_key = keyring_manager.get_key("usajobs") or ""
        email   = keyring_manager.get_key("usajobs_email") or ""
        if api_key and email:
            providers.append(UsajobsProvider(api_key, email))
        else:
            logger.warning("USAJobs: No API key/email in keyring — skipping.")
    except Exception as e:
        logger.error(f"USAJobs init error: {e}")

    provider_cfg = config.get("providers", {})

    for pid, module_path, class_name, key_name in [
        ("indeed",    "integrations.indeed_provider",    "IndeedProvider",    "indeed"),
        ("linkedin",  "integrations.linkedin_provider",  "LinkedInProvider",  "linkedin"),
        ("glassdoor", "integrations.glassdoor_provider", "GlassdoorProvider", "glassdoor"),
        ("adzuna",    "integrations.adzuna_provider",    "AdzunaProvider",    "adzuna"),
    ]:
        if provider_cfg.get(pid, {}).get("enabled", False):
            try:
                import importlib
                mod = importlib.import_module(module_path)
                cls = getattr(mod, class_name)
                key = keyring_manager.get_key(key_name) or ""
                if key:
                    providers.append(cls(key))
            except Exception as e:
                logger.error(f"{pid} init error: {e}")

    logger.info(f"Enabled providers: {[p.DISPLAY_NAME for p in providers]}")
    return providers
