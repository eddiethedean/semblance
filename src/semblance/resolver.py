"""
Constraint resolution engine.

Inspects output models for dependency metadata (FromInput, DateRangeFrom,
WhenInput, ComputedFrom, or registered custom links), resolves against the
validated request input, and produces a dict of field overrides (values or
callables) for the Polyfactory layer.
"""

import random
from collections.abc import Callable
from datetime import date, datetime, timedelta
from typing import Any, Protocol, get_origin

from pydantic import BaseModel
from starlette.requests import Request

from semblance.links import (
    ComputedFrom,
    DateRangeFrom,
    FromCookie,
    FromHeader,
    FromInput,
    WhenInput,
    get_field_metadata,
)
from semblance.plugins import is_registered


class _RandomLike(Protocol):
    def uniform(self, a: float, b: float) -> float: ...


def _make_random_datetime_closure(
    start_dt: datetime, end_dt: datetime, rng: _RandomLike
) -> Callable[[], datetime]:
    def fn(
        s: datetime = start_dt,
        e: datetime = end_dt,
        r: _RandomLike = rng,
    ) -> datetime:
        delta = e - s
        if delta.total_seconds() <= 0:
            return s
        sec = r.uniform(0, delta.total_seconds())
        return s + timedelta(seconds=sec)

    return fn


def _get_nested_model(field_annotation: object) -> type[BaseModel] | None:
    """Extract BaseModel from field annotation (handles Optional[BaseModel])."""
    origin = get_origin(field_annotation)
    if origin is not None:
        args = getattr(field_annotation, "__args__", ())
        for arg in args:
            if isinstance(arg, type) and issubclass(arg, BaseModel):
                return arg
        return None
    if isinstance(field_annotation, type) and issubclass(field_annotation, BaseModel):
        return field_annotation
    return None


def resolve_overrides(
    output_model: type[BaseModel],
    input_model: type[BaseModel],
    input_instance: BaseModel,
    seed: int | None = None,
    request: Request | None = None,
) -> dict[str, Any]:
    """
    Build a dict of field overrides for the output model.

    Walks output_model fields, inspects Annotated metadata for links, and
    resolves each against input_instance (and optionally request for
    FromHeader/FromCookie). Returns mapping field_name -> value or callable() -> value.
    For nested BaseModel fields, value is {_nested: model, _overrides: dict}.
    When seed is set, uses a seeded RNG for determinism.
    """
    overrides: dict[str, Any] = {}
    input_data = input_instance.model_dump()
    rng = random.Random(seed) if seed is not None else random

    for name in output_model.model_fields:
        field_info = output_model.model_fields.get(name)
        if field_info is not None:
            nested_model = _get_nested_model(
                getattr(field_info, "annotation", None) or object
            )
            if nested_model is not None:
                nested_overrides = resolve_overrides(
                    nested_model,
                    input_model,
                    input_instance,
                    seed=seed,
                    request=request,
                )
                overrides[name] = {
                    "_nested": nested_model,
                    "_overrides": nested_overrides,
                }
                continue

        meta = get_field_metadata(output_model, name)
        if meta is None:
            continue

        if isinstance(meta, FromHeader):
            if request is not None:
                val = request.headers.get(meta.name)
                if val is not None:
                    overrides[name] = val
        elif isinstance(meta, FromCookie):
            if request is not None:
                val = request.cookies.get(meta.name)
                if val is not None:
                    overrides[name] = val
        elif isinstance(meta, FromInput):
            val = input_data.get(meta.field)
            # When val is None (missing or optional input), no override is applied;
            # Polyfactory will generate a value for the field.
            if val is not None:
                overrides[name] = val

        elif isinstance(meta, WhenInput):
            if input_data.get(meta.condition_field) == meta.condition_value:
                inner = meta.then_link
                if isinstance(inner, FromInput):
                    val = input_data.get(inner.field)
                    if val is not None:
                        overrides[name] = val
                elif isinstance(inner, DateRangeFrom):
                    start_val = input_data.get(inner.start)
                    end_val = input_data.get(inner.end)
                    if start_val is not None and end_val is not None:
                        start = _to_datetime(start_val)
                        end = _to_datetime(end_val)
                        if start is not None and end is not None:
                            overrides[name] = _make_random_datetime_closure(
                                start, end, rng
                            )

        elif isinstance(meta, DateRangeFrom):
            start_val = input_data.get(meta.start)
            end_val = input_data.get(meta.end)
            if start_val is not None and end_val is not None:
                start = _to_datetime(start_val)
                end = _to_datetime(end_val)
                if start is not None and end is not None:
                    overrides[name] = _make_random_datetime_closure(start, end, rng)

        elif isinstance(meta, ComputedFrom):
            overrides[name] = {"_computed": meta.fields, "_fn": meta.fn}

        elif is_registered(meta):
            val = meta.resolve(input_data, rng)
            if val is not None:
                overrides[name] = val

    return overrides


def _to_datetime(value: Any) -> datetime | None:
    """Convert a value to datetime (handles date, datetime, or ISO string)."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date) and not isinstance(value, datetime):
        return datetime.combine(value, datetime.min.time())
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            pass
    return None


def get_output_model_for_type(annotation: type) -> type[BaseModel] | None:
    """
    Resolve the concrete output model from an annotation like T or list[T].
    Returns the inner model for list[T], or the type itself for a single model.
    """
    origin = get_origin(annotation)
    if origin is list:
        args = getattr(annotation, "__args__", ())
        if args and isinstance(args[0], type):
            return args[0]
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return annotation
    return None
