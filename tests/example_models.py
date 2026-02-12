"""Example Pydantic models matching the roadmap doc (UserQuery, User with FromInput/DateRangeFrom)."""

from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel

from semblance import DateRangeFrom, FromInput


class UserQuery(BaseModel):
    """GET query params for user list."""

    name: str = "alice"
    start_date: date = date(2020, 1, 1)
    end_date: date = date(2025, 12, 31)


class User(BaseModel):
    """Output model with dependencies on UserQuery."""

    name: Annotated[str, FromInput("name")]
    created_at: Annotated[
        datetime,
        DateRangeFrom("start_date", "end_date"),
    ]
