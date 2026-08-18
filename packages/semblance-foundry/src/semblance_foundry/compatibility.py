"""Load and publish the per-operation compatibility manifest."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

_MANIFEST_PATH = Path(__file__).resolve().parent / "compatibility.yaml"


@lru_cache(maxsize=1)
def load_manifest() -> dict[str, Any]:
    data = yaml.safe_load(_MANIFEST_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("compatibility.yaml must be a mapping")
    return data


def manifest_json() -> dict[str, Any]:
    return load_manifest()


def operations_table() -> list[dict[str, Any]]:
    ops = load_manifest().get("operations", [])
    if not isinstance(ops, list):
        return []
    return [op for op in ops if isinstance(op, dict)]
