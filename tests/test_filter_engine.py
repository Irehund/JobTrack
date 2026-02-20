"""
tests/test_filter_engine.py
=============================
Tests for core/filter_engine.py and core/job_fetcher.py dedup logic.
All tests run in-memory — no API calls, no database, no network.
"""

import pytest
from datetime import datetime, timezone
from core.job_model import JobListing
from core import filter_engine
from core.job_fetcher import _deduplicate, _quality_score, FetchProgress, MAX_RETRIES


# ── Helpers ───────────────────────────────────────────────────────────────────

def _job(**kw) -> JobListing:
    """Build a JobListing with sensible defaults, overriding as needed."""
    defaults = dict(
        job_id="test_001", provider="usajobs",
        title="SOC Analyst", company="CISA",
        location="Dallas, TX", city="Dallas", state="TX",
        latitude=32.7767, longitude=-96.7970,
        is_remote=False, is_hybrid=False,
        experience_level="entry",
        description="Monitor security events.",
        salary_min=75000.0, salary_max=95000.0,
        salary_interval="annual",
    )
    defaults.update(kw)
    return JobListing(**defaults)


def _cfg(**kw) -> dict:
    """Build a config dict, Forney TX home, 50 mile radius, no filters."""
    cfg = {
        "location": {
            "city": "Forney", "state": "TX",
            "latitude": 32.7459, "longitude": -96.4685,
        },
        "search_radius_miles": 50,
        "job_preferences": {
            "keywords": [], "work_type": "any", "experience_level": "any",
        },
    }
    for k, v in kw.items():
        if isinstance(v, dict) and k in cfg and isinstance(cfg[k], dict):
            cfg[k].update(v)
        else:
            cfg[k] = v
    return cfg


# ── filter_by_radius ──────────────────────────────────────────────────────────

class TestFilterByRadius:

    def test_nearby_job_passes(self):
        job = _job(latitude=32.7767, longitude=-96.7970)  # Dallas ~19 mi
        assert len(filter_engine.filter_by_radius([job], 32.7459, -96.4685, 50)) == 1

    def test_distant_job_filtered(self):
        job = _job(latitude=47.6062, longitude=-122.3321)  # Seattle ~1,800 mi
        assert len(filter_engine.filter_by_radius([job], 32.7459, -96.4685, 50)) == 0

    def test_no_coords_always_passes(self):
        job = _job(latitude=None, longitude=None)
        assert len(filter_engine.filter_by_radius([job], 32.7459, -96.4685, 50)) == 1

    def test_empty_list_returns_empty(self):
        assert filter_engine.filter_by_radius([], 32.74, -96.46, 50) == []

    def test_mix_nearby_distant_no_coords(self):
        nearby  = _job(job_id="a", latitude=32.7767,  longitude=-96.7970)
        distant = _job(job_id="b", latitude=47.6062,  longitude=-122.3321)
        no_loc  = _job(job_id="c", latitude=None,     longitude=None)
        result  = filter_engine.filter_by_radius(
            [nearby, distant, no_loc], 32.7459, -96.4685, 50)
        ids = [j.job_id for j in result]
        assert "a" in ids
        assert "b" not in ids
        assert "c" in ids

    def test_wider_radius_includes_more(self):
        ft_worth = _job(job_id="fw", latitude=32.7555, longitude=-97.3308)  # ~50 mi
        result_50  = filter_engine.filter_by_radius([ft_worth], 32.7459, -96.4685, 40)
        result_100 = filter_engine.filter_by_radius([ft_worth], 32.7459, -96.4685, 100)
        assert len(result_50) == 0
        assert len(result_100) == 1


# ── filter_by_work_type ───────────────────────────────────────────────────────

class TestFilterByWorkType:

    def _three_jobs(self):
        return [
            _job(job_id="r", is_remote=True,  is_hybrid=False),
            _job(job_id="h", is_remote=False, is_hybrid=True),
            _job(job_id="o", is_remote=False, is_hybrid=False),
        ]

    def test_any_returns_all(self):
        assert len(filter_engine.filter_by_work_type(self._three_jobs(), "any")) == 3

    def test_remote_only(self):
        result = filter_engine.filter_by_work_type(self._three_jobs(), "remote")
        assert len(result) == 1 and result[0].job_id == "r"

    def test_hybrid_only(self):
        result = filter_engine.filter_by_work_type(self._three_jobs(), "hybrid")
        assert len(result) == 1 and result[0].job_id == "h"

    def test_onsite_only(self):
        result = filter_engine.filter_by_work_type(self._three_jobs(), "onsite")
        assert len(result) == 1 and result[0].job_id == "o"

    def test_unknown_value_passes_all(self):
        result = filter_engine.filter_by_work_type(self._three_jobs(), "teleport")
        assert len(result) == 3

    def test_empty_list_returns_empty(self):
        assert filter_engine.filter_by_work_type([], "remote") == []


# ── filter_by_experience ──────────────────────────────────────────────────────

