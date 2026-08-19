from pydantic import BaseModel

from semblance import ErrorCase, PageTable, ScenarioStep, SemblanceAPI
from semblance.testing import test_client as make_client


class Query(BaseModel):
    name: str = "alice"
    cluster_id: str = "ok"


class User(BaseModel):
    name: str


def test_default_route_is_open() -> None:
    api = SemblanceAPI(seed=1)
    api.get("/users", input=Query, output=list[User], list_count=1)(lambda: None)
    client = make_client(api.as_fastapi())
    assert client.get("/users").status_code == 200


def test_bearer_allow_list() -> None:
    api = SemblanceAPI(seed=1)
    api.get(
        "/users",
        input=Query,
        output=list[User],
        list_count=1,
        bearer_tokens=("secret",),
    )(lambda: None)
    client = make_client(api.as_fastapi())
    denied = client.get("/users")
    assert denied.status_code == 401
    assert "secret" not in denied.text
    assert (
        client.get("/users", headers={"Authorization": "Bearer secret"}).status_code
        == 200
    )
    bad = client.get("/users", headers={"Authorization": "Bearer other"})
    assert bad.status_code == 401
    assert "other" not in bad.text
    malformed = client.get("/users", headers={"Authorization": "Token secret"})
    assert malformed.status_code == 401


def test_empty_bearer_list_is_open() -> None:
    api = SemblanceAPI(seed=1)
    api.get(
        "/users",
        input=Query,
        output=list[User],
        list_count=1,
        bearer_tokens=(),
    )(lambda: None)
    client = make_client(api.as_fastapi())
    assert client.get("/users").status_code == 200


def test_bytes_bearer_token_matches() -> None:
    api = SemblanceAPI(seed=1)
    api.get(
        "/users",
        input=Query,
        output=list[User],
        list_count=1,
        bearer_tokens=(b"secret",),  # type: ignore[arg-type]
    )(lambda: None)
    client = make_client(api.as_fastapi())
    assert (
        client.get("/users", headers={"Authorization": "Bearer secret"}).status_code
        == 200
    )


def test_openapi_documents_401() -> None:
    api = SemblanceAPI(seed=1)
    api.get(
        "/users",
        input=Query,
        output=list[User],
        bearer_tokens=("t",),
    )(lambda: None)
    schema = api.as_fastapi().openapi()
    assert "401" in schema["paths"]["/users"]["get"]["responses"]


def test_openapi_documents_mapped_and_scenario_errors() -> None:
    api = SemblanceAPI(seed=1)
    api.get(
        "/users",
        input=Query,
        output=list[User],
        errors=(ErrorCase(when=lambda q: False, status=409, detail="conflict"),),
        scenario=(ScenarioStep(status=503, detail="busy"),),
        page_table=PageTable(pages={None: [{"name": "a"}]}),
    )(lambda: None)
    responses = api.as_fastapi().openapi()["paths"]["/users"]["get"]["responses"]
    assert "409" in responses
    assert "503" in responses
    assert "400" in responses


def test_error_map_first_match() -> None:
    api = SemblanceAPI(seed=1)
    api.get(
        "/users",
        input=Query,
        output=list[User],
        list_count=1,
        errors=(
            ErrorCase(
                when=lambda q: q.cluster_id == "bad", status=400, detail="bad cluster"
            ),
            ErrorCase(when=lambda q: q.name == "nobody", status=404, detail="missing"),
        ),
        error_rate=1.0,
        error_codes=[500],
    )(lambda: None)
    client = make_client(api.as_fastapi())
    mapped = client.get("/users", params={"cluster_id": "bad"})
    assert mapped.status_code == 400
    assert mapped.json()["detail"] == "bad cluster"
    ok = client.get("/users")
    assert ok.status_code == 500


def test_delete_bearer() -> None:
    class PathId(BaseModel):
        id: str = "1"

    api = SemblanceAPI(seed=1)
    api.delete("/users/{id}", input=PathId, bearer_tokens=("t",))(lambda: None)
    client = make_client(api.as_fastapi())
    assert client.delete("/users/1").status_code == 401
    r = client.delete("/users/1", headers={"Authorization": "Bearer t"})
    assert r.status_code == 204


def test_scenario_holds_last() -> None:
    api = SemblanceAPI(seed=1)
    api.get(
        "/users",
        input=Query,
        output=list[User],
        list_count=1,
        scenario=(ScenarioStep(status=503, detail="busy"), ScenarioStep(status=200)),
    )(lambda: None)
    api.get(
        "/other",
        input=Query,
        output=list[User],
        list_count=1,
        scenario=(ScenarioStep(status=200),),
    )(lambda: None)
    client = make_client(api.as_fastapi())
    assert client.get("/users").status_code == 503
    assert client.get("/users").status_code == 200
    assert client.get("/users").status_code == 200
    assert client.get("/other").status_code == 200
