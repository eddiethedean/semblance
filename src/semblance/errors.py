"""Declarative error maps and per-route scenario steps."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel


@dataclass(frozen=True)
class ErrorCase:
    """Return this status/body when ``when(input)`` is true.

    First matching case on a route wins. Evaluated after the input model
    validates (schema failures remain 422).
    """

    when: Callable[[BaseModel], bool]
    status: int
    detail: Any = "Invalid request"


@dataclass(frozen=True)
class ScenarioStep:
    """One step in a per-route response sequence.

    ``status`` other than 200 raises HTTPException. 200 with ``detail`` None
    continues to normal response generation. After the last step, the last
    step is held (retry-friendly).
    """

    status: int = 200
    detail: Any | None = None
