"""
Phase 6 example: Full stateful CRUD — POST, GET list, GET by id, PUT, PATCH, DELETE.

Run: semblance run examples.stateful_crud.app:api --port 8000
"""

from typing import Annotated

from pydantic import BaseModel
from semblance import FromInput, SemblanceAPI


class CreateUser(BaseModel):
    """POST body for creating a user."""

    name: str = "alice"


class UserWithId(BaseModel):
    """User with id; used for list and by-id responses."""

    id: str = ""
    name: Annotated[str, FromInput("name")]


class UpdateBody(BaseModel):
    """Request body for PUT and PATCH."""

    name: str = "updated"


class PathIdInput(BaseModel):
    """Path parameter for by-id routes."""

    id: str = ""


api = SemblanceAPI(stateful=True, seed=42)


@api.post("/users", input=CreateUser, output=UserWithId, summary="Create user")
def create_user():
    """Stores created user; returns instance with generated id."""
    pass


@api.get("/users", input=CreateUser, output=list[UserWithId], summary="List users")
def list_users():
    """Returns all stored users."""
    pass


@api.get(
    "/users/{id}",
    input=PathIdInput,
    output=UserWithId,
    summary="Get user by id",
)
def get_user():
    """Returns stored user or 404."""
    pass


@api.put(
    "/users/{id}",
    input=UpdateBody,
    output=UserWithId,
    summary="Upsert user",
)
def put_user():
    """Replaces existing or adds new user with this id."""
    pass


@api.patch(
    "/users/{id}",
    input=UpdateBody,
    output=UserWithId,
    summary="Update user",
)
def patch_user():
    """Updates existing user; 404 if not found."""
    pass


@api.delete(
    "/users/{id}",
    input=PathIdInput,
    summary="Delete user",
)
def delete_user():
    """Removes user; 204 if found, 404 if not."""
    pass


app = api.as_fastapi()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
