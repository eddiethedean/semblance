"""Tests for semblance.factory - build_response, pagination, edge cases."""

from datetime import date

import pytest
from pydantic import BaseModel

from semblance.factory import (
    build_list,
    build_one,
    build_response,
)
from semblance.pagination import PaginatedResponse
from tests.example_models import User, UserQuery


def test_build_one_with_seed_produces_deterministic_result():
    """build_one with seed produces same output across calls."""
    query = UserQuery(name="deterministic")
    r1 = build_one(User, UserQuery, query, seed=42)
    r2 = build_one(User, UserQuery, query, seed=42)
    assert r1.name == r2.name == "deterministic"
    assert r1.created_at == r2.created_at


def test_build_list_with_seed_produces_deterministic_results():
    """build_list with seed produces same outputs across calls."""
    query = UserQuery(name="list_seed")
    r1 = build_list(User, UserQuery, query, count=2, seed=99)
    r2 = build_list(User, UserQuery, query, count=2, seed=99)
    assert [u.name for u in r1] == [u.name for u in r2]
    assert [u.created_at for u in r1] == [u.created_at for u in r2]


def test_build_response_single_with_seed():
    """build_response for single model with seed uses seed_random."""
    query = UserQuery(name="single_seed")
    r1 = build_response(User, UserQuery, query, seed=123)
    r2 = build_response(User, UserQuery, query, seed=123)
    assert r1.name == r2.name == "single_seed"
    assert r1.created_at == r2.created_at


def test_pagination_limit_offset_fallback_on_invalid_limit():
    """Pagination uses fallback when limit cannot be coerced to int."""

    class BadLimitQuery(BaseModel):
        limit: str = "not-a-number"
        offset: int = 0
        name: str = "x"

    result = build_response(
        PaginatedResponse[User],
        BadLimitQuery,
        BadLimitQuery(),
        seed=1,
    )
    assert result.limit == 10  # fallback
    assert result.offset == 0


def test_pagination_limit_offset_fallback_on_invalid_offset():
    """Pagination uses fallback when offset cannot be coerced to int."""

    class BadOffsetQuery(BaseModel):
        limit: int = 5
        offset: str = "invalid"
        name: str = "x"

    result = build_response(
        PaginatedResponse[User],
        BadOffsetQuery,
        BadOffsetQuery(),
        seed=1,
    )
    assert result.limit == 5
    assert result.offset == 0  # fallback


def test_build_response_invalid_single_model_raises():
    """build_response with non-BaseModel single type raises TypeError."""
    query = UserQuery(name="x")
    with pytest.raises(TypeError, match="Invalid output type"):
        build_response(int, UserQuery, query)


def test_build_response_list_output():
    """build_response for list[Model] returns list of instances."""
    query = UserQuery(name="list_test")
    result = build_response(list[User], UserQuery, query, list_count=3, seed=1)
    assert isinstance(result, list)
    assert len(result) == 3
    for item in result:
        assert item.name == "list_test"


def test_evaluate_overrides_callable_path():
    """build_one evaluates callables from DateRangeFrom in overrides."""
    query = UserQuery(
        name="callable_test", start_date=date(2024, 1, 1), end_date=date(2024, 12, 31)
    )
    result = build_one(User, UserQuery, query)
    assert result.name == "callable_test"
    assert result.created_at is not None


def test_build_list_with_filter_by():
    """build_list with filter_by returns items matching input field value."""
    query = UserQuery(name="alice")
    result = build_list(User, UserQuery, query, count=3, filter_by="name", seed=1)
    assert len(result) == 3
    for item in result:
        assert item.name == "alice"
