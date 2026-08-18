from fastapi.testclient import TestClient


def test_list_ontologies(client: TestClient) -> None:
    r = client.get("/api/v2/ontologies")
    assert r.status_code == 200
    data = r.json()["data"]
    assert len(data) == 1
    assert data[0]["apiName"] == "acme"
    assert data[0]["rid"].startswith("ri.ontology.main.ontology.")
    assert "X-Request-ID" in r.headers


def test_get_ontology(client: TestClient) -> None:
    listed = client.get("/api/v2/ontologies").json()["data"][0]
    by_name = client.get("/api/v2/ontologies/acme")
    assert by_name.status_code == 200
    assert by_name.json()["apiName"] == "acme"
    by_rid = client.get(f"/api/v2/ontologies/{listed['rid']}")
    assert by_rid.status_code == 200
    assert by_rid.json()["apiName"] == "acme"


def test_get_ontology_missing(client: TestClient) -> None:
    r = client.get("/api/v2/ontologies/nope")
    assert r.status_code == 404
    assert r.json()["errorName"] == "OntologyNotFound"
