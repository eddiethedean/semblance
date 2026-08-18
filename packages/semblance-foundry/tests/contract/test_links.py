from fastapi.testclient import TestClient


def test_list_linked_objects(client: TestClient) -> None:
    r = client.get("/api/v2/ontologies/acme/objects/Employee/1/links/worksAt")
    assert r.status_code == 200
    data = r.json()["data"]
    assert len(data) == 1
    assert data[0]["officeId"] == "hq"
    assert data[0]["name"] == "Headquarters"


def test_list_linked_objects_missing_link_type(client: TestClient) -> None:
    r = client.get("/api/v2/ontologies/acme/objects/Employee/1/links/nope")
    assert r.status_code == 404
    assert r.json()["errorName"] == "LinkTypeNotFound"
