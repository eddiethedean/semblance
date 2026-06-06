"""Semblance API with invalid link bindings for CLI validate tests."""

from typing import Annotated

from pydantic import BaseModel

from semblance import FromInput, SemblanceAPI

api = SemblanceAPI()


class Query(BaseModel):
    x: str = "a"


class Out(BaseModel):
    name: Annotated[str, FromInput("typo")]


@api.get("/bad", input=Query, output=Out)
def bad():
    pass
