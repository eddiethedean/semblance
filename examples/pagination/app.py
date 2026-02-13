"""
Pagination example - PageParams and PaginatedResponse.

Run: semblance run examples.pagination.app:api --port 8000
"""

from typing import Annotated

from pydantic import BaseModel

from semblance import FromInput, PageParams, PaginatedResponse, SemblanceAPI


class UserQuery(PageParams, BaseModel):
    """Query with limit and offset."""

    name: str = "alice"


class User(BaseModel):
    name: Annotated[str, FromInput("name")]


api = SemblanceAPI()


@api.get(
    "/users",
    input=UserQuery,
    output=PaginatedResponse[User],
    list_count="limit",
    summary="List users (paginated)",
)
def users():
    """Returns paginated user list."""
    pass


app = api.as_fastapi()
