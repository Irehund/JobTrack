"""
core/job_fetcher.py
====================
Orchestrates job searches across all enabled provider modules.
Runs providers in parallel using threads to keep the UI responsive.
Deduplicates results using JobListing.dedup_key().
Reports progress back to the UI via a callback.

Error/retry behavior per provider:
    - Attempt 1: Run normally
    - Attempt 2: On failure, notify UI ("Retrying Indeed — Attempt 2 of 3")
    - Attempt 3: On failure, notify UI ("Retrying Indeed — Attempt 3 of 3")
    - After 3 failures: Skip silently, continue with remaining providers
"""

from typing import Callable, Optional
from core.job_model import JobListing


MAX_RETRIES = 3


class FetchProgress:
    """
    Passed to the progress callback during a search.
    UI uses this to update the progress bar and status label.
    """
    def __init__(self, total_providers: int):
        self.total_providers = total_providers
        self.completed_providers = 0
        self.current_provider: str = ""
        self.retry_attempt: int = 0       # 0 = not retrying
        self.failed_providers: list[str] = []
        self.total_results: int = 0

    @property
    def percent_complete(self) -> float:
        if self.total_providers == 0:
            return 100.0
        return (self.completed_providers / self.total_providers) * 100


# Type alias for the progress callback the UI registers
ProgressCallback = Callable[[FetchProgress], None]


def fetch_jobs(
    config: dict,
    progress_callback: Optional[ProgressCallback] = None,
) -> list[JobListing]:
    """
    Run a job search across all enabled providers.

    Args:
        config:            The loaded config dict from config_manager.load()
        progress_callback: Optional function called after each provider
                           completes or fails, receiving a FetchProgress object.

    Returns:
        Deduplicated list of JobListing objects sorted by date_posted descending.
    """
    # TODO: Implement parallel fetch logic
    # 1. Determine which providers are enabled in config
    # 2. Instantiate each provider module
    # 3. Run each in a ThreadPoolExecutor
    # 4. For each provider: attempt up to MAX_RETRIES times
    #    - On each retry failure: call progress_callback with retry info
    #    - After MAX_RETRIES: add to failed_providers, continue
    # 5. Collect all results, deduplicate via _deduplicate()
    # 6. Sort by date_posted descending
    # 7. Return final list
    raise NotImplementedError


def _deduplicate(listings: list[JobListing]) -> list[JobListing]:
    """
    Remove duplicate listings using JobListing.dedup_key().
    When duplicates exist across providers, prefer the listing
    with the most complete data (longest description, has salary, etc.).
    """
    # TODO: Build a dict keyed by dedup_key, keeping the "best" listing per key
    raise NotImplementedError


def _get_enabled_providers(config: dict):
    """
    Instantiate and return a list of enabled provider objects.
    Each object is an instance of a class that extends BaseProvider.
    """
    # TODO: Import each provider module and instantiate if enabled in config
    # Always include USAJobsProvider regardless of config
    raise NotImplementedError
