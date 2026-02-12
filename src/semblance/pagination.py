"""
Pagination helpers for list endpoints.

PageParams and PaginatedResponse support offset/limit pagination.
"""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PageParams(BaseModel):
    """Query/body params for pagination: limit and offset."""

    limit: int = 10
    offset: int = 0


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated list response with items, total, limit, and offset."""

    items: list[T]
    total: int
    limit: int
    offset: int
