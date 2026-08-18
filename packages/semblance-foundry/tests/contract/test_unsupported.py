from fastapi.testclient import TestClient

from semblance_foundry import FoundryMock, FoundryMockConfig, TokenGrant
from semblance_foundry.fixtures.loaders import bundled_acme_path


def test_unknown_path_404(client: TestClient) -> None:
    r = client.get("/api/v2/not-a-real-endpoint")
    assert r.status_code == 404
    assert r.json()["errorName"] == "NotFound"


def test_apply_optional_404(client: TestClient) -> None:
    r = client.post("/api/v2/ontologies/acme/actions/renameEmployee/apply")
    assert r.status_code == 404
    assert r.json()["errorName"] == "NotFound"


def test_apply_strict_501(strict_client: TestClient) -> None:
    r = strict_client.post(
        "/api/v2/ontologies/acme/actions/renameEmployee/apply",
        headers={"Authorization": "Bearer test-token"},
    )
    assert r.status_code == 501
    assert r.json()["errorName"] == "UnsupportedOperation"


def test_apply_batch_strict_501() -> None:
    mock = FoundryMock(
        FoundryMockConfig(
            seed=42,
            auth="strict",
            tokens=(TokenGrant(token="test-token"),),
        )
    )
    mock.load_fixture(bundled_acme_path())
    client = TestClient(mock.as_fastapi())
    r = client.post(
        "/api/v2/ontologies/acme/actions/renameEmployee/applyBatch",
        headers={"Authorization": "Bearer test-token"},
    )
    assert r.status_code == 501
    assert r.json()["errorName"] == "UnsupportedOperation"
