"""
Polyfactory integration layer.

Builds response instances from output models using resolved overrides.
Supports single model and list[model] outputs.
"""

from typing import Any, Callable, get_origin

from pydantic import BaseModel
from polyfactory.factories.pydantic_factory import ModelFactory

from semblance.resolver import get_output_model_for_type, resolve_overrides


def _evaluate_overrides(overrides: dict[str, Any]) -> dict[str, Any]:
    """Replace callables in overrides with their return values."""
    result: dict[str, Any] = {}
    for key, value in overrides.items():
        if callable(value) and not isinstance(value, type):
            result[key] = value()
        else:
            result[key] = value
    return result


def build_one(
    output_model: type[BaseModel],
    input_model: type[BaseModel],
    input_instance: BaseModel,
) -> BaseModel:
    """Build a single instance of output_model with dependencies from input_instance."""
    overrides = resolve_overrides(output_model, input_model, input_instance)
    resolved = _evaluate_overrides(overrides)
    factory_class = ModelFactory.create_factory(output_model)
    return factory_class.build(**resolved)


def build_list(
    output_model: type[BaseModel],
    input_model: type[BaseModel],
    input_instance: BaseModel,
    count: int = 5,
) -> list[BaseModel]:
    """Build a list of instances of output_model with dependencies from input_instance."""
    overrides = resolve_overrides(output_model, input_model, input_instance)
    factory_class = ModelFactory.create_factory(output_model)
    result: list[BaseModel] = []
    for _ in range(count):
        resolved = _evaluate_overrides(overrides)
        result.append(factory_class.build(**resolved))
    return result


def build_response(
    output_annotation: type,
    input_model: type[BaseModel],
    input_instance: BaseModel,
    list_count: int = 5,
) -> BaseModel | list[BaseModel]:
    """
    Build the response (single or list) according to output_annotation.
    output_annotation is the type passed to @api.get(..., output=...).
    """
    origin = get_origin(output_annotation)
    if origin is list:
        model = get_output_model_for_type(output_annotation)
        if model is None:
            raise TypeError(f"Cannot resolve list item model from {output_annotation}")
        return build_list(model, input_model, input_instance, count=list_count)

    model = get_output_model_for_type(output_annotation)
    if model is None:
        raise TypeError(f"Cannot resolve output model from {output_annotation}")
    return build_one(model, input_model, input_instance)