class TestFilterByExperience:

    def _three_jobs(self):
        return [
            _job(job_id="e", experience_level="entry"),
            _job(job_id="m", experience_level="mid"),
            _job(job_id="s", experience_level="senior"),
        ]

    def test_any_returns_all(self):
        assert len(filter_engine.filter_by_experience(self._three_jobs(), "any")) == 3

    def test_entry_only(self):
        result = filter_engine.filter_by_experience(self._three_jobs(), "entry")
        assert len(result) == 1 and result[0].job_id == "e"

    def test_mid_only(self):
        result = filter_engine.filter_by_experience(self._three_jobs(), "mid")
        assert len(result) == 1 and result[0].job_id == "m"

    def test_senior_only(self):
        result = filter_engine.filter_by_experience(self._three_jobs(), "senior")
        assert len(result) == 1 and result[0].job_id == "s"

    def test_unknown_experience_always_passes(self):
        """Jobs with empty experience_level pass through any filter."""
        jobs = [
            _job(job_id="u", experience_level=""),
            _job(job_id="e", experience_level="entry"),
            _job(job_id="m", experience_level="mid"),
        ]
        result = filter_engine.filter_by_experience(jobs, "entry")
        ids = [j.job_id for j in result]
        assert "u" in ids   # unknown always passes
        assert "e" in ids   # entry matches
        assert "m" not in ids

    def test_empty_list_returns_empty(self):
        assert filter_engine.filter_by_experience([], "entry") == []


# ── filter_by_keywords ────────────────────────────────────────────────────────

class TestFilterByKeywords:

    def test_empty_keywords_returns_all(self):
        jobs = [_job(job_id="a"), _job(job_id="b")]
        assert len(filter_engine.filter_by_keywords(jobs, [])) == 2

    def test_match_in_title(self):
        jobs = [
            _job(job_id="a", title="SOC Analyst II",    description=""),
            _job(job_id="b", title="Software Engineer", description=""),
        ]
        result = filter_engine.filter_by_keywords(jobs, ["SOC Analyst"])
        assert len(result) == 1 and result[0].job_id == "a"

    def test_match_in_description(self):
        jobs = [
            _job(job_id="a", title="Security Specialist",
                 description="Must have SOC analyst experience"),
            _job(job_id="b", title="IT Support",
                 description="Help desk role"),
        ]
        result = filter_engine.filter_by_keywords(jobs, ["SOC analyst"])
        assert len(result) == 1 and result[0].job_id == "a"

    def test_case_insensitive(self):
        job = _job(title="soc analyst")
        assert len(filter_engine.filter_by_keywords([job], ["SOC ANALYST"])) == 1

    def test_any_keyword_passes(self):
        job = _job(title="Intelligence Analyst")
        result = filter_engine.filter_by_keywords(
            [job], ["SOC Analyst", "Security Analyst", "Intelligence Analyst"])
        assert len(result) == 1

    def test_no_match_filtered(self):
        job = _job(title="Nurse Practitioner", description="Healthcare")
        assert filter_engine.filter_by_keywords(job, ["SOC Analyst"]) == []

    def test_substring_match(self):
        job = _job(title="Cyber Analyst II")
        assert len(filter_engine.filter_by_keywords([job], ["analyst"])) == 1

    def test_whitespace_only_keywords_ignored(self):
        job = _job(job_id="a")
        assert len(filter_engine.filter_by_keywords([job], ["  ", ""])) == 1

    def test_empty_list_returns_empty(self):
        assert filter_engine.filter_by_keywords([], ["SOC"]) == []


# ── apply_filters pipeline ────────────────────────────────────────────────────

class TestApplyFilters:

    def test_empty_listings_returns_empty(self):
        assert filter_engine.apply_filters([], _cfg()) == []

    def test_all_any_no_coords_passes_everything(self):
        jobs = [_job(job_id=f"j{i}") for i in range(5)]
        config = _cfg()
        config["location"].pop("latitude")
        config["location"].pop("longitude")
        assert len(filter_engine.apply_filters(jobs, config)) == 5

    def test_radius_applied_when_coords_present(self):
        nearby = _job(job_id="near", latitude=32.7767, longitude=-96.7970)
        far    = _job(job_id="far",  latitude=47.6062, longitude=-122.3321)
        result = filter_engine.apply_filters([nearby, far], _cfg())
        ids = [j.job_id for j in result]
        assert "near" in ids and "far" not in ids

    def test_work_type_applied(self):
        config = _cfg()
        config["location"].pop("latitude"); config["location"].pop("longitude")
        config["job_preferences"]["work_type"] = "remote"
        jobs = [
            _job(job_id="r", is_remote=True),
            _job(job_id="o", is_remote=False, is_hybrid=False),
        ]
        result = filter_engine.apply_filters(jobs, config)
        assert len(result) == 1 and result[0].job_id == "r"

    def test_keyword_applied(self):
        config = _cfg()
        config["location"].pop("latitude"); config["location"].pop("longitude")
        config["job_preferences"]["keywords"] = ["SOC Analyst"]
        jobs = [
            _job(job_id="soc",   title="SOC Analyst"),
            _job(job_id="nurse", title="Registered Nurse"),
        ]
        result = filter_engine.apply_filters(jobs, config)
        assert len(result) == 1 and result[0].job_id == "soc"

    def test_all_filters_combined(self):
        match = _job(job_id="m", title="SOC Analyst", is_remote=True,
                     experience_level="entry",
                     latitude=32.7767, longitude=-96.7970)
        wrong_title = _job(job_id="n", title="Nurse Practitioner",
                           is_remote=True, experience_level="entry",
                           latitude=32.7767, longitude=-96.7970)
        wrong_type  = _job(job_id="o", title="SOC Analyst",
                           is_remote=False, is_hybrid=False,
                           experience_level="entry",
                           latitude=32.7767, longitude=-96.7970)
        config = _cfg()
        config["job_preferences"]["keywords"]         = ["SOC Analyst"]
        config["job_preferences"]["work_type"]        = "remote"
        config["job_preferences"]["experience_level"] = "entry"
        result = filter_engine.apply_filters([match, wrong_title, wrong_type], config)
        assert len(result) == 1 and result[0].job_id == "m"


