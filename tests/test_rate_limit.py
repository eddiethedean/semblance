"""Unit tests for semblance.rate_limit - RateLimiter and get_limiter."""

import time
from types import SimpleNamespace

import pytest

from semblance.rate_limit import RateLimiter, get_limiter


def test_separate_apis_have_independent_rate_limits(monkeypatch):
    from semblance import SemblanceAPI
    from semblance.testing import test_client as make_client
    from tests.example_models import User, UserQuery

    monkeypatch.setattr(
        "semblance.rate_limit.time", SimpleNamespace(monotonic=lambda: 100.0)
    )
    first = SemblanceAPI()
    second = SemblanceAPI()
    for api in (first, second):
        api.get("/users", input=UserQuery, output=User, rate_limit=1)(lambda: None)

    with make_client(first.as_fastapi()) as first_client:
        with make_client(second.as_fastapi()) as second_client:
            assert first_client.get("/users").status_code == 200
            assert first_client.get("/users").status_code == 429
            assert second_client.get("/users").status_code == 200
            assert second_client.get("/users").status_code == 429


class TestRateLimiter:
    """Direct unit tests for RateLimiter.check_and_record."""

    def test_limit_zero_always_allows(self):
        limiter = RateLimiter()
        for _ in range(10):
            assert limiter.check_and_record("/x", "GET", 0) is True
        assert limiter.check_and_record("/x", "GET", -1) is True

    def test_at_limit_allows_then_denies(self):
        limiter = RateLimiter()
        assert limiter.check_and_record("/users", "GET", 2) is True
        assert limiter.check_and_record("/users", "GET", 2) is True
        assert limiter.check_and_record("/users", "GET", 2) is False
        assert limiter.check_and_record("/users", "GET", 2) is False

    @pytest.mark.slow
    def test_after_window_allows_again(self):
        limiter = RateLimiter()
        assert limiter.check_and_record("/a", "POST", 1) is True
        assert limiter.check_and_record("/a", "POST", 1) is False
        time.sleep(1.1)
        assert limiter.check_and_record("/a", "POST", 1) is True

    def test_different_keys_independent(self):
        limiter = RateLimiter()
        assert limiter.check_and_record("/users", "GET", 1) is True
        assert limiter.check_and_record("/users", "GET", 1) is False
        assert limiter.check_and_record("/users", "POST", 1) is True
        assert limiter.check_and_record("/items", "GET", 1) is True

    @pytest.mark.slow
    def test_sliding_window_prunes_old_timestamps(self):
        limiter = RateLimiter()
        assert limiter.check_and_record("/x", "GET", 1) is True
        time.sleep(1.1)
        assert limiter.check_and_record("/x", "GET", 1) is True
        assert limiter.check_and_record("/x", "GET", 1) is False


class TestGetLimiter:
    def test_get_limiter_returns_singleton(self):
        a = get_limiter()
        b = get_limiter()
        assert a is b
