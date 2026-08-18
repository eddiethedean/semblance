from fastapi.testclient import TestClient


def test_compatibility_manifest(client: TestClient) -> None:
    r = client.get("/.well-known/foundry-mock-compatibility.json")
    assert r.status_code == 200
    body = r.json()
    assert body["documentedAt"] == "2026-08-18"
    ids = {op["operationId"] for op in body["operations"]}
    assert "ListOntologies" in ids
    assert "SearchObjects" in ids
    search = next(
        op for op in body["operations"] if op["operationId"] == "SearchObjects"
    )
    assert search["supportLevel"] == "representative"
    apply = next(op for op in body["operations"] if op["operationId"] == "ApplyAction")
    assert apply["supportLevel"] == "unsupported"
