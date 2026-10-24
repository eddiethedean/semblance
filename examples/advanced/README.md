# Advanced Example

WhenInput, ComputedFrom, and filter_by.

[Python source](https://github.com/eddiethedean/semblance/blob/main/examples/advanced/app.py)

## Code

```python
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


api = SemblanceAPI(seed=42)


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
```

## Run

From the repository root, with Semblance installed:

```bash
semblance run examples.advanced.app:api --port 8000
```

## Requests and responses

**Input 1:**

```bash
curl -sS 'http://127.0.0.1:8000/user/status?name=alice&include_status=true&status=active'
```

**Output — `200 OK`:**

```json
{"name": "alice", "status": "active"}
```

**Input 2:**

```bash
curl -sS 'http://127.0.0.1:8000/user/fullname?first=Jane&last=Smith'
```

**Output — `200 OK`:**

```json
{"first": "Jane", "last": "Smith", "full": "Jane Smith"}
```

**Input 3:**

```bash
curl -sS 'http://127.0.0.1:8000/users?name=x&status=active&include_status=true'
```

**Output — `200 OK`:**

```json
[
  {"name": "x", "status": "active"},
  {"name": "x", "status": "active"},
  {"name": "x", "status": "active"}
]
```

Exact generated values can change with dependency versions.

## Further reading

See the [guide](../../docs/guides/advanced-links.md) for the behavior and available options.
