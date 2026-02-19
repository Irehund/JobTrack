"""
tests/test_usajobs_provider.py
================================
Tests for integrations/usajobs_provider.py and core/job_model.py.
All HTTP calls are mocked — no real API calls made during testing.
"""

import json
import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from core.job_model import JobListing, _haversine
from integrations.usajobs_provider import UsajobsProvider
from integrations.base_provider import ProviderError


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _make_provider():
    return UsajobsProvider(api_key="test-api-key-12345", user_email="test@example.com")


def _make_raw_item(overrides: dict = None) -> dict:
    """Build a minimal realistic USAJobs API response item."""
    item = {
        "MatchedObjectId": "12345678",
        "MatchedObjectDescriptor": {
            "PositionID": "CISA-2026-001",
            "PositionTitle": "Information Security Analyst",
            "OrganizationName": "Cybersecurity and Infrastructure Security Agency",
            "DepartmentName": "Department of Homeland Security",
            "PositionLocation": [
                {
                    "CityName": "Dallas",
                    "CountrySubDivisionCode": "TX",
                    "CountryCode": "US",
                    "Latitude": "32.7767",
                    "Longitude": "-96.7970",
                }
            ],
            "PositionURI": "https://www.usajobs.gov/job/12345678",
            "PublicationStartDate": "2026-02-01T00:00:00.0000000Z",
            "ApplicationCloseDate": "2026-03-01T00:00:00.0000000Z",
            "PositionRemuneration": [
                {
                    "MinimumRange": "75000",
                    "MaximumRange": "95000",
                    "RateIntervalCode": "PA",
                }
            ],
            "PositionSchedule": [{"Code": "FullTime", "Name": "Full-time"}],
            "TeleworkSchedule": [{"Code": "03", "Name": "Situational telework"}],
            "JobGrade": [{"Code": "GS-11"}],
            "UserArea": {
                "Details": {
                    "JobSummary": "Serve as an information security analyst protecting critical infrastructure."
                }
            },
        }
    }
    if overrides:
        item["MatchedObjectDescriptor"].update(overrides)
    return item


def _make_api_response(items: list) -> dict:
    """Wrap items in a realistic USAJobs API response envelope."""
    return {
        "SearchResult": {
            "SearchResultCount": len(items),
            "SearchResultItems": items,
        }
    }


# ── JobListing tests ──────────────────────────────────────────────────────────

class TestJobListing:

    def test_dedup_key_same_job_different_providers(self):
        """Same job from two providers should produce identical dedup keys."""
        j1 = JobListing(job_id="usajobs_1", provider="usajobs",
                        title="SOC Analyst", company="Acme Corp", location="Dallas, TX",
                        state="TX")
        j2 = JobListing(job_id="indeed_99", provider="indeed",
                        title="SOC Analyst", company="Acme Corp", location="Dallas, TX",
                        state="TX")
        assert j1.dedup_key() == j2.dedup_key()

    def test_dedup_key_normalizes_case_and_punctuation(self):
        """dedup_key should be case-insensitive and strip punctuation."""
        j1 = JobListing(job_id="a", provider="x", title="Sr. SOC Analyst",
                        company="Acme, Inc.", location="Dallas, TX", state="TX")
        j2 = JobListing(job_id="b", provider="x", title="sr soc analyst",
                        company="acme inc", location="Dallas, TX", state="TX")
        assert j1.dedup_key() == j2.dedup_key()

    def test_dedup_key_different_companies_differ(self):
        j1 = JobListing(job_id="a", provider="x", title="Analyst",
                        company="Acme", location="Dallas, TX", state="TX")
        j2 = JobListing(job_id="b", provider="x", title="Analyst",
                        company="Globex", location="Dallas, TX", state="TX")
        assert j1.dedup_key() != j2.dedup_key()

    def test_is_within_radius_true_for_nearby_job(self):
        """A job 10 miles away should pass a 50-mile radius check."""
        # Forney TX to Dallas TX is roughly 25 miles
        job = JobListing(job_id="a", provider="x", title="T", company="C",
                         location="Dallas, TX", latitude=32.7767, longitude=-96.7970)
        # Forney TX approximate coords
        assert job.is_within_radius(32.7459, -96.4685, 50) == True

    def test_is_within_radius_false_for_distant_job(self):
        """A job 1500 miles away should fail a 50-mile radius check."""
        job = JobListing(job_id="a", provider="x", title="T", company="C",
                         location="Seattle, WA", latitude=47.6062, longitude=-122.3321)
        assert job.is_within_radius(32.7459, -96.4685, 50) == False

    def test_is_within_radius_true_when_no_coords(self):
        """Jobs with no coordinates should always pass the radius check."""
        job = JobListing(job_id="a", provider="x", title="T", company="C",
                         location="Unknown", latitude=None, longitude=None)
        assert job.is_within_radius(32.7459, -96.4685, 50) == True

    def test_haversine_dallas_to_forney(self):
        """Dallas to Forney TX should be roughly 25 miles."""
        dist = _haversine(32.7767, -96.7970, 32.7459, -96.4685)
        assert 20 < dist < 35

    def test_haversine_same_point_is_zero(self):
        dist = _haversine(32.7767, -96.7970, 32.7767, -96.7970)
        assert dist < 0.001


