"""Tests for simulation options: error rate, latency, jitter."""

import time

import pytest

from semblance import SemblanceAPI
from semblance.testing import test_client as make_client
from tests.example_models import User, UserQuery


def test_error_rate_zero_returns_success():
    api = SemblanceAPI()
    api.get("/users", input=UserQuery, output=list[User], error_rate=0)(lambda: None)
    client = make_client(api.as_fastapi())
    for _ in range(5):
        assert client.get("/users?name=x").status_code == 200


def test_error_rate_one_returns_errors():
    api = SemblanceAPI()
    api.get(
        "/users",
        input=UserQuery,
        output=list[User],
        error_rate=1.0,
        error_codes=[418],
    )(lambda: None)
    client = make_client(api.as_fastapi())
    assert client.get("/users?name=x").status_code == 418


def test_error_rate_probabilistic_with_seed():
    """With fixed API seed, error_rate=0.5 produces configured error codes."""
    api = SemblanceAPI(seed=12345)
    api.get(
        "/users",
        input=UserQuery,
        output=list[User],
        error_rate=0.5,
        error_codes=[503, 404],
    )(lambda: None)
    client = make_client(api.as_fastapi())
    statuses = {client.get("/users?name=x").status_code for _ in range(20)}
    assert statuses <= {200, 503, 404}
    assert 503 in statuses or 404 in statuses


def test_latency_ms_adds_delay():
    api = SemblanceAPI()
    api.get("/users", input=UserQuery, output=list[User], list_count=1, latency_ms=50)(
        lambda: None
    )
    client = make_client(api.as_fastapi())
    start = time.perf_counter()
    r = client.get("/users?name=latency")
    elapsed = time.perf_counter() - start
    assert r.status_code == 200
    assert elapsed >= 0.045


def test_latency_zero_no_delay():
    api = SemblanceAPI()
    api.get("/users", input=UserQuery, output=list[User], list_count=1)(lambda: None)
    client = make_client(api.as_fastapi())
    start = time.perf_counter()
    r = client.get("/users?name=fast")
    elapsed = time.perf_counter() - start
    assert r.status_code == 200
    assert elapsed < 0.1


@pytest.mark.slow
def test_jitter_ms_adds_bounded_delay():
    api = SemblanceAPI(seed=42)
    api.get(
        "/users",
        input=UserQuery,
        output=list[User],
        list_count=1,
        latency_ms=100,
        jitter_ms=50,
    )(lambda: None)
    client = make_client(api.as_fastapi())
    start = time.perf_counter()
    r = client.get("/users?name=jitter")
    elapsed = time.perf_counter() - start
    assert r.status_code == 200
    assert elapsed >= 0.045
    assert elapsed < 0.25
