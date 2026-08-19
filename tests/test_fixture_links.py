import json
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel

from semblance import FromJsonFixture, FromNestedFixture, SemblanceAPI
from semblance.testing import test_client as make_client


class Query(BaseModel):
    page_token: str | None = None
    office: str = "hq"


class Item(BaseModel):
    id: str
    title: str


def _write_fixture(tmp_path: Path) -> Path:
    path = tmp_path / "data.json"
    path.write_text(
        json.dumps(
            {
                "pages": {
                    "first": [{"id": "1", "title": "one"}],
                    "second": [{"id": "2", "title": "two"}],
                },
                "people": [
                    {"id": "a", "office": "hq", "title": "HQ"},
                    {"id": "b", "office": "nyc", "title": "NYC"},
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def test_json_fixture_variant(tmp_path: Path) -> None:
    path = str(_write_fixture(tmp_path))

    class Out(BaseModel):
        title: Annotated[
            str,
            FromJsonFixture(
                path,
                pointer="pages/first/0/title",
                variant_from="page_token",
                variants={"p2": "pages/second/0/title"},
            ),
        ]

    api = SemblanceAPI(seed=1)
    api.get("/item", input=Query, output=Out)(lambda: None)
    client = make_client(api.as_fastapi())
    assert client.get("/item").json()["title"] == "one"
    assert client.get("/item", params={"page_token": "p2"}).json()["title"] == "two"


def test_nested_where(tmp_path: Path) -> None:
    path = str(_write_fixture(tmp_path))

    class Out(BaseModel):
        person: Annotated[
            Item,
            FromNestedFixture(path, pointer="people", where={"office": "office"}),
        ]

    api = SemblanceAPI(seed=1)
    api.get("/p", input=Query, output=Out)(lambda: None)
    client = make_client(api.as_fastapi())
    assert client.get("/p", params={"office": "nyc"}).json()["person"]["id"] == "b"


def test_nested_index(tmp_path: Path) -> None:
    path = str(_write_fixture(tmp_path))

    class Out(BaseModel):
        person: Annotated[
            Item,
            FromNestedFixture(path, pointer="people", index=1),
        ]

    api = SemblanceAPI(seed=1)
    api.get("/p", input=Query, output=Out)(lambda: None)
    client = make_client(api.as_fastapi())
    assert client.get("/p").json()["person"]["id"] == "b"


def test_strict_miss_raises(tmp_path: Path) -> None:
    path = str(_write_fixture(tmp_path))

    class Out(BaseModel):
        title: Annotated[
            str,
            FromJsonFixture(path, pointer="missing/key", strict=True),
        ]

    api = SemblanceAPI(seed=1)
    api.get("/item", input=Query, output=Out)(lambda: None)
    client = make_client(api.as_fastapi())
    r = client.get("/item")
    assert r.status_code == 500
    assert r.json()["detail"] == "Fixture miss"


def test_nonstrict_miss_generates(tmp_path: Path) -> None:
    path = str(_write_fixture(tmp_path))

    class Out(BaseModel):
        title: Annotated[
            str, FromJsonFixture(path, pointer="missing/key", strict=False)
        ]

    api = SemblanceAPI(seed=1)
    api.get("/item", input=Query, output=Out)(lambda: None)
    client = make_client(api.as_fastapi())
    r = client.get("/item")
    assert r.status_code == 200
    assert isinstance(r.json()["title"], str)


def test_nested_first_item(tmp_path: Path) -> None:
    path = str(_write_fixture(tmp_path))

    class Out(BaseModel):
        person: Annotated[Item, FromNestedFixture(path, pointer="people")]

    api = SemblanceAPI(seed=1)
    api.get("/p", input=Query, output=Out)(lambda: None)
    client = make_client(api.as_fastapi())
    assert client.get("/p").json()["person"]["id"] == "a"
