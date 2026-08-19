"""Pytest / in-process helpers. Prefer TestClient; no live Databricks."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from semblance_databricks.app import DatabricksMock
from semblance_databricks.config import DatabricksMockConfig
from semblance_databricks.fixtures.loaders import bundled_acme_path


class DatabricksMockContext:
    """Load a fixture, yield a TestClient, reset state on exit."""

    def __init__(
        self,
        *,
        seed: int | None = 42,
        fixture: str | Path | None = None,
        config: DatabricksMockConfig | None = None,
    ) -> None:
        if config is None:
            config = DatabricksMockConfig(seed=seed)
        self.mock = DatabricksMock(config)
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


def databricks_test_client(
    mock: DatabricksMock | None = None,
    *,
    fixture: str | Path | None = None,
    config: DatabricksMockConfig | None = None,
) -> TestClient:
    """Build a TestClient for a DatabricksMock (loads bundled acme if needed)."""
    if mock is None:
        mock = DatabricksMock(config or DatabricksMockConfig())
        mock.load_fixture(fixture if fixture is not None else bundled_acme_path())
    return TestClient(mock.as_fastapi())


def acme_client_iter(
    config: DatabricksMockConfig | None = None,
) -> Iterator[tuple[DatabricksMock, TestClient]]:
    mock = DatabricksMock(config or DatabricksMockConfig(seed=42))
    mock.load_fixture(bundled_acme_path())
    client = TestClient(mock.as_fastapi())
    try:
        yield mock, client
    finally:
        mock.state.clear()
        client.close()
