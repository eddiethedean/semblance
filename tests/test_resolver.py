"""Tests for semblance.resolver - resolve_overrides, _to_datetime, get_output_model_for_type."""

from datetime import date, datetime

from pydantic import BaseModel

from semblance.resolver import (
    _to_datetime,
    get_output_model_for_type,
    resolve_overrides,
)
from tests.example_models import User, UserQuery


def test_resolve_overrides_skips_fields_without_metadata():
    """resolve_overrides skips output fields that have no Semblance metadata."""

    class SimpleOutput(BaseModel):
        name: str
        count: int

    overrides = resolve_overrides(SimpleOutput, UserQuery, UserQuery(name="x"))
    assert overrides == {}


def test_date_range_from_end_equals_start_returns_start():
    """DateRangeFrom when end <= start returns start (no range to sample)."""

    class QueryWithSameDates(BaseModel):
        name: str = "same"
        start_date: date = date(2024, 6, 15)
        end_date: date = date(2024, 6, 15)

    overrides = resolve_overrides(User, QueryWithSameDates, QueryWithSameDates())
    assert "created_at" in overrides
    callable_val = overrides["created_at"]
    assert callable(callable_val)
    result = callable_val()
    assert result == datetime(2024, 6, 15, 0, 0, 0)


def test_date_range_from_end_before_start():
    """DateRangeFrom when end < start returns start."""

    class QueryWithReversedDates(BaseModel):
        name: str = "reversed"
        start_date: date = date(2024, 12, 31)
        end_date: date = date(2024, 1, 1)

    overrides = resolve_overrides(
        User, QueryWithReversedDates, QueryWithReversedDates()
    )
    result = overrides["created_at"]()
    assert result == datetime(2024, 12, 31, 0, 0, 0)


def test_to_datetime_with_date_object():
    """_to_datetime converts date (not datetime) to datetime."""
    d = date(2024, 3, 15)
    result = _to_datetime(d)
    assert result == datetime(2024, 3, 15, 0, 0, 0)


def test_to_datetime_with_iso_string():
    """_to_datetime parses ISO format string."""
    result = _to_datetime("2024-06-15T14:30:00")
    assert result == datetime(2024, 6, 15, 14, 30, 0)


def test_to_datetime_with_z_suffix():
    """_to_datetime handles Z suffix in ISO string."""
    result = _to_datetime("2024-01-01T00:00:00Z")
    assert result is not None
    assert result.year == 2024


def test_to_datetime_invalid_string_returns_none():
    """_to_datetime returns None for invalid string."""
    assert _to_datetime("not-a-date") is None


def test_get_output_model_for_type_single_model():
    """get_output_model_for_type returns model for single BaseModel."""
    result = get_output_model_for_type(User)
    assert result is User


def test_get_output_model_for_type_list_model():
    """get_output_model_for_type returns inner model for list[Model]."""
    result = get_output_model_for_type(list[User])
    assert result is User


def test_get_output_model_for_type_bare_list_returns_none():
    """get_output_model_for_type returns None for bare list."""
    result = get_output_model_for_type(list)
    assert result is None


def test_get_output_model_for_type_non_model_returns_none():
    """get_output_model_for_type returns None for non-BaseModel type."""
    assert get_output_model_for_type(str) is None
    assert get_output_model_for_type(int) is None
