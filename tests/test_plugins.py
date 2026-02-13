"""Tests for plugin system: register_link, custom links."""

from typing import Annotated, Protocol, cast

from pydantic import BaseModel

from semblance import SemblanceAPI, register_link, test_client
from semblance.plugins import get_registered_links, is_registered


class _ChoiceProtocol(Protocol):
    def choice(self, seq: object) -> object: ...


class FromEnv:
    """Custom link: read value from environment variable."""

    def __init__(self, env_var: str):
        self.env_var = env_var

    def resolve(self, input_data: dict, rng) -> str | None:
        import os

        return os.environ.get(self.env_var)


class RandomChoice:
    """Custom link: pick from input list field."""

    def __init__(self, field: str):
        self.field = field

    def resolve(
        self, input_data: dict[str, object], rng: _ChoiceProtocol
    ) -> str | None:
        opts = input_data.get(self.field)
        if opts and isinstance(opts, (list, tuple)):
            return cast(str, rng.choice(opts))
        return None


def test_register_and_is_registered():
    register_link(FromEnv)
    assert FromEnv in get_registered_links()
    assert is_registered(FromEnv("X"))


def test_custom_link_resolve():
    register_link(FromEnv)
    try:
        import os

        os.environ["TEST_VAR"] = "custom_value"

        class Query(BaseModel):
            name: str = "alice"

        class User(BaseModel):
            name: Annotated[str, FromEnv("TEST_VAR")]

        api = SemblanceAPI()
        api.get("/user", input=Query, output=User)(lambda: None)
        app = api.as_fastapi()
        client = test_client(app)
        r = client.get("/user?name=x")
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "custom_value"
    finally:
        import os

        os.environ.pop("TEST_VAR", None)


def test_custom_link_random_choice():
    register_link(RandomChoice)

    class QueryWithOptions(BaseModel):
        options: list[str] = ["a", "b", "c"]

    class Item(BaseModel):
        choice: Annotated[str, RandomChoice("options")]

    api = SemblanceAPI(seed=42)
    api.get("/item", input=QueryWithOptions, output=Item)(lambda: None)
    app = api.as_fastapi()
    client = test_client(app)
    r = client.get("/item?options=a&options=b&options=c")
    assert r.status_code == 200
    data = r.json()
    assert data["choice"] in ("a", "b", "c")
