# Basic Example

Minimal Semblance API with a single GET list endpoint.

## Code

```python
"""
Basic Semblance API - minimal GET list endpoint.
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


api = SemblanceAPI(seed=42)


@api.get("/users", input=UserQuery, output=list[User], list_count=2, summary="List users")
def users():
    """Returns users with name from query and created_at in date range."""
    pass


app = api.as_fastapi()
```

## Run

```bash
semblance run examples.basic.app:api --port 8000
# or
uvicorn examples.basic.app:app --reload
```

## Try

```bash
curl "http://127.0.0.1:8000/users?name=alice&start_date=2024-01-01&end_date=2024-12-31"
```

Example response (with `seed=42`):

```json
[
  {"name": "alice", "created_at": "2024-08-21T09:22:43.516168"},
  {"name": "alice", "created_at": "2024-01-10T03:05:39.176702"}
]
```

## Concepts

- **UserQuery** – input model for query params
- **User** – output model with `FromInput` and `DateRangeFrom` links
- No endpoint logic – schemas drive behavior
