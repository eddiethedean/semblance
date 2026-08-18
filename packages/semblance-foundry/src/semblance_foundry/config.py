"""Typed configuration for FoundryMock."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

AuthMode = Literal["disabled", "optional", "strict"]


@dataclass(frozen=True)
class TokenGrant:
    """A token accepted in strict auth mode. Never log or echo ``token``."""

    token: str
    scopes: tuple[str, ...] = ()


@dataclass
class FoundryMockConfig:
    """Runtime options for a Foundry mock server."""

    seed: int | None = 42
    auth: AuthMode = "optional"
    stateful: bool = True
    tokens: tuple[TokenGrant, ...] = ()
    error_rate: float = 0.0
    error_codes: list[int] | None = None
    latency_ms: float = 0.0
    jitter_ms: float = 0.0
    rate_limit: float | None = None
    default_page_size: int = 100
    max_page_size: int = 1000

    def __post_init__(self) -> None:
        if self.error_codes is None:
            self.error_codes = [500]
        if self.auth not in ("disabled", "optional", "strict"):
            raise ValueError(
                f"auth must be 'disabled', 'optional', or 'strict', got {self.auth!r}"
            )
        if not 0.0 <= self.error_rate <= 1.0:
            raise ValueError("error_rate must be between 0 and 1")
