"""
tests/test_map_builder.py
==========================
Tests for core/map_builder.py and core/commute_calculator.py.
No network calls, no Folium rendering, no ORS API — all mocked.
"""

import pytest
from unittest.mock import MagicMock, patch
from core.job_model import JobListing
from core.map_builder import _commute_color, _build_popup_html, build_map
from core import commute_calculator


# ── Helpers ───────────────────────────────────────────────────────────────────

def _job(**kw) -> JobListing:
    defaults = dict(
        job_id="test_001", provider="usajobs",
        title="SOC Analyst", company="CISA",
        location="Dallas, TX", city="Dallas", state="TX",
        latitude=32.7767, longitude=-96.7970,
        is_remote=False, is_hybrid=False,
        salary_min=75000.0, salary_max=95000.0,
        salary_interval="annual",
        url="https://usajobs.gov/1",
        commute_minutes=None,
    )
    defaults.update(kw)
    return JobListing(**defaults)


# ── _commute_color ────────────────────────────────────────────────────────────

class TestCommuteColor:

    def test_none_returns_gray(self):
        assert _commute_color(None) == "gray"

    def test_under_30_returns_green(self):
        assert _commute_color(0)  == "green"
        assert _commute_color(15) == "green"
        assert _commute_color(29) == "green"

    def test_30_to_60_returns_orange(self):
        assert _commute_color(30) == "orange"
        assert _commute_color(45) == "orange"
        assert _commute_color(60) == "orange"

    def test_over_60_returns_red(self):
        assert _commute_color(61)  == "red"
        assert _commute_color(90)  == "red"
        assert _commute_color(120) == "red"

    def test_boundary_30_is_orange_not_green(self):
        assert _commute_color(30) == "orange"
        assert _commute_color(29) == "green"

    def test_boundary_60_is_orange_not_red(self):
        assert _commute_color(60) == "orange"
        assert _commute_color(61) == "red"


# ── _build_popup_html ─────────────────────────────────────────────────────────

class TestBuildPopupHtml:

    def test_title_in_popup(self):
        html = _build_popup_html(_job(title="SOC Analyst"))
        assert "SOC Analyst" in html

    def test_company_in_popup(self):
        html = _build_popup_html(_job(company="CISA"))
        assert "CISA" in html

    def test_location_in_popup(self):
        html = _build_popup_html(_job(location="Dallas, TX"))
        assert "Dallas, TX" in html

    def test_commute_time_shown_when_available(self):
        html = _build_popup_html(_job(commute_minutes=25))
        assert "25 min" in html

    def test_commute_hours_and_mins_formatted(self):
        html = _build_popup_html(_job(commute_minutes=90))
        assert "1h" in html and "30min" in html

    def test_commute_unknown_when_none(self):
        html = _build_popup_html(_job(commute_minutes=None))
        assert "not calculated" in html.lower()

    def test_remote_badge_shown(self):
        html = _build_popup_html(_job(is_remote=True))
        assert "Remote" in html

    def test_hybrid_badge_shown(self):
        html = _build_popup_html(_job(is_hybrid=True))
        assert "Hybrid" in html

    def test_no_badge_for_onsite(self):
        html = _build_popup_html(_job(is_remote=False, is_hybrid=False))
        assert "Remote" not in html
        assert "Hybrid" not in html

    def test_apply_link_present_when_url_set(self):
        html = _build_popup_html(_job(url="https://usajobs.gov/123"))
        assert "https://usajobs.gov/123" in html

    def test_no_apply_link_when_no_url(self):
        html = _build_popup_html(_job(url=""))
        assert "View Posting" not in html

    def test_salary_included(self):
        html = _build_popup_html(_job(salary_min=75000.0, salary_max=95000.0))
        assert "75,000" in html

    def test_returns_string(self):
        assert isinstance(_build_popup_html(_job()), str)


# ── build_map ─────────────────────────────────────────────────────────────────

