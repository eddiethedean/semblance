"""
Basic Semblance API - minimal GET list endpoint.

Run: semblance run examples.basic.app:api --port 8000
Or:  uvicorn examples.basic.app:app --reload
"""

from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel

from semblance import DateRangeFrom, FromInput, SemblanceAPI


class UserQuery(BaseModel):
    """GET query params for user list."""

    name: str = "alice"
    start_date: date = date(2020, 1, 1)
    end_date: date = date(2025, 12, 31)


class User(BaseModel):
    """Output model with links to input."""

    name: Annotated[str, FromInput("name")]
    created_at: Annotated[
        datetime,
        DateRangeFrom("start_date", "end_date"),
    ]


api = SemblanceAPI()


@api.get("/users", input=UserQuery, output=list[User], summary="List users")
def users():
    """Returns users with name from query and created_at in date range."""
    pass


app = api.as_fastapi()
