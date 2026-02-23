"""
Validation of endpoint specs before building the FastAPI app.

Validates link bindings (FromInput, DateRangeFrom, WhenInput, ComputedFrom)
so missing or invalid references surface at startup or via `semblance validate`.
"""

from typing import Any

from pydantic import BaseModel

from semblance.links import (
    ComputedFrom,
    DateRangeFrom,
    FromInput,
    WhenInput,
    get_field_metadata,
)
from semblance.resolver import _get_nested_model, get_output_model_for_type


def _validate_output_links(
    output_model: type[BaseModel],
    input_model: type[BaseModel],
    path: str,
    method: str,
    errors: list[str],
    prefix: str = "",
) -> None:
    """Recursively validate output model link metadata against input model."""
    input_fields = set(input_model.model_fields)
    output_fields = set(output_model.model_fields)

    for field_name in output_model.model_fields:
        meta = get_field_metadata(output_model, field_name)
        field_prefix = f"{prefix}{field_name}" if prefix else field_name

        if meta is None:
            # Nested BaseModel: recurse
            field_info = output_model.model_fields.get(field_name)
            if field_info is not None:
                ann = getattr(field_info, "annotation", None)
                nested = _get_nested_model(ann or object)
                if nested is not None:
                    _validate_output_links(
                        nested,
                        input_model,
                        path,
                        method,
                        errors,
                        prefix=f"{field_prefix}.",
                    )
            continue

        if isinstance(meta, FromInput):
            if meta.field not in input_fields:
                errors.append(
                    f"{method} {path}: output field {field_prefix!r} uses FromInput({meta.field!r}) "
                    f"but input model {input_model.__name__!r} has no field {meta.field!r}"
                )
        elif isinstance(meta, DateRangeFrom):
            for attr, name in (("start", meta.start), ("end", meta.end)):
                if name not in input_fields:
                    errors.append(
                        f"{method} {path}: output field {field_prefix!r} uses DateRangeFrom "
                        f"with {attr}={name!r} but input model {input_model.__name__!r} has no field {name!r}"
                    )
        elif isinstance(meta, WhenInput):
            if meta.condition_field not in input_fields:
                errors.append(
                    f"{method} {path}: output field {field_prefix!r} uses WhenInput(condition_field={meta.condition_field!r}) "
                    f"but input model {input_model.__name__!r} has no field {meta.condition_field!r}"
                )
            then_link = meta.then_link
            if isinstance(then_link, FromInput) and then_link.field not in input_fields:
                errors.append(
                    f"{method} {path}: output field {field_prefix!r} WhenInput(then_link=FromInput({then_link.field!r})) "
                    f"but input model {input_model.__name__!r} has no field {then_link.field!r}"
                )
            elif isinstance(then_link, DateRangeFrom):
                for name in (then_link.start, then_link.end):
                    if name not in input_fields:
                        errors.append(
                            f"{method} {path}: output field {field_prefix!r} WhenInput(then_link=DateRangeFrom) "
                            f"references {name!r} but input model {input_model.__name__!r} has no field {name!r}"
                        )
        elif isinstance(meta, ComputedFrom):
            for dep in meta.fields:
                if dep not in output_fields:
                    errors.append(
                        f"{method} {path}: output field {field_prefix!r} uses ComputedFrom "
                        f"with dependency {dep!r} but output model {output_model.__name__!r} has no field {dep!r}"
                    )
        # FromHeader, FromCookie, custom links: no input-field validation


def validate_specs(
    specs: list[Any],
) -> list[str]:
    """
    Validate a list of endpoint specs (e.g. SemblanceAPI._specs).

    Each spec must have: path, methods, input_model, output_annotation.
    Returns a list of error messages; empty if valid.
    """
    errors: list[str] = []
    for spec in specs:
        path = getattr(spec, "path", None)
        methods = getattr(spec, "methods", None)
        input_model = getattr(spec, "input_model", None)
        output_annotation = getattr(spec, "output_annotation", None)
        if path is None or methods is None or input_model is None:
            continue
        if output_annotation is None:
            # DELETE without output is valid
            continue
        method = (methods[0] or "GET").upper()
        output_model = get_output_model_for_type(output_annotation)
        if output_model is None:
            continue
        if not isinstance(input_model, type) or not issubclass(input_model, BaseModel):
            continue
        _validate_output_links(
            output_model,
            input_model,
            path,
            method,
            errors,
        )
    return errors


def get_duplicate_endpoint_errors(specs: list[Any]) -> list[str]:
    """
    Check for duplicate (path, method) registrations.
    Returns a list of error messages; empty if none.
    """
    errors: list[str] = []
    seen: set[tuple[str, str]] = set()
    for spec in specs:
        path = getattr(spec, "path", None)
        methods = getattr(spec, "methods", None)
        if path is None or methods is None:
            continue
        for method in methods:
            key = (path, method)
            if key in seen:
                method_upper = (method or "GET").upper()
                errors.append(
                    f"Duplicate {method_upper} endpoint registered for path {path!r}. "
                    "Register only one handler per (path, method)."
                )
            seen.add(key)
    return errors
