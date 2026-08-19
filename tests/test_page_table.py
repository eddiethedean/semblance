from pydantic import BaseModel

from semblance import PageSlice, PageTable, SemblanceAPI
from semblance.testing import test_client as make_client


class Query(BaseModel):
    page_token: str | None = None


class User(BaseModel):
    name: str


def test_page_table_sequence() -> None:
    api = SemblanceAPI(seed=1)
    api.get(
        "/users",
        input=Query,
        output=PageSlice[User],
        page_table=PageTable(
            pages={
                None: [{"name": "a"}, {"name": "b"}],
                "p2": [{"name": "c"}],
            },
            next_tokens={None: "p2", "p2": None},
        ),
    )(lambda: None)
    client = make_client(api.as_fastapi())
    first = client.get("/users").json()
    assert [u["name"] for u in first["items"]] == ["a", "b"]
    assert first["next_page_token"] == "p2"
    second = client.get("/users", params={"page_token": "p2"}).json()
    assert [u["name"] for u in second["items"]] == ["c"]
    assert second["next_page_token"] is None


def test_unknown_page_token_400() -> None:
    api = SemblanceAPI(seed=1)
    api.get(
        "/users",
        input=Query,
        output=list[User],
        page_table=PageTable(pages={None: [{"name": "a"}]}),
    )(lambda: None)
    client = make_client(api.as_fastapi())
    r = client.get("/users", params={"page_token": "nope"})
    assert r.status_code == 400
    assert r.json()["detail"] == "Invalid page token"


def test_empty_token_uses_first_page() -> None:
    api = SemblanceAPI(seed=1)
    api.get(
        "/users",
        input=Query,
        output=list[User],
        page_table=PageTable(pages={None: [{"name": "a"}]}),
    )(lambda: None)
    client = make_client(api.as_fastapi())
    assert client.get("/users", params={"page_token": ""}).json()[0]["name"] == "a"