# ── _deduplicate ──────────────────────────────────────────────────────────────

class TestDeduplicate:

    def test_unique_listings_unchanged(self):
        jobs = [
            _job(job_id="a", title="SOC Analyst",         company="CISA", state="TX"),
            _job(job_id="b", title="Security Engineer",   company="FBI",  state="VA"),
            _job(job_id="c", title="Intelligence Analyst",company="NSA",  state="MD"),
        ]
        assert len(_deduplicate(jobs)) == 3

    def test_duplicates_reduced_to_one(self):
        j1 = _job(job_id="usajobs_1", provider="usajobs",
                  title="SOC Analyst", company="CISA", state="TX")
        j2 = _job(job_id="indeed_99", provider="indeed",
                  title="SOC Analyst", company="CISA", state="TX")
        assert len(_deduplicate([j1, j2])) == 1

    def test_richer_listing_wins(self):
        poor = _job(job_id="a", provider="usajobs",
                    title="SOC Analyst", company="CISA", state="TX",
                    description="", salary_min=None, salary_max=None)
        rich = _job(job_id="b", provider="indeed",
                    title="SOC Analyst", company="CISA", state="TX",
                    description="Detailed description.",
                    salary_min=80000.0, salary_max=100000.0)
        result = _deduplicate([poor, rich])
        assert len(result) == 1
        assert result[0].description == "Detailed description."

    def test_order_does_not_affect_winner(self):
        poor = _job(job_id="a", provider="usajobs",
                    title="Analyst", company="Acme", state="TX",
                    description="", salary_min=None)
        rich = _job(job_id="b", provider="indeed",
                    title="Analyst", company="Acme", state="TX",
                    description="Great role.", salary_min=80000.0)
        assert _deduplicate([rich, poor])[0].salary_min == 80000.0
        assert _deduplicate([poor, rich])[0].salary_min == 80000.0

    def test_empty_returns_empty(self):
        assert _deduplicate([]) == []

    def test_single_unchanged(self):
        job = _job()
        assert _deduplicate([job]) == [job]


# ── _quality_score ────────────────────────────────────────────────────────────

class TestQualityScore:

    def test_empty_listing_scores_zero(self):
        job = _job(description="", salary_min=None, salary_max=None,
                   closing_date=None, latitude=None)
        assert _quality_score(job) == 0

    def test_full_listing_scores_higher_than_empty(self):
        poor = _job(description="", salary_min=None, salary_max=None,
                    closing_date=None, latitude=None)
        rich = _job(description="Full description",
                    salary_min=80000.0, salary_max=100000.0,
                    closing_date=datetime(2026, 3, 1, tzinfo=timezone.utc),
                    latitude=32.77)
        assert _quality_score(rich) > _quality_score(poor)

    def test_description_worth_most(self):
        with_desc    = _job(description="Some text",
                            salary_min=None, salary_max=None)
        without_desc = _job(description="",
                            salary_min=80000.0, salary_max=100000.0)
        assert _quality_score(with_desc) > _quality_score(without_desc)


# ── FetchProgress ─────────────────────────────────────────────────────────────

class TestFetchProgress:

    def test_starts_at_zero(self):
        p = FetchProgress(total_providers=4)
        assert p.percent_complete == 0.0

    def test_half_complete(self):
        p = FetchProgress(total_providers=4)
        p.completed_providers = 2
        assert p.percent_complete == 50.0

    def test_fully_complete(self):
        p = FetchProgress(total_providers=4)
        p.completed_providers = 4
        assert p.percent_complete == 100.0

    def test_zero_providers_is_100(self):
        assert FetchProgress(total_providers=0).percent_complete == 100.0

    def test_status_message_searching(self):
        p = FetchProgress(total_providers=1)
        p.current_provider = "USAJobs"
        p.retry_attempt = 0
        assert "USAJobs" in p.status_message

    def test_status_message_retrying(self):
        p = FetchProgress(total_providers=1)
        p.current_provider = "Indeed"
        p.retry_attempt = 2
        msg = p.status_message
        assert "Retrying" in msg
        assert "Indeed" in msg
        assert "2" in msg

    def test_max_retries_is_3(self):
        assert MAX_RETRIES == 3
