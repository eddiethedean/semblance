"""
Plugin system for custom link types.

Register custom link classes that implement the LinkProtocol.
The resolver will call meta.resolve(input_data, rng) for registered links.
"""

import random
from typing import Any, Protocol


class LinkProtocol(Protocol):
    """Protocol for custom link types.

    Custom links must implement resolve(input_data, rng) and return
    the override value (or a callable that returns the value when called).
    """

    def resolve(self, input_data: dict[str, Any], rng: random.Random) -> Any:
        """Return the override value for this field."""
        ...


_REGISTRY: set[type] = set()


def register_link(link_class: type) -> None:
    """Register a custom link type. Resolver will call meta.resolve(input_data, rng) for instances."""
    _REGISTRY.add(link_class)


def get_registered_links() -> set[type]:
    """Return the set of registered link classes."""
    return set(_REGISTRY)


def is_registered(meta: Any) -> bool:
    """Check if meta's type is registered as a custom link."""
    return type(meta) in _REGISTRY
