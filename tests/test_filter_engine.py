"""
tests/test_filter_engine.py
=============================
Tests for core/filter_engine.py.
Covers: keyword filtering, radius filtering, work type, experience level.
"""
import pytest
from core.filter_engine import filter_by_keywords, filter_by_work_type, filter_by_radius
from core.job_model import JobListing


def _make_job(**kwargs) -> JobListing:
    defaults = dict(job_id="test_1", provider="test", title="Analyst",
                    company="Acme", location="Dallas, TX")
    defaults.update(kwargs)
    return JobListing(**defaults)


def test_keyword_filter_matches_title():
    jobs = [_make_job(title="SOC Analyst"), _make_job(title="Data Engineer")]
    result = filter_by_keywords(jobs, ["SOC"])
    # TODO: Assert only the SOC Analyst is returned
    raise NotImplementedError


def test_keyword_filter_empty_returns_all():
    jobs = [_make_job(), _make_job(title="Engineer")]
    result = filter_by_keywords(jobs, [])
    # TODO: Assert all jobs returned when keywords list is empty
    raise NotImplementedError


def test_work_type_remote_filters_correctly():
    jobs = [_make_job(is_remote=True), _make_job(is_remote=False)]
    result = filter_by_work_type(jobs, "remote")
    # TODO: Assert only remote job returned
    raise NotImplementedError


def test_radius_filter_excludes_distant_jobs():
    # TODO: Create jobs with known lat/lon, assert distant ones filtered out
    raise NotImplementedError
