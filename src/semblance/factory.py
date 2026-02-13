"""
Polyfactory integration layer.

Builds response instances from output models using overrides produced by the
resolver. Supports single model, list[model], and PaginatedResponse[model]
outputs. Handles nested models, ComputedFrom, filter_by, and determinism via seed.
"""

from typing import Any, cast, get_origin

from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import BaseModel

from semblance.pagination import PaginatedResponse
from semblance.resolver import get_output_model_for_type, resolve_overrides


def _evaluate_overrides(
    overrides: dict[str, Any],
    seed: int | None = None,
) -> dict[str, Any]:
    """Replace callables and nested specs in overrides with their resolved values."""
    result: dict[str, Any] = {}
    computed: dict[str, tuple[tuple[str, ...], Any]] = {}

    for key, value in overrides.items():
        if isinstance(value, dict) and "_computed" in value and "_fn" in value:
            computed[key] = (value["_computed"], value["_fn"])
        elif isinstance(value, dict) and "_nested" in value and "_overrides" in value:
            nested_model = value["_nested"]
            nested_overrides = value["_overrides"]
            nested_resolved = _evaluate_overrides(nested_overrides, seed=seed)
            factory_class: type[ModelFactory[Any]] = ModelFactory.create_factory(
                nested_model
            )
            if seed is not None:
                factory_class.seed_random(seed)
            result[key] = factory_class.build(**nested_resolved)
        elif callable(value) and not isinstance(value, type):
            result[key] = value()
        else:
            result[key] = value

    for key, (dep_fields, fn) in computed.items():
        dep_values = [result[f] for f in dep_fields]
        result[key] = fn(*dep_values)

    return result


def build_one(
    output_model: type[BaseModel],
    input_model: type[BaseModel],
    input_instance: BaseModel,
    seed: int | None = None,
) -> BaseModel:
    """Build a single instance of output_model with dependencies from input_instance."""
    overrides = resolve_overrides(output_model, input_model, input_instance, seed=seed)
    resolved = _evaluate_overrides(overrides, seed=seed)
    factory_class = ModelFactory.create_factory(output_model)
    if seed is not None:
        factory_class.seed_random(seed)
    return cast(BaseModel, factory_class.build(**resolved))


def build_list(
    output_model: type[BaseModel],
    input_model: type[BaseModel],
    input_instance: BaseModel,
    count: int = 5,
    seed: int | None = None,
    filter_by: str | None = None,
) -> list[BaseModel]:
    """Build a list of instances of output_model with dependencies from input_instance."""
    overrides = resolve_overrides(output_model, input_model, input_instance, seed=seed)
    factory_class = ModelFactory.create_factory(output_model)
    if seed is not None:
        factory_class.seed_random(seed)

    if filter_by:
        target_val = input_instance.model_dump().get(filter_by)
        oversample = count * 5
        result: list[BaseModel] = []
        for _ in range(oversample):
            resolved = _evaluate_overrides(overrides, seed=seed)
            item = factory_class.build(**resolved)
            item_val = getattr(item, filter_by, None)
            if item_val == target_val:
                result.append(item)
                if len(result) >= count:
                    break
        return result[:count]

    result = []
    for _ in range(count):
        resolved = _evaluate_overrides(overrides, seed=seed)
        result.append(factory_class.build(**resolved))
    return result


def _get_paginated_inner(annotation: type) -> type[BaseModel] | None:
    """Extract inner model from PaginatedResponse[Model]."""
    try:
        if not issubclass(annotation, PaginatedResponse):
            return None
    except TypeError:
        return None
    # PaginatedResponse[User] has items: list[User]; extract User
    items_field = annotation.model_fields.get("items")
    if items_field is None:
        return None
    items_annotation = getattr(items_field, "annotation", None)
    if items_annotation is None:
        return None
    origin = get_origin(items_annotation)
    if origin is list:
        args = getattr(items_annotation, "__args__", ())
        if args and isinstance(args[0], type) and issubclass(args[0], BaseModel):
            return args[0]
    return None


def build_response(
    output_annotation: type,
    input_model: type[BaseModel],
    input_instance: BaseModel,
    list_count: int = 5,
    seed: int | None = None,
    filter_by: str | None = None,
) -> BaseModel | list[BaseModel]:
    """
    Build the response according to output_annotation.

    Handles single model, list[model], and PaginatedResponse[model].
    Uses input_instance for link resolution; list_count and filter_by
    affect list generation.
    """
    # PaginatedResponse[Model]
    inner = _get_paginated_inner(output_annotation)
    if inner is not None:
        input_data = input_instance.model_dump()
        try:
            limit = int(input_data.get("limit", 10))
        except (TypeError, ValueError):
            limit = 10
        try:
            offset = int(input_data.get("offset", 0))
        except (TypeError, ValueError):
            offset = 0
        limit = max(1, limit)
        offset = max(0, offset)
        all_items = build_list(
            inner, input_model, input_instance, count=offset + limit, seed=seed
        )
        items = all_items[offset : offset + limit]
        total = offset + len(items)
        return PaginatedResponse(items=items, total=total, limit=limit, offset=offset)

    # list[Model]
    origin = get_origin(output_annotation)
    if origin is list:
        model = get_output_model_for_type(output_annotation)
        if model is None:
            raise TypeError(
                f"Invalid output type {output_annotation!r}. "
                "Use list[SomeModel] where SomeModel is a Pydantic BaseModel."
            )
        return build_list(
            model,
            input_model,
            input_instance,
            count=list_count,
            seed=seed,
            filter_by=filter_by,
        )

    # Single Model
    model = get_output_model_for_type(output_annotation)
    if model is None:
        raise TypeError(
            f"Invalid output type {output_annotation!r}. "
            "Use a Pydantic BaseModel or list[SomeModel] for output."
        )
    return build_one(model, input_model, input_instance, seed=seed)
