"""
Pagination helpers for list endpoints.

PageParams mixes into input models for limit/offset query params.
PaginatedResponse[T] wraps a list of items with total, limit, and offset.
"""

from typing import Generic, TypeVar

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
