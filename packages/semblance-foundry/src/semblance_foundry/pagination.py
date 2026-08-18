"""Pagination helpers using PageTokenCodec."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TypeVar

from semblance_foundry.errors import FoundryError
from semblance_foundry.ids import PageTokenCodec

T = TypeVar("T")


def paginate(
    items: Sequence[T],
    *,
    page_size: int | None,
    page_token: str | None,
    resource: str,
    codec: PageTokenCodec,
    revision: int,
    default_page_size: int = 100,
    max_page_size: int = 1000,
) -> tuple[list[T], str | None]:
    size = default_page_size if page_size is None else page_size
    if size <= 0:
        raise FoundryError(
            status_code=400,
            error_code="INVALID_ARGUMENT",
            error_name="InvalidPageSize",
            parameters={"pageSize": size},
        )
    size = min(size, max_page_size)
    offset = 0
    if page_token:
        cursor = codec.decode(page_token, resource)
        offset = cursor.offset
    page = list(items[offset : offset + size])
    next_offset = offset + len(page)
    next_token = None
    if next_offset < len(items):
        next_token = codec.encode(resource, next_offset, revision)
    return page, next_token
