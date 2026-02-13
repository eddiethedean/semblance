"""Tests for semblance.links (FromInput, DateRangeFrom, get_field_metadata)."""

from datetime import date, datetime
from typing import Annotated

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


def test_get_field_metadata_fallback_to_model_fields():
    """get_field_metadata falls back to model_fields when get_type_hints fails."""

    # Create a model that might trigger fallback (e.g. forward ref or edge case)
    # When get_type_hints fails, we fall back to model_fields[field].annotation
    class ModelWithAnnotation(BaseModel):
        x: Annotated[int, "custom"] = 0

    # Field without Semblance metadata - should return None
    meta = get_field_metadata(ModelWithAnnotation, "x")
    assert meta is None


def test_get_field_metadata_field_not_in_model_returns_none():
    """get_field_metadata returns None for non-existent field."""
    assert get_field_metadata(User, "nonexistent") is None