class TestBuildMap:

    def test_returns_output_path(self, tmp_path):
        out = str(tmp_path / "test_map.html")
        result = build_map(
            listings=[_job()],
            home_lat=32.7459, home_lon=-96.4685,
            output_path=out,
        )
        assert result == out

    def test_creates_html_file(self, tmp_path):
        out = str(tmp_path / "test_map.html")
        build_map(
            listings=[_job()],
            home_lat=32.7459, home_lon=-96.4685,
            output_path=out,
        )
        import os
        assert os.path.exists(out)

    def test_html_file_not_empty(self, tmp_path):
        out = str(tmp_path / "test_map.html")
        build_map(
            listings=[_job()],
            home_lat=32.7459, home_lon=-96.4685,
            output_path=out,
        )
        content = open(out).read()
        assert len(content) > 100

    def test_html_contains_leaflet(self, tmp_path):
        """Folium maps always include Leaflet.js."""
        out = str(tmp_path / "test_map.html")
        build_map(listings=[_job()], home_lat=32.7459,
                  home_lon=-96.4685, output_path=out)
        assert "leaflet" in open(out).read().lower()

    def test_html_contains_job_title(self, tmp_path):
        out = str(tmp_path / "test_map.html")
        build_map(listings=[_job(title="Cyber Analyst")],
                  home_lat=32.7459, home_lon=-96.4685, output_path=out)
        assert "Cyber Analyst" in open(out).read()

    def test_skips_jobs_without_coords(self, tmp_path):
        """Jobs with no coords should not crash map generation."""
        jobs = [
            _job(job_id="a", latitude=32.7767, longitude=-96.7970),
            _job(job_id="b", latitude=None, longitude=None),
        ]
        out = str(tmp_path / "test_map.html")
        result = build_map(jobs, 32.7459, -96.4685, out)
        assert result == out  # No crash

    def test_empty_listings_still_generates_map(self, tmp_path):
        """Empty results list should still produce a valid map."""
        out = str(tmp_path / "test_map.html")
        result = build_map([], 32.7459, -96.4685, out)
        assert result == out
        assert "leaflet" in open(out).read().lower()

    def test_legend_in_map(self, tmp_path):
        out = str(tmp_path / "test_map.html")
        build_map(listings=[_job()], home_lat=32.7459,
                  home_lon=-96.4685, output_path=out)
        content = open(out).read()
        assert "Commute Time" in content

    def test_commute_color_reflected_in_map(self, tmp_path):
        """A job with commute < 30 min should have green pin."""
        out = str(tmp_path / "test_map.html")
        build_map(listings=[_job(commute_minutes=20)],
                  home_lat=32.7459, home_lon=-96.4685, output_path=out)
        assert "green" in open(out).read()


# ── commute_calculator: _commute_color ───────────────────────────────────────
# (Also tested in TestCommuteColor above via map_builder import)

class TestCommuteCalculatorCache:

    def setup_method(self):
        """Clear the in-memory cache before each test."""
        commute_calculator.clear_cache()

    def test_clear_cache_empties_store(self):
        commute_calculator._cache[(1.0, 2.0, 3.0, 4.0)] = 25
        commute_calculator.clear_cache()
        assert len(commute_calculator._cache) == 0

    def test_cache_populated_after_calculate_single(self):
        """calculate_single should populate _cache after an API call."""
        with patch("core.commute_calculator._call_api") as mock_api:
            with patch("core.commute_calculator.keyring_manager.get_key", return_value="test-key"):
                mock_api.return_value = [22]
                result = commute_calculator.calculate_single(
                    32.7459, -96.4685, 32.7767, -96.7970)
                assert result == 22
                cache_key = (32.7459, -96.4685, 32.7767, -96.7970)
                assert cache_key in commute_calculator._cache

    def test_cache_hit_skips_api_call(self):
        """Second call with same coords should use cache, not API."""
        commute_calculator._cache[(32.7459, -96.4685, 32.7767, -96.7970)] = 19

        with patch("core.commute_calculator._call_api") as mock_api:
            result = commute_calculator.calculate_single(
                32.7459, -96.4685, 32.7767, -96.7970)
            assert result == 19
            mock_api.assert_not_called()

    def test_calculate_single_returns_none_on_error(self):
        """API failure should return None, not raise."""
        with patch("core.commute_calculator._call_api",
                   side_effect=Exception("Network error")):
            with patch("core.commute_calculator.keyring_manager.get_key", return_value="key"):
                result = commute_calculator.calculate_single(
                    32.7459, -96.4685, 32.7767, -96.7970)
                assert result is None


