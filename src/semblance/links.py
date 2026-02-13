"""
Dependency metadata and DSL for model-embedded constraints.

Relationships are declared inside output models using typing.Annotated.
Dependencies live with the fields they affect.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class FromInput:
    """Bind this field to the value of a request input field by name.

    When the input field is None (missing or optional), no override is applied
    and Polyfactory generates a value for the field.
    """

    field: str


@dataclass(frozen=True)
class DateRangeFrom:
    """Generate a datetime within the range defined by two date fields on the input.

    When end <= start, returns start (no valid range to sample from).
    """

    start: str
    end: str


@dataclass(frozen=True)
class WhenInput:
    """Apply the inner link only when condition_field equals condition_value.

    When the condition is not met, no override is applied and Polyfactory
    generates a value for the field.
    """

    condition_field: str
    condition_value: Any
    then_link: FromInput | DateRangeFrom


@dataclass(frozen=True)
class ComputedFrom:
    """Compute this field from other output fields in the same model.

    The fn receives dependency values in order: fn(*[resolved[f] for f in fields]).
    Dependencies must be resolved before this field (topological order).
    """

    fields: tuple[str, ...]
    fn: Callable[..., Any]


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
        from semblance.plugins import is_registered

        for meta in hint.__metadata__:
            if isinstance(meta, (FromInput, DateRangeFrom, WhenInput, ComputedFrom)):
                return meta
            if is_registered(meta):
                return meta
    return None
