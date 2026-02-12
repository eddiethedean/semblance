"""
Dependency metadata and DSL for model-embedded constraints.

Relationships are declared inside output models using typing.Annotated.
Dependencies live with the fields they affect.
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FromInput:
    """Bind this field to the value of a request input field by name."""

    field: str


@dataclass(frozen=True)
class DateRangeFrom:
    """Generate a datetime within the range defined by two date fields on the input."""

    start: str
    end: str


def get_field_metadata(model_class: type, field_name: str) -> Any | None:
    """
    Extract dependency metadata from a Pydantic model field's Annotated type.
    Returns the first non-type annotation that looks like a Semblance link.
    """
    import typing

    hint = None
    try:
        # Prefer get_type_hints so we get full Annotated[T, ...] with __metadata__
        annotations = typing.get_type_hints(model_class, include_extras=True)
        hint = annotations.get(field_name)
    except Exception:
        pass
    if hint is None and hasattr(model_class, "model_fields") and field_name in model_class.model_fields:
        hint = getattr(model_class.model_fields[field_name], "annotation", None)
    if hint is None:
        return None

    # Annotated[T, x, y, ...] has __metadata__ as tuple of the extra args
    if hasattr(hint, "__metadata__"):
        for meta in hint.__metadata__:
            if isinstance(meta, (FromInput, DateRangeFrom)):
                return meta
    return None
