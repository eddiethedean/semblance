"""Unit tests for semblance.rate_limit - RateLimiter and get_limiter."""

import time

import pytest

from semblance.rate_limit import RateLimiter, get_limiter


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