# ── UsajobsProvider._normalize tests ─────────────────────────────────────────

class TestUsajobsNormalize:

    def setup_method(self):
        self.provider = _make_provider()

    def test_normalize_basic_fields(self):
        listing = self.provider._normalize(_make_raw_item())
        assert listing.job_id == "usajobs_CISA-2026-001"
        assert listing.provider == "usajobs"
        assert listing.title == "Information Security Analyst"
        assert "Cybersecurity" in listing.company
        assert listing.city == "Dallas"
        assert listing.state == "TX"
        assert listing.location == "Dallas, TX"

    def test_normalize_coordinates(self):
        listing = self.provider._normalize(_make_raw_item())
        assert listing.latitude == pytest.approx(32.7767, rel=1e-3)
        assert listing.longitude == pytest.approx(-96.7970, rel=1e-3)

    def test_normalize_salary(self):
        listing = self.provider._normalize(_make_raw_item())
        assert listing.salary_min == 75000.0
        assert listing.salary_max == 95000.0
        assert listing.salary_interval == "annual"

    def test_normalize_biweekly_salary_converted_to_annual(self):
        """Bi-weekly pay should be multiplied by 26 for annual display."""
        raw = _make_raw_item({
            "PositionRemuneration": [{"MinimumRange": "2000", "MaximumRange": "3000",
                                       "RateIntervalCode": "BW"}]
        })
        listing = self.provider._normalize(raw)
        assert listing.salary_min == pytest.approx(52000.0)
        assert listing.salary_max == pytest.approx(78000.0)
        assert listing.salary_interval == "annual"

    def test_normalize_hybrid_telework(self):
        listing = self.provider._normalize(_make_raw_item())
        assert listing.is_hybrid == True
        assert listing.is_remote == False

    def test_normalize_remote_from_telework_code(self):
        raw = _make_raw_item({"TeleworkSchedule": [{"Code": "01"}]})
        listing = self.provider._normalize(raw)
        assert listing.is_remote == True

    def test_normalize_remote_from_title(self):
        raw = _make_raw_item({"PositionTitle": "Remote Security Analyst"})
        listing = self.provider._normalize(raw)
        assert listing.is_remote == True

    def test_normalize_senior_experience_level(self):
        raw = _make_raw_item({"JobGrade": [{"Code": "GS-14"}]})
        listing = self.provider._normalize(raw)
        assert listing.experience_level == "senior"

    def test_normalize_entry_experience_level(self):
        raw = _make_raw_item({"JobGrade": [{"Code": "GS-5"}]})
        listing = self.provider._normalize(raw)
        assert listing.experience_level == "entry"

    def test_normalize_url(self):
        listing = self.provider._normalize(_make_raw_item())
        assert "usajobs.gov" in listing.url

    def test_normalize_dates(self):
        listing = self.provider._normalize(_make_raw_item())
        assert isinstance(listing.date_posted, datetime)
        assert listing.date_posted.year == 2026
        assert listing.date_posted.month == 2

    def test_normalize_multiple_locations_note(self):
        raw = _make_raw_item({
            "PositionLocation": [
                {"CityName": "Dallas", "CountrySubDivisionCode": "TX",
                 "CountryCode": "US", "Latitude": "32.7767", "Longitude": "-96.7970"},
                {"CityName": "Austin", "CountrySubDivisionCode": "TX",
                 "CountryCode": "US", "Latitude": "30.2672", "Longitude": "-97.7431"},
            ]
        })
        listing = self.provider._normalize(raw)
        assert "+1 locations" in listing.location

    def test_normalize_missing_coords_graceful(self):
        raw = _make_raw_item({"PositionLocation": [
            {"CityName": "Nationwide", "CountrySubDivisionCode": "",
             "CountryCode": "US"}  # No Latitude/Longitude
        ]})
        listing = self.provider._normalize(raw)
        assert listing.latitude is None
        assert listing.longitude is None

    def test_normalize_stores_raw(self):
        raw = _make_raw_item()
        listing = self.provider._normalize(raw)
        assert listing.raw == raw


