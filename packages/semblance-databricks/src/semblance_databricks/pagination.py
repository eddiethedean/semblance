"""Pagination helpers using PageTokenCodec."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TypeVar

from semblance_databricks.errors import DatabricksError
from semblance_databricks.ids import PageTokenCodec

T = TypeVar("T")


def paginate(
    items: Sequence[T],
    *,
    page_size: int | None,
    page_token: str | None,
    resource: str,
    codec: PageTokenCodec,
    revision: int,
    default_page_size: int = 20,
    max_page_size: int = 100,
) -> tuple[list[T], str | None]:
    size = default_page_size if page_size is None else page_size
    if size <= 0:
        raise DatabricksError(
            400,
            "INVALID_PARAMETER_VALUE",
            "page_size must be positive",
        )
    size = min(size, max_page_size)
    offset = 0
    if page_token:
        cursor = codec.decode(page_token, resource)
        if cursor.revision != revision:
            raise DatabricksError(
                400,
                "INVALID_PARAMETER_VALUE",
                "Invalid page token",
            )
        offset = cursor.offset
    page = list(items[offset : offset + size])
    next_offset = offset + len(page)
    next_token = None
    if next_offset < len(items):
        next_token = codec.encode(resource, next_offset, revision)
    return page, next_token
