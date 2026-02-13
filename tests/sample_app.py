"""Minimal Semblance app for CLI/testing."""

from typing import Annotated

from pydantic import BaseModel

from semblance import FromInput, SemblanceAPI


class UserQuery(BaseModel):
    name: str = "alice"


class User(BaseModel):
    name: Annotated[str, FromInput("name")]


api = SemblanceAPI()


@api.get("/users", input=UserQuery, output=list[User])
def users():
    pass


app = api.as_fastapi()