# ── UsajobsProvider.search tests ─────────────────────────────────────────────

class TestUsajobsSearch:

    def setup_method(self):
        self.provider = _make_provider()

    @patch("integrations.usajobs_provider.requests.get")
    def test_search_returns_listings(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: _make_api_response([_make_raw_item()])
        )
        results = self.provider.search(["SOC Analyst"], "Dallas, TX", 50)
        assert len(results) == 1
        assert isinstance(results[0], JobListing)

    @patch("integrations.usajobs_provider.requests.get")
    def test_search_empty_results(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: _make_api_response([])
        )
        results = self.provider.search(["very obscure title xyz"], "Dallas, TX", 50)
        assert results == []

    @patch("integrations.usajobs_provider.requests.get")
    def test_search_raises_provider_error_on_401(self, mock_get):
        mock_get.return_value = MagicMock(status_code=401)
        with pytest.raises(ProviderError) as exc_info:
            self.provider.search(["analyst"], "Dallas, TX", 50)
        assert exc_info.value.status_code == 401

    @patch("integrations.usajobs_provider.requests.get")
    def test_search_raises_provider_error_on_429(self, mock_get):
        mock_get.return_value = MagicMock(status_code=429)
        with pytest.raises(ProviderError) as exc_info:
            self.provider.search(["analyst"], "Dallas, TX", 50)
        assert exc_info.value.status_code == 429

    @patch("integrations.usajobs_provider.requests.get")
    def test_search_raises_provider_error_on_network_failure(self, mock_get):
        import requests as req
        mock_get.side_effect = req.RequestException("Connection refused")
        with pytest.raises(ProviderError):
            self.provider.search(["analyst"], "Dallas, TX", 50)

    @patch("integrations.usajobs_provider.requests.get")
    def test_search_skips_malformed_items_gracefully(self, mock_get):
        """A bad item in the results should be skipped, not crash the search."""
        good = _make_raw_item()
        bad  = {"MatchedObjectDescriptor": None}  # Will cause normalize to fail
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: _make_api_response([bad, good])
        )
        results = self.provider.search(["analyst"], "Dallas, TX", 50)
        assert len(results) == 1  # Only the good one

    @patch("integrations.usajobs_provider.requests.get")
    def test_search_sends_correct_headers(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: _make_api_response([])
        )
        self.provider.search(["analyst"], "Dallas, TX", 50)
        call_kwargs = mock_get.call_args
        headers = call_kwargs[1]["headers"]
        assert headers["Authorization-Key"] == "test-api-key-12345"
        assert headers["User-Agent"] == "test@example.com"

    @patch("integrations.usajobs_provider.requests.get")
    def test_search_max_results_capped_at_500(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: _make_api_response([])
        )
        self.provider.search(["analyst"], "Dallas, TX", 50, max_results=9999)
        params = mock_get.call_args[1]["params"]
        assert int(params["ResultsPerPage"]) <= 500


# ── UsajobsProvider.validate_key tests ───────────────────────────────────────

class TestUsajobsValidateKey:

    def setup_method(self):
        self.provider = _make_provider()

    @patch("integrations.usajobs_provider.requests.get")
    def test_validate_returns_true_on_200(self, mock_get):
        mock_get.return_value = MagicMock(status_code=200)
        valid, msg = self.provider.validate_key()
        assert valid == True
        assert "successfully" in msg.lower()

    @patch("integrations.usajobs_provider.requests.get")
    def test_validate_returns_false_on_401(self, mock_get):
        mock_get.return_value = MagicMock(status_code=401)
        valid, msg = self.provider.validate_key()
        assert valid == False
        assert len(msg) > 0

    @patch("integrations.usajobs_provider.requests.get")
    def test_validate_returns_false_on_network_error(self, mock_get):
        import requests as req
        mock_get.side_effect = req.RequestException("timeout")
        valid, msg = self.provider.validate_key()
        assert valid == False
        assert "internet" in msg.lower()
