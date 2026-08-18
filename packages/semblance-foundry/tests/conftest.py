"""Shared Foundry mock fixtures."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from semblance_foundry import FoundryMock, FoundryMockConfig, TokenGrant
from semblance_foundry.fixtures.loaders import bundled_acme_path


@pytest.fixture
def mock() -> FoundryMock:
    foundry = FoundryMock(FoundryMockConfig(seed=42, auth="optional"))
    foundry.load_fixture(bundled_acme_path())
    return foundry


@pytest.fixture
def client(mock: FoundryMock) -> TestClient:
    return TestClient(mock.as_fastapi())


@pytest.fixture
def strict_client() -> TestClient:
    foundry = FoundryMock(
        FoundryMockConfig(
            seed=42,
            auth="strict",
            tokens=(TokenGrant(token="test-token"),),
        )
    )
    foundry.load_fixture(bundled_acme_path())
    return TestClient(foundry.as_fastapi())