class TestCalculateBatch:

    def setup_method(self):
        commute_calculator.clear_cache()

    def test_batch_skips_jobs_without_coords(self):
        """Jobs without coordinates should be skipped silently."""
        jobs = [_job(job_id="no_loc", latitude=None, longitude=None)]
        with patch("core.commute_calculator._call_api") as mock_api:
            with patch("core.commute_calculator._load_db_cache", return_value=jobs):
                with patch("core.commute_calculator._save_db_cache"):
                    result = commute_calculator.calculate_batch(
                        32.7459, -96.4685, jobs)
                    mock_api.assert_not_called()
                    assert result[0].commute_minutes is None

    def test_batch_uses_cache_for_known_jobs(self):
        """Jobs already in cache should not trigger an API call."""
        job = _job(latitude=32.7767, longitude=-96.7970)
        commute_calculator._cache[(32.7459, -96.4685, 32.7767, -96.7970)] = 19

        with patch("core.commute_calculator._call_api") as mock_api:
            commute_calculator.calculate_batch(32.7459, -96.4685, [job])
            mock_api.assert_not_called()
        assert job.commute_minutes == 19

    def test_batch_calls_progress_callback(self):
        """progress_callback should be called for each completed job."""
        job = _job(latitude=32.7767, longitude=-96.7970)
        commute_calculator._cache[(32.7459, -96.4685, 32.7767, -96.7970)] = 19

        calls = []
        commute_calculator.calculate_batch(
            32.7459, -96.4685, [job],
            progress_callback=lambda done, total: calls.append((done, total)))
        assert len(calls) == 1
        assert calls[0] == (1, 1)

    def test_batch_returns_listings(self):
        """calculate_batch should return the listings list."""
        jobs = [_job()]
        commute_calculator._cache[(32.7459, -96.4685, 32.7767, -96.7970)] = 25
        result = commute_calculator.calculate_batch(32.7459, -96.4685, jobs)
        assert result is jobs  # Same list returned


# ── _call_api parsing ─────────────────────────────────────────────────────────

class TestCallApi:

    def test_converts_seconds_to_minutes(self):
        """ORS returns seconds; result should be in minutes."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "durations": [[0, 1140, 2700]]  # 19 min, 45 min (in seconds)
        }
        mock_response.raise_for_status = MagicMock()

        with patch("core.commute_calculator.requests.post",
                   return_value=mock_response):
            with patch("core.commute_calculator.keyring_manager.get_key",
                       return_value="test-ors-key"):
                result = commute_calculator._call_api(
                    32.7459, -96.4685,
                    [(32.7767, -96.7970), (32.8998, -97.0641)],
                )
        assert result[0] == 19   # 1140s / 60 = 19
        assert result[1] == 45   # 2700s / 60 = 45

    def test_none_returned_for_unreachable_destination(self):
        """ORS returns null for destinations it can't route to."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "durations": [[0, None]]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("core.commute_calculator.requests.post",
                   return_value=mock_response):
            with patch("core.commute_calculator.keyring_manager.get_key",
                       return_value="test-key"):
                result = commute_calculator._call_api(
                    32.7459, -96.4685, [(99.0, 99.0)])
        assert result[0] is None

    def test_raises_on_missing_api_key(self):
        """Should raise ValueError if no ORS key is in keyring."""
        with patch("core.commute_calculator.keyring_manager.get_key",
                   return_value=None):
            with pytest.raises(ValueError, match="API key not set"):
                commute_calculator._call_api(32.7, -96.4, [(32.8, -96.5)])

    def test_raises_on_401(self):
        """Should raise HTTPError on 401 response."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.raise_for_status = MagicMock()

        with patch("core.commute_calculator.requests.post",
                   return_value=mock_response):
            with patch("core.commute_calculator.keyring_manager.get_key",
                       return_value="bad-key"):
                import requests
                with pytest.raises(requests.HTTPError):
                    commute_calculator._call_api(32.7, -96.4, [(32.8, -96.5)])

    def test_lon_lat_order_sent_to_ors(self):
        """ORS expects [longitude, latitude], not [latitude, longitude]."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"durations": [[0, 600]]}
        mock_response.raise_for_status = MagicMock()

        with patch("core.commute_calculator.requests.post",
                   return_value=mock_response) as mock_post:
            with patch("core.commute_calculator.keyring_manager.get_key",
                       return_value="key"):
                commute_calculator._call_api(32.7459, -96.4685, [(32.7767, -96.7970)])

        payload = mock_post.call_args.kwargs["json"]
        origin = payload["locations"][0]
        dest   = payload["locations"][1]
        # Lon first, lat second
        assert origin == [-96.4685, 32.7459]
        assert dest   == [-96.7970, 32.7767]
