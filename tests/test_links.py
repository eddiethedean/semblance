"""Tests for semblance.links (FromInput, DateRangeFrom, get_field_metadata)."""

from datetime import date, datetime
from typing import Annotated

import pytest
from pydantic import BaseModel

from semblance.links import DateRangeFrom, FromInput, get_field_metadata


class UserQuery(BaseModel):
    name: str = ""
    start_date: date = date(2020, 1, 1)
    end_date: date = date(2025, 12, 31)


class User(BaseModel):
    name: Annotated[str, FromInput("name")]
    created_at: Annotated[datetime, DateRangeFrom("start_date", "end_date")]


def test_from_input_metadata():
    meta = get_field_metadata(User, "name")
    assert meta is not None
    assert isinstance(meta, FromInput)
    assert meta.field == "name"


def test_date_range_from_metadata():
    meta = get_field_metadata(User, "created_at")
    assert meta is not None
    assert isinstance(meta, DateRangeFrom)
    assert meta.start == "start_date"
    assert meta.end == "end_date"


def test_no_metadata_returns_none():
    # UserQuery has no Annotated links
    assert get_field_metadata(UserQuery, "name") is None
