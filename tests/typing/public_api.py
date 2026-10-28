"""Static consumer checks for typing information shipped in package wheels."""

import random
from typing import Any, assert_type

from semblance import (
    LinkProtocol,
    PageSlice,
    PaginatedResponse,
    SemblanceAPI,
    register_link,
)
from semblance_databricks import DatabricksMock
from semblance_foundry import FoundryMock


class CustomAPI(SemblanceAPI):
    pass


class CustomFoundryMock(FoundryMock):
    pass


class CustomDatabricksMock(DatabricksMock):
    pass


assert_type(CustomAPI.from_config(), CustomAPI)
assert_type(CustomFoundryMock().load_fixture("fixture.yaml"), CustomFoundryMock)
assert_type(CustomFoundryMock().load_bundled_fixture(), CustomFoundryMock)
assert_type(CustomDatabricksMock().load_fixture("fixture.yaml"), CustomDatabricksMock)
assert_type(CustomDatabricksMock().load_bundled_fixture(), CustomDatabricksMock)
assert_type(PageSlice[int](items=[1]).items, list[int])
assert_type(
    PaginatedResponse[str](items=["item"], total=1, limit=10, offset=0).items,
    list[str],
)


class CustomLink:
    def resolve(self, input_data: dict[str, Any], rng: random.Random) -> object | None:
        return input_data.get("value")


link_type: type[LinkProtocol] = CustomLink
register_link(link_type)
