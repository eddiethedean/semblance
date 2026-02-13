# Advanced Example

WhenInput, ComputedFrom, and filter_by.

## Code

```python
"""
Advanced example - WhenInput, ComputedFrom, filter_by.
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
```

## Run

```bash
semblance run examples.advanced.app:api --port 8000
```

## Try

```bash
# WhenInput - status applied only when include_status=true
curl "http://127.0.0.1:8000/user/status?name=alice&include_status=true&status=active"

# ComputedFrom - full name computed from first + last
curl "http://127.0.0.1:8000/user/fullname?first=Jane&last=Smith"

# filter_by - all list items match status (include_status=true so status comes from input)
curl "http://127.0.0.1:8000/users?name=x&status=active&include_status=true"
```

Example responses:

```json
// GET /user/status?name=alice&include_status=true&status=active
{"name": "alice", "status": "active"}

// GET /user/fullname?first=Jane&last=Smith
{"first": "Jane", "last": "Smith", "full": "Jane Smith"}

// GET /users?name=x&status=active&include_status=true (filter_by)
[
  {"name": "x", "status": "active"},
  {"name": "x", "status": "active"},
  {"name": "x", "status": "active"}
]
```

## Concepts

- **WhenInput(cond, val, link)** – apply link only when cond matches
- **ComputedFrom(fields, fn)** – compute field from other output fields
- **filter_by** – filter list items to those matching input field value
