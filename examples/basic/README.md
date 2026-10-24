# Basic Example

Minimal Semblance API with a single GET list endpoint.

[Python source](https://github.com/eddiethedean/semblance/blob/main/examples/basic/app.py)

## Code

```python
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


api = SemblanceAPI(seed=42)


@api.get(
    "/users", input=UserQuery, output=list[User], list_count=2, summary="List users"
)
def users():
    """Returns users with name from query and created_at in date range."""
    pass


app = api.as_fastapi()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
```

## Run

From the repository root, with Semblance installed:

```bash
semblance run examples.basic.app:api --port 8000
```

## Requests and responses

**Input:**

```bash
curl -sS 'http://127.0.0.1:8000/users?name=alice&start_date=2024-01-01&end_date=2024-12-31'
```

**Output — `200 OK`:**

```json
[
  {"name": "alice", "created_at": "2024-08-22T00:43:29.352128"},
  {"name": "alice", "created_at": "2024-01-10T03:41:40.080943"}
]
```

Exact generated values can change with dependency versions.

## Further reading

See the [guide](../../docs/guides/getting-started.md) for the behavior and available options.
