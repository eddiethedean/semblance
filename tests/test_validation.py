"""Tests for link validation at as_fastapi() and validate_specs()."""

import pytest
from pydantic import BaseModel

from semblance import FromInput, SemblanceAPI
from semblance.validation import validate_specs


def test_validate_specs_valid_from_input():
    """Valid FromInput (field exists on input) produces no errors."""
    from typing import Annotated

    class Query(BaseModel):
        name: str = "x"

    class Out(BaseModel):
        name: Annotated[str, FromInput("name")]

    api = SemblanceAPI()
    api.get("/users", input=Query, output=Out)(lambda: None)
    errors = validate_specs(api._specs)
    assert errors == []


def test_validate_specs_invalid_from_input_missing_field():
    """FromInput referencing missing input field produces an error."""
    from typing import Annotated

    class Query(BaseModel):
        name: str = "x"

    class OutWithLink(BaseModel):
        name: Annotated[str, FromInput("typo")]

    api = SemblanceAPI()
    api.get("/users", input=Query, output=OutWithLink)(lambda: None)
    errors = validate_specs(api._specs)
    assert len(errors) == 1
    assert "typo" in errors[0]
    assert "GET" in errors[0]
    assert "/users" in errors[0]
    assert "name" in errors[0]


def test_as_fastapi_raises_on_invalid_from_input():
    """as_fastapi() raises ValueError with path and field when FromInput is invalid and validate_links=True."""
    from typing import Annotated

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
    """ComputedFrom with existing output fields produces no errors."""
    from typing import Annotated

    from semblance import ComputedFrom

    class Query(BaseModel):
        first: str = "a"
        last: str = "b"

    class Out(BaseModel):
        first: Annotated[str, FromInput("first")]
        last: Annotated[str, FromInput("last")]
        full: Annotated[str, ComputedFrom(("first", "last"), lambda a, b: f"{a} {b}")]

    api = SemblanceAPI()
    api.get("/user", input=Query, output=Out)(lambda: None)
    errors = validate_specs(api._specs)
    assert errors == []


def test_validate_specs_invalid_computed_from_missing_dependency():
    """ComputedFrom referencing missing output field produces an error."""
    from typing import Annotated

    from semblance import ComputedFrom

    class Query(BaseModel):
        name: str = "x"

    class Out(BaseModel):
        name: Annotated[str, FromInput("name")]
        full: Annotated[str, ComputedFrom(("nonexistent",), lambda x: x)]

    api = SemblanceAPI()
    api.get("/user", input=Query, output=Out)(lambda: None)
    errors = validate_specs(api._specs)
    assert len(errors) == 1
    assert "nonexistent" in errors[0]
    assert "ComputedFrom" in errors[0]
