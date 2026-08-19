from fastapi.testclient import TestClient


def test_list_scopes(client: TestClient) -> None:
    r = client.get("/api/2.0/secrets/scopes/list")
    assert r.status_code == 200
    names = [s["name"] for s in r.json()["scopes"]]
    assert "acme-scope" in names


def test_list_secret_keys(client: TestClient) -> None:
    r = client.get("/api/2.0/secrets/list", params={"scope": "acme-scope"})
    assert r.status_code == 200
    secrets = r.json()["secrets"]
    assert secrets[0]["key"] == "api-key"
    blob = r.text.lower()
    assert "redacted" not in blob
    assert "string_value" not in blob
    assert "value" not in secrets[0]


def test_put_and_list_keys_only(client: TestClient) -> None:
    put = client.post(
        "/api/2.0/secrets/put",
        json={"scope": "acme-scope", "key": "new-key", "string_value": "super-secret"},
    )
    assert put.status_code == 200
    listed = client.get("/api/2.0/secrets/list", params={"scope": "acme-scope"})
    keys = {row["key"] for row in listed.json()["secrets"]}
    assert "new-key" in keys
    assert "super-secret" not in listed.text
