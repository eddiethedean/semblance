"""Load JSON fixtures and resolve slash pointers for fixture links."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_CACHE: dict[str, Any] = {}


def load_json_file(path: str) -> Any:
    """Load and cache a JSON file by resolved path."""
    resolved = str(Path(path).expanduser().resolve())
    if resolved not in _CACHE:
        with open(resolved, encoding="utf-8") as fh:
            _CACHE[resolved] = json.load(fh)
    return _CACHE[resolved]


def resolve_pointer(doc: Any, pointer: str) -> Any:
    """Walk ``items/0/name`` style paths. Empty pointer returns ``doc``."""
    if not pointer:
        return doc
    current = doc
    for part in pointer.strip("/").split("/"):
        if isinstance(current, list):
            try:
                current = current[int(part)]
            except (ValueError, IndexError) as exc:
                raise KeyError(part) from exc
        elif isinstance(current, dict):
            if part not in current:
                raise KeyError(part)
            current = current[part]
        else:
            raise KeyError(part)
    return current


def pick_where(
    items: list[Any],
    where: dict[str, str],
    input_data: dict[str, Any],
) -> Any:
    """Return the first list object matching ``obj[field] == input[input_field]``."""
    for item in items:
        if not isinstance(item, dict):
            continue
        if all(
            item.get(field) == input_data.get(source) for field, source in where.items()
        ):
            return item
    raise KeyError("where")
