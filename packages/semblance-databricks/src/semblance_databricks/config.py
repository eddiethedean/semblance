"""Typed configuration for DatabricksMock."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

AuthMode = Literal["disabled", "optional", "strict"]
ClockMode = Literal["virtual", "real"]
FailStage = Literal["before_validate", "before_write", "after_write"] | None


@dataclass(frozen=True)
class TokenGrant:
    """A token accepted in strict auth mode. Never log or echo ``token``."""

    token: str
    scopes: tuple[str, ...] = ()


@dataclass
class DatabricksMockConfig:
    """Runtime options for a Databricks mock server."""

    seed: int | None = 42
    auth: AuthMode = "optional"
    tokens: tuple[TokenGrant, ...] = ()
    error_rate: float = 0.0
    error_codes: list[int] | None = None
    latency_ms: float = 0.0
    jitter_ms: float = 0.0
    rate_limit: float | None = None
    default_page_size: int = 20
    max_page_size: int = 100
    clock: ClockMode = "virtual"
    org_id: str | None = "1234567890"
    fail_stage: FailStage = None
    dbfs_temp_dir: str | None = None
    dbfs_max_files: int = 100
    dbfs_max_bytes: int = 1_048_576

    def __post_init__(self) -> None:
        if self.error_codes is None:
            self.error_codes = [500]
        if self.auth not in ("disabled", "optional", "strict"):
            raise ValueError(
                f"auth must be 'disabled', 'optional', or 'strict', got {self.auth!r}"
            )
        if self.clock not in ("virtual", "real"):
            raise ValueError("clock must be 'virtual' or 'real'")
        if not 0.0 <= self.error_rate <= 1.0:
            raise ValueError("error_rate must be between 0 and 1")
