"""Shared Databricks mock fixtures."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from semblance_databricks import DatabricksMock, DatabricksMockConfig, TokenGrant


@pytest.fixture
def mock() -> DatabricksMock:
    dbx = DatabricksMock(DatabricksMockConfig(seed=42, auth="optional"))
    dbx.load_bundled_fixture()
    return dbx


@pytest.fixture
def client(mock: DatabricksMock) -> TestClient:
    return TestClient(mock.as_fastapi())


@pytest.fixture
def strict_client() -> TestClient:
    dbx = DatabricksMock(
        DatabricksMockConfig(
            seed=42,
            auth="strict",
            tokens=(TokenGrant(token="test-token"),),
        )
    )
    dbx.load_bundled_fixture()
    return TestClient(dbx.as_fastapi())
