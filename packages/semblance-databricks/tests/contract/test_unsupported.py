from fastapi.testclient import TestClient

from semblance_databricks import DatabricksMock, DatabricksMockConfig, TokenGrant
from semblance_databricks.fixtures.loaders import bundled_acme_path


def test_unknown_path_404(client: TestClient) -> None:
    r = client.get("/api/2.0/jobs/list")
    assert r.status_code == 404
    assert r.json()["error_code"] == "RESOURCE_DOES_NOT_EXIST"


def test_permanent_delete_optional_404(client: TestClient) -> None:
    r = client.post("/api/2.1/clusters/permanent-delete", json={"cluster_id": "x"})
    assert r.status_code == 404


def test_permanent_delete_strict_501(strict_client: TestClient) -> None:
    r = strict_client.post(
        "/api/2.1/clusters/permanent-delete",
        json={"cluster_id": "x"},
        headers={"Authorization": "Bearer test-token"},
    )
    assert r.status_code == 501
    assert r.json()["error_code"] == "FEATURE_DISABLED"


def test_add_block_strict_501() -> None:
    mock = DatabricksMock(
        DatabricksMockConfig(
            seed=42,
            auth="strict",
            tokens=(TokenGrant(token="test-token"),),
        )
    )
    mock.load_fixture(bundled_acme_path())
    client = TestClient(mock.as_fastapi())
    r = client.post(
        "/api/2.0/dbfs/add-block",
        json={"handle": 1, "data": "YQ=="},
        headers={"Authorization": "Bearer test-token"},
    )
    assert r.status_code == 501
    assert r.json()["error_code"] == "FEATURE_DISABLED"
