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
    uninst = client.post(
        "/api/2.0/libraries/uninstall",
        json={"cluster_id": "0101-acme-0001"},
    )
    assert uninst.status_code == 200
