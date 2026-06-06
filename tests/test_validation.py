"""Tests for link validation at as_fastapi() and validate_specs()."""

from typing import Annotated

import pytest
from pydantic import BaseModel

from semblance import ComputedFrom, DateRangeFrom, FromInput, SemblanceAPI, WhenInput
from semblance.validation import get_duplicate_endpoint_errors, validate_specs


def test_validate_specs_valid_from_input():
    class Query(BaseModel):
        name: str = "x"

    class Out(BaseModel):
        name: Annotated[str, FromInput("name")]

    api = SemblanceAPI()
    api.get("/users", input=Query, output=Out)(lambda: None)
    assert validate_specs(api.get_endpoint_specs()) == []


def test_validate_specs_invalid_from_input_missing_field():
    class Query(BaseModel):
        name: str = "x"

    class OutWithLink(BaseModel):
        name: Annotated[str, FromInput("typo")]

    api = SemblanceAPI()
    api.get("/users", input=Query, output=OutWithLink)(lambda: None)
    errors = validate_specs(api.get_endpoint_specs())
    assert len(errors) == 1
    assert "typo" in errors[0]
    assert "GET" in errors[0]
    assert "/users" in errors[0]


def test_as_fastapi_raises_on_invalid_from_input():
    class Query(BaseModel):
        name: str = "x"

    class Out(BaseModel):
        name: Annotated[str, FromInput("wrong_field")]

    api = SemblanceAPI(validate_links=True)
    api.get("/users", input=Query, output=Out)(lambda: None)
    with pytest.raises(ValueError) as exc_info:
        api.as_fastapi()
    msg = str(exc_info.value)
    assert "Link validation failed" in msg
    assert "wrong_field" in msg
    assert "/users" in msg


def test_validate_specs_valid_computed_from():
    class Query(BaseModel):
        first: str = "a"
        last: str = "b"

    class Out(BaseModel):
        first: Annotated[str, FromInput("first")]
        last: Annotated[str, FromInput("last")]
        full: Annotated[str, ComputedFrom(("first", "last"), lambda a, b: f"{a} {b}")]

    api = SemblanceAPI()
    api.get("/user", input=Query, output=Out)(lambda: None)
    assert validate_specs(api.get_endpoint_specs()) == []


def test_validate_specs_invalid_computed_from_missing_dependency():
    class Query(BaseModel):
        name: str = "x"

    class Out(BaseModel):
        name: Annotated[str, FromInput("name")]
        full: Annotated[str, ComputedFrom(("nonexistent",), lambda x: x)]

    api = SemblanceAPI()
    api.get("/user", input=Query, output=Out)(lambda: None)
    errors = validate_specs(api.get_endpoint_specs())
    assert len(errors) == 1
    assert "nonexistent" in errors[0]
    assert "ComputedFrom" in errors[0]


def test_validate_specs_invalid_date_range_from():
    from datetime import datetime

    class Query(BaseModel):
        name: str = "x"

    class Out(BaseModel):
        name: Annotated[str, FromInput("name")]
        created_at: Annotated[datetime, DateRangeFrom("missing_start", "missing_end")]

    api = SemblanceAPI()
    api.get("/users", input=Query, output=Out)(lambda: None)
    errors = validate_specs(api.get_endpoint_specs())
    assert len(errors) == 2
    assert any("missing_start" in e for e in errors)
    assert any("missing_end" in e for e in errors)


def test_validate_specs_invalid_when_input():
    class Query(BaseModel):
        name: str = "x"

    class Out(BaseModel):
        status: Annotated[str, WhenInput("missing_flag", True, FromInput("status"))]

    api = SemblanceAPI()
    api.get("/user", input=Query, output=Out)(lambda: None)
    errors = validate_specs(api.get_endpoint_specs())
    assert len(errors) >= 1
    assert any("missing_flag" in e for e in errors)


def test_validate_specs_nested_model_invalid_link():
    class Query(BaseModel):
        city: str = "NYC"

    class Address(BaseModel):
        city: Annotated[str, FromInput("typo_city")]

    class Out(BaseModel):
        address: Address

    api = SemblanceAPI()
    api.get("/user", input=Query, output=Out)(lambda: None)
    errors = validate_specs(api.get_endpoint_specs())
    assert len(errors) == 1
    assert "address." in errors[0] or "address" in errors[0]
    assert "typo_city" in errors[0]


def test_get_duplicate_endpoint_errors():
    class Query(BaseModel):
        name: str = "x"

    class Out(BaseModel):
        name: str

    api = SemblanceAPI()
    api.get("/dup", input=Query, output=Out)(lambda: None)
    api.get("/dup", input=Query, output=Out)(lambda: None)
    errors = get_duplicate_endpoint_errors(api.get_endpoint_specs())
    assert len(errors) == 1
    assert "Duplicate GET" in errors[0]
    assert "/dup" in errors[0]
