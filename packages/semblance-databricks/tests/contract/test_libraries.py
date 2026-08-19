from fastapi.testclient import TestClient


def test_install_uninstall(client: TestClient) -> None:
    inst = client.post(
        "/api/2.0/libraries/install",
        json={
            "cluster_id": "0101-acme-0001",
            "libraries": [{"pypi": {"package": "pandas"}}],
        },
    )
    assert inst.status_code == 200
    listed = client.get("/api/2.1/clusters/get?cluster_id=0101-acme-0001")
    assert listed.json()["libraries"] == [{"pypi": {"package": "pandas"}}]
    uninst = client.post(
        "/api/2.0/libraries/uninstall",
        json={
            "cluster_id": "0101-acme-0001",
            "libraries": [{"pypi": {"package": "pandas"}}],
        },
    )
    assert uninst.status_code == 200
    cleared = client.get("/api/2.1/clusters/get?cluster_id=0101-acme-0001")
    assert cleared.json()["libraries"] == []
