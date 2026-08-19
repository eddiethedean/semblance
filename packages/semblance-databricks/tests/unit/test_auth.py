from fastapi.testclient import TestClient

from semblance_databricks import DatabricksMock, DatabricksMockConfig, TokenGrant
from semblance_databricks.fixtures.loaders import bundled_acme_path


def _client(config: DatabricksMockConfig) -> TestClient:
    mock = DatabricksMock(config)
    mock.load_fixture(bundled_acme_path())
    return TestClient(mock.as_fastapi())


def test_optional_allows_missing_auth() -> None:
    client = _client(DatabricksMockConfig(auth="optional", seed=42))
    assert client.get("/api/2.1/clusters/list").status_code == 200


def test_optional_rejects_malformed_auth() -> None:
    client = _client(DatabricksMockConfig(auth="optional", seed=42))
    r = client.get("/api/2.1/clusters/list", headers={"Authorization": "Token abc"})
    assert r.status_code == 401
    body = r.json()
    assert body["error_code"] == "UNAUTHENTICATED"
    assert "abc" not in r.text


def test_disabled_ignores_auth() -> None:
    client = _client(DatabricksMockConfig(auth="disabled", seed=42))
    r = client.get("/api/2.1/clusters/list", headers={"Authorization": "nope"})
    assert r.status_code == 200


def test_strict_requires_allowlisted_token() -> None:
    client = _client(
        DatabricksMockConfig(
            auth="strict",
            seed=42,
            tokens=(TokenGrant(token="good"),),
        )
    )
    assert client.get("/api/2.1/clusters/list").status_code == 401
    ok = client.get("/api/2.1/clusters/list", headers={"Authorization": "Bearer good"})
    assert ok.status_code == 200
    bad = client.get(
        "/api/2.1/clusters/list", headers={"Authorization": "Bearer other"}
    )
    assert bad.status_code == 401
    assert "other" not in bad.text
