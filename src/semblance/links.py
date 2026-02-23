"""
Dependency metadata and DSL for model-embedded constraints.

Declare how output fields relate to input using typing.Annotated and link
types (FromInput, DateRangeFrom, WhenInput, ComputedFrom). The resolver
builds Polyfactory overrides from these metadata; custom links are supported
via the plugin system (register_link).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FromInput:
    """Bind this output field to the value of a request input field by name.

    Use with typing.Annotated, e.g. Annotated[str, FromInput("name")].
    When the input field is None (missing or optional), no override is applied
    and Polyfactory generates a value for the field.
    """

    field: str


@dataclass(frozen=True)
class DateRangeFrom:
    """Generate a datetime within the range defined by two date fields on input.

    Use with typing.Annotated, e.g. Annotated[datetime, DateRangeFrom("start_date", "end_date")].
    When end <= start, returns start (no valid range to sample from).
    """

    start: str
    end: str


@dataclass(frozen=True)
class WhenInput:
    """Apply the inner link only when condition_field equals condition_value.

    Use with typing.Annotated, e.g. Annotated[str, WhenInput("include_status", True, FromInput("status"))].
    When the condition is not met, no override is applied and Polyfactory
    generates a value for the field.
    """

    condition_field: str
    condition_value: Any
    then_link: FromInput | DateRangeFrom


@dataclass(frozen=True)
class ComputedFrom:
    """Compute this field from other output fields in the same model.

    Use with typing.Annotated, e.g. Annotated[str, ComputedFrom(("first", "last"), lambda a, b: f"{a} {b}")].
    The fn receives dependency values in order: fn(*[resolved[f] for f in fields]).
    Dependencies must be resolved before this field (topological order).
    """

    fields: tuple[str, ...]
    fn: Callable[..., Any]


@dataclass(frozen=True)
class FromHeader:
    """Bind this output field to a request header by name.

    Use with typing.Annotated, e.g. Annotated[str, FromHeader("X-Request-Id")].
    Requires request context when resolving (used in request handlers).
    When the header is missing, no override is applied and Polyfactory generates a value.
    """

    name: str


@dataclass(frozen=True)
class FromCookie:
    """Bind this output field to a request cookie by name.

    Use with typing.Annotated, e.g. Annotated[str, FromCookie("session_id")].
    Requires request context when resolving (used in request handlers).
    When the cookie is missing, no override is applied and Polyfactory generates a value.
    """

    name: str


def get_field_metadata(model_class: type, field_name: str) -> Any | None:
    """
    Extract dependency metadata from a Pydantic model field's Annotated type.

    Returns the first metadata that looks like a Semblance link (FromInput,
    DateRangeFrom, WhenInput, ComputedFrom, FromHeader, FromCookie) or a registered custom link.
    Returns None if no link metadata is found.
    """
    import typing

    hint = None
    try:
        # Prefer get_type_hints so we get full Annotated[T, ...] with __metadata__
        annotations = typing.get_type_hints(model_class, include_extras=True)
        hint = annotations.get(field_name)
    except Exception:
        pass
    if (
        hint is None
        and hasattr(model_class, "model_fields")
        and field_name in model_class.model_fields
    ):
        hint = getattr(model_class.model_fields[field_name], "annotation", None)
    if hint is None:
        return None

    # Annotated[T, x, y, ...] has __metadata__ as tuple of the extra args
    if hasattr(hint, "__metadata__"):
        from semblance.plugins import is_registered

        for meta in hint.__metadata__:
            if isinstance(
                meta,
                (
                    FromInput,
                    DateRangeFrom,
                    WhenInput,
                    ComputedFrom,
                    FromHeader,
                    FromCookie,
                ),
            ):
                return meta
            if is_registered(meta):
                return meta
    return None
