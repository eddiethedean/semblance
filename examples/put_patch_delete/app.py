"""
Phase 5 example: PUT, PATCH, DELETE endpoints (non-stateful).

Run: semblance run examples.put_patch_delete.app:api --port 8000
"""

from typing import Annotated

from pydantic import BaseModel
from semblance import FromInput, SemblanceAPI


class User(BaseModel):
    """Output model for user resources."""

    id: str = ""
    name: Annotated[str, FromInput("name")]


class UpdateBody(BaseModel):
    """Request body for PUT and PATCH."""

    name: str = "updated"


class PathIdInput(BaseModel):
    """Path parameter for by-id routes."""

    id: str = ""


api = SemblanceAPI(seed=42)


@api.put("/users/{id}", input=UpdateBody, output=User, summary="Replace user")
def put_user():
    """PUT returns a generated response; path param id is available for links."""
    pass


@api.patch("/users/{id}", input=UpdateBody, output=User, summary="Update user")
def patch_user():
    """PATCH returns a generated response with body merged into path params."""
    pass


@api.delete("/users/{id}", input=PathIdInput, summary="Delete user")
def delete_user():
    """DELETE with no output returns 204 No Content."""
    pass


@api.delete(
    "/users/{id}/with-body",
    input=PathIdInput,
    output=User,
    summary="Delete user (return deleted)",
)
def delete_user_with_output():
    """DELETE with output returns 200 and a generated body."""
    pass


app = api.as_fastapi()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
