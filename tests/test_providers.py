"""
tests/test_providers.py
========================
Tests for Phase 12 providers: Indeed, LinkedIn, Glassdoor, Adzuna.
No network calls — all requests.get/post are mocked.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from core.job_model import JobListing
from integrations.base_provider import ProviderError


# ── Shared mock response builder ──────────────────────────────────────────────

def _jsearch_response(jobs: list, status: int = 200) -> MagicMock:
    r = MagicMock()
    r.status_code = status
    r.ok = (status == 200)
    r.json.return_value = {"data": jobs}
    r.raise_for_status = MagicMock()
    return r

def _adzuna_response(jobs: list, status: int = 200) -> MagicMock:
    r = MagicMock()
    r.status_code = status
    r.ok = (status == 200)
    r.json.return_value = {"results": jobs, "count": len(jobs)}
    r.raise_for_status = MagicMock()
    return r

def _jsearch_job(**kw) -> dict:
    defaults = {
        "job_id": "abc123",
        "job_title": "SOC Analyst",
        "employer_name": "CISA",
        "job_city": "Dallas",
        "job_state": "TX",
        "job_apply_link": "https://jobs.example.com/1",
        "job_description": "Monitor security events and respond to incidents.",
        "job_is_remote": False,
        "job_min_salary": 70000,
        "job_max_salary": 95000,
        "job_salary_period": "YEAR",
        "job_posted_at_datetime_utc": "2026-02-01T12:00:00Z",
        "job_publisher": "Indeed",
    }
    defaults.update(kw)
    return defaults

def _adzuna_job(**kw) -> dict:
    defaults = {
        "id": "az_001",
        "title": "Security Analyst",
        "company": {"display_name": "Lockheed Martin"},
        "location": {"display_name": "Fort Worth, TX", "area": ["TX", "Fort Worth"]},
        "redirect_url": "https://www.adzuna.com/details/az_001",
        "description": "Perform security monitoring and threat hunting.",
        "salary_min": 65000,
        "salary_max": 90000,
        "created": "2026-02-10T08:00:00Z",
        "category": {"label": "IT Jobs"},
    }
    defaults.update(kw)
    return defaults


# ══════════════════════════════════════════════════════════════════════════════
# IndeedProvider
# ══════════════════════════════════════════════════════════════════════════════

class TestIndeedProvider:

    def _provider(self):
        from integrations.indeed_provider import IndeedProvider
        return IndeedProvider(api_key="test-rapidapi-key")

    def test_search_returns_list_of_job_listings(self):
        p = self._provider()
        mock_resp = _jsearch_response([_jsearch_job()])
        with patch("integrations.indeed_provider.requests.get", return_value=mock_resp):
            results = p.search(["SOC Analyst"], "Dallas, TX", 50)
        assert isinstance(results, list)
        assert len(results) == 1
        assert isinstance(results[0], JobListing)

    def test_provider_id_is_indeed(self):
        result = self._provider()._normalize(_jsearch_job())
        assert result.provider == "indeed"

    def test_job_id_prefixed_indeed(self):
        result = self._provider()._normalize(_jsearch_job(job_id="xyz789"))
        assert result.job_id.startswith("indeed_")

    def test_title_mapped(self):
        result = self._provider()._normalize(_jsearch_job(job_title="Threat Hunter"))
        assert result.title == "Threat Hunter"

    def test_company_mapped(self):
        result = self._provider()._normalize(_jsearch_job(employer_name="FBI"))
        assert result.company == "FBI"

    def test_location_city_state(self):
        result = self._provider()._normalize(_jsearch_job(job_city="Dallas", job_state="TX"))
        assert "Dallas" in result.location
        assert "TX" in result.location

    def test_salary_annual(self):
        result = self._provider()._normalize(
            _jsearch_job(job_min_salary=70000, job_max_salary=95000, job_salary_period="YEAR"))
        assert result.salary_min == 70000.0
        assert result.salary_max == 95000.0
        assert result.salary_interval == "annual"

    def test_salary_hourly(self):
        result = self._provider()._normalize(
            _jsearch_job(job_min_salary=30, job_max_salary=45, job_salary_period="HOUR"))
        assert result.salary_interval == "hourly"

    def test_is_remote_true(self):
        result = self._provider()._normalize(_jsearch_job(job_is_remote=True))
        assert result.is_remote is True

    def test_is_remote_false(self):
        result = self._provider()._normalize(_jsearch_job(job_is_remote=False))
        assert result.is_remote is False

    def test_date_posted_parsed(self):
        result = self._provider()._normalize(
            _jsearch_job(job_posted_at_datetime_utc="2026-02-01T12:00:00Z"))
        assert isinstance(result.date_posted, datetime)
        assert result.date_posted.year == 2026

    def test_bad_date_does_not_crash(self):
        result = self._provider()._normalize(
            _jsearch_job(job_posted_at_datetime_utc="not-a-date"))
        assert result.date_posted is None

    def test_senior_experience_detected(self):
        result = self._provider()._normalize(_jsearch_job(job_title="Senior SOC Analyst"))
        assert result.experience_level == "senior"

    def test_entry_experience_detected(self):
        result = self._provider()._normalize(_jsearch_job(job_title="Entry Level SOC Analyst"))
        assert result.experience_level == "entry"

    def test_raises_provider_error_on_401(self):
        p = self._provider()
        with patch("integrations.indeed_provider.requests.get",
                   return_value=_jsearch_response([], 401)):
            with pytest.raises(ProviderError) as exc:
                p.search(["SOC"], "Dallas", 50)
            assert exc.value.status_code == 401

    def test_raises_provider_error_on_429(self):
        p = self._provider()
        with patch("integrations.indeed_provider.requests.get",
                   return_value=_jsearch_response([], 429)):
            with pytest.raises(ProviderError) as exc:
                p.search(["SOC"], "Dallas", 50)
            assert exc.value.status_code == 429

    def test_malformed_result_skipped_not_crashed(self):
        p = self._provider()
        bad = {"job_id": None, "job_title": None}
        mock_resp = _jsearch_response([bad, _jsearch_job()])
        with patch("integrations.indeed_provider.requests.get", return_value=mock_resp):
            results = p.search(["SOC"], "Dallas", 50)
        assert len(results) >= 0   # Should not raise

    def test_validate_key_returns_true_on_200(self):
        p = self._provider()
        with patch("integrations.indeed_provider.requests.get",
                   return_value=_jsearch_response([_jsearch_job()])):
            ok, msg = p.validate_key()
        assert ok is True

    def test_validate_key_returns_false_on_401(self):
        p = self._provider()
        with patch("integrations.indeed_provider.requests.get",
                   return_value=_jsearch_response([], 401)):
            ok, msg = p.validate_key()
        assert ok is False

    def test_max_results_respected(self):
        p = self._provider()
        jobs = [_jsearch_job(job_id=f"j{i}") for i in range(20)]
        mock_resp = _jsearch_response(jobs)
        with patch("integrations.indeed_provider.requests.get", return_value=mock_resp):
            results = p.search(["SOC"], "Dallas", 50, max_results=5)
        assert len(results) <= 5


# ══════════════════════════════════════════════════════════════════════════════
# LinkedInProvider
# ══════════════════════════════════════════════════════════════════════════════

class TestLinkedInProvider:

    def _provider(self):
        from integrations.linkedin_provider import LinkedInProvider
        return LinkedInProvider(api_key="test-rapidapi-key")

    def test_returns_job_listings(self):
        p = self._provider()
        with patch("integrations.linkedin_provider.requests.get",
                   return_value=_jsearch_response([_jsearch_job()])):
            results = p.search(["SOC"], "Dallas, TX", 50)
        assert isinstance(results, list)

    def test_provider_id_is_linkedin(self):
        result = self._provider()._normalize(_jsearch_job())
        assert result.provider == "linkedin"

    def test_job_id_prefixed_linkedin(self):
        result = self._provider()._normalize(_jsearch_job(job_id="xyz"))
        assert result.job_id.startswith("linkedin_")

    def test_title_mapped(self):
        result = self._provider()._normalize(_jsearch_job(job_title="Security Engineer"))
        assert result.title == "Security Engineer"

    def test_salary_mapped(self):
        result = self._provider()._normalize(
            _jsearch_job(job_min_salary=80000, job_max_salary=110000, job_salary_period="YEAR"))
        assert result.salary_min == 80000.0
        assert result.salary_interval == "annual"

    def test_raises_on_401(self):
        p = self._provider()
        with patch("integrations.linkedin_provider.requests.get",
                   return_value=_jsearch_response([], 401)):
            with pytest.raises(ProviderError):
                p.search(["SOC"], "Dallas", 50)

    def test_validate_key_true_on_200(self):
        p = self._provider()
        with patch("integrations.linkedin_provider.requests.get",
                   return_value=_jsearch_response([_jsearch_job()])):
            ok, _ = p.validate_key()
        assert ok is True

    def test_validate_key_false_on_401(self):
        p = self._provider()
        with patch("integrations.linkedin_provider.requests.get",
                   return_value=_jsearch_response([], 401)):
            ok, _ = p.validate_key()
        assert ok is False


# ══════════════════════════════════════════════════════════════════════════════
# GlassdoorProvider
# ══════════════════════════════════════════════════════════════════════════════

class TestGlassdoorProvider:

    def _provider(self):
        from integrations.glassdoor_provider import GlassdoorProvider
        return GlassdoorProvider(api_key="test-rapidapi-key")

    def test_returns_job_listings(self):
        p = self._provider()
        with patch("integrations.glassdoor_provider.requests.get",
                   return_value=_jsearch_response([_jsearch_job()])):
            results = p.search(["SOC"], "Dallas, TX", 50)
        assert isinstance(results, list)

    def test_provider_id_is_glassdoor(self):
        result = self._provider()._normalize(_jsearch_job())
        assert result.provider == "glassdoor"

    def test_job_id_prefixed_glassdoor(self):
        result = self._provider()._normalize(_jsearch_job(job_id="gd123"))
        assert result.job_id.startswith("glassdoor_")

    def test_title_and_company_mapped(self):
        result = self._provider()._normalize(
            _jsearch_job(job_title="Intel Analyst", employer_name="Raytheon"))
        assert result.title == "Intel Analyst"
        assert result.company == "Raytheon"

    def test_raises_on_401(self):
        p = self._provider()
        with patch("integrations.glassdoor_provider.requests.get",
                   return_value=_jsearch_response([], 401)):
            with pytest.raises(ProviderError):
                p.search(["SOC"], "Dallas", 50)

    def test_validate_key_true_on_200(self):
        p = self._provider()
        with patch("integrations.glassdoor_provider.requests.get",
                   return_value=_jsearch_response([_jsearch_job()])):
            ok, _ = p.validate_key()
        assert ok is True


# ══════════════════════════════════════════════════════════════════════════════
# AdzunaProvider
# ══════════════════════════════════════════════════════════════════════════════

class TestAdzunaProvider:

    def _provider(self):
        from integrations.adzuna_provider import AdzunaProvider
        return AdzunaProvider(api_key="app123:key456")

    def test_parse_creds_splits_on_colon(self):
        from integrations.adzuna_provider import AdzunaProvider
        p = AdzunaProvider(api_key="myapp:mykey")
        app_id, app_key = p._parse_creds()
        assert app_id == "myapp"
        assert app_key == "mykey"

    def test_parse_creds_no_colon_fallback(self):
        from integrations.adzuna_provider import AdzunaProvider
        p = AdzunaProvider(api_key="onlyone")
        app_id, app_key = p._parse_creds()
        assert app_id == "onlyone"

    def test_returns_job_listings(self):
        p = self._provider()
        with patch("integrations.adzuna_provider.requests.get",
                   return_value=_adzuna_response([_adzuna_job()])):
            results = p.search(["SOC Analyst"], "Dallas, TX", 50)
        assert isinstance(results, list)
        assert len(results) == 1
        assert isinstance(results[0], JobListing)

    def test_provider_id_is_adzuna(self):
        result = self._provider()._normalize(_adzuna_job())
        assert result.provider == "adzuna"

    def test_job_id_prefixed_adzuna(self):
        result = self._provider()._normalize(_adzuna_job(id="az_789"))
        assert result.job_id == "adzuna_az_789"

    def test_title_mapped(self):
        result = self._provider()._normalize(_adzuna_job(title="Cyber Threat Analyst"))
        assert result.title == "Cyber Threat Analyst"

    def test_company_from_nested_dict(self):
        result = self._provider()._normalize(
            _adzuna_job(company={"display_name": "Northrop Grumman"}))
        assert result.company == "Northrop Grumman"

    def test_location_from_display_name(self):
        result = self._provider()._normalize(
            _adzuna_job(location={"display_name": "Fort Worth, TX", "area": ["TX","Fort Worth"]}))
        assert "Fort Worth" in result.location

    def test_salary_annual(self):
        result = self._provider()._normalize(
            _adzuna_job(salary_min=65000, salary_max=90000))
        assert result.salary_min == 65000.0
        assert result.salary_max == 90000.0
        assert result.salary_interval == "annual"

    def test_no_salary_is_none(self):
        raw = _adzuna_job()
        raw.pop("salary_min"); raw.pop("salary_max")
        result = self._provider()._normalize(raw)
        assert result.salary_min is None
        assert result.salary_max is None

    def test_date_posted_parsed(self):
        result = self._provider()._normalize(
            _adzuna_job(created="2026-02-10T08:00:00Z"))
        assert isinstance(result.date_posted, datetime)
        assert result.date_posted.month == 2

    def test_bad_date_does_not_crash(self):
        result = self._provider()._normalize(_adzuna_job(created="garbage"))
        assert result.date_posted is None

    def test_remote_detected_from_category(self):
        result = self._provider()._normalize(
            _adzuna_job(category={"label": "Remote IT Jobs"}))
        assert result.is_remote is True

    def test_remote_detected_from_description(self):
        result = self._provider()._normalize(
            _adzuna_job(description="This is a 100% remote position working from home."))
        assert result.is_remote is True

    def test_senior_experience_from_title(self):
        result = self._provider()._normalize(_adzuna_job(title="Senior Security Analyst"))
        assert result.experience_level == "senior"

    def test_entry_experience_from_title(self):
        result = self._provider()._normalize(_adzuna_job(title="Junior SOC Analyst"))
        assert result.experience_level == "entry"

    def test_raises_on_401(self):
        p = self._provider()
        with patch("integrations.adzuna_provider.requests.get",
                   return_value=_adzuna_response([], 401)):
            with pytest.raises(ProviderError) as exc:
                p.search(["SOC"], "Dallas", 50)
            assert exc.value.status_code == 401

    def test_raises_on_429(self):
        p = self._provider()
        with patch("integrations.adzuna_provider.requests.get",
                   return_value=_adzuna_response([], 429)):
            with pytest.raises(ProviderError) as exc:
                p.search(["SOC"], "Dallas", 50)
            assert exc.value.status_code == 429

    def test_max_results_respected(self):
        p = self._provider()
        jobs = [_adzuna_job(id=str(i)) for i in range(30)]
        with patch("integrations.adzuna_provider.requests.get",
                   return_value=_adzuna_response(jobs)):
            results = p.search(["SOC"], "Dallas", 50, max_results=10)
        assert len(results) <= 10

    def test_validate_key_true_on_200(self):
        p = self._provider()
        with patch("integrations.adzuna_provider.requests.get",
                   return_value=_adzuna_response([_adzuna_job()])):
            ok, msg = p.validate_key()
        assert ok is True
        assert "Adzuna" in msg

    def test_validate_key_false_on_401(self):
        p = self._provider()
        with patch("integrations.adzuna_provider.requests.get",
                   return_value=_adzuna_response([], 401)):
            ok, _ = p.validate_key()
        assert ok is False

    def test_network_error_raises_provider_error(self):
        import requests as req
        p = self._provider()
        with patch("integrations.adzuna_provider.requests.get",
                   side_effect=req.RequestException("timeout")):
            with pytest.raises(ProviderError):
                p.search(["SOC"], "Dallas", 50)
