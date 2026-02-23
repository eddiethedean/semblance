"""
Plugin system for custom link types.

Define custom link classes that implement the LinkProtocol (resolve method),
then register them with register_link. The resolver calls meta.resolve(input_data, rng)
for instances of registered types, using the return value as the field override.
"""

import random
from typing import Any, Protocol


class LinkProtocol(Protocol):
    """Protocol for custom link types.

    Custom links must implement resolve(input_data, rng). Return the override
    value for the field, or a callable that returns the value when invoked.
    """

    def resolve(self, input_data: dict[str, Any], rng: random.Random) -> object | None:
        """
        Return the override value for this field.

        Args:
            input_data: Validated request input as a dict (from model_dump()).
            rng: Random instance for deterministic generation when seed is set.
        """
        ...


_REGISTRY: set[type] = set()


def register_link(link_class: type[LinkProtocol]) -> None:
    """Register a custom link type. The resolver will call meta.resolve(input_data, rng) for its instances."""
    _REGISTRY.add(link_class)


def get_registered_links() -> set[type]:
    """Return the set of registered link classes."""
    return set(_REGISTRY)


def is_registered(meta: object) -> bool:
    """Check if meta's type is registered as a custom link."""
    return type(meta) in _REGISTRY
