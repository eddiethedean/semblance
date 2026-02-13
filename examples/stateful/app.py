"""
Stateful example - POST stores items, GET returns stored list.

Run: semblance run examples.stateful.app:api --port 8000
"""

from typing import Annotated

from pydantic import BaseModel

from semblance import FromInput, SemblanceAPI


class CreateUser(BaseModel):
    """POST body for creating a user."""

    name: str = "alice"


class UserWithId(BaseModel):
    id: str = ""
    name: Annotated[str, FromInput("name")]


api = SemblanceAPI(stateful=True)


@api.post("/users", input=CreateUser, output=UserWithId, summary="Create user")
def create_user():
    """Creates user and stores in state. Returns stored instance with id."""
    pass


@api.get("/users", input=CreateUser, output=list[UserWithId], summary="List users")
def list_users():
    """Returns all stored users (stateful)."""
    pass


app = api.as_fastapi()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
