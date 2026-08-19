"""
Pagination helpers for list endpoints.

PageParams mixes into input models for limit/offset query params.
PaginatedResponse[T] wraps a list of items with total, limit, and offset.
PageTable / PageSlice serve a declared token → page map (not adapter codecs).
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar, get_origin

from pydantic import BaseModel

T = TypeVar("T")


class PageParams(BaseModel):
    """Mixin for pagination query/body params: limit and offset."""

    limit: int = 10
    offset: int = 0


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated list response: items, total count, limit, and offset."""

    items: list[T]
    total: int
    limit: int
    offset: int


@dataclass(frozen=True)
class PageTable:
    """Declared pages keyed by incoming page token (None is the first page)."""

    pages: Mapping[str | None, Sequence[Any]]
    next_tokens: Mapping[str | None, str | None] = field(default_factory=dict)
    token_field: str = "page_token"


class PageSlice(BaseModel, Generic[T]):
    """One cursor page: items plus the token for the next request."""

    items: list[T]
    next_page_token: str | None = None


def is_page_slice_output(annotation: object) -> bool:
    """True for ``PageSlice`` and parameterized ``PageSlice[Model]``."""
    candidates: list[object] = [annotation]
    origin = get_origin(annotation)
    if origin is not None:
        candidates.append(origin)
    for candidate in candidates:
        try:
            if isinstance(candidate, type) and issubclass(candidate, PageSlice):
                return True
        except TypeError:
            continue
    return False
