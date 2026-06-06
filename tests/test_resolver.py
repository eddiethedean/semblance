"""Tests for semblance.resolver - resolve_overrides, _to_datetime, get_output_model_for_type."""

from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel

from semblance.links import FromCookie, FromHeader
from semblance.resolver import (
    _to_datetime,
    get_output_model_for_type,
    resolve_overrides,
)
from tests.example_models import User, UserQuery


def test_resolve_overrides_from_header_and_from_cookie():
    class OutputWithHeaderAndCookie(BaseModel):
        request_id: Annotated[str, FromHeader("X-Request-Id")]
        session: Annotated[str, FromCookie("session_id")]

    class AnyInput(BaseModel):
        name: str = "x"

    class MockHeaders:
        def __init__(self, d: dict):
            self._d = d

        def get(self, name: str, default: str | None = None) -> str | None:
            return self._d.get(name, default)

    class MockRequest:
        def __init__(self, headers: dict | None = None, cookies: dict | None = None):
            self.headers = MockHeaders(headers or {})
            self.cookies = cookies or {}

    req = MockRequest(
        headers={"X-Request-Id": "req-123"},
        cookies={"session_id": "sess-456"},
    )
    overrides = resolve_overrides(
        OutputWithHeaderAndCookie,
        AnyInput,
        AnyInput(name="a"),
        request=req,
    )
    assert overrides["request_id"] == "req-123"
    assert overrides["session"] == "sess-456"


def test_resolve_overrides_from_header_without_request_no_override():
    class OutputWithHeader(BaseModel):
        request_id: Annotated[str, FromHeader("X-Request-Id")]

    class AnyInput(BaseModel):
        name: str = "x"

    overrides = resolve_overrides(
        OutputWithHeader, AnyInput, AnyInput(name="a"), request=None
    )
    assert overrides == {}


def test_resolve_overrides_skips_fields_without_metadata():
    class SimpleOutput(BaseModel):
        name: str
        count: int

    overrides = resolve_overrides(SimpleOutput, UserQuery, UserQuery(name="x"))
    assert overrides == {}


def test_date_range_from_end_equals_start_returns_start():
    class QueryWithSameDates(BaseModel):
        name: str = "same"
        start_date: date = date(2024, 6, 15)
        end_date: date = date(2024, 6, 15)

    overrides = resolve_overrides(User, QueryWithSameDates, QueryWithSameDates())
    result = overrides["created_at"]()
    assert result == datetime(2024, 6, 15, 0, 0, 0)


def test_date_range_from_end_before_start():
    class QueryWithReversedDates(BaseModel):
        name: str = "reversed"
        start_date: date = date(2024, 12, 31)
        end_date: date = date(2024, 1, 1)

    overrides = resolve_overrides(
        User, QueryWithReversedDates, QueryWithReversedDates()
    )
    assert overrides["created_at"]() == datetime(2024, 12, 31, 0, 0, 0)


def test_to_datetime_converts_date_and_iso_string():
    assert _to_datetime(date(2024, 3, 15)) == datetime(2024, 3, 15, 0, 0, 0)
    assert _to_datetime("2024-06-15T14:30:00") == datetime(2024, 6, 15, 14, 30, 0)
    assert _to_datetime("not-a-date") is None


def test_get_output_model_for_type_single_model():
    assert get_output_model_for_type(User) is User


def test_get_output_model_for_type_list_model():
    assert get_output_model_for_type(list[User]) is User


def test_get_output_model_for_type_invalid():
    assert get_output_model_for_type(list) is None
    assert get_output_model_for_type(str) is None
