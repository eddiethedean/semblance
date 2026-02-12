"""
Constraint resolution engine.

Inspects output models for dependency metadata, resolves against the request input,
and produces a dict of field overrides (values or callables) for Polyfactory.
"""

import random
from datetime import date, datetime, timedelta
from typing import Any, get_origin

from pydantic import BaseModel

from semblance.links import DateRangeFrom, FromInput, get_field_metadata


def resolve_overrides(
    output_model: type[BaseModel],
    input_model: type[BaseModel],
    input_instance: BaseModel,
    seed: int | None = None,
) -> dict[str, Any]:
    """
    Build a dict of field overrides for the output model based on
    dependency metadata and the validated input instance.

    Returns mapping: field_name -> value or callable() -> value.
    When seed is set, DateRangeFrom uses a seeded RNG for determinism.
    """
    overrides: dict[str, Any] = {}
    input_data = input_instance.model_dump()
    rng = random.Random(seed) if seed is not None else random

    for name in output_model.model_fields:
        meta = get_field_metadata(output_model, name)
        if meta is None:
            continue

        if isinstance(meta, FromInput):
            val = input_data.get(meta.field)
            # When val is None (missing or optional input), no override is applied;
            # Polyfactory will generate a value for the field.
            if val is not None:
                overrides[name] = val

        elif isinstance(meta, DateRangeFrom):
            start_val = input_data.get(meta.start)
            end_val = input_data.get(meta.end)
            if start_val is not None and end_val is not None:
                start = _to_datetime(start_val)
                end = _to_datetime(end_val)
                if start is not None and end is not None:
                    _rng = rng

                    def make_random_datetime(
                        s: datetime = start,
                        e: datetime = end,
                        r: Any = _rng,
                    ) -> datetime:
                        # When end <= start, returns start (no valid range to sample).
                        delta = e - s
                        if delta.total_seconds() <= 0:
                            return s
                        sec = r.uniform(0, delta.total_seconds())
                        return s + timedelta(seconds=sec)

                    overrides[name] = make_random_datetime

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
