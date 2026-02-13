"""
Advanced example - WhenInput, ComputedFrom, filter_by.

Run: semblance run examples.advanced.app:api --port 8000
"""

from typing import Annotated

from pydantic import BaseModel

from semblance import ComputedFrom, FromInput, SemblanceAPI, WhenInput


class UserWithStatus(BaseModel):
    name: Annotated[str, FromInput("name")]
    status: Annotated[str, WhenInput("include_status", True, FromInput("status"))]


class QueryWithStatus(BaseModel):
    name: str = "alice"
    status: str = "active"
    include_status: bool = False


class UserWithFullName(BaseModel):
    first: Annotated[str, FromInput("first")]
    last: Annotated[str, FromInput("last")]
    full: Annotated[str, ComputedFrom(("first", "last"), lambda a, b: f"{a} {b}")]


class QueryWithNames(BaseModel):
    first: str = "John"
    last: str = "Doe"


api = SemblanceAPI()


@api.get(
    "/user/status",
    input=QueryWithStatus,
    output=UserWithStatus,
    summary="Get user with optional status",
)
def user_status():
    """WhenInput: status only applied when include_status=True."""
    pass


@api.get(
    "/user/fullname",
    input=QueryWithNames,
    output=UserWithFullName,
    summary="Get user with computed full name",
)
def user_fullname():
    """ComputedFrom: full = first + ' ' + last."""
    pass


@api.get(
    "/users",
    input=QueryWithStatus,
    output=list[UserWithStatus],
    list_count=3,
    filter_by="status",
    summary="List users filtered by status",
)
def users_filtered():
    """filter_by: all items match input.status."""
    pass


app = api.as_fastapi()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
