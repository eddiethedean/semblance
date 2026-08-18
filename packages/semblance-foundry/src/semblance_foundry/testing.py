"""Pytest / in-process helpers. Prefer TestClient; no live Foundry."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from semblance_foundry.app import FoundryMock
from semblance_foundry.config import FoundryMockConfig
from semblance_foundry.fixtures.loaders import bundled_acme_path


class FoundryMockContext:
    """Load a fixture, yield a TestClient, reset state on exit."""

    def __init__(
        self,
        *,
        seed: int | None = 42,
        fixture: str | Path | None = None,
        config: FoundryMockConfig | None = None,
    ) -> None:
        if config is None:
            config = FoundryMockConfig(seed=seed)
        self.mock = FoundryMock(config)
        path = fixture if fixture is not None else bundled_acme_path()
        self.mock.load_fixture(path)
        self._client: TestClient | None = None

    def __enter__(self) -> TestClient:
        self._client = TestClient(self.mock.as_fastapi())
        return self._client

    def __exit__(self, *exc: Any) -> None:
        self.mock.state.clear()
        if self._client is not None:
            self._client.close()


def foundry_test_client(
    mock: FoundryMock | None = None,
    *,
    fixture: str | Path | None = None,
    config: FoundryMockConfig | None = None,
) -> TestClient:
    """Build a TestClient for a FoundryMock (loads bundled acme if needed)."""
    if mock is None:
        mock = FoundryMock(config or FoundryMockConfig())
        mock.load_fixture(fixture if fixture is not None else bundled_acme_path())
    return TestClient(mock.as_fastapi())


def acme_client_iter(
    config: FoundryMockConfig | None = None,
) -> Iterator[tuple[FoundryMock, TestClient]]:
    mock = FoundryMock(config or FoundryMockConfig(seed=42))
    mock.load_fixture(bundled_acme_path())
    client = TestClient(mock.as_fastapi())
    try:
        yield mock, client
    finally:
        mock.state.clear()
        client.close()
