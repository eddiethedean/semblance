from fastapi.testclient import TestClient


def test_compatibility_manifest(client: TestClient) -> None:
    r = client.get("/.well-known/semblance-databricks-compat.json")
    assert r.status_code == 200
    body = r.json()
    assert body["documentedAt"] == "2026-08-19"
    ids = {op["operationId"] for op in body["operations"]}
    assert "ListClusters" in ids
    assert "ExecuteStatement" in ids
    search = next(
        op for op in body["operations"] if op["operationId"] == "CurrentUserMe"
    )
    assert search["supportLevel"] == "representative"
    stub = next(
        op for op in body["operations"] if op["operationId"] == "PermanentDeleteCluster"
    )
    assert stub["supportLevel"] == "stub"
